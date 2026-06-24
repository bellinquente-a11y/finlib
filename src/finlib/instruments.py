from abc import ABC, abstractmethod
from decimal import Decimal

from typing import Protocol, runtime_checkable

class Instrument(ABC):
    """Abstract base class for all instruments"""

    @property
    @abstractmethod
    def symbol(self) -> str: ...

    @abstractmethod
    def price(self) -> Decimal: ...

    @abstractmethod
    def description(self) -> str: ...

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.symbol!r})'


class Equity(Instrument):
    """Equity instrument"""

    def __init__(self, ticker: str, current_price: Decimal) -> None:
        if not isinstance(current_price, Decimal): 
            raise TypeError
        self._symbol = ticker.upper()
        self._price = current_price

    @property
    def symbol(self) -> str: return self._symbol

    def price(self) -> Decimal: return self._price
    
    def description(self) -> str:
        return f'Equity: {self._symbol} @ {self._price:.2f}'


class Future(Instrument):
    """Future instrument"""

    def __init__(self, ticker: str, current_price: Decimal) -> None:
        if not isinstance(current_price, Decimal): 
            raise TypeError
        self._symbol = ticker.upper()
        self._price = current_price

    @property
    def symbol(self) -> str: return self._symbol

    def price(self) -> Decimal: return self._price
    
    def description(self) -> str:
        return f'Future: {self._symbol} @ {self._price:.2f}'


@runtime_checkable
class Priceable(Protocol):
    """Protocol for all instruments that can be priced"""

    @property
    def symbol(self) -> str: ...
    def price(self) -> Decimal: ...

class ThirdPartyInstrument(Priceable):
    """Third party instrument"""

    @property
    def symbol(self) -> str: return 'XYZ'
    def price(self) -> Decimal: return Decimal('100.00')

def get_value(instrument: Priceable, qty: float) -> Decimal:
    """Get the value of an instrument"""

    return instrument.price() * Decimal(qty)