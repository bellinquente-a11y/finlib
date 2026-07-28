"""CLI to run the finlib pipeline"""

import argparse
import asyncio
import logging
from datetime import timedelta
from pathlib import Path

import structlog

from finlib.config import get_settings
from finlib.ohlcv_repo import FileOHLCVRepository
from finlib.pipeline import analytics, data, output
from finlib.trade_repo import FileTradeRepository


def main() -> None:
    """Entry point for the finlib pipeline CLI.

    Parses a trade repository path and a market data frequency, fetches OHLCV
    data from Binance starting just before the first trade, stores it locally,
    then prints a market summary and portfolio performance tables (market value,
    cost basis, cumulative PnL) to stdout.
    """
    parser = argparse.ArgumentParser(
        description="Fetch and analyse trades and market data \
        from Binance"
    )
    parser.add_argument("trade_repo_path", help="Path of the JSONL trade repo")
    parser.add_argument("frequency", type=str, help="Market data quantisation frequency")
    args = parser.parse_args()

    settings = get_settings()

    # structlog config
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.environment == "production":
        renderer: structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer = (
            structlog.processors.JSONRenderer()
        )
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[settings.log_level]
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Create repo objects
    trade_repo = FileTradeRepository(Path(args.trade_repo_path))
    mkt_repo = FileOHLCVRepository(settings.data_dir / f"mkt_data_{args.frequency}.csv")

    # Fetch and store market data
    _, symbols, first_ts = data.fetch_trades(trade_repo)
    mkt_df = asyncio.run(
        data.fetch_market_data(symbols, args.frequency, first_ts - timedelta(days=1))
    )
    data.store_market_data(mkt_repo, mkt_df)

    # Compute market data analytics
    market_summary = analytics.compute_market_summary(mkt_repo, symbols, window=24)

    cols = ["close", "rolling_vol", "rolling_sharpe"]
    formatters = {
        "close": "{:,.0f}".format,
        "rolling_vol": "{:.3f}".format,
        "rolling_sharpe": "{:.2f}".format,
    }
    _headline_title("Market summary")
    output.print_market_summary(market_summary, cols, formatters)

    # Compute cumulative PnL of the portfolio
    cumpnl, market_value, cost_basis = analytics.compute_portfolio_performance_metrics(
        trade_repo, mkt_repo
    )
    _headline_title("Portfolio market value")
    output.print_trading_summary(market_value, "{:,.0f}", "%Y-%m-%d %H:%M")

    _headline_title("Portfolio cost basis")
    output.print_trading_summary(cost_basis, "{:,.0f}", "%Y-%m-%d %H:%M")

    _headline_title("Portfolio PnL")
    output.print_trading_summary(cumpnl, "{:,.0f}", "%Y-%m-%d %H:%M")
    print("\n")


def _headline_title(title: str) -> None:
    full_str = f"\n\n{title}\n{100 * '-'}\n"
    print(full_str)


if __name__ == "__main__":
    main()
