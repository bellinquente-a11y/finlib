from finlib import value_portfolio, Equity, Portfolio
from decimal import Decimal
import pandas as pd

def test_value_portfolio_calculation():
    positions = {"BHP": (Equity("BHP", Decimal(130.)), 10.), 
                 "XYZ": (Equity("BHP", Decimal(150.)), -10.)}
    value = value_portfolio(positions)
    assert value == {"BHP": Decimal(1300), "XYZ": Decimal(-1500)}

def test_portfolio_len(sample_portfolio):
    assert len(sample_portfolio)==6

def test_portfolio_contains(sample_portfolio):
    assert ("BBB" in sample_portfolio) and ("CBA" not in sample_portfolio)

def test_portfolio_iter(sample_trades):
    p = Portfolio(name='My Portfolio', trades=sample_trades)
    for i, trade in enumerate(p):
        assert trade == sample_trades[i]

def test_portfolio_historic_position(sample_historic_portfolio):
    pos = sample_historic_portfolio.historic_position()
    exp_pos = pd.DataFrame(data = [
        [Decimal(0), Decimal(100)],
        [Decimal(-100), Decimal(100)],
        [Decimal(-100), Decimal(60)],
        [Decimal(-200), Decimal(60)],
        [Decimal(-200), Decimal(-30)],
    ], 
    columns=["AAA", "BHP"], index = sorted([t.timestamp for t in sample_historic_portfolio]))
    assert (pos==exp_pos).all().all()

def test_portfolio_historic_cost_basis(sample_historic_portfolio):
    cost = sample_historic_portfolio.historic_cost_basis()
    exp_cost = -pd.DataFrame(data = [
        [Decimal(0), Decimal(100*45)],
        [Decimal(-100*12), Decimal(100*45)],
        [Decimal(-100*12), Decimal(100*45-40*48)],
        [Decimal(-100*12-100*19), Decimal(100*45-40*48)],
        [Decimal(-100*12-100*19), Decimal(100*45-40*48-90*52)],
    ], 
    columns=["AAA", "BHP"], index = sorted([t.timestamp for t in sample_historic_portfolio]))
    assert (cost==exp_cost).all().all()

def test_historic_market_value_calculation(sample_historic_portfolio, sample_market_making_prices):
    mv = sample_historic_portfolio.historic_market_value(sample_market_making_prices)
    exp_mv = pd.DataFrame(
        data = [
            [Decimal(0), Decimal(0)],
            [Decimal(0), Decimal(51.4)*Decimal(100)],
            [Decimal(13.3)*Decimal(-100), Decimal(52.4)*Decimal(60)],
            [Decimal(14.3)*Decimal(-200), Decimal(53.4)*Decimal(-30)],
        ],
        columns = ["AAA", "BHP"],
        index = sample_market_making_prices.index
    )
    assert (mv == exp_mv).all().all()

def test_historic_pnl_calculation(sample_historic_portfolio, sample_market_making_prices):
    pnl = sample_historic_portfolio.historic_pnl(sample_market_making_prices)
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
        index = sample_market_making_prices.index
    )
    assert (pnl == exp_pnl).all().all()
