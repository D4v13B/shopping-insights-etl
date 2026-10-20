from pathlib import Path

import polars as pl
import pytest

from shopping_etl.config import Settings
from shopping_etl.extract import ExtractError, extract, read_raw_csv


def settings(**kwargs: object) -> Settings:
    return Settings(DATABASE_URL_ETL="postgresql://u:p@localhost/db", **kwargs)  # type: ignore[arg-type]


def test_read_raw_csv_reads_everything_as_text(dataset_path: Path) -> None:
    df = read_raw_csv(dataset_path)
    assert df.shape == (3900, 19)
    assert set(df.dtypes) == {pl.String}
    assert df.columns[0] == "customer_id"


def test_read_raw_csv_fails_on_missing_columns(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("Customer ID,Age\n1,30\n")
    with pytest.raises(ExtractError, match="Faltan columnas"):
        read_raw_csv(bad)


def test_read_raw_csv_fails_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ExtractError, match="No existe"):
        read_raw_csv(tmp_path / "nope.csv")


def test_extract_uses_local_without_credentials(dataset_path: Path) -> None:
    result = extract(settings(ETL_FALLBACK_CSV=dataset_path))
    assert result.source == "local"
    assert result.raw.height == 3900


def test_extract_falls_back_when_kaggle_fails(
    dataset_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_: Settings) -> Path:
        raise ConnectionError("sin red")

    monkeypatch.setattr("shopping_etl.extract._download_from_kaggle", boom)
    s = settings(ETL_FALLBACK_CSV=dataset_path, KAGGLE_USERNAME="u", KAGGLE_KEY="k")
    assert extract(s).source == "local"


def test_extract_uses_kaggle_with_credentials(
    dataset_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("shopping_etl.extract._download_from_kaggle", lambda _: dataset_path)
    s = settings(ETL_FALLBACK_CSV=Path("/no/existe.csv"), KAGGLE_USERNAME="u", KAGGLE_KEY="k")
    assert extract(s).source == "kaggle"
