import time
from typing import Generator, TypeVar, Callable, Any
from contextlib import contextmanager
import functools
import logging

log = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])

@contextmanager
def timer(label: str = "") -> Generator[None, None, None]:
    """Context manager to time an operation"""

    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"{label}: {elapsed:.4f}s")


def retry(max_attempts: int = 3, 
          delay: float = 1., 
          exceptions: tuple[type[Exception], ...] = (Exception, )
          ) -> Callable[[F], F]:
    """Decorator to retry a callable in case of exceptions"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            last_exc: Exception | None = None
            while attempt<=max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    wait_time = delay * 2**(attempt-1)
                    log.warning(f"Attempt {attempt} failed, wait {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1
            raise RuntimeError(f"Failed after {max_attempts} attempts") from last_exc
        
        return wrapper # type: ignore[return-value]
    return decorator


def validate_inputs(min_quantity: int) -> Callable[[F], F]:
    """Decorator to validate the minimum quantity input of a function"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            quantity = kwargs.get('quantity', args[0] if args else None)
            if quantity is not None and quantity<min_quantity:
                raise ValueError(f"quantity {quantity} needs to be >= than {min_quantity}")
            return func(*args, **kwargs)
        return wrapper # type: ignore[return-value]
    return decorator