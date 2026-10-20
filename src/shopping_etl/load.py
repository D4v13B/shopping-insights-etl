"""Carga transaccional: TRUNCATE + COPY de las tres capas + REFRESH, todo o nada."""

from collections.abc import Callable
from typing import Any, Final

import polars as pl
import psycopg
from psycopg import sql

from shopping_etl.logs import get_logger
from shopping_etl.model import StarModel

log = get_logger(__name__)

# Orden de COPY respetando las FKs (dimensiones antes que hechos).
TRUNCATE_TABLES: Final = (
    "raw.shopping_trends",
    "staging.purchases",
    "staging.rejected_rows",
    "analytics.fact_purchase",
    "analytics.dim_customer",
    "analytics.dim_product",
    "analytics.dim_location",
    "analytics.dim_payment",
)
MATERIALIZED_VIEWS: Final = (
    "analytics.mv_sales_cube",
    "analytics.mv_sales_by_state",
    "analytics.mv_product_ranking",
)


def _ident(qualified: str) -> sql.Identifier:
    return sql.Identifier(*qualified.split("."))


def copy_frame(cur: psycopg.Cursor[Any], table: str, df: pl.DataFrame) -> int:
    """COPY ... FROM STDIN con las columnas del DataFrame (sus nombres = columnas de la tabla)."""
    stmt = sql.SQL("COPY {} ({}) FROM STDIN").format(
        _ident(table), sql.SQL(", ").join(sql.Identifier(c) for c in df.columns)
    )
    with cur.copy(stmt) as copy:
        for row in df.iter_rows():
            copy.write_row(row)
    return df.height


def load(
    conn: psycopg.Connection[Any],
    *,
    run_id: str,
    raw: pl.DataFrame,
    staging: pl.DataFrame,
    rejected: pl.DataFrame,
    model: StarModel,
    on_success: Callable[[psycopg.Connection[Any]], None],
) -> dict[str, int]:
    """Ejecuta toda la carga en UNA transacción. `on_success` corre dentro de la misma
    transacción (marca la ejecución como success), así el estado y los datos son atómicos.
    Si algo falla, psycopg hace rollback y la base queda como estaba."""
    counts: dict[str, int] = {}
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            sql.SQL("TRUNCATE {}").format(sql.SQL(", ").join(_ident(t) for t in TRUNCATE_TABLES))
        )
        run = pl.lit(run_id)
        counts["raw.shopping_trends"] = copy_frame(
            cur, "raw.shopping_trends", raw.with_columns(run.alias("_run_id"))
        )
        counts["staging.purchases"] = copy_frame(
            cur, "staging.purchases", staging.with_columns(run.alias("_run_id"))
        )
        counts["staging.rejected_rows"] = copy_frame(
            cur, "staging.rejected_rows", rejected.with_columns(run.alias("run_id"))
        )
        for table, df in (
            ("analytics.dim_customer", model.dim_customer),
            ("analytics.dim_product", model.dim_product),
            ("analytics.dim_location", model.dim_location),
            ("analytics.dim_payment", model.dim_payment),
            ("analytics.fact_purchase", model.fact_purchase),
        ):
            counts[table] = copy_frame(cur, table, df)
        for view in MATERIALIZED_VIEWS:
            cur.execute(sql.SQL("REFRESH MATERIALIZED VIEW {}").format(_ident(view)))
        on_success(conn)
    log.info("carga_completa", counts=counts)
    return counts
