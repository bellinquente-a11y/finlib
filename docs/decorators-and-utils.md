# Decorators & utilities

`decorators.py` and `context_managers.py` hold the cross-cutting helpers — retry, timing, input validation, deprecation — that wrap the pure functions at layer boundaries. Keeping them separate lets the core logic stay focused while resilience and instrumentation are added declaratively.

## Decorators — `decorators.py`

All four decorators are generic over the wrapped callable (`def retry[F: Callable[...]]`), use `functools.wraps` to preserve the target's identity, and log through `structlog`.

### `@retry(max_attempts=3, delay=1.0, exceptions=(Exception,))`

Retries a **sync** callable when it raises one of `exceptions`, sleeping `delay * 2**(attempt-1)` between tries — **exponential backoff**. After the attempts are exhausted it raises `RuntimeError(...) from last_exc`, chaining the original exception so the root cause is preserved in the traceback. Used on `calculate_daily_vwap` ([analytics.md](analytics.md)).

**Why exponential backoff?** A fixed short delay hammers a struggling resource; doubling the wait gives a transient problem (network blip, momentary contention) time to clear while bounding the total attempts.

### `@async_retry(max_retry, delay=1.0, exceptions=(Exception,))`

The `async` counterpart: same backoff, but `await asyncio.sleep(...)` instead of `time.sleep(...)`, so the event loop keeps running other coroutines while this one waits. This is what protects each Binance symbol fetch ([async-and-concurrency.md](async-and-concurrency.md)). A sync `time.sleep` inside a coroutine would block the whole loop — hence the separate implementation.

### `@validate_inputs(min_quantity)`

Guards a function whose first argument (or `quantity` keyword) must be `>= min_quantity`, raising `ValueError` otherwise. A small example of enforcing a caller contract at the boundary rather than sprinkling checks through the body.

### `@timer`

Logs the wall-clock duration of the wrapped call (`func`, `elapsed`) via `structlog`. This is the **decorator** form of timing, for instrumenting a whole function.

### `@deprecated`

Emits a `DeprecationWarning` (with `stacklevel=2`, so the warning points at the *caller*, not this wrapper) then delegates. A standard-library-idiomatic way to signal a sunset API without breaking it.

## Context manager — `context_managers.py`

`timer(label=None)` is a `@contextmanager` that times a **block** of code and prints the elapsed seconds (labelled if a label is given), using `try/finally` so the time is reported even if the block raises.

```python
from finlib.context_managers import timer

with timer("VWAP for BTC"):
    result = expensive_calculation()
# -> "VWAP for BTC: 0.0123s"
```

### Two timers, on purpose

There are deliberately two timing tools: the `@timer` **decorator** (whole function, logs structured) and the `timer` **context manager** (arbitrary block, prints). Use the decorator to instrument a function you own; use the context manager to time a specific region — as `calculate_daily_vwap` does around just the streaming/VWAP step. They share a name across modules but differ in scope and output, so import them explicitly to keep it clear which one is in play.

## See also

- [async-and-concurrency.md](async-and-concurrency.md) — `@async_retry` in action.
- [analytics.md](analytics.md) — `@retry` and the `timer` context manager wrapping VWAP.
