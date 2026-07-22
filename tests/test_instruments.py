from decimal import Decimal

import pytest

from finlib import Equity, Future


def test_price_Decimal() -> None:
    for instrument in [Equity, Future]:
        with pytest.raises(TypeError):
            _ = instrument("xyz", 154.0)  # type: ignore # this is a test


def test_ticker_uppercase() -> None:
    for instrument in [Equity, Future]:
        x = instrument("xyz", Decimal(154.0))
        assert x.symbol == "XYZ"


def test_repr_description_equity_class() -> None:
    obj = Equity("AAA", Decimal(101.2))
    assert obj.__repr__() == "Equity('AAA')"
    assert obj.description() == "Equity: AAA @ 101.20"


def test_repr_description_future_class() -> None:
    obj = Future("BBB", Decimal(101.236))
    assert obj.__repr__() == "Future('BBB')"
    assert obj.description() == "Future: BBB @ 101.24"
