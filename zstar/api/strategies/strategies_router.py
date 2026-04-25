from fastapi import APIRouter

from zstar.api.utils import list_strategy_filenames
from zstar.logger import get_logger
from .models import StrategiesListResponse

router = APIRouter(prefix="/api/strategies", tags=["strategies"])
logger = get_logger(__name__)


@router.get("")
def list_strategy_files() -> StrategiesListResponse:
    strategy_files = list_strategy_filenames()
    logger.info("Listed strategies count=%s", len(strategy_files))
    return StrategiesListResponse(strategies=strategy_files)
