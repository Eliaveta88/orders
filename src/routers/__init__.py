"""API routers registry with versioned entrypoint."""

from fastapi import APIRouter

from src.routers.v1 import v1_router


class Router:
    """Central router registry: (router, prefix, tags) tuples."""

    routers: list[tuple[APIRouter, str, list[str]]] = [
        (v1_router, "/api/v1", ["v1"]),
    ]
