# finlib

[![CI](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml/badge.svg)](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml)

Production-grade Python for financial data modelling.

## Features
- Type-safe Trade model with Pydantic v2
- Instrument hierarchy using ABCs and Protocols
- Streaming OHLCV pipeline - O(1) memory
- Portfolio valuation via structural subtyping
- Asynchronous fetching of data from Binance with retry on failure, per-request timeout and concurrency Semaphore
- Portfolio service trade management using repository pattern DI
- project settings managed via pydantic_settings
- A trade repository with swappable backend (in memory vs JSONL)
- An interval market-data repository with swappable backend (in memory vs CSV)


## Installation
  git clone https://github.com/bellinquente-a11y/finlib
  cd finlib && poetry install

## Portfolio analysis pipeline

This script provides historic analysis of the portfolio performance.

### Features
- Historic trades are read from a JSONL file.
- Market data inputs read from config and CLI.
- Historic market data fetched asynchronously and stored in a local CSV repository.
- Calculation of market data analysics.
- Calculation of portfolio analytics.
- Summary results printed on the CLI.

### CLI inputs

- string path of the trades.jsonl file
- quantisation frequency of the market data
- (optional) string path of the directory where the CSV market data is saved 

### `trades.jsonl` format

Below is the expected format of the JSONL file reporting the trades of the portfolio.

```text
{"symbol": "BTCUSDT", "quantity": "3", "price": "75539.5", "side": "BUY", "timestamp": "2026-05-22T07:08:47.107473Z"}
{"symbol": "BNBUSDT", "quantity": "117", "price": "653.22", "side": "BUY", "timestamp": "2026-05-22T14:37:17.848749Z"}
{"symbol": "BTCUSDT", "quantity": "2", "price": "76790.59", "side": "BUY", "timestamp": "2026-05-22T17:12:45.681453Z"}
```

### Quick start

```bash
poetry run finlib-pipeline ~/data/trades20260703.jsonl 1h
```

```text

INFO:finlib.pipeline.data:Loading trades from the trade repository
INFO:finlib.pipeline.data:Trades loaded    = 221
INFO:finlib.pipeline.data:Symbols          = BTCUSDT, BNBUSDT, ETHUSDT
INFO:finlib.pipeline.data:First time stamp = datetime.datetime(2026, 5, 22, 7, 8, 47, 107473, tzinfo=TzInfo(0))
INFO:finlib.pipeline.data:Fetching 1h market data for symbols: BTCUSDT, BNBUSDT, ETHUSDT from 2026-05-21 07:08:47.107473+00:00
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=BTCUSDT
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=BNBUSDT
2026-07-07 09:24:19 [info     ] Async fetching Binance data    interval=1h limit=1120 symbol=ETHUSDT
INFO:finlib.pipeline.data:Storing market data in OHLCV repository
2026-07-07 09:24:20 [info     ] adding intervals               symbol=BTCUSDT
2026-07-07 09:24:20 [info     ] adding intervals               symbol=BNBUSDT
2026-07-07 09:24:20 [info     ] adding intervals               symbol=ETHUSDT
2026-07-07 09:24:20 [info     ] Added rows to trade repo       count=3000


     symbol   close rolling_vol rolling_sharpe
38  BTCUSDT  62,583       0.285           0.64
39  BTCUSDT  63,144       0.286           1.10
39  ETHUSDT   1,781       0.399           2.66
39  BNBUSDT     575       0.276          -0.60
40  ETHUSDT   1,786       0.388           1.94
40  BTCUSDT  63,650       0.265           0.14
40  BNBUSDT     590       0.267          -0.92
41  BNBUSDT     587       0.267          -0.98
41  BTCUSDT  64,114       0.266           0.46
41  ETHUSDT   1,803       0.388           2.33


Market value
                 BNBUSDT    BTCUSDT   ETHUSDT
timestamp                                    
2026-07-06 23:59  90,412  1,089,938  -880,069

Cost basis
                   BNBUSDT     BTCUSDT  ETHUSDT
2026-07-03 23:21   24,373   1,173,382  -827,762

PnL
                  BNBUSDT  BTCUSDT  ETHUSDT
timestamp                                  
2026-07-06 23:59   33,961   83,444   52,307

Total PnL =  169,711
```

### Testing

```bash
poetry run pytest --cov=finlib.pipeline
```