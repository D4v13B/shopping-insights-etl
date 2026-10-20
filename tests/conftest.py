from pathlib import Path

import polars as pl
import pytest

from shopping_etl.extract import RAW_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET = REPO_ROOT / "data" / "shopping_trends.csv"


def raw_row(**overrides: str | None) -> dict[str, str | None]:
    """Una fila cruda válida (todo texto, nombres de raw.shopping_trends)."""
    row: dict[str, str | None] = {
        "customer_id": "1",
        "age": "30",
        "gender": "Female",
        "item_purchased": "Blouse",
        "category": "Clothing",
        "purchase_amount_usd": "50",
        "location": "Texas",
        "size": "M",
        "color": "Red",
        "season": "Winter",
        "review_rating": "4.5",
        "subscription_status": "No",
        "payment_method": "Cash",
        "shipping_type": "Express",
        "discount_applied": "Yes",
        "promo_code_used": "Yes",
        "previous_purchases": "10",
        "preferred_payment_method": "Venmo",
        "frequency_of_purchases": "Fortnightly",
    }
    row.update(overrides)
    return row


def raw_frame(*rows: dict[str, str | None]) -> pl.DataFrame:
    return pl.DataFrame(list(rows), schema=dict.fromkeys(RAW_COLUMNS.values(), pl.String))


@pytest.fixture
def dataset_path() -> Path:
    return DATASET
