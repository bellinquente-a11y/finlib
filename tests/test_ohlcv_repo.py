from decimal import Decimal
from finlib.ohlcv_repo import OHLCVInterval, OHLCVRepo, InMemoryOHLCVRepo, FileOHLCVRepo
from datetime import datetime
import pandas as pd
import dataclasses
import pytest

_int1 = OHLCVInterval(symbol="SYM1", timestamp=datetime(2026,6,1,1,2,3), open=Decimal(101.2), high=Decimal(102.4), 
                      low=Decimal(100.8), close=Decimal(100.9), volume=Decimal(1_342))
_int2 = OHLCVInterval(symbol="SYM1", timestamp=datetime(2026,6,2,1,2,3), open=Decimal(101.2), high=Decimal(102.4), 
                      low=Decimal(100.8), close=Decimal(100.9), volume=Decimal(1_342))
_int3 = OHLCVInterval(symbol="SYM1", timestamp=datetime(2026,6,3,1,2,3), open=Decimal(101.2), high=Decimal(102.4), 
                      low=Decimal(100.8), close=Decimal(100.9), volume=Decimal(1_342))
_int4 = OHLCVInterval(symbol="SYM2", timestamp=datetime(2026,6,4,1,2,3), open=Decimal(101.2), high=Decimal(102.4), 
                      low=Decimal(100.8), close=Decimal(100.9), volume=Decimal(1_342))

@pytest.fixture(params=["memory", "csv"])
def repo(request, tmp_path) -> OHLCVRepo:
    if request.param == "memory":
        return InMemoryOHLCVRepo()
    if request.param == "csv":
        return FileOHLCVRepo(tmp_path / "ohlcv_repo.csv")

def test_in_memory_repo_output(repo: OHLCVRepo):
    for i in [_int1, _int2, _int3, _int4]:
        repo.add_interval(i)
    df = repo.get_data("SYM1", datetime(2026,6,2,0,0,0), datetime(2026,6,2,23,59,59))
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    assert (df == pd.DataFrame([[getattr(_int2, f) for f in fieldnames]], columns=fieldnames)).all().all()

def test_in_memory_repo_add_batch(repo: OHLCVRepo):
    _intervals = [_int1, _int2, _int3, _int4]
    fieldnames = [f.name for f in dataclasses.fields(OHLCVInterval)]
    map = {"datetime": "timestamp", "open_price": "open"}
    inv_map = {v:k for k,v in map.items()}
    columns = [inv_map[f] if f in inv_map.keys() else f for f in fieldnames]
    df = pd.DataFrame([[getattr(i,f) for f in fieldnames] for i in _intervals], columns=columns)
    repo.add_intervals_batch(df, map)
    df_out = repo.get_data("SYM1") 
    assert (df_out == df.query('symbol == "SYM1"').rename(columns=map)).all().all()