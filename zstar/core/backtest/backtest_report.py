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
    risk_free_rate: float = 0.0


    def _strategy_equity_curve(self) -> pd.Series:
        if self.data.empty:
            return pd.Series(dtype=float, name="strategy")

        equity_values = [
            self._compute_strategy_equity_at(timestamp, close_price)
            for timestamp, close_price in self.data["close"].astype(float).items()
        ]
        return pd.Series(equity_values, index=self.data.index, name="strategy")


    def _compute_strategy_equity_at(self, timestamp: pd.Timestamp, price: float) -> float:
        """
        Calculate strategy equity at one timestamp.

        Formula: initial_balance + realized_pnl + open_unrealized_pnl - open_entry_fees

        Edge cases:
            - Closed trades are realized at and after exit_datetime.
            - Open trades are marked to the current close price before exit_datetime.
        """
        realized = sum(trade.net_pnl for trade in self.trades if trade.exit_datetime <= timestamp)
        open_pnl = sum(
            self._compute_unrealized_trade_pnl(trade, price) - trade.entry_fee
            for trade in self.trades
            if trade.entry_datetime <= timestamp < trade.exit_datetime
        )
        return float(self.initial_balance + realized + open_pnl)


    def _compute_unrealized_trade_pnl(self, trade: Trade, price: float) -> float:
        """
        Calculate mark-to-market raw PnL for an open trade.

        Formula: (current_price - entry_price) * size * side_sign

        Edge cases:
            - Uses trade side sign, so short positions gain when price declines.
        """
        return float((price - trade.entry_price) * trade.size * trade.side.to_sign())


    def _compute_return_pct(self, final_value: float) -> float:
        """
        Calculate percentage return.

        Formula: ((final_value - initial_balance) / initial_balance) * 100

        Edge cases:
            - Returns 0.0 when initial_balance is zero because return is undefined.
        """
        if self.initial_balance == 0:
            return 0.0
        return ((final_value - self.initial_balance) / self.initial_balance) * 100


    def _compute_max_drawdown_pct(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.

        Formula: min((equity_t / rolling_peak_t - 1) * 100)

        Edge cases:
            - Returns 0.0 for empty curves.
            - Ignores periods where rolling peak is not positive to avoid division by zero.
        """
        if equity_curve.empty:
            return 0.0

        peak = equity_curve.cummax()
        drawdown_pct = (equity_curve[peak > 0] / peak[peak > 0] - 1.0) * 100
        if drawdown_pct.empty:
            return 0.0
        return float(drawdown_pct.min())


    def _buy_and_hold_equity_curve(self) -> pd.Series:
        if self.data.empty:
            return pd.Series(dtype=float, name="buy_and_hold")

        close_prices = self.data["close"].astype(float)
        first_close = float(close_prices.iloc[0])
        if first_close <= 0:
            return pd.Series(dtype=float, name="buy_and_hold")

        units = self.initial_balance / first_close

        return (close_prices * units).rename("buy_and_hold")


    def _compute_buy_and_hold_final_balance(self, buy_and_hold_curve: pd.Series) -> float:
        """
        Calculate final buy-and-hold account value.

        Formula: close_last * (initial_balance / close_first)

        Edge cases:
            - Returns initial_balance when buy-and-hold cannot be built.
        """
        if buy_and_hold_curve.empty:
            return float(self.initial_balance)
        return float(buy_and_hold_curve.iloc[-1])


    def _compute_buy_and_hold_return_pct(self, buy_and_hold_final: float) -> float:
        """
        Calculate buy-and-hold percentage return.

        Formula: ((buy_and_hold_final - initial_balance) / initial_balance) * 100

        Edge cases:
            - Returns 0.0 when initial_balance is zero because return is undefined.
        """
        return self._compute_return_pct(buy_and_hold_final)


    def _compute_buy_and_hold_max_drawdown_pct(
        self,
        buy_and_hold_curve: pd.Series,
    ) -> float:
        """
        Calculate buy-and-hold maximum drawdown percentage.

        Formula: min((equity_t / rolling_peak_t - 1) * 100)

        Edge cases:
            - Returns 0.0 for empty or non-positive buy-and-hold curves.
        """
        return self._compute_max_drawdown_pct(buy_and_hold_curve)


    def _compute_return_diff_vs_buy_and_hold_pct(
        self,
        strategy_return_pct: float,
        buy_and_hold_return_pct: float,
    ) -> float:
        """
        Calculate strategy return minus buy-and-hold return.

        Formula: strategy_return_pct - buy_and_hold_return_pct

        Edge cases:
            - Uses already-normalized percentages, so no division occurs here.
        """
        return strategy_return_pct - buy_and_hold_return_pct


    def equity_curve(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "strategy": self._strategy_equity_curve(),
                "buy_and_hold": self._buy_and_hold_equity_curve(),
            }
        )


    def _compute_sharpe_ratio(self, strategy_returns: pd.Series) -> float:
        """
        Calculate annualized Sharpe ratio.

        Formula: mean(r_t - rf_period) / std(r_t, ddof=1) * sqrt(periods_per_year)

        Edge cases:
            - Returns NaN for fewer than two returns or zero return volatility.
            - risk_free_rate is annual decimal return, converted to a per-period rate.
        """
        if strategy_returns.size <= 1:
            return float(np.nan)

        returns_std = strategy_returns.std(ddof=1)
        if returns_std <= 0:
            return float(np.nan)

        annualization_factor = self._annualization_factor()
        excess_return = strategy_returns.mean() - (self.risk_free_rate / annualization_factor)
        return float((excess_return / returns_std) * np.sqrt(annualization_factor))


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


    def _compute_avg_trade_duration_minutes(self) -> float:
        """
        Calculate average elapsed minutes per trade.

        Formula: mean((exit_datetime - entry_datetime).total_seconds() / 60)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        if len(self.trades) == 0:
            return 0.0

        durations = [
            (trade.exit_datetime - trade.entry_datetime).total_seconds() / 60
            for trade in self.trades
        ]

        return float(np.mean(durations))


    def _trade_pnls(self) -> np.ndarray:
        return np.array([trade.net_pnl for trade in self.trades], dtype=float)


    def _winning_pnls(self, pnls: np.ndarray) -> np.ndarray:
        return pnls[pnls > 0]


    def _losing_pnls(self, pnls: np.ndarray) -> np.ndarray:
        return pnls[pnls < 0]


    def _compute_net_pnl(self) -> float:
        """
        Calculate net profit and loss.

        Formula: final_balance - initial_balance

        Edge cases:
            - Negative values correctly indicate a losing backtest.
        """
        return float(self.final_balance - self.initial_balance)


    def _compute_total_trades(self) -> int:
        """
        Count closed trades.

        Formula: len(trades)

        Edge cases:
            - Returns 0 when no trades were closed.
        """
        return len(self.trades)


    def _compute_total_fees(self) -> float:
        """
        Calculate total fees paid.

        Formula: sum(entry_fee_i + exit_fee_i)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        return float(sum(trade.total_fees for trade in self.trades))


    def _compute_gross_profit(self, wins: np.ndarray) -> float:
        """
        Calculate gross profit from winning trades.

        Formula: sum(net_pnl_i for net_pnl_i > 0)

        Edge cases:
            - Returns 0.0 when there are no winning trades.
        """
        return float(wins.sum()) if wins.size > 0 else 0.0


    def _compute_gross_loss(self, losses: np.ndarray) -> float:
        """
        Calculate absolute gross loss from losing trades.

        Formula: abs(sum(net_pnl_i for net_pnl_i < 0))

        Edge cases:
            - Returns 0.0 when there are no losing trades.
        """
        return float(abs(losses.sum())) if losses.size > 0 else 0.0


    def _compute_win_rate_pct(self, wins: np.ndarray, total_trades: int) -> float:
        """
        Calculate percentage of trades with positive net PnL.

        Formula: count(net_pnl_i > 0) / total_trades * 100

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        if total_trades == 0:
            return 0.0
        return float((wins.size / total_trades) * 100)


    def _compute_avg_trade_pnl(self, pnls: np.ndarray) -> float:
        """
        Calculate mean net PnL per trade.

        Formula: mean(net_pnl_i)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        return float(pnls.mean()) if pnls.size > 0 else 0.0


    def _compute_avg_win(self, wins: np.ndarray) -> float:
        """
        Calculate mean net PnL among winning trades.

        Formula: mean(net_pnl_i for net_pnl_i > 0)

        Edge cases:
            - Returns 0.0 when there are no winning trades.
        """
        return float(wins.mean()) if wins.size > 0 else 0.0


    def _compute_avg_loss(self, losses: np.ndarray) -> float:
        """
        Calculate mean net PnL among losing trades.

        Formula: mean(net_pnl_i for net_pnl_i < 0)

        Edge cases:
            - Returns 0.0 when there are no losing trades.
            - Returned value is negative by definition.
        """
        return float(losses.mean()) if losses.size > 0 else 0.0


    def _compute_profit_factor(self, gross_profit: float, gross_loss: float) -> float:
        """
        Calculate profit factor.

        Formula: gross_profit / gross_loss

        Edge cases:
            - Returns inf when profits exist and gross_loss is zero.
            - Returns NaN when both gross_profit and gross_loss are zero.
        """
        if gross_loss > 0:
            return float(gross_profit / gross_loss)
        return float(np.inf) if gross_profit > 0 else float(np.nan)


    def _compute_best_trade(self, pnls: np.ndarray) -> float:
        """
        Calculate best trade net PnL.

        Formula: max(net_pnl_i)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        return float(pnls.max()) if pnls.size > 0 else 0.0


    def _compute_worst_trade(self, pnls: np.ndarray) -> float:
        """
        Calculate worst trade net PnL.

        Formula: min(net_pnl_i)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        return float(pnls.min()) if pnls.size > 0 else 0.0


    def _compute_median_trade(self, pnls: np.ndarray) -> float:
        """
        Calculate median trade net PnL.

        Formula: median(net_pnl_i)

        Edge cases:
            - Returns 0.0 when there are no trades.
        """
        return float(np.median(pnls)) if pnls.size > 0 else 0.0


    def kpis(self) -> dict[str, float]:
        pnls = self._trade_pnls()
        wins = self._winning_pnls(pnls)
        losses = self._losing_pnls(pnls)
        total_trades = self._compute_total_trades()
        net_pnl = self._compute_net_pnl()
        total_return_pct = self._compute_return_pct(self.final_balance)
        gross_profit = self._compute_gross_profit(wins)
        gross_loss = self._compute_gross_loss(losses)
        strategy_curve = self._strategy_equity_curve()
        strategy_returns = strategy_curve.pct_change().dropna()
        buy_and_hold_curve = self._buy_and_hold_equity_curve()
        buy_and_hold_final = self._compute_buy_and_hold_final_balance(buy_and_hold_curve)
        buy_and_hold_return_pct = self._compute_buy_and_hold_return_pct(buy_and_hold_final)

        metrics = {
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "net_pnl": net_pnl,
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "total_fees": self._compute_total_fees(),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "win_rate_pct": self._compute_win_rate_pct(wins, total_trades),
            "avg_trade_pnl": self._compute_avg_trade_pnl(pnls),
            "avg_win": self._compute_avg_win(wins),
            "avg_loss": self._compute_avg_loss(losses),
            "profit_factor": self._compute_profit_factor(gross_profit, gross_loss),
            "max_drawdown_pct": self._compute_max_drawdown_pct(strategy_curve),
            "sharpe_ratio": self._compute_sharpe_ratio(strategy_returns),
            "best_trade": self._compute_best_trade(pnls),
            "worst_trade": self._compute_worst_trade(pnls),
            "median_trade": self._compute_median_trade(pnls),
            "avg_trade_duration_minutes": self._compute_avg_trade_duration_minutes(),
            "buy_and_hold_final_balance": buy_and_hold_final,
            "buy_and_hold_return_pct": buy_and_hold_return_pct,
            "buy_and_hold_max_drawdown_pct": self._compute_buy_and_hold_max_drawdown_pct(
                buy_and_hold_curve,
            ),
            "return_diff_vs_buy_and_hold_pct": self._compute_return_diff_vs_buy_and_hold_pct(
                total_return_pct,
                buy_and_hold_return_pct,
            ),
        }

        return metrics
