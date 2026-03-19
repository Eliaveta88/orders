"""API routers registry."""

from fastapi import APIRouter


class Router:
    """Central router registry: (router, prefix, tags) tuples."""

    routers: list[tuple[APIRouter, str, list[str]]] = []
