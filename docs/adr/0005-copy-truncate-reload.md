# 0005 · COPY con truncate-reload transaccional

**Estado:** Aceptada

## Contexto
El ETL debe ser idempotente y no puede dejar la base en un estado intermedio si falla.

## Opciones
1. **TRUNCATE + COPY de todas las capas en una sola transacción.**
2. Upsert por clave natural (`INSERT … ON CONFLICT`): necesario con cargas incrementales, pero no hay
   fechas ni lotes.
3. INSERT fila a fila: lento y sin ventajas aquí.

## Decisión
En una transacción: `TRUNCATE` de las 8 tablas, `COPY FROM STDIN` (psycopg 3) de cada capa,
`REFRESH MATERIALIZED VIEW` de las 3 vistas y el `UPDATE etl_runs → success`.

## Consecuencias
- N ejecuciones dan el mismo estado; las *surrogate keys* son deterministas.
- Un fallo en cualquier punto hace rollback total; un test lo verifica con un error inducido en mitad
  del `COPY`.
- `TRUNCATE` toma un lock exclusivo: durante la carga (~0.4 s) las lecturas esperan. Aceptable aquí;
  con volumen se cargaría en tablas paralelas y se intercambiarían, o se pasaría a carga incremental.
- `REFRESH … CONCURRENTLY` no aporta nada dentro de la misma transacción del `TRUNCATE`, así que se usa
  `REFRESH` simple.
