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

ENV GRANIAN_BIND=0.0.0.0:8000

# Run migrations then start Granian
ENTRYPOINT ["/bin/sh", "-c", "uv run alembic -c src/database/alembic.ini upgrade head && exec uv run granian --interface asgi src.main:app"]
