import numpy as np
import pandas as pd
import pytest

from zstar.core.backtest.backtest_report import BacktestReport
from zstar.core.backtest.backtest_report_timeseries import buy_and_hold_equity_curve
from zstar.core.backtest.backtest_report_timeseries import strategy_equity_curve
from zstar.core.enums import TradeSide
from zstar.core.trade_order import Trade


def _trade(
    *,
    trade_id: str,
    entry_datetime: pd.Timestamp,
    exit_datetime: pd.Timestamp,
    net_pnl: float,
    raw_pnl: float | None = None,
    entry_fee: float = 0.0,
    exit_fee: float = 0.0,
    side: TradeSide = TradeSide.LONG,
) -> Trade:
    resolved_raw_pnl = net_pnl if raw_pnl is None else raw_pnl
    total_fees = entry_fee + exit_fee

    return Trade(
        id=trade_id,
        trade_name='',
        side=side,
        size=1.0,
        entry_price=100.0,
        exit_price=100.0 + net_pnl,
        entry_datetime=entry_datetime,
        exit_datetime=exit_datetime,
        raw_pnl=resolved_raw_pnl,
        entry_fee=entry_fee,
        exit_fee=exit_fee,
        total_fees=total_fees,
        net_pnl=net_pnl,
    )


def test_sharpe_ratio_annualization_uses_interval():
    index = pd.date_range('2026-01-01 09:30:00', periods=6, freq='h')
    data = pd.DataFrame(
        {
            'open': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5],
        },
        index=index,
    )
    trades = [
        _trade(
            trade_id='t1',
            entry_datetime=index[0],
            exit_datetime=index[1],
            net_pnl=120.0,
        ),
        _trade(
            trade_id='t2',
            entry_datetime=index[2],
            exit_datetime=index[3],
            net_pnl=-60.0,
        ),
        _trade(
            trade_id='t3',
            entry_datetime=index[4],
            exit_datetime=index[5],
            net_pnl=90.0,
        ),
    ]

    initial_balance = 10_000.0
    final_balance = initial_balance + sum(trade.net_pnl for trade in trades)

    daily_report = BacktestReport(
        initial_balance=initial_balance,
        final_balance=final_balance,
        trades=trades,
        data=data,
        interval='1d',
    )
    hourly_report = BacktestReport(
        initial_balance=initial_balance,
        final_balance=final_balance,
        trades=trades,
        data=data,
        interval='1h',
    )

    strategy_returns = strategy_equity_curve(initial_balance, trades, data).pct_change().dropna()
    base_sharpe = strategy_returns.mean() / strategy_returns.std(ddof=1)
    expected_daily = float(base_sharpe * np.sqrt(252.0))
    expected_hourly = float(base_sharpe * np.sqrt(252.0 * 6.5))

    assert daily_report.kpis()['sharpe_ratio'] == pytest.approx(expected_daily)
    assert hourly_report.kpis()['sharpe_ratio'] == pytest.approx(expected_hourly)
    assert hourly_report.kpis()['sharpe_ratio'] > daily_report.kpis()['sharpe_ratio']


