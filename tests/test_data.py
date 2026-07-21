from pathlib import Path

import pytest

from finlib.data import stream_ohlcv, stream_trades


def test_stream_ohlcv_non_existing_path() -> None:
    bars = (bar for bar in stream_ohlcv(Path("aaxsad")))
    with pytest.raises(ValueError):
        for bar in bars:
            print(bar.close)
            break

def test_stream_ohlcv_file_columns(tmp_path: Path) -> None:
    csv_file = tmp_path / "prices.csv"
    columns = "symbol,timestamp,open,low,close,volume\n"
    line = "AAPL,2026-01-02T09:30:00,195,194.75,195.28,1551595\n"
    csv_file.write_text(f"{columns}{line}")    
    bars = (bar for bar in stream_ohlcv(Path(csv_file)))
    with pytest.raises(KeyError):
        for bar in bars:
            print(bar.close)
            break

def test_stream_ohlcv_header(tmp_path: Path) -> None:
    csv_file = tmp_path / "prices.csv"
    line = "AAPL,2026-01-02T09:30:00,195,194.75,195.28,1551595\n"
    csv_file.write_text(f"{line}{line}")    
    bars = (bar for bar in stream_ohlcv(Path(csv_file)))
    with pytest.raises(KeyError):
        for bar in bars:
            print(bar.close)
            break

def test_stream_trades_non_existing_path() -> None:
    bars = (bar for bar in stream_trades(Path("aaxsad")))
    with pytest.raises(ValueError):
        for bar in bars:
            print(bar.symbol)
            break

def test_stream_trades_file_columns(tmp_path: Path) -> None:
    csv_file = tmp_path / "trades.csv"
    columns = "symbol,timestamp,price,side\n"
    line = "AMZN,2026-06-23T09:30:30,205.14,BUY\n"
    csv_file.write_text(f"{columns}{line}")    
    bars = (bar for bar in stream_trades(Path(csv_file)))
    with pytest.raises(KeyError):
        for bar in bars:
            print(bar.symbol)
            break

def test_stream_trades_header(tmp_path: Path) -> None:
    csv_file = tmp_path / "trades.csv"
    line = "AMZN,2026-06-23T09:30:30,205.14,331,BUY\n"
    csv_file.write_text(f"{line}{line}")    
    bars = (bar for bar in stream_trades(Path(csv_file)))
    with pytest.raises(KeyError):
        for bar in bars:
            print(bar.symbol)
            break