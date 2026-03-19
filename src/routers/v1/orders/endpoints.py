"""Orders v1 endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.routers.v1.orders.actions import (
    _create_order,
    _get_order_detail,
    _list_orders,
    _update_order_status,
)
from src.routers.v1.orders.dal import OrderDAL
from src.routers.v1.orders.description import (
    CREATE_ORDER_DESC,
    GET_ORDER_DESC,
    LIST_ORDERS_DESC,
    UPDATE_ORDER_STATUS_DESC,
)
from src.routers.v1.orders.schemas import (
    CreateOrderRequest,
    OrderListResponse,
    OrderResponse,
    UpdateOrderStatusRequest,
)
from src.routers.v1.orders.summary import (
    CREATE_ORDER_SUMMARY,
    GET_ORDER_SUMMARY,
    LIST_ORDERS_SUMMARY,
    UPDATE_ORDER_STATUS_SUMMARY,
)

orders_router = APIRouter(prefix="/orders", tags=["orders"])


async def get_dal(
    session: AsyncSession = Depends(get_async_session),
) -> OrderDAL:
    """Dependency: get OrderDAL instance."""
    return OrderDAL(session=session)


@orders_router.get(
    "/",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary=LIST_ORDERS_SUMMARY,
    description=LIST_ORDERS_DESC,
)
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    dal: OrderDAL = Depends(get_dal),
) -> OrderListResponse:
    """Get orders."""
    return await _list_orders(dal, skip=skip, limit=limit)


@orders_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary=GET_ORDER_SUMMARY,
    description=GET_ORDER_DESC,
)
async def get_order(
    order_id: int,
    dal: OrderDAL = Depends(get_dal),
) -> OrderResponse:
    """Get order details."""
    return await _get_order_detail(order_id, dal)


@orders_router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary=CREATE_ORDER_SUMMARY,
    description=CREATE_ORDER_DESC,
)
async def create_order(
    order_in: CreateOrderRequest,
    dal: OrderDAL = Depends(get_dal),
) -> OrderResponse:
    """Create order."""
    return await _create_order(order_in, dal)


@orders_router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary=UPDATE_ORDER_STATUS_SUMMARY,
    description=UPDATE_ORDER_STATUS_DESC,
)
async def update_order_status(
    order_id: int,
    status_req: UpdateOrderStatusRequest,
    dal: OrderDAL = Depends(get_dal),
) -> OrderResponse:
    """Update order status."""
    return await _update_order_status(order_id, status_req, dal)
