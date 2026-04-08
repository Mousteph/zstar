import pytest
from pydantic import ValidationError

from zstar.core.data_loader.data_loader_model import DataLoaderConfigModel


def test_data_loader_model_normalizes_symbol_and_keeps_interval():
    config = DataLoaderConfigModel(
        symbol=" aapl ",
        start_date="2025-01-01",
        end_date="2025-01-10",
        interval="1h",
    )

    assert config.symbol == "AAPL"
    assert config.interval == "1h"


def test_data_loader_model_rejects_empty_symbol_after_strip():
    with pytest.raises(ValidationError):
        DataLoaderConfigModel(symbol="   ")


def test_data_loader_model_rejects_end_date_before_start_date():
    with pytest.raises(ValidationError):
        DataLoaderConfigModel(
            symbol="MSFT",
            start_date="2025-01-10",
            end_date="2025-01-01",
            interval="1d",
        )
