"""Worker: escucha `NOTIFY etl_requested` y procesa las solicitudes pendientes de la API."""

import signal
import threading
import time
from types import FrameType

import psycopg

from shopping_etl import runs
from shopping_etl.config import Settings
from shopping_etl.logs import get_logger
from shopping_etl.pipeline import AlreadyRunningError, execute

log = get_logger(__name__)

CHANNEL = "etl_requested"
MAX_BACKOFF_SECONDS = 60.0


def process_pending(settings: Settings) -> None:
    """Procesa todas las solicitudes `requested`. Se llama al arrancar, tras cada NOTIFY y
    periódicamente: un NOTIFY enviado sin nadie escuchando se pierde, la fila no."""
    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        pending = runs.pending_requests(conn)
    for run_id in pending:
        try:
            execute(settings, trigger="api", run_id=run_id)
        except AlreadyRunningError:
            log.info("etl_ocupado_reintento_luego", run_id=str(run_id))
            return
        except Exception:  # ya quedó registrado como failed; seguir con la siguiente
            continue


def run_worker(settings: Settings) -> None:
    stop = threading.Event()

    def handle_signal(signum: int, _frame: FrameType | None) -> None:
        log.info("worker_apagando", signal=signal.Signals(signum).name)
        stop.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    backoff = 1.0
    while not stop.is_set():
        try:
            with psycopg.connect(settings.dsn, autocommit=True) as conn:
                conn.execute(f"LISTEN {CHANNEL}")
                log.info("worker_escuchando", channel=CHANNEL)
                backoff = 1.0
                process_pending(settings)
                last_poll = time.monotonic()
                while not stop.is_set():
                    # Timeout corto para reaccionar rápido a SIGTERM.
                    notified = any(True for _ in conn.notifies(timeout=1.0, stop_after=1))
                    if notified or time.monotonic() - last_poll >= settings.worker_poll_seconds:
                        if notified:
                            log.info("notificacion_recibida")
                        process_pending(settings)
                        last_poll = time.monotonic()
        except psycopg.OperationalError as exc:
            log.warning("worker_sin_conexion", error=str(exc), reintento_en_s=backoff)
            stop.wait(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
    log.info("worker_detenido")
