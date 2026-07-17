from finlib.trade_repo import InMemoryTradeRepository
from finlib.ohlcv_repo import InMemoryOHLCVRepository
from finlib import Trade
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from finlib.pipeline.data import fetch_trades, store_market_data
import pytest
import pandas as pd

def test_fetch_trades_output():
    ts = datetime(2026,1,1,12,3,34, tzinfo=timezone.utc) 
    repo = InMemoryTradeRepository()
    repo.add(Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(105.), side="BUY"))
    repo.add(Trade(symbol="BBB", quantity=Decimal(10.), price=Decimal(105.), side="BUY"))
    repo.add(Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(105.), side="BUY"))
    repo.add(Trade(symbol="AAA", quantity=Decimal(10.), price=Decimal(105.), side="BUY", timestamp=ts))
    repo.add(Trade(symbol="CCC", quantity=Decimal(10.), price=Decimal(105.), side="BUY"))
    trades, symbols, first_dt = fetch_trades(repo)
    assert len(trades)==5 and len(symbols)==3 and first_dt==ts

def test_fetch_trades_empty_repo():
    repo = InMemoryTradeRepository()
    with pytest.raises(RuntimeError):
        _, _, _ = fetch_trades(repo)

def test_store_market_data_ordered_output():
    columns = ["symbol", "close_time", "open", "high", "low", "close", "volume"]
    data = 5*[["AAA", datetime(2026,2,1,13,4,10), *[Decimal(100.) for _ in range(5)]]]
    for i in range(5):
        data[i][1] = data[i][1] + timedelta(minutes=1)
    df = pd.DataFrame(data, columns=columns)
    df_inv = df.sort_values(by="close_time", ascending=False)
    ohlcv_repo = InMemoryOHLCVRepository()
    store_market_data(ohlcv_repo, df_inv)
    df_out = ohlcv_repo.get_data("AAA")
    assert (df_out.rename(columns={"timestamp": "close_time"})==df).all().all()
