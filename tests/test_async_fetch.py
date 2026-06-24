from finlib.async_fetch import stream_binance_data
import pytest

def test_stream_binance_data_interval():
    with pytest.raises(ValueError):
        _ = stream_binance_data(["BTCUSDT"], "13m")

def test_stream_binance_data_symbol_type():
    with pytest.raises(TypeError):
        _ = stream_binance_data("BTCUSDT", "1m")

def test_stream_binance_data_len_output():
    res = stream_binance_data(["x", "y", "z"], "1m")
    assert len(res)==3
