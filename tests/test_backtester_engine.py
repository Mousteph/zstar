import pandas as pd
import pytest
from pydantic import ValidationError

from zstar.core.strategy import CoreStrategy
from zstar.core.data_loader.data_handler import DataHandler
from zstar.core.backtest.backtester_engine import BacktesterEngine
from zstar.core.backtest.backtest_config_model import BacktestConfigModel
from zstar.core.enums import TradeSide


def _price_frame(open_prices, close_prices, high_prices=None, low_prices=None):
    index = pd.date_range('2026-01-01', periods=len(open_prices), freq='D')
    resolved_high_prices = high_prices if high_prices is not None else [max(open_price, close_price) for open_price, close_price in zip(open_prices, close_prices)]
    resolved_low_prices = low_prices if low_prices is not None else [min(open_price, close_price) for open_price, close_price in zip(open_prices, close_prices)]
    return pd.DataFrame(
        {'open': open_prices, 'high': resolved_high_prices, 'low': resolved_low_prices, 'close': close_prices},
        index=index,
    )


class FixedSignalStrategy(CoreStrategy):
    def __init__(
        self,
        *,
        size: float,
        long_entry_rows=(),
        long_exit_rows=(),
        short_entry_rows=(),
        short_exit_rows=(),
        long_take_profit_prices=None,
        short_take_profit_prices=None,
        long_stop_loss_prices=None,
        short_stop_loss_prices=None,
    ):
        super().__init__()
        self._size = size
        self._long_entry_rows = tuple(long_entry_rows)
        self._long_exit_rows = tuple(long_exit_rows)
        self._short_entry_rows = tuple(short_entry_rows)
        self._short_exit_rows = tuple(short_exit_rows)
        self._long_take_profit_prices = long_take_profit_prices or {}
        self._short_take_profit_prices = short_take_profit_prices or {}
        self._long_stop_loss_prices = long_stop_loss_prices or {}
        self._short_stop_loss_prices = short_stop_loss_prices or {}

    def _apply_signal(self, data: pd.DataFrame, column: str, rows):
        data[column] = 0
        for row in rows:
            data.at[data.index[row], column] = 1
        return data

    def _apply_prices(self, data: pd.DataFrame, column: str, prices):
        data[column] = float('nan')
        for row, price in prices.items():
            data.at[data.index[row], column] = price
        return data

    def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'long_entry', self._long_entry_rows)

    def short_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'short_entry', self._short_entry_rows)

    def long_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'long_exit', self._long_exit_rows)

    def short_exit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_signal(data, 'short_exit', self._short_exit_rows)

    def long_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_prices(data, 'long_take_profit', self._long_take_profit_prices)

    def short_take_profit_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_prices(data, 'short_take_profit', self._short_take_profit_prices)

    def long_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_prices(data, 'long_stop_loss', self._long_stop_loss_prices)

    def short_stop_loss_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._apply_prices(data, 'short_stop_loss', self._short_stop_loss_prices)

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


def test_nan_signal_values_do_not_trigger_entries():
    data = _price_frame(open_prices=[100.0, 110.0], close_prices=[101.0, 111.0])

    class NanSignalStrategy(FixedSignalStrategy):
        def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
            data["long_entry"] = float("nan")
            return data

    strategy = NanSignalStrategy(size=1.0)
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

    assert report.trades == []
    assert report.final_balance == pytest.approx(1000.0)


def test_non_one_numeric_signal_values_do_not_trigger_entries():
    data = _price_frame(open_prices=[100.0, 110.0], close_prices=[101.0, 111.0])

    class NonOneSignalStrategy(FixedSignalStrategy):
        def long_entry_signals(self, data: pd.DataFrame) -> pd.DataFrame:
            data["long_entry"] = 2
            return data

    strategy = NonOneSignalStrategy(size=1.0)
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

    assert report.trades == []
    assert report.final_balance == pytest.approx(1000.0)


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


def test_long_take_profit_closes_intrabar_at_take_profit_price():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 115.0, 101.0],
        low_prices=[99.0, 98.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, long_entry_rows=[0], long_take_profit_prices={0: 110.0})
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

    trade = report.trades[0]
    assert trade.exit_price == pytest.approx(110.0)
    assert trade.take_profit_price == pytest.approx(110.0)
    assert trade.stop_loss_price is None
    assert trade.exit_reason == 'take_profit'
    assert trade.net_pnl == pytest.approx(10.0)


def test_long_stop_loss_closes_intrabar_at_stop_loss_price():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 102.0, 101.0],
        low_prices=[99.0, 90.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, long_entry_rows=[0], long_stop_loss_prices={0: 95.0})
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

    trade = report.trades[0]
    assert trade.exit_price == pytest.approx(95.0)
    assert trade.stop_loss_price == pytest.approx(95.0)
    assert trade.exit_reason == 'stop_loss'
    assert trade.net_pnl == pytest.approx(-5.0)


