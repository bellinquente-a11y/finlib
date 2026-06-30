from finlib.config import get_settings
import requests
import pandas as pd
from finlib.async_fetch import binance_interval
from typing import get_args
from typing import Any

def _fetch_binance_data_per_product(symbol: str, interval: binance_interval, limit: int) -> Any:
    """Fetch historic data from Binance"""
    if interval not in get_args(binance_interval):
        raise ValueError
    if limit <=0:
        raise ValueError
    settings = get_settings()
    resp = requests.get(settings.binance.url, 
                        params={
                            "symbol": symbol, 
                            "interval": interval, 
                            "limit": str(limit),
                            },
                        timeout = settings.fetch_timeout_seconds
                        )
    return resp.json()

def _format_binance_output(data: list[list[int|str]]) -> pd.DataFrame:
    """Format the raw Binance data into a DataFrame"""
    settings = get_settings()
    if len(data) == 0:
        raise ValueError
    if not all(len(row)==len(settings.binance.columns) for row in data):
        raise ValueError
    for i, col in enumerate(settings.binance.columns):
        expected_type = settings.binance.columns_type[col]
        if not all(isinstance(x[i],expected_type) for x in data):
            raise ValueError(f"Binance data column {i}: not all data is {expected_type}")
    df = pd.DataFrame(data=data, columns=settings.binance.columns)
    return (
        df
        .drop(columns=["ignore"])
        .assign(
            open_time=lambda d: pd.to_datetime(d["open_time"], unit="ms", utc=True),
            close_time=lambda d: pd.to_datetime(d["close_time"], unit="ms", utc=True),
        )
        .astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
                "quote_asset_volume": float,
                "number_of_trades": int,
                "taker_buy_base_asset_volume": float,
                "taker_buy_quote_asset_volume": float,
            }
        )
    )

def load_binance_data_per_product(symbol: str, interval: binance_interval, limit: int) -> pd.DataFrame:
    """Load historic Binance data per product"""
    return _format_binance_output(_fetch_binance_data_per_product(symbol, interval, limit))
