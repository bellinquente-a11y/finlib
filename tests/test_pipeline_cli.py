
from unittest.mock import patch
from finlib.pipeline.cli import main
from finlib import Trade
from decimal import Decimal
from datetime import datetime
import pandas as pd

def test_main_wiring():
    summary = pd.DataFrame({"symbol": 5*["AAA"],
                       "close": 5*[Decimal(100)],
                       "rolling_vol": 5*[0.1],
                       "rolling_sharpe": 5*[1.0]})
    ts = datetime(2026,2,2,2,2,2)
    trade = Trade(symbol="AAA", quantity=10, price=100., side="BUY", timestamp=ts)

    with (patch("finlib.pipeline.data.fetch_trades") as mock_fetch_trades,
          patch("finlib.pipeline.data.fetch_market_data") as mock_fetch_market_data,
          patch("finlib.pipeline.data.store_market_data"),
          patch("finlib.pipeline.analytics.compute_market_summary", return_value = summary),
          patch("sys.argv", ["cli", "~/data/trades.jsonl", "1h"])
          ):
        mock_fetch_trades.return_value = (5*[trade], ["AAA"], ts)
        main()
    mock_fetch_trades.assert_called_once()
    mock_fetch_market_data.assert_called_once()