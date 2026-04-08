from __future__ import annotations

import importlib
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from zstar.core.backtest.backtest_report import BacktestReport
from zstar.api.start_backend import app

backtest_router_module = importlib.import_module("zstar.api.backtest.backtest_router")
client = TestClient(app)

VALID_STRATEGY_CODE = """
from zstar.core.core_strategy import CoreStrategy

class SimpleStrategy(CoreStrategy):
    def long_entry_signals(self, data):
        data["long_entry"] = 0
        data.loc[data.index[0], "long_entry"] = 1
        return data

    def long_exit_signals(self, data):
        data["long_exit"] = 0
        data.loc[data.index[1], "long_exit"] = 1
        return data

    def position_size(self, balance, entry_price):
        return 1.0

strategy = SimpleStrategy()
"""


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _payload(strategy_code: str = VALID_STRATEGY_CODE) -> dict:
    return {
        "strategy_code": strategy_code,
        "data": {
            "symbol": "AAPL",
            "start_date": "2025-01-01",
            "end_date": "2025-01-06",
            "interval": "1d",
        },
        "backtest_config": {
            "initial_balance": 1000.0,
            "entry_fee_pct": 0.0,
            "exit_fee_pct": 0.0,
            "slippage_pct": 0.0,
            "slippage_seed": 42,
        },
    }


def _price_frame() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=4, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0, 105.0, 110.0, 111.0],
            "high": [102.0, 107.0, 112.0, 113.0],
            "low": [99.0, 103.0, 109.0, 110.0],
            "close": [101.0, 106.0, 111.0, 112.0],
            "volume": [1000.0, 1100.0, 1200.0, 1300.0],
        },
        index=index,
    )


def test_run_backtest_returns_complete_payload(monkeypatch):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["symbol"] == "AAPL"
    assert body["meta"]["bars_count"] == 4
    assert len(body["equity_curve"]) == 4
    assert "datetime" in body["equity_curve"][0]
    assert "+00:00" in body["equity_curve"][0]["datetime"]
    assert "strategy" in body["equity_curve"][0]
    assert "buy_and_hold" in body["equity_curve"][0]
    assert len(body["market_ohlcv"]) == 4
    assert "datetime" in body["market_ohlcv"][0]
    assert "+00:00" in body["market_ohlcv"][0]["datetime"]
    assert "open" in body["market_ohlcv"][0]
    assert "high" in body["market_ohlcv"][0]
    assert "low" in body["market_ohlcv"][0]
    assert "close" in body["market_ohlcv"][0]
    assert "volume" in body["market_ohlcv"][0]
    assert len(body["trades"]) == 1
    assert body["trades"][0]["symbol"] == "AAPL"
    assert body["trades"][0]["side"] == "LONG"
    assert "total_return_pct" in body["kpis"]
    assert "sharpe_ratio" in body["kpis"]
    assert "best_trade" in body["kpis"]
    assert "worst_trade" in body["kpis"]


def test_run_backtest_rejects_missing_strategy_instance(monkeypatch):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)

    response = client.post(
        "/api/backtest/run",
        json=_payload(
            strategy_code="""
from zstar.core.core_strategy import CoreStrategy
class BadStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0
""",
        ),
    )

    assert response.status_code == 400
    assert "backtest_execution_error" in response.json()["detail"].lower()


def test_run_backtest_rejects_empty_market_data(monkeypatch):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = pd.DataFrame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 400
    assert "backtest_execution_error" in response.json()["detail"].lower()


def test_run_backtest_serializes_nan_and_inf_kpis_to_null(monkeypatch):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)

    original_kpis = BacktestReport.kpis

    def _patched_kpis(self: BacktestReport):
        metrics = original_kpis(self)
        metrics["profit_factor"] = np.nan
        metrics["sharpe_ratio"] = np.inf
        return metrics

    monkeypatch.setattr(BacktestReport, "kpis", _patched_kpis)

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["profit_factor"] is None
    assert body["kpis"]["sharpe_ratio"] is None
