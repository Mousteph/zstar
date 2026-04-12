import pandas as pd
import pytest

from zstar.core.strategy.core_strategy import CoreStrategy, load_strategy_from_code
from zstar.core.exceptions import StrategyExecutionError, StrategyValidationError


VALID_STRATEGY_CODE = """
class MyStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0
"""

MULTI_STRATEGY_CODE = """
class FirstStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0

class SecondStrategy(CoreStrategy):
    def position_size(self, balance, entry_price):
        return 1.0
"""


REQUIRES_ARGS_STRATEGY_CODE = """
class ParamStrategy(CoreStrategy):
    def __init__(self, risk_pct):
        super().__init__()
        self.risk_pct = risk_pct

    def position_size(self, balance, entry_price):
        return self.risk_pct
"""



def test_load_strategy_from_code_returns_strategy_instance_for_class_only_code():
    strategy = load_strategy_from_code(VALID_STRATEGY_CODE)

    assert isinstance(strategy, CoreStrategy)
    assert strategy.__class__.__name__ == "MyStrategy"


def test_load_strategy_from_code_wraps_execution_errors():
    with pytest.raises(StrategyValidationError):
        load_strategy_from_code("this is invalid python code")


def test_load_strategy_from_code_rejects_multiple_strategy_classes():
    with pytest.raises(StrategyValidationError):
        load_strategy_from_code(MULTI_STRATEGY_CODE)


def test_load_strategy_from_code_rejects_missing_strategy_class():
    with pytest.raises(StrategyValidationError):
        load_strategy_from_code("value = 1")


def test_load_strategy_from_code_rejects_non_zero_arg_strategy_class():
    with pytest.raises(StrategyValidationError):
        load_strategy_from_code(REQUIRES_ARGS_STRATEGY_CODE)


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
