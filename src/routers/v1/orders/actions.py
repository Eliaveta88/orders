"""Business logic actions for orders endpoints."""

from fastapi import HTTPException, status

from src.routers.v1.orders.dal import OrderDAL
from src.routers.v1.orders.schemas import (
    OrderListResponse,
    OrderResponse,
    CreateOrderRequest,
    UpdateOrderStatusRequest,
)


async def _list_orders(
    dal: OrderDAL,
    skip: int = 0,
    limit: int = 50,
) -> OrderListResponse:
    """Get orders list."""
    orders = await dal.list_orders(skip=skip, limit=limit)
    total = await dal.count_orders()
    return OrderListResponse(
        items=[OrderResponse(**o) for o in orders],
        total=total,
        skip=skip,
        limit=limit,
    )


async def _get_order_detail(
    order_id: int,
    dal: OrderDAL,
) -> OrderResponse:
    """Get order details."""
    order = await dal.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return OrderResponse(**order)


async def _create_order(
    order_in: CreateOrderRequest,
    dal: OrderDAL,
) -> OrderResponse:
    """Create new order."""
    order = await dal.create(order_in)
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
    return OrderResponse(**order)
