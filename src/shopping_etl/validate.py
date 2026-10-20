"""Validación de entrada: separa filas válidas e inválidas sin detener el pipeline."""

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import polars as pl
from pandera.errors import SchemaErrors

from shopping_etl.schemas import INPUT_DTYPES, InputSchema

RejectedErrors = list[dict[str, Any]]


class ContractError(RuntimeError):
    """El archivo completo incumple el contrato (no es un problema de filas sueltas)."""


@dataclass(frozen=True)
class ValidationResult:
    valid: pl.DataFrame
    """Filas válidas, ya tipadas, con `row_number`."""
    rejected: pl.DataFrame
    """row_number, payload (JSON de la fila original) y errors (JSON con los motivos)."""


def _with_row_number(raw: pl.DataFrame) -> pl.DataFrame:
    # row_number = línea de datos del CSV (1 = primera fila tras el encabezado).
    return raw.with_row_index("row_number", offset=1).with_columns(
        pl.col("row_number").cast(pl.Int64)
    )


def _cast_types(df: pl.DataFrame) -> tuple[pl.DataFrame, dict[int, RejectedErrors]]:
    """Recorta espacios y convierte los numéricos; lo no convertible es un error de fila."""
    text_cols = [c for c in df.columns if c != "row_number"]
    df = df.with_columns(pl.col(text_cols).str.strip_chars())
    typed = df.with_columns(
        pl.col(col).cast(dtype, strict=False) for col, dtype in INPUT_DTYPES.items()
    )
    errors: dict[int, RejectedErrors] = defaultdict(list)
    for col in INPUT_DTYPES:
        bad = df.filter(pl.col(col).is_not_null() & typed[col].is_null())
        for row_number, value in bad.select("row_number", col).iter_rows():
            errors[row_number].append({"column": col, "check": "tipo numérico", "value": value})
    return typed, errors


def _schema_errors(typed: pl.DataFrame) -> dict[int, RejectedErrors]:
    try:
        InputSchema.validate(typed, lazy=True)
    except SchemaErrors as exc:
        cases = exc.failure_cases
        if cases.filter(pl.col("index").is_null()).height:
            raise ContractError(f"Fallo de contrato a nivel de archivo:\n{cases}") from exc
        row_numbers = typed["row_number"]
        errors: dict[int, RejectedErrors] = defaultdict(list)
        for case in cases.iter_rows(named=True):
            row_number = int(row_numbers[case["index"]])
            errors[row_number].append(
                {"column": case["column"], "check": case["check"], "value": case["failure_case"]}
            )
        return errors
    return {}


def validate(raw: pl.DataFrame) -> ValidationResult:
    numbered = _with_row_number(raw)
    typed, errors = _cast_types(numbered)

    # Las filas con errores de tipo no pasan por Pandera: sus columnas numéricas son nulas.
    castable = typed.filter(~pl.col("row_number").is_in(list(errors)))
    for row_number, row_errors in _schema_errors(castable).items():
        errors[row_number].extend(row_errors)

    bad_rows = list(errors)
    valid = typed.filter(~pl.col("row_number").is_in(bad_rows))
    rejected_source = numbered.filter(pl.col("row_number").is_in(bad_rows))
    rejected = pl.DataFrame(
        {
            "row_number": rejected_source["row_number"],
            "payload": [
                json.dumps({k: v for k, v in row.items() if k != "row_number"}, ensure_ascii=False)
                for row in rejected_source.iter_rows(named=True)
            ],
            "errors": [
                json.dumps(errors[n], ensure_ascii=False, default=str)
                for n in rejected_source["row_number"]
            ],
        },
        schema={"row_number": pl.Int64, "payload": pl.String, "errors": pl.String},
    )
    return ValidationResult(valid=valid, rejected=rejected)
