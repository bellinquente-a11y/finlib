import csv
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Literal, cast
from finlib import Trade
from datetime import datetime

EXAMPLE_PATH = "~/data/simulated_financial_data.csv"

@dataclass(frozen=True)
class OHLCVBar:
    """Dataclass representing an OHLCV bar"""
    symbol: str
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __repr__(self) -> str:
        return f"OHLCVBar(symbol={self.symbol!r}, timestamp={self.timestamp!r}, open={self.open!r}, high={self.high!r}, low={self.low!r}, close={self.close!r}, volume={self.volume!r})"

def stream_ohlcv(path: Path, min_volume: int = 0) -> Generator[OHLCVBar, None, None]:
    """Stream OHLCV bars from a CSV file"""

    if not path.is_file():
        raise ValueError(f"Missing path {path!s}")

    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bar = OHLCVBar(
                symbol=row['symbol'],
                timestamp=row['timestamp'],
                open=Decimal(row['open']),
                high=Decimal(row['high']),
                low=Decimal(row['low']),
                close=Decimal(row['close']),
                volume=Decimal(row['volume'])
            )
            if bar.volume >= min_volume:
                yield bar

def stream_trades(path: Path, timestamp_format: str = '%Y-%m-%dT%H:%M:%S') -> Generator[Trade, None, None]:
    """Stream trades from a CSV file"""

    if not path.is_file():
        raise ValueError(f"Missing path {path!s}")

    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trade = Trade(
                symbol = row['symbol'],
                quantity=Decimal(row["volume"]),
                price=Decimal(row["price"]),
                side=cast(Literal['BUY', 'SELL'], row['side']),
                timestamp=datetime.strptime(row["timestamp"], timestamp_format)
            )
            yield trade