""""Trades and market data analysis module"""

import logging
from datetime import datetime

import pandas as pd

from finlib import historic_analytics
from finlib.ohlcv_repo import OHLCVRepository
from finlib.portfolio import Portfolio
from finlib.trade_repo import TradeRepository

log = logging.getLogger(__name__)

INTERVALS_PER_YEAR_DAILY = 252

def compute_market_summary(ohlcv_repo: OHLCVRepository, 
                           symbols: list[str], window: int = 24) -> pd.DataFrame:
    """
    Pull OHLCV data from the repo, resample to daily, and compute
    rolling statistics for each symbol.

    Returns a DataFrame with columns:
      symbol, timestamp, open, high, low, close, volume,
      returns, rolling_vol, rolling_sharpe
    """
    result = pd.DataFrame()
    for symbol in symbols:
        df = ohlcv_repo.get_data(symbol)
        log.debug("df from market repo shape %s: [%i, %i]", symbol, df.shape[0], df.shape[1])
        if df.shape[0]==0:
            log.warning(f"Missing market data for {symbol}")
        
        else:
            df = historic_analytics.resample_dataframe(df
                                                      .drop(columns="symbol")
                                                      .sort_values(by="timestamp"), 
                                                      freq="D")
            log.debug("df daily resampling shape %s: [%i, %i]", symbol, df.shape[0], df.shape[1])
            df = historic_analytics.add_rolling_stats(df, INTERVALS_PER_YEAR_DAILY, window)
            result = (pd.concat((result, 
                                 (df
                                  .dropna(axis=0, how="any")
                                  .assign(symbol=symbol)
                                  .astype({"symbol": "category"})
                                  )
                                 ), 
                                 axis=0)
                      )

    if result.shape[0]>0:
        return result.sort_values(by="timestamp")
    return result

def get_market_price(ohlcv_repo: OHLCVRepository, 
                     symbols: list[str], first_ts: datetime) -> pd.DataFrame:
    """
    Returns a DataFrame of close prices from the OHLCV repo. 
        - index: timestamps starting from first_ts
        - columns: symbols
    """
    result = pd.DataFrame()
    for symbol in symbols:
        df = ohlcv_repo.get_data(symbol, first_ts)
        log.debug("df from market repo shape %s: [%i, %i]", symbol, df.shape[0], df.shape[1])
        if df.shape[0]==0:
            log.warning(f"Missing market data for {symbol}")
        
        else:
            df = (
                df
                [["timestamp", "close"]]
                .set_index("timestamp")
                .sort_index()
                .rename(columns={"close": symbol})
            )
            result = pd.concat((result, df), axis=1)

    if result.shape[0]>0:
        return result.sort_values(by="timestamp")
    return result


def compute_portfolio_performance_metrics(trade_repo: TradeRepository, ohlcv_repo: OHLCVRepository
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns 3 DataFrames (cumulative Pnl, market value, cost basis) associated to a trade 
    repository by marking to market with prices from the OHLCV repo.
    Dataframes output:
        - index: timestampe
        - columns: traded symbols
    """
    trades = trade_repo.get_all()
    symbols = trade_repo.get_all_symbols()
    first_ts, _ = trade_repo.get_extreme_timestamps()
    if first_ts is None:
        raise ValueError
    portfolio = Portfolio(name="My portfolio", trades=trades)
    prices = get_market_price(ohlcv_repo, list(symbols), first_ts)
    if set(symbols) != set(prices.columns.to_list()):
        raise RuntimeError("Missing sumbols in price dataframe")
    return portfolio.historic_pnl(prices), \
           portfolio.historic_market_value(prices), \
           portfolio.historic_cost_basis() 