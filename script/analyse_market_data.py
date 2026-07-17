from finlib.async_fetch import fetch_binance
import logging
from finlib.ohlcv_repo import FileOHLCVRepository
from pathlib import Path
from datetime import timedelta, datetime, timezone
import pandas as pd
from finlib.historic_analytics import add_rolling_stats
import sys
import subprocess
import asyncio

log = logging.getLogger(__name__)

async def main(filepath: str) -> None:
    
    repo_path = Path(filepath)

    # delete existing repo file
    if repo_path.exists():
        subprocess.run(["rm", filepath])

    repo = FileOHLCVRepository(Path(repo_path))

    log.info("Save market data in OHLCV repo")
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    df = await fetch_binance(symbols, "1h", datetime.now() - timedelta(days=30))
    repo.add_intervals_batch(df, {"close_time": "timestamp"})

    log.info("Extract market data from repo")
    mdata = pd.DataFrame()
    for s in symbols:
        new_df = repo.get_data(s, start=datetime.now(tz=timezone.utc)-timedelta(days=10)).sort_values("timestamp")
        new_df = add_rolling_stats(new_df, 24*252, 24*5)
        mdata = pd.concat((mdata, new_df), axis=0)

    mdata = mdata.sort_values(["timestamp", "symbol"])

    log.info("Print rolling summary stats")
    
    print(mdata.tail(10))


if __name__=="__main__":
    asyncio.run(main(sys.argv[1]))