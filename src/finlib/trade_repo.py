import sqlite3
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, Protocol, cast, runtime_checkable

from finlib.models import Trade


@runtime_checkable
class TradeRepository(Protocol):
    def add(self, trade: Trade) -> None: ...
    def get_all(self) -> list[Trade]: ...
    def get_by_symbol(self, symbol: str) -> list[Trade]: ...
    def get_extreme_timestamps(
        self, symbol: str | None = None
    ) -> tuple[datetime | None, datetime | None]: ...
    def get_all_symbols(self) -> set[str]: ...


class InMemoryTradeRepository:
    def __init__(self) -> None:
        self._trades: list[Trade] = []

    def add(self, trade: Trade) -> None:
        self._trades.append(trade)

    def get_all(self) -> list[Trade]:
        return list(self._trades)

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        return [*filter(lambda t: t.symbol == symbol, self._trades)]

    def get_extreme_timestamps(
        self, symbol: str | None = None
    ) -> tuple[datetime | None, datetime | None]:
        trades: Iterator[Trade] = (t for t in self._trades)
        if symbol is not None:
            trades = filter(lambda t: t.symbol == symbol, trades)
        return _get_extreme_timestamps(trades)

    def get_all_symbols(self) -> set[str]:
        symbols = set()
        for t in self._trades:
            symbols |= {t.symbol}
        return symbols


class FileTradeRepository:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath

    def add(self, trade: Trade) -> None:
        with self._filepath.open("a") as f:
            f.write(trade.model_dump_json() + "\n")

    def get_all(self) -> list[Trade]:
        if not self._filepath.exists():
            return []
        with self._filepath.open() as f:
            return [Trade.model_validate_json(line) for line in f if line.strip()]

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        with self._filepath.open() as f:
            all_trades = (Trade.model_validate_json(line) for line in f if line.strip())
            return [*filter(lambda t: t.symbol == symbol, all_trades)]

    def get_extreme_timestamps(
        self, symbol: str | None = None
    ) -> tuple[datetime | None, datetime | None]:
        with self._filepath.open() as f:
            trades: Iterator[Trade] = (
                Trade.model_validate_json(line) for line in f if line.strip()
            )
            if symbol is not None:
                trades = filter(lambda t: t.symbol == symbol, trades)
            return _get_extreme_timestamps(trades)

    def get_all_symbols(self) -> set[str]:
        symbols = set()
        with self._filepath.open() as f:
            for line in f:
                if line.strip():
                    symbols |= {Trade.model_validate_json(line).symbol}
        return symbols


class SQLiteTradeRepository:
    def __init__(self, dbpath: Path) -> None:
        self._dbpath = str(dbpath)
        if not dbpath.exists():
            query = """
                CREATE TABLE trades (
                    symbol      TEXT NOT NULL,
                    quantity    TEXT NOT NULL,
                    price       TEXT NOT NULL,
                    side        TEXT NOT NULL,
                    timestamp   TEXT NOT NULL
                );
            """
            with sqlite3.connect(self._dbpath) as conn:
                cur = conn.cursor()
                cur.execute(query)

    @classmethod
    def _Trade_to_row(cls, trade: Trade) -> tuple[str, ...]:
        return (
            trade.symbol,
            str(trade.quantity),
            str(trade.price),
            trade.side,
            trade.timestamp.isoformat(),
        )

    @classmethod
    def _row_to_Trade(cls, row: dict[str, str]) -> Trade:
        return Trade(
            symbol=row["symbol"],
            quantity=Decimal(row["quantity"]),
            price=Decimal(row["price"]),
            side=cast(Literal["BUY", "SELL"], row["side"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def add(self, trade: Trade) -> None:
        query = "INSERT INTO trades (symbol, quantity, price, side, timestamp) VALUES (?,?,?,?,?)"
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            cur.execute(query, SQLiteTradeRepository._Trade_to_row(trade))

    def get_all(self) -> list[Trade]:
        with sqlite3.connect(self._dbpath) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("SELECT * FROM trades")
            return [SQLiteTradeRepository._row_to_Trade(row) for row in rows]

    def get_by_symbol(self, symbol: str) -> list[Trade]:
        with sqlite3.connect(self._dbpath) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute("SELECT * FROM trades WHERE symbol = ?", (symbol,))
            return [SQLiteTradeRepository._row_to_Trade(row) for row in rows]

    def get_extreme_timestamps(
        self, symbol: str | None = None
    ) -> tuple[datetime | None, datetime | None]:
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            query_min = "SELECT MIN(timestamp) FROM trades"
            query_max = "SELECT MAX(timestamp) FROM trades"
            if symbol is None:
                row_min = cur.execute(query_min).fetchone()
                row_max = cur.execute(query_max).fetchone()
            else:
                query_min = f"{query_min} WHERE symbol = ?"
                query_max = f"{query_max} WHERE symbol = ?"
                row_min = cur.execute(query_min, (symbol,)).fetchone()
                row_max = cur.execute(query_max, (symbol,)).fetchone()
        return datetime.fromisoformat(row_min[0]), datetime.fromisoformat(row_max[0])

    def get_all_symbols(self) -> set[str]:
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            res = cur.execute("SELECT symbol FROM trades GROUP BY symbol").fetchall()
        return set([x[0] for x in res])


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
            symbol: {"position": self.get_position(symbol), "notional": self.get_notional(symbol)}
            for symbol in symbols
        }