def test_short_take_profit_closes_intrabar_at_take_profit_price():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 102.0, 101.0],
        low_prices=[99.0, 85.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, short_entry_rows=[0], short_take_profit_prices={0: 90.0})
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

    trade = report.trades[0]
    assert trade.exit_price == pytest.approx(90.0)
    assert trade.take_profit_price == pytest.approx(90.0)
    assert trade.exit_reason == 'take_profit'
    assert trade.net_pnl == pytest.approx(10.0)


def test_short_stop_loss_closes_intrabar_at_stop_loss_price():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 115.0, 101.0],
        low_prices=[99.0, 98.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, short_entry_rows=[0], short_stop_loss_prices={0: 110.0})
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

    trade = report.trades[0]
    assert trade.exit_price == pytest.approx(110.0)
    assert trade.stop_loss_price == pytest.approx(110.0)
    assert trade.exit_reason == 'stop_loss'
    assert trade.net_pnl == pytest.approx(-10.0)


def test_stop_loss_wins_when_stop_loss_and_take_profit_hit_same_candle():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 115.0, 101.0],
        low_prices=[99.0, 90.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(
        size=1.0,
        long_entry_rows=[0],
        long_take_profit_prices={0: 110.0},
        long_stop_loss_prices={0: 95.0},
    )
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

    trade = report.trades[0]
    assert trade.exit_price == pytest.approx(95.0)
    assert trade.exit_reason == 'stop_loss'
    assert trade.net_pnl == pytest.approx(-5.0)


def test_entry_is_cancelled_when_open_crosses_long_risk_prices():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 120.0, 105.0],
        low_prices=[99.0, 80.0, 99.0],
        close_prices=[100.0, 100.0, 105.0],
    )
    strategy = FixedSignalStrategy(
        size=1.0,
        long_entry_rows=[0],
        long_take_profit_prices={0: 90.0},
        long_stop_loss_prices={0: 110.0},
    )
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

    assert report.trades == []


def test_entry_is_cancelled_when_open_crosses_short_risk_prices():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 120.0, 105.0],
        low_prices=[99.0, 80.0, 99.0],
        close_prices=[100.0, 100.0, 105.0],
    )
    strategy = FixedSignalStrategy(
        size=1.0,
        short_entry_rows=[0],
        short_take_profit_prices={0: 110.0},
        short_stop_loss_prices={0: 90.0},
    )
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

    assert report.trades == []


def test_risk_prices_are_captured_from_prepare_candle_not_execution_candle():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 115.0, 105.0],
        low_prices=[99.0, 80.0, 99.0],
        close_prices=[100.0, 100.0, 105.0],
    )
    strategy = FixedSignalStrategy(
        size=1.0,
        long_entry_rows=[0],
        long_take_profit_prices={1: 110.0},
        long_stop_loss_prices={1: 95.0},
    )
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

    trade = report.trades[0]
    assert trade.take_profit_price is None
    assert trade.stop_loss_price is None
    assert trade.exit_price == pytest.approx(105.0)
    assert trade.exit_reason == 'end_of_data'


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


def test_slippage_applies_to_take_profit_exit():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 115.0, 101.0],
        low_prices=[99.0, 98.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, long_entry_rows=[0], long_take_profit_prices={0: 110.0})
    report = _backtest_report(
        strategy=strategy,
        data=data,
        config={
            'initial_balance': 1000.0,
            'entry_fee_pct': 0.0,
            'exit_fee_pct': 0.0,
            'slippage_pct': 5.0,
            'slippage_seed': 123,
        },
    )

    trade = report.trades[0]
    assert trade.take_profit_price == pytest.approx(110.0)
    assert trade.exit_price < trade.take_profit_price
    assert trade.exit_reason == 'take_profit'


def test_slippage_applies_to_stop_loss_exit():
    data = _price_frame(
        open_prices=[100.0, 100.0, 100.0],
        high_prices=[101.0, 102.0, 101.0],
        low_prices=[99.0, 90.0, 99.0],
        close_prices=[100.0, 100.0, 100.0],
    )
    strategy = FixedSignalStrategy(size=1.0, long_entry_rows=[0], long_stop_loss_prices={0: 95.0})
    report = _backtest_report(
        strategy=strategy,
        data=data,
        config={
            'initial_balance': 1000.0,
            'entry_fee_pct': 0.0,
            'exit_fee_pct': 0.0,
            'slippage_pct': 5.0,
            'slippage_seed': 123,
        },
    )

    trade = report.trades[0]
    assert trade.stop_loss_price == pytest.approx(95.0)
    assert trade.exit_price < trade.stop_loss_price
    assert trade.exit_reason == 'stop_loss'


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
