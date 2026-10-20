import polars as pl
import pytest

from shopping_etl.extract import read_raw_csv
from shopping_etl.model import IntegrityError, build_model
from shopping_etl.segment import segment
from shopping_etl.transform import transform
from shopping_etl.validate import validate


@pytest.fixture(scope="module")
def staging(dataset_path) -> pl.DataFrame:  # type: ignore[no-untyped-def]
    staged, _ = segment(transform(validate(read_raw_csv(dataset_path)).valid))
    return staged


@pytest.fixture(scope="module")
def dataset_path():  # type: ignore[no-untyped-def]
    from tests.conftest import DATASET

    return DATASET


def test_dimension_sizes(staging: pl.DataFrame) -> None:
    m = build_model(staging)
    assert m.dim_customer.height == 3900
    assert m.dim_product.height == 25
    assert m.dim_location.height == 50
    assert m.dim_payment.height == 36
    assert m.fact_purchase.height == 3900


def test_surrogate_keys_are_deterministic(staging: pl.DataFrame) -> None:
    a = build_model(staging)
    b = build_model(staging.sample(fraction=1.0, shuffle=True, seed=42))
    assert a.dim_product.equals(b.dim_product)
    assert a.dim_payment.equals(b.dim_payment)
    assert a.fact_purchase.equals(b.fact_purchase)


def test_fact_totals_match_staging(staging: pl.DataFrame) -> None:
    m = build_model(staging)
    assert m.fact_purchase["amount_usd"].sum() == staging["amount_usd"].sum() == 233081


def test_unknown_state_breaks_integrity(staging: pl.DataFrame) -> None:
    broken = staging.with_columns(
        pl.when(pl.col("customer_id") == 1)
        .then(pl.lit("Atlantis"))
        .otherwise(pl.col("state_name"))
        .alias("state_name")
    )
    with pytest.raises(IntegrityError):
        build_model(broken)
