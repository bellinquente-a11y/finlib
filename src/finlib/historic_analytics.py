import pandas as pd

def resample_dataframe(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    columns = list(df.columns)
    return (
        df
        .set_index("timestamp")
        .sort_index()
        .resample(freq, label="right")
        .agg(            
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .dropna()
        .reset_index()
        [columns]
    )

def add_rolling_stats(df: pd.DataFrame, intervals_per_year: int, window: int) -> pd.DataFrame:
    return(
        df
        .assign(
            returns=lambda d: d["close"].pct_change()
        )
        .assign(
            rolling_vol= lambda d: (intervals_per_year**0.5)*(d["returns"]
                                                              .rolling(window=window)
                                                              .std()),
            rolling_sharpe= lambda d: (intervals_per_year**0.5)*(d["returns"]
                                                                 .rolling(window=window)
                                                                 .mean()) / 
                                                                 (d["returns"]
                                                                 .rolling(window=window)
                                                                 .std()),
        )
    )

def maximum_drawdown(returns: pd.Series) -> float:
    """Returns the maximum drawdown of a (cumulative) PnL series."""
    cum_pnl = (returns.astype(float) + 1.).cumprod()
    max_cum_pnl = cum_pnl.cummax()
    return min(cum_pnl/max_cum_pnl-1.)