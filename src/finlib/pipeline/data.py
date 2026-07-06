"""Trades and market data fetching and storing"""

from finlib import OHLCVRepo, Trade, TradeRepository
from finlib.async_fetch import fetch_binance, binance_interval
import logging
import pandas as pd
from datetime import datetime

log = logging.getLogger(__name__)

def fetch_trades(trade_repo: TradeRepository) -> tuple[list[Trade], list[str], datetime]:
    """Load trades from in file repository and return list of symbols and first trade timestamp."""
    log.info("Loading trades from the trade repository")
    trades = trade_repo.get_all()
    if trades == []:
        raise RuntimeError("No trades in trade repository")

    symbols = trade_repo.get_all_symbols()
    first_ts, _ = trade_repo.get_extreme_timestamps()
    if first_ts is None:
        raise ValueError
        
    log.info(f"Trades loaded    = {len(trades)}")
    log.info(f"Symbols          = {", ".join([s for s in symbols])}")
    log.info(f"First time stamp = {first_ts!r}")

    return trades, list(symbols), first_ts


async def fetch_market_data(symbols: list[str], interval: binance_interval, start: datetime) -> pd.DataFrame:
    """Fetch OHLCV market data from Binance for the given symbols.

    Args:
        symbols: Trading pair symbols to fetch (e.g. ``["BTCUSDT", "ETHUSDT"]``).
        interval: Candlestick interval (e.g. ``"1h"``, ``"1d"``).
        start: Earliest timestamp to include in the returned data.

    Returns:
        DataFrame with one row per symbol/interval combination.
    """
    log.info(f"Fetching {interval} market data for symbols: {", ".join(symbols)} from {start!s}")
    return await fetch_binance(symbols, interval, start)


def store_market_data(ohlcv_repo: OHLCVRepo, df: pd.DataFrame) -> None:
    """"Store market data in the OHLCV repository."""
    log.info("Storing market data in OHLCV repository")
    if df.shape[0]==0:
        raise ValueError("Empty market data DataFrame")
    columns_map = {"close_time": "timestamp"}
    ohlcv_repo.add_intervals_batch(df, columns_map=columns_map)
    return