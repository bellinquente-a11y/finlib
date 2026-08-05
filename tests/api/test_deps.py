from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from finlib.api import deps
from finlib.config import Settings
from finlib.ohlcv_repo import SQLiteOHLCVRepository
from finlib.trade_repo import SQLiteTradeRepository

TEST_KEY = "test-key"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path, api_key=SecretStr(TEST_KEY))


def test_get_trade_repo() -> None:
    repo = deps.get_trade_repo()
    assert isinstance(repo, SQLiteTradeRepository)
    assert repo._dbpath == str(deps.TRADES_DB_PATH)


def test_get_market_data_repo() -> None:
    repo = deps.get_market_data_repo()
    assert isinstance(repo, SQLiteOHLCVRepository)
    assert repo._dbpath == str(deps.MKT_DATA_DB_PATH)


def test_require_key_missing(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc_info:
        deps.require_key(settings=settings, x_api_key=None)
    assert exc_info.value.status_code == 401


def test_require_key_empty(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc_info:
        deps.require_key(settings=settings, x_api_key="")
    assert exc_info.value.status_code == 401


def test_require_key_invalid(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc_info:
        deps.require_key(settings=settings, x_api_key="wrong-key")
    assert exc_info.value.status_code == 403
