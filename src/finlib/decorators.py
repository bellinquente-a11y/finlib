import asyncio
import functools
import time
import warnings
from collections.abc import Callable
from typing import Any

import structlog

log = structlog.get_logger(__name__)


def retry[F: Callable[..., Any]](
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator to retry a callable in case of exceptions"""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            last_exc: Exception | None = None
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    wait_time = delay * 2 ** (attempt - 1)
                    log.warning(
                        "Failed function call attempt", attempt=attempt, wait_time=wait_time
                    )
                    time.sleep(wait_time)
                    attempt += 1
            raise RuntimeError(f"Failed after {max_attempts} attempts") from last_exc

        return wrapper  # type: ignore[return-value]

    return decorator


def validate_inputs[F: Callable[..., Any]](min_quantity: int) -> Callable[[F], F]:
    """Decorator to validate the minimum quantity input of a function"""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            quantity = kwargs.get("quantity", args[0] if args else None)
            if quantity is not None and quantity < min_quantity:
                raise ValueError(f"quantity {quantity} needs to be >= than {min_quantity}")
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def timer[F: Callable[..., Any]](func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        interval = time.perf_counter() - start
        log.info("timed call to function", func=func.__name__, elapsed=interval)
        return result

    return wrapper  # type: ignore[return-value]


def deprecated[F: Callable[..., Any]](func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"Function {func.__name__} will not be supported in a future release",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def async_retry[F: Callable[..., Any]](
    max_retry: int, delay: float = 1.0, exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            count = 1
            while count <= max_retry:
                wait_time = delay * 2 ** (count - 1)
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    log.info("Retry function call", func=func, count=count, wait=wait_time, exc=e)
                    count += 1
                    await asyncio.sleep(wait_time)
            raise RuntimeError(
                f"Failed call to {func.__name__} after {count - 1} attempts"
            ) from last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
