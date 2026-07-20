from decimal import Decimal

import pytest

from finlib.models import Trade
from finlib.portfolio import Portfolio


def test_symbol_is_uppercased():
    t = Trade(symbol='bhp', quantity=100, price=45.5, side='BUY')
    assert t.symbol == 'BHP'

def test_rejects_negative_quantity():
    with pytest.raises(Exception):
        Trade(symbol='BHP', quantity=-10, price=45.5, side='BUY')

def test_notional_calculation():
    t = Trade(symbol='BHP', quantity=100,
              price=Decimal('45.50'), side='BUY')
    assert t.notional == Decimal('4550.00')

def test_portfolio_notional_calculation():
    t1 = Trade(symbol='BHP', quantity=100,
              price=Decimal('45.50'), side='BUY')
    t2 = Trade(symbol='BHP', quantity=200,
              price=Decimal('45.50'), side='SELL')
    p = Portfolio(name='My Portfolio', trades=[t1, t2])
    assert p.notional == Decimal('-4550.00')