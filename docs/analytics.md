# Analytics

The analytics modules turn price and trade data into numbers: VWAP, rolling volatility and Sharpe, maximum drawdown, resampling, and position sizing. They are pure functions over pandas/`Decimal` inputs — no I/O, no storage — which makes them easy to test in isolation and to reuse from both the pipeline and the API.

## VWAP — `analytics.py`

`calculate_vwap(bars)` folds a generator of `OHLCVBar`s into a single volume-weighted average price: `Σ(close · volume) / Σ(volume)`. It consumes the generator lazily (see [data-ingestion.md](data-ingestion.md)), so it never materialises the bars, and raises `ValueError` if total volume is zero.

`calculate_daily_vwap(path, symbol, min_volume=0)` is the file-facing wrapper. It streams one day's CSV, filters to `symbol`, and delegates to `calculate_vwap`. Two decorators wrap it: `@retry(max_attempts=3, ...)` re-runs on transient `ValueError`s, and a `timer` context manager logs how long the calculation took. This is a deliberate demonstration of layering cross-cutting concerns (retry, timing) around a pure core — see [decorators-and-utils.md](decorators-and-utils.md).

The module also has trade helpers: `group_trades_by_symbol(trades)` (sorted, grouped dict, with type/empty validation) and `trade_summary(trades)` (prints per-symbol count, quantity, notional).

## Rolling statistics — `historic_analytics.py`

Three functions operate on OHLCV DataFrames:

| Function | What it computes |
|---|---|
| `resample_dataframe(df, freq="D")` | Down-samples bars to `freq` with correct OHLCV aggregation: open=first, high=max, low=min, close=last, volume=sum. |
| `add_rolling_stats(df, intervals_per_year, window)` | Adds `returns`, `rolling_vol`, and `rolling_sharpe` columns. |
| `maximum_drawdown(returns)` | Largest peak-to-trough decline of a cumulative return series. |

### Annualisation, and why `intervals_per_year`

`add_rolling_stats` first computes simple returns via `close.pct_change()`, then a rolling-window standard deviation and mean. Both are scaled by `intervals_per_year ** 0.5`:

- **`rolling_vol`** = `√(intervals_per_year) · std(returns)` — volatility scales with the square root of time, so per-interval volatility is annualised by multiplying by the root of the number of intervals in a year.
- **`rolling_sharpe`** = `√(intervals_per_year) · mean(returns) / std(returns)` — the annualised (zero-risk-free-rate) reward-to-variability ratio.

`intervals_per_year` is what makes the function frequency-agnostic: the pipeline resamples to daily and passes `252` (trading days). The same function works for any bar frequency by passing the matching count.

### Maximum drawdown

`maximum_drawdown` builds a cumulative return index (`(1 + returns).cumprod()`), tracks its running peak (`cummax()`), and returns the minimum of `index/peak − 1`. The result is always `≤ 0`, and that invariant is exactly what the property-based tests assert (see [testing.md](testing.md)).

## Position sizing — `sizing.py`

`kelly_fraction(p, b, cap)` computes the capped Kelly stake `max(min(p − (1 − p)/b, cap), 0)` for win probability `p`, payoff ratio `b`, and an upper `cap`. It validates its inputs (`0 ≤ p ≤ 1`, `b > 0`, `cap > 0`) and floors the result at zero, so a negative-edge bet returns a zero stake rather than a short position.

## Trade reporting — `report.py`

`daily_trade_summary(trades)` groups trades by `(symbol, date)` and returns per-group `count` and `abs_notional`. Unlike `analytics.trade_summary`, it returns a dict (rather than printing), so it composes cleanly into other output.

## Portfolio analytics

Position, cost basis, market value, and PnL are methods on `Portfolio` itself rather than free functions — they are documented in [domain-model.md](domain-model.md). The pipeline's orchestration of all of this (pulling from repos, resampling, marking to market) lives in [pipeline.md](pipeline.md).
