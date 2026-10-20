import polars as pl
import pytest

from shopping_etl.transform import (
    add_age_band,
    add_location,
    add_value_metrics,
    normalize_frequency,
    promo_mismatches,
    rename_columns,
    to_booleans,
    transform,
    unify_promo,
)
from shopping_etl.validate import validate
from tests.conftest import raw_frame, raw_row


def test_rename_columns() -> None:
    df = pl.DataFrame(
        {
            "item_purchased": ["x"],
            "purchase_amount_usd": [1.0],
            "location": ["Ohio"],
            "subscription_status": ["Yes"],
        }
    )
    assert rename_columns(df).columns == ["item_name", "amount_usd", "state_name", "subscribed"]


def test_to_booleans() -> None:
    df = pl.DataFrame(
        {
            "subscribed": ["Yes", "No"],
            "discount_applied": ["No", "Yes"],
            "promo_code_used": ["No", "No"],
        }
    )
    out = to_booleans(df)
    assert out["subscribed"].to_list() == [True, False]
    assert out["discount_applied"].to_list() == [False, True]


def test_promo_unification_and_mismatch_count() -> None:
    df = pl.DataFrame(
        {"discount_applied": [True, False, True], "promo_code_used": [True, False, False]}
    )
    assert promo_mismatches(df) == 1
    out = unify_promo(df)
    assert out.columns == ["promo_used"]
    assert out["promo_used"].to_list() == [True, False, True]


@pytest.mark.parametrize(
    ("original", "label", "days", "per_year"),
    [
        ("Weekly", "weekly", 7, 52.14),
        ("Fortnightly", "biweekly", 14, 26.07),
        ("Bi-Weekly", "biweekly", 14, 26.07),
        ("Monthly", "monthly", 30, 12.17),
        ("Quarterly", "quarterly", 90, 4.06),
        ("Every 3 Months", "quarterly", 90, 4.06),
        ("Annually", "annually", 365, 1.0),
    ],
)
def test_normalize_frequency(original: str, label: str, days: int, per_year: float) -> None:
    out = normalize_frequency(pl.DataFrame({"frequency_of_purchases": [original]}))
    assert out.row(0, named=True) == {
        "frequency_label": label,
        "frequency_days": days,
        "purchases_per_year": per_year,
    }


def test_normalize_frequency_rejects_unknown_values() -> None:
    with pytest.raises(pl.exceptions.InvalidOperationError):
        normalize_frequency(pl.DataFrame({"frequency_of_purchases": ["Daily"]}))


@pytest.mark.parametrize(
    ("age", "band"),
    [
        (18, "18-24"),
        (24, "18-24"),
        (25, "25-34"),
        (44, "35-44"),
        (54, "45-54"),
        (64, "55-64"),
        (65, "65+"),
        (70, "65+"),
    ],
)
def test_age_band_boundaries(age: int, band: str) -> None:
    assert add_age_band(pl.DataFrame({"age": [age]}))["age_band"][0] == band


def test_add_location() -> None:
    out = add_location(pl.DataFrame({"state_name": ["New York", "Texas", "Ohio", "Oregon"]}))
    assert out["state_code"].to_list() == ["NY", "TX", "OH", "OR"]
    assert out["region"].to_list() == ["Northeast", "South", "Midwest", "West"]


def test_add_value_metrics() -> None:
    df = pl.DataFrame(
        {"amount_usd": [50.0], "purchases_per_year": [12.17], "previous_purchases": [9]}
    )
    out = add_value_metrics(df).row(0, named=True)
    assert out["estimated_annual_value"] == 608.5
    assert out["lifetime_purchases"] == 10


def test_transform_end_to_end() -> None:
    valid = validate(raw_frame(raw_row(age="23", location="Maine"))).valid
    row = transform(valid).row(0, named=True)
    assert row["age_band"] == "18-24"
    assert row["state_code"] == "ME"
    assert row["region"] == "Northeast"
    assert row["promo_used"] is True
    assert row["frequency_label"] == "biweekly"
    assert row["subscribed"] is False
    assert "row_number" not in row
    assert "discount_applied" not in row


def test_transform_is_pure() -> None:
    valid = validate(raw_frame(raw_row())).valid
    before = valid.clone()
    transform(valid)
    assert valid.equals(before)
