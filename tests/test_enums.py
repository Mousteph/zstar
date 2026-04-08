from zstar.core.enums import TradeSide, TradeStatus


def test_trade_side_helpers_and_conversions():
    assert TradeSide.LONG.is_long() is True
    assert TradeSide.LONG.is_short() is False
    assert TradeSide.SHORT.is_short() is True
    assert TradeSide.LONG.to_sign() == 1
    assert TradeSide.SHORT.to_sign() == -1
    assert int(TradeSide.LONG) == 1
    assert str(TradeSide.SHORT) == "SHORT"
    assert TradeSide.LONG.opposite() == TradeSide.SHORT
    assert TradeSide.SHORT.opposite() == TradeSide.LONG


def test_trade_status_helpers():
    assert TradeStatus.OPEN.is_open() is True
    assert TradeStatus.CLOSE.is_close() is True
    assert TradeStatus.PENDING_OPEN.is_pending_open() is True
    assert TradeStatus.PENDING_CLOSE.is_pending_close() is True
    assert str(TradeStatus.PENDING_CLOSE) == "PENDING_CLOSE"
