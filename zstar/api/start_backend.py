from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zstar.api.backtest import backtest_router
from zstar.api.strategies import strategies_router
from zstar.api.settings import get_settings

settings = get_settings("config.yaml")

app = FastAPI(title="ZStar Backtesting API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest_router)
app.include_router(strategies_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
