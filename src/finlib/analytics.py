from pathlib import Path
from decimal import Decimal
from finlib.utils import timer, retry
from finlib.data import stream_ohlcv, OHLCVBar
from typing import Generator

@retry(max_attempts=3, delay=1.0, exceptions=(ValueError,))
def calculate_daily_vwap(path: Path, symbol: str, min_volume: int = 0) -> Decimal:
    """Calculate VWAP from CSV file"""

    with timer(f"VWAP for ticker {symbol}"):
        bars = (bar for bar in stream_ohlcv(path, min_volume) if bar.symbol==symbol)
        try:
            return calculate_vwap(bars)
        except ValueError:
            raise ValueError(f"Missing data for ticker {symbol}")

def calculate_vwap(bars: Generator[OHLCVBar, None, None]) -> Decimal:
    numerator, total_volume = Decimal(0.), Decimal(0.)
    for bar in bars:
        numerator += bar.close*Decimal(bar.volume)
        total_volume += bar.volume
    if total_volume==Decimal(0):
        raise ValueError("Missing trading volume")
    else:
        return Decimal(numerator/total_volume)
