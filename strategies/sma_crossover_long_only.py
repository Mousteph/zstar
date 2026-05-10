import pandas as pd

from zstar.core.strategy import CoreStrategy


class SMACrossoverLongOnlyStrategy(CoreStrategy):
    SHORT_WINDOW = 20
    LONG_WINDOW = 50
    STOP_LOSS_MULTIPLIER = 0.97

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_sma"] = data["close"].rolling(window=self.SHORT_WINDOW, min_periods=1).mean()
        data["long_sma"] = data["close"].rolling(window=self.LONG_WINDOW, min_periods=1).mean()
        data["sma_spread"] = data["short_sma"] - data["long_sma"]
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        spread = data["sma_spread"]
        data["long_entry"] = ((spread > 0.0) & (spread.shift(1).fillna(0.0) <= 0.0)).astype(int)
        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        spread = data["sma_spread"]
        data["long_exit"] = ((spread < 0.0) & (spread.shift(1).fillna(0.0) >= 0.0)).astype(int)
        return data

    def long_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_stop_loss"] = data["long_sma"] * self.STOP_LOSS_MULTIPLIER
        return data

    def position_size(self, balance: float, entry_price: float) -> float:
        if entry_price <= 0:
            return 0.0

        return balance / entry_price
