from decimal import Decimal

import pytest

from finlib import Equity, Future


def test_price_Decimal():
    for instrument in [Equity, Future]:
        with pytest.raises(TypeError):
            _ = instrument("xyz", 154.)        

def test_ticker_uppercase():
    for instrument in [Equity, Future]:
        x = instrument("xyz", Decimal(154.))
        assert x.symbol == "XYZ"