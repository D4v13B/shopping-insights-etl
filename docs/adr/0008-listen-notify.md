# 0008 · Disparo del ETL con LISTEN/NOTIFY

**Estado:** Aceptada

## Contexto
La API (TypeScript) debe poder disparar el ETL (Python) en otro contenedor.

## Opciones
1. **LISTEN/NOTIFY de PostgreSQL**, más la tabla `etl_runs` como cola durable.
2. Un endpoint HTTP en el ETL: otro servidor, otro puerto y otro punto de autenticación.
3. Redis, BullMQ o SQS: una pieza de infraestructura más para un solo tipo de trabajo.

## Decisión
La API inserta la solicitud y hace `pg_notify` en la misma transacción. El `etl-worker` escucha y
procesa. La fila en `etl_runs` es la fuente de verdad; el `NOTIFY` solo despierta al worker.

## Consecuencias
- Sin infraestructura extra; la API no necesita conocer al worker.
- `NOTIFY` no se encola: el worker procesa las filas `requested` al arrancar, al reconectar y cada
  30 s, así que una notificación perdida solo retrasa la ejecución.
- La concurrencia la controlan un índice único parcial (409 en la API) y un advisory lock (en el ETL).
- Con varios workers o muchos tipos de trabajo convendría una cola real.
