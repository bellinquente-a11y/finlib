""""Trades and market data analysis module"""

from finlib import historic_analytics
import pandas as pd
from finlib.ohlcv_repo import FileOHLCVRepo
import logging

log = logging.getLogger(__name__)

INTERVALS_PER_YEAR_DAILY = 252

def compute_market_summary(repo: FileOHLCVRepo, symbols: list[str], window: int = 24) -> pd.DataFrame:
    """
    Pull OHLCV data from the repo, resample to daily, and compute
    rolling statistics for each symbol.

    Returns a DataFrame with columns:
      symbol, timestamp, open, high, low, close, volume,
      returns, rolling_vol, rolling_sharpe
    """
    result = pd.DataFrame()
    for symbol in symbols:
        df = repo.get_data(symbol)
        log.debug("df from market repo shape %s: [%i, %i]", symbol, df.shape[0], df.shape[1])
        if df.shape[0]==0:
            log.warning(f"Missing market data for {symbol}")
        
        else:
            df = historic_analytics.resample_dataframe(df.drop(columns="symbol").sort_values(by="timestamp"), freq="D")
            log.debug("df daily resampling shape %s: [%i, %i]", symbol, df.shape[0], df.shape[1])
            df = historic_analytics.add_rolling_stats(df, INTERVALS_PER_YEAR_DAILY, window)
            assert (df["rolling_sharpe"].iloc[:window].isna().all()) and (df["rolling_sharpe"].iloc[window:].notna().all())
            result = pd.concat((result, df.dropna(axis=0, how="any").assign(symbol=symbol).astype({"symbol": "category"})), axis=0)

    return result.sort_values(by="timestamp")
        