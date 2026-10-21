# 0001 · Dataset Customer Shopping Trends

**Estado:** Aceptada

## Contexto
El proyecto necesita un dataset público de comercio o retail para construir un flujo end-to-end. La
empresa es una cadena de moda (H&M Panamá / Hola Moda), así que el dataset debía permitir hablar de
categorías, temporadas, clientes y canales de pago.

## Opciones
1. **Customer Shopping Trends** (Kaggle): ropa, calzado y accesorios, con temporada, cliente y pago.

## Decisión
Customer Shopping Trends. Su dominio coincide con el negocio, el volumen permite una demo local en
segundos y sus defectos (sin fechas, columnas redundantes, sesgos) dan material real para mostrar
validación y calidad de datos.

## Consecuencias
- No hay series de tiempo: el análisis temporal se limita a temporadas (ver
  [data-quality.md](../data-quality.md)).
- Es sintético: los insights se presentan con avisos explícitos y no como conclusiones de negocio.
- Con 3,900 filas, el rendimiento se demuestra con buen diseño (cubo, índices, `COPY`) y no con volumen.
