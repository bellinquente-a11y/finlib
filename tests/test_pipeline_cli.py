from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from finlib import Trade
from finlib.pipeline.cli import main


def test_main_wiring(tmp_path: Path) -> None:
    summary = pd.DataFrame(
        {
            "symbol": 5 * ["AAA"],
            "close": 5 * [Decimal(100)],
            "rolling_vol": 5 * [0.1],
            "rolling_sharpe": 5 * [1.0],
        }
    )
    pnl = pd.DataFrame([[Decimal(1)]], columns=["AAA"], index=[datetime(2026, 1, 1)])
    ts = datetime(2026, 2, 2, 2, 2, 2)
    trade = Trade(
        symbol="AAA", quantity=Decimal(10), price=Decimal(100.0), side="BUY", timestamp=ts
    )
    trades_path = tmp_path / "trades.jsonl"
    with trades_path.open("a") as f:
        f.write(trade.model_dump_json())

    with (
        patch("finlib.ohlcv_repo.FileOHLCVRepository.__init__", return_value=None),
        patch("finlib.pipeline.data.fetch_trades") as mock_fetch_trades,
        patch("finlib.pipeline.data.fetch_market_data") as mock_fetch_market_data,
        patch("finlib.pipeline.data.store_market_data"),
        patch("finlib.pipeline.analytics.compute_market_summary", return_value=summary),
        patch(
            "finlib.pipeline.analytics.compute_portfolio_performance_metrics",
            return_value=(pnl, pnl, pnl),
        ),
        patch("sys.argv", ["cli", str(trades_path), "1h"]),
    ):
        mock_fetch_trades.return_value = (5 * [trade], ["AAA"], ts)
        main()
    mock_fetch_trades.assert_called_once()
    mock_fetch_market_data.assert_called_once()
