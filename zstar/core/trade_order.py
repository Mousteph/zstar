from zstar.core.enums.trade_side import TradeSide
from zstar.core.enums.trade_status import TradeStatus
from dataclasses import dataclass
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


class Order:
    def get_side(self) -> TradeSide:
        return self.__side

    
    def get_status(self) -> TradeStatus:
        return self.__status


    def get_size(self) -> float:
        return self.__size


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

        self.__status = TradeStatus.PENDING_OPEN


    def open(self, price: float, datetime: pd.Timestamp, size: float, fee: float = 0.0):
        self.__entry_price = price
        self.__entry_datetime = datetime
        self.__size = size
        self.__entry_fee = fee
        self.__status = TradeStatus.OPEN


    def close(self, price: float, datetime: pd.Timestamp, fee: float = 0.0):
        self.__exit_price = price
        self.__exit_datetime = datetime
        self.__exit_fee = fee
        self.__status = TradeStatus.CLOSE

    
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
            entry_datetime=self.__entry_datetime,
            exit_datetime=self.__exit_datetime,
            raw_pnl=raw_pnl,
            entry_fee=self.__entry_fee,
            exit_fee=self.__exit_fee,
            total_fees=total_fees,
            net_pnl=net_pnl
        )
