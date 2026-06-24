import asyncio
import aiohttp
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import logging
from typing import Literal, TypeAlias, get_args, Any

binance_interval: TypeAlias = Literal["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

log = logging.getLogger(__name__)

BINANCE_URL = "https://api.binance.com/api/v3/klines"

EARLY_DATE_TIMESTAMP = int(datetime(2015,1,1).timestamp()*1000)

BINANCE_DATA_ROWS = ["open_time", "open", "high", "low", "close", "volume", "close_time", 
                     "quote_asset_volume", "number_of_trades", "taker_buy_quote_asset_volume", "ignore"] 

class BinanceDataRow(BaseModel):
    """Pydantic class to capture a Binance data row"""
    open_time: int = Field(..., gt=EARLY_DATE_TIMESTAMP)
    open: str = Field(..., min_length=1)
    high: str = Field(..., min_length=1)
    low: str = Field(..., min_length=1)
    close: str = Field(..., min_length=1)
    volume: str = Field(..., min_length=1)
    close_time: int = Field(..., gt=EARLY_DATE_TIMESTAMP)
    quote_asset_volume: str = Field(..., min_length=1)
    number_of_trades: int = Field(..., gt=0)
    taker_buy_quote_asset_volume: str = Field(..., min_length=1)
    ignore: str

async def fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval) -> Any:
    """Coroutine to fetch one data for one syumbol from Binance."""
    async with session.get(BINANCE_URL, params={"symbol": symbol, "interval": interval, "limit": 1}) as resp:
        resp.raise_for_status()
        return await resp.json()

async def validated_fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval) -> BinanceDataRow | None:
    """Coroutine to fetch one data for one syumbol from Binance. Validated with Pydantic."""
    try:
        data = await fetch_binance_one_symbol_one_row(session, symbol, interval)
        return BinanceDataRow(**{k: v for k, v in zip(BINANCE_DATA_ROWS, data[0])})
    except (ValidationError, aiohttp.client_exceptions.ClientResponseError) as e:
        log.warning(f"Bad response from {BINANCE_URL} for symbol {symbol}: {e}")
        return None
    except KeyError as e:
        log.warning(f"Missing data from {BINANCE_URL} for symbol {symbol}: {e}")
        return None

async def fetch_binance_data(symbols: list[str], interval: binance_interval) -> list[BinanceDataRow | None]:
    """Coroutine to fetch multiple symbols from Binance"""
    if not isinstance(symbols, list):
        raise TypeError
    if interval not in get_args(binance_interval):
        raise ValueError
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[validated_fetch_binance_one_symbol_one_row(session, symbol, interval) for symbol in symbols])
    return result

def stream_binance_data(symbols: list[str], interval: binance_interval) -> list[BinanceDataRow | None]:
    return asyncio.run(fetch_binance_data(symbols, interval))
