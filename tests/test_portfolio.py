import pandas as pd

from zstar.core.backtest.asset_portfolio import Portfolio
from zstar.core.enums import TradeSide
from zstar.core.trade_order import Order


def test_portfolio_without_position_reports_empty_state():
    portfolio = Portfolio()

    assert portfolio.get_position() is None
    assert portfolio.has_position() is False
    assert portfolio.is_position() is False
    assert portfolio.is_position_open() is False
    assert portfolio.is_position_pending_open() is False
    assert portfolio.is_position_pending_close() is False


def test_portfolio_position_lifecycle_states():
    portfolio = Portfolio()
    order = Order(TradeSide.LONG)

    portfolio.open_position(order)
    assert portfolio.has_position() is True
    assert portfolio.is_position_pending_open() is True

    order.open(price=100.0, datetime=pd.Timestamp("2026-01-01 10:00:00"), size=1.0)
    assert portfolio.is_position_open() is True
    assert portfolio.is_position_pending_open() is False

    portfolio.set_pending_close()
    assert portfolio.is_position_pending_close() is True


def test_portfolio_set_pending_close_is_noop_when_position_not_open():
    portfolio = Portfolio()
    order = Order(TradeSide.SHORT)
    portfolio.open_position(order)

    portfolio.set_pending_close()

    assert portfolio.is_position_pending_open() is True
    assert portfolio.is_position_pending_close() is False
