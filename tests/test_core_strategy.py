import pandas as pd
import pytest

from zstar.core.core_strategy import CoreStrategy, load_strategy_from_code
from zstar.core.exceptions import StrategyExecutionError


VALID_STRATEGY_CODE = """
from zstar.core.core_strategy import CoreStrategy

class MyStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0

strategy = MyStrategy()
"""


def test_load_strategy_from_code_returns_strategy_instance():
    strategy = load_strategy_from_code(VALID_STRATEGY_CODE)

    assert isinstance(strategy, CoreStrategy)


def test_load_strategy_from_code_wraps_execution_errors():
    with pytest.raises(StrategyExecutionError):
        load_strategy_from_code("this is invalid python code")


def test_core_strategy_default_signal_methods_add_expected_columns():
    class MinimalStrategy(CoreStrategy):
        def position_size(self, balance: float, entry_price: float) -> float:
            return 1.0

    strategy = MinimalStrategy()
    data = pd.DataFrame({"open": [1.0], "close": [1.1]})

    data = strategy.long_entry_signals(data)
    data = strategy.short_entry_signals(data)
    data = strategy.long_exit_signals(data)
    data = strategy.short_exit_signals(data)

    assert list(data["long_entry"]) == [0]
    assert list(data["short_entry"]) == [0]
    assert list(data["long_exit"]) == [0]
    assert list(data["short_exit"]) == [0]
