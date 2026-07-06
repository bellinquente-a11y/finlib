from finlib.trade_repo import TradeRepository, PortfolioService, InMemoryTradeRepository, InFileTradeRepository
from finlib.models import Trade
from decimal import Decimal
import pytest
from datetime import datetime

_TIMESTAMP1 = datetime(2026,2,1,13,4,56)
_TIMESTAMP2 = datetime(2026,3,1,13,4,56)
_TIMESTAMP3 = datetime(2026,4,1,13,4,56)

_TRADES =[
    Trade(symbol="BBB", quantity=Decimal(10.), price=Decimal(1_000.), side="BUY", timestamp=_TIMESTAMP1),
    Trade(symbol="BBB", quantity=Decimal(30.), price=Decimal(1_000.), side="SELL", timestamp=_TIMESTAMP2),
    Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(1_000.), side="SELL", timestamp=_TIMESTAMP3),
]

@pytest.fixture(params = ("memory", "jsonl"))
def trade_repo(request, tmp_path) -> TradeRepository:
    if request.param=="memory":
        return InMemoryTradeRepository()
    elif request.param=="jsonl":
        return InFileTradeRepository(tmp_path / "trade_repo.jsonl")

def test_trade_repo_get_symbols(trade_repo: TradeRepository):
    for trade in _TRADES:
        trade_repo.add(trade)
    assert trade_repo.get_all_symbols() == {"AAA", "BBB"}    

def test_trade_repo_get_timestamp(trade_repo: TradeRepository):
    for trade in _TRADES:
        trade_repo.add(trade)
    assert trade_repo.get_extreme_timestamps() == (_TIMESTAMP1, _TIMESTAMP3)
    assert trade_repo.get_extreme_timestamps("AAA") == (_TIMESTAMP3, _TIMESTAMP3)
    assert trade_repo.get_extreme_timestamps("BBB") == (_TIMESTAMP1, _TIMESTAMP2)

def test_portfolio_service_position_calculation(trade_repo: TradeRepository):
    for trade in _TRADES:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_position("BBB") == Decimal(-20.)

def test_portfolio_service_summary_calculation(trade_repo: TradeRepository):
    for trade in _TRADES:
        trade_repo.add(trade)
    ps = PortfolioService(trade_repo)
    assert ps.get_summary() == {"AAA": {"position": Decimal(-15), "notional": Decimal(-15_000)}, 
                                "BBB": {"position": Decimal(-20), "notional": Decimal(-20_000)}}