from pydantic import BaseModel
from zstar.core.backtest import BacktestConfigModel
from zstar.core.data_loader import DataLoaderConfigModel

class BacktestCliConfig(BaseModel):
    kpis_output: str = "outputs/kpis.json"
    equity_curve_output: str = "outputs/equity_curve.html"
    data: DataLoaderConfigModel
    backtest_config: BacktestConfigModel
