from finlib import value_portfolio, Equity, Trade, Portfolio
from decimal import Decimal
from datetime import datetime
import pandas as pd

_TIMESTAMP1 = datetime(2026,2,1,3,0,0)
_TIMESTAMP2 = datetime(2026,2,4,2,9,0)
_TIMESTAMP3 = datetime(2026,2,6,3,5,0)
_TIMESTAMP4 = datetime(2026,2,8,3,44,0)
_TIMESTAMP5 = datetime(2026,2,11,3,33,0)
_TRADE1 = Trade(symbol="BHP", quantity=Decimal(100), price=Decimal(45.), side="BUY", timestamp=_TIMESTAMP1)
_TRADE2 = Trade(symbol="BHP", quantity=Decimal(40), price=Decimal(48.), side="SELL", timestamp=_TIMESTAMP3)
_TRADE3 = Trade(symbol="BHP", quantity=Decimal(90), price=Decimal(52.), side="SELL", timestamp=_TIMESTAMP5)
_TRADE4 = Trade(symbol="AAA", quantity=Decimal(100), price=Decimal(12.), side="SELL", timestamp=_TIMESTAMP2)
_TRADE5 = Trade(symbol="AAA", quantity=Decimal(100), price=Decimal(19.), side="SELL", timestamp=_TIMESTAMP4)

# Mark to market prices
_MM_TIMESTAMPS = [
    datetime(2026,2,1,2,0,0),
    datetime(2026,2,2,2,0,0),
    datetime(2026,2,6,3,5,0),
    datetime(2026,2,12,2,0,0),
]
_MM_PRICES = pd.DataFrame(
    data = [
        [Decimal(11.3), Decimal(50.4)],
        [Decimal(12.3), Decimal(51.4)],
        [Decimal(13.3), Decimal(52.4)],
        [Decimal(14.3), Decimal(53.4)],
    ],
    columns = ["AAA", "BHP"],
    index = _MM_TIMESTAMPS
)


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

def test_portfolio_historic_position():
    p = Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])
    pos = p.historic_position()
    exp_pos = pd.DataFrame(data = [
        [Decimal(0), Decimal(100)],
        [Decimal(-100), Decimal(100)],
        [Decimal(-100), Decimal(60)],
        [Decimal(-200), Decimal(60)],
        [Decimal(-200), Decimal(-30)],
    ], 
    columns=["AAA", "BHP"], index = [_TIMESTAMP1, _TIMESTAMP2, _TIMESTAMP3, _TIMESTAMP4, _TIMESTAMP5])
    assert (pos==exp_pos).all().all()

def test_portfolio_historic_cost_basis():
    p = Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])
    cost = p.historic_cost_basis()
    exp_cost = -pd.DataFrame(data = [
        [Decimal(0), Decimal(100*45)],
        [Decimal(-100*12), Decimal(100*45)],
        [Decimal(-100*12), Decimal(100*45-40*48)],
        [Decimal(-100*12-100*19), Decimal(100*45-40*48)],
        [Decimal(-100*12-100*19), Decimal(100*45-40*48-90*52)],
    ], 
    columns=["AAA", "BHP"], index = [_TIMESTAMP1, _TIMESTAMP2, _TIMESTAMP3, _TIMESTAMP4, _TIMESTAMP5])
    assert (cost==exp_cost).all().all()

def test_historic_market_value_calculation():
    p = Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])
    mv = p.historic_market_value(_MM_PRICES)
    exp_mv = pd.DataFrame(
        data = [
            [Decimal(0), Decimal(0)],
            [Decimal(0), Decimal(51.4)*Decimal(100)],
            [Decimal(13.3)*Decimal(-100), Decimal(52.4)*Decimal(60)],
            [Decimal(14.3)*Decimal(-200), Decimal(53.4)*Decimal(-30)],
        ],
        columns = ["AAA", "BHP"],
        index = _MM_TIMESTAMPS
    )
    assert (mv == exp_mv).all().all()

def test_historic_pnl_calculation():
    p = Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])
    pnl = p.historic_pnl(_MM_PRICES)
    exp_pnl = pd.DataFrame(
        data = [
            [Decimal(0), Decimal(0)],
            [Decimal(0), Decimal(51.4)*Decimal(100)-Decimal(45.)*Decimal(100)],
            [Decimal(13.3)*Decimal(-100)-Decimal(12.)*Decimal(-100), 
             Decimal(52.4)*Decimal(60)-Decimal(45.)*Decimal(100)-Decimal(48)*Decimal(-40)],
            [Decimal(14.3)*Decimal(-200)-Decimal(12.)*Decimal(-100)-Decimal(19.)*Decimal(-100), 
             Decimal(53.4)*Decimal(-30)-Decimal(45.)*Decimal(100)-Decimal(48)*Decimal(-40)-Decimal(52)*Decimal(-90)],
        ],
        columns = ["AAA", "BHP"],
        index = _MM_TIMESTAMPS
    )
    assert (pnl == exp_pnl).all().all()
