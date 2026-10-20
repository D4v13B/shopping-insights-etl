"""Punto de entrada: `shopping-etl run` y `shopping-etl worker`."""

from enum import StrEnum
from typing import Annotated

import typer

from shopping_etl.config import get_settings
from shopping_etl.logs import configure_logging, get_logger
from shopping_etl.pipeline import AlreadyRunningError, execute
from shopping_etl.worker import run_worker

app = typer.Typer(help="ETL de Shopping Insights", no_args_is_help=True)
log = get_logger(__name__)


class Trigger(StrEnum):
    cli = "cli"
    startup = "startup"


@app.callback()
def _setup() -> None:
    configure_logging(get_settings().log_level)


@app.command()
def run(
    trigger: Annotated[Trigger, typer.Option(help="Origen de la ejecución")] = Trigger.cli,
) -> None:
    """Ejecuta el ETL una vez (idempotente)."""
    try:
        execute(get_settings(), trigger=trigger.value)
    except AlreadyRunningError as exc:
        log.error("etl_ya_en_curso", error=str(exc))
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        raise typer.Exit(code=1) from exc


@app.command()
def worker() -> None:
    """Escucha solicitudes de la API (LISTEN etl_requested) y las ejecuta de una en una."""
    run_worker(get_settings())


if __name__ == "__main__":
    app()
