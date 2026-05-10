from __future__ import annotations

import pandas as pd

from zstar.core.backtest.backtest_report_kpis import compute_kpis
from zstar.core.backtest.backtest_report_timeseries import compute_equity_curve
from zstar.core.trade_order import Trade


class BacktestReport:
    def __init__(
        self,
        initial_balance: float,
        final_balance: float,
        trades: list[Trade],
        data: pd.DataFrame,
        interval: str = "1d",
        risk_free_rate: float = 0.0,
    ) -> None:
        self.initial_balance = initial_balance
        self.final_balance = final_balance
        self.trades = trades
        self.data = data
        self.interval = interval
        self.risk_free_rate = risk_free_rate

    def equity_curve(self) -> pd.DataFrame:
        return compute_equity_curve(self.initial_balance, self.trades, self.data)

    def kpis(self) -> dict[str, float | int]:
        return compute_kpis(
            self.initial_balance,
            self.final_balance,
            self.trades,
            self.data,
            self.interval,
            self.risk_free_rate,
        )
