from pydantic import BaseModel, Field


class BacktestConfigModel(BaseModel):
    initial_balance: float = Field(default=10000.0, ge=0)
    entry_fee_pct: float = Field(default=0, ge=0, le=100)
    exit_fee_pct: float = Field(default=0, ge=0, le=100)
    slippage_pct: float = Field(default=0, ge=0, le=100)
    slippage_seed: int | None = Field(default=None)
