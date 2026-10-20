# 0003 · ETL en capas raw → staging → analytics (sin dbt)

**Estado:** Aceptada

## Contexto
Hay que validar, limpiar y modelar, y poder explicar qué llegó, qué se descartó y por qué.

## Opciones
1. **Python en capas** (raw → staging → analytics) con transformaciones como funciones puras.
2. dbt: el estándar para transformaciones SQL, pero agrega un runtime, un proyecto y una curva de
   configuración desproporcionados para una sola fuente de 3,900 filas.
3. Cargar directo al modelo final: más simple, pero sin trazabilidad.

## Decisión
Tres capas en PostgreSQL, alimentadas por el ETL en Python:
- `raw`: copia literal en texto, para auditar.
- `staging`: filas válidas y tipadas, más `rejected_rows` con su motivo.
- `analytics`: estrella y vistas.

## Consecuencias
- Se puede responder "¿por qué falta esta fila?" consultando `staging.rejected_rows`.
- Las transformaciones se testean sin base de datos (`transform.py` al 100% de cobertura).
- Con más fuentes, migrar `staging → analytics` a dbt es directo, porque las capas ya existen.
