from __future__ import annotations

import inspect
import sys
import traceback
import types
import uuid
from dataclasses import dataclass
from pathlib import Path
from traceback import FrameSummary
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from zstar.core.strategy.core_strategy import CoreStrategy


@dataclass(frozen=True)
class ValidationIssue:
    category: str
    file: str
    line: Optional[int]
    message: str


@dataclass(frozen=True)
class ValidationResult:
    strategy_filename: str
    issues: List[ValidationIssue]

    @property
    def total_errors(self) -> int:
        return len(self.issues)

    @property
    def ready_to_backtest(self) -> bool:
        return self.total_errors == 0

    @property
    def summary_text(self) -> str:
        if self.total_errors == 0:
            return "Ready to backtest"
        return f"Validation completed with {self.total_errors} error(s)"


class ValidateStrategy:
    required_signal_columns = ["long_entry", "short_entry", "long_exit", "short_exit"]
    risk_price_columns = ["long_take_profit", "short_take_profit", "long_stop_loss", "short_stop_loss"]


    def __init__(self, strategy_filename: Optional[str] = None, strategy_path: Optional[Path | str] = None):
        self.strategy_path = Path(strategy_path) if strategy_path else None
        self.strategy_filename = strategy_filename or (self.strategy_path.name if self.strategy_path else "<memory>")


    def validate_file(self) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        if self.strategy_path is None:
            raise ValueError("strategy_path is required for validate_file()")

        code = self.strategy_path.read_text(encoding="utf-8")
        return self.validate_result(code)


    def validate_result(self, code: str) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        strategy, load_errors = self._run_load_validation(code)

        if load_errors:
            return None, ValidationResult(strategy_filename=self.strategy_filename, issues=load_errors)

        runtime_errors = self._run_runtime_validation(strategy, code)
        
        return strategy, ValidationResult(strategy_filename=self.strategy_filename, issues=runtime_errors)


    def validate(self, code: str) -> Tuple[Optional[CoreStrategy], List[str]]:
        strategy, result = self.validate_result(code)
        
        messages = [
            f"[{issue.category}] {issue.file}" + (f":{issue.line}" if issue.line is not None else "") + f"\n{issue.message}"
            for issue in result.issues
        ]
        
        return strategy, messages


    def sample_data(self, rows: int = 200) -> pd.DataFrame:
        dates = pd.date_range(start="2020-01-01", periods=rows, freq="D")
        rng = np.random.default_rng(seed=42)

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


    def _run_load_validation(self, code: str) -> Tuple[Optional[CoreStrategy], List[ValidationIssue]]:
        try:
            if self.strategy_path is None:
                scope = self._execute_inline_code(code)
            else:
                scope = self._execute_file_module(code)

        except SyntaxError as error:
            message, line = self._format_syntax_error(error, code)
            file = error.filename or self.strategy_filename
            issue = ValidationIssue("syntax", file, line, message)
            return None, [issue]

        except Exception as error:
            message, line, file_name = self._format_exception_detail(error, code)
            issue = ValidationIssue("template", file_name, line, message)
            return None, [issue]

        strategy_class, class_error = self._resolve_strategy_class(scope)
        if class_error is not None:
            return None, [class_error]

        strategy, init_error = self._instantiate_strategy(strategy_class, code)
        if init_error is not None:
            return None, [init_error]

        return strategy, []


    def _run_runtime_validation(self, strategy: CoreStrategy, code: str) -> List[ValidationIssue]:
        signal_data, signal_error = self._run_signal_pipeline(strategy, code)
        if signal_error is not None:
            return [signal_error]

        issues = self._validate_required_columns(signal_data)

        size_error = self._validate_position_size(strategy, code)
        if size_error is not None:
            issues.append(size_error)

        return issues


    def _execute_inline_code(self, code: str) -> Dict[str, object]:
        scope = {"__builtins__": __builtins__}
        compiled = compile(code, self.strategy_filename, "exec")
        exec(compiled, scope, scope)

        return scope
    

    def _execute_file_module(self, code: str) -> Dict[str, object]:
        package_name = f"_zstar_user_strategy_pkg_{uuid.uuid4().hex}"
        module_name = f"{package_name}.{self.strategy_path.stem}"

        package_module = types.ModuleType(package_name)
        package_module.__path__ = [str(self.strategy_path.parent)]
        package_module.__package__ = package_name

        module = types.ModuleType(module_name)
        module.__file__ = str(self.strategy_path)
        module.__package__ = package_name

        scope = module.__dict__
        scope.update({"__builtins__": __builtins__})

        sys.modules[package_name] = package_module
        sys.modules[module_name] = module

        try:
            compiled = compile(code, str(self.strategy_path), "exec")
            exec(compiled, scope, scope)
        finally:
            sys.modules.pop(module_name, None)
            sys.modules.pop(package_name, None)
        
        return scope
    

    def _resolve_strategy_class(self, scope: Dict[str, object]) -> Tuple[Optional[type[CoreStrategy]], Optional[ValidationIssue]]:
        strategy_classes = self._collect_strategy_classes(scope)

        if len(strategy_classes) == 1:
            return strategy_classes[0], None

        if len(strategy_classes) == 0:
            message = (
                "No CoreStrategy subclass found in the strategy code. "
                "Define a class that inherits from CoreStrategy."
            )
        else:
            class_names = ", ".join(sorted(cls.__name__ for cls in strategy_classes))
            message = (
                "Multiple CoreStrategy subclasses found. Keep exactly one. "
                f"Found: {class_names}. "
                "Keep only one CoreStrategy subclass in the strategy code."
            )

        issue = ValidationIssue("template", self.strategy_filename, None, message)
        return None, issue


    def _instantiate_strategy(
        self,
        strategy_class: type[CoreStrategy],
        code: str,
    ) -> Tuple[Optional[CoreStrategy], Optional[ValidationIssue]]:
        try:
            return strategy_class(), None
        except Exception as error:
            message, line, file_name = self._format_exception_detail(error, code)
            issue = ValidationIssue("template", file_name, line, message)
            return None, issue

    def _run_signal_pipeline(self, strategy: CoreStrategy, code: str) -> Tuple[Optional[pd.DataFrame], Optional[ValidationIssue]]:
        data = self.sample_data()

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
            message, line, file_name = self._format_exception_detail(error, code)
            issue = ValidationIssue("logic", file_name, line, message)
            return None, issue


    def _validate_required_columns(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for column_name in self.required_signal_columns:
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

        for column_name in self.risk_price_columns:
            if column_name in data.columns and not pd.api.types.is_numeric_dtype(data[column_name]):
                message = f"Risk price column '{column_name}' must contain numeric values."
                issues.append(ValidationIssue("type", self.strategy_filename, None, message))

        return issues


    def _validate_position_size(self, strategy: CoreStrategy, code: str) -> Optional[ValidationIssue]:
        try:
            size = strategy.position_size(10000, 100)
        except Exception as error:
            message, line, file_name = self._format_exception_detail(error, code)
            return ValidationIssue("logic", file_name, line, message)

        is_numeric = isinstance(size, (int, float, np.integer, np.floating))
        if not is_numeric or not np.isfinite(float(size)) or float(size) <= 0:
            message = "position_size(balance, entry_price) must return a finite positive numeric value."
            return ValidationIssue("type", self.strategy_filename, None, message)

        return None


    def _collect_strategy_classes(self, scope: Dict[str, object]) -> List[type[CoreStrategy]]:
        classes = {}
        
        for value in scope.values():
            if inspect.isclass(value) and issubclass(value, CoreStrategy) and value is not CoreStrategy:
                classes[id(value)] = value
        
        return list(classes.values())
    

    def _is_signal_dtype_valid(self, data: pd.Series) -> bool:
        return pd.api.types.is_bool_dtype(data) or pd.api.types.is_numeric_dtype(data)


    def _contains_only_binary_signals(self, data: pd.Series) -> bool:
        normalized = data.dropna()
        if normalized.empty:
            return True

        return normalized.isin([0, 1, False, True]).all()


    def _format_syntax_error(self, error: SyntaxError, code: str) -> Tuple[str, Optional[int]]:
        line = error.lineno if isinstance(error.lineno, int) else None
        column = error.offset if isinstance(error.offset, int) else None
        file_name = error.filename or self.strategy_filename

        lines = [
            "Strategy failed to load (SyntaxError)",
            f"File        : {file_name}",
            f"Line        : {line if line is not None else 'N/A'}",
            f"Column      : {column if column is not None else 'N/A'}",
            f"Error       : {error.msg}",
        ]

        context = self._code_context(code, line, column)
        if context:
            lines.extend(["", context])

        return "\n".join(lines), line


    def _format_exception_detail(self, error: Exception, code: Optional[str]) -> Tuple[str, Optional[int], str]:
        extracted = traceback.extract_tb(error.__traceback__)
        frame = self._select_relevant_frame(extracted)

        file_name = frame.filename if frame else self.strategy_filename
        line = frame.lineno if frame else None
        where = frame.name if frame else "N/A"
        error_text = str(error) if str(error) else repr(error)

        lines = [
            f"Strategy execution failed ({type(error).__name__})",
            f"File        : {file_name}",
            f"Line        : {line if line is not None else 'N/A'}",
            f"Where       : {where}",
            f"Error       : {error_text}",
        ]

        context = self._resolve_code_context(file_name, line, code)
        if context:
            lines.extend(["", context])

        if error.args:
            lines.append("")
            lines.append("Exception args:")
            for idx, arg in enumerate(error.args, 1):
                lines.append(f"  [{idx}] {repr(arg)}")

        return "\n".join(lines), line, file_name


    def _select_relevant_frame(self, frames: List[FrameSummary]) -> Optional[FrameSummary]:
        if not frames:
            return None

        if self.strategy_path is not None:
            root = self.strategy_path.parent.resolve()
            for frame in reversed(frames):
                try:
                    Path(frame.filename).resolve().relative_to(root)
                    return frame
                except ValueError:
                    continue

        for frame in reversed(frames):
            if frame.filename == self.strategy_filename:
                return frame

        return frames[-1]


    def _resolve_code_context(self, file_name: str, line: Optional[int], code: Optional[str]) -> str:
        if line is None:
            return ""

        if code is not None and file_name == self.strategy_filename:
            return self._code_context(code, line)

        path = Path(file_name)
        if not path.is_file():
            return ""

        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return ""

        return self._code_context(source, line)


    def _code_context(self, source: str, line: Optional[int], column: Optional[int] = None, radius: int = 2) -> str:
        if line is None:
            return ""

        rows = source.splitlines()
        if not rows:
            return ""

        start = max(1, line - radius)
        end = min(len(rows), line + radius)
        lines = ["Code context:"]

        for idx in range(start, end + 1):
            marker = ">>" if idx == line else "  "
            lines.append(f"{marker} {idx:>4} | {rows[idx - 1]}")
            if idx == line and column is not None and column > 0:
                lines.append(f"      | {' ' * (column + 1)}^")

        return "\n".join(lines)
