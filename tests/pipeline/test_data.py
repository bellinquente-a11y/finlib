from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from structlog.testing import capture_logs

from finlib import Trade
from finlib.ohlcv_repo import InMemoryOHLCVRepository
from finlib.pipeline.data import (
    fetch_trades,
    store_market_data,
    update_market_data_repo,
)
from finlib.trade_repo import InMemoryTradeRepository


def _market_df(symbol: str, base: datetime, n: int = 3) -> pd.DataFrame:
    """Build a market-data DataFrame shaped like the Binance fetch output."""
    columns = ["symbol", "close_time", "open", "high", "low", "close", "volume"]
    data = [
        [symbol, base + i * timedelta(minutes=1), *[Decimal(100.0) for _ in range(5)]]
        for i in range(n)
    ]
    return pd.DataFrame(data, columns=columns)


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


def test_update_market_data_repo_fetches_new_symbols() -> None:
    """A symbol with no local data is fetched from the given start and stored."""
    ohlcv_repo = InMemoryOHLCVRepository()
    start = datetime(2026, 3, 1, tzinfo=UTC)
    fetched = _market_df("AAA", start)

    with patch(
        "finlib.pipeline.data.fetch_market_data", new=AsyncMock(return_value=fetched)
    ) as mock_fetch:
        update_market_data_repo(
            ohlcv_repo, ["AAA"], "1h", start, max_update_freq=timedelta(hours=1)
        )

    mock_fetch.assert_awaited_once_with(["AAA"], "1h", start)
    assert ohlcv_repo.get_data("AAA").shape[0] == 3


def test_update_market_data_repo_skips_fresh_symbols() -> None:
    """A symbol updated more recently than max_update_freq is not fetched again."""
    ohlcv_repo = InMemoryOHLCVRepository()
    start = datetime(2026, 3, 1, tzinfo=UTC)
    store_market_data(ohlcv_repo, _market_df("AAA", start))

    with patch("finlib.pipeline.data.fetch_market_data", new=AsyncMock()) as mock_fetch:
        update_market_data_repo(ohlcv_repo, ["AAA"], "1h", start, max_update_freq=timedelta(days=1))

    mock_fetch.assert_not_awaited()


def test_update_market_data_repo_refetches_stale_symbols() -> None:
    """A stale symbol is re-fetched from its last stored timestamp when earlier than start."""
    ohlcv_repo = InMemoryOHLCVRepository()
    stored_base = datetime(2026, 1, 1, tzinfo=UTC)
    store_market_data(ohlcv_repo, _market_df("AAA", stored_base))
    # Force the symbol to look stale.
    ohlcv_repo._last_updated["AAA"] = datetime(2026, 1, 1, tzinfo=UTC)
    last_ts = cast(datetime, ohlcv_repo.last_timestamp("AAA"))

    start = datetime(2026, 6, 1, tzinfo=UTC)
    fetched = _market_df("AAA", last_ts + timedelta(minutes=1))

    with patch(
        "finlib.pipeline.data.fetch_market_data", new=AsyncMock(return_value=fetched)
    ) as mock_fetch:
        update_market_data_repo(
            ohlcv_repo, ["AAA"], "1h", start, max_update_freq=timedelta(hours=1)
        )

    # start is narrowed to the last stored timestamp (min of start and last_timestamp).
    mock_fetch.assert_awaited_once_with(["AAA"], "1h", last_ts)


def test_update_market_data_repo_no_symbols() -> None:
    """With no symbols there is nothing to fetch."""
    ohlcv_repo = InMemoryOHLCVRepository()
    with patch("finlib.pipeline.data.fetch_market_data", new=AsyncMock()) as mock_fetch:
        update_market_data_repo(
            ohlcv_repo,
            [],
            "1h",
            datetime(2026, 3, 1, tzinfo=UTC),
            max_update_freq=timedelta(hours=1),
        )
    mock_fetch.assert_not_awaited()
