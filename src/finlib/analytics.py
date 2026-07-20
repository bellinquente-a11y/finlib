from pathlib import Path
from decimal import Decimal
from finlib.context_managers import timer
from finlib.decorators import retry
from finlib.data import stream_ohlcv, OHLCVBar
from typing import Generator
from finlib import Trade
from operator import attrgetter
from itertools import groupby

@retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
def calculate_daily_vwap(path: Path, symbol: str, min_volume: int = 0) -> Decimal:
    """Calculate VWAP from CSV file. It assumes the file reports data for one day only."""

    with timer(f"VWAP for ticker {symbol}"):
        bars = (bar for bar in stream_ohlcv(path, min_volume) if bar.symbol==symbol)
        try:
            return calculate_vwap(bars)
        except ValueError:
            raise ValueError(f"Missing data for ticker {symbol}")

def calculate_vwap(bars: Generator[OHLCVBar, None, None]) -> Decimal:
    """VWAP calculation from bars generator"""
    numerator, total_volume = Decimal(0.), Decimal(0.)
    for bar in bars:
        numerator += bar.close*Decimal(bar.volume)
        total_volume += bar.volume
    if total_volume==Decimal(0):
        raise ValueError("Missing trading volume")
    else:
        return Decimal(numerator/total_volume)


def group_trades_by_symbol(trades: list[Trade]) -> dict[str, list[Trade]]:
    """Groups a list of trades by symbol"""
    if trades == []:
        raise ValueError
    for trade in trades:
        if not isinstance(trade, Trade):
            raise TypeError
    sorted_trades = sorted(trades, key=attrgetter("symbol"))
    return {symbol: list(group) 
            for symbol, group in groupby(sorted_trades, key=attrgetter("symbol"))}

def trade_summary(trades: list[Trade]) -> None:
    """"Prints a summary of a list of trades, aggregated by symbol"""
    trades_by_group = group_trades_by_symbol(trades)
    sorted_symbol = sorted(trades_by_group.keys())
    for symbol in sorted_symbol:
        symbol_trades = trades_by_group[symbol]
        quantity = sum([trade.quantity for trade in symbol_trades])
        notional = sum([trade.notional for trade in symbol_trades])
        print((f"{symbol}: {len(symbol_trades)} trades; quantity = {quantity:,.2f}; "
               f"notional = {notional:,.2f}"))
    return