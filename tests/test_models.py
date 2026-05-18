import pytest
from decimal import Decimal
from src.finlib.models import Trade

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