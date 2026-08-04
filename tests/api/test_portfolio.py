from collections.abc import Generator, Hashable
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, TypeAdapter

from finlib.api.apps import app
from finlib.api.deps import get_market_data_repo, get_trade_repo
from finlib.config import Settings, get_settings
from finlib.models import Trade
from finlib.ohlcv_repo import InMemoryOHLCVRepository, OHLCVInterval
from finlib.pipeline.analytics import compute_portfolio_performance_metrics
from finlib.portfolio import Portfolio
from finlib.trade_repo import InMemoryTradeRepository

TEST_KEY = "test-key"

# Mirrors the response_model of the /positions and /pnl routes so tests compare
# against the exact JSON the endpoint emits (Decimals serialized as strings).
_response_adapter: TypeAdapter[dict[Hashable, dict[Hashable, Any]]] = TypeAdapter(
    dict[Hashable, dict[Hashable, Any]]
)


def serialize_like_endpoint(df: pd.DataFrame) -> dict[Hashable, dict[Hashable, Any]]:
    serialized = _response_adapter.dump_python(df.to_dict("index"), mode="json")
    return cast(dict[Hashable, dict[Hashable, Any]], serialized)


@pytest.fixture
def repo() -> InMemoryTradeRepository:
    return InMemoryTradeRepository()


@pytest.fixture
def market_data_repo(sample_trades: list[Trade]) -> InMemoryOHLCVRepository:
    """OHLCV repo with a close price for every traded symbol at/after the first trade."""
    repo = InMemoryOHLCVRepository()
    symbols = {trade.symbol for trade in sample_trades}
    timestamps = [datetime(2025, 2, 3), datetime(2026, 1, 1), datetime(2026, 8, 1)]
    for symbol in symbols:
        for i, timestamp in enumerate(timestamps):
            price = Decimal(10 + i)
            repo.add_interval(
                OHLCVInterval(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=Decimal(1_000),
                )
            )
    return repo


@pytest.fixture
def client(
    repo: InMemoryTradeRepository, market_data_repo: InMemoryOHLCVRepository
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_trade_repo] = lambda: repo
    app.dependency_overrides[get_market_data_repo] = lambda: market_data_repo
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=SecretStr(TEST_KEY))
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_add_trade_ok(sample_trades: list[Trade], client: TestClient) -> None:
    trade = sample_trades[0]
    resp = client.post(
        "/trades", json=trade.model_dump(mode="json"), headers={"X-API-KEY": TEST_KEY}
    )
    assert resp.status_code == 201
    assert resp.json() == trade.model_dump(mode="json")


def test_trades_ok(sample_trades: list[Trade], client: TestClient) -> None:
    for trade in sample_trades:
        _ = client.post(
            "/trades", json=trade.model_dump(mode="json"), headers={"X-API-KEY": TEST_KEY}
        )
    resp = client.get("/trades", headers={"X-API-KEY": TEST_KEY})
    assert resp.json() == [trade.model_dump(mode="json") for trade in sample_trades]


def test_missing_key(sample_trades: list[Trade], client: TestClient) -> None:
    trade = sample_trades[0]
    resp = client.post("/trades", json=trade.model_dump(mode="json"))
    assert resp.status_code == 401


def test_invalid_key(sample_trades: list[Trade], client: TestClient) -> None:
    trade = sample_trades[0]
    resp = client.post("/trades", json=trade.model_dump(mode="json"), headers={"X-API-KEY": "ABC"})
    assert resp.status_code == 403


def test_invalid_trade(client: TestClient) -> None:
    resp = client.post("/trades", json={"price": -1}, headers={"X-API-KEY": TEST_KEY})
    assert resp.status_code == 422


def test_portfolio_ok(sample_trades: list[Trade], client: TestClient) -> None:
    for trade in sample_trades:
        _ = client.post(
            "/trades", json=trade.model_dump(mode="json"), headers={"X-API-KEY": TEST_KEY}
        )
    resp = client.get("/positions", headers={"X-API-KEY": TEST_KEY})

    assert resp.status_code == 200
    expected = Portfolio(name="portfolio", trades=sample_trades).historic_position()
    assert resp.json() == serialize_like_endpoint(expected)


def test_pnl_ok(
    sample_trades: list[Trade],
    client: TestClient,
    repo: InMemoryTradeRepository,
    market_data_repo: InMemoryOHLCVRepository,
) -> None:
    for trade in sample_trades:
        _ = client.post(
            "/trades", json=trade.model_dump(mode="json"), headers={"X-API-KEY": TEST_KEY}
        )
    resp = client.get("/pnl", headers={"X-API-KEY": TEST_KEY})

    assert resp.status_code == 200
    expected_pnl, _, _ = compute_portfolio_performance_metrics(repo, market_data_repo)
    assert resp.json() == serialize_like_endpoint(expected_pnl)
