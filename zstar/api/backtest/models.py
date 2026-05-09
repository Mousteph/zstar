from __future__ import annotations

from typing import Dict, List, Optional, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from zstar.core.backtest import BacktestConfigModel


class BaseDataLoaderConfigModel(BaseModel):
    source: Literal["yahoo", "csv"]


class CsvDataLoaderConfigModel(BaseDataLoaderConfigModel):
    source: Literal["csv"]
    filename: str = Field(min_length=1)


class YahooDataLoaderConfigModel(BaseDataLoaderConfigModel):
    source: Literal["yahoo"] = "yahoo"
    symbol: str = Field(min_length=1, max_length=20)
    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)
    interval: str = Field(default="1d")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol cannot be empty")
        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "YahooDataLoaderConfigModel":
        if self.end_date is not None and self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class BacktestRunRequest(BaseModel):
    data: Union[YahooDataLoaderConfigModel, CsvDataLoaderConfigModel]
    backtest_config: BacktestConfigModel
    strategy_filename: Optional[str] = None


class CsvFilesListResponse(BaseModel):
    files: list[str]


class CsvFileUploadResponse(BaseModel):
    filename: str
    files: list[str]


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
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    exit_reason: str = "signal"
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


class BacktestRunEnvelopeResponse(BaseModel):
    strategy_validation: Optional[ValidateStrategiesResponse] = None
    backtest_result: Optional[BacktestRunResponse] = None


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
