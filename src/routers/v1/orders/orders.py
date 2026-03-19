"""Orders v1 HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.routers.v1.orders.actions import OrderActions
from src.routers.v1.orders.dal import OrderDAL

orders_router = APIRouter(prefix="/orders", tags=["orders"])


async def get_actions() -> OrderActions:
    dal = OrderDAL(session=None)  # type: ignore
    return OrderActions(dal)


@orders_router.post("/orders", summary="Create order")
async def create_order(
    data: dict,
    actions: Annotated[OrderActions, Depends(get_actions)],
) -> dict:
    return await actions.create_order(data)


@orders_router.get("/orders", summary="List orders")
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    actions: Annotated[OrderActions, Depends(get_actions)] = Depends(
        get_actions
    ),
) -> list[dict]:
    return await actions.list_orders(skip, limit)
