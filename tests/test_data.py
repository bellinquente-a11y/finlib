import pytest
from finlib.data import stream_ohlcv
from pathlib import Path

def test_stream_ohlcv_non_existing_path():
    bars = (bar for bar in stream_ohlcv(Path("aaxsad")))
    with pytest.raises(ValueError):
        for bar in bars:
            print(bar.close)
