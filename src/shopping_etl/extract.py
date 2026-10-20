"""Extracción: Kaggle (si hay credenciales) con respaldo en el CSV local."""

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

import polars as pl

from shopping_etl.config import Settings
from shopping_etl.logs import get_logger

log = get_logger(__name__)

# Encabezado original del CSV -> nombre de columna en raw.shopping_trends.
RAW_COLUMNS: Final[dict[str, str]] = {
    "Customer ID": "customer_id",
    "Age": "age",
    "Gender": "gender",
    "Item Purchased": "item_purchased",
    "Category": "category",
    "Purchase Amount (USD)": "purchase_amount_usd",
    "Location": "location",
    "Size": "size",
    "Color": "color",
    "Season": "season",
    "Review Rating": "review_rating",
    "Subscription Status": "subscription_status",
    "Payment Method": "payment_method",
    "Shipping Type": "shipping_type",
    "Discount Applied": "discount_applied",
    "Promo Code Used": "promo_code_used",
    "Previous Purchases": "previous_purchases",
    "Preferred Payment Method": "preferred_payment_method",
    "Frequency of Purchases": "frequency_of_purchases",
}

Source = Literal["kaggle", "local"]


class ExtractError(RuntimeError):
    """El archivo no existe o no tiene las columnas esperadas."""


@dataclass(frozen=True)
class Extracted:
    raw: pl.DataFrame
    source: Source
    path: Path


def read_raw_csv(path: Path) -> pl.DataFrame:
    """Lee el CSV todo como texto y renombra a snake_case. No valida valores."""
    if not path.is_file():
        raise ExtractError(f"No existe el archivo {path}")
    df = pl.read_csv(path, infer_schema=False)
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ExtractError(f"Faltan columnas en {path.name}: {sorted(missing)}")
    return df.select(pl.col(src).alias(dst) for src, dst in RAW_COLUMNS.items())


def _download_from_kaggle(settings: Settings) -> Path:
    import kagglehub  # import diferido: solo hace falta con credenciales

    folder = Path(kagglehub.dataset_download(settings.kaggle_dataset))
    return folder / settings.kaggle_file


def extract(settings: Settings) -> Extracted:
    if settings.has_kaggle_credentials:
        try:
            path = _download_from_kaggle(settings)
            df = read_raw_csv(path)
        except Exception as exc:  # cualquier fallo de red o de formato -> respaldo local
            log.warning("kaggle_fallo_usando_respaldo", error=str(exc))
        else:
            log.info("extraccion", source="kaggle", rows=df.height, path=str(path))
            return Extracted(df, "kaggle", path)
    else:
        log.info("kaggle_sin_credenciales_usando_respaldo")

    df = read_raw_csv(settings.fallback_csv)
    log.info("extraccion", source="local", rows=df.height, path=str(settings.fallback_csv))
    return Extracted(df, "local", settings.fallback_csv)
