# finlib

[![CI](https://github.com/simone-belli/finlib/actions/workflows/ci.yml/badge.svg)](https://github.com/simone-belli/finlib/actions/workflows/ci.yml)

Production-grade Python for financial data modelling.
- Strict type annotations (mypy --strict)
- Protocol-based dependency injection
- structured logging (structlog)
- property-based testing (Hypothesis)

## Installation

```bash
git clone https://github.com/simone-belli/finlib
cd finlib && poetry install
```

## Portfolio analysis: quick start

Reads historic trades from a JSONL file, fetches OHLCV market data from Binance, caches it locally as CSV, and computes portfolio analytics.

CLI inputs:

1. Trades JSONL file path

2. Quantisation frequency

```bash
poetry run finlib-pipeline ./examples/trades.jsonl 1h
```

### trades.jsonl format

See `examples/trades.jsonl`.

### Example output

```text
2026-07-27T07:28:54.333459Z [info     ] Trades loaded from repo        first_date=22-05-2026 last_date=03-07-2026 num_symbols=3 num_trades=221
2026-07-27T07:28:54.333717Z [info     ] Fetching market data           symbols=['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
2026-07-27T07:28:54.333933Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=ETHUSDT
2026-07-27T07:28:54.334235Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=BNBUSDT
2026-07-27T07:28:54.334334Z [info     ] Async fetching Binance data    interval=1h limit=1608 symbol=BTCUSDT
2026-07-27T07:28:54.679417Z [info     ] Fetched Binance data           elapsed=0.3s interval=1h symbols=['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
2026-07-27T07:28:54.729248Z [info     ] Storing market data            dataframe_shape=(3000, 12) size=36,000
2026-07-27T07:28:54.758581Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=ETHUSDT
2026-07-27T07:28:54.761593Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=BNBUSDT
2026-07-27T07:28:54.762791Z [info     ] adding intervals               last_timestamp='27-07-2026 17:59:59' symbol=BTCUSDT
2026-07-27T07:28:54.763832Z [info     ] New rows added to trade repo   count=0


Market summary
----------------------------------------------------------------------------------------------------

     symbol         timestamp   close rolling_vol rolling_sharpe
62  BNBUSDT  2026-07-28 00:00     575       0.170           0.23
62  BTCUSDT  2026-07-28 00:00  65,385       0.236           2.07
62  ETHUSDT  2026-07-28 00:00   1,969       0.336           3.70


Portfolio market value
----------------------------------------------------------------------------------------------------

                  BNBUSDT     BTCUSDT  ETHUSDT
2026-07-27 07:59  -88,575  -1,111,551  960,896


Portfolio cost basis
----------------------------------------------------------------------------------------------------

                  BNBUSDT    BTCUSDT   ETHUSDT
2026-07-03 23:21  124,373  1,173,382  -827,762


Portfolio PnL
----------------------------------------------------------------------------------------------------

                 BNBUSDT BTCUSDT  ETHUSDT
2026-07-27 07:59  35,798  61,831  133,134

```
