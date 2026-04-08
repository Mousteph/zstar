from __future__ import annotations

from typing import Optional

from zstar.core.trade_order import Order


class Portfolio:
    def __init__(self) -> None:
        self._open_position: Optional[Order] = None

    def open_position(self, order: Order) -> None:
        self._open_position = order

    def get_position(self) -> Optional[Order]:
        return self._open_position

    def has_position(self) -> bool:
        return self._open_position is not None

    def is_position(self) -> bool:
        return self.has_position()

    def is_position_open(self) -> bool:
        return self.has_position() and self._open_position.get_status().is_open()

    def is_position_pending_open(self) -> bool:
        return self.has_position() and self._open_position.get_status().is_pending_open()

    def is_position_pending_close(self) -> bool:
        return self.has_position() and self._open_position.get_status().is_pending_close()

    def set_pending_close(self) -> None:
        if self.is_position_open():
            self._open_position.set_pending_close()
