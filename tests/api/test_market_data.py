from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from finlib.api.apps import app
from finlib.config import Settings, get_settings

TEST_KEY = "test-key"

MOCK_FETCH_BINANCE_OUTPUT = pd.DataFrame(
    [
        {
            "symbol": "BTCUSDT",
            "open_time": datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            "close_time": datetime(2024, 1, 1, 0, 59, 59, tzinfo=UTC),
            "open": Decimal("42000.00"),
            "high": Decimal("42500.00"),
            "low": Decimal("41800.00"),
            "close": Decimal("42350.00"),
            "volume": Decimal("1234.56"),
            "something_else": "something",
        },
        {
            "symbol": "ETHUSDT",
            "open_time": datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            "close_time": datetime(2024, 1, 1, 0, 59, 59, tzinfo=UTC),
            "open": Decimal("2200.00"),
            "high": Decimal("2250.00"),
            "low": Decimal("2180.00"),
            "close": Decimal("2240.00"),
            "volume": Decimal("9876.54"),
            "something_else": "something",
        },
    ]
)

EXPECTED_JSON_OUTPUT = [
    {
        "symbol": "BTCUSDT",
        "open_time": "2024-01-01T00:00:00Z",
        "close_time": "2024-01-01T00:59:59Z",
        "open": "42000.00",
        "high": "42500.00",
        "low": "41800.00",
        "close": "42350.00",
        "volume": "1234.56",
    },
    {
        "symbol": "ETHUSDT",
        "open_time": "2024-01-01T00:00:00Z",
        "close_time": "2024-01-01T00:59:59Z",
        "open": "2200.00",
        "high": "2250.00",
        "low": "2180.00",
        "close": "2240.00",
        "volume": "9876.54",
    },
]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=SecretStr(TEST_KEY))
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_market_data_ok(client: TestClient) -> None:
    with patch(
        "finlib.api.routes.market_data.fetch_binance",
        new=AsyncMock(return_value=MOCK_FETCH_BINANCE_OUTPUT),
    ):
        resp = client.get(
            "/market-data",
            params={
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "interval": "1h",
                "start": datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            },
            headers={"X-API-KEY": TEST_KEY},
        )
        assert resp.status_code == 200
        assert resp.json() == EXPECTED_JSON_OUTPUT
