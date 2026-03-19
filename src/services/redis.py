"""Redis service for orders: order status caching and cross-service events."""

from __future__ import annotations

import json

import redis.asyncio as aioredis

from src.config import redis_cfg

_KEY_PREFIX = "orders"
_ORDER_CACHE = f"{_KEY_PREFIX}:order:"
_ORDER_STATUS = f"{_KEY_PREFIX}:status:"
_CHANNEL_ORDER = f"{_KEY_PREFIX}:events:status"

_ORDER_CACHE_TTL = 300  # 5 min
_STATUS_CACHE_TTL = 120  # 2 min

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis connection (lazy-init)."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            redis_cfg.url,
            decode_responses=redis_cfg.decode_responses,
            socket_timeout=redis_cfg.socket_timeout_seconds,
            socket_connect_timeout=redis_cfg.socket_connect_timeout_seconds,
            health_check_interval=redis_cfg.health_check_interval_seconds,
            max_connections=redis_cfg.max_connections,
        )
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ---------------------------------------------------------------------------
# Order cache
# ---------------------------------------------------------------------------


async def cache_order(order_id: int, data: dict) -> None:
    """Cache full order data."""
    r = await get_redis()
    await r.set(
        f"{_ORDER_CACHE}{order_id}",
        json.dumps(data, default=str),
        ex=_ORDER_CACHE_TTL,
    )


async def get_cached_order(order_id: int) -> dict | None:
    """Return cached order or None on miss."""
    r = await get_redis()
    raw = await r.get(f"{_ORDER_CACHE}{order_id}")
    return json.loads(raw) if raw else None


async def invalidate_order(order_id: int) -> None:
    """Remove order from cache (after mutation)."""
    r = await get_redis()
    await r.delete(f"{_ORDER_CACHE}{order_id}")
    await r.delete(f"{_ORDER_STATUS}{order_id}")


# ---------------------------------------------------------------------------
# Order status (lightweight key for quick status lookups)
# ---------------------------------------------------------------------------


async def set_order_status(order_id: int, status: str) -> None:
    """Cache current order status for quick lookup without DB query."""
    r = await get_redis()
    await r.set(f"{_ORDER_STATUS}{order_id}", status, ex=_STATUS_CACHE_TTL)


async def get_order_status(order_id: int) -> str | None:
    """Return cached status string or None."""
    r = await get_redis()
    return await r.get(f"{_ORDER_STATUS}{order_id}")


# ---------------------------------------------------------------------------
# Pub/Sub  (order status events for other services)
# ---------------------------------------------------------------------------


async def publish_order_event(event: dict) -> int:
    """Publish order status change event.

    Warehouse listens for ``confirmed`` to trigger stock reservation.
    Logistics listens for ``in_delivery`` to plan routes.
    Finance listens for ``closed`` to finalize invoices.
    """
    r = await get_redis()
    return await r.publish(_CHANNEL_ORDER, json.dumps(event, default=str))


async def subscribe_order_events():
    """Return an async pubsub subscription for order events.

    Usage::

        sub = await subscribe_order_events()
        async for message in sub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                ...
    """
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(_CHANNEL_ORDER)
    return pubsub
