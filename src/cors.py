"""Настройка CORS из окружения: безопаснее, чем всегда ``*`` + credentials."""

import os


def cors_allow_origins() -> list[str]:
    """Список origin. ``CORS_ORIGINS=*`` или пусто — разрешить все (только dev)."""
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def cors_allow_credentials() -> bool:
    """С ``allow_origins=['*']`` credentials в браузере недопустимы — отключаем."""
    return cors_allow_origins() != ["*"]
