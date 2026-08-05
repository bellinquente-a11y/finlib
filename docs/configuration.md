# Configuration

All runtime settings live in `config.py`, built on `pydantic-settings`. Configuration is typed, validated on load, and sourced from the environment or a `.env` file — there are no bare `os.getenv` calls scattered through the code.

## `Settings`

The top-level `Settings` model:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `environment` | `Literal["local", "production"]` | `"local"` | Selects console vs JSON logging in the pipeline. |
| `log_level` | `str` | `"INFO"` | Logging threshold. |
| `data_dir` | `Path` | `./data` | Where repositories and caches are written. |
| `fetch_timeout_seconds` | `float` | `10.0` | Per-request timeout for Binance fetches. |
| `binance` | `BinanceSettings` | (below) | Nested Binance configuration. |
| `api_key` | `SecretStr` | `""` | Expected `X-API-KEY` for the HTTP API. |

## `BinanceSettings` (nested)

| Field | Default | Purpose |
|---|---|---|
| `url` | Binance `/klines` endpoint | REST endpoint for OHLCV bars. |
| `columns` | 12-tuple | Names of the raw kline array fields, in order. |
| `columns_type` | dict | Expected type per raw column. |
| `max_number_concurrent_calls` | `5` | Semaphore size for concurrent fetches. |
| `max_retry` | `3` | Fetch retry budget. |

Defining `columns` in config rather than hard-coding them means the fetcher zips these names against Binance's positional arrays ([async-and-concurrency.md](async-and-concurrency.md)); if the API's column order changed, this is the one place to adjust.

## Sources and precedence

```python
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    env_nested_delimiter="__",
)
```

Values come from process environment variables first, then `.env`, then the field defaults. Nested settings use a `__` delimiter, so the Binance concurrency cap is set as:

```dotenv
# .env
ENVIRONMENT=local
LOG_LEVEL=INFO
DATA_DIR=./data
API_KEY=change-me
BINANCE__MAX_NUMBER_CONCURRENT_CALLS=5
```

`.env` is for local development and is git-ignored; production should inject real environment variables.

## `get_settings()` and caching

```python
@lru_cache(1)
def get_settings() -> Settings:
    return Settings()
```

`get_settings` is the single accessor used across the codebase (pipeline, `async_fetch`, API deps). The `lru_cache(1)` makes it a lazily-initialised singleton: settings are parsed once, on first use, and reused thereafter — so there is no repeated file/env parsing, and every caller sees the same instance. In tests, the cache can be cleared (`get_settings.cache_clear()`) or the dependency overridden to inject alternate settings.

## Secrets

`api_key` is a `SecretStr`, so its value is masked in reprs and logs and must be read explicitly via `.get_secret_value()` — which the API's `require_key` does inside a constant-time comparison ([http-api.md](http-api.md)). This prevents the key from leaking into a stray log line or exception message.

## See also

- [async-and-concurrency.md](async-and-concurrency.md) — consumes the Binance settings and timeout.
- [http-api.md](http-api.md) — consumes `api_key`.
- [pipeline.md](pipeline.md) — consumes `environment`, `log_level`, `data_dir`.
