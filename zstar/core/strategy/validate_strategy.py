from __future__ import annotations

import inspect
import traceback
import types
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd

from zstar.core.strategy.core_strategy import CoreStrategy


class Severity(Enum):
    ERROR = "error"


class Category(Enum):
    SYNTAX = "syntax"
    TEMPLATE = "template"
    TYPE = "type"
    LOGIC = "logic"


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
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
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def ready_to_backtest(self) -> bool:
        return self.total_errors == 0

    @property
    def summary_text(self) -> str:
        if self.total_errors == 0:
            return "Ready to backtest"

        parts: List[str] = []
        if self.total_errors:
            parts.append(f"{self.total_errors} error(s)")

        return "Validation completed with " + " and ".join(parts)


class ValidateStrategy:
    scope_globals = {
        "__builtins__": __builtins__,
        "CoreStrategy": CoreStrategy,
    }

    required_signal_columns = ["long_entry", "short_entry", "long_exit", "short_exit"]


    def __init__(self, strategy_filename: Optional[str] = None, strategy_path: Optional[Path | str] = None):
        self.strategy_filename = strategy_filename
        self.strategy_path = Path(strategy_path) if strategy_path else None

        if self.strategy_filename is None:
            self.strategy_filename = self.strategy_path.name


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


    def _code_context(self, source: str, lineno: Optional[int], offset: Optional[int] = None, radius: int = 2) -> str:
        rows = source.splitlines()
        if lineno is None or not rows:
            return ""

        start = max(1, lineno - radius)
        end = min(len(rows), lineno + radius)
        lines = ["Code context:"]

        for idx in range(start, end + 1):
            marker = ">>" if idx == lineno else "  "
            lines.append(f"{marker} {idx:>4} | {rows[idx - 1]}")
            if idx == lineno and offset is not None and offset > 0:
                lines.append(f"      | {' ' * (offset + 1)}^")

        return "\n".join(lines)


    def _read_file_context(self, file_name: str, lineno: Optional[int], offset: Optional[int] = None) -> str:
        file_path = Path(file_name)
        if lineno is None or not file_path.is_file():
            return ""

        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError:
            return ""

        return self._code_context(source, lineno, offset)


    def _format_syntax_error(self, error: SyntaxError, code: str) -> Tuple[str, Optional[int]]:
        lineno = error.lineno if isinstance(error.lineno, int) else None
        offset = error.offset if isinstance(error.offset, int) else None
        file_name = error.filename or self.strategy_filename

        lines = [
            "Strategy failed to load (SyntaxError)",
            f"File        : {file_name}",
            f"Line        : {lineno if lineno is not None else 'N/A'}",
            f"Column      : {offset if offset is not None else 'N/A'}",
            f"Error       : {error.msg}",
        ]

        context = self._code_context(code, lineno, offset)
        if context:
            lines.append("")
            lines.append(context)

        return "\n".join(lines), lineno


    def _format_exception_detail(
        self,
        error: Exception,
        strategy_root: Optional[Path] = None,
        code: Optional[str] = None,
    ) -> Tuple[str, Optional[int], str]:
        frame = self._find_frame(error.__traceback__, strategy_root)
        
        file_name = frame.filename if frame else self.strategy_filename
        lineno = frame.lineno if frame else None
        where = frame.name if frame else "N/A"
        
        lines = [
            f"Strategy execution failed ({type(error).__name__})",
            f"File        : {file_name}",
            f"Line        : {lineno or 'N/A'}",
            f"Where       : {where}",
            f"Error       : {str(error) or repr(error)}",
        ]
        
        if code and file_name == self.strategy_filename:
            context = self._code_context(code, lineno)
        else:
            context = self._read_file_context(file_name, lineno)
        
        if context:
            lines.extend(["", context])
        
        if error.args:
            lines.append("")
            lines.append("Exception args:")
            lines.extend(f"  [{i}] {repr(arg)}" for i, arg in enumerate(error.args, 1))
        
        return "\n".join(lines), lineno, file_name


    def _find_frame(self, traceback_obj, strategy_root: Optional[Path]):
        extracted = traceback.extract_tb(traceback_obj)
        
        if strategy_root:
            root = strategy_root.resolve()
            for candidate in reversed(extracted):
                try:
                    Path(candidate.filename).resolve().relative_to(root)
                    return candidate
                except ValueError:
                    continue
        
        return extracted[-1] if extracted else None


    def _collect_strategy_classes(self, scope: Dict[str, object]) -> List[type[CoreStrategy]]:
        classes: Dict[int, type[CoreStrategy]] = {}
        for value in scope.values():
            if inspect.isclass(value) and issubclass(value, CoreStrategy) and value is not CoreStrategy:
                classes[id(value)] = value

        return list(classes.values())


    def _execute_code(self, code: str, scope: Dict[str, object]) -> Dict[str, object]:
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
        scope.update(self.scope_globals)

        import sys

        sys.modules[package_name] = package_module
        sys.modules[module_name] = module

        return self._execute_code(code, scope=scope)


    def run_load_validation(self, code: str) -> Tuple[Optional[CoreStrategy], List[ValidationIssue]]:
        try:
            if self.strategy_path:
                scope = self._execute_file_module(code)
            else:
                scope = self._execute_code(code, self.scope_globals)

        except SyntaxError as error:
            detail, line = self._format_syntax_error(error, code)

            return None, [
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.SYNTAX.value,
                    file=self.strategy_filename,
                    line=line,
                    message=detail,
                )
            ]

        except Exception as error:
            detail, line, file_name = self._format_exception_detail(
                error,
                strategy_root=self.strategy_path.parent if self.strategy_path else None,
                code=code,
            )
            return None, [
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.TEMPLATE.value,
                    file=file_name,
                    line=line,
                    message=detail,
                )
            ]

        strategy_classes = self._collect_strategy_classes(scope)
        if len(strategy_classes) != 1:
            class_names = "\n- ".join(sorted(strategy_class.__name__ for strategy_class in strategy_classes))
            message = (
                "The strategy file must define exactly one CoreStrategy subclass."
                if len(strategy_classes) == 0 else
                f"Multiple CoreStrategy subclasses were found: {class_names}\n Keep exactly one."
            )
            return None, [
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.TEMPLATE.value,
                    file=self.strategy_filename,
                    message=message
                )
            ]

        strategy_class = strategy_classes[0]
        try:
            strategy = strategy_class()
        except Exception as error:
            detail, line, file_name = self._format_exception_detail(
                error,
                strategy_root=self.strategy_path.parent if self.strategy_path else None,
                code=code,
            )
            return None, [
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.TEMPLATE.value,
                    file=file_name,
                    line=line,
                    message=detail,
                )
            ]

        return strategy, []


    def _is_signal_dtype_valid(self, data: pd.Series) -> bool:
        return pd.api.types.is_bool_dtype(data) or pd.api.types.is_numeric_dtype(data)


    def run_runtime_validation(self, strategy: CoreStrategy) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        data = self.sample_data()

        try:
            data = strategy.calculate_indicators(data)
            data = strategy.long_entry_signals(data)
            data = strategy.short_entry_signals(data)
            data = strategy.long_exit_signals(data)
            data = strategy.short_exit_signals(data)
        except Exception as error:
            detail, line, file_name = self._format_exception_detail(
                error,
                strategy_root=self.strategy_path.parent if self.strategy_path else None,
            )
            return [
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.LOGIC.value,
                    file=file_name,
                    line=line,
                    message=detail,
                )
            ]

        for column_name in self.required_signal_columns:
            if column_name not in data.columns:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR.value,
                        category=Category.TEMPLATE.value,
                        file=self.strategy_filename,
                        message=f"Missing required signal column '{column_name}' from strategy methods.",
                    )
                )
                continue

            signal_data = data[column_name]
            if not self._is_signal_dtype_valid(signal_data):
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR.value,
                        category=Category.TYPE.value,
                        file=self.strategy_filename,
                        message=f"Use numeric or boolean values in '{column_name}' signal column.",
                    )
                )

        try:
            size = strategy.position_size(10000, 100)
            if not isinstance(size, (int, float, np.integer, np.floating)) or float(size) <= 0:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR.value,
                        category=Category.TYPE.value,
                        file=self.strategy_filename,
                        message="position_size(balance, entry_price) must return a positive numeric value.",
                    )
                )

        except Exception as error:
            detail, line, file_name = self._format_exception_detail(
                error,
                strategy_root=self.strategy_path.parent if self.strategy_path else None,
            )
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR.value,
                    category=Category.LOGIC.value,
                    file=file_name,
                    line=line,
                    message=detail,
                )
            )

        return issues


    def validate_result(self, code: str) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        strategy, load_issues = self.run_load_validation(code)

        if load_issues:
            return None, ValidationResult(strategy_filename=self.strategy_filename, issues=load_issues)

        runtime_issues = self.run_runtime_validation(strategy)
        return strategy, ValidationResult(strategy_filename=self.strategy_filename, issues=runtime_issues)


    def validate_file(self) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        path = self.strategy_path
        code = path.read_text(encoding="utf-8")

        return self.validate_result(code)
