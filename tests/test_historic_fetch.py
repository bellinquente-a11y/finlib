from finlib.historic_fetch import _format_binance_output, _fetch_binance_data_per_product, load_binance_data_per_product
import pytest
from unittest.mock import patch

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

def test_load_binance_data_per_product_output_shape():
    with patch("finlib.historic_fetch._fetch_binance_data_per_product") as mock:
        mocked_line = [1782707280000, '59969.64000000','59972.00000000','59941.03000000', '59941.03000000', '7.63798000', 
                       1782707339999, '458032.05198250', 1714, '0.66735000', '40088.75994900', '0']
        mock.return_value = [mocked_line, mocked_line, mocked_line]
        result = load_binance_data_per_product("SYM", "1m", 3)
    assert result.shape == (3, 11)
