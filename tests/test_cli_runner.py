import json

import pandas as pd

from zstar.cli.models import BacktestCliConfig
from zstar.cli.runner import CliRunner
from zstar.core.backtest.backtest_report import BacktestReport
from zstar.core.data_loader.data_loader_model import DataLoaderConfigModel
from zstar.core.backtest.backtest_config_model import BacktestConfigModel


def test_cli_runner_writes_kpis_json_and_equity_html(tmp_path):
    data_index = pd.date_range("2026-01-01", periods=3, freq="D")
    data = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "close": [101.0, 102.0, 103.0],
        },
        index=data_index,
    )

    report = BacktestReport(
        initial_balance=1000.0,
        final_balance=1100.0,
        trades=[],
        data=data,
        interval="1d",
    )
    config = BacktestCliConfig(
        kpis_output=str(tmp_path / "outputs" / "kpis.json"),
        equity_curve_output=str(tmp_path / "outputs" / "equity_curve.html"),
        data=DataLoaderConfigModel(symbol="AAPL"),
        backtest_config=BacktestConfigModel(),
    )

    kpis_path, equity_path = CliRunner.write_backtest_outputs(config, report)

    assert kpis_path.exists() is True
    assert equity_path.exists() is True

    saved_kpis = json.loads(kpis_path.read_text(encoding="utf-8"))
    html_output = equity_path.read_text(encoding="utf-8")
    assert "total_return_pct" in saved_kpis
    assert "Strategy" in html_output
    assert "Buy & Hold" in html_output
