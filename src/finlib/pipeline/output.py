"""Finlib output management module"""

import pandas as pd
from typing import Callable, Any

def print_market_summary(market_summary: pd.DataFrame, columns: list[str], formatters: dict[str, Callable[..., str]]) -> None:
    print(
        market_summary[columns]
        .dropna()
        .tail(10)
        .to_string(
            formatters=formatters
        )
    )
    return

def print_trading_summary(df: pd.DataFrame, format: str, axis_format: str) -> None:
    formatters = {k: format.format for k in df.columns.to_list()}
    print(
        df
        .set_axis(pd.DatetimeIndex(df.index).strftime(axis_format))
        .tail(1)
        .to_string(
            formatters=formatters
        )
    )
    return