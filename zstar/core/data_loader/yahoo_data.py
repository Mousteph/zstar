import yfinance as yf
import pandas as pd

from zstar.core.data_loader.data_handler import DataHandler
from zstar.core.exceptions import (
    zstar_error,
    MarketDataDownloadError,
    IntervalNotSupportedError,
)   


class YahooData(DataHandler):
    ALLOWED_INTERVALS = {
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "1d",
    }

    def _load_data(self, symbol: str, start_date: str | None, end_date: str | None, interval: str) -> pd.DataFrame:
        if interval not in self.ALLOWED_INTERVALS:
            error_message = f"Interval {interval} is not supported. Allowed intervals are: {self.ALLOWED_INTERVALS}"
            raise IntervalNotSupportedError(error_message)
        
        with zstar_error(MarketDataDownloadError, "An error occurred while downloading market data from Yahoo Finance"):
            data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False,
                progress=False,
                multi_level_index=False,
            )

        if data.empty:
            raise MarketDataDownloadError(f"No data found for symbol {symbol} with the specified parameters.")

        data.columns = [col.lower() for col in data.columns]
        data.sort_index(inplace=True)

        return data


    def __init__(self, symbol: str, start_date: str | None, end_date: str | None, interval: str):
        data = self._load_data(symbol, start_date, end_date, interval)
        
        super().__init__(data, interval=interval)
