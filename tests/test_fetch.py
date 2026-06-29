from finlib.fetch import fetch_price
import pytest


def test_fetch_price_input_type():
    with pytest.raises(Exception):
        _ = fetch_price(12.)

def test_fetch_price_input_uppercase():
    with pytest.raises(ValueError):
        _ = fetch_price("Abc")

def test_fetch_logged_error(capsys):
    res = fetch_price("BBB")
    captured = capsys.readouterr().out
    assert (res is None) and ("error" in captured)

def test_fetch_logged_info(capsys):
    res = fetch_price("AAA")
    captured = capsys.readouterr().out
    assert isinstance(res, float) and ("info" in captured)