import asyncio
import aiohttp
from pydantic import BaseModel, Field, ValidationError
import logging
from typing import Literal, TypeAlias, get_args, Any
from finlib.config import settings

log = logging.getLogger(__name__)

binance_interval: TypeAlias = Literal["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

class BinanceDataRow(BaseModel):
    """Pydantic class to capture a Binance data row"""
    open_time: int = Field(..., gt=int(settings.binance.first_date.timestamp()*1000))
    open: str = Field(..., min_length=1)
    high: str = Field(..., min_length=1)
    low: str = Field(..., min_length=1)
    close: str = Field(..., min_length=1)
    volume: str = Field(..., min_length=1)
    close_time: int = Field(..., gt=int(settings.binance.first_date.timestamp()*1000))
    quote_asset_volume: str = Field(..., min_length=1)
    number_of_trades: int = Field(..., gt=0)
    taker_buy_quote_asset_volume: str = Field(..., min_length=1)
    ignore: str

async def fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval) -> Any:
    """Coroutine to fetch one data for one syumbol from Binance."""
    log.info(f"Fetching {interval} data for {symbol}")
    async with session.get(settings.binance.url, params={"symbol": symbol, "interval": interval, "limit": 1}) as resp:
        resp.raise_for_status()
        return await resp.json()

async def validated_fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval) -> BinanceDataRow | None:
    """Coroutine to fetch one data for one syumbol from Binance. Validated with Pydantic."""
    try:
        data = await fetch_binance_one_symbol_one_row(session, symbol, interval)
        return BinanceDataRow(**{k: v for k, v in zip(settings.binance.columns, data[0])})
    except (ValidationError, aiohttp.client_exceptions.ClientResponseError) as e:
        log.warning(f"Bad response from {settings.binance.url} for symbol {symbol}: {e}")
        return None
    except KeyError as e:
        log.warning(f"Missing data from {settings.binance.url} for symbol {symbol}: {e}")
        return None

async def fetch_binance_data(symbols: list[str], interval: binance_interval) -> dict[str, BinanceDataRow | None]:
    """Coroutine to fetch multiple symbols from Binance"""
    if not isinstance(symbols, list):
        raise TypeError
    if interval not in get_args(binance_interval):
        raise ValueError(f"Binance quantisation interval {interval} not available")
    timeout = aiohttp.ClientTimeout(settings.fetch_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        result = await asyncio.gather(*[validated_fetch_binance_one_symbol_one_row(session, symbol, interval) for symbol in symbols])
    return {s:r for s,r in zip(symbols, result)}

def stream_binance_data(symbols: list[str], interval: binance_interval) -> dict[str, BinanceDataRow | None]:
    return asyncio.run(fetch_binance_data(symbols, interval))
