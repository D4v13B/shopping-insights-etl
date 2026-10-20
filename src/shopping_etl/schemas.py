"""Contratos de datos (Pandera) de la entrada tipada y de staging."""

import pandera.polars as pa
import polars as pl

from shopping_etl.reference import (
    AGE_BANDS,
    CATEGORIES,
    FREQUENCIES,
    GENDERS,
    SEASONS,
    SIZES,
    US_STATES,
    YES_NO,
)


class InputSchema(pa.DataFrameModel):
    """Reglas de RF-ETL-02 sobre la entrada ya convertida a sus tipos."""

    row_number: int
    customer_id: int = pa.Field(gt=0, unique=True)
    age: int = pa.Field(ge=18, le=100)
    gender: str = pa.Field(isin=GENDERS)
    item_purchased: str = pa.Field(str_length={"min_value": 1})
    category: str = pa.Field(isin=CATEGORIES)
    purchase_amount_usd: float = pa.Field(gt=0)
    location: str = pa.Field(isin=list(US_STATES))
    size: str = pa.Field(isin=SIZES)
    color: str = pa.Field(str_length={"min_value": 1})
    season: str = pa.Field(isin=SEASONS)
    review_rating: float = pa.Field(ge=1, le=5)
    subscription_status: str = pa.Field(isin=YES_NO)
    payment_method: str = pa.Field(str_length={"min_value": 1})
    shipping_type: str = pa.Field(str_length={"min_value": 1})
    discount_applied: str = pa.Field(isin=YES_NO)
    promo_code_used: str = pa.Field(isin=YES_NO)
    previous_purchases: int = pa.Field(ge=0)
    preferred_payment_method: str = pa.Field(str_length={"min_value": 1})
    frequency_of_purchases: str = pa.Field(isin=list(FREQUENCIES))

    class Config:
        strict = True


class StagingSchema(pa.DataFrameModel):
    """Salida de transform + segment: lo que se carga en staging.purchases."""

    customer_id: int = pa.Field(unique=True)
    age: int
    age_band: str = pa.Field(isin=[label for _, label in AGE_BANDS])
    gender: str
    item_name: str
    category: str
    amount_usd: float = pa.Field(gt=0)
    state_name: str
    state_code: str = pa.Field(str_length={"min_value": 2, "max_value": 2})
    region: str
    size: str
    color: str
    season: str
    review_rating: float
    subscribed: bool
    payment_method: str
    shipping_type: str
    promo_used: bool
    previous_purchases: int
    lifetime_purchases: int
    preferred_payment_method: str
    frequency_label: str
    frequency_days: int = pa.Field(gt=0)
    purchases_per_year: float = pa.Field(gt=0)
    estimated_annual_value: float = pa.Field(gt=0)
    segment: str

    class Config:
        strict = "filter"


INPUT_DTYPES: dict[str, pl.DataType] = {
    "customer_id": pl.Int64(),
    "age": pl.Int64(),
    "purchase_amount_usd": pl.Float64(),
    "review_rating": pl.Float64(),
    "previous_purchases": pl.Int64(),
}
