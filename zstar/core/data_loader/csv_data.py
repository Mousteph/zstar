import pandas as pd

from zstar.core.data_loader.data_handler import DataHandler
from zstar.core.exceptions import CsvDataError, zstar_error
REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}


def validate_csv_columns(data: pd.DataFrame, filename: str) -> pd.DataFrame:
    data.columns = [str(column).strip().lower() for column in data.columns]
    missing_columns = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing_columns:
        raise CsvDataError(f"CSV file {filename} is missing required columns: {', '.join(missing_columns)}.")

    return data


def prepare_csv_data(data: pd.DataFrame, filename: str) -> pd.DataFrame:
    if data.empty:
        raise CsvDataError(f"CSV file {filename} is empty.")

    data = validate_csv_columns(data, filename)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date"])
    if data.empty:
        raise CsvDataError(f"CSV file {filename} does not contain readable dates.")

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    invalid_columns = [column for column in numeric_columns if data[column].isna().any()]
    if invalid_columns:
        raise CsvDataError(
            f"CSV file {filename} contains non-numeric values in required columns: {', '.join(invalid_columns)}."
        )

    data = data.set_index("date").sort_index()
    
    return data[["open", "high", "low", "close", "volume"]]


def detect_interval(data: pd.DataFrame) -> str:
    if len(data.index) < 2:
        return "1d"

    deltas = data.index.to_series().diff().dropna()
    if deltas.empty:
        return "1d"

    median_seconds = float(deltas.dt.total_seconds().median())
    if median_seconds <= 120:
        return "1m"
    if median_seconds <= 600:
        return "5m"
    if median_seconds <= 1320:
        return "15m"
    if median_seconds <= 2700:
        return "30m"
    if median_seconds <= 5400:
        return "1h"
    return "1d"


class CsvData(DataHandler):
    def __init__(self, csv_path: str):
        with zstar_error(CsvDataError, f"An error occurred while reading CSV file {csv_path}"):
            data = pd.read_csv(csv_path)

        prepared = prepare_csv_data(data, csv_path)
        super().__init__(prepared, interval=detect_interval(prepared))
