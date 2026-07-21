import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from finlib.async_fetch import fetch_binance
from finlib.models import Trade
from finlib.trade_repo import InMemoryTradeRepository, PortfolioService

log = logging.getLogger(__name__)


async def main() -> None:

    log.info("Load market data")
    orders: list[tuple[str, Literal["BUY", "SELL"], float]] = [
        ("BTCUSDT", "BUY", 10),
        ("ETHUSDT", "SELL", 10),
        ("BNBUSDT", "SELL", 10),
    ]
    symbols = list(set([order[0] for order in orders]))
    market_data = await fetch_binance(symbols, "1m", datetime.now() - timedelta(minutes=5))

    log.info("Add trades to repo")
    trades = [
        Trade(
            symbol=o[0],
            quantity=Decimal(o[2]),
            price=market_data.query(f'symbol=="{o[0]}"')["close"].iloc[-1],
            side=o[1],
        )
        for o in orders
    ]

    trade_repo = InMemoryTradeRepository()
    service = PortfolioService(trade_repo)
    for trade in trades:
        service.record_trade(trade)

    log.info("Print portfolio summary")
    summary = service.get_summary()

    for k, v in summary.items():
        print(f"{k:>10} {v['position']:>10.2g} {v['notional']:>10,.0f}")


if __name__ == "__main__":
    asyncio.run(main())
