import asyncio
import aiohttp
from pydantic import BaseModel, Field, ValidationError
import structlog
from typing import Literal, TypeAlias, get_args, Any
from finlib.config import settings
from finlib.decorators import async_retry

log = structlog.get_logger(__name__)

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
    taker_buy_base_asset_volume: str = Field(..., min_length=1)
    taker_buy_quote_asset_volume: str = Field(..., min_length=1)
    ignore: str

async def fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval) -> Any:
    """Coroutine to fetch one data for one symbol from Binance."""
    log.info("Async fetching Binance data", interval=interval, symbol=symbol)
    async with asyncio.timeout(settings.fetch_timeout_seconds):
        async with session.get(settings.binance.url, params={"symbol": symbol, "interval": interval, "limit": 1}) as resp:
            resp.raise_for_status()
            return await resp.json()

@async_retry(max_retry=settings.binance.max_retry, delay=1.)
async def validated_fetch_binance_one_symbol_one_row(session: aiohttp.ClientSession, symbol: str, interval: binance_interval, semaphore: asyncio.Semaphore) -> BinanceDataRow | None:
    """Coroutine to fetch one data for one symbol from Binance. Validated with Pydantic."""
    async with semaphore:
        try:
            data = await fetch_binance_one_symbol_one_row(session, symbol, interval)
            return BinanceDataRow(**{k: v for k, v in zip(settings.binance.columns, data[0])})
        except (ValidationError, aiohttp.client_exceptions.ClientResponseError) as e:
            log.warning("Bad response", url=settings.binance.url, symbol=symbol, exc=e)
            return None
        except KeyError as e:
            log.warning("Missing data", url=settings.binance.url, symbol=symbol, exc=e)
            return None

async def fetch_binance_data(symbols: list[str], interval: binance_interval) -> dict[str, BinanceDataRow | None]:
    """Coroutine to fetch multiple symbols from Binance"""
    if not isinstance(symbols, list):
        raise TypeError
    if interval not in get_args(binance_interval):
        raise ValueError(f"Binance quantisation interval {interval} not available")

    semaphore = asyncio.Semaphore(settings.binance.max_number_concurrent_calls)    
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[validated_fetch_binance_one_symbol_one_row(session, symbol, interval, semaphore) for symbol in symbols])
    return {s:r for s,r in zip(symbols, result)}

def stream_binance_data(symbols: list[str], interval: binance_interval) -> dict[str, BinanceDataRow | None]:
    return asyncio.run(fetch_binance_data(symbols, interval))
