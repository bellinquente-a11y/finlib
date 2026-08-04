from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from structlog.testing import capture_logs

from finlib import Trade
from finlib.ohlcv_repo import InMemoryOHLCVRepository
from finlib.pipeline.data import fetch_trades, store_market_data
from finlib.trade_repo import InMemoryTradeRepository


def test_fetch_trades_output() -> None:
    ts = datetime(2026, 1, 1, 12, 3, 34, tzinfo=UTC)
    repo = InMemoryTradeRepository()
    repo.add(Trade(symbol="AAA", quantity=Decimal(10.0), price=Decimal(105.0), side="BUY"))
    repo.add(Trade(symbol="BBB", quantity=Decimal(10.0), price=Decimal(105.0), side="BUY"))
    repo.add(Trade(symbol="AAA", quantity=Decimal(10.0), price=Decimal(105.0), side="BUY"))
    repo.add(
        Trade(symbol="AAA", quantity=Decimal(10.0), price=Decimal(105.0), side="BUY", timestamp=ts)
    )
    repo.add(Trade(symbol="CCC", quantity=Decimal(10.0), price=Decimal(105.0), side="BUY"))
    trades, symbols, first_dt = fetch_trades(repo)
    assert len(trades) == 5 and len(symbols) == 3 and first_dt == ts


def test_fetch_trades_empty_repo() -> None:
    repo = InMemoryTradeRepository()
    with pytest.raises(RuntimeError):
        _, _, _ = fetch_trades(repo)


def test_store_market_data_ordered_output() -> None:
    columns = ["symbol", "close_time", "open", "high", "low", "close", "volume"]
    base_timestamp = datetime(2026, 2, 1, 13, 4, 10)
    data = [
        ["AAA", base_timestamp + i * timedelta(minutes=1), *[Decimal(100.0) for _ in range(5)]]
        for i in range(5)
    ]
    df = pd.DataFrame(data, columns=columns)
    df_inv = df.sort_values(by="close_time", ascending=False)
    ohlcv_repo = InMemoryOHLCVRepository()
    store_market_data(ohlcv_repo, df_inv)
    df_out = ohlcv_repo.get_data("AAA")
    assert (
        (
            (df_out.rename(columns={"timestamp": "close_time"}).reset_index(drop=True))
            == (df.reset_index(drop=True))
        )
        .all()
        .all()
    )


def test_fstore_market_data_empty_df_error() -> None:
    repo = InMemoryTradeRepository()
    with pytest.raises(RuntimeError, match="No trades in trade repository"), capture_logs() as logs:
        _ = fetch_trades(repo)
        assert logs[0]["event"] == "Empty trade repository"


def test_fetch_trades_empty_repo_error() -> None:
    ohlcv_repo = InMemoryOHLCVRepository()
    with pytest.raises(ValueError, match="Empty market data DataFrame"), capture_logs() as logs:
        store_market_data(ohlcv_repo, pd.DataFrame())
        assert logs[0]["event"] == "Empty market price dataframe"
