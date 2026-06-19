import pytest
from finlib.data import stream_ohlcv
from pathlib import Path

def test_stream_ohlcv_non_existing_path():
    bars = (bar for bar in stream_ohlcv(Path("aaxsad")))
    with pytest.raises(ValueError):
        for bar in bars:
            print(bar.close)
            break

def test_stream_ohlcv_file_columns(tmp_path):
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,low,close,volume\n"
    line = "AAPL,2026-01-02T09:30:00,195,194.75,195.28,1551595\n"
    csv_file.write_text(f"{columns}{line}")    
    bars = (bar for bar in stream_ohlcv(Path(csv_file)))
    with pytest.raises(Exception):
        for bar in bars:
            print(bar.close)
            break

def test_stream_ohlcv_header(tmp_path):
    csv_file = tmp_path / "prices.csv"
    line = "AAPL,2026-01-02T09:30:00,195,194.75,195.28,1551595\n"
    csv_file.write_text(f"{line}{line}")    
    bars = (bar for bar in stream_ohlcv(Path(csv_file)))
    with pytest.raises(Exception):
        for bar in bars:
            print(bar.close)
            break