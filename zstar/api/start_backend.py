from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zstar.api.backtest import backtest_router
from zstar.api.strategies import strategies_router
from zstar.config import AppConfig, load_config


def create_app(settings: AppConfig | None = None) -> FastAPI:
    app_settings = settings or load_config()
    application = FastAPI(title="ZStar Backtesting API", version="1.0.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.backend.allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(backtest_router)
    application.include_router(strategies_router)

    @application.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
