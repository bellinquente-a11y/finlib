from finlib.fetch import fetch_price
import pytest


def test_fetch_price_input_type():
    with pytest.raises(TypeError):
        _ = fetch_price(12.)

def test_fetch_price_input_uppercase():
    with pytest.raises(ValueError):
        _ = fetch_price("Abc")