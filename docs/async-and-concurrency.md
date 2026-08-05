# Async & concurrency

`async_fetch.py` fetches OHLCV market data from the Binance REST API for many symbols at once. It is the project's showcase of I/O-bound concurrency: `asyncio.gather` for parallelism, a `Semaphore` for rate limiting, retry-with-backoff for resilience, and Pydantic validation on every row that comes back.

## Why async here

Fetching N symbols is I/O-bound: almost all the wall-clock time is spent waiting on the network, not on CPU. Under `asyncio`, while one request waits for Binance to respond, the event loop runs the others — so N requests overlap and total time approaches the slowest single request rather than their sum. For this workload async also edges out threads, because it does the same overlap on a single thread in user space, avoiding thread-creation overhead. The measured comparison is in [concurrency_benchmark.md](concurrency_benchmark.md).

## The fetch path

```
fetch_binance(symbols, interval, start)
  └─ _fetch_binance_raw_data(symbols, interval, limit)   # gather + semaphore
       └─ _validated_fetch_binance_one_symbol(...)        # per symbol: semaphore + validate
            └─ _fetch_binance_one_symbol_with_retry(...)   # @async_retry
                 └─ _fetch_binance_one_symbol(...)         # aiohttp GET + timeout
```

- **`fetch_binance`** is the public entry point. It converts the requested `interval` (`"1h"`, `"1d"`, …) into a `timedelta`, computes how many bars (`limit`) are needed to cover `start → now`, times the whole fetch, and converts the result to a tidy DataFrame (one row per symbol/bar, sorted by `open_time`).
- **`_fetch_binance_raw_data`** creates one shared `aiohttp.ClientSession`, builds a `Semaphore`, and `asyncio.gather`s one coroutine per symbol. It validates the `interval` against the allowed `binance_interval` literals before making any call.
- **`_validated_fetch_binance_one_symbol`** acquires the semaphore, fetches (with retry), then parses each row into a `BinanceDataRow`. Invalid rows are counted and skipped (logged as a warning) rather than aborting the whole symbol.
- **`_fetch_binance_one_symbol`** does the actual `session.get`, wrapped in `asyncio.timeout(settings.fetch_timeout_seconds)` and `resp.raise_for_status()`.

## Rate limiting with a Semaphore

`asyncio.gather` would otherwise launch *all* symbol requests simultaneously, which risks tripping Binance's rate limits. An `asyncio.Semaphore(max_number_concurrent_calls)` (default **5**, from [configuration.md](configuration.md)) caps how many requests are in flight at once: each coroutine must acquire the semaphore before fetching and releases it after. This is the async analogue of a thread-pool's `max_workers` — enough concurrency to be fast, bounded enough to be a good API citizen.

## Retry & backoff

The per-symbol fetch is wrapped by `@async_retry(max_retry=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))`. Transient network failures and timeouts are retried with exponentially growing waits (`delay * 2**(n-1)`), so a brief blip does not fail the run, while a persistent outage still surfaces after the attempts are exhausted. The decorator itself is documented in [decorators-and-utils.md](decorators-and-utils.md).

## Validation on the way in

`BinanceDataRow` is a Pydantic model mirroring Binance's kline schema, with `gt=0` constraints on every price/volume field. Rows are built by zipping the configured `binance.columns` names against each raw array, so a change in the API's column order is caught by configuration rather than hard-coded. This is the same boundary-validation principle as the file parser: the DataFrame that leaves this module is guaranteed well-formed. `_convert_binance_data_to_DataFrame` then drops the unused `ignore` column and tags rows with a categorical `symbol`.

## Cooperative, not preemptive

A note that trips people up: `asyncio` is *cooperative*. Control only passes to another coroutine at an `await`. The `await`s in this module — the network call and the `asyncio.sleep` in backoff — are exactly the points where waiting time is yielded to other symbols. There is no preemption, so a purely CPU-bound loop with no `await` would block the whole event loop. For this network-bound workload that is fine; for CPU-bound work, multiprocessing would be the right tool instead.

## See also

- [concurrency_benchmark.md](concurrency_benchmark.md) — sequential vs threading vs async, measured.
- [configuration.md](configuration.md) — `max_number_concurrent_calls`, `fetch_timeout_seconds`, Binance URL and columns.
- [decorators-and-utils.md](decorators-and-utils.md) — `@async_retry` internals.
