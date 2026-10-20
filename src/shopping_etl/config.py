"""Configuración del ETL, validada al arrancar con pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/shopping_etl/config.py -> raíz del repo
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn = Field(validation_alias="DATABASE_URL_ETL")
    kaggle_username: str | None = Field(default=None, validation_alias="KAGGLE_USERNAME")
    kaggle_key: str | None = Field(default=None, validation_alias="KAGGLE_KEY")
    kaggle_dataset: str = "iamsouravbanerjee/customer-shopping-trends-dataset"
    kaggle_file: str = "shopping_trends.csv"
    fallback_csv: Path = Field(
        default=_REPO_ROOT / "data" / "shopping_trends.csv", validation_alias="ETL_FALLBACK_CSV"
    )
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")
    worker_poll_seconds: float = Field(default=30.0, validation_alias="ETL_WORKER_POLL_SECONDS")

    @property
    def has_kaggle_credentials(self) -> bool:
        return bool(self.kaggle_username and self.kaggle_key)

    @property
    def dsn(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # los valores vienen del entorno
