"""HTTP client for identity service (client display name)."""

from __future__ import annotations

import logging

import httpx

from src.config import integration_cfg

logger = logging.getLogger(__name__)


async def fetch_user_display_name(user_id: int) -> str | None:
    """GET /api/v1/identity/users/{id}; returns username or None if 404."""
    url = f"{integration_cfg.identity_base_url}/api/v1/identity/users/{user_id}"
    timeout = httpx.Timeout(integration_cfg.http_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()
            return str(data.get("username", "")) or None
    except httpx.HTTPError as exc:
        logger.warning("identity.fetch_user_failed user_id=%s err=%s", user_id, exc)
        raise
