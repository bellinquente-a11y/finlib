import pandas as pd


def resample_binance_data(df: pd.DataFrame, freq: str = "d") -> pd.DataFrame:
    columns = list(df.columns)
    return (
        df
        .set_index("close_time")
        .sort_index()
        .resample(freq, label="right")
        .agg(            
            open_time=("open_time", "first"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            quote_asset_volume=("quote_asset_volume", "sum"),
            number_of_trades=("number_of_trades", "sum"),
            taker_buy_base_asset_volume=("taker_buy_base_asset_volume", "sum"),
            taker_buy_quote_asset_volume=("taker_buy_quote_asset_volume", "sum"),
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
            rolling_vol= lambda d: (intervals_per_year**0.5)*d["returns"].rolling(window=window).std(),
            rolling_sharpe= lambda d: (intervals_per_year**0.5)*d["returns"].rolling(window=window).mean()/d["returns"].rolling(window=window).std(),
        )
    )