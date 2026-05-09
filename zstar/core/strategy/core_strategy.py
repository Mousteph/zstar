from abc import ABC, abstractmethod
import pandas as pd

from zstar.core.exceptions import StrategyValidationError


def _format_issue_message(messages: list[str]) -> str:
    return "\n- ".join(messages)


def load_strategy_from_code(strategy_code: str) -> "CoreStrategy":
    from zstar.core.strategy.validate_strategy import ValidateStrategy

    validate_strategy = ValidateStrategy(strategy_filename="<memory>")
    strategy, result = validate_strategy.validate_result(strategy_code)

    if result.total_errors > 0:
        error_messages = [
            f"{issue.category}: {issue.message}"
            + (f" (line {issue.line})" if issue.line is not None else "")
            for issue in result.issues
        ]
        raise StrategyValidationError(_format_issue_message(error_messages))

    if strategy is None:
        raise StrategyValidationError("Strategy loading failed without explicit validation errors.")

    return strategy


class CoreStrategy(ABC):
    def __init__(self):
        self._name = self.__class__.__name__

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_entry"] = 0

        return data

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_entry"] = 0

        return data

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_exit"] = 0

        return data

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_exit"] = 0

        return data

    def long_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_take_profit"] = float("nan")

        return data

    def short_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_take_profit"] = float("nan")

        return data

    def long_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["long_stop_loss"] = float("nan")

        return data

    def short_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data["short_stop_loss"] = float("nan")

        return data

    @abstractmethod
    def position_size(self, balance: float, entry_price: float) -> float:
        pass
