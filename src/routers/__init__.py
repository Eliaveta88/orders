"""API routers registry with versioned entrypoint."""

from fastapi import APIRouter

service_router = APIRouter(prefix="/orders", tags=["orders"])
common_router = APIRouter(tags=["common"])
v1_router = APIRouter()


@common_router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orders"}


@common_router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "orders"}


@service_router.get("/ping", summary="Orders router ping")
async def orders_ping() -> dict[str, str]:
    return {"status": "ok", "module": "orders"}


v1_router.include_router(common_router)
v1_router.include_router(service_router)


class Router:
    """Central router registry: (router, prefix, tags) tuples."""

    routers: list[tuple[APIRouter, str, list[str]]] = [
        (v1_router, "/api/v1", ["v1"]),
    ]
