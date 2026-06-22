from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Literal, Protocol, runtime_checkable
from decimal import Decimal

class Trade(BaseModel):
    """Class representing a trade"""
    
    model_config = {'frozen': True, 'str_strip_whitespace': True}

    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    side: Literal['BUY', 'SELL']
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator('symbol')
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        return v.upper()

    @property
    def notional(self) -> Decimal:
        """Calculate the SIGNED notional value of the trade"""

        if self.side == 'BUY':
            return self.quantity * self.price
        elif self.side == 'SELL':
            return -1 * (self.quantity * self.price)    
        else:
            raise ValueError(f"Invalid side: {self.side}")

    def lot_size(self) -> Decimal:
        """Get the lot size of the trade"""
        return self.quantity if self.side == 'BUY' else -1 * self.quantity

    def __str__(self) -> str:
        return f"Trade(symbol={self.symbol!r}, quantity={self.quantity!r}, price={self.price!r}, side={self.side!r}, timestamp={self.timestamp!r})"

@runtime_checkable
class Tradeable(Protocol):
    """Protocol for a generic trade"""

    @property
    def symbol(self) -> str: ...
    @property
    def price(self) -> Decimal: ...
    def lot_size(self) -> Decimal: ...

def is_valid_trade_size(instrument: Tradeable, notional: Decimal) -> bool:
    """Check if a trade is a valid size"""

    return bool(instrument.lot_size()*instrument.price == notional)

# t = Trade(symbol='bhp', quantity=Decimal('100'), price=Decimal('45.50'), side='BUY')
# print(is_valid_trade_size(t, Decimal('4550.00')))
# print(t.symbol)    # BHP
# print(t.notional)  # Decimal('4550.00')

