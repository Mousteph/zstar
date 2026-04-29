from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from zstar.api.utils import resolve_strategy_file
from zstar.core.backtest import BacktestReport
from zstar.core.strategy import CoreStrategy, ValidateStrategy
from zstar.core.trade_order import Trade

from .models import (
    BacktestMetaResponse,
    EquityPointResponse,
    MarketOhlcvPointResponse,
    TradeResponse,
    ValidateStrategiesResponse,
    ValidationIssueResponse
)


@dataclass(frozen=True)
class StrategyValidationPayload:
    strategy: Optional[CoreStrategy]
    validation: ValidateStrategiesResponse


def resolve_strategy_validation(strategy_filename: Optional[str]) -> StrategyValidationPayload:
    strategy_path = resolve_strategy_file(strategy_filename)
    validator = ValidateStrategy(strategy_path=strategy_path)
    strategy, validation_result = validator.validate_file()

    validation = ValidateStrategiesResponse(
        strategy_filename=validation_result.strategy_filename,
        ready_to_backtest=validation_result.ready_to_backtest,
        total_errors=validation_result.total_errors,
        summary_text=validation_result.summary_text,
        issues=[
            ValidationIssueResponse(
                category=issue.category,
                file=issue.file,
                line=issue.line,
                message=issue.message,
            )
            for issue in validation_result.issues
        ],
    )

    return StrategyValidationPayload(strategy=strategy, validation=validation)


def serialize_trades(trades: List[Trade], symbol: str) -> List[TradeResponse]:
    return [
        TradeResponse(
            id=trade.id,
            symbol=symbol,
            side=trade.side.value,
            size=float(trade.size),
            entry_price=float(trade.entry_price),
            exit_price=float(trade.exit_price),
            entry_datetime=timestamp_to_iso(trade.entry_datetime),
            exit_datetime=timestamp_to_iso(trade.exit_datetime),
            raw_pnl=float(trade.raw_pnl),
            total_fees=float(trade.total_fees),
            net_pnl=float(trade.net_pnl),
        )
        for trade in trades
    ]


def serialize_equity_curve(report: BacktestReport) -> List[EquityPointResponse]:
    rows: List[EquityPointResponse] = []
    for row in report.equity_curve().itertuples():
        rows.append(
            EquityPointResponse(
                datetime=timestamp_to_iso(row.Index),
                strategy=safe_number(row.strategy),  # type: ignore[arg-type]
                buy_and_hold=safe_number(row.buy_and_hold),  # type: ignore[arg-type]
            )
        )

    return rows


def serialize_kpis(report: BacktestReport) -> Dict[str, Optional[float | str]]:
    return {key: safe_number(value) for key, value in report.kpis().items()}


def serialize_market_ohlcv(report: BacktestReport) -> List[MarketOhlcvPointResponse]:
    rows: List[MarketOhlcvPointResponse] = []
    for row in report.data.itertuples():
        rows.append(
            MarketOhlcvPointResponse(
                datetime=timestamp_to_iso(row.Index),
                open=safe_number(getattr(row, "open", None)),
                high=safe_number(getattr(row, "high", None)),
                low=safe_number(getattr(row, "low", None)),
                close=safe_number(getattr(row, "close", None)),
                volume=safe_number(getattr(row, "volume", None)),
            )
        )

    return rows


def build_backtest_meta(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str,
    bars_count: int,
) -> BacktestMetaResponse:
    return BacktestMetaResponse(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        bars_count=bars_count,
    )


def safe_number(value: Any) -> Optional[float | str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            return None
        return numeric
    if isinstance(value, (np.integer, int)):
        return float(value)
    return str(value)


def timestamp_to_iso(value: pd.Timestamp | datetime) -> str:
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            return value.tz_localize("UTC").isoformat()
        return value.tz_convert("UTC").isoformat()

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()

    return value.astimezone(timezone.utc).isoformat()
