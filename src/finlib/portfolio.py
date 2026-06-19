from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Iterator
from finlib import Trade, Priceable, Equity
from finlib.instruments import ThirdPartyInstrument

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
        return any([symbol == trade.symbol for trade in self.trades])

    def iter_trades(self) -> Iterator[Trade]:
        """Iterate over the trades in the portfolio"""

        return iter(self.trades)

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
        

trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'), Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL')]
p = Portfolio(name='My Portfolio', trades=trades)

print(len(p))
print('BHP' in p)
print('CBA' in p)
print([trade.symbol for trade in p.iter_trades()])
print(p[1])


positions: dict[str, tuple[Priceable, float]] = {"BHP": (Equity("BHP", Decimal(131.)), 15.0), "XYZ": (ThirdPartyInstrument(), 11.0)}
# positions = {"BHP": (Equity("BHP", Decimal(131.)), 15)}

# print(value_portfolio(positions))
print(sum(value_portfolio(positions).values()))