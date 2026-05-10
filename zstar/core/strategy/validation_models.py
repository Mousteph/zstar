from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


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
