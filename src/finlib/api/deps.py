import secrets
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from finlib.config import Settings, get_settings
from finlib.trade_repo import SQLiteTradeRepository, TradeRepository

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_trade_repo() -> TradeRepository:
    return SQLiteTradeRepository(get_settings().data_dir / "trades.db")


def require_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: str | None = Depends(api_key_header),
) -> None:
    if not x_api_key:
        raise HTTPException(401, "API key is required")
    if not secrets.compare_digest(x_api_key, settings.api_key.get_secret_value()):
        raise HTTPException(403, "Invalid API key")
    return
