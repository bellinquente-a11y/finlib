from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Generator
from finlib import Trade, Priceable

class Portfolio(BaseModel):
    """Class representing a portfolio of trades"""

    model_config = {'frozen': True, 'str_strip_whitespace': True}

    name: str = Field(..., min_length=1)
    trades: list[Trade] = Field(min_length=1)

    @property
    def notional(self) -> Decimal:
        """Calculate the notional value of the portfolio"""

        return Decimal(sum([trade.notional for trade in self.trades]))

    def __len__(self) -> int:
        return len(self.trades)

    def __contains__(self, symbol: str) -> bool:
        for trade in self.trades:
            if trade.symbol == symbol:
                return True
                break
        return False

    def __iter__(self) -> Generator[Trade, None, None]:  # type: ignore[override]
        """Iterate over the trades in the portfolio"""
        for trade in self.trades:
            yield trade

    def __getitem__(self, index: int) -> Trade:
        return self.trades[index]

def value_portfolio(
    positions: dict[str, tuple[Priceable, float]]
) -> dict[str, Decimal]:
    """Get the value of a portfolio"""

    return {
        name: instrument.price() * Decimal(qty)
        for name, (instrument, qty) in positions.items()
    }