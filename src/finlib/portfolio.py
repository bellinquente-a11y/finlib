from decimal import Decimal
from itertools import groupby
from typing import Generator

import pandas as pd
from pydantic import BaseModel, Field

from finlib.instruments import Priceable
from finlib.models import Trade


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

    def historic_position(self) -> pd.DataFrame:
        """
        Returns a DataFrame with the historic position of the porfolio in number of contracts
            index: timestamp associated to the tarde
            columns: symbols of the contracts in the portfolio
        """
        sorted_trades = sorted(self.trades, key=lambda t: (t.symbol, t.timestamp))
        dhld = pd.DataFrame()
        for key, group in groupby(sorted_trades, key=lambda t: t.symbol):
            group_trades = [*group]
            dhld_symbol = pd.DataFrame(
                data = [[t.lot_size()] for t in group_trades], 
                columns=[key], 
                index = [t.timestamp for t in group_trades]
                )
            dhld = pd.concat((dhld, dhld_symbol), axis=1, sort=True)
        return dhld.fillna(value=0).cumsum(axis=0)

    def historic_cost_basis(self) -> pd.DataFrame:
        """
        Returns the costs basis of the portfolio. This is equal to MINUS the cumulative 
        sum of the signed notional of all trades at execution price.
            index: timestamp associated to the tarde
            columns: symbols of the contracts in the portfolio
        """
        sorted_trades = sorted(self.trades, key=lambda t: (t.symbol, t.timestamp))
        dhld = pd.DataFrame()
        for key, group in groupby(sorted_trades, key=lambda t: t.symbol):
            group_trades = [*group]
            dhld_symbol = pd.DataFrame(
                data = [[t.notional] for t in group_trades], 
                columns=[key], 
                index = [t.timestamp for t in group_trades]
                )
            dhld = pd.concat((dhld, dhld_symbol), axis=1, sort=True)
        return -dhld.fillna(value=0).cumsum(axis=0)

    def historic_market_value(self, price: pd.DataFrame) -> pd.DataFrame:
        """
        Returns the historic market value of the portfolio from marking-to-market prices. 
        Both input and output have:
            index: timestamp associated to the tarde
            columns: symbols of the contracts in the portfolio
        """
        holdings = self.historic_position()
        symbols = holdings.columns

        if not set(symbols) <= set(price.columns):
            missing_symbols = list(set(symbols) - set(price.columns))
            raise ValueError(f"price missing for: {", ".join(missing_symbols)}")

        holdings_resampled = holdings.reindex(price.index, method="ffill").fillna(0)
        return holdings_resampled * price[symbols]

    def historic_pnl(self, price: pd.DataFrame) -> pd.DataFrame:
        """
        Returns the historic PnL associated with the portfolio from marking-to-market prices. 
        Both input and output have:
            index: timestamp associated to the trade
            columns: symbols of the contracts in the portfolio
        """
        cost_basis = (
            self.historic_cost_basis()
            .reindex(price.index, method="ffill")
            .fillna(0)
        )
        return self.historic_market_value(price) + cost_basis

def value_portfolio(
    positions: dict[str, tuple[Priceable, float]]
) -> dict[str, Decimal]:
    """Get the value of a portfolio"""

    return {
        name: instrument.price() * Decimal(qty)
        for name, (instrument, qty) in positions.items()
    }