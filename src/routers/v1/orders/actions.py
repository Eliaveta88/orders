"""Business logic actions for orders endpoints."""

import logging
from datetime import datetime
from decimal import Decimal

import httpx
from fastapi import HTTPException, status

from src.routers.v1.orders.dal import OrderDAL
from src.services.catalog_client import fetch_product
from src.services.identity_client import fetch_user_display_name
from src.services.warehouse_client import release_stock, reserve_stock
from src.routers.v1.orders.schemas import (
    OrderListResponse,
    OrderResponse,
    OrderSummaryResponse,
    CreateOrderRequest,
    UpdateOrderStatusRequest,
)
from src.services.redis import (
    cache_order,
    clear_order_reservations,
    get_cached_order,
    get_order_reservations,
    invalidate_order,
    publish_order_event,
    set_order_status,
    store_order_reservations,
)

_CANCELLED_STATUSES = {"cancelled"}


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
    """Create new order (resolve catalog prices/names and identity client label)."""
    resolved_lines: list[tuple[Decimal, str]] = []
    for item in order_in.items:
        try:
            product = await fetch_product(item.product_id)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Catalog service unavailable: {exc}",
            ) from exc
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} not found in catalog",
            )
        unit_price = Decimal(str(product["price"]))
        product_name = str(product["name"])
        resolved_lines.append((unit_price, product_name))

    try:
        client_label = await fetch_user_display_name(order_in.client_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Identity service unavailable: {exc}",
        ) from exc
    client_name = client_label or f"Client #{order_in.client_id}"

    order = await dal.create(
        order_in,
        resolved_lines=resolved_lines,
        client_name=client_name,
    )
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


async def _reserve_order_stock(order: dict) -> list[int]:
    """Reserve stock for every line in the order. On partial failure, release already-reserved ids."""
    order_id = int(order["id"])
    reservation_ids: list[int] = []
    items = order.get("items") or []
    try:
        for item in items:
            qty = int(round(float(item["quantity"])))
            if qty <= 0:
                continue
            try:
                reservation = await reserve_stock(
                    product_id=int(item["product_id"]),
                    quantity=qty,
                    order_id=order_id,
                )
            except httpx.HTTPStatusError as exc:
                detail = None
                try:
                    detail = exc.response.json().get("detail")
                except Exception:
                    detail = exc.response.text
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot reserve product {item['product_id']}: {detail or exc}",
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Warehouse service unavailable: {exc}",
                ) from exc

            rid = reservation.get("reservation_id")
            if rid is not None:
                reservation_ids.append(int(rid))
    except Exception:
        # Compensation: release anything we already reserved so we don't leak stock.
        for rid in reservation_ids:
            try:
                await release_stock(rid)
            except Exception:
                logger.exception(
                    "orders.compensating_release_failed",
                    extra={"order_id": order_id, "reservation_id": rid},
                )
        raise

    return reservation_ids


async def _release_order_stock(order_id: int) -> None:
    """Release any previously tracked reservations for the order (best-effort)."""
    try:
        rids = await get_order_reservations(order_id)
    except Exception:
        logger.exception("orders.read_reservations_failed", extra={"order_id": order_id})
        return
    for rid in rids:
        try:
            await release_stock(rid)
        except Exception:
            logger.exception(
                "orders.release_stock_failed",
                extra={"order_id": order_id, "reservation_id": rid},
            )
    try:
        await clear_order_reservations(order_id)
    except Exception:
        logger.exception("orders.clear_reservations_failed", extra={"order_id": order_id})


async def _update_order_status(
    order_id: int,
    status_req: UpdateOrderStatusRequest,
    dal: OrderDAL,
) -> OrderResponse:
    """Update order status and orchestrate inventory side-effects when needed."""
    current = await dal.get_by_id(order_id)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    new_status = status_req.status
    previous_status = current.get("status")

    reserved_ids: list[int] = []
    if new_status == "confirmed" and previous_status != "confirmed":
        # Only reserve on the first transition into `confirmed` to avoid double-booking stock.
        reserved_ids = await _reserve_order_stock(current)
        if reserved_ids:
            try:
                existing = await get_order_reservations(order_id)
                await store_order_reservations(order_id, existing + reserved_ids)
            except Exception:
                logger.exception(
                    "orders.store_reservations_failed", extra={"order_id": order_id}
                )
    elif new_status in _CANCELLED_STATUSES and previous_status not in _CANCELLED_STATUSES:
        # Cancelling a previously confirmed order must free the stock.
        await _release_order_stock(order_id)

    order = await dal.update_status(order_id, new_status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

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
