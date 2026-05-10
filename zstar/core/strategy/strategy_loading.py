from __future__ import annotations

import inspect
import sys
import types
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from zstar.core.strategy.core_strategy import CoreStrategy
from zstar.core.strategy.strategy_error_formatter import StrategyValidationErrorFormatter
from zstar.core.strategy.validation_models import ValidationIssue


class StrategyLoader:
    def __init__(self, strategy_filename: str, strategy_path: Optional[Path] = None):
        self.strategy_filename = strategy_filename
        self.strategy_path = strategy_path
        self._formatter = StrategyValidationErrorFormatter(strategy_filename, strategy_path)

    def load(self, code: str) -> Tuple[Optional[CoreStrategy], List[ValidationIssue]]:
        try:
            if self.strategy_path is None:
                scope = self._execute_inline_code(code)
            else:
                scope = self._execute_file_module(code)
        except SyntaxError as error:
            message, line = self._formatter.format_syntax_error(error, code)
            file = error.filename or self.strategy_filename
            issue = ValidationIssue("syntax", file, line, message)
            return None, [issue]
        except Exception as error:
            message, line, file_name = self._formatter.format_exception_detail(error, code)
            issue = ValidationIssue("template", file_name, line, message)
            return None, [issue]

        strategy_class, class_error = self._resolve_strategy_class(scope)
        if class_error is not None:
            return None, [class_error]

        strategy, init_error = self._instantiate_strategy(strategy_class, code)
        if init_error is not None:
            return None, [init_error]

        return strategy, []

    def _execute_inline_code(self, code: str) -> Dict[str, object]:
        scope = {"__builtins__": __builtins__}
        compiled = compile(code, self.strategy_filename, "exec")
        exec(compiled, scope, scope)
        return scope

    def _execute_file_module(self, code: str) -> Dict[str, object]:
        if self.strategy_path is None:
            raise ValueError("strategy_path is required for file-based strategy loading")

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
            message, line, file_name = self._formatter.format_exception_detail(error, code)
            issue = ValidationIssue("template", file_name, line, message)
            return None, issue

    def _collect_strategy_classes(self, scope: Dict[str, object]) -> List[type[CoreStrategy]]:
        classes = {}

        for value in scope.values():
            if inspect.isclass(value) and issubclass(value, CoreStrategy) and value is not CoreStrategy:
                classes[id(value)] = value

        return list(classes.values())
