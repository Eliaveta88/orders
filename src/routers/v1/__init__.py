"""V1 API: health + orders."""

from fastapi import APIRouter

from src.routers.v1.orders.endpoints import orders_router

common_router = APIRouter(tags=["common"])


@common_router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orders"}


@common_router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "orders"}


v1_router = APIRouter()
v1_router.include_router(common_router)
v1_router.include_router(orders_router)
