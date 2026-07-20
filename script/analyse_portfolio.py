import logging
import sys
from decimal import Decimal
from pathlib import Path

from finlib import Equity, value_portfolio
from finlib.context_managers import timer
from finlib.data import stream_ohlcv, stream_trades

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main(trades_csv: Path, prices_csv: Path) -> None:
    log.info('Loading trades...')
    trades = stream_trades(trades_csv)

    lot_size = {}
    for trade in trades:
        if trade.symbol not in lot_size:
            lot_size[trade.symbol] = trade.lot_size()
        else:
            lot_size[trade.symbol] += trade.lot_size()

    log.info('Getting EOD price')
    bars = stream_ohlcv(prices_csv, min_volume=1)
    eod_price = {}
    for bar in bars:
        eod_price[bar.symbol] = bar.close

    log.info('Generate portfolio...')
    positions = {}
    for symbol in lot_size.keys():
        if lot_size[symbol] == Decimal(0):
            continue
        if symbol not in eod_price:
            raise RuntimeError(f"Missing symbol {symbol} in market data file")
        positions[symbol] = (Equity(symbol, eod_price[symbol]), lot_size[symbol])

    log.info('Valuing portfolio...')
    with timer('Portfolio valuation'):
        values = value_portfolio(positions)

    print('=== PORTFOLIO SUMMARY ===')
    for symbol, value in sorted(values.items()):
        print(f'  {symbol:10s}: ${value:>15,.2f}')
    print(f'  TOTAL     : ${sum(values.values()):>15,.2f}')

if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))