"""Modelo estrella a partir de staging, con surrogate keys deterministas."""

from dataclasses import dataclass

import polars as pl

from shopping_etl.reference import US_STATES


class IntegrityError(RuntimeError):
    """Una fila de hechos no encontró su dimensión."""


@dataclass(frozen=True)
class StarModel:
    dim_customer: pl.DataFrame
    dim_product: pl.DataFrame
    dim_location: pl.DataFrame
    dim_payment: pl.DataFrame
    fact_purchase: pl.DataFrame


def _with_key(df: pl.DataFrame, key: str, natural_key: list[str]) -> pl.DataFrame:
    """Clave 1..n ordenada por la clave natural: la misma entrada da siempre las mismas claves."""
    return (
        df.unique(subset=natural_key)
        .sort(natural_key)
        .with_row_index(key, offset=1)
        .with_columns(pl.col(key).cast(pl.Int64))
    )


def build_dim_location() -> pl.DataFrame:
    """Los 50 estados, aunque alguno no tenga ventas (el mapa los necesita todos)."""
    base = pl.DataFrame(
        {
            "state_name": list(US_STATES),
            "state_code": [code for code, _ in US_STATES.values()],
            "region": [region for _, region in US_STATES.values()],
        }
    )
    return _with_key(base, "location_id", ["state_name"])


def build_model(staging: pl.DataFrame) -> StarModel:
    dim_customer = staging.select(
        "customer_id",
        "age",
        "age_band",
        "gender",
        "subscribed",
        "previous_purchases",
        "lifetime_purchases",
        "frequency_label",
        "frequency_days",
        "purchases_per_year",
        "preferred_payment_method",
        "estimated_annual_value",
        "segment",
    ).sort("customer_id")
    dim_product = _with_key(
        staging.select("item_name", "category"), "product_id", ["item_name", "category"]
    ).select("product_id", "item_name", "category")
    dim_location = build_dim_location().select("location_id", "state_name", "state_code", "region")
    dim_payment = _with_key(
        staging.select("payment_method", "shipping_type"),
        "payment_id",
        ["payment_method", "shipping_type"],
    ).select("payment_id", "payment_method", "shipping_type")

    fact = (
        staging.join(dim_product, on=["item_name", "category"], how="left")
        .join(dim_location.select("location_id", "state_name"), on="state_name", how="left")
        .join(dim_payment, on=["payment_method", "shipping_type"], how="left")
        .select(
            pl.col("customer_id").alias("purchase_id"),
            "customer_id",
            "product_id",
            "location_id",
            "payment_id",
            "season",
            "size",
            "color",
            "amount_usd",
            "review_rating",
            "promo_used",
        )
        .sort("purchase_id")
    )
    orphans = fact.filter(
        pl.any_horizontal(pl.col("product_id", "location_id", "payment_id").is_null())
    )
    if orphans.height:
        raise IntegrityError(f"{orphans.height} hechos sin dimensión: {orphans.head(5)}")

    return StarModel(dim_customer, dim_product, dim_location, dim_payment, fact)
