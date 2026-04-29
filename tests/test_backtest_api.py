from __future__ import annotations

import importlib
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from zstar.core.backtest.backtest_report import BacktestReport
from zstar.core.strategy import CoreStrategy
from zstar.core.strategy.validate_strategy import ValidationIssue, ValidationResult
from zstar.api.backtest.strategy_models import ValidateStrategiesResponse, ValidationIssueResponse
from zstar.api.start_backend import app

backtest_router_module = importlib.import_module("zstar.api.backtest.backtest_router")
file_utils_module = importlib.import_module("zstar.api.utils.file_utils")
client = TestClient(app)

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


class _FakePaths:
    def __init__(self, strategies_dir: Path, default_strategy_name: str = "default_strategy") -> None:
        self.strategies_dir = strategies_dir
        self.default_strategy_name = default_strategy_name


class _FakeConfig:
    def __init__(self, strategies_dir: Path, default_strategy_name: str = "default_strategy") -> None:
        self.paths = _FakePaths(strategies_dir, default_strategy_name)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _payload(strategy_filename: str | None = None) -> dict:
    payload = {
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
    if strategy_filename is not None:
        payload["strategy_filename"] = strategy_filename
    return payload


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


def _mock_validation_success(strategy_filename: str):
    return SimpleStrategy(), ValidationResult(strategy_filename=strategy_filename, issues=[])


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
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: type("Payload", (), {"strategy": SimpleStrategy(), "validation": type("Validation", (), {"ready_to_backtest": True, "strategy_filename": "default_strategy.py", "total_errors": 0, "summary_text": "Ready to backtest", "issues": []})()})(),
    )

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_validation"] is None
    assert body["backtest_result"]["meta"]["symbol"] == "AAPL"
    assert body["backtest_result"]["meta"]["bars_count"] == 4
    assert len(body["backtest_result"]["equity_curve"]) == 4
    assert "datetime" in body["backtest_result"]["equity_curve"][0]
    assert "+00:00" in body["backtest_result"]["equity_curve"][0]["datetime"]
    assert "strategy" in body["backtest_result"]["equity_curve"][0]
    assert "buy_and_hold" in body["backtest_result"]["equity_curve"][0]
    assert len(body["backtest_result"]["market_ohlcv"]) == 4
    assert "datetime" in body["backtest_result"]["market_ohlcv"][0]
    assert "+00:00" in body["backtest_result"]["market_ohlcv"][0]["datetime"]
    assert "open" in body["backtest_result"]["market_ohlcv"][0]
    assert "high" in body["backtest_result"]["market_ohlcv"][0]
    assert "low" in body["backtest_result"]["market_ohlcv"][0]
    assert "close" in body["backtest_result"]["market_ohlcv"][0]
    assert "volume" in body["backtest_result"]["market_ohlcv"][0]
    assert len(body["backtest_result"]["trades"]) == 1
    assert body["backtest_result"]["trades"][0]["symbol"] == "AAPL"
    assert body["backtest_result"]["trades"][0]["side"] == "LONG"
    assert "total_return_pct" in body["backtest_result"]["kpis"]
    assert "sharpe_ratio" in body["backtest_result"]["kpis"]
    assert "best_trade" in body["backtest_result"]["kpis"]
    assert "worst_trade" in body["backtest_result"]["kpis"]


def test_list_strategies_returns_python_filenames_without_extension(monkeypatch, tmp_path):
    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "alpha.py").write_text("print('alpha')", encoding="utf-8")
    (strategy_dir / "zeta.py").write_text("print('zeta')", encoding="utf-8")
    (strategy_dir / "notes.txt").write_text("ignore me", encoding="utf-8")
    (strategy_dir / "nested").mkdir()
    (strategy_dir / "nested" / "child.py").write_text("print('nested')", encoding="utf-8")

    monkeypatch.setattr(file_utils_module, "load_config", lambda: _FakeConfig(strategy_dir))

    response = client.get("/api/strategies")

    assert response.status_code == 200
    assert response.json() == {"strategies": ["alpha", "zeta"]}


