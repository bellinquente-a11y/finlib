from finlib.pipeline.analytics import compute_market_summary, get_market_price, \
    compute_portfolio_performance_metrics
from finlib.ohlcv_repo import InMemoryOHLCVRepository, OHLCVInterval, OHLCVRepository, \
    FileOHLCVRepository
from finlib.trade_repo import TradeRepository, FileTradeRepository, InMemoryTradeRepository
from finlib import Trade
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from numpy import nan

_TIMESTAMP1 = datetime(2026,6,1,1,2,3)
_TIMESTAMP2 = datetime(2026,6,2,1,2,3)
_TIMESTAMP3 = datetime(2026,6,3,1,2,3)
_TIMESTAMP4 = datetime(2026,6,4,1,2,3)

_OHLCVINT = [
    OHLCVInterval(symbol="SYM1", timestamp=_TIMESTAMP1, open=Decimal(101.2), high=Decimal(102.4), 
                    low=Decimal(100.8), close=Decimal(100.9), volume=Decimal(1_342)),
    OHLCVInterval(symbol="SYM1", timestamp=_TIMESTAMP2, open=Decimal(101.2), high=Decimal(102.4), 
                    low=Decimal(100.8), close=Decimal(101.9), volume=Decimal(1_342)),
    OHLCVInterval(symbol="SYM1", timestamp=_TIMESTAMP3, open=Decimal(101.2), high=Decimal(102.4), 
                    low=Decimal(100.8), close=Decimal(102.9), volume=Decimal(1_342)),
    OHLCVInterval(symbol="SYM2", timestamp=_TIMESTAMP4, open=Decimal(101.2), high=Decimal(102.4), 
                    low=Decimal(100.8), close=Decimal(103.9), volume=Decimal(1_342)),
]

_TRADES = [
    Trade(symbol="BHP", quantity=Decimal(100), price=Decimal(45.), 
          side="BUY", timestamp=_TIMESTAMP1),
    Trade(symbol="BHP", quantity=Decimal(40), price=Decimal(48.), 
          side="SELL", timestamp=_TIMESTAMP3),
    Trade(symbol="AAA", quantity=Decimal(100), price=Decimal(12.), 
          side="SELL", timestamp=_TIMESTAMP2),
    Trade(symbol="AAA", quantity=Decimal(100), price=Decimal(19.), 
          side="SELL", timestamp=_TIMESTAMP4),
]

@pytest.fixture(params=["memory", "csv"])
def ohlcv_repo(request, tmp_path) -> OHLCVRepository:
    if request.param == "memory":
        return InMemoryOHLCVRepository()
    if request.param == "csv":
        return FileOHLCVRepository(tmp_path / "ohlcv_repo.csv")

@pytest.fixture(params = ("memory", "jsonl"))
def trade_repo(request, tmp_path) -> TradeRepository:
    if request.param=="memory":
        return InMemoryTradeRepository()
    elif request.param=="jsonl":
        return FileTradeRepository(tmp_path / "trade_repo.jsonl")

def test_compute_market_summary_empty_repo(ohlcv_repo: OHLCVRepository):
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    df = pd.DataFrame([["AAA", datetime(2026,2,1,13,4,10), *[Decimal(100.) for _ in range(5)]]], 
                      columns=columns)
    ohlcv_repo.add_intervals_batch(df)
    df = compute_market_summary(ohlcv_repo, ["CCC", "BBB"])
    assert (df == pd.DataFrame()).all().all()

def test_compute_market_summary_rolling_sharpe(ohlcv_repo: OHLCVRepository):
    window = 3
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    data = 5*[["AAA", datetime(2026,2,1,13,4,10), *[Decimal(100.) for _ in range(5)]]]
    for i in range(5):
        data[i][1] = data[i][1] + timedelta(days=1)
    df = pd.DataFrame(data, columns=columns)
    ohlcv_repo.add_intervals_batch(df)
    result = compute_market_summary(ohlcv_repo, ["AAA"], window)
    assert (result["rolling_sharpe"].iloc[:window].isna().all()) and \
        (result["rolling_sharpe"].iloc[window:].notna().all())

def test_get_market_price_calculation(ohlcv_repo: OHLCVRepository):
    for oint in _OHLCVINT:
        ohlcv_repo.add_interval(oint)
    df = get_market_price(ohlcv_repo, ["SYM1", "SYM2"], datetime(1990,1,1))
    exp_df = pd.DataFrame([
        [Decimal(100.9), nan],
        [Decimal(101.9), nan],
        [Decimal(102.9), nan],
        [nan, Decimal(103.9)],
        ],
        columns= ["SYM1", "SYM2"],
        index=[_TIMESTAMP1, _TIMESTAMP2, _TIMESTAMP3, _TIMESTAMP4]
    )
    assert (df.isna()==exp_df.isna()).all().all()
    assert (df.fillna(Decimal(0)) == exp_df.fillna(Decimal(0))).all().all()

def test_compute_portfolio_performance_metrics(ohlcv_repo: OHLCVRepository, 
                                               trade_repo: TradeRepository):
    for oint in _OHLCVINT:
        ohlcv_repo.add_interval(oint)
    for t in _TRADES:
        trade_repo.add(t)
    with pytest.raises(RuntimeError):
        _ = compute_portfolio_performance_metrics(trade_repo, ohlcv_repo)
