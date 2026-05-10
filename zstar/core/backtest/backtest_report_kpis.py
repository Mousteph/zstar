from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from zstar.core.backtest.backtest_report_timeseries import buy_and_hold_equity_curve
from zstar.core.backtest.backtest_report_timeseries import strategy_equity_curve
from zstar.core.trade_order import Trade


def compute_kpis(
    initial_balance: float,
    final_balance: float,
    trades: Sequence[Trade],
    data: pd.DataFrame,
    interval: str,
    risk_free_rate: float = 0.0,
) -> dict[str, float | int]:
    pnls = _trade_pnls(trades)
    wins = _winning_pnls(pnls)
    losses = _losing_pnls(pnls)
    total_trades = _compute_total_trades(trades)
    net_pnl = _compute_net_pnl(initial_balance, final_balance)
    total_return_pct = _compute_return_pct(initial_balance, final_balance)
    gross_profit = _compute_gross_profit(wins)
    gross_loss = _compute_gross_loss(losses)
    strategy_curve = strategy_equity_curve(initial_balance, trades, data)
    strategy_returns = strategy_curve.pct_change().dropna()
    buy_and_hold_curve = buy_and_hold_equity_curve(initial_balance, data)
    buy_and_hold_final = _compute_buy_and_hold_final_balance(initial_balance, buy_and_hold_curve)
    buy_and_hold_return_pct = _compute_buy_and_hold_return_pct(initial_balance, buy_and_hold_final)

    metrics = {
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "net_pnl": net_pnl,
        "total_return_pct": total_return_pct,
        "total_trades": total_trades,
        "total_fees": _compute_total_fees(trades),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "win_rate_pct": _compute_win_rate_pct(wins, total_trades),
        "avg_trade_pnl": _compute_avg_trade_pnl(pnls),
        "avg_win": _compute_avg_win(wins),
        "avg_loss": _compute_avg_loss(losses),
        "profit_factor": _compute_profit_factor(gross_profit, gross_loss),
        "max_drawdown_pct": _compute_max_drawdown_pct(strategy_curve),
        "sharpe_ratio": _compute_sharpe_ratio(interval, risk_free_rate, strategy_returns),
        "best_trade": _compute_best_trade(pnls),
        "worst_trade": _compute_worst_trade(pnls),
        "median_trade": _compute_median_trade(pnls),
        "avg_trade_duration_minutes": _compute_avg_trade_duration_minutes(trades),
        "buy_and_hold_final_balance": buy_and_hold_final,
        "buy_and_hold_return_pct": buy_and_hold_return_pct,
        "buy_and_hold_max_drawdown_pct": _compute_buy_and_hold_max_drawdown_pct(
            equity_curve=buy_and_hold_curve,
        ),
        "return_diff_vs_buy_and_hold_pct": _compute_return_diff_vs_buy_and_hold_pct(
            total_return_pct,
            buy_and_hold_return_pct,
        ),
    }

    return metrics


def _compute_return_pct(initial_balance: float, final_value: float) -> float:
    if initial_balance == 0:
        return 0.0
    return ((final_value - initial_balance) / initial_balance) * 100


def _compute_max_drawdown_pct(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0

    peak = equity_curve.cummax()
    drawdown_pct = (equity_curve[peak > 0] / peak[peak > 0] - 1.0) * 100
    if drawdown_pct.empty:
        return 0.0
    return float(drawdown_pct.min())


def _compute_buy_and_hold_final_balance(initial_balance: float, buy_and_hold_curve: pd.Series) -> float:
    if buy_and_hold_curve.empty:
        return float(initial_balance)
    return float(buy_and_hold_curve.iloc[-1])


def _compute_buy_and_hold_return_pct(initial_balance: float, buy_and_hold_final: float) -> float:
    return _compute_return_pct(initial_balance, buy_and_hold_final)


def _compute_buy_and_hold_max_drawdown_pct(equity_curve: pd.Series) -> float:
    return _compute_max_drawdown_pct(equity_curve)


def _compute_return_diff_vs_buy_and_hold_pct(
    strategy_return_pct: float,
    buy_and_hold_return_pct: float,
) -> float:
    return strategy_return_pct - buy_and_hold_return_pct


def _compute_sharpe_ratio(interval: str, risk_free_rate: float, strategy_returns: pd.Series) -> float:
    if strategy_returns.size <= 1:
        return float(np.nan)

    returns_std = strategy_returns.std(ddof=1)
    if returns_std <= 0:
        return float(np.nan)

    annualization_factor = _annualization_factor(interval)
    excess_return = strategy_returns.mean() - (risk_free_rate / annualization_factor)
    return float((excess_return / returns_std) * np.sqrt(annualization_factor))


def _annualization_factor(interval: str) -> float:
    trading_days_per_year = 252.0
    trading_minutes_per_day = 390.0
    interval_value = interval.strip().lower()

    if interval_value.endswith("d"):
        day_count = _parse_positive_number(interval_value[:-1])
        if day_count is not None:
            return trading_days_per_year / day_count
        return trading_days_per_year

    if interval_value.endswith("h"):
        hour_count = _parse_positive_number(interval_value[:-1])
        if hour_count is not None:
            bars_per_day = trading_minutes_per_day / (hour_count * 60.0)
            return trading_days_per_year * bars_per_day

    if interval_value.endswith("m"):
        minute_count = _parse_positive_number(interval_value[:-1])
        if minute_count is not None:
            bars_per_day = trading_minutes_per_day / minute_count
            return trading_days_per_year * bars_per_day

    return trading_days_per_year


def _parse_positive_number(value: str) -> float | None:
    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    return parsed_value if parsed_value > 0 else None


def _compute_avg_trade_duration_minutes(trades: Sequence[Trade]) -> float:
    if len(trades) == 0:
        return 0.0

    durations = [
        (trade.exit_datetime - trade.entry_datetime).total_seconds() / 60
        for trade in trades
    ]
    return float(np.mean(durations))


def _trade_pnls(trades: Sequence[Trade]) -> np.ndarray:
    return np.array([trade.net_pnl for trade in trades], dtype=float)


def _winning_pnls(pnls: np.ndarray) -> np.ndarray:
    return pnls[pnls > 0]


def _losing_pnls(pnls: np.ndarray) -> np.ndarray:
    return pnls[pnls < 0]


def _compute_net_pnl(initial_balance: float, final_balance: float) -> float:
    return float(final_balance - initial_balance)


def _compute_total_trades(trades: Sequence[Trade]) -> int:
    return len(trades)


def _compute_total_fees(trades: Sequence[Trade]) -> float:
    return float(sum(trade.total_fees for trade in trades))


def _compute_gross_profit(wins: np.ndarray) -> float:
    return float(wins.sum()) if wins.size > 0 else 0.0


def _compute_gross_loss(losses: np.ndarray) -> float:
    return float(abs(losses.sum())) if losses.size > 0 else 0.0


def _compute_win_rate_pct(wins: np.ndarray, total_trades: int) -> float:
    if total_trades == 0:
        return 0.0
    return float((wins.size / total_trades) * 100)


def _compute_avg_trade_pnl(pnls: np.ndarray) -> float:
    return float(pnls.mean()) if pnls.size > 0 else 0.0


def _compute_avg_win(wins: np.ndarray) -> float:
    return float(wins.mean()) if wins.size > 0 else 0.0


def _compute_avg_loss(losses: np.ndarray) -> float:
    return float(losses.mean()) if losses.size > 0 else 0.0


def _compute_profit_factor(gross_profit: float, gross_loss: float) -> float:
    if gross_loss > 0:
        return float(gross_profit / gross_loss)
    return float(np.inf) if gross_profit > 0 else float(np.nan)


def _compute_best_trade(pnls: np.ndarray) -> float:
    return float(pnls.max()) if pnls.size > 0 else 0.0


def _compute_worst_trade(pnls: np.ndarray) -> float:
    return float(pnls.min()) if pnls.size > 0 else 0.0


def _compute_median_trade(pnls: np.ndarray) -> float:
    return float(np.median(pnls)) if pnls.size > 0 else 0.0
