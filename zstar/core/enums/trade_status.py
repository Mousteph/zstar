from enum import Enum

class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    PENDING_OPEN = "PENDING_OPEN"
    PENDING_CLOSE = "PENDING_CLOSE"

    def __str__(self):
        return self.value

    def is_open(self):
        return self == TradeStatus.OPEN

    def is_close(self):
        return self == TradeStatus.CLOSE

    def is_pending_open(self):
        return self == TradeStatus.PENDING_OPEN

    def is_pending_close(self):
        return self == TradeStatus.PENDING_CLOSE
