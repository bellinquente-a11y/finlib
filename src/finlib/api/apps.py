from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from finlib.api.deps import MKT_DATA_DB_PATH, TRADES_DB_PATH
from finlib.api.routes import market_data, portfolio
from finlib.config import get_settings
from finlib.ohlcv_repo import FileOHLCVRepository, SQLiteOHLCVRepository
from finlib.trade_repo import FileTradeRepository, SQLiteTradeRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db_dir = get_settings().data_dir
    db_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[3]
    file_trade_repo_path = repo_root / "examples" / "trades.jsonl"
    file_mkt_repo_path = repo_root / "examples" / "mkt_data_1h.csv"

    # Make sure the files exist
    if not file_trade_repo_path.exists():
        raise ValueError(f"Missing file {file_trade_repo_path}")
    if not file_mkt_repo_path.exists():
        raise ValueError(f"Missing file {file_mkt_repo_path}")

    # Remove existing databases
    TRADES_DB_PATH.unlink(missing_ok=True)
    MKT_DATA_DB_PATH.unlink(missing_ok=True)

    # Clone repos
    trade_repo_file = FileTradeRepository(file_trade_repo_path)
    trade_repo_db = SQLiteTradeRepository(TRADES_DB_PATH)
    for trade in trade_repo_file.get_all():
        trade_repo_db.add(trade)

    mkt_repo_file = FileOHLCVRepository(file_mkt_repo_path)
    mkt_repo_db = SQLiteOHLCVRepository(MKT_DATA_DB_PATH)
    for symbol in mkt_repo_file.symbols():
        mkt_repo_db.add_intervals_batch(mkt_repo_file.get_data(symbol))
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(market_data.router)
app.include_router(portfolio.router)
