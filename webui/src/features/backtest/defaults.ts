import type { BacktestSettings } from "@/types/backtest";

export const defaultStrategyCode = `import numpy as np
import pandas as pd
from zstar.core.strategy import CoreStrategy

class MovingAverageCrossStrategy(CoreStrategy):
    def __init__(self, short_window=20, long_window=50, risk_pct=2.0):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.risk_pct = risk_pct

    def calculate_indicators(self, data):
        data["short_sma"] = data["close"].rolling(window=self.short_window, min_periods=1).mean()
        data["long_sma"] = data["close"].rolling(window=self.long_window, min_periods=1).mean()
        return data

    def long_entry_signals(self, data):
        data["long_entry"] = ((data["short_sma"] > data["long_sma"]) &
                              (data["short_sma"].shift(1) <= data["long_sma"].shift(1))).astype(int)
        return data

    def long_exit_signals(self, data):
        data["long_exit"] = ((data["short_sma"] < data["long_sma"]) &
                             (data["short_sma"].shift(1) >= data["long_sma"].shift(1))).astype(int)
        return data

    def short_entry_signals(self, data):
        data["short_entry"] = 0
        return data

    def short_exit_signals(self, data):
        data["short_exit"] = 0
        return data

    def position_size(self, balance, entry_price):
        max_risk = balance * (self.risk_pct / 100)
        if entry_price <= 0:
            return 0
        return max(1, round(max_risk / entry_price, 4))

strategy = MovingAverageCrossStrategy()
`;

export const defaultBacktestSettings: BacktestSettings = {
  symbol: "AAPL",
  startDate: "2024-01-01",
  endDate: "2025-01-01",
  interval: "1d",
  initialBalance: 100000,
  entryFeePct: 0.05,
  exitFeePct: 0.05,
  slippagePct: 0.02,
  slippageSeed: "42",
};
