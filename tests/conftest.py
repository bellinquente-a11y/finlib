import pytest
from finlib import Trade, Portfolio
from decimal import Decimal
from datetime import datetime
import pandas as pd
from finlib.trade_repo import TradeRepository, InFileTradeRepository, InMemoryTradeRepository

@pytest.fixture
def sample_trades() -> list[Trade]:
    def create_trade(symbol, price, quantity, side, timestamp):
        return Trade(symbol=symbol, price=Decimal(price), quantity=Decimal(quantity), side=side, timestamp=datetime(*timestamp))
    return [
        create_trade("BBB", 10,  100, "BUY", [2026,2,3,12,3,45]),
        create_trade("AAA", 10, 50, "BUY", [2026,1,3,12,3,45]),
        create_trade("AAA", 10, 10, "SELL", [2025,2,3,12,3,45]),
        create_trade("CCC", 10.2, 70.45,  "SELL", [2026,2,17,12,3,45]),
        create_trade("BBB", 10, 80, "BUY", [2026,6,3,12,3,45]),
        create_trade("AAA", 10, 20, "SELL", [2026,7,3,12,3,45]),
    ]

@pytest.fixture
def sample_portfolio(sample_trades):
    return Portfolio(name="My portfolio", trades=sample_trades)

@pytest.fixture
def sample_historic_portfolio(sample_trades):
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
    return Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])

@pytest.fixture
def sample_market_making_prices():
    _MM_TIMESTAMPS = [
        datetime(2026,2,1,2,0,0),
        datetime(2026,2,2,2,0,0),
        datetime(2026,2,6,3,5,0),
        datetime(2026,2,12,2,0,0),
    ]
    return pd.DataFrame(
        data = [
            [Decimal(11.3), Decimal(50.4)],
            [Decimal(12.3), Decimal(51.4)],
            [Decimal(13.3), Decimal(52.4)],
            [Decimal(14.3), Decimal(53.4)],
        ],
        columns = ["AAA", "BHP"],
        index = _MM_TIMESTAMPS
    )    

@pytest.fixture(params = ("memory", "jsonl"))
def tmp_trade_repo(request, tmp_path) -> TradeRepository:
    if request.param=="memory":
        repo = InMemoryTradeRepository()
    elif request.param=="jsonl":
        repo = InFileTradeRepository(tmp_path / "trade_repo.jsonl")
    trades =[
        Trade(symbol="BBB", quantity=Decimal(10.), price=Decimal(1_000.), side="BUY", timestamp=datetime(2026,2,1,13,4,56)),
        Trade(symbol="BBB", quantity=Decimal(30.), price=Decimal(1_000.), side="SELL", timestamp=datetime(2026,3,1,13,4,56)),
        Trade(symbol="AAA", quantity=Decimal(15.), price=Decimal(1_000.), side="SELL", timestamp=datetime(2026,4,1,13,4,56)),
    ]
    for trade in trades:
        repo.add(trade)
    return repo