"""Integración contra un PostgreSQL migrado (con roles). Requiere TEST_DATABASE_URL_ETL y
TEST_DATABASE_URL_ADMIN; si no están, se omiten."""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest

from shopping_etl import pipeline
from shopping_etl.config import Settings
from shopping_etl.pipeline import ETL_LOCK_KEY, AlreadyRunningError, execute
from shopping_etl.worker import process_pending
from tests.conftest import DATASET

ETL_URL = os.environ.get("TEST_DATABASE_URL_ETL")
ADMIN_URL = os.environ.get("TEST_DATABASE_URL_ADMIN")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not (ETL_URL and ADMIN_URL), reason="sin base de datos de pruebas"),
]


@pytest.fixture
def settings() -> Settings:
    return Settings(DATABASE_URL_ETL=ETL_URL, ETL_FALLBACK_CSV=DATASET)  # type: ignore[arg-type]


@pytest.fixture
def admin() -> Iterator[psycopg.Connection[Any]]:
    assert ADMIN_URL
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute("DELETE FROM etl_runs")
        yield conn
        conn.execute("DELETE FROM etl_runs")


def counts(conn: psycopg.Connection[Any]) -> tuple[Any, ...]:
    row = conn.execute(
        """
        SELECT (SELECT count(*) FROM raw.shopping_trends),
               (SELECT count(*) FROM staging.purchases),
               (SELECT count(*) FROM analytics.fact_purchase),
               (SELECT sum(revenue) FROM analytics.mv_sales_cube),
               (SELECT count(*) FROM analytics.mv_sales_by_state)
        """
    ).fetchone()
    assert row is not None
    return tuple(row)


def statuses(conn: psycopg.Connection[Any]) -> list[str]:
    return [r[0] for r in conn.execute("SELECT status FROM etl_runs ORDER BY requested_at")]


def test_run_is_idempotent(settings: Settings, admin: psycopg.Connection[Any]) -> None:
    execute(settings, trigger="cli")
    first = counts(admin)
    execute(settings, trigger="cli")
    assert counts(admin) == first == (3900, 3900, 3900, 233081, 50)
    assert statuses(admin) == ["success", "success"]
    report = admin.execute("SELECT quality_report FROM etl_runs LIMIT 1").fetchone()
    assert report is not None and report[0]["discount_equals_promo"]["equal"] is True


def test_failure_rolls_back_and_keeps_previous_data(
    settings: Settings, admin: psycopg.Connection[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    execute(settings, trigger="cli")
    before = counts(admin)

    original_copy = pipeline.load.__globals__["copy_frame"]

    def failing_copy(cur: Any, table: str, df: Any) -> int:
        if table == "analytics.fact_purchase":
            raise RuntimeError("fallo inducido")
        return int(original_copy(cur, table, df))

    monkeypatch.setitem(pipeline.load.__globals__, "copy_frame", failing_copy)
    with pytest.raises(RuntimeError, match="fallo inducido"):
        execute(settings, trigger="cli")

    assert counts(admin) == before
    assert statuses(admin) == ["success", "failed"]
    err = admin.execute("SELECT error FROM etl_runs WHERE status = 'failed'").fetchone()
    assert err is not None and "fallo inducido" in err[0]


def test_orphan_running_rows_are_failed_on_next_run(
    settings: Settings, admin: psycopg.Connection[Any]
) -> None:
    admin.execute("INSERT INTO etl_runs (status, trigger) VALUES ('running', 'api')")
    execute(settings, trigger="cli")
    assert sorted(statuses(admin)) == ["failed", "success"]


def test_pending_request_is_adopted_by_cli_run(
    settings: Settings, admin: psycopg.Connection[Any]
) -> None:
    admin.execute("INSERT INTO etl_runs (status, trigger) VALUES ('requested', 'api')")
    execute(settings, trigger="cli")
    rows = admin.execute("SELECT status, trigger FROM etl_runs").fetchall()
    assert rows == [("success", "api")]


def test_worker_processes_pending_requests(
    settings: Settings, admin: psycopg.Connection[Any]
) -> None:
    admin.execute("INSERT INTO etl_runs (status, trigger) VALUES ('requested', 'api')")
    process_pending(settings)
    assert statuses(admin) == ["success"]


def test_concurrent_run_is_refused(settings: Settings, admin: psycopg.Connection[Any]) -> None:
    assert ETL_URL
    with psycopg.connect(ETL_URL, autocommit=True) as other:
        other.execute("SELECT pg_advisory_lock(%s)", (ETL_LOCK_KEY,))
        with pytest.raises(AlreadyRunningError):
            execute(settings, trigger="cli")
    assert statuses(admin) == []


def test_unknown_request_id_is_skipped(settings: Settings, admin: psycopg.Connection[Any]) -> None:
    import uuid

    assert execute(settings, trigger="api", run_id=uuid.uuid4()) is None


def test_fixture_dataset_exists() -> None:
    assert Path(DATASET).is_file()
