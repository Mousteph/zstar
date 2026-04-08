import pandas as pd
import pytest
from pydantic import ValidationError

from zstar.core.core_strategy import CoreStrategy
from zstar.core.data_loader.data_handler import DataHandler
from zstar.core.backtest.backtester_engine import BacktesterEngine
from zstar.core.backtest.backtest_config_model import BacktestConfigModel
from zstar.core.enums import TradeSide


def _price_frame(open_prices, close_prices):
    index = pd.date_range('2026-01-01', periods=len(open_prices), freq='D')
    return pd.DataFrame({'open': open_prices, 'close': close_prices}, index=index)


class FixedSignalStrategy(CoreStrategy):
    def __init__(self, *, size: float, long_entry_rows=(), long_exit_rows=(), short_entry_rows=(), short_exit_rows=()):
        super().__init__()
        self._size = size
        self._long_entry_rows = tuple(long_entry_rows)
        self._long_exit_rows = tuple(long_exit_rows)
        self._short_entry_rows = tuple(short_entry_rows)
        self._short_exit_rows = tuple(short_exit_rows)

    def _apply_signal(self, data: pd.DataFrame, column: str, rows):
        data[column] = 0
        for row in rows:
            data.at[data.index[row], column] = 1
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'long_entry', self._long_entry_rows)

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'short_entry', self._short_entry_rows)

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'long_exit', self._long_exit_rows)

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'short_exit', self._short_exit_rows)

    def position_size(self, balance: float, entry_price: float) -> float:
        return self._size


class DummyStrategy(CoreStrategy):
    def position_size(self, balance: float, entry_price: float) -> float:
        return 1.0


def _backtest_report(strategy: CoreStrategy, data: pd.DataFrame, config: dict, interval: str = '1d'):
    engine = BacktesterEngine(
        strategy,
        DataHandler(data, interval=interval),
        BacktestConfigModel.model_validate(config),
    )
    return engine.run_backtest()


def test_long_trade_records_entry_and_exit_prices_and_balance():
    data = _price_frame(open_prices=[100.0, 110.0, 120.0], close_prices=[101.0, 111.0, 121.0])
    strategy = FixedSignalStrategy(size=5.0, long_entry_rows=[0], long_exit_rows=[1])
    report = _backtest_report(
        strategy=strategy,
        data=data,
        config={
            'initial_balance': 1000.0,
            'entry_fee_pct': 0.0,
            'exit_fee_pct': 0.0,
            'slippage_pct': 0.0,
        },
    )

    assert report.initial_balance == pytest.approx(1000.0)
    assert report.final_balance == pytest.approx(1050.0)
    assert report.interval == '1d'
    assert len(report.trades) == 1

    trade = report.trades[0]
    assert trade.side == TradeSide.LONG
    assert trade.entry_price == data.iloc[1].open
    assert trade.exit_price == data.iloc[2].open
    assert trade.net_pnl == pytest.approx(50.0)


def test_short_trade_records_entry_and_exit_prices_and_balance():
    data = _price_frame(open_prices=[200.0, 180.0, 170.0], close_prices=[199.0, 179.0, 171.0])
    strategy = FixedSignalStrategy(size=4.0, short_entry_rows=[0], short_exit_rows=[1])
    report = _backtest_report(
        strategy=strategy,
        data=data,
        config={
            'initial_balance': 1000.0,
            'entry_fee_pct': 0.0,
            'exit_fee_pct': 0.0,
            'slippage_pct': 0.0,
        },
    )

    assert report.initial_balance == pytest.approx(1000.0)
    assert report.final_balance == pytest.approx(1040.0)
    assert len(report.trades) == 1

    trade = report.trades[0]
    assert trade.side == TradeSide.SHORT
    assert trade.entry_price == data.iloc[1].open
    assert trade.exit_price == data.iloc[2].open
    assert trade.net_pnl == pytest.approx(40.0)


def test_slippage_applies_adverse_adjustments_for_long_entry_and_exit():
    config = BacktestConfigModel(slippage_pct=5.0, slippage_seed=123)
    engine = BacktesterEngine(
        DummyStrategy(),
        DataHandler(pd.DataFrame({'open': [1.0], 'close': [1.0]})),
        config,
    )

    entry_price = engine._simulate_slippage(100.0, TradeSide.LONG, is_entry=True)
    exit_price = engine._simulate_slippage(100.0, TradeSide.LONG, is_entry=False)

    assert entry_price > 100.0
    assert exit_price < 100.0


def test_pct_to_rate_rejects_negative_values():
    with pytest.raises(ValidationError):
        BacktestConfigModel(entry_fee_pct=-1.0)


def test_engine_passes_data_interval_to_report():
    data = _price_frame(open_prices=[100.0, 102.0, 104.0], close_prices=[101.0, 103.0, 105.0])
    strategy = FixedSignalStrategy(size=1.0, long_entry_rows=[0], long_exit_rows=[1])
    report = _backtest_report(
        strategy=strategy,
        data=data,
        config={
            'initial_balance': 1000.0,
            'entry_fee_pct': 0.0,
            'exit_fee_pct': 0.0,
            'slippage_pct': 0.0,
        },
        interval='1h',
    )

    assert report.interval == '1h'
