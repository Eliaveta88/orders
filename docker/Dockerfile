# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependencies
COPY pyproject.toml .
RUN uv sync --no-dev

# Copy source
COPY src ./src

EXPOSE 8000

ENV PYTHONPATH=/app
ENV GRANIAN_HOST=0.0.0.0
ENV GRANIAN_PORT=8000

# Alembic migrations on every container start, then ASGI server (fail fast if migrate fails)
ENTRYPOINT ["/bin/sh", "-c", "set -e && uv run alembic -c src/database/alembic.ini upgrade head && exec uv run granian --interface asgi src.main:app"]
