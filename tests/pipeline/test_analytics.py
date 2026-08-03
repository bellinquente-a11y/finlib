from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest
from numpy import nan
from structlog.testing import capture_logs

from finlib import Trade
from finlib.ohlcv_repo import (
    FileOHLCVRepository,
    InMemoryOHLCVRepository,
    OHLCVInterval,
    OHLCVRepository,
)
from finlib.pipeline.analytics import (
    compute_market_summary,
    compute_portfolio_performance_metrics,
    get_market_price,
)
from finlib.trade_repo import FileTradeRepository, InMemoryTradeRepository, TradeRepository

_TIMESTAMP1 = datetime(2026, 6, 1, 1, 2, 3)
_TIMESTAMP2 = datetime(2026, 6, 2, 1, 2, 3)
_TIMESTAMP3 = datetime(2026, 6, 3, 1, 2, 3)
_TIMESTAMP4 = datetime(2026, 6, 4, 1, 2, 3)

_OHLCVINT = [
    OHLCVInterval(
        symbol="SYM1",
        timestamp=_TIMESTAMP1,
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(100.9),
        volume=Decimal(1_342),
    ),
    OHLCVInterval(
        symbol="SYM1",
        timestamp=_TIMESTAMP2,
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(101.9),
        volume=Decimal(1_342),
    ),
    OHLCVInterval(
        symbol="SYM1",
        timestamp=_TIMESTAMP3,
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(102.9),
        volume=Decimal(1_342),
    ),
    OHLCVInterval(
        symbol="SYM2",
        timestamp=_TIMESTAMP4,
        open=Decimal(101.2),
        high=Decimal(102.4),
        low=Decimal(100.8),
        close=Decimal(103.9),
        volume=Decimal(1_342),
    ),
]

_TRADES = [
    Trade(
        symbol="BHP", quantity=Decimal(100), price=Decimal(45.0), side="BUY", timestamp=_TIMESTAMP1
    ),
    Trade(
        symbol="BHP", quantity=Decimal(40), price=Decimal(48.0), side="SELL", timestamp=_TIMESTAMP3
    ),
    Trade(
        symbol="AAA", quantity=Decimal(100), price=Decimal(12.0), side="SELL", timestamp=_TIMESTAMP2
    ),
    Trade(
        symbol="AAA", quantity=Decimal(100), price=Decimal(19.0), side="SELL", timestamp=_TIMESTAMP4
    ),
]


@pytest.fixture(params=["memory", "csv"])
def ohlcv_repo(request: pytest.FixtureRequest, tmp_path: Path) -> OHLCVRepository:
    if request.param == "memory":
        return InMemoryOHLCVRepository()
    return FileOHLCVRepository(tmp_path / "ohlcv_repo.csv")


@pytest.fixture(params=("memory", "jsonl"))
def trade_repo(request: pytest.FixtureRequest, tmp_path: Path) -> TradeRepository:
    if request.param == "memory":
        return InMemoryTradeRepository()
    return FileTradeRepository(tmp_path / "trade_repo.jsonl")


def test_compute_market_summary_empty_repo(ohlcv_repo: OHLCVRepository) -> None:
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    df = pd.DataFrame(
        [["AAA", datetime(2026, 2, 1, 13, 4, 10), *[Decimal(100.0) for _ in range(5)]]],
        columns=columns,
    )
    ohlcv_repo.add_intervals_batch(df)
    df = compute_market_summary(ohlcv_repo, ["CCC", "BBB"])
    assert (df == pd.DataFrame()).all().all()


def test_compute_market_summary_rolling_sharpe(ohlcv_repo: OHLCVRepository) -> None:
    window = 3
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    base_timestamp = datetime(2026, 2, 1, 13, 4, 10)
    data = [
        ["AAA", base_timestamp + timedelta(days=i), *[Decimal(100.0) for _ in range(5)]]
        for i in range(5)
    ]
    df = pd.DataFrame(data, columns=columns)
    ohlcv_repo.add_intervals_batch(df)
    result = compute_market_summary(ohlcv_repo, ["AAA"], window)
    assert (result["rolling_sharpe"].iloc[:window].isna().all()) and (
        result["rolling_sharpe"].iloc[window:].notna().all()
    )


def test_get_market_price_calculation(ohlcv_repo: OHLCVRepository) -> None:
    for oint in _OHLCVINT:
        ohlcv_repo.add_interval(oint)
    df = get_market_price(ohlcv_repo, ["SYM1", "SYM2"], datetime(1990, 1, 1))
    exp_df = pd.DataFrame(
        [
            [Decimal(100.9), nan],
            [Decimal(101.9), nan],
            [Decimal(102.9), nan],
            [nan, Decimal(103.9)],
        ],
        columns=["SYM1", "SYM2"],
        index=[_TIMESTAMP1, _TIMESTAMP2, _TIMESTAMP3, _TIMESTAMP4],
    )
    assert (df.isna() == exp_df.isna()).all().all()
    assert (df.fillna(0) == exp_df.fillna(0)).all().all()


def test_compute_portfolio_performance_metrics(
    ohlcv_repo: OHLCVRepository, trade_repo: TradeRepository
) -> None:
    for oint in _OHLCVINT:
        ohlcv_repo.add_interval(oint)
    for t in _TRADES:
        trade_repo.add(t)
    with pytest.raises(RuntimeError):
        _ = compute_portfolio_performance_metrics(trade_repo, ohlcv_repo)


def test_compute_market_summary_missing_symbol_warning() -> None:
    ohlcv_repo = InMemoryOHLCVRepository()
    with capture_logs() as logs:
        _ = compute_market_summary(ohlcv_repo, ["AAA"])
        assert logs[0]["log_level"] == "warning"
        assert logs[0]["event"] == "Missing data from OHLCV repo"
        assert logs[0]["symbol"] == "AAA"


def test_get_market_price_missing_symbol_warning() -> None:
    ohlcv_repo = InMemoryOHLCVRepository()
    with capture_logs() as logs:
        _ = get_market_price(ohlcv_repo, ["ABC"], datetime(2022, 1, 1))
        assert logs[0]["log_level"] == "warning"
        assert logs[0]["event"] == "Missing data from OHLCV repo"
        assert logs[0]["symbol"] == "ABC"


def test_compute_portfolio_performance_metrics_missing_symbols_error(
    tmp_trade_repo: TradeRepository, tmp_ohlcv_repo: OHLCVRepository
) -> None:
    with (
        pytest.raises(RuntimeError, match="Missing symbols in price dataframe"),
        capture_logs() as logs,
    ):
        _ = compute_portfolio_performance_metrics(tmp_trade_repo, tmp_ohlcv_repo)
        assert logs[0]["log_level"] == "error"
        assert logs[0]["event"] == "Missing symbols in the market price dataframe"
