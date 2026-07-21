from datetime import datetime
from decimal import Decimal

from finlib.trade_repo import PortfolioService, TradeRepository


def test_trade_repo_get_symbols(tmp_trade_repo: TradeRepository) -> None:
    assert tmp_trade_repo.get_all_symbols() == {"AAA", "BBB"}


def test_trade_repo_get_timestamp(tmp_trade_repo: TradeRepository) -> None:
    assert tmp_trade_repo.get_extreme_timestamps() == (
        datetime(2026, 2, 1, 13, 4, 56),
        datetime(2026, 4, 1, 13, 4, 56),
    )
    assert tmp_trade_repo.get_extreme_timestamps("AAA") == (
        datetime(2026, 4, 1, 13, 4, 56),
        datetime(2026, 4, 1, 13, 4, 56),
    )
    assert tmp_trade_repo.get_extreme_timestamps("BBB") == (
        datetime(2026, 2, 1, 13, 4, 56),
        datetime(2026, 3, 1, 13, 4, 56),
    )


def test_portfolio_service_position_calculation(tmp_trade_repo: TradeRepository) -> None:
    ps = PortfolioService(tmp_trade_repo)
    assert ps.get_position("BBB") == Decimal(-20.0)


def test_portfolio_service_summary_calculation(tmp_trade_repo: TradeRepository) -> None:
    ps = PortfolioService(tmp_trade_repo)
    assert ps.get_summary() == {
        "AAA": {"position": Decimal(-15), "notional": Decimal(-15_000)},
        "BBB": {"position": Decimal(-20), "notional": Decimal(-20_000)},
    }
