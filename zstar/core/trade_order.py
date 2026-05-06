from zstar.core.enums.trade_side import TradeSide
from zstar.core.enums.trade_status import TradeStatus
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import uuid


@dataclass(frozen=True)
class Trade:
    id: str
    trade_name: str
    side: TradeSide
    size: float
    entry_price: float
    exit_price: float
    entry_datetime: pd.Timestamp
    exit_datetime: pd.Timestamp
    raw_pnl: float
    entry_fee: float
    exit_fee: float
    total_fees: float
    net_pnl: float
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    exit_reason: str = "signal"


class Order:
    def get_side(self) -> TradeSide:
        return self.__side

    
    def get_status(self) -> TradeStatus:
        return self.__status


    def get_size(self) -> float:
        return self.__size


    def get_entry_price(self) -> float:
        return self.__entry_price


    def get_take_profit_price(self) -> Optional[float]:
        return self.__take_profit_price


    def get_stop_loss_price(self) -> Optional[float]:
        return self.__stop_loss_price


    def __init__(self, side: TradeSide, trade_name: str = ""):
        self.__id = uuid.uuid4().hex
        self.__trade_name = trade_name
        self.__side = side
        self.__size = 0.0
        self.__entry_price = 0.0
        self.__exit_price = 0.0
        self.__entry_datetime = pd.NaT
        self.__exit_datetime = pd.NaT
        self.__entry_fee = 0.0
        self.__exit_fee = 0.0
        self.__take_profit_price: Optional[float] = None
        self.__stop_loss_price: Optional[float] = None
        self.__exit_reason = "signal"

        self.__status = TradeStatus.PENDING_OPEN


    def open(self, price: float, datetime: pd.Timestamp, size: float, fee: float = 0.0):
        self.__entry_price = price
        self.__entry_datetime = datetime
        self.__size = size
        self.__entry_fee = fee
        self.__status = TradeStatus.OPEN


    def close(self, price: float, datetime: pd.Timestamp, fee: float = 0.0, exit_reason: str = "signal"):
        self.__exit_price = price
        self.__exit_datetime = datetime
        self.__exit_fee = fee
        self.__exit_reason = exit_reason
        self.__status = TradeStatus.CLOSE


    def set_risk_prices(self, take_profit_price: Optional[float], stop_loss_price: Optional[float]):
        self.__take_profit_price = take_profit_price
        self.__stop_loss_price = stop_loss_price

    
    def set_pending_close(self):
        self.__status = TradeStatus.PENDING_CLOSE

    
    def to_trade(self) -> Trade:
        raw_pnl = (self.__exit_price - self.__entry_price) * self.__size * self.__side.to_sign()
        total_fees = self.__entry_fee + self.__exit_fee
        net_pnl = raw_pnl - total_fees

        return Trade(
            id=self.__id,
            trade_name=self.__trade_name,
            side=self.__side,
            size=self.__size,
            entry_price=self.__entry_price,
            exit_price=self.__exit_price,
            take_profit_price=self.__take_profit_price,
            stop_loss_price=self.__stop_loss_price,
            exit_reason=self.__exit_reason,
            entry_datetime=self.__entry_datetime,
            exit_datetime=self.__exit_datetime,
            raw_pnl=raw_pnl,
            entry_fee=self.__entry_fee,
            exit_fee=self.__exit_fee,
            total_fees=total_fees,
            net_pnl=net_pnl
        )
