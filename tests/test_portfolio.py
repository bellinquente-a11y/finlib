from finlib import value_portfolio, Equity, Trade, Portfolio
from decimal import Decimal

def test_value_portfolio_calculation():
    positions = {"BHP": (Equity("BHP", Decimal(130.)), 10.), 
                 "XYZ": (Equity("BHP", Decimal(150.)), -10.)}
    value = value_portfolio(positions)
    assert value == {"BHP": Decimal(1300), "XYZ": Decimal(-1500)}

def test_portfolio_len():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL')]
    p = Portfolio(name='My Portfolio', trades=trades)
    assert len(p)==2

def test_portfolio_contains():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL')]
    p = Portfolio(name='My Portfolio', trades=trades)
    assert ("BHP" in p) and ("CBA" not in p)

def test_portfolio_iter():
    trades = [Trade(symbol='BHP', quantity=Decimal(100), price=Decimal('45.50'), side='BUY'),
              Trade(symbol='AAP', quantity=Decimal(200), price=Decimal('10.00'), side='SELL')]
    p = Portfolio(name='My Portfolio', trades=trades)
    for i, trade in enumerate(p):
        assert trade == trades[i]