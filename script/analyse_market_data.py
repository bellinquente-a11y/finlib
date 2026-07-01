from finlib.historic_fetch import load_binance_data_per_product
import logging
from finlib.ohlcv_repo import FileOHLCVRepo
from pathlib import Path
from datetime import timedelta, datetime, timezone
import pandas as pd
from finlib.historic_analytics import add_rolling_stats
import sys
import subprocess

log = logging.getLogger(__name__)

def main(filepath: str) -> None:
    
    repo_path = Path(filepath)

    # delete existing repo file
    if repo_path.exists():
        subprocess.run(["rm", filepath])

    repo = FileOHLCVRepo(Path(repo_path))

    log.info("Save market data in OHLCV repo")
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    for s in symbols:
        df = (
            load_binance_data_per_product(s, "1h", 1_000)
            .assign(
                symbol=lambda d: s,
                timestamp=lambda d: d["close_time"]
            )
            .astype({"symbol": "category"})
            [["symbol", "timestamp", "open", "high", "low", "close", "volume"]]
        )
        repo.add_intervals_batch(df)

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
    main(sys.argv[1])