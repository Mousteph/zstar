from fastapi import APIRouter

from zstar.api.utils import list_strategy_filenames
from .models import StrategiesListResponse

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("")
def list_strategy_files() -> StrategiesListResponse:
    return StrategiesListResponse(strategies=list_strategy_filenames())
