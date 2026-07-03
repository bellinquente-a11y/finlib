"""Trades and market data fetching and storing"""

from finlib import InFileTradeRepository, FileOHLCVRepo, Trade, TradeRepository
from finlib.async_fetch import fetch_binance, binance_interval
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

log = logging.getLogger(__name__)

def fetch_trades(trade_repo_path: Path) -> tuple[list[Trade], list[str], datetime]:
    """Load trades from in file repository and return list of symbols and first trade timestamp."""
    log.info(f"Loading trades from {trade_repo_path}")
    trade_repo = InFileTradeRepository(trade_repo_path)
    trades = trade_repo.get_all()
    if trades == []:
        raise RuntimeError(f"No trades in file {trade_repo_path}")

    symbols = set()
    first_dt = datetime(2100,1,1,tzinfo=timezone.utc)
    for trade in trades:
        symbols |= {trade.symbol}
        first_dt = min(first_dt, trade.timestamp)

    return trades, list(symbols), first_dt


async def fetch_market_data(symbols: list[str], interval: binance_interval, start: datetime) -> pd.DataFrame:
    """Fetch market data."""
    log.info(f"Fetching {interval} market data for symbols: {", ".join(symbols)}")
    return await fetch_binance(symbols, interval, start)


def store_market_data(df: pd.DataFrame, repo_path: Path) -> None:
    """"Store market data in the OHLCV repository."""
    log.info(f"Storing market data in {repo_path}")
    if df.shape[0]==0:
        raise ValueError("Empty market data DataFrame")
    repo = FileOHLCVRepo(repo_path)
    columns_map = {"close_time": "timestamp"}
    repo.add_intervals_batch(df, columns_map=columns_map)
    return