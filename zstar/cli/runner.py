from pathlib import Path
from typing import Tuple

from zstar.core.backtest import BacktestReport
from .utils import resolve_output_path
from .models import BacktestCliConfig

import json
import plotly.graph_objects as go

class CliRunner:
    @staticmethod
    def write_backtest_outputs(config: BacktestCliConfig, report: BacktestReport) -> Tuple[Path, Path]:
        kpis_output_path = resolve_output_path(config.kpis_output)
        equity_output_path = resolve_output_path(config.equity_curve_output)
        
        kpis_output_path.write_text(json.dumps(report.kpis(), indent=2), encoding="utf-8")
        
        equity_curve = report.equity_curve()
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve["strategy"],
                mode="lines",
                name="Strategy",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve["buy_and_hold"],
                mode="lines",
                name="Buy & Hold",
            )
        )
        figure.update_layout(
            title=f"Equity Curve - {config.data.symbol}",
            xaxis_title="Datetime",
            yaxis_title="Equity",
        )
        figure.write_html(str(equity_output_path), include_plotlyjs="cdn", full_html=True)

        return kpis_output_path, equity_output_path
