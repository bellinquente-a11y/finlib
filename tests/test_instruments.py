from decimal import Decimal

import pytest

from finlib import Equity, Future


def test_price_Decimal() -> None:
    for instrument in [Equity, Future]:
        with pytest.raises(TypeError):
            _ = instrument("xyz", 154.)   # type: ignore # this is a test

def test_ticker_uppercase() -> None:
    for instrument in [Equity, Future]:
        x = instrument("xyz", Decimal(154.))
        assert x.symbol == "XYZ"