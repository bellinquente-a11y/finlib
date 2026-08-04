from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from finlib.api.deps import require_key
from finlib.api.schemas import OHLCVBar
from finlib.async_fetch import binance_interval, fetch_binance

router = APIRouter()


@router.get("/market-data", dependencies=[Depends(require_key)])
async def market_data(
    symbols: Annotated[list[str], Query()], interval: binance_interval, start: datetime | str
) -> list[OHLCVBar]:
    res = await fetch_binance(symbols, interval, start)

    return [
        OHLCVBar(
            symbol=row["symbol"],
            open_time=row["open_time"],
            close_time=row["close_time"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
        )
        for row in res.to_dict("records")
    ]
