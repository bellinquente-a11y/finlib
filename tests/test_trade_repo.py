from finlib.trade_repo import InMemoryTradeRepository, PortfolioService
from finlib.models import Trade
from decimal import Decimal
import pytest

def test_portfolio_service_position_missing_symbol():
    t1 = Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(100.), side="BUY")
    trade_repo = InMemoryTradeRepository()
    trade_repo.add(t1)
    ps = PortfolioService(trade_repo)
    with pytest.raises(ValueError):
        _ = ps.get_position("BBB")

def test_portfolio_service_position_calculation():
    t1 = Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(100.), side="BUY")
    t2 = Trade(symbol="AAA", quantity=Decimal(30.), price=Decimal(100.), side="BUY")
    t3 = Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(100.), side="SELL")
    trade_repo = InMemoryTradeRepository()
    for trade in [t1, t2, t3]:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_position("AAA") == Decimal(25.)

def test_portfolio_service_summary_calculation():
    t1 = Trade(symbol="BBB", quantity=Decimal(10.), price=Decimal(100.), side="BUY")
    t2 = Trade(symbol="BBB", quantity=Decimal(30.), price=Decimal(100.), side="SELL")
    t3 = Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(100.), side="SELL")
    trade_repo = InMemoryTradeRepository()
    for trade in [t1, t2, t3]:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_summary() == {"AAA": Decimal(-15), "BBB": Decimal(-20)}