def test_kpis_are_calculated_correctly_for_deterministic_inputs():
    index = pd.date_range('2026-01-01', periods=4, freq='D')
    data = pd.DataFrame(
        {
            'open': [100.0, 110.0, 90.0, 120.0],
            'close': [100.0, 110.0, 90.0, 120.0],
        },
        index=index,
    )
    trades = [
        _trade(
            trade_id='t1',
            entry_datetime=index[1] - pd.Timedelta(minutes=60),
            exit_datetime=index[1],
            net_pnl=50.0,
            raw_pnl=55.0,
            entry_fee=2.0,
            exit_fee=3.0,
        ),
        _trade(
            trade_id='t2',
            entry_datetime=index[2] - pd.Timedelta(minutes=120),
            exit_datetime=index[2],
            net_pnl=-20.0,
            raw_pnl=-16.0,
            entry_fee=1.0,
            exit_fee=3.0,
        ),
        _trade(
            trade_id='t3',
            entry_datetime=index[3] - pd.Timedelta(minutes=30),
            exit_datetime=index[3],
            net_pnl=30.0,
            raw_pnl=31.0,
            entry_fee=1.0,
            exit_fee=0.0,
        ),
    ]

    report = BacktestReport(
        initial_balance=1000.0,
        final_balance=1060.0,
        trades=trades,
        data=data,
        interval='1d',
    )

    kpis = report.kpis()
    strategy_curve = strategy_equity_curve(report.initial_balance, report.trades, report.data)
    strategy_returns = strategy_curve.pct_change().dropna()
    expected_sharpe = float((strategy_returns.mean() / strategy_returns.std(ddof=1)) * np.sqrt(252.0))

    assert kpis['initial_balance'] == pytest.approx(1000.0)
    assert kpis['final_balance'] == pytest.approx(1060.0)
    assert kpis['net_pnl'] == pytest.approx(60.0)
    assert kpis['total_return_pct'] == pytest.approx(6.0)
    assert kpis['total_trades'] == 3
    assert kpis['total_fees'] == pytest.approx(10.0)
    assert kpis['gross_profit'] == pytest.approx(80.0)
    assert kpis['gross_loss'] == pytest.approx(20.0)
    assert kpis['win_rate_pct'] == pytest.approx((2 / 3) * 100)
    assert kpis['avg_trade_pnl'] == pytest.approx(20.0)
    assert kpis['avg_win'] == pytest.approx(40.0)
    assert kpis['avg_loss'] == pytest.approx(-20.0)
    assert kpis['profit_factor'] == pytest.approx(4.0)
    assert 'expectancy' not in kpis
    assert kpis['max_drawdown_pct'] == pytest.approx(-1.904761904761909)
    assert kpis['sharpe_ratio'] == pytest.approx(expected_sharpe)
    assert kpis['best_trade'] == pytest.approx(50.0)
    assert kpis['worst_trade'] == pytest.approx(-20.0)
    assert kpis['median_trade'] == pytest.approx(30.0)
    assert kpis['avg_trade_duration_minutes'] == pytest.approx(70.0)

    assert kpis['buy_and_hold_final_balance'] == pytest.approx(1200.0)
    assert kpis['buy_and_hold_return_pct'] == pytest.approx(20.0)
    assert kpis['buy_and_hold_max_drawdown_pct'] == pytest.approx(-18.181818181818176)
    assert kpis['return_diff_vs_buy_and_hold_pct'] == pytest.approx(-14.0)


def test_kpis_with_no_trades_produces_expected_zero_and_nan_values():
    index = pd.date_range('2026-01-01', periods=3, freq='D')
    data = pd.DataFrame(
        {
            'open': [100.0, 101.0, 102.0],
            'close': [100.0, 101.0, 102.0],
        },
        index=index,
    )
    report = BacktestReport(
        initial_balance=1000.0,
        final_balance=1000.0,
        trades=[],
        data=data,
        interval='1d',
    )

    kpis = report.kpis()

    assert kpis['total_trades'] == 0
    assert kpis['net_pnl'] == pytest.approx(0.0)
    assert kpis['total_return_pct'] == pytest.approx(0.0)
    assert kpis['total_fees'] == pytest.approx(0.0)
    assert kpis['gross_profit'] == pytest.approx(0.0)
    assert kpis['gross_loss'] == pytest.approx(0.0)
    assert kpis['win_rate_pct'] == pytest.approx(0.0)
    assert kpis['avg_trade_pnl'] == pytest.approx(0.0)
    assert kpis['avg_win'] == pytest.approx(0.0)
    assert kpis['avg_loss'] == pytest.approx(0.0)
    assert np.isnan(kpis['profit_factor'])
    assert 'expectancy' not in kpis
    assert kpis['max_drawdown_pct'] == pytest.approx(0.0)
    assert np.isnan(kpis['sharpe_ratio'])
    assert kpis['best_trade'] == pytest.approx(0.0)
    assert kpis['worst_trade'] == pytest.approx(0.0)
    assert kpis['median_trade'] == pytest.approx(0.0)
    assert kpis['avg_trade_duration_minutes'] == pytest.approx(0.0)
    assert kpis['buy_and_hold_final_balance'] == pytest.approx(1020.0)
    assert kpis['buy_and_hold_return_pct'] == pytest.approx(2.0)
    assert kpis['buy_and_hold_max_drawdown_pct'] == pytest.approx(0.0)
    assert kpis['return_diff_vs_buy_and_hold_pct'] == pytest.approx(-2.0)


