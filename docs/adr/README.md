# Architecture Decision Records

Cada ADR registra una decisión con su contexto, las opciones evaluadas y sus consecuencias.
Formato: Estado · Contexto · Opciones · Decisión · Consecuencias.

La numeración es común a los tres repositorios del proyecto; cada ADR vive en el repo al que
afecta. Los de otros repos enlazan a GitHub.

| # | Decisión | Repo | Estado |
|---|---|---|---|
| [0001](0001-dataset-shopping-trends.md) | Dataset Customer Shopping Trends | etl | Aceptada |
| [0002](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0002-postgres-estrella-cubo.md) | PostgreSQL con esquema estrella y cubo materializado | api | Aceptada |
| [0003](0003-etl-en-capas.md) | ETL en capas raw → staging → analytics (sin dbt) | etl | Aceptada |
| [0004](0004-polars-pandera.md) | Polars + Pandera en lugar de Pandas | etl | Aceptada |
| [0005](0005-copy-truncate-reload.md) | COPY con truncate-reload transaccional | etl | Aceptada |
| [0006](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0006-drizzle-dueno-del-esquema.md) | Drizzle como único dueño del esquema | api | Aceptada |
| [0007](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0007-hono-zod-openapi.md) | Hono + zod-openapi en lugar de Elysia | api | Aceptada |
| [0008](0008-listen-notify.md) | Disparo del ETL con LISTEN/NOTIFY | etl | Aceptada |
| [0009](https://github.com/D4v13B/shopping-insights-web/blob/main/docs/adr/0009-cliente-generado-openapi.md) | Cliente tipado generado desde OpenAPI | web | Aceptada |
| [0010](https://github.com/D4v13B/shopping-insights-web/blob/main/docs/adr/0010-filtros-en-la-url.md) | Estado de los filtros en la URL | web | Aceptada |
| [0011](https://github.com/D4v13B/shopping-insights-web/blob/main/docs/adr/0011-mapa-d3-geo.md) | Mapa con d3-geo en lugar de una librería de mapas | web | Aceptada |
| [0012](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0012-monorepo-bun-compose.md) | Monorepo con Bun workspaces y Docker Compose | api | Reemplazada por 0016 |
| [0013](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0013-vista-v-purchases.md) | Vista `v_purchases` para las consultas sobre la estrella | api | Aceptada |
| [0014](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0014-versiones-y-runtimes.md) | Versiones y runtimes fijados (TS 5.9, Table 8, web en Node) | api | Aceptada |
| [0015](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0015-minimo-privilegio-db.md) | Roles de base de datos con mínimo privilegio | api | Aceptada |
| [0016](https://github.com/D4v13B/shopping-insights-api/blob/main/docs/adr/0016-tres-repositorios.md) | Tres repositorios: ETL, API y frontend | api | Aceptada |
