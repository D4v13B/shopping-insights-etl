# 0004 · Polars + Pandera en lugar de Pandas

**Estado:** Aceptada

## Contexto
El ETL necesita transformaciones expresivas y validación por contrato que identifique cada fila
inválida.

## Opciones
1. **Polars + Pandera** (backend Polars).
2. Pandas + Pandera: más conocido, pero con una API más propensa a errores silenciosos (copias,
   índices, `SettingWithCopyWarning`) y más lento.
3. Validación manual con `if`: frágil y difícil de mantener.

## Decisión
Polars para transformar (expresiones puras y tipado estricto) y Pandera con `lazy=True` para
validar.

## Consecuencias
- Riesgo detectado en la planificación: el backend Polars de Pandera podría no devolver el índice de
  la fila que falla. Se mitigó numerando las filas (`row_number`) antes de validar y se verificó que
  `failure_cases` sí trae el índice con Pandera 0.34 y Polars 2.0.
- Los valores que no se pueden convertir a número se detectan en un paso previo con
  `cast(strict=False)`, porque un error de tipo en Pandera es a nivel de columna, no de fila.
- `replace_strict` hace que un valor de dominio desconocido falle en vez de quedar nulo en silencio.
