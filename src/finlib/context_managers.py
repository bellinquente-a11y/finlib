import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def timer(label: str | None = None) -> Generator[None, None, None]:
    """Context manager to time an operation"""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        if label is None:
            print(f"{elapsed:.4f}s")
        else:
            print(f"{label}: {elapsed:.4f}s")