def test_profit_factor_is_infinite_when_no_losses_exist():
    index = pd.date_range('2026-01-01', periods=3, freq='D')
    data = pd.DataFrame(
        {
            'open': [100.0, 101.0, 102.0],
            'close': [100.0, 101.0, 102.0],
        },
        index=index,
    )
    trades = [
        _trade(
            trade_id='t1',
            entry_datetime=index[0],
            exit_datetime=index[1],
            net_pnl=25.0,
        ),
        _trade(
            trade_id='t2',
            entry_datetime=index[1],
            exit_datetime=index[2],
            net_pnl=15.0,
        ),
    ]
    report = BacktestReport(1000.0, 1040.0, trades, data)

    assert np.isinf(report.kpis()['profit_factor'])


def test_strategy_equity_curve_marks_open_trade_to_market():
    index = pd.date_range('2026-01-01', periods=4, freq='D')
    data = pd.DataFrame(
        {
            'open': [100.0, 100.0, 100.0, 100.0],
            'close': [100.0, 110.0, 90.0, 120.0],
        },
        index=index,
    )
    trade = Trade(
        id='t1',
        trade_name='',
        side=TradeSide.LONG,
        size=2.0,
        entry_price=100.0,
        exit_price=120.0,
        entry_datetime=index[0],
        exit_datetime=index[3],
        raw_pnl=40.0,
        entry_fee=1.0,
        exit_fee=2.0,
        total_fees=3.0,
        net_pnl=37.0,
    )
    report = BacktestReport(1000.0, 1037.0, [trade], data)

    assert strategy_equity_curve(report.initial_balance, report.trades, report.data).tolist() == pytest.approx(
        [999.0, 1019.0, 979.0, 1037.0],
    )
    assert report.kpis()['max_drawdown_pct'] == pytest.approx(-3.925417075564278)


def test_sharpe_ratio_subtracts_periodic_risk_free_rate():
    index = pd.date_range('2026-01-01', periods=4, freq='D')
    data = pd.DataFrame(
        {
            'open': [100.0, 100.0, 100.0, 100.0],
            'close': [100.0, 100.0, 100.0, 100.0],
        },
        index=index,
    )
    trades = [
        _trade(
            trade_id='t1',
            entry_datetime=index[0],
            exit_datetime=index[1],
            net_pnl=10.0,
        ),
        _trade(
            trade_id='t2',
            entry_datetime=index[1],
            exit_datetime=index[2],
            net_pnl=-5.0,
        ),
        _trade(
            trade_id='t3',
            entry_datetime=index[2],
            exit_datetime=index[3],
            net_pnl=15.0,
        ),
    ]
    report = BacktestReport(
        initial_balance=1000.0,
        final_balance=1020.0,
        trades=trades,
        data=data,
        risk_free_rate=0.0252,
    )

    returns = strategy_equity_curve(report.initial_balance, report.trades, report.data).pct_change().dropna()
    expected = ((returns.mean() - (0.0252 / 252.0)) / returns.std(ddof=1)) * np.sqrt(252.0)

    assert report.kpis()['sharpe_ratio'] == pytest.approx(float(expected))


def test_buy_and_hold_handles_non_positive_start_price():
    index = pd.date_range('2026-01-01', periods=2, freq='D')
    data = pd.DataFrame(
        {
            'open': [0.0, 100.0],
            'close': [0.0, 100.0],
        },
        index=index,
    )
    report = BacktestReport(1000.0, 1000.0, [], data)
    kpis = report.kpis()
    buy_and_hold_curve = buy_and_hold_equity_curve(report.initial_balance, report.data)

    assert kpis['buy_and_hold_final_balance'] == pytest.approx(1000.0)
    assert kpis['buy_and_hold_return_pct'] == pytest.approx(0.0)
    assert kpis['buy_and_hold_max_drawdown_pct'] == pytest.approx(0.0)
    assert buy_and_hold_curve.empty
