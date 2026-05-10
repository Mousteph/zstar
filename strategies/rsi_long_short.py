import numpy as np
import pandas as pd

from zstar.core.strategy import CoreStrategy


class RSILongShortStrategy(CoreStrategy):
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30.0
    RSI_OVERBOUGHT = 70.0
    RSI_EXIT_LEVEL = 50.0
    STOP_LOSS_LONG_MULTIPLIER = 0.97
    TAKE_PROFIT_LONG_MULTIPLIER = 1.05
    STOP_LOSS_SHORT_MULTIPLIER = 1.03
    TAKE_PROFIT_SHORT_MULTIPLIER = 0.95
    POSITION_SIZE_PCT = 0.10

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        close = data["close"].astype(float)
        data["rsi"] = self._compute_rsi(close)

        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        rsi = data["rsi"]
        data["long_entry"] = (
            (rsi < self.RSI_OVERSOLD)
            & (rsi.shift(1).fillna(self.RSI_OVERSOLD) >= self.RSI_OVERSOLD)
        ).astype(int)

        return data

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        rsi = data["rsi"]
        data["short_entry"] = (
            (rsi > self.RSI_OVERBOUGHT)
            & (rsi.shift(1).fillna(self.RSI_OVERBOUGHT) <= self.RSI_OVERBOUGHT)
        ).astype(int)

        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        rsi = data["rsi"]
        data["long_exit"] = (
            (rsi < self.RSI_EXIT_LEVEL) &
            (rsi.shift(1).fillna(self.RSI_EXIT_LEVEL) >= self.RSI_EXIT_LEVEL)
        ).astype(int)

        return data

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        rsi = data["rsi"]
        data["short_exit"] = (
            (rsi > self.RSI_EXIT_LEVEL) &
            (rsi.shift(1).fillna(self.RSI_EXIT_LEVEL) <= self.RSI_EXIT_LEVEL)
        ).astype(int)
        
        return data

    def long_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_take_profit"] = data["close"] * self.TAKE_PROFIT_LONG_MULTIPLIER
        return data

    def short_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_take_profit"] = data["close"] * self.TAKE_PROFIT_SHORT_MULTIPLIER
        return data

    def long_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_stop_loss"] = data["close"] * self.STOP_LOSS_LONG_MULTIPLIER
        return data

    def short_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_stop_loss"] = data["close"] * self.STOP_LOSS_SHORT_MULTIPLIER
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        if entry_price <= 0:
            return 0.0

        return (balance * self.POSITION_SIZE_PCT) / entry_price

    def _compute_rsi(self, close: pd.Series) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)

        avg_gain = gain.ewm(alpha=1 / self.RSI_PERIOD, adjust=False, min_periods=self.RSI_PERIOD).mean()
        avg_loss = loss.ewm(alpha=1 / self.RSI_PERIOD, adjust=False, min_periods=self.RSI_PERIOD).mean()

        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)
