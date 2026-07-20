"""Finlib output management module"""

import pandas as pd
from typing import Callable

def print_market_summary(market_summary: pd.DataFrame, 
                         columns: list[str], 
                         formatters: dict[str, Callable[..., str]]) -> None:
    """Print the last 10 rows of the market summary table to stdout.

    Args:
        market_summary: DataFrame produced by compute_market_summary.
        columns: Subset of columns to display.
        formatters: Per-column format callables passed to DataFrame.to_string.
    """
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
    """Print the most recent row of a per-symbol trading summary to stdout.

    Args:
        df: DataFrame with a DatetimeIndex and one column per symbol.
        format: Python format string applied to every numeric cell (e.g. ``"{:,.0f}"``).
        axis_format: strftime pattern used to label the index (e.g. ``"%Y-%m-%d %H:%M"``).
    """
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