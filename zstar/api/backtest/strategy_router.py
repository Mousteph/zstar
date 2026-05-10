from fastapi import APIRouter, HTTPException

from zstar.api.utils import list_strategy_filenames
from zstar.core.exceptions import BacktestServiceError
from zstar.logger import get_logger

from .services import resolve_strategy_validation
from .models import (
    StrategiesListResponse,
    ValidateStrategiesRequest,
    ValidateStrategiesResponse,
)

router = APIRouter(prefix="/api", tags=["strategies"])
logger = get_logger(__name__)


@router.get("/strategies")
def list_strategy_files() -> StrategiesListResponse:
    strategy_files = list_strategy_filenames()
    logger.info("Listed strategies count=%s", len(strategy_files))
    return StrategiesListResponse(strategies=strategy_files)


@router.post("/validate-strategies")
def validate_strategy_file(request: ValidateStrategiesRequest) -> ValidateStrategiesResponse:
    try:
        payload = resolve_strategy_validation(request.strategy_filename)
    except BacktestServiceError as exc:
        logger.info("Strategy validation request rejected error=%s", exc.error_code)
        raise HTTPException(status_code=exc.status_code, detail=f"{exc.error_code}:\n- {str(exc)}") from exc

    logger.info(
        "Strategy validated file=%s errors=%s ready=%s",
        payload.validation.strategy_filename,
        payload.validation.total_errors,
        payload.validation.ready_to_backtest,
    )

    return payload.validation
