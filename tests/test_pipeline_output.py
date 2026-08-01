from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from finlib.pipeline.output import print_market_summary, print_trading_summary

_TIMESTAMP1 = datetime(2026, 2, 1, 10, 30)
_TIMESTAMP2 = datetime(2026, 2, 2, 10, 30)
_TIMESTAMP3 = datetime(2026, 2, 3, 10, 30)

_FORMATTERS = {"close": "{:,.0f}".format, "rolling_sharpe": "{:.2f}".format}


def _market_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["BBB", _TIMESTAMP1, Decimal(10), np.nan],
            ["BBB", _TIMESTAMP2, Decimal(11), Decimal("0.5")],
            ["AAA", _TIMESTAMP1, Decimal(20), Decimal("0.1")],
            ["AAA", _TIMESTAMP3, Decimal(21), np.nan],
        ],
        columns=["symbol", "timestamp", "close", "rolling_sharpe"],
    )


def _trading_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [[1_000.0, 2_000.0], [1_500.0, 2_500.0]],
        columns=["AAA", "BBB"],
        index=[_TIMESTAMP1, _TIMESTAMP2],
    )


def test_print_market_summary_one_row_per_symbol(capsys: pytest.CaptureFixture[str]) -> None:
    print_market_summary(_market_summary(), ["close", "rolling_sharpe"], _FORMATTERS)
    out = capsys.readouterr().out
    assert out.count("AAA") == 1
    assert out.count("BBB") == 1


def test_print_market_summary_symbols_sorted(capsys: pytest.CaptureFixture[str]) -> None:
    print_market_summary(_market_summary(), ["close", "rolling_sharpe"], _FORMATTERS)
    out = capsys.readouterr().out
    assert out.index("AAA") < out.index("BBB")


def test_print_market_summary_drops_rows_with_missing_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # AAA's most recent row (_TIMESTAMP3) has a NaN rolling_sharpe, so the most
    # recent *complete* row (_TIMESTAMP1) must be shown instead.
    print_market_summary(_market_summary(), ["close", "rolling_sharpe"], _FORMATTERS)
    out = capsys.readouterr().out
    assert "2026-02-01 10:30" in out
    assert "2026-02-03 10:30" not in out


def test_print_market_summary_applies_formatters(capsys: pytest.CaptureFixture[str]) -> None:
    print_market_summary(_market_summary(), ["close", "rolling_sharpe"], _FORMATTERS)
    out = capsys.readouterr().out
    assert "0.10" in out  # AAA rolling_sharpe formatted with "{:.2f}"
    assert "0.50" in out  # BBB rolling_sharpe formatted with "{:.2f}"


def test_print_market_summary_includes_symbol_and_timestamp_headers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_market_summary(_market_summary(), ["close"], {"close": "{:,.0f}".format})
    out = capsys.readouterr().out
    assert "symbol" in out
    assert "timestamp" in out
    assert "close" in out


def test_print_trading_summary_prints_only_last_row(capsys: pytest.CaptureFixture[str]) -> None:
    print_trading_summary(_trading_summary(), "{:,.0f}", "%Y-%m-%d %H:%M")
    out = capsys.readouterr().out
    assert "2026-02-02 10:30" in out
    assert "2026-02-01 10:30" not in out


def test_print_trading_summary_formats_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    print_trading_summary(_trading_summary(), "{:,.0f}", "%Y-%m-%d %H:%M")
    out = capsys.readouterr().out
    assert "1,500" in out  # last-row AAA value with thousands separator
    assert "2,500" in out  # last-row BBB value with thousands separator


def test_print_trading_summary_shows_column_names(capsys: pytest.CaptureFixture[str]) -> None:
    print_trading_summary(_trading_summary(), "{:,.0f}", "%Y-%m-%d %H:%M")
    out = capsys.readouterr().out
    assert "AAA" in out
    assert "BBB" in out


def test_print_trading_summary_uses_axis_format(capsys: pytest.CaptureFixture[str]) -> None:
    print_trading_summary(_trading_summary(), "{:,.0f}", "%Y/%m/%d")
    out = capsys.readouterr().out
    assert "2026/02/02" in out
