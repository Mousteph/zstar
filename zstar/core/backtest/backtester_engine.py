from typing import Any

import numpy as np
import pandas as pd

from zstar.core.strategy.core_strategy import CoreStrategy
from zstar.core.trade_order import Order, Trade
from zstar.core.data_loader import DataHandler
from zstar.core.enums import TradeSide
from zstar.core.backtest.backtest_config_model import BacktestConfigModel
from zstar.core.backtest.backtest_report import BacktestReport
from zstar.core.backtest.asset_portfolio import Portfolio
from zstar.core.exceptions import func_errors, BacktestExecutionError


class BacktesterEngine:
    def __init__(self, strategy: CoreStrategy, data_handler: DataHandler, config: BacktestConfigModel) -> None:
        self.strategy = strategy
        self.data_handler = data_handler

        self.initial_balance = config.initial_balance
        self._entry_fee_rate = self._pct_to_rate(config.entry_fee_pct)
        self._exit_fee_rate = self._pct_to_rate(config.exit_fee_pct)
        self._slippage_rate = self._pct_to_rate(config.slippage_pct)
        self._slippage_seed = config.slippage_seed

        self.reset()

    def reset(self) -> None:
        self._portfolio = Portfolio()
        self._closed_trades: list[Trade] = []
        self._current_balance = self.initial_balance
        self._rng = np.random.default_rng(self._slippage_seed)


    def _pct_to_rate(self, pct_value: float) -> float:
        return pct_value / 100.0


    def _simulate_slippage(self, price: float, side: TradeSide, is_entry: bool) -> float:
        if self._slippage_rate == 0:
            return price

        slip_factor = self._rng.uniform(0.0, self._slippage_rate)

        # Apply adverse slippage: buys pay up, sells receive less.
        if (is_entry and side.is_long()) or (not is_entry and side.is_short()):
            return price * (1.0 + slip_factor)

        return price * (1.0 - slip_factor)


    def _should_mark_position_pending_close(self, row: Any) -> bool:
        if not self._portfolio.is_position_open():
            return False

        side = self._portfolio.get_position().get_side()
        return (side.is_long() and row.long_exit) or (side.is_short() and row.short_exit)


    @func_errors(BacktestExecutionError, "An error occurred during backtest execution")
    def run_backtest(self) -> BacktestReport:
        self.reset()

        data = self.data_handler.get_data()
        data = self.strategy.calculate_indicators(data)
        data = self.strategy.long_entry_signals(data)
        data = self.strategy.short_entry_signals(data)
        data = self.strategy.long_exit_signals(data)
        data = self.strategy.short_exit_signals(data)

        for row in data.itertuples():
            open_price = row.open
            timestamp = row.Index

            if self._portfolio.is_position_pending_close():
                self._close_position(open_price, timestamp)

            if self._portfolio.is_position_pending_open():
                self._open_position(open_price, timestamp)

            if self._should_mark_position_pending_close(row):
                self._portfolio.set_pending_close()

            if not self._portfolio.has_position() and row.long_entry:
                self._prepare_entry_order(TradeSide.LONG)

            if not self._portfolio.has_position() and row.short_entry:
                self._prepare_entry_order(TradeSide.SHORT)

        if self._portfolio.is_position_open():
            self._close_position(float(data.iloc[-1].close), data.index[-1])

        return BacktestReport(
            initial_balance=self.initial_balance,
            final_balance=self._current_balance,
            trades=self._closed_trades,
            data=data,
            interval=self.data_handler.get_interval(),
        )


    def _close_position(self, price: float, timestamp: pd.Timestamp) -> None:
        if not (self._portfolio.is_position_pending_close() or self._portfolio.is_position_open()):
            return

        order = self._portfolio.get_position()
        execution_price = self._simulate_slippage(
            price=price,
            side=order.get_side(),
            is_entry=False,
        )
        exit_fee = execution_price * order.get_size() * self._exit_fee_rate
        order.close(price=execution_price, datetime=timestamp, fee=exit_fee)
        trade = order.to_trade()

        self._closed_trades.append(trade)
        self._portfolio = Portfolio()

        self._current_balance += trade.entry_price * trade.size + trade.raw_pnl - trade.exit_fee


    def _open_position(self, price: float, timestamp: pd.Timestamp) -> None:
        if not self._portfolio.is_position_pending_open():
            return

        order = self._portfolio.get_position()
        execution_price = self._simulate_slippage(
            price=price,
            side=order.get_side(),
            is_entry=True,
        )
        size = self.strategy.position_size(balance=self._current_balance, entry_price=execution_price)
        entry_fee = execution_price * size * self._entry_fee_rate
        order.open(price=execution_price, datetime=timestamp, size=size, fee=entry_fee)

        self._current_balance -= execution_price * size + entry_fee


    def _prepare_entry_order(self, side: TradeSide) -> None:
        self._portfolio.open_position(Order(side=side))
