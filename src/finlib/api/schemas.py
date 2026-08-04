from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OHLCVBar(BaseModel):
    """API class for market data requests"""

    symbol: str = Field(..., min_length=1, max_length=10)
    open_time: datetime
    close_time: datetime
    open: Decimal = Field(..., gt=0)
    high: Decimal = Field(..., gt=0)
    low: Decimal = Field(..., gt=0)
    close: Decimal = Field(..., gt=0)
    volume: Decimal = Field(..., gt=0)
