from finlib.trade_repo import TradeRepository, PortfolioService, InMemoryTradeRepository, InFileTradeRepository
from finlib.models import Trade
from decimal import Decimal
import pytest

@pytest.fixture(params = ("memory", "jsonl"))
def trade_repo(request, tmp_path) -> TradeRepository:
    if request.param=="memory":
        return InMemoryTradeRepository()
    elif request.param=="jsonl":
        return InFileTradeRepository(tmp_path / "trade_repo.jsonl")

def test_portfolio_service_position_calculation(trade_repo: TradeRepository):
    t1 = Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(100.), side="BUY")
    t2 = Trade(symbol="AAA", quantity=Decimal(30.), price=Decimal(100.), side="BUY")
    t3 = Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(100.), side="SELL")
    for trade in [t1, t2, t3]:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_position("AAA") == Decimal(25.)

def test_portfolio_service_summary_calculation(trade_repo: TradeRepository):
    t1 = Trade(symbol="BBB", quantity=Decimal(10.), price=Decimal(1_000.), side="BUY")
    t2 = Trade(symbol="BBB", quantity=Decimal(30.), price=Decimal(1_000.), side="SELL")
    t3 = Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(1_000.), side="SELL")
    for trade in [t1, t2, t3]:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_summary() == {"AAA": {"position": Decimal(-15), "notional": Decimal(-15_000)}, 
                                "BBB": {"position": Decimal(-20), "notional": Decimal(-20_000)}}