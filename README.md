# finlib

[![CI](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml/badge.svg)](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml)

Production-grade Python for financial data modelling.

## Features
- Type-safe Trade model with Pydantic v2
- Instrument hierarchy using ABCs and Protocols
- Streaming OHLCV pipeline - O(1) memory
- Portfolio valuation via structural subtyping
- asynchronous fetching of data from Binance
- Portfolio service trade management using repository pattern DI
- project settings managed via pydantic_settings

## Installation
  git clone https://github.com/bellinquente-a11y/finlib
  cd finlib && poetry install

## Quick start

```python
from finlib import Trade, Equity, PortfolioService
from finlib.trade_repo import InMemoryTradeRepository
from decimal import Decimal
t = Trade(symbol='BHP', quantity=1000,
            price=Decimal('45.50'), side='BUY')
trade_repo = InMemoryTradeRepository()
service = PortfolioService(trade_repo)
service.record_trade(t)
summary = service.get_summary()
```