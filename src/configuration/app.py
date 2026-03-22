import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.middleware import db_session_middleware
from src.routers import Router
from src.services.redis import close_redis, get_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: connecting to Redis …")
    await get_redis()
    logger.info("Redis connected.")
    yield
    logger.info("Shutting down: closing Redis …")
    await close_redis()
    logger.info("Redis closed.")


class App:
    def __init__(self):
        self._app: FastAPI = FastAPI(
            title="Api orders",
            description="Api orders",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
            openapi_url="/api/openapi.json",
            default_response_class=ORJSONResponse,
            lifespan=lifespan,
        )
        self._app.add_middleware(
            middleware_class=CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT", "OPTIONS"],
            allow_headers=["*"],
        )
        self._app.add_middleware(
            middleware_class=BaseHTTPMiddleware,
            dispatch=db_session_middleware,
        )

        self._register_routers()

    def _register_routers(self) -> None:
        for router, prefix, tags in Router.routers:
            self._app.include_router(router=router, prefix=prefix, tags=tags)

    @property
    def app(self) -> FastAPI:
        return self._app
