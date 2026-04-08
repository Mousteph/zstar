import pandas as pd
import pytest

from zstar.core.data_loader.data_handler import DataHandler


def test_data_handler_returns_copy_and_interval():
    source = pd.DataFrame({"open": [1.0, 2.0], "close": [1.1, 2.1]})
    handler = DataHandler(source, interval="15m")

    data_copy = handler.get_data()
    data_copy.loc[0, "open"] = 999.0

    assert handler.get_interval() == "15m"
    assert source.loc[0, "open"] == pytest.approx(1.0)
