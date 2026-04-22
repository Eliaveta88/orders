"""HTTP client for warehouse service (stock reservations)."""

from __future__ import annotations

import logging

import httpx

from src.config import integration_cfg

logger = logging.getLogger(__name__)


async def reserve_stock(
    product_id: int,
    quantity: int,
    order_id: int,
    unit_type: str = "unit",
) -> dict:
    """POST /api/v1/warehouse/stock/reserve. Raises httpx.HTTPError on transport errors."""
    url = f"{integration_cfg.warehouse_base_url}/api/v1/warehouse/stock/reserve"
    timeout = httpx.Timeout(integration_cfg.http_timeout_seconds)
    payload = {
        "product_id": product_id,
        "quantity": quantity,
        "order_id": order_id,
        "unit_type": unit_type,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


async def release_stock(reservation_id: int) -> dict | None:
    """POST /api/v1/warehouse/stock/release. Best-effort; returns None on 404, raises on transport errors."""
    url = f"{integration_cfg.warehouse_base_url}/api/v1/warehouse/stock/release"
    timeout = httpx.Timeout(integration_cfg.http_timeout_seconds)
    payload = {"reservation_id": reservation_id}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
