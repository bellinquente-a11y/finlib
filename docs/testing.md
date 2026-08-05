# Testing

Tests live under `tests/`, mirroring the `src/finlib/` layout (`tests/api/`, `tests/pipeline/`, and module-level tests). The suite leans on two ideas: **parametrized fixtures** that run the same test against every repository backend, and **property-based tests** (Hypothesis) that assert invariants over generated inputs rather than hand-picked examples.

## Running the suite

```bash
poetry run pytest                 # all tests
poetry run pytest --cov=finlib    # with coverage (pytest-cov)
poetry run mypy src tests         # strict type check
poetry run ruff check .           # lint
poetry run pre-commit run --all-files
```

`pytest` is configured with `asyncio_mode = "auto"` (in `pyproject.toml`), so `async def` tests — e.g. those exercising `fetch_binance` — run without a per-test marker.

## Fixtures — `conftest.py`

The static fixtures build known trade/price sets for deterministic assertions: `sample_trades`, `sample_portfolio`, `sample_historic_portfolio`, and `sample_market_making_prices`.

The two most instructive fixtures are **parametrized across backends**:

```python
@pytest.fixture(params=("memory", "jsonl", "sql"))
def tmp_trade_repo(request, tmp_path) -> TradeRepository: ...

@pytest.fixture(params=("memory", "csv", "sqlite"))
def tmp_ohlcv_repo(request, tmp_path) -> OHLCVRepository: ...
```

Each yields a repository pre-loaded with identical data, once per backend. Any test that takes `tmp_trade_repo` automatically runs three times — in-memory, file, and SQLite — so a single test body verifies that all backends honour the Protocol identically. This is the practical payoff of structural subtyping ([repositories.md](repositories.md)): the contract is tested once and enforced everywhere. File and SQLite backends write under pytest's `tmp_path`, so runs are isolated and self-cleaning.

## Property-based testing — `strategies.py`

Hypothesis strategies generate valid domain objects:

- `trade_strategy()` — builds arbitrary valid `Trade`s (upper-case symbols, positive quantity/price, either side).
- `ordered_trades_list(min_trades, max_trades)` — a `@composite` strategy producing a chronologically ordered list of trades over a small set of symbols.

Instead of asserting a function's output on a few fixed inputs, property tests assert a **law** that must hold for *all* inputs, and Hypothesis searches for a counterexample (then shrinks it to a minimal failing case). Examples in this codebase:

- `maximum_drawdown(returns) <= 0` for any valid return series ([analytics.md](analytics.md)).
- Portfolio notional equals the sum of signed trade notionals, for any generated trade list.

**Why bother?** Hand-written examples encode the cases the author already thought of. Property tests probe the edges the author didn't — empty groups, extreme magnitudes, single-element series — which is where numeric code tends to break.

## What's covered

The tests span every layer: models and portfolio arithmetic, both repository families across all backends, the async fetcher, decorators and context managers, the analytics functions, the pipeline stages (`tests/pipeline/`), and the API routes (`tests/api/`, using FastAPI's test client via `httpx`). The whole tree — `src` and `tests` — is kept `mypy --strict` clean, so the type contracts the docs describe are verified on every run, not just by convention.

## See also

- [repositories.md](repositories.md) — the Protocol that the parametrized fixtures exercise.
- [architecture.md](architecture.md) — the design principles the property tests encode as executable checks.
