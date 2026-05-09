from contextlib import asynccontextmanager
import time
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from zstar.api.backtest import backtest_router, csv_router, strategy_router
from zstar.config import AppConfig, load_config
from zstar.logger import clear_log_context, get_logger, set_log_context, setup_logging


_lazy_app: FastAPI | None = None


def create_app(settings: AppConfig | None = None, *, configure_logging: bool = True) -> FastAPI:
    app_settings = settings or load_config()
    logger = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        if configure_logging:
            setup_logging(app_settings.logging)
        yield

    application = FastAPI(title="ZStar Backtesting API", version="1.0.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.backend.allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(backtest_router)
    application.include_router(csv_router)
    application.include_router(strategy_router)

    @application.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        user_action = f"{request.method} {request.url.path}"
        set_log_context(request_id=request_id, user_action=user_action)
        logger.info("Request started")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception("Request failed duration_ms=%.3f", duration_ms)
            clear_log_context()
            raise

        response.headers["X-Request-ID"] = request_id
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("Request finished status_code=%s duration_ms=%.3f", response.status_code, duration_ms)
        clear_log_context()
        return response

    @application.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


async def app(scope, receive, send) -> None:
    global _lazy_app
    if _lazy_app is None:
        _lazy_app = create_app()
    await _lazy_app(scope, receive, send)
