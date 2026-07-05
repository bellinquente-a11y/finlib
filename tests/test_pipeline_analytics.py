from finlib.pipeline.analytics import compute_market_summary
from finlib.ohlcv_repo import InMemoryOHLCVRepo
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

def test_compute_market_summary_empty_repo():
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    df = pd.DataFrame([["AAA", datetime(2026,2,1,13,4,10), *[Decimal(100.) for _ in range(5)]]], columns=columns)
    ohlcv_repo = InMemoryOHLCVRepo()
    ohlcv_repo.add_intervals_batch(df)
    df = compute_market_summary(ohlcv_repo, ["CCC", "BBB"])
    assert (df == pd.DataFrame()).all().all()

def test_compute_market_summary_rolling_sharpe():
    window = 3
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    data = 5*[["AAA", datetime(2026,2,1,13,4,10), *[Decimal(100.) for _ in range(5)]]]
    for i in range(5):
        data[i][1] = data[i][1] + timedelta(days=1)
    df = pd.DataFrame(data, columns=columns)
    ohlcv_repo = InMemoryOHLCVRepo()
    ohlcv_repo.add_intervals_batch(df)
    result = compute_market_summary(ohlcv_repo, ["AAA"], window)
    assert (result["rolling_sharpe"].iloc[:window].isna().all()) and (result["rolling_sharpe"].iloc[window:].notna().all())

