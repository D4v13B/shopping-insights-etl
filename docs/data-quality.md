# Calidad de datos

Hallazgos del perfilado de `shopping_trends.csv` (versión 2 del dataset en Kaggle). Las cifras salen
del reporte que el ETL guarda en cada ejecución (`etl_runs.quality_report`, vista **Calidad de
datos**) y de la API.

## Fuente y licencia

- **Dataset**: [Customer Shopping Trends Dataset](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset),
  de Sourav Banerjee.
- **Naturaleza**: según su autor, es **sintético**, generado con ChatGPT con fines de aprendizaje.
- **Licencia**: Kaggle la lista como "Other (specified in description)" y la descripción no impone
  restricciones explícitas. El CSV se versiona en `data/` con atribución, solo como respaldo para
  ejecutar sin conexión ni credenciales.

## Resumen

| Aspecto | Resultado |
|---|---|
| Volumen | 3,900 filas × 19 columnas |
| Filas válidas / rechazadas | 3,900 / 0 |
| Valores nulos | Ninguno |
| `Customer ID` | Único en todas las filas: cada fila es un cliente con una compra observada |
| Rangos | Edad 18–70 · monto 20–100 USD · rating 2.5–5.0 · compras previas 1–50 |
| Cardinalidad | 25 productos · 4 categorías · 25 colores · 4 tallas · 4 temporadas · 50 estados · 6 métodos de pago · 6 tipos de envío |

## Hallazgos y cómo se tratan

### 1. `Discount Applied` y `Promo Code Used` son idénticas

Coinciden en las 3,900 filas (0 diferencias). Son redundantes.

**Tratamiento**: se unifican en `promo_used`. El ETL verifica la igualdad en cada carga y la reporta;
si algún día difirieran, `promo_used` es el OR de ambas y el reporte muestra cuántas filas difieren.

### 2. Frecuencias de compra con sinónimos

`Frequency of Purchases` tiene 7 valores, pero representan 5 frecuencias:

| Original | Normalizada | Días | Compras/año |
|---|---|---|---|
| Weekly | weekly | 7 | 52.14 |
| Fortnightly, Bi-Weekly | biweekly | 14 | 26.07 |
| Monthly | monthly | 30 | 12.17 |
| Quarterly, Every 3 Months | quarterly | 90 | 4.06 |
| Annually | annually | 365 | 1.00 |

**Tratamiento**: diccionario de sinónimos en `reference.py`. Una frecuencia desconocida hace fallar la
validación de la fila, no la transformación.

### 3. No hay fechas

No existe ninguna columna de fecha: no hay series de tiempo, estacionalidad mensual ni recencia. La
única dimensión temporal es `Season`.

**Tratamiento**: el dashboard compara temporadas en lugar de mostrar tendencias. La segmentación usa
la frecuencia declarada como *proxy* de actividad ("En riesgo" = historial relevante con frecuencia
anual o trimestral). La vista Resumen lo advierte de forma explícita.

### 4. Sesgo de género, suscripción y promoción

| Grupo | Clientes | Suscritos | Usaron promoción |
|---|---|---|---|
| Hombres | 2,652 | 1,053 (39.7%) | 1,677 (63.2%) |
| Mujeres | 1,248 | **0** | **0** |
| Suscritos | 1,053 | — | **1,053 (100%)** |

- Ninguna mujer está suscrita ni usó una promoción.
- **Todos** los suscritos usaron promoción. Entre los no suscritos, solo hombres la usaron (624).
- Hay el doble de hombres que de mujeres.

Es un artefacto de cómo se generó el dataset, no un comportamiento creíble de clientes reales.

**Tratamiento**: avisos explícitos en la vista Clientes y en Calidad de datos. Las comparaciones por
género también se muestran con promedios (ticket, rating) y no solo con totales.

### 5. Una compra por cliente

Como `Customer ID` es único, "órdenes" y "clientes" valen lo mismo en cualquier corte.
`Previous Purchases` es un contador histórico, no compras presentes en el archivo.

**Tratamiento**: la tarjeta de órdenes lo aclara (`= clientes: 1 compra por cliente`). El cubo puede
sumar `customers` de forma aditiva gracias a esta propiedad; con datos reales habría que contar
clientes distintos en la tabla de hechos.

### 6. `Payment Method` frente a `Preferred Payment Method`

Ambas columnas existen y difieren en 3,283 de las 3,900 filas (84%). La descripción original del dataset define `Payment
Method` como el método "preferido", lo que es ambiguo.

**Tratamiento**: `payment_method` (de la compra) va a `dim_payment` y es el que filtra la API;
`preferred_payment_method` queda como atributo del cliente en `dim_customer`.

### 7. Distribuciones casi uniformes

Las ventas por estado (USD 3,437 a 5,784), por producto y por temporada son muy parejas, y el rating
promedio ronda 3.75 en casi cualquier corte. Es otra señal de datos sintéticos: los rankings
existen, pero las diferencias son pequeñas y no deberían sobreinterpretarse.

## Segmentación resultante

| Segmento | Clientes | % |
|---|---|---|
| Ocasionales | 1,625 | 41.7% |
| Leales | 860 | 22.1% |
| En riesgo | 554 | 14.2% |
| Potenciales | 432 | 11.1% |
| Campeones | 429 | 11.0% |

Umbrales (terciles): valor anual estimado 286.91 y 1,156.15 USD; compras previas 17 y 33.
