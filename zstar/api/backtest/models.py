from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from zstar.core.backtest import BacktestConfigModel
from zstar.core.data_loader import DataLoaderConfigModel


class BacktestRunRequest(BaseModel):
    data: DataLoaderConfigModel
    backtest_config: BacktestConfigModel


class EquityPointResponse(BaseModel): 
    datetime: str
    strategy: Optional[float] = None
    buy_and_hold: Optional[float] = None


class TradeResponse(BaseModel):
    id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: float
    entry_datetime: str
    exit_datetime: str
    raw_pnl: float
    total_fees: float
    net_pnl: float


class MarketOhlcvPointResponse(BaseModel):
    datetime: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class BacktestMetaResponse(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    interval: str
    bars_count: int


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    equity_curve: List[EquityPointResponse]
    market_ohlcv: List[MarketOhlcvPointResponse]
    trades: List[TradeResponse]
    kpis: Dict[str, Optional[float | str]]
    meta: BacktestMetaResponse
