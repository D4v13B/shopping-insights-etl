import polars as pl

from shopping_etl.segment import (
    SEGMENT_RULES,
    Thresholds,
    assign_segments,
    compute_thresholds,
    segment,
)

T = Thresholds(value_low=100, value_high=1000, purchases_low=10, purchases_high=30)


def seg(value: float, purchases: int, frequency: str = "monthly") -> str:
    df = pl.DataFrame(
        {
            "estimated_annual_value": [value],
            "previous_purchases": [purchases],
            "frequency_label": [frequency],
        }
    )
    return str(assign_segments(df, T)["segment"][0])


def test_rules_in_priority_order() -> None:
    assert seg(5000, 40) == "Campeones"
    assert seg(5000, 40, "annually") == "Campeones"  # la primera regla gana
    assert seg(500, 40) == "Leales"
    assert seg(50, 40, "annually") == "Leales"
    assert seg(500, 20, "quarterly") == "En riesgo"
    assert seg(500, 20, "monthly") == "Ocasionales"
    assert seg(5000, 5) == "Potenciales"
    assert seg(50, 5) == "Ocasionales"


def test_thresholds_are_strict_upper_bounds() -> None:
    # Justo en el umbral cuenta como el nivel inferior.
    assert seg(1000, 30) == "Ocasionales"
    assert seg(1000.01, 31) == "Campeones"


def test_compute_thresholds_terciles() -> None:
    df = pl.DataFrame(
        {
            "estimated_annual_value": [float(x) for x in range(1, 301)],
            "previous_purchases": list(range(1, 301)),
        }
    )
    t = compute_thresholds(df)
    assert round(t.value_low) == 101
    assert round(t.value_high) == 200


def test_every_customer_gets_one_of_the_five_segments(dataset_path) -> None:  # type: ignore[no-untyped-def]
    from shopping_etl.extract import read_raw_csv
    from shopping_etl.transform import transform
    from shopping_etl.validate import validate

    df, _ = segment(transform(validate(read_raw_csv(dataset_path)).valid))
    names = {r.segment for r in SEGMENT_RULES}
    assert df["segment"].null_count() == 0
    assert set(df["segment"].unique()) == names
