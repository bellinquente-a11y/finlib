from finlib import value_portfolio, Equity
from decimal import Decimal

def test_value_portfolio_calculation():
    positions = {"BHP": (Equity("BHP", Decimal(130.)), 10.), 
                 "XYZ": (Equity("BHP", Decimal(150.)), -10.)}
    value = value_portfolio(positions)
    assert value == {"BHP": Decimal(1300), "XYZ": Decimal(-1500)}