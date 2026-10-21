# Datos

`shopping_trends.csv` es una copia de respaldo del dataset
[Customer Shopping Trends Dataset](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset)
(Sourav Banerjee, Kaggle, versión 2).

- Según su autor, es un **dataset sintético** generado con ChatGPT con fines de aprendizaje.
- Kaggle lo publica con la licencia "Other (specified in description)"; la descripción no impone
  restricciones explícitas. Se incluye aquí solo para que el ETL funcione sin conexión, con atribución
  a su autor y sin uso comercial.
- El ETL descarga la versión de Kaggle con `kagglehub` cuando existen `KAGGLE_USERNAME` y
  `KAGGLE_KEY` (en Docker vienen del `.env` de `shopping-insights-api`); si no, o si la descarga
  falla, usa **este archivo**. Está versionado en git para que la prueba técnica no dependa solo de
  la API de Kaggle (~3 900 filas, archivo `shopping_trends.csv` en esta carpeta).
