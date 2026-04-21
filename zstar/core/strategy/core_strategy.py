from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
from zstar.core.exceptions import StrategyValidationError


def load_strategy_from_code(strategy_code: str) -> "CoreStrategy":
    from zstar.core.strategy.validate_strategy import ValidateStrategy
    validate_strategy = ValidateStrategy()
    strategy, errors = validate_strategy.validate(strategy_code)

    if errors:
        message = "\n- ".join(errors)
        raise StrategyValidationError(message)

    return strategy


def load_strategy_from_file(strategy_path: Path | str) -> "CoreStrategy":
    path = Path(strategy_path)
    try:
        strategy_code = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StrategyValidationError(f"Unable to read strategy file '{path}': {exc}") from exc

    return load_strategy_from_code(strategy_code)


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
