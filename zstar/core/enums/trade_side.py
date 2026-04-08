from enum import Enum

class TradeSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    
    def is_long(self):
        return self == TradeSide.LONG
    
    def is_short(self):
        return self == TradeSide.SHORT
    
    def to_sign(self):
        return 1 if self.is_long() else -1

    def __str__(self):
        return self.value
    
    def __int__(self):
        return self.to_sign()

    def opposite(self):
        return TradeSide.SHORT if self.is_long() else TradeSide.LONG    
