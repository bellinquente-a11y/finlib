from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from finlib.api.apps import app
from finlib.api.deps import get_trade_repo
from finlib.config import Settings, get_settings
from finlib.models import Trade
from finlib.trade_repo import InMemoryTradeRepository

TEST_KEY = "test-key"


@pytest.fixture
def repo() -> InMemoryTradeRepository:
    return InMemoryTradeRepository()


@pytest.fixture
def client(repo: InMemoryTradeRepository) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_trade_repo] = lambda: repo
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
