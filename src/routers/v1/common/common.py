"""Common v1 HTTP endpoints."""

from fastapi import APIRouter

from src.routers.v1.common.schemas import HealthResponse, ReadyResponse

common_router = APIRouter(tags=["common"])


@common_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="orders")


@common_router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    return ReadyResponse(status="ready", service="orders")
