import sqlite3
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

import pandas as pd
import structlog

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class OHLCVInterval:
    """Dataclass representing an OHLCV bar"""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def to_string(self) -> str:
        fields_names = [f.name for f in fields(self)]
        fields_types = [f.type for f in fields(self)]
        output = []
        for fname, ftype in zip(fields_names, fields_types, strict=True):
            field = getattr(self, fname)
            if ftype is str:
                output.append(field)
            elif ftype is datetime:
                output.append(field.isoformat())
            elif ftype is Decimal:
                output.append(f"{field}")
            else:
                raise NotImplementedError
        return ",".join(output)

    @classmethod
    def from_string(cls, string: str) -> "OHLCVInterval":
        fields_names = [f.name for f in fields(cls)]
        fields_types = [f.type for f in fields(cls)]
        data_list = string.strip().split(",")
        data: dict[str, Any] = {k: v for k, v in zip(fields_names, data_list, strict=True)}
        for fname, ftype in zip(fields_names, fields_types, strict=True):
            if ftype is str:
                continue
            if ftype is datetime:
                data[fname] = datetime.fromisoformat(data[fname])
            elif ftype is Decimal:
                data[fname] = Decimal(data[fname])
            else:
                raise NotImplementedError
        return cls(**data)


class OHLCVRepository(Protocol):
    def add_interval(self, data: OHLCVInterval) -> None: ...
    def add_intervals_batch(
        self, data: pd.DataFrame, columns_map: dict[str, str] | None = None
    ) -> None: ...
    def get_data(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> pd.DataFrame: ...
    def last_updated(self, symbol: str) -> datetime | None: ...
    def last_timestamp(self, symbol: str) -> datetime | None: ...


class InMemoryOHLCVRepository:
    def __init__(self) -> None:
        self._data: list[OHLCVInterval] = []
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        self._last_updated: dict[str, datetime] = {}

    def add_interval(self, data: OHLCVInterval) -> None:
        self._data.append(data)
        self._update_last_updated(data.symbol)

    def add_intervals_batch(
        self, df: pd.DataFrame, columns_map: dict[str, str] | None = None
    ) -> None:
        if columns_map is not None:
            df = _reformat_dataframe_for_batch_input(df, self._fieldnames, columns_map)
        if not (set(df.columns) <= set(self._fieldnames)):
            raise ValueError

        last_timestamp = self._get_last_timestamps()
        symbols = set(df["symbol"].to_list())
        count = 0
        for symbol in symbols:
            query = "symbol==@symbol"
            if symbol in last_timestamp:
                last_timestamp_symbol = last_timestamp[symbol]  # noqa: F841 # this is a pandas-query false positive
                query = f"{query} and timestamp>@last_timestamp_symbol"
            for row in df.query(query).itertuples():
                self.add_interval(OHLCVInterval(**{k: getattr(row, k) for k in self._fieldnames}))
                count += 1
        log.info("Added rows to trade repo", count=count)

    def get_data(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> pd.DataFrame:
        filtered_data = filter(lambda b: b.symbol == symbol, self._data)
        if start is not None:
            filtered_data = filter(lambda b: b.timestamp >= start, filtered_data)
        if end is not None:
            filtered_data = filter(lambda b: b.timestamp <= end, filtered_data)
        return pd.DataFrame(
            [[getattr(i, f) for f in self._fieldnames] for i in filtered_data],
            columns=self._fieldnames,
        ).sort_values(["timestamp", "symbol"])

    def last_timestamp(self, symbol: str) -> datetime | None:
        ts_dict = self._get_last_timestamps()
        if symbol in ts_dict:
            return ts_dict[symbol]
        return None

    def _get_last_timestamps(self) -> dict[str, datetime]:
        res: dict[str, datetime] = {}
        for row in self._data:
            if row.symbol not in res:
                res[row.symbol] = row.timestamp
            else:
                res[row.symbol] = max(res[row.symbol], row.timestamp)
        return res

    def _update_last_updated(self, symbol: str) -> None:
        self._last_updated[symbol] = datetime.now(tz=UTC)

    def last_updated(self, symbol: str) -> datetime | None:
        if symbol in self._last_updated:
            return self._last_updated[symbol]
        return None


class FileOHLCVRepository:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        first_row = f"{','.join(self._fieldnames)},last_updated\n"
        if not self._filepath.exists():
            with self._filepath.open("w") as f:
                f.write(first_row)
        else:
            with self._filepath.open() as f:
                row = f.readline()
                if row and row != first_row:
                    raise FileExistsError

    def add_interval(self, data: OHLCVInterval) -> None:
        with self._filepath.open("a") as f:
            f.write(f"{data.to_string()},{datetime.now(tz=UTC).isoformat()}\n")

    def add_intervals_batch(
        self, df: pd.DataFrame, columns_map: dict[str, str] | None = None
    ) -> None:
        if columns_map is not None:
            df = _reformat_dataframe_for_batch_input(df, self._fieldnames, columns_map)
        if not (set(df.columns) <= set(self._fieldnames)):
            raise ValueError

        symbols = set(df["symbol"].to_list())
        last_timestamp = self._get_last_timestamps()
        count = 0
        for symbol in symbols:
            query = "symbol==@symbol"
            if symbol in last_timestamp:
                last_timestamp_symbol = last_timestamp[symbol]
                query = f"{query} and timestamp>@last_timestamp_symbol"
                log.info(
                    "adding intervals",
                    symbol=symbol,
                    last_timestamp=last_timestamp_symbol.astimezone().strftime("%d-%m-%Y %H:%M:%S"),
                )
            else:
                log.info("adding intervals", symbol=symbol)

            for row in df.query(query).itertuples():
                ohlcv_int = OHLCVInterval(**{k: getattr(row, k) for k in self._fieldnames})
                self.add_interval(ohlcv_int)
                count += 1

        log.info("New rows added to trade repo", count=count)

    def get_data(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> pd.DataFrame:
        data = []
        with self._filepath.open() as f:
            for i, row_with_last_updated in enumerate(f):
                if i == 0:
                    continue
                row = ",".join(row_with_last_updated.split(",")[:-1])
                row_data = OHLCVInterval.from_string(row)
                if row_data.symbol == symbol:
                    if (start is not None) and (end is not None):
                        if row_data.timestamp < start or row_data.timestamp > end:
                            continue
                    elif (start is not None) and (end is None):
                        if row_data.timestamp < start:
                            continue
                    elif (start is None) and (end is not None) and row_data.timestamp > end:
                        continue
                    data.append([getattr(row_data, f) for f in self._fieldnames])
        return pd.DataFrame(data, columns=self._fieldnames).sort_values(by="timestamp")

    def last_timestamp(self, symbol: str) -> datetime | None:
        ts_dict = self._get_last_timestamps()
        if symbol in ts_dict:
            return ts_dict[symbol]
        return None

    def _get_last_timestamps(self) -> dict[str, datetime]:
        res: dict[str, datetime] = {}
        with self._filepath.open() as f:
            _ = f.readline()
            for row_with_last_updated in f:
                row = ",".join(row_with_last_updated.split(",")[:-1])
                row_data = OHLCVInterval.from_string(row)
                if row_data.symbol not in res:
                    res[row_data.symbol] = row_data.timestamp
                else:
                    res[row_data.symbol] = max(row_data.timestamp, res[row_data.symbol])
        return res

    def last_updated(self, symbol: str) -> datetime | None:
        res = None
        with self._filepath.open() as f:
            _ = f.readline()
            for row_with_last_updated in f:
                row = ",".join(row_with_last_updated.split(",")[:-1])
                row_data = OHLCVInterval.from_string(row)
                last_updated = datetime.fromisoformat(row_with_last_updated.split(",")[-1].strip())
                if row_data.symbol == symbol:
                    res = last_updated if res is None else max(last_updated, res)
        return res


class SQLiteOHLCVRepository:
    def __init__(self, dbpath: Path) -> None:
        self._dbpath = str(dbpath)
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        if not dbpath.exists():
            with sqlite3.connect(self._dbpath) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE ohlcv (
                        symbol      TEXT NOT NULL,
                        timestamp   TEXT NOT NULL,
                        open        TEXT NOT NULL,
                        high        TEXT NOT NULL,
                        low         TEXT NOT NULL,
                        close       TEXT NOT NULL,
                        volume      TEXT NOT NULL
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE last_updated (
                        symbol          TEXT NOT NULL UNIQUE,
                        timestamp       TEXT NOT NULL
                    );
                    """
                )

    @classmethod
    def _OHLCVInterval_to_row(cls, interval: OHLCVInterval) -> tuple[str, ...]:
        return (
            interval.symbol,
            interval.timestamp.isoformat(),
            str(interval.open),
            str(interval.high),
            str(interval.low),
            str(interval.close),
            str(interval.volume),
        )

    @classmethod
    def _row_to_OHLCVInterval(cls, row: dict[str, str]) -> OHLCVInterval:
        return OHLCVInterval(
            symbol=row["symbol"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            open=Decimal(row["open"]),
            high=Decimal(row["high"]),
            low=Decimal(row["low"]),
            close=Decimal(row["close"]),
            volume=Decimal(row["volume"]),
        )

    def add_interval(self, data: OHLCVInterval) -> None:
        query = (
            "INSERT INTO ohlcv (symbol, timestamp, open, high, low, close, volume) "
            "VALUES (?,?,?,?,?,?,?)"
        )
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            cur.execute(query, SQLiteOHLCVRepository._OHLCVInterval_to_row(data))
        self._update_last_updated(data.symbol)

    def add_intervals_batch(
        self, df: pd.DataFrame, columns_map: dict[str, str] | None = None
    ) -> None:
        if columns_map is not None:
            df = _reformat_dataframe_for_batch_input(df, self._fieldnames, columns_map)
        if not (set(df.columns) <= set(self._fieldnames)):
            raise ValueError

        symbols = set(df["symbol"].to_list())
        last_timestamp = self._get_last_timestamps()
        count = 0
        for symbol in symbols:
            query = "symbol==@symbol"
            if symbol in last_timestamp:
                last_timestamp_symbol = last_timestamp[symbol]  # noqa: F841 # pandas-query false positive
                query = f"{query} and timestamp>@last_timestamp_symbol"
            for row in df.query(query).itertuples():
                ohlcv_int = OHLCVInterval(**{k: getattr(row, k) for k in self._fieldnames})
                self.add_interval(ohlcv_int)
                count += 1

        log.info("New rows added to ohlcv repo", count=count)

    def get_data(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> pd.DataFrame:
        query = "SELECT * FROM ohlcv WHERE symbol = ?"
        params: list[str] = [symbol]
        if start is not None:
            query = f"{query} AND timestamp >= ?"
            params.append(start.isoformat())
        if end is not None:
            query = f"{query} AND timestamp <= ?"
            params.append(end.isoformat())
        with sqlite3.connect(self._dbpath) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            rows = cur.execute(query, params)
            intervals = [SQLiteOHLCVRepository._row_to_OHLCVInterval(row) for row in rows]
        return pd.DataFrame(
            [[getattr(i, f) for f in self._fieldnames] for i in intervals],
            columns=self._fieldnames,
        ).sort_values(by="timestamp")

    def last_timestamp(self, symbol: str) -> datetime | None:
        query = "SELECT timestamp FROM ohlcv WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            res = cur.execute(query, (symbol,)).fetchone()
        if res is None:
            return None
        return datetime.fromisoformat(res[0])

    def _get_last_timestamps(self) -> dict[str, datetime]:
        query = "SELECT symbol, MAX(timestamp) FROM ohlcv GROUP BY symbol"
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            rows = cur.execute(query).fetchall()
        return {symbol: datetime.fromisoformat(ts) for symbol, ts in rows}

    def _update_last_updated(self, symbol: str) -> None:
        query = (
            "INSERT INTO last_updated (symbol, timestamp) "
            "VALUES (?,?)"
            "ON CONFLICT (symbol)"
            "DO UPDATE SET timestamp = EXCLUDED.timestamp"
        )
        with sqlite3.connect(self._dbpath) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, (symbol, datetime.now(tz=UTC).isoformat()))

    def last_updated(self, symbol: str) -> datetime | None:
        query = "SELECT timestamp FROM last_updated WHERE symbol = ? "
        with sqlite3.connect(self._dbpath) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            res = cur.execute(query, (symbol,)).fetchone()
        if res is None:
            return None
        return datetime.fromisoformat(res[0])


def _reformat_dataframe_for_batch_input(
    df: pd.DataFrame, repo_field_names: list[str], columns_map: dict[str, str]
) -> pd.DataFrame:
    """Rename columns of the input dataframe to match repo expectations"""
    # Validate column_map
    if not set(columns_map.keys()) <= set(df.columns):
        raise ValueError
    if not set(columns_map.values()) <= set(repo_field_names):
        raise ValueError
    # Rename columns and keep only the required ones
    return df.rename(columns=columns_map)[repo_field_names]
