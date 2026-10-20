"""Transformaciones puras (DataFrame -> DataFrame). Sin E/S: todo es testeable en memoria."""

import polars as pl

from shopping_etl.reference import AGE_BANDS, FREQUENCIES, US_STATES

_YES = "Yes"


def rename_columns(df: pl.DataFrame) -> pl.DataFrame:
    return df.rename(
        {
            "item_purchased": "item_name",
            "purchase_amount_usd": "amount_usd",
            "location": "state_name",
            "subscription_status": "subscribed",
        }
    )


def to_booleans(df: pl.DataFrame) -> pl.DataFrame:
    """Yes/No -> booleano."""
    cols = ["subscribed", "discount_applied", "promo_code_used"]
    return df.with_columns(pl.col(c).eq(_YES) for c in cols)


def promo_mismatches(df: pl.DataFrame) -> int:
    """Cuántas filas tienen discount_applied distinto de promo_code_used (se espera 0)."""
    return df.filter(pl.col("discount_applied") != pl.col("promo_code_used")).height


def unify_promo(df: pl.DataFrame) -> pl.DataFrame:
    """Discount Applied y Promo Code Used son redundantes: se unifican en promo_used (OR)."""
    return df.with_columns(
        (pl.col("discount_applied") | pl.col("promo_code_used")).alias("promo_used")
    ).drop("discount_applied", "promo_code_used")


def normalize_frequency(df: pl.DataFrame) -> pl.DataFrame:
    """Fusiona sinónimos (Fortnightly = Bi-Weekly, Quarterly = Every 3 Months) y deriva días."""
    labels = {k: label for k, (label, _) in FREQUENCIES.items()}
    days = {k: d for k, (_, d) in FREQUENCIES.items()}
    freq = pl.col("frequency_of_purchases")
    return (
        df.with_columns(
            freq.replace_strict(labels, return_dtype=pl.String).alias("frequency_label"),
            freq.replace_strict(days, return_dtype=pl.Int64).alias("frequency_days"),
        )
        .with_columns(
            (365 / pl.col("frequency_days")).round(2).alias("purchases_per_year"),
        )
        .drop("frequency_of_purchases")
    )


def add_age_band(df: pl.DataFrame) -> pl.DataFrame:
    expr: pl.Expr = pl.lit(None, dtype=pl.String)
    # Se evalúa de mayor a menor límite: la primera banda cuyo mínimo se cumple gana.
    for lower, label in AGE_BANDS:
        expr = pl.when(pl.col("age") >= lower).then(pl.lit(label)).otherwise(expr)
    return df.with_columns(expr.alias("age_band"))


def add_location(df: pl.DataFrame) -> pl.DataFrame:
    codes = {name: code for name, (code, _) in US_STATES.items()}
    regions = {name: region for name, (_, region) in US_STATES.items()}
    state = pl.col("state_name")
    return df.with_columns(
        state.replace_strict(codes, return_dtype=pl.String).alias("state_code"),
        state.replace_strict(regions, return_dtype=pl.String).alias("region"),
    )


def add_value_metrics(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        (pl.col("amount_usd") * pl.col("purchases_per_year"))
        .round(2)
        .alias("estimated_annual_value"),
        (pl.col("previous_purchases") + 1).alias("lifetime_purchases"),
    )


def transform(valid: pl.DataFrame) -> pl.DataFrame:
    """Aplica todas las transformaciones en orden. Recibe la salida tipada de validate()."""
    return (
        valid.drop("row_number")
        .pipe(rename_columns)
        .pipe(to_booleans)
        .pipe(unify_promo)
        .pipe(normalize_frequency)
        .pipe(add_age_band)
        .pipe(add_location)
        .pipe(add_value_metrics)
    )
