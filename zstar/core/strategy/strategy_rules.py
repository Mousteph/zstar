from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from zstar.core.strategy.core_strategy import CoreStrategy
from zstar.core.strategy.strategy_error_formatter import StrategyValidationErrorFormatter
from zstar.core.strategy.validation_models import ValidationIssue


class StrategyRules:
    REQUIRED_SIGNAL_COLUMNS = ["long_entry", "short_entry", "long_exit", "short_exit"]
    RISK_PRICE_COLUMNS = ["long_take_profit", "short_take_profit", "long_stop_loss", "short_stop_loss"]
    DEFAULT_SAMPLE_ROWS = 200
    DEFAULT_SAMPLE_SEED = 42

    def __init__(self, strategy_filename: str, strategy_path: Optional[Path] = None):
        self.strategy_filename = strategy_filename
        self._formatter = StrategyValidationErrorFormatter(strategy_filename, strategy_path)

    def validate(self, strategy: CoreStrategy, code: str) -> List[ValidationIssue]:
        signal_data, signal_error = self._run_signal_pipeline(strategy, code)
        if signal_error is not None:
            return [signal_error]

        issues = self._validate_required_columns(signal_data)

        size_error = self._validate_position_size(strategy, code)
        if size_error is not None:
            issues.append(size_error)

        return issues

    def _run_signal_pipeline(
        self,
        strategy: CoreStrategy,
        code: str,
    ) -> Tuple[Optional[pd.DataFrame], Optional[ValidationIssue]]:
        data = self._build_sample_data()

        try:
            data = strategy.calculate_indicators(data)
            data = strategy.long_entry_signals(data)
            data = strategy.short_entry_signals(data)
            data = strategy.long_exit_signals(data)
            data = strategy.short_exit_signals(data)
            data = strategy.long_take_profit_signals(data)
            data = strategy.short_take_profit_signals(data)
            data = strategy.long_stop_loss_signals(data)
            data = strategy.short_stop_loss_signals(data)
            return data, None
        except Exception as error:
            message, line, file_name = self._formatter.format_exception_detail(error, code)
            issue = ValidationIssue("logic", file_name, line, message)
            return None, issue

    def _validate_required_columns(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for column_name in self.REQUIRED_SIGNAL_COLUMNS:
            if column_name not in data.columns:
                message = f"Missing required signal column '{column_name}' from strategy methods."
                issues.append(ValidationIssue("template", self.strategy_filename, None, message))
                continue

            signal_data = data[column_name]
            if not self._is_signal_dtype_valid(signal_data):
                message = f"Signal column '{column_name}' must contain numeric or boolean values."
                issues.append(ValidationIssue("type", self.strategy_filename, None, message))
                continue

            if not self._contains_only_binary_signals(signal_data):
                message = f"Signal column '{column_name}' must contain only 0/1, True/False, or missing values."
                issues.append(ValidationIssue("type", self.strategy_filename, None, message))

        for column_name in self.RISK_PRICE_COLUMNS:
            if column_name in data.columns and not pd.api.types.is_numeric_dtype(data[column_name]):
                message = f"Risk price column '{column_name}' must contain numeric values."
                issues.append(ValidationIssue("type", self.strategy_filename, None, message))

        return issues

    def _validate_position_size(
        self,
        strategy: CoreStrategy,
        code: str,
    ) -> Optional[ValidationIssue]:
        try:
            size = strategy.position_size(10000, 100)
        except Exception as error:
            message, line, file_name = self._formatter.format_exception_detail(error, code)
            return ValidationIssue("logic", file_name, line, message)

        is_numeric = isinstance(size, (int, float, np.integer, np.floating))
        if not is_numeric or not np.isfinite(float(size)) or float(size) <= 0:
            message = "position_size(balance, entry_price) must return a finite positive numeric value."
            return ValidationIssue("type", self.strategy_filename, None, message)

        return None

    def _build_sample_data(self, rows: Optional[int] = None) -> pd.DataFrame:
        rows = self.DEFAULT_SAMPLE_ROWS if rows is None else rows
        dates = pd.date_range(start="2020-01-01", periods=rows, freq="D")
        rng = np.random.default_rng(seed=self.DEFAULT_SAMPLE_SEED)

        open_prices = rng.random(rows) * 100
        close_prices = rng.random(rows) * 100
        high_noise = rng.random(rows) * 10
        low_noise = rng.random(rows) * 10

        data = {
            "open": open_prices,
            "high": np.maximum(open_prices, close_prices) + high_noise,
            "low": np.minimum(open_prices, close_prices) - low_noise,
            "close": close_prices,
            "volume": rng.integers(1, 1000, size=rows),
        }
        return pd.DataFrame(data, index=dates)

    def _is_signal_dtype_valid(self, data: pd.Series) -> bool:
        return pd.api.types.is_bool_dtype(data) or pd.api.types.is_numeric_dtype(data)

    def _contains_only_binary_signals(self, data: pd.Series) -> bool:
        normalized = data.dropna()
        if normalized.empty:
            return True

        return normalized.isin([0, 1, False, True]).all()