def test_validate_strategies_endpoint_returns_success_payload(monkeypatch, tmp_path):
    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "alpha.py").write_text(
        """
from zstar.core.strategy import CoreStrategy

class AlphaStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(file_utils_module, "load_config", lambda: _FakeConfig(strategy_dir))

    response = client.post("/api/validate-strategies", json={"strategy_filename": "alpha"})

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_filename"] == "alpha.py"
    assert body["ready_to_backtest"] is True
    assert body["total_errors"] == 0
    assert "issues" in body


def test_validate_strategies_endpoint_returns_categorized_issue(monkeypatch, tmp_path):
    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "broken.py").write_text(
        """
from zstar.core.strategy import CoreStrategy

class BrokenStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return "bad"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(file_utils_module, "load_config", lambda: _FakeConfig(strategy_dir))

    response = client.post("/api/validate-strategies", json={"strategy_filename": "broken"})

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_backtest"] is False
    assert body["total_errors"] >= 1
    assert body["issues"][0]["category"] in {"type", "logic", "template", "syntax"}
    assert body["issues"][0]["file"] == "broken.py"


def test_validate_strategies_endpoint_rejects_missing_file():
    response = client.post("/api/validate-strategies", json={"strategy_filename": "unknown_strategy"})

    assert response.status_code == 400
    assert "strategy_validation_error" in response.json()["detail"].lower()


def test_run_backtest_uses_selected_strategy_filename(monkeypatch, tmp_path):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    validated_files: list[str] = []

    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "alpha_strategy.py").write_text("class Placeholder: pass", encoding="utf-8")

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)
    monkeypatch.setattr(file_utils_module, "load_config", lambda: _FakeConfig(strategy_dir))
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: (
            validated_files.append("alpha_strategy.py"),
            type("Payload", (), {"strategy": SimpleStrategy(), "validation": type("Validation", (), {"ready_to_backtest": True, "strategy_filename": "alpha_strategy.py", "total_errors": 0, "summary_text": "Ready to backtest", "issues": []})()})(),
        )[1],
    )

    response = client.post("/api/backtest/run", json=_payload(strategy_filename="alpha_strategy"))

    assert response.status_code == 200
    assert validated_files[0] == "alpha_strategy.py"


def test_run_backtest_defaults_to_default_strategy_when_filename_missing(monkeypatch, tmp_path):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    validated_files: list[str] = []

    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "default_strategy.py").write_text("class Placeholder: pass", encoding="utf-8")

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)
    monkeypatch.setattr(file_utils_module, "load_config", lambda: _FakeConfig(strategy_dir))
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: (
            validated_files.append("default_strategy.py"),
            type("Payload", (), {"strategy": SimpleStrategy(), "validation": type("Validation", (), {"ready_to_backtest": True, "strategy_filename": "default_strategy.py", "total_errors": 0, "summary_text": "Ready to backtest", "issues": []})()})(),
        )[1],
    )

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 200
    assert validated_files[0] == "default_strategy.py"


def test_run_backtest_rejects_missing_strategy_file(monkeypatch):
    response = client.post("/api/backtest/run", json=_payload(strategy_filename="unknown_strategy"))

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "strategy_validation_error" in detail
    assert "unknown_strategy.py" in detail


def test_run_backtest_propagates_strategy_file_validation_errors(monkeypatch):
    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(backtest_router_module, "YahooData", _FakeYahooData)
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: type("Payload", (), {"strategy": None, "validation": ValidateStrategiesResponse(ready_to_backtest=False, strategy_filename="default_strategy.py", total_errors=1, summary_text="Validation completed with 1 error(s)", issues=[ValidationIssueResponse(category="template", file="default_strategy.py", line=None, message="Keep exactly one CoreStrategy subclass. Found: AlphaStrategy, BetaStrategy.")])})(),
    )

    response = client.post("/api/backtest/run", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["backtest_result"] is None
    assert body["strategy_validation"]["ready_to_backtest"] is False
    assert body["strategy_validation"]["total_errors"] == 1
    assert "corestrategy subclass" in body["strategy_validation"]["issues"][0]["message"].lower()


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
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: type("Payload", (), {"strategy": SimpleStrategy(), "validation": type("Validation", (), {"ready_to_backtest": True, "strategy_filename": "default_strategy.py", "total_errors": 0, "summary_text": "Ready to backtest", "issues": []})()})(),
    )

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
    monkeypatch.setattr(
        backtest_router_module,
        "resolve_strategy_validation",
        lambda _strategy_filename: type("Payload", (), {"strategy": SimpleStrategy(), "validation": type("Validation", (), {"ready_to_backtest": True, "strategy_filename": "default_strategy.py", "total_errors": 0, "summary_text": "Ready to backtest", "issues": []})()})(),
    )

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
    assert body["strategy_validation"] is None
    assert body["backtest_result"]["kpis"]["profit_factor"] is None
    assert body["backtest_result"]["kpis"]["sharpe_ratio"] is None
