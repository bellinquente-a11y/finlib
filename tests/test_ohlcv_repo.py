import dataclasses
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from finlib.ohlcv_repo import (
    FileOHLCVRepository,
    InMemoryOHLCVRepository,
    OHLCVInterval,
    OHLCVRepository,
)

_int1 = OHLCVInterval(
    symbol="SYM1",
    timestamp=datetime(2026, 6, 1, 1, 2, 3),
    open=Decimal(101.2),
    high=Decimal(102.4),
    low=Decimal(100.8),
    close=Decimal(100.9),
    volume=Decimal(1_342),
)
_int2 = OHLCVInterval(
    symbol="SYM1",
    timestamp=datetime(2026, 6, 2, 1, 2, 3),
    open=Decimal(101.2),
    high=Decimal(102.4),
    low=Decimal(100.8),
    close=Decimal(100.9),
    volume=Decimal(1_342),
)
_int3 = OHLCVInterval(
    symbol="SYM1",
    timestamp=datetime(2026, 6, 3, 1, 2, 3),
    open=Decimal(101.2),
    high=Decimal(102.4),
    low=Decimal(100.8),
    close=Decimal(100.9),
    volume=Decimal(1_342),
)
_int4 = OHLCVInterval(
    symbol="SYM2",
    timestamp=datetime(2026, 6, 4, 1, 2, 3),
    open=Decimal(101.2),
    high=Decimal(102.4),
    low=Decimal(100.8),
    close=Decimal(100.9),
    volume=Decimal(1_342),
)


@pytest.fixture(params=["memory", "csv"])
def repo(request: pytest.FixtureRequest, tmp_path: Path) -> OHLCVRepository:
    if request.param == "memory":
        return InMemoryOHLCVRepository()
    return FileOHLCVRepository(tmp_path / "ohlcv_repo.csv")


def test_in_memory_repo_output(repo: OHLCVRepository) -> None:
    for i in [_int1, _int2, _int3, _int4]:
        repo.add_interval(i)
    df = repo.get_data("SYM1", datetime(2026, 6, 2, 0, 0, 0), datetime(2026, 6, 2, 23, 59, 59))
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    assert (
        (df == pd.DataFrame([[getattr(_int2, f) for f in fieldnames]], columns=fieldnames))
        .all()
        .all()
    )


def test_in_memory_repo_add_batch(repo: OHLCVRepository) -> None:
    _intervals = [_int1, _int2, _int3, _int4]
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    map = {"datetime": "timestamp", "open_price": "open"}
    inv_map = {v: k for k, v in map.items()}
    columns = [inv_map.get(f, f) for f in fieldnames]
    df = pd.DataFrame([[getattr(i, f) for f in fieldnames] for i in _intervals], columns=columns)
    repo.add_intervals_batch(df, map)
    df_out = repo.get_data("SYM1")
    assert (df_out == df.query('symbol == "SYM1"').rename(columns=map)).all().all()


def test_in_memory_repo_add_multiple_batches(repo: OHLCVRepository) -> None:
    _intervals1 = [_int1, _int2]
    _intervals2 = [_int3, _int4]
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    map = {"datetime": "timestamp", "open_price": "open"}
    inv_map = {v: k for k, v in map.items()}
    columns = [inv_map.get(f, f) for f in fieldnames]
    df1 = pd.DataFrame([[getattr(i, f) for f in fieldnames] for i in _intervals1], columns=columns)
    df2 = pd.DataFrame([[getattr(i, f) for f in fieldnames] for i in _intervals2], columns=columns)
    repo.add_intervals_batch(df1, map)
    repo.add_intervals_batch(df2, map)
    df_out = repo.get_data("SYM1")
    exp_df = (
        pd.concat((df1, df2), axis=0)
        .query('symbol == "SYM1"')
        .rename(columns=map)
        .reset_index(drop=True)
    )
    assert set(df_out.columns) == set(exp_df.columns)
    assert all(df_out.index == exp_df.index)
    assert (df_out == exp_df).all().all()


def test_in_memory_repo_add_same_batches(repo: OHLCVRepository) -> None:
    _intervals1 = [_int1, _int2, _int3, _int4]
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    map = {"datetime": "timestamp", "open_price": "open"}
    inv_map = {v: k for k, v in map.items()}
    columns = [inv_map.get(f, f) for f in fieldnames]
    df1 = pd.DataFrame([[getattr(i, f) for f in fieldnames] for i in _intervals1], columns=columns)
    df2 = pd.DataFrame([[getattr(i, f) for f in fieldnames] for i in _intervals1], columns=columns)
    repo.add_intervals_batch(df1, map)
    repo.add_intervals_batch(df2, map)
    df_out = repo.get_data("SYM1")
    exp_df = df1.query('symbol == "SYM1"').rename(columns=map).reset_index(drop=True)
    assert set(df_out.columns) == set(exp_df.columns)
    assert all(df_out.index == exp_df.index)
    assert (df_out == exp_df).all().all()
