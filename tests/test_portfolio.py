from pydantic_core import ValidationError
from finlib import value_portfolio, Equity, Portfolio, Trade
from decimal import Decimal
import pandas as pd
import pytest
from datetime import datetime

def test_portfolio_empty_trade_list_validation_error():
    with pytest.raises(ValidationError):
        _ = Portfolio(name="MyPortfolio", trades = [])


def test_value_portfolio_calculation():
    positions = {"BHP": (Equity("BHP", Decimal(130.)), 10.), 
                 "XYZ": (Equity("BHP", Decimal(150.)), -10.)}
    value = value_portfolio(positions)
    assert value == {"BHP": Decimal(1300), "XYZ": Decimal(-1500)}

def test_portfolio_len(sample_portfolio):
    assert len(sample_portfolio)==6

@pytest.mark.parametrize("symbol,expected", [("BBB", True), ("CBA", False)], ids=["present", "missing"])
def test_portfolio_contains(sample_portfolio, symbol, expected):
    assert (symbol in sample_portfolio) == expected

def test_portfolio_name_missing(sample_trades):
    with pytest.raises(ValidationError):
        _ = Portfolio(name="", trades=sample_trades)

def test_portfolio_iter_trades_order(sample_trades):
    p = Portfolio(name='My Portfolio', trades=sample_trades)
    for i, trade in enumerate(p):
        assert trade == sample_trades[i]

def test_portfolio_get_item_out_of_range(sample_portfolio):
    with pytest.raises(IndexError):
        sample_portfolio[99]

def test_portfolio_notional_calculation(sample_portfolio):
    assert abs(sample_portfolio.notional-Decimal(1_281.41)) <1e-12

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

def test_historic_market_value_missing_symbol(sample_historic_portfolio, sample_market_making_prices):
    sample_historic_portfolio.trades.append(Trade(symbol="ZZZ", quantity=10., price=10., side="BUY", timestamp=datetime(2026,2,1,13,4,56)))
    with pytest.raises(ValueError, match="price missing for: ZZZ"):
        _ = sample_historic_portfolio.historic_market_value(sample_market_making_prices)