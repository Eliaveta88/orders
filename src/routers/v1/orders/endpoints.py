"""HTTP endpoints for orders v1."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.routers.v1.orders.actions import _get_order_detail, _list_orders
from src.routers.v1.orders.dal import OrderDAL
from src.routers.v1.orders.schemas import OrderListResponse, OrderResponse

orders_router = APIRouter(prefix="/orders", tags=["orders"])


async def get_dal(
    session: AsyncSession = Depends(get_async_session),
) -> OrderDAL:
    return OrderDAL(session=session)


@orders_router.get("/ping", summary="Orders router ping")
async def orders_ping() -> dict[str, str]:
    return {"status": "ok", "module": "orders"}


@orders_router.get(
    "",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список заказов",
)
async def list_orders(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    dal: OrderDAL = Depends(get_dal),
) -> OrderListResponse:
    return await _list_orders(dal, skip=skip, limit=limit)


@orders_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Детали заказа",
)
async def get_order(
    order_id: int,
    dal: OrderDAL = Depends(get_dal),
) -> OrderResponse:
    return await _get_order_detail(order_id, dal)
