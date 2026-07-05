"""CLI to run the finlib pipeline"""

from finlib.pipeline import data, analytics
import asyncio
import logging
import argparse
from finlib.config import get_settings
from finlib.ohlcv_repo import FileOHLCVRepo
from finlib.trade_repo import InFileTradeRepository
from pathlib import Path
from datetime import timedelta

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and analyse trades and market data from Binance")
    parser.add_argument("trade_repo_path", help="Path of the JSONL trade repo")
    parser.add_argument("frequency", type=str, help="Market data quantisation frequency")
    args = parser.parse_args()

    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    # Create repo objects
    trade_repo = InFileTradeRepository(Path(args.trade_repo_path))
    mkt_repo = FileOHLCVRepo(settings.data_dir / f"mkt_data_{args.frequency}.csv")

    # Fetch and store market data
    _, symbols, first_ts = data.fetch_trades(trade_repo)
    mkt_df = asyncio.run(data.fetch_market_data(symbols, args.frequency, first_ts-timedelta(days=1)))
    data.store_market_data(mkt_repo, mkt_df)

    # Compute analytics
    summary = analytics.compute_market_summary(mkt_repo, symbols, window=24)

    cols = ['symbol', 'close', 'rolling_vol', 'rolling_sharpe']
    print(summary[cols].dropna().tail(10).to_string())


if __name__=="__main__":
    main()