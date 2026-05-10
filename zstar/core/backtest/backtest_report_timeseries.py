from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from zstar.core.trade_order import Trade


def strategy_equity_curve(
    initial_balance: float,
    trades: Sequence[Trade],
    data: pd.DataFrame,
) -> pd.Series:
    if data.empty:
        return pd.Series(dtype=float, name="strategy")

    equity_values = [
        _compute_strategy_equity_at(initial_balance, trades, timestamp, close_price)
        for timestamp, close_price in data["close"].astype(float).items()
    ]
    return pd.Series(equity_values, index=data.index, name="strategy")


def buy_and_hold_equity_curve(initial_balance: float, data: pd.DataFrame) -> pd.Series:
    if data.empty:
        return pd.Series(dtype=float, name="buy_and_hold")

    close_prices = data["close"].astype(float)
    first_close = float(close_prices.iloc[0])
    if first_close <= 0:
        return pd.Series(dtype=float, name="buy_and_hold")

    units = initial_balance / first_close
    return (close_prices * units).rename("buy_and_hold")


def compute_equity_curve(initial_balance: float, trades: Sequence[Trade], data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "strategy": strategy_equity_curve(initial_balance, trades, data),
            "buy_and_hold": buy_and_hold_equity_curve(initial_balance, data),
        }
    )


def _compute_strategy_equity_at(
    initial_balance: float,
    trades: Sequence[Trade],
    timestamp: pd.Timestamp,
    price: float,
) -> float:
    realized = sum(trade.net_pnl for trade in trades if trade.exit_datetime <= timestamp)
    open_pnl = sum(
        _compute_unrealized_trade_pnl(trade, price) - trade.entry_fee
        for trade in trades
        if trade.entry_datetime <= timestamp < trade.exit_datetime
    )
    return float(initial_balance + realized + open_pnl)


def _compute_unrealized_trade_pnl(trade: Trade, price: float) -> float:
    return float((price - trade.entry_price) * trade.size * trade.side.to_sign())
