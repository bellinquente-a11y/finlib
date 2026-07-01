from typing import Protocol
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, fields
from decimal import Decimal
from pathlib import Path
from typing import Any

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
        for fname, ftype in zip(fields_names, fields_types):
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
        data: dict[str, Any] = {k:v for k,v in zip(fields_names, data_list)}
        for fname, ftype in zip(fields_names, fields_types):
            if ftype is str:
                continue
            elif ftype is datetime:
                data[fname] = datetime.fromisoformat(data[fname])
            elif ftype is Decimal:
                data[fname] = Decimal(data[fname])
            else:
                raise NotImplementedError
        return cls(**data)


class OHLCVRepo(Protocol):
    def add_interval(self, data: OHLCVInterval) -> None: ...
    def add_intervals_batch(self, data: pd.DataFrame) -> None: ...
    def get_data(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pd.DataFrame: ...

class InMemoryOHLCVRepo:
    def __init__(self) -> None:
        self._data: list[OHLCVInterval] = []
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]

    def add_interval(self, data: OHLCVInterval) -> None:
        self._data.append(data)

    def add_intervals_batch(self, data: pd.DataFrame) -> None:
        for row in data.itertuples():
            self.add_interval(
                OHLCVInterval(**{k:getattr(row,k) for k in  self._fieldnames})
            )

    def get_data(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pd.DataFrame:
        filtered_data = filter(lambda b: b.symbol==symbol, self._data)
        if start is not None:
            filtered_data = filter(lambda b: b.timestamp>=start, filtered_data)
        if end is not None:
            filtered_data = filter(lambda b: b.timestamp<=end, filtered_data)
        return pd.DataFrame([[getattr(i, f) for f in self._fieldnames] for i in filtered_data], columns=self._fieldnames)

class FileOHLCVRepo:
    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self._fieldnames = [f.name for f in fields(OHLCVInterval)]
        first_row = ",".join(self._fieldnames) + "\n"
        if not self._filepath.exists():
            with self._filepath.open("w") as f:
                f.write(first_row)
        else:
            with self._filepath.open() as f:
                for row in f:
                    break
                if row != first_row:
                    raise FileExistsError

    def add_interval(self, data: OHLCVInterval) -> None:
        with self._filepath.open("a") as f:
            f.write(data.to_string() + "\n")

    def add_intervals_batch(self, data: pd.DataFrame) -> None:
        for row in data.itertuples():
            ohlcv_int = OHLCVInterval(**{k:getattr(row,k) for k in self._fieldnames})
            self.add_interval(ohlcv_int)

    def get_data(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pd.DataFrame:
        data = []
        with self._filepath.open() as f:
            for i, row in enumerate(f):
                if i==0:
                    continue
                row_data = OHLCVInterval.from_string(row)
                if row_data.symbol==symbol:
                    if (start is not None) and (end is not None):
                        if row_data.timestamp<start or row_data.timestamp>end:
                            continue
                    elif (start is not None) and (end is None):
                        if row_data.timestamp<start:
                            continue
                    elif (start is None) and (end is not None):
                        if row_data.timestamp>end:
                            continue
                    data.append([getattr(row_data,f) for f in self._fieldnames])
        return pd.DataFrame(data, columns=self._fieldnames)