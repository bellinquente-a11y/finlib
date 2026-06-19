from finlib import calculate_daily_vwap
from pathlib import Path
import pytest

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