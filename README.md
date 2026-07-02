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

## Pipeline

The pipeline provides historic analysis of the portfolio performance.

### Features
- Historic trades are read from a JSONL file.
- Market data inputs read from config.
- Historic market data fetched asynchronously and stored in a local CSV repository.
- Calculation of market data analysics.
- Calculation of portfolio analytics.
- Summary results printed on the CLI.

### `trades.jsonl` format

```text
{"symbol":"BBB","quantity":"10","price":"1000","side":"BUY","timestamp":"2026-06-30T01:14:46.306031Z"}
{"symbol":"BBB","quantity":"30","price":"1000","side":"SELL","timestamp":"2026-06-30T01:14:46.306152Z"}
{"symbol":"AAA","quantity":"15","price":"1000","side":"SELL","timestamp":"2026-06-30T01:14:46.306192Z"}
```

### Quick start

Input the JSONL trades file path as a CLI argument.

```bash
poetry run python -m finlib.pipeline ~/data/my_trades.jsonl