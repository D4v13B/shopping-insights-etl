# syntax=docker/dockerfile:1
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ETL_FALLBACK_CSV=/app/data/shopping_trends.csv

WORKDIR /app
# Primero solo las dependencias: esta capa se reutiliza mientras no cambie el lockfile.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
COPY data/shopping_trends.csv ./data/shopping_trends.csv

RUN useradd --system --uid 10001 --home-dir /home/etl --create-home etl
USER etl
ENTRYPOINT ["shopping-etl"]
CMD ["run", "--trigger", "startup"]
