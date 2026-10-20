"""Ciclo de vida de public.etl_runs: requested -> running -> success | failed."""

import json
from typing import Any
from uuid import UUID

import psycopg

Conn = psycopg.Connection[Any]


def fail_orphans(conn: Conn) -> int:
    """Marca como failed las ejecuciones en running. Solo se llama con el advisory lock tomado:
    si nadie más lo tiene, cualquier fila en running quedó huérfana (proceso caído)."""
    cur = conn.execute(
        """
        UPDATE etl_runs
           SET status = 'failed', finished_at = now(),
               error = 'Ejecución huérfana: el proceso terminó sin cerrarla'
         WHERE status = 'running'
        """
    )
    return cur.rowcount


def pending_requests(conn: Conn) -> list[UUID]:
    rows = conn.execute(
        "SELECT id FROM etl_runs WHERE status = 'requested' ORDER BY requested_at"
    ).fetchall()
    return [row[0] for row in rows]


def claim(conn: Conn, run_id: UUID) -> bool:
    """requested -> running. Devuelve False si la fila ya no está pendiente."""
    cur = conn.execute(
        """
        UPDATE etl_runs SET status = 'running', started_at = now()
         WHERE id = %s AND status = 'requested'
        """,
        (run_id,),
    )
    return cur.rowcount == 1


def claim_pending_or_create(conn: Conn, trigger: str) -> UUID:
    """Para `shopping-etl run`: adopta una solicitud pendiente si existe; si no, crea una fila.
    (El índice único parcial impide crear una segunda ejecución activa.)"""
    for run_id in pending_requests(conn):
        if claim(conn, run_id):
            return run_id
    row = conn.execute(
        """
        INSERT INTO etl_runs (status, trigger, started_at)
        VALUES ('running', %s, now()) RETURNING id
        """,
        (trigger,),
    ).fetchone()
    assert row is not None
    return UUID(str(row[0]))


def mark_success(
    conn: Conn,
    run_id: UUID,
    *,
    source: str,
    rows_read: int,
    rows_valid: int,
    rows_rejected: int,
    duration_ms: int,
    quality_report: dict[str, Any],
) -> None:
    conn.execute(
        """
        UPDATE etl_runs
           SET status = 'success', finished_at = now(), source = %s,
               rows_read = %s, rows_valid = %s, rows_rejected = %s,
               duration_ms = %s, quality_report = %s::jsonb, error = NULL
         WHERE id = %s
        """,
        (
            source,
            rows_read,
            rows_valid,
            rows_rejected,
            duration_ms,
            json.dumps(quality_report, default=str),
            run_id,
        ),
    )


def mark_failed(conn: Conn, run_id: UUID, *, error: str, duration_ms: int) -> None:
    conn.execute(
        """
        UPDATE etl_runs
           SET status = 'failed', finished_at = now(), error = %s, duration_ms = %s
         WHERE id = %s
        """,
        (error[:2000], duration_ms, run_id),
    )
