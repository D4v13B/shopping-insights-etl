import json

import pytest

from shopping_etl.validate import validate
from tests.conftest import raw_frame, raw_row


def errors_for(result_rejected_errors: str) -> set[str]:
    return {e["column"] for e in json.loads(result_rejected_errors)}


def test_valid_rows_pass_and_are_typed() -> None:
    result = validate(raw_frame(raw_row()))
    assert result.valid.height == 1
    assert result.rejected.height == 0
    assert result.valid["age"].dtype.is_integer()
    assert result.valid["row_number"].to_list() == [1]


@pytest.mark.parametrize(
    ("overrides", "column"),
    [
        ({"age": "17"}, "age"),
        ({"age": "101"}, "age"),
        ({"age": "treinta"}, "age"),
        ({"purchase_amount_usd": "0"}, "purchase_amount_usd"),
        ({"review_rating": "5.5"}, "review_rating"),
        ({"gender": "Other"}, "gender"),
        ({"season": "Monsoon"}, "season"),
        ({"size": "XXL"}, "size"),
        ({"category": "Toys"}, "category"),
        ({"frequency_of_purchases": "Daily"}, "frequency_of_purchases"),
        ({"location": "Atlantis"}, "location"),
        ({"subscription_status": "Maybe"}, "subscription_status"),
        ({"color": None}, "color"),
    ],
)
def test_invalid_rows_are_rejected_with_reason(
    overrides: dict[str, str | None], column: str
) -> None:
    result = validate(raw_frame(raw_row(customer_id="1"), raw_row(customer_id="2", **overrides)))
    assert result.valid["customer_id"].to_list() == [1]
    assert result.rejected["row_number"].to_list() == [2]
    assert column in errors_for(result.rejected["errors"][0])


def test_duplicate_customer_ids_are_rejected() -> None:
    result = validate(raw_frame(raw_row(customer_id="7"), raw_row(customer_id="7")))
    assert result.valid.height == 0
    assert result.rejected["row_number"].to_list() == [1, 2]


def test_rejected_payload_keeps_original_text() -> None:
    result = validate(raw_frame(raw_row(age="abc")))
    payload = json.loads(result.rejected["payload"][0])
    assert payload["age"] == "abc"
    assert "row_number" not in payload


def test_whitespace_is_trimmed() -> None:
    result = validate(raw_frame(raw_row(gender="  Male ", age=" 40 ")))
    assert result.valid["gender"].to_list() == ["Male"]
    assert result.valid["age"].to_list() == [40]


def test_full_dataset_has_no_rejections(dataset_path) -> None:  # type: ignore[no-untyped-def]
    from shopping_etl.extract import read_raw_csv

    result = validate(read_raw_csv(dataset_path))
    assert (result.valid.height, result.rejected.height) == (3900, 0)
