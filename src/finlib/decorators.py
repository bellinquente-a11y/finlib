import time
from typing import TypeVar, Callable, Any
import functools
import logging
import warnings

log = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])


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


def timer(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        interval = time.perf_counter() - start
        print(f"call to {func.__name__}: {interval:.3f}s")
        return result
    return wrapper # type: ignore[return-value]


def deprecated(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        warnings.warn(f"Function {func.__name__} will not be supported in a future release", DeprecationWarning, stacklevel=2)
        return result
    return wrapper # type: ignore[return-value]