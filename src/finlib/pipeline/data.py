"""Trades and market data fetching and storing"""

from datetime import datetime

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
    if first_ts is None or last_ts is None:
        log.error("Empty trade repository")
        raise RuntimeError("No trades in trade repository")

    log.info(
        "Trades loaded from repo",
        num_trades=len(trades),
        num_symbols=len(symbols),
        first_date=first_ts.strftime("%d-%m-%Y"),
        last_date=last_ts.strftime("%d-%m-%Y"),
    )

    return trades, list(symbols), first_ts


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
    """ "Store market data in the OHLCV repository."""
    if df.shape[0] == 0:
        log.error("Empty market price dataframe")
        raise ValueError("Empty market data DataFrame")
    columns_map = {"close_time": "timestamp"}
    log.info("Storing market data", dataframe_shape=df.shape, size=f"{df.size:,.0f}")
    ohlcv_repo.add_intervals_batch(df, columns_map=columns_map)
    return
