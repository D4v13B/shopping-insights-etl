"""Orquestación de una ejecución completa: extract -> validate -> transform -> segment -> load."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Final
from uuid import UUID

import polars as pl
import psycopg
import structlog

from shopping_etl import runs
from shopping_etl.config import Settings
from shopping_etl.extract import extract
from shopping_etl.load import load
from shopping_etl.logs import get_logger
from shopping_etl.model import StarModel, build_model
from shopping_etl.quality import build_report
from shopping_etl.schemas import StagingSchema
from shopping_etl.segment import segment
from shopping_etl.transform import promo_mismatches, transform
from shopping_etl.validate import validate

log = get_logger(__name__)

# Clave del advisory lock de sesión: lo mantiene quien está ejecutando el ETL.
ETL_LOCK_KEY: Final = 7_340_211_905


class AlreadyRunningError(RuntimeError):
    """Otro proceso tiene el lock del ETL."""


@dataclass(frozen=True)
class Prepared:
    source: str
    raw: pl.DataFrame
    staging: pl.DataFrame
    rejected: pl.DataFrame
    model: StarModel
    report: dict[str, Any]


def prepare(settings: Settings) -> Prepared:
    """Todo lo que no toca la base: se puede probar en memoria."""
    extracted = extract(settings)
    validation = validate(extracted.raw)
    mismatches = promo_mismatches(validation.valid)
    if mismatches:
        log.warning("discount_y_promo_difieren", filas=mismatches)
    transformed = transform(validation.valid)
    staged, thresholds = segment(transformed)
    staged = StagingSchema.validate(staged)
    model = build_model(staged)
    report = build_report(extracted.raw, validation, staged, thresholds, mismatches)
    report["source"] = extracted.source
    log.info(
        "preparado",
        filas_leidas=extracted.raw.height,
        validas=validation.valid.height,
        rechazadas=validation.rejected.height,
        segmentos=report["segments"],
    )
    return Prepared(extracted.source, extracted.raw, staged, validation.rejected, model, report)


@contextmanager
def etl_lock(dsn: str) -> Iterator[psycopg.Connection[Any]]:
    """Conexión de control (autocommit) que mantiene el advisory lock durante toda la ejecución.
    Si el proceso muere, Postgres libera el lock al cerrarse la conexión."""
    with psycopg.connect(dsn, autocommit=True) as conn:
        row = conn.execute("SELECT pg_try_advisory_lock(%s)", (ETL_LOCK_KEY,)).fetchone()
        if not row or not row[0]:
            raise AlreadyRunningError("Ya hay una ejecución del ETL en curso")
        try:
            yield conn
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (ETL_LOCK_KEY,))


def execute(settings: Settings, *, trigger: str, run_id: UUID | None = None) -> UUID | None:
    """Ejecuta el ETL. Sin run_id crea (o adopta) una ejecución; con run_id procesa esa solicitud.
    Devuelve el id ejecutado, o None si la solicitud ya no estaba pendiente."""
    with etl_lock(settings.dsn) as control:
        orphans = runs.fail_orphans(control)
        if orphans:
            log.warning("ejecuciones_huerfanas_marcadas_failed", cantidad=orphans)

        if run_id is None:
            run_id = runs.claim_pending_or_create(control, trigger)
        elif not runs.claim(control, run_id):
            log.info("solicitud_ya_no_pendiente", run_id=str(run_id))
            return None

        structlog.contextvars.bind_contextvars(run_id=str(run_id))
        started = time.perf_counter()

        def elapsed_ms() -> int:
            return int((time.perf_counter() - started) * 1000)

        try:
            log.info("etl_inicio", trigger=trigger)
            prepared = prepare(settings)
            current_run = run_id

            def on_success(conn: psycopg.Connection[Any]) -> None:
                runs.mark_success(
                    conn,
                    current_run,
                    source=prepared.source,
                    rows_read=prepared.raw.height,
                    rows_valid=prepared.staging.height,
                    rows_rejected=prepared.rejected.height,
                    duration_ms=elapsed_ms(),
                    quality_report=prepared.report,
                )

            with psycopg.connect(settings.dsn) as conn:
                load(
                    conn,
                    run_id=str(run_id),
                    raw=prepared.raw,
                    staging=prepared.staging,
                    rejected=prepared.rejected,
                    model=prepared.model,
                    on_success=on_success,
                )
            log.info("etl_ok", duration_ms=elapsed_ms())
            return run_id
        except Exception as exc:
            # El rollback ya dejó los datos como estaban; el estado se registra aparte.
            runs.mark_failed(
                control, run_id, error=f"{type(exc).__name__}: {exc}", duration_ms=elapsed_ms()
            )
            log.exception("etl_fallo", duration_ms=elapsed_ms())
            raise
        finally:
            structlog.contextvars.unbind_contextvars("run_id")
