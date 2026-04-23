import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from zstar.core.trade_order import Trade
from zstar.core.backtest import BacktestReport, BacktesterEngine
from zstar.core.data_loader import YahooData
from zstar.core.strategy import load_strategy_from_file
from zstar.core.exceptions import BacktestServiceError
from zstar.api.utils import resolve_strategy_file

from .models import (
    BacktestMetaResponse,
    BacktestRunRequest,
    BacktestRunResponse,
    EquityPointResponse,
    MarketOhlcvPointResponse,
    TradeResponse,
)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
responses = {
    400: {"description": "Error during backtest execution"},
    500: {"description": "Internal server error during backtest execution"},
}


def _safe_number(value: Any) -> Optional[float | str]:
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


def _timestamp_to_iso(value: pd.Timestamp | datetime) -> str:
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            value = value.tz_localize("UTC")
        else:
            value = value.tz_convert("UTC")
        return value.isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def _serialize_trades(trades: List[Trade], symbol: str) -> List[TradeResponse]:
    return [
        TradeResponse(
            id=trade.id,
            symbol=symbol,
            side=trade.side.value,
            size=float(trade.size),
            entry_price=float(trade.entry_price),
            exit_price=float(trade.exit_price),
            entry_datetime=_timestamp_to_iso(trade.entry_datetime),
            exit_datetime=_timestamp_to_iso(trade.exit_datetime),
            raw_pnl=float(trade.raw_pnl),
            total_fees=float(trade.total_fees),
            net_pnl=float(trade.net_pnl),
        )
        for trade in trades
    ]


def _serialize_equity_curve(report: BacktestReport) -> List[EquityPointResponse]:
    curve = report.equity_curve()
    rows: List[EquityPointResponse] = []

    for row in curve.itertuples():
        rows.append(
            EquityPointResponse(
                datetime=_timestamp_to_iso(row.Index),
                strategy=_safe_number(row.strategy),  # type: ignore[arg-type]
                buy_and_hold=_safe_number(row.buy_and_hold),  # type: ignore[arg-type]
            )
        )

    return rows


def _serialize_kpis(report: BacktestReport) -> Dict[str, Optional[float | str]]:
    kpis: Dict[str, Optional[float | str]] = {}
    for key, value in report.kpis().items():
        kpis[key] = _safe_number(value)

    return kpis


def _serialize_market_ohlcv(report: BacktestReport) -> List[MarketOhlcvPointResponse]:
    rows: List[MarketOhlcvPointResponse] = []

    for row in report.data.itertuples():
        timestamp = row.Index
        rows.append(
            MarketOhlcvPointResponse(
                datetime=_timestamp_to_iso(timestamp),
                open=_safe_number(getattr(row, "open", None)),
                high=_safe_number(getattr(row, "high", None)),
                low=_safe_number(getattr(row, "low", None)),
                close=_safe_number(getattr(row, "close", None)),
                volume=_safe_number(getattr(row, "volume", None)),
            )
        )

    return rows


@router.post("/run", responses=responses)
def run_backtest(request: BacktestRunRequest) -> BacktestRunResponse:
    try:
        strategy_path = resolve_strategy_file(request.strategy_filename)
        strategy = load_strategy_from_file(strategy_path)
        data_handler = YahooData(request.data)
        backtest_engine = BacktesterEngine(strategy, data_handler, request.backtest_config)
        report = backtest_engine.run_backtest()
        data = data_handler.get_data()

    except BacktestServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"{exc.error_code}:\n- {str(exc)}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"INTERNAL_SERVER_ERROR: {str(exc)}") from exc

    return BacktestRunResponse(
        equity_curve=_serialize_equity_curve(report),
        market_ohlcv=_serialize_market_ohlcv(report),
        trades=_serialize_trades(report.trades, symbol=request.data.symbol),
        kpis=_serialize_kpis(report),
        meta=BacktestMetaResponse(
            symbol=request.data.symbol,
            start_date=request.data.start_date,
            end_date=request.data.end_date,
            interval=request.data.interval,
            bars_count=len(data),
        ),
    )
