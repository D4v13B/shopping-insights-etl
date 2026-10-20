"""Segmentación determinista de clientes (PRD RF-ETL-04).

V = tercil de estimated_annual_value, P = tercil de previous_purchases. Las reglas se evalúan
en orden y gana la primera que se cumple. Sin fechas no hay recencia: "En riesgo" es un proxy
(historial relevante con frecuencia de compra baja).
"""

from dataclasses import dataclass
from typing import Final

import polars as pl

LOW_FREQUENCIES: Final = ("annually", "quarterly")
ALTO, MEDIO, BAJO = "alto", "medio", "bajo"


@dataclass(frozen=True)
class Rule:
    segment: str
    value_levels: tuple[str, ...]
    purchase_levels: tuple[str, ...]
    low_frequency_only: bool = False


ANY: Final = (ALTO, MEDIO, BAJO)

SEGMENT_RULES: Final[tuple[Rule, ...]] = (
    Rule("Campeones", value_levels=(ALTO,), purchase_levels=(ALTO,)),
    Rule("Leales", value_levels=ANY, purchase_levels=(ALTO,)),
    Rule("En riesgo", value_levels=ANY, purchase_levels=(MEDIO, ALTO), low_frequency_only=True),
    Rule("Potenciales", value_levels=(ALTO,), purchase_levels=(BAJO,)),
    Rule("Ocasionales", value_levels=ANY, purchase_levels=ANY),
)


@dataclass(frozen=True)
class Thresholds:
    value_low: float
    value_high: float
    purchases_low: float
    purchases_high: float


def compute_thresholds(df: pl.DataFrame) -> Thresholds:
    value, purchases = df["estimated_annual_value"], df["previous_purchases"]

    def q(series: pl.Series, quantile: float) -> float:
        result = series.quantile(quantile, interpolation="linear")
        if result is None:
            raise ValueError(f"No se puede calcular el cuantil de {series.name}: serie vacía")
        return float(result)

    return Thresholds(
        value_low=q(value, 1 / 3),
        value_high=q(value, 2 / 3),
        purchases_low=q(purchases, 1 / 3),
        purchases_high=q(purchases, 2 / 3),
    )


def _level(col: str, low: float, high: float) -> pl.Expr:
    return (
        pl.when(pl.col(col) > high)
        .then(pl.lit(ALTO))
        .when(pl.col(col) > low)
        .then(pl.lit(MEDIO))
        .otherwise(pl.lit(BAJO))
    )


def assign_segments(df: pl.DataFrame, thresholds: Thresholds) -> pl.DataFrame:
    v = _level("estimated_annual_value", thresholds.value_low, thresholds.value_high)
    p = _level("previous_purchases", thresholds.purchases_low, thresholds.purchases_high)
    low_freq = pl.col("frequency_label").is_in(LOW_FREQUENCIES)

    expr: pl.Expr = pl.lit(None, dtype=pl.String)
    # Se construye de la última regla a la primera, para que la primera tenga prioridad.
    for rule in reversed(SEGMENT_RULES):
        cond = v.is_in(rule.value_levels) & p.is_in(rule.purchase_levels)
        if rule.low_frequency_only:
            cond = cond & low_freq
        expr = pl.when(cond).then(pl.lit(rule.segment)).otherwise(expr)
    return df.with_columns(expr.alias("segment"))


def segment(df: pl.DataFrame) -> tuple[pl.DataFrame, Thresholds]:
    thresholds = compute_thresholds(df)
    return assign_segments(df, thresholds), thresholds
