import pandas as pd
import pytest

from zstar.core.enums import TradeSide, TradeStatus
from zstar.core.trade_order import Order


def test_order_defaults_to_pending_open():
    order = Order(TradeSide.LONG, trade_name="alpha")

    assert order.get_side() == TradeSide.LONG
    assert order.get_status() == TradeStatus.PENDING_OPEN
    assert order.get_size() == pytest.approx(0.0)


def test_order_open_and_close_for_long_trade_calculates_pnl_and_fees():
    order = Order(TradeSide.LONG, trade_name="alpha")
    entry_dt = pd.Timestamp("2026-01-01 10:00:00")
    exit_dt = pd.Timestamp("2026-01-01 11:00:00")

    order.open(price=100.0, datetime=entry_dt, size=2.0, fee=1.25)
    assert order.get_status() == TradeStatus.OPEN
    assert order.get_size() == pytest.approx(2.0)

    order.close(price=110.0, datetime=exit_dt, fee=0.75)
    assert order.get_status() == TradeStatus.CLOSE

    trade = order.to_trade()
    assert trade.trade_name == "alpha"
    assert trade.raw_pnl == pytest.approx(20.0)
    assert trade.total_fees == pytest.approx(2.0)
    assert trade.net_pnl == pytest.approx(18.0)
    assert trade.entry_datetime == entry_dt
    assert trade.exit_datetime == exit_dt


def test_order_to_trade_for_short_side_uses_negative_sign():
    order = Order(TradeSide.SHORT, trade_name="beta")
    order.open(price=200.0, datetime=pd.Timestamp("2026-01-02 10:00:00"), size=1.5, fee=0.5)
    order.close(price=180.0, datetime=pd.Timestamp("2026-01-02 12:00:00"), fee=0.5)

    trade = order.to_trade()

    assert trade.side == TradeSide.SHORT
    assert trade.raw_pnl == pytest.approx(30.0)
    assert trade.total_fees == pytest.approx(1.0)
    assert trade.net_pnl == pytest.approx(29.0)


def test_order_set_pending_close_updates_status():
    order = Order(TradeSide.LONG)
    order.open(price=100.0, datetime=pd.Timestamp("2026-01-01 10:00:00"), size=1.0)

    order.set_pending_close()

    assert order.get_status() == TradeStatus.PENDING_CLOSE
