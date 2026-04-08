from dataclasses import dataclass

import numpy as np
import pandas as pd

from zstar.core.trade_order import Trade


@dataclass
class BacktestReport:
    initial_balance: float
    final_balance: float
    trades: list[Trade]
    data: pd.DataFrame
    interval: str = "1d"


    def _strategy_equity_curve(self) -> pd.Series:
        if self.data.empty:
            return pd.Series(dtype=float, name="strategy")

        index = self.data.index
        pnl_changes = np.zeros(len(index), dtype=float)

        for trade in sorted(self.trades, key=lambda trade_item: trade_item.exit_datetime):
            exit_idx = index.searchsorted(trade.exit_datetime, side="left")
            if exit_idx < len(index):
                pnl_changes[exit_idx] += float(trade.net_pnl)

        equity = self.initial_balance + np.cumsum(pnl_changes)
        return pd.Series(equity, index=index, name="strategy")


    def _return_pct(self, final_value: float) -> float:
        if self.initial_balance == 0:
            return 0.0
        return ((final_value - self.initial_balance) / self.initial_balance) * 100


    @staticmethod
    def _max_drawdown_pct(equity_curve: pd.Series) -> float:
        if equity_curve.empty:
            return 0.0

        peak = equity_curve.cummax()
        drawdown_pct = (equity_curve / peak - 1.0) * 100
        return float(drawdown_pct.min())


    def _buy_and_hold_equity_curve(self) -> pd.Series:
        if self.data.empty:
            return pd.Series(dtype=float, name="buy_and_hold")

        close_prices = self.data["close"].astype(float)
        first_close = float(close_prices.iloc[0])
        units = self.initial_balance / first_close

        return (close_prices * units).rename("buy_and_hold")


    def _buy_and_hold_metrics(self, strategy_return_pct: float) -> dict[str, float]:
        buy_and_hold_curve = self._buy_and_hold_equity_curve()
        buy_and_hold_final = (
            float(buy_and_hold_curve.iloc[-1])
            if not buy_and_hold_curve.empty
            else self.initial_balance
        )
        buy_and_hold_return_pct = self._return_pct(buy_and_hold_final)
        buy_and_hold_max_drawdown_pct = self._max_drawdown_pct(buy_and_hold_curve)

        return {
            "buy_and_hold_final_balance": buy_and_hold_final,
            "buy_and_hold_return_pct": buy_and_hold_return_pct,
            "buy_and_hold_max_drawdown_pct": buy_and_hold_max_drawdown_pct,
            "return_diff_vs_buy_and_hold_pct": strategy_return_pct - buy_and_hold_return_pct,
        }


    def equity_curve(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "strategy": self._strategy_equity_curve(),
                "buy_and_hold": self._buy_and_hold_equity_curve(),
            }
        )


    def _compute_sharpe_ratio(self, strategy_returns: pd.Series) -> float:
        sharpe_ratio = np.nan

        if strategy_returns.size > 1:
            returns_std = strategy_returns.std(ddof=1)
            if returns_std > 0:
                sharpe_ratio = (strategy_returns.mean() / returns_std) * np.sqrt(self._annualization_factor())

        return float(sharpe_ratio)


    def _annualization_factor(self) -> float:
        trading_days_per_year = 252.0
        trading_minutes_per_day = 390.0
        interval_value = self.interval.strip().lower()

        if interval_value.endswith("d"):
            day_count = self._parse_positive_number(interval_value[:-1])
            if day_count is not None:
                return trading_days_per_year / day_count
            return trading_days_per_year

        if interval_value.endswith("h"):
            hour_count = self._parse_positive_number(interval_value[:-1])
            if hour_count is not None:
                bars_per_day = trading_minutes_per_day / (hour_count * 60.0)
                return trading_days_per_year * bars_per_day

        if interval_value.endswith("m"):
            minute_count = self._parse_positive_number(interval_value[:-1])
            if minute_count is not None:
                bars_per_day = trading_minutes_per_day / minute_count
                return trading_days_per_year * bars_per_day

        return trading_days_per_year


    @staticmethod
    def _parse_positive_number(value: str) -> float | None:
        try:
            parsed_value = float(value)
        except (TypeError, ValueError):
            return None

        return parsed_value if parsed_value > 0 else None


    def _average_trade_duration_minutes(self) -> float:
        if len(self.trades) == 0:
            return 0.0

        durations = [
            (trade.exit_datetime - trade.entry_datetime).total_seconds() / 60
            for trade in self.trades
        ]

        return float(np.mean(durations))


    def kpis(self) -> dict[str, float]:
        total_trades = len(self.trades)
        net_pnl = self.final_balance - self.initial_balance
        total_return_pct = self._return_pct(self.final_balance)
        strategy_curve = self._strategy_equity_curve()
        strategy_max_drawdown_pct = self._max_drawdown_pct(strategy_curve)
        strategy_returns = strategy_curve.pct_change().dropna()

        pnls = np.array([trade.net_pnl for trade in self.trades], dtype=float)
        total_fees = float(sum(trade.total_fees for trade in self.trades))
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]

        gross_profit = wins.sum() if wins.size > 0 else 0.0
        gross_loss = abs(losses.sum()) if losses.size > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan
        sharpe_ratio = self._compute_sharpe_ratio(strategy_returns)

        best_trade = float(pnls.max()) if total_trades > 0 else 0.0
        worst_trade = float(pnls.min()) if total_trades > 0 else 0.0
        median_trade = float(np.median(pnls)) if total_trades > 0 else 0.0
        avg_trade_duration_minutes = self._average_trade_duration_minutes()

        metrics = {
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "net_pnl": net_pnl,
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "total_fees": total_fees,
            "gross_profit": float(gross_profit),
            "gross_loss": float(gross_loss),
            "win_rate_pct": (wins.size / total_trades) * 100 if total_trades > 0 else 0.0,
            "avg_trade_pnl": float(pnls.mean()) if total_trades > 0 else 0.0,
            "avg_win": float(wins.mean()) if wins.size > 0 else 0.0,
            "avg_loss": float(losses.mean()) if losses.size > 0 else 0.0,
            "profit_factor": float(profit_factor),
            "expectancy": float(pnls.mean()) if total_trades > 0 else 0.0,
            "max_drawdown_pct": strategy_max_drawdown_pct,
            "sharpe_ratio": float(sharpe_ratio),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "median_trade": median_trade,
            "avg_trade_duration_minutes": avg_trade_duration_minutes,
        }

        metrics.update(self._buy_and_hold_metrics(total_return_pct))
        return metrics
