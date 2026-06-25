from finlib.historic_fetch import _format_binance_output, _fetch_binance_data_per_product
import pytest

def test__format_binance_output_len_rows():
    data = [[1, 2], [3, 4, 5]]
    with pytest.raises(ValueError):
        _ = _format_binance_output(data)

def test__format_binance_output_zero_input():
    data = []
    with pytest.raises(ValueError):
        _ = _format_binance_output(data)

def test__format_binance_output_wrong_type():
    data = [12*["a"]]
    with pytest.raises(ValueError):
        _ = _format_binance_output(data)

def test__fetch_binance_data_per_product_interval():
    with pytest.raises(ValueError):
        _ = _fetch_binance_data_per_product("XYZ", "13s", 1)

def test__fetch_binance_data_per_product_limit():
    with pytest.raises(ValueError):
        _ = _fetch_binance_data_per_product("XYZ", "1h", 0)