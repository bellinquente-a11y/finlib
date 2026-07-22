from decimal import Decimal
from pathlib import Path

import pytest

from finlib import calculate_daily_vwap
from finlib.analytics import group_trades_by_symbol, trade_summary
from finlib.models import Trade


def test_calculate_daily_vwap_path_exists() -> None:
    with pytest.raises(RuntimeError):
        _ = calculate_daily_vwap(Path("xyz"), "AAPL")


def test_calculate_daily_vwap_missing_symbol(tmp_path: Path) -> None:
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,high,low,close,volume\n"
    line = "AAPL,2026-01-02T09:30:00,195,195.3,194.75,195.28,1551595\n"
    csv_file.write_text(f"{columns}{line}")
    with pytest.raises(RuntimeError):
        _ = calculate_daily_vwap(csv_file, "XYZ")


def test_calculate_daily_vwap_calculation(tmp_path: Path) -> None:
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,high,low,close,volume\n"
    line1 = "AAPL,2026-01-02T09:30:00,195,195.3,194.75,195.28,1551595\n"
    line2 = "AAPL,2026-01-02T10:30:00,195,195.3,194.75,200.00,1400000\n"
    csv_file.write_text(f"{columns}{line1}{line2}")
    assert calculate_daily_vwap(csv_file, "AAPL") == pytest.approx(
        Decimal((195.28 * 1551595 + 200.00 * 1400000) / (1551595 + 1400000))
    )


def test_group_trades_by_symbol_result(sample_trades: list[Trade]) -> None:
    group = group_trades_by_symbol(sample_trades)
    assert group == {
        "AAA": [sample_trades[i] for i in (1, 2, 5)],
        "BBB": [sample_trades[i] for i in (0, 4)],
        "CCC": [sample_trades[i] for i in (3,)],
    }


def test_group_trades_by_symbol_input_type(sample_trades: list[Trade]) -> None:
    with pytest.raises(TypeError):
        _ = group_trades_by_symbol(sample_trades + [None])  # type: ignore # this is a test


def test_trade_summary_input_type(sample_trades: list[Trade]) -> None:
    with pytest.raises(TypeError):
        trade_summary(sample_trades + [None])  # type: ignore # this is a test


def test_trade_summary_empty_list() -> None:
    with pytest.raises(ValueError):
        trade_summary([])


def test_trade_summary_calculation(
    capsys: pytest.CaptureFixture[str], sample_trades: list[Trade]
) -> None:
    trade_summary(sample_trades)
    captured = capsys.readouterr()
    expected = (
        "\n".join(
            [
                "AAA: 3 trades; quantity = 80.00; notional = 200.00",
                "BBB: 2 trades; quantity = 180.00; notional = 1,800.00",
                "CCC: 1 trades; quantity = 70.45; notional = -718.59",
            ]
        )
        + "\n"
    )
    assert captured.out == expected
