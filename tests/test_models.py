from decimal import Decimal

import pytest
from pydantic import ValidationError

from finlib.models import Trade
from finlib.portfolio import Portfolio


def test_symbol_is_uppercased() -> None:
    t = Trade(symbol="bhp", quantity=Decimal(100), price=Decimal(45.5), side="BUY")
    assert t.symbol == "BHP"


def test_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        Trade(symbol="BHP", quantity=Decimal(-10), price=Decimal(45.5), side="BUY")


def test_notional_calculation() -> None:
    t = Trade(symbol="BHP", quantity=Decimal(100), price=Decimal("45.50"), side="BUY")
    assert t.notional == Decimal("4550.00")


def test_portfolio_notional_calculation() -> None:
    t1 = Trade(symbol="BHP", quantity=Decimal(100), price=Decimal("45.50"), side="BUY")
    t2 = Trade(symbol="BHP", quantity=Decimal(200), price=Decimal("45.50"), side="SELL")
    p = Portfolio(name="My Portfolio", trades=[t1, t2])
    assert p.notional == Decimal("-4550.00")
