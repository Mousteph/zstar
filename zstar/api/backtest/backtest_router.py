from fastapi import APIRouter, HTTPException

from zstar.core.backtest import BacktestReport, BacktesterEngine
from zstar.core.data_loader import YahooData
from zstar.core.exceptions import BacktestServiceError, StrategyValidationError
from zstar.logger import get_logger

from .models import BacktestRunEnvelopeResponse, BacktestRunRequest, BacktestRunResponse
from .services import (
    build_backtest_meta,
    resolve_strategy_validation,
    serialize_equity_curve,
    serialize_kpis,
    serialize_market_ohlcv,
    serialize_trades,
)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
logger = get_logger(__name__)
responses = {
    400: {"description": "Error during backtest execution"},
    500: {"description": "Internal server error during backtest execution"},
}


@router.post("/run", responses=responses)
def run_backtest(request: BacktestRunRequest) -> BacktestRunEnvelopeResponse:
    logger.info(
        "Backtest requested symbol=%s interval=%s start_date=%s end_date=%s",
        request.data.symbol,
        request.data.interval,
        request.data.start_date,
        request.data.end_date,
    )

    try:
        validation_payload = resolve_strategy_validation(request.strategy_filename)
        if not validation_payload.validation.ready_to_backtest:
            return BacktestRunEnvelopeResponse(
                strategy_validation=validation_payload.validation,
                backtest_result=None,
            )

        if validation_payload.strategy is None:
            raise StrategyValidationError("Strategy could not be instantiated after validation.")

        data_handler = YahooData(request.data)
        backtest_engine = BacktesterEngine(
            validation_payload.strategy,
            data_handler,
            request.backtest_config,
        )
        report: BacktestReport = backtest_engine.run_backtest()
        data = data_handler.get_data()
        logger.info(
            "Backtest completed symbol=%s bars_count=%s trades_count=%s",
            request.data.symbol,
            len(data),
            len(report.trades),
        )

    except BacktestServiceError as exc:
        logger.warning("Backtest validation failed error=%s", exc.error_code)
        raise HTTPException(status_code=exc.status_code, detail=f"{exc.error_code}:\n- {str(exc)}") from exc
    except Exception as exc:
        logger.exception("Backtest failed with internal error")
        raise HTTPException(status_code=500, detail=f"INTERNAL_SERVER_ERROR: {str(exc)}") from exc

    return BacktestRunEnvelopeResponse(
        strategy_validation=None,
        backtest_result=BacktestRunResponse(
            equity_curve=serialize_equity_curve(report),
            market_ohlcv=serialize_market_ohlcv(report),
            trades=serialize_trades(report.trades, symbol=request.data.symbol),
            kpis=serialize_kpis(report),
            meta=build_backtest_meta(
                symbol=request.data.symbol,
                start_date=request.data.start_date,
                end_date=request.data.end_date,
                interval=request.data.interval,
                bars_count=len(data),
            ),
        ),
    )
