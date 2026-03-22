"""Business logic actions for orders endpoints."""

import logging
from datetime import datetime

from fastapi import HTTPException, status

from src.routers.v1.orders.dal import OrderDAL
from src.routers.v1.orders.schemas import (
    OrderListResponse,
    OrderResponse,
    OrderSummaryResponse,
    CreateOrderRequest,
    UpdateOrderStatusRequest,
)
from src.services.redis import (
    cache_order,
    get_cached_order,
    invalidate_order,
    publish_order_event,
    set_order_status,
)


logger = logging.getLogger(__name__)


async def _list_orders(
    dal: OrderDAL,
    skip: int = 0,
    limit: int = 50,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> OrderListResponse:
    """Get orders list."""
    orders = await dal.list_orders(
        skip=skip,
        limit=limit,
        created_from=created_from,
        created_to=created_to,
    )
    total = await dal.count_orders(created_from=created_from, created_to=created_to)
    return OrderListResponse(
        items=[OrderSummaryResponse(**o) for o in orders],
        total=total,
        skip=skip,
        limit=limit,
    )


async def _get_order_detail(
    order_id: int,
    dal: OrderDAL,
) -> OrderResponse:
    """Get order details."""
    try:
        cached = await get_cached_order(order_id)
        if cached:
            logger.info("orders.cache_hit", extra={"order_id": order_id})
            return OrderResponse(**cached)
    except Exception:
        logger.exception("orders.cache_read_failed", extra={"order_id": order_id})

    order = await dal.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    try:
        await cache_order(order_id, order)
    except Exception:
        logger.exception("orders.cache_write_failed", extra={"order_id": order_id})

    return OrderResponse(**order)


async def _create_order(
    order_in: CreateOrderRequest,
    dal: OrderDAL,
) -> OrderResponse:
    """Create new order."""
    order = await dal.create(order_in)
    order_id = order.get("id")
    order_status = order.get("status")

    if order_id is not None:
        try:
            await cache_order(order_id, order)
            if order_status is not None:
                await set_order_status(order_id, str(order_status))
        except Exception:
            logger.exception("orders.post_create_cache_failed", extra={"order_id": order_id})

        try:
            await publish_order_event(
                {
                    "order_id": order_id,
                    "status": order_status,
                    "source": "orders",
                    "event_type": "order_created",
                }
            )
        except Exception:
            logger.exception("orders.publish_created_failed", extra={"order_id": order_id})

    return OrderResponse(**order)


async def _update_order_status(
    order_id: int,
    status_req: UpdateOrderStatusRequest,
    dal: OrderDAL,
) -> OrderResponse:
    """Update order status."""
    order = await dal.update_status(order_id, status_req.status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    new_status = status_req.status
    try:
        await set_order_status(order_id, str(new_status))
        await invalidate_order(order_id)
    except Exception:
        logger.exception("orders.post_status_update_cache_failed", extra={"order_id": order_id})

    try:
        await publish_order_event(
            {
                "order_id": order_id,
                "status": new_status,
                "source": "orders",
                "event_type": "order_status_updated",
            }
        )
    except Exception:
        logger.exception("orders.publish_status_updated_failed", extra={"order_id": order_id})

    return OrderResponse(**order)
