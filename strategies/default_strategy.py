from __future__ import annotations

import numpy as np
import pandas as pd

from zstar.core.strategy import CoreStrategy


class MovingAverageCrossStrategy(CoreStrategy):
    def __init__(self, short_window: int = 20, long_window: int = 50, risk_pct: float = 2.0):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.risk_pct = risk_pct

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_sma"] = data["close"].rolling(window=self.short_window, min_periods=1).mean()
        data["long_sma"] = data["close"].rolling(window=self.long_window, min_periods=1).mean()
        data["sma_spread"] = data["short_sma"] - data["long_sma"]
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_entry"] = (
            (data["sma_spread"] > 0.0) & (data["sma_spread"].shift(1).fillna(0.0) <= 0.0)
        ).astype(int)
        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_exit"] = (
            (data["sma_spread"] < 0.0) & (data["sma_spread"].shift(1).fillna(0.0) >= 0.0)
        ).astype(int)
        return data

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_entry"] = np.zeros(len(data), dtype=int)
        return data

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_exit"] = np.zeros(len(data), dtype=int)
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        if entry_price <= 0:
            return 0.0

        max_risk = balance * (self.risk_pct / 100.0)
        return max(1.0, round(max_risk / entry_price, 4))
