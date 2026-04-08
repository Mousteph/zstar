from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from zstar.core.exceptions import (
    zstar_error,
    StrategyExecutionError,
    StrategyValidationError
)

def load_strategy_from_code(strategy_code: str) -> CoreStrategy:
    scope = {
        "__builtins__": __builtins__,
        "CoreStrategy": CoreStrategy,
        "pd": pd,
        "np": np,
    }

    with zstar_error(StrategyExecutionError, "An error occurred while loading the strategy from code"):
        exec(strategy_code, scope, scope)
    
    with zstar_error(StrategyValidationError, "The provided strategy code does not define a valid strategy class"):
        strategy = scope.get("strategy")

    return strategy


class CoreStrategy(ABC):
    def __init__(self):
        self._name = self.__class__.__name__


    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        return data

    
    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['long_entry'] = 0

        return data

    
    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['short_entry'] = 0

        return data

    
    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['long_exit'] = 0

        return data
    

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['short_exit'] = 0

        return data


    @abstractmethod
    def position_size(self, balance: float, entry_price: float) -> float:
        pass
