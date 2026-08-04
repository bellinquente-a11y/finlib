import sqlite3
from dataclasses import dataclass, fields
from datetime import datetime
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


class InMemoryOHLCVRepository:
    def __init__(self) -> None:
        self._data: list[OHLCVInterval] = []
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]

    def add_interval(self, data: OHLCVInterval) -> None:
        self._data.append(data)

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

    def _get_last_timestamps(self) -> dict[str, datetime]:
        res: dict[str, datetime] = {}
        for row in self._data:
            if row.symbol not in res:
                res[row.symbol] = row.timestamp
            else:
                res[row.symbol] = max(res[row.symbol], row.timestamp)
        return res


class FileOHLCVRepository:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        first_row = ",".join(self._fieldnames) + "\n"
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
            f.write(data.to_string() + "\n")

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
            for i, row in enumerate(f):
                if i == 0:
                    continue
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

    def _get_last_timestamps(self) -> dict[str, datetime]:
        res: dict[str, datetime] = {}
        with self._filepath.open() as f:
            _ = f.readline()
            for row in f:
                row_data = OHLCVInterval.from_string(row)
                if row_data.symbol not in res:
                    res[row_data.symbol] = row_data.timestamp
                else:
                    res[row_data.symbol] = max(row_data.timestamp, res[row_data.symbol])
        return res


class SQLiteOHLCVRepository:
    def __init__(self, dbpath: Path) -> None:
        self._dbpath = str(dbpath)
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        if not dbpath.exists():
            query = """
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
            with sqlite3.connect(self._dbpath) as conn:
                cur = conn.cursor()
                cur.execute(query)

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

    def _get_last_timestamps(self) -> dict[str, datetime]:
        query = "SELECT symbol, MAX(timestamp) FROM ohlcv GROUP BY symbol"
        with sqlite3.connect(self._dbpath) as conn:
            cur = conn.cursor()
            rows = cur.execute(query).fetchall()
        return {symbol: datetime.fromisoformat(ts) for symbol, ts in rows}


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
