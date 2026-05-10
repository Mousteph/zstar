import pytest
from pydantic import ValidationError

from zstar.api.backtest.models import YahooDataLoaderConfigModel
from zstar.core.data_loader.csv_data import CsvData


def test_data_loader_model_normalizes_symbol_and_keeps_interval():
    config = YahooDataLoaderConfigModel(
        source="yahoo",
        symbol=" aapl ",
        start_date="2025-01-01",
        end_date="2025-01-10",
        interval="1h",
    )

    assert config.symbol == "AAPL"
    assert config.interval == "1h"


def test_data_loader_model_rejects_empty_symbol_after_strip():
    with pytest.raises(ValidationError):
        YahooDataLoaderConfigModel(source="yahoo", symbol="   ")


def test_data_loader_model_rejects_end_date_before_start_date():
    with pytest.raises(ValidationError):
        YahooDataLoaderConfigModel(
            source="yahoo",
            symbol="MSFT",
            start_date="2025-01-10",
            end_date="2025-01-01",
            interval="1d",
        )


def test_data_loader_model_parses_dates_before_comparison():
    config = YahooDataLoaderConfigModel(
        source="yahoo",
        symbol="MSFT",
        start_date="2025-01-02",
        end_date="2025-01-10",
        interval="1d",
    )

    assert config.start_date.isoformat() == "2025-01-02"
    assert config.end_date.isoformat() == "2025-01-10"


def test_data_loader_model_rejects_invalid_date_format():
    with pytest.raises(ValidationError):
        YahooDataLoaderConfigModel(
            source="yahoo",
            symbol="MSFT",
            start_date="not-a-date",
            interval="1d",
        )


def test_csv_data_loads_ohlcv_file(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    csv_path = data_dir / "sample.csv"
    csv_path.write_text(
        "date,close,high,low,open,volume\n"
        "2025-01-02,102,103,99,100,1000\n"
        "2025-01-01,101,102,98,99,900\n",
        encoding="utf-8",
    )

    handler = CsvData(str(csv_path))
    data = handler.get_data()

    assert handler.get_interval() == "1d"
    assert list(data.columns) == ["open", "high", "low", "close", "volume"]
    assert str(data.index[0].date()) == "2025-01-01"


def test_csv_data_rejects_missing_required_columns(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    csv_path = data_dir / "bad.csv"
    csv_path.write_text("date,open,close\n2025-01-01,99,101\n", encoding="utf-8")

    with pytest.raises(Exception, match="missing required columns"):
        CsvData(str(csv_path))


def test_csv_data_rejects_unreadable_dates(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    csv_path = data_dir / "bad_dates.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\nnot-a-date,99,102,98,101,900\n",
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="readable dates"):
        CsvData(str(csv_path))


def test_csv_data_rejects_non_numeric_ohlcv_values(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    csv_path = data_dir / "bad_values.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n2025-01-01,99,not-a-number,98,101,900\n",
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="non-numeric values"):
        CsvData(str(csv_path))


def test_csv_data_detects_hourly_timeframe(tmp_path):
    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    csv_path = data_dir / "hourly.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n"
        "2025-01-01 00:00:00,99,102,98,101,900\n"
        "2025-01-01 01:00:00,100,103,99,102,950\n"
        "2025-01-01 02:00:00,101,104,100,103,980\n",
        encoding="utf-8",
    )

    handler = CsvData(str(csv_path))
    assert handler.get_interval() == "1h"
