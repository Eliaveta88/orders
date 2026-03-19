"""API v1 router aggregator."""

from fastapi import APIRouter

from src.routers.v1.orders.orders import orders_router
from src.routers.v1.common.common import common_router

v1_router = APIRouter()
v1_router.include_router(common_router)
v1_router.include_router(orders_router)
