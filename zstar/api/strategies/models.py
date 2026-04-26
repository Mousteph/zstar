from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class StrategiesListResponse(BaseModel):
    strategies: list[str]


class ValidateStrategiesRequest(BaseModel):
    strategy_filename: Optional[str] = None


class ValidationIssueResponse(BaseModel):
    category: Literal["syntax", "template", "type", "logic"]
    file: str
    line: Optional[int] = None
    message: str


class ValidateStrategiesResponse(BaseModel):
    strategy_filename: str
    ready_to_backtest: bool
    total_errors: int
    issues: list[ValidationIssueResponse]
    summary_text: str
