from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from finlib.models import Trade


@runtime_checkable
class TradeRepository(Protocol):
    def add(self, trade: Trade) -> None: ...
    def get_all(self) -> list[Trade]: ...
    def get_by_symbol(self, symbol: str) -> list[Trade]: ...
    def get_extreme_timestamps(self, 
                               symbol: str | None = None) \
                                -> tuple[datetime | None, datetime | None]: ...
    def get_all_symbols(self) -> set[str]: ...

class InMemoryTradeRepository:
    def __init__(self) -> None:
        self._trades: list[Trade] = []

    def add(self, trade: Trade) -> None:
        self._trades.append(trade)

    def get_all(self) -> list[Trade]:
        return list(self._trades)

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        return [*filter(lambda t: t.symbol==symbol, self._trades)]

    def get_extreme_timestamps(self, 
                               symbol: str | None = None) \
                                -> tuple[datetime | None, datetime | None]:
        trades: Iterator[Trade] = (t for t in self._trades) 
        if symbol is not None:
            trades = filter(lambda t: t.symbol==symbol, trades)
        return _get_extreme_timestamps(trades)

    def get_all_symbols(self) -> set[str]:
        symbols = set()
        for t in self._trades:
            symbols |= {t.symbol}
        return symbols


class FileTradeRepository:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self._symbols: set[str] = set()

    def add(self, trade: Trade) -> None:
        with self._filepath.open("a") as f:
            f.write(trade.model_dump_json() + "\n")
        self._symbols |= {trade.symbol}
    
    def get_all(self) -> list[Trade]:
        if not self._filepath.exists():
            return []
        with self._filepath.open() as f:
            return [Trade.model_validate_json(line) for line in f if line.strip()]
    
    def get_by_symbol(self, symbol: str) -> list[Trade]:
        with self._filepath.open() as f:
            all_trades = (Trade.model_validate_json(line) for line in f if line.strip())
            return [*filter(lambda t: t.symbol==symbol, all_trades)]    

    def get_extreme_timestamps(self, 
                               symbol: str | None = None) \
                                -> tuple[datetime | None, datetime | None]:
        with self._filepath.open() as f:
            trades: Iterator[Trade] = (Trade.model_validate_json(line) 
                                       for line in f if line.strip())
            if symbol is not None:
                trades = filter(lambda t: t.symbol==symbol, trades)
            return _get_extreme_timestamps(trades)

    def get_all_symbols(self) -> set[str]:
        symbols = set()
        with self._filepath.open() as f:
            for line in f:
                if line.strip():
                    symbols |= {Trade.model_validate_json(line).symbol}
        return symbols

def _get_extreme_timestamps(trades: Iterator[Trade]) -> tuple[datetime | None, datetime | None]:
    min_ts, max_ts = None, None
    for t in trades:
        if min_ts is None or max_ts is None:
            min_ts, max_ts = t.timestamp, t.timestamp
        else:
            min_ts = min(min_ts, t.timestamp)
            max_ts = max(max_ts, t.timestamp)
    return min_ts, max_ts


class PortfolioService:
    def __init__(self, trade_repo: TradeRepository):
        self._trade_repo = trade_repo

    def record_trade(self, trade: Trade) -> None:
        self._trade_repo.add(trade)

    def get_notional(self, symbol: str) -> Decimal:
        trades = self._trade_repo.get_by_symbol(symbol)
        return Decimal(sum(t.notional for t in trades))

    def get_position(self, symbol: str) -> Decimal:
        trades = self._trade_repo.get_by_symbol(symbol)
        return Decimal(sum(t.lot_size() for t in trades))

    def get_summary(self) -> dict[str, dict[str, Decimal]]:
        symbols = sorted(list(set(t.symbol for t in self._trade_repo.get_all())))
        return {
            symbol: {"position": self.get_position(symbol),
                     "notional": self.get_notional(symbol)
                    } 
                for symbol in symbols
            }