# finlib

[![CI](https://github.com/bellinquente-a11y/finlib/actions/workflows/ci.yml/badge.svg)](...)

Production-grade Python for financial data modelling.

## Features
- Type-safe Trade model with Pydantic v2
- Instrument hierarchy using ABCs and Protocols
- Streaming OHLCV pipeline - O(1) memory
- Portfolio valuation via structural subtyping

## Installation
  git clone https://github.com/bellinquente-a11y/finlib
  cd finlib && poetry install

## Quick start
  from finlib import Trade, Equity
  from decimal import Decimal
  t = Trade(symbol='BHP', quantity=1000,
            price=Decimal('45.50'), side='BUY')
  print(t.notional)  # Decimal('45500.00')