from __future__ import annotations

import importlib
import json

import pandas as pd
from pydantic import ValidationError
from typer.testing import CliRunner

from zstar.cli import app

runner = CliRunner()
cli_app_module = importlib.import_module("zstar.cli.app")


VALID_STRATEGY = """
from zstar.core.strategy import CoreStrategy

class SimpleStrategy(CoreStrategy):
    def long_entry_signals(self, data):
        data[\"long_entry\"] = 0
        data.loc[data.index[0], \"long_entry\"] = 1
        return data

    def long_exit_signals(self, data):
        data[\"long_exit\"] = 0
        data.loc[data.index[1], \"long_exit\"] = 1
        return data

    def position_size(self, balance, entry_price):
        return 1.0

strategy = SimpleStrategy()
"""


INVALID_STRATEGY = """
from zstar.core.strategy import CoreStrategy

class BadStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0
"""


def _price_frame() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=4, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0, 105.0, 110.0, 111.0],
            "close": [101.0, 106.0, 111.0, 112.0],
        },
        index=index,
    )


def _config_payload(**overrides):
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
        "kpis_output": "kpis.json",
        "equity_curve_output": "equity_curve.html",
    }
    payload.update(overrides)
    return payload


def test_cli_backtest_writes_kpis_and_equity_html(tmp_path, monkeypatch):
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(VALID_STRATEGY, encoding="utf-8")

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            _config_payload(
                kpis_output=str(tmp_path / "kpis.json"),
                equity_curve_output=str(tmp_path / "equity_curve.html"),
            )
        ),
        encoding="utf-8",
    )

    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(cli_app_module, "YahooData", _FakeYahooData)

    result = runner.invoke(
        app,
        [
            "backtest",
            "--strategy-file",
            str(strategy_file),
            "--config-file",
            str(config_file),
        ],
    )

    assert result.exit_code == 0

    kpis_output_path = tmp_path / "kpis.json"
    equity_output_path = tmp_path / "equity_curve.html"

    assert kpis_output_path.exists()
    assert equity_output_path.exists()

    kpis = json.loads(kpis_output_path.read_text(encoding="utf-8"))
    assert "total_return_pct" in kpis


def test_cli_backtest_fails_when_strategy_instance_missing(tmp_path, monkeypatch):
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(INVALID_STRATEGY, encoding="utf-8")

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(_config_payload()), encoding="utf-8")

    class _FakeYahooData:
        def __init__(self, *_args, **_kwargs):
            self.data = _price_frame()
            self.interval = "1d"

        def get_data(self):
            return self.data.copy()

        def get_interval(self):
            return self.interval

    monkeypatch.setattr(cli_app_module, "YahooData", _FakeYahooData)

    result = runner.invoke(
        app,
        [
            "backtest",
            "--strategy-file",
            str(strategy_file),
            "--config-file",
            str(config_file),
        ],
    )

    assert result.exit_code == 1
    assert "error occurred during backtest execution" in result.stdout.lower()


def test_cli_backtest_fails_when_config_is_invalid(tmp_path):
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(VALID_STRATEGY, encoding="utf-8")

    config_file = tmp_path / "config.json"
    config_file.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "backtest",
            "--strategy-file",
            str(strategy_file),
            "--config-file",
            str(config_file),
        ],
    )

    assert result.exit_code == 1
    assert isinstance(result.exception, ValidationError)
