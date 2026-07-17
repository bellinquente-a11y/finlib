from finlib import calculate_daily_vwap
from pathlib import Path
import pytest
from finlib.analytics import group_trades_by_symbol, trade_summary

def test_calculate_daily_vwap_path_exists():
    with pytest.raises(Exception):
        _ = calculate_daily_vwap(Path("xyz"), "AAPL")

def test_calculate_daily_vwap_missing_symbol(tmp_path):
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,high,low,close,volume\n"
    line = "AAPL,2026-01-02T09:30:00,195,195.3,194.75,195.28,1551595\n"
    csv_file.write_text(f"{columns}{line}")
    with pytest.raises(Exception):
        _ = calculate_daily_vwap(csv_file, "XYZ")

def test_group_trades_by_symbol_result(sample_trades):
    group = group_trades_by_symbol(sample_trades)
    assert group == {"AAA": [sample_trades[i] for i in (1,2,5)], 
                     "BBB": [sample_trades[i] for i in (0,4)],
                     "CCC": [sample_trades[i] for i in (3,)]
                     }

def test_group_trades_by_symbol_input_type(sample_trades):
    sample_trades.append(None)
    with pytest.raises(TypeError):
        _ = group_trades_by_symbol(sample_trades)

def test_trade_summary_input_type(sample_trades):
    sample_trades.append(None)
    with pytest.raises(TypeError):
        trade_summary(sample_trades)

def test_trade_summary_empty_list():
    with pytest.raises(Exception):
        trade_summary([])

def test_trade_summary_calculation(capsys, sample_trades):
    trade_summary(sample_trades)
    captured = capsys.readouterr()
    expected = "\n".join(
     [
        "AAA: 3 trades; quantity = 80.00; notional = 200.00",
        "BBB: 2 trades; quantity = 180.00; notional = 1,800.00",
        "CCC: 1 trades; quantity = 70.45; notional = -718.59",
     ]) + "\n"
    assert captured.out==expected