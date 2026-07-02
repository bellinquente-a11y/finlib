"""Trades and market data fetching and storing"""

from finlib import InFileTradeRepository, FileOHLCVRepo, Trade
from finlib.async_fetch import fetch_binance, binance_interval
import logging