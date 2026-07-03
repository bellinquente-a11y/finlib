import asyncio
import aiohttp
from pydantic import BaseModel, Field, ValidationError
import structlog
from typing import Literal, TypeAlias, get_args, Any
from finlib.config import get_settings
from finlib.decorators import async_retry
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal
from dateutil.parser import parse

log = structlog.get_logger(__name__)

binance_interval: TypeAlias = Literal["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

class BinanceDataRow(BaseModel):
    """Pydantic class to capture a Binance data row"""
    open_time: datetime
    open: Decimal = Field(..., gt=0)
    high: Decimal = Field(..., gt=0)
    low: Decimal = Field(..., gt=0)
    close: Decimal = Field(..., gt=0)
    volume: Decimal = Field(..., gt=0)
    close_time: datetime
    quote_asset_volume: Decimal = Field(..., gt=0)
    number_of_trades: int = Field(..., gt=0)
    taker_buy_base_asset_volume: Decimal = Field(..., gt=0)
    taker_buy_quote_asset_volume: Decimal = Field(..., gt=0)
    ignore: str

async def _fetch_binance_one_symbol(session: aiohttp.ClientSession, symbol: str, interval: binance_interval, limit: int) -> Any:
    """Coroutine to fetch one data for one symbol from Binance."""
    settings = get_settings()
    log.info("Async fetching Binance data", interval=interval, symbol=symbol, limit=limit)
    async with asyncio.timeout(settings.fetch_timeout_seconds):
        async with session.get(settings.binance.url, params={"symbol": symbol, "interval": interval, "limit": limit}) as resp:
            resp.raise_for_status()
            return await resp.json()

@async_retry(max_retry=3, delay=1., exceptions=(aiohttp.ClientError, asyncio.TimeoutError, aiohttp.client_exceptions.ClientResponseError))
async def _fetch_binance_one_symbol_with_retry(session: aiohttp.ClientSession, symbol: str, interval: binance_interval, limit: int) -> Any:
    return await _fetch_binance_one_symbol(session, symbol, interval, limit)


async def _validated_fetch_binance_one_symbol(session: aiohttp.ClientSession, symbol: str, interval: binance_interval, limit: int, semaphore: asyncio.Semaphore) -> list[BinanceDataRow] | None:
    """Coroutine to fetch one data for one symbol from Binance. Validated with Pydantic."""
    settings = get_settings()
    async with semaphore:
        try:
            data = await _fetch_binance_one_symbol_with_retry(session, symbol, interval, limit)
            result = []
            invalid_rows_count=0
            for row in data:
                try:
                    result.append(BinanceDataRow(**{k: v for k, v in zip(settings.binance.columns, row)}))
                except ValidationError:
                    invalid_rows_count+=0
            if invalid_rows_count>0:
                log.warning("Invalid Binance data", symbol=symbol, invalid_rows_count=invalid_rows_count)
            if result == []:
                log.warning("Unable to fetch Binance data", url=settings.binance.url, symbol=symbol)
            return result
        except RuntimeError as e:
            log.warning("Unable to fetch Binance data", url=settings.binance.url, symbol=symbol, exc=e)
            return None

async def _fetch_binance_raw_data(symbols: list[str], interval: binance_interval, limit: int) -> dict[str, list[BinanceDataRow] | None]:
    """Coroutine to fetch multiple symbols from Binance"""
    if not isinstance(symbols, list):
        raise TypeError
    if interval not in get_args(binance_interval):
        raise ValueError(f"Binance quantisation interval {interval} not available")
    settings = get_settings()
    semaphore = asyncio.Semaphore(settings.binance.max_number_concurrent_calls)    
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[_validated_fetch_binance_one_symbol(session, symbol, interval, limit, semaphore) for symbol in symbols])
    return {s:r for s,r in zip(symbols, result)}

def _convert_binance_data_to_DataFrame(data: dict[str, list[BinanceDataRow] | None]) -> pd.DataFrame:
    result = pd.DataFrame()
    columns = BinanceDataRow.model_fields
    for symbol, symbol_data in data.items():
        if symbol_data is not None:
            df = (
                pd.DataFrame([row.model_dump() for row in symbol_data])
                .assign(symbol=symbol)
                [["symbol", *columns]]
                .drop(columns=["ignore"])
                .astype({"symbol": "category"})
            )
            result = pd.concat((result, df), axis=0)
    return result.sort_values(["open_time", "symbol"])

async def fetch_binance(symbols: list[str], interval: binance_interval, start: datetime | str) -> pd.DataFrame:
    match interval[-1]:
        case "s":
            deltat = timedelta(seconds=float(interval[:-1]))
        case "m":
            deltat = timedelta(minutes=float(interval[:-1]))
        case "h":
            deltat = timedelta(hours=float(interval[:-1]))
        case "d":
            deltat = timedelta(days=float(interval[:-1]))
        case _:
            raise NotImplementedError


    start = parse(start) if isinstance(start, str) else start
    limit = max(int((datetime.now() - start) / deltat),1)

    data = await _fetch_binance_raw_data(symbols, interval, limit)
    return _convert_binance_data_to_DataFrame(data)
