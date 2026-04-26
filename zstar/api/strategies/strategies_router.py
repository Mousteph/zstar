from fastapi import APIRouter, HTTPException

from zstar.api.utils import list_strategy_filenames, resolve_strategy_file
from zstar.core.strategy import ValidateStrategy
from zstar.core.exceptions import BacktestServiceError
from zstar.logger import get_logger

from .models import (
    StrategiesListResponse,
    ValidateStrategiesRequest,
    ValidateStrategiesResponse,
    ValidationIssueResponse,
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
        strategy_path = resolve_strategy_file(request.strategy_filename)
        validator = ValidateStrategy(strategy_path=strategy_path)
        _, validation_result = validator.validate_file()
    except BacktestServiceError as exc:
        logger.info("Strategy validation request rejected error=%s", exc.error_code)
        raise HTTPException(status_code=exc.status_code, detail=f"{exc.error_code}:\n- {str(exc)}") from exc

    logger.info(
        "Strategy validated file=%s errors=%s ready=%s",
        validation_result.strategy_filename,
        validation_result.total_errors,
        validation_result.ready_to_backtest,
    )

    return ValidateStrategiesResponse(
        strategy_filename=validation_result.strategy_filename,
        ready_to_backtest=validation_result.ready_to_backtest,
        total_errors=validation_result.total_errors,
        summary_text=validation_result.summary_text,
        issues=[
            ValidationIssueResponse(
                severity=issue.severity,
                category=issue.category,
                file=issue.file,
                line=issue.line,
                message=issue.message,
            )
            for issue in validation_result.issues
        ],
    )
