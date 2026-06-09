from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Literal
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
        """Calculate the notional value of the trade"""

        if self.side == 'BUY':
            return self.quantity * self.price
        elif self.side == 'SELL':
            return -1 * (self.quantity * self.price)    
        else:
            raise ValueError(f"Invalid side: {self.side}")

    def __str__(self) -> str:
        return f"Trade(symbol={self.symbol!r}, quantity={self.quantity!r}, price={self.price!r}, side={self.side!r}, timestamp={self.timestamp!r})"

# t = Trade(symbol='bhp', quantity='100', price='45.50', side='BUY')
# print(t.symbol)    # BHP
# print(t.notional)  # Decimal('4550.00')

