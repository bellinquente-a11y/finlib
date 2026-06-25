from finlib.async_fetch import fetch_binance_data
from finlib.trade_repo import InMemoryTradeRepository, PortfolioService
from finlib.models import Trade
import asyncio

async def main() -> None:
    
    orders = [("BTCUSDT", "BUY", 10), 
              ("ETHUSDT", "SELL", 10), 
              ("BNBUSDT", "SELL", 10)]

    symbols = list(set([order[0] for order in orders])) 

    market_data = await fetch_binance_data(symbols, "1m")
    trades = [Trade(symbol=o[0], 
                    quantity=o[2], 
                    price=market_data[o[0]].close, 
                    side=o[1]) 
              for o in orders]

    trade_repo = InMemoryTradeRepository()
    service = PortfolioService(trade_repo)
    for trade in trades:
        service.record_trade(trade)
    summary = service.get_summary()

    for k, v in summary.items():
        print(f"{k:>10} {v["position"]:>10.2g} {v["notional"]:>10,.0f}")


if __name__ == "__main__":
    asyncio.run(main())

