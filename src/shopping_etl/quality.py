"""Reporte de calidad de datos que se guarda en etl_runs.quality_report."""

from typing import Any

import polars as pl

from shopping_etl.reference import FREQUENCIES
from shopping_etl.segment import Thresholds
from shopping_etl.validate import ValidationResult


def build_report(
    raw: pl.DataFrame,
    validation: ValidationResult,
    staging: pl.DataFrame,
    thresholds: Thresholds,
    promo_mismatches: int,
) -> dict[str, Any]:
    synonyms: dict[str, list[str]] = {}
    for original, (label, _) in FREQUENCIES.items():
        synonyms.setdefault(label, []).append(original)
    merged = {label: originals for label, originals in synonyms.items() if len(originals) > 1}

    gender_subscription = (
        staging.group_by("gender", "subscribed").len().sort("gender", "subscribed").rows(named=True)
    )
    segments = staging.group_by("segment").len().sort("len", descending=True).rows(named=True)

    return {
        "rows": {
            "read": raw.height,
            "valid": validation.valid.height,
            "rejected": validation.rejected.height,
        },
        "nulls_by_column": {k: v for k, v in raw.null_count().row(0, named=True).items() if v},
        "discount_equals_promo": {
            "equal": promo_mismatches == 0,
            "mismatches": promo_mismatches,
            "action": "Se unifican en promo_used",
        },
        "frequency_synonyms_merged": merged,
        "gender_by_subscription": gender_subscription,
        "subscribed_women": staging.filter(
            (pl.col("gender") == "Female") & pl.col("subscribed")
        ).height,
        "has_date_column": False,
        "segments": segments,
        "segment_thresholds": {
            "estimated_annual_value": [thresholds.value_low, thresholds.value_high],
            "previous_purchases": [thresholds.purchases_low, thresholds.purchases_high],
        },
    }
