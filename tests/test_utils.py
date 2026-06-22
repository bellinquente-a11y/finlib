from finlib.utils import retry, validate_inputs
import pytest
def test_retry_does_not_affect_working_function():
    @retry(max_attempts=3, delay=0.5, exceptions=(ValueError,))
    def test_retry() -> int: return int(1)
    assert isinstance(test_retry(), int)
    assert test_retry()==1 

def test_validate_inputs():
    @validate_inputs(min_quantity=1)
    def price_order(quantity: float, price: float) -> float:
        return quantity * price
    assert price_order(10, 15.) == 150.
    assert price_order(1, 15.) == 15.
    with pytest.raises(ValueError):
        _ = price_order(0, 15.)
    