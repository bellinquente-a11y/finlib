from finlib.utils import retry
import pytest

def test_retry_does_not_affect_working_function():
    @retry(max_attempts=3, delay=0.5, exceptions=(ValueError,))
    def test_retry() -> int: return int(1)
    assert isinstance(test_retry(), int)
    assert test_retry()==1 
    