from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from zstar.core.strategy.core_strategy import CoreStrategy
from zstar.core.strategy.strategy_loading import StrategyLoader
from zstar.core.strategy.strategy_rules import StrategyRules
from zstar.core.strategy.validation_models import ValidationResult


class ValidateStrategy:
    def __init__(self, strategy_filename: Optional[str] = None, strategy_path: Optional[Path | str] = None):
        self.strategy_path = Path(strategy_path) if strategy_path else None
        self.strategy_filename = strategy_filename or (self.strategy_path.name if self.strategy_path else "<memory>")
        self._loader = StrategyLoader(self.strategy_filename, self.strategy_path)
        self._rules = StrategyRules(self.strategy_filename, self.strategy_path)

    def validate_file(self) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        if self.strategy_path is None:
            raise ValueError("strategy_path is required for validate_file()")

        code = self.strategy_path.read_text(encoding="utf-8")
        return self.validate_result(code)

    def validate_result(self, code: str) -> Tuple[Optional[CoreStrategy], ValidationResult]:
        strategy, load_errors = self._loader.load(code)

        if load_errors:
            return None, ValidationResult(strategy_filename=self.strategy_filename, issues=load_errors)

        runtime_errors = self._rules.validate(strategy, code)

        return strategy, ValidationResult(strategy_filename=self.strategy_filename, issues=runtime_errors)
