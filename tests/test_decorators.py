import pytest

from finlib.decorators import deprecated, retry, timer, validate_inputs


def test_retry_does_not_affect_working_function() -> None:
    @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
    def test_retry() -> int:
        return 1

    assert isinstance(test_retry(), int)
    assert test_retry() == 1


def test_retry_number_retries() -> None:
    count = 0

    @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
    def test_retry() -> int:
        nonlocal count
        count += 1
        raise ValueError

    with pytest.raises(RuntimeError):
        _ = test_retry()
    assert count == 3


def test_validate_inputs() -> None:
    @validate_inputs(min_quantity=1)
    def price_order(quantity: float, price: float) -> float:
        return quantity * price

    assert price_order(10, 15.0) == 150.0
    assert price_order(1, 15.0) == 15.0
    with pytest.raises(ValueError):
        _ = price_order(0, 15.0)


def test_timer_preserves_return_value() -> None:
    @timer
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


def test_timer_prints_output(capsys: pytest.CaptureFixture[str]) -> None:
    @timer
    def add(a: int, b: int) -> int:
        return a + b

    add(1, 2)
    out = capsys.readouterr().out
    assert "timed call to function" in out


def test_deprecated_warning() -> None:
    @deprecated
    def add(a: int, b: int) -> int:
        return a + b

    with pytest.warns(DeprecationWarning):
        add(2, 3)
