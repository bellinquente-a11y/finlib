"""Trades and market data fetching and storing"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast

import pandas as pd
import structlog

from finlib.async_fetch import binance_interval, fetch_binance
from finlib.models import Trade
from finlib.ohlcv_repo import OHLCVRepository
from finlib.trade_repo import TradeRepository

log = structlog.getLogger(__name__)


def fetch_trades(trade_repo: TradeRepository) -> tuple[list[Trade], list[str], datetime]:
    """Load trades from in file repository and return list of symbols and first trade timestamp."""
    trades = trade_repo.get_all()
    if trades == []:
        log.error("Empty trade repository")
        raise RuntimeError("No trades in trade repository")

    symbols = trade_repo.get_all_symbols()
    first_ts, last_ts = trade_repo.get_extreme_timestamps()

    log.info(
        "Trades loaded from repo",
        num_trades=len(trades),
        num_symbols=len(symbols),
        first_date="n/a" if first_ts is None else first_ts.strftime("%d-%m-%Y"),
        last_date="n/a" if last_ts is None else last_ts.strftime("%d-%m-%Y"),
    )

    return trades, list(symbols), (first_ts if first_ts else datetime.now())


async def fetch_market_data(
    symbols: list[str], interval: binance_interval, start: datetime
) -> pd.DataFrame:
    """Fetch OHLCV market data from Binance for the given symbols.

    Args:
        symbols: Trading pair symbols to fetch (e.g. ``["BTCUSDT", "ETHUSDT"]``).
        interval: Candlestick interval (e.g. ``"1h"``, ``"1d"``).
        start: Earliest timestamp to include in the returned data.

    Returns:
        DataFrame with one row per symbol/interval combination.
    """
    log.info("Fetching market data", symbols=symbols)
    return await fetch_binance(symbols, interval, start)


def store_market_data(ohlcv_repo: OHLCVRepository, df: pd.DataFrame) -> None:
    """Store market data in the OHLCV repository."""
    if df.shape[0] == 0:
        log.error("Empty market price dataframe")
        raise ValueError("Empty market data DataFrame")
    columns_map = {"close_time": "timestamp"}
    log.info("Storing market data", dataframe_shape=df.shape, size=f"{df.size:,.0f}")
    ohlcv_repo.add_intervals_batch(df, columns_map=columns_map)
    return


def update_market_data_repo(
    ohlcv_repo: OHLCVRepository,
    symbols: list[str],
    interval: binance_interval,
    start: datetime,
    max_update_freq: timedelta,
) -> None:
    """Update the OHLCV repo by fetching remotely if the data
    was last updated since more tha 'update_freq'."""
    symbols_to_update = []
    for symbol in symbols:
        last_updated = ohlcv_repo.last_updated(symbol)
        if last_updated is None:
            symbols_to_update.append(symbol)
        else:
            if last_updated < datetime.now(tz=UTC) - max_update_freq:
                symbols_to_update.append(symbol)
                last_timestamp = cast(datetime, ohlcv_repo.last_timestamp(symbol))
                start = min(start, last_timestamp)
    if symbols_to_update == []:
        return
    df = asyncio.run(fetch_market_data(symbols_to_update, interval, start))
    store_market_data(ohlcv_repo, df)
    return
