from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

import pandas as pd
import pytest

from finlib import Portfolio, Trade
from finlib.ohlcv_repo import (
    FileOHLCVRepository,
    InMemoryOHLCVRepository,
    OHLCVInterval,
    OHLCVRepository,
)
from finlib.trade_repo import FileTradeRepository, InMemoryTradeRepository, TradeRepository


@pytest.fixture
def sample_trades() -> list[Trade]:
    def create_trade(
        symbol: str,
        price: float,
        quantity: float,
        side: Literal["BUY", "SELL"],
        timestamp: tuple[int, int, int, int, int, int],
    ) -> Trade:
        return Trade(
            symbol=symbol,
            price=Decimal(price),
            quantity=Decimal(quantity),
            side=side,
            timestamp=datetime(*timestamp),
        )

    return [
        create_trade("BBB", 10, 100, "BUY", (2026, 2, 3, 12, 3, 45)),
        create_trade("AAA", 10, 50, "BUY", (2026, 1, 3, 12, 3, 45)),
        create_trade("AAA", 10, 10, "SELL", (2025, 2, 3, 12, 3, 45)),
        create_trade("CCC", 10.2, 70.45, "SELL", (2026, 2, 17, 12, 3, 45)),
        create_trade("BBB", 10, 80, "BUY", (2026, 6, 3, 12, 3, 45)),
        create_trade("AAA", 10, 20, "SELL", (2026, 7, 3, 12, 3, 45)),
    ]


@pytest.fixture
def sample_portfolio(sample_trades: list[Trade]) -> Portfolio:
    return Portfolio(name="My portfolio", trades=sample_trades)


@pytest.fixture
def sample_historic_portfolio(sample_trades: list[Trade]) -> Portfolio:
    _TIMESTAMP1 = datetime(2026, 2, 1, 3, 0, 0)
    _TIMESTAMP2 = datetime(2026, 2, 4, 2, 9, 0)
    _TIMESTAMP3 = datetime(2026, 2, 6, 3, 5, 0)
    _TIMESTAMP4 = datetime(2026, 2, 8, 3, 44, 0)
    _TIMESTAMP5 = datetime(2026, 2, 11, 3, 33, 0)
    _TRADE1 = Trade(
        symbol="BHP", quantity=Decimal(100), price=Decimal(45.0), side="BUY", timestamp=_TIMESTAMP1
    )
    _TRADE2 = Trade(
        symbol="BHP", quantity=Decimal(40), price=Decimal(48.0), side="SELL", timestamp=_TIMESTAMP3
    )
    _TRADE3 = Trade(
        symbol="BHP", quantity=Decimal(90), price=Decimal(52.0), side="SELL", timestamp=_TIMESTAMP5
    )
    _TRADE4 = Trade(
        symbol="AAA", quantity=Decimal(100), price=Decimal(12.0), side="SELL", timestamp=_TIMESTAMP2
    )
    _TRADE5 = Trade(
        symbol="AAA", quantity=Decimal(100), price=Decimal(19.0), side="SELL", timestamp=_TIMESTAMP4
    )
    return Portfolio(name="My portfolio", trades=[_TRADE3, _TRADE4, _TRADE1, _TRADE5, _TRADE2])


@pytest.fixture
def sample_market_making_prices() -> pd.DataFrame:
    _MM_TIMESTAMPS = [
        datetime(2026, 2, 1, 2, 0, 0),
        datetime(2026, 2, 2, 2, 0, 0),
        datetime(2026, 2, 6, 3, 5, 0),
        datetime(2026, 2, 12, 2, 0, 0),
    ]
    return pd.DataFrame(
        data=[
            [Decimal(11.3), Decimal(50.4)],
            [Decimal(12.3), Decimal(51.4)],
            [Decimal(13.3), Decimal(52.4)],
            [Decimal(14.3), Decimal(53.4)],
        ],
        columns=["AAA", "BHP"],
        index=_MM_TIMESTAMPS,
    )


@pytest.fixture(params=("memory", "jsonl"))
def tmp_trade_repo(request: pytest.FixtureRequest, tmp_path: Path) -> TradeRepository:
    if request.param == "memory":
        repo: FileTradeRepository | InMemoryTradeRepository = InMemoryTradeRepository()
    elif request.param == "jsonl":
        repo = FileTradeRepository(tmp_path / "trade_repo.jsonl")
    trades = [
        Trade(
            symbol="BBB",
            quantity=Decimal(10.0),
            price=Decimal(1_000.0),
            side="BUY",
            timestamp=datetime(2026, 2, 1, 13, 4, 56),
        ),
        Trade(
            symbol="BBB",
            quantity=Decimal(30.0),
            price=Decimal(1_000.0),
            side="SELL",
            timestamp=datetime(2026, 3, 1, 13, 4, 56),
        ),
        Trade(
            symbol="AAA",
            quantity=Decimal(15.0),
            price=Decimal(1_000.0),
            side="SELL",
            timestamp=datetime(2026, 4, 1, 13, 4, 56),
        ),
    ]
    for trade in trades:
        repo.add(trade)
    return repo


@pytest.fixture(params=("memory", "csv"))
def tmp_ohlcv_repo(request: pytest.FixtureRequest, tmp_path: Path) -> OHLCVRepository:
    if request.param == "memory":
        repo: FileOHLCVRepository | InMemoryOHLCVRepository = InMemoryOHLCVRepository()
    elif request.param == "csv":
        repo = FileOHLCVRepository(tmp_path / "ohlcv_repo.csv")

    _int1 = OHLCVInterval(
        symbol="SYM1",
        timestamp=datetime(2026, 6, 1, 1, 2, 3),
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(100.9),
        volume=Decimal(1_342),
    )
    _int2 = OHLCVInterval(
        symbol="SYM1",
        timestamp=datetime(2026, 6, 2, 1, 2, 3),
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(100.9),
        volume=Decimal(1_342),
    )
    _int3 = OHLCVInterval(
        symbol="SYM1",
        timestamp=datetime(2026, 6, 3, 1, 2, 3),
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(100.9),
        volume=Decimal(1_342),
    )
    _int4 = OHLCVInterval(
        symbol="SYM2",
        timestamp=datetime(2026, 6, 4, 1, 2, 3),
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(100.9),
        volume=Decimal(1_342),
    )

    for i in [_int1, _int2, _int3, _int4]:
        repo.add_interval(i)

    return repo
