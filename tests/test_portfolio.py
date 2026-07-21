import functools
import operator
import random
from datetime import datetime
from decimal import Decimal
from itertools import groupby

import pandas as pd
import pytest
from hypothesis import given
from pandas.testing import assert_series_equal
from pydantic_core import ValidationError

from finlib import Equity, Portfolio, Priceable, Trade, value_portfolio
from tests.strategies import ordered_trades_list


def test_portfolio_empty_trade_list_validation_error() -> None:
    with pytest.raises(ValidationError):
        _ = Portfolio(name="MyPortfolio", trades=[])


def test_value_portfolio_calculation() -> None:
    positions: dict[str, tuple[Priceable, float]] = {
        "BHP": (Equity("BHP", Decimal(130.0)), 10.0),
        "XYZ": (Equity("BHP", Decimal(150.0)), -10.0),
    }
    value = value_portfolio(positions)
    assert value == {"BHP": Decimal(1300), "XYZ": Decimal(-1500)}


def test_portfolio_len(sample_portfolio: Portfolio) -> None:
    assert len(sample_portfolio) == 6


@given(trades=ordered_trades_list())
def test_portfolio_hypothesis_len(trades: list[Trade]) -> None:
    portfolio = Portfolio(name="MyPortfolio", trades=trades)
    assert len(portfolio) == len(trades)


@pytest.mark.parametrize(
    "symbol,expected", [("BBB", True), ("CBA", False)], ids=["present", "missing"]
)
def test_portfolio_contains(sample_portfolio: Portfolio, symbol: str, expected: bool) -> None:
    assert (symbol in sample_portfolio) == expected


@given(trades=ordered_trades_list())
def test_portfolio_hypothesis_contains(trades: list[Trade]) -> None:
    portfolio = Portfolio(name="MyPortfolio", trades=trades)
    symbols = set([t.symbol for t in trades])
    for s in symbols:
        assert s in portfolio


def test_portfolio_name_missing(sample_trades: list[Trade]) -> None:
    with pytest.raises(ValidationError):
        _ = Portfolio(name="", trades=sample_trades)


def test_portfolio_iter_trades_order(sample_trades: list[Trade]) -> None:
    p = Portfolio(name="My Portfolio", trades=sample_trades)
    for i, trade in enumerate(p):
        assert trade == sample_trades[i]


def test_portfolio_get_item_out_of_range(sample_portfolio: Portfolio) -> None:
    with pytest.raises(IndexError):
        sample_portfolio[99]


def test_portfolio_notional_calculation(sample_portfolio: Portfolio) -> None:
    assert sample_portfolio.notional == pytest.approx(Decimal(1_281.41))


@given(trades=ordered_trades_list())
def test_portfolio_hypothesis_notional_calculation(trades: list[Trade]) -> None:
    portfolio = Portfolio(name="MyPortfolio", trades=trades)
    assert portfolio.notional == pytest.approx(sum([t.notional for t in trades]))


@given(trades=ordered_trades_list())
def test_portfolio_hypothesis_notional_calculation_independent_of_permutations(
    trades: list[Trade],
) -> None:
    portf1 = Portfolio(name="MyPortfolio", trades=trades)
    portf2 = Portfolio(name="MyPortfolio", trades=random.sample(trades, len(trades)))
    assert portf1.notional == pytest.approx(portf2.notional)


def test_portfolio_historic_position(sample_historic_portfolio: Portfolio) -> None:
    pos = sample_historic_portfolio.historic_position()
    exp_pos = pd.DataFrame(
        data=[
            [Decimal(0), Decimal(100)],
            [Decimal(-100), Decimal(100)],
            [Decimal(-100), Decimal(60)],
            [Decimal(-200), Decimal(60)],
            [Decimal(-200), Decimal(-30)],
        ],
        columns=["AAA", "BHP"],
        index=sorted([t.timestamp for t in sample_historic_portfolio]),
    )
    assert (pos == exp_pos).all().all()


@given(trades=ordered_trades_list())
def test_portfolio_historic_position_hypothesis(trades: list[Trade]) -> None:
    portfolio = Portfolio(name="MyPortfolio", trades=trades)
    sorted_trades = sorted(trades, key=lambda t: t.symbol)
    positions = {}
    for key, group in groupby(sorted_trades, key=lambda t: t.symbol):
        positions[key] = functools.reduce(operator.add, [t.lot_size() for t in group])
    exp_pos_df = pd.Series(positions)
    pos_df = portfolio.historic_position().iloc[-1].rename(None)
    assert_series_equal(pos_df, exp_pos_df)


@given(trades=ordered_trades_list())
def test_portfolio_final_position_hypothesis_independent_permutations_trades(
    trades: list[Trade],
) -> None:
    portf1 = Portfolio(name="MyPortfolio", trades=trades)
    portf2 = Portfolio(name="MyPortfolio", trades=random.sample(trades, len(trades)))
    assert (portf1.historic_position().iloc[-1] == portf2.historic_position().iloc[-1]).all()


def test_portfolio_historic_cost_basis(sample_historic_portfolio: Portfolio) -> None:
    cost = sample_historic_portfolio.historic_cost_basis()
    exp_cost = -pd.DataFrame(
        data=[
            [Decimal(0), Decimal(100 * 45)],
            [Decimal(-100 * 12), Decimal(100 * 45)],
            [Decimal(-100 * 12), Decimal(100 * 45 - 40 * 48)],
            [Decimal(-100 * 12 - 100 * 19), Decimal(100 * 45 - 40 * 48)],
            [Decimal(-100 * 12 - 100 * 19), Decimal(100 * 45 - 40 * 48 - 90 * 52)],
        ],
        columns=["AAA", "BHP"],
        index=sorted([t.timestamp for t in sample_historic_portfolio]),
    )
    assert (cost == exp_cost).all().all()


def test_historic_market_value_calculation(
    sample_historic_portfolio: Portfolio, sample_market_making_prices: pd.DataFrame
) -> None:
    mv = sample_historic_portfolio.historic_market_value(sample_market_making_prices)
    exp_mv = pd.DataFrame(
        data=[
            [Decimal(0), Decimal(0)],
            [Decimal(0), Decimal(51.4) * Decimal(100)],
            [Decimal(13.3) * Decimal(-100), Decimal(52.4) * Decimal(60)],
            [Decimal(14.3) * Decimal(-200), Decimal(53.4) * Decimal(-30)],
        ],
        columns=["AAA", "BHP"],
        index=sample_market_making_prices.index,
    )
    assert (mv == exp_mv).all().all()


def test_historic_pnl_calculation(
    sample_historic_portfolio: Portfolio, sample_market_making_prices: pd.DataFrame
) -> None:
    pnl = sample_historic_portfolio.historic_pnl(sample_market_making_prices)
    exp_pnl = pd.DataFrame(
        data=[
            [Decimal(0), Decimal(0)],
            [Decimal(0), Decimal(51.4) * Decimal(100) - Decimal(45.0) * Decimal(100)],
            [
                Decimal(13.3) * Decimal(-100) - Decimal(12.0) * Decimal(-100),
                Decimal(52.4) * Decimal(60)
                - Decimal(45.0) * Decimal(100)
                - Decimal(48) * Decimal(-40),
            ],
            [
                Decimal(14.3) * Decimal(-200)
                - Decimal(12.0) * Decimal(-100)
                - Decimal(19.0) * Decimal(-100),
                Decimal(53.4) * Decimal(-30)
                - Decimal(45.0) * Decimal(100)
                - Decimal(48) * Decimal(-40)
                - Decimal(52) * Decimal(-90),
            ],
        ],
        columns=["AAA", "BHP"],
        index=sample_market_making_prices.index,
    )
    assert (pnl == exp_pnl).all().all()


def test_historic_market_value_missing_symbol(
    sample_historic_portfolio: Portfolio, sample_market_making_prices: pd.DataFrame
) -> None:
    sample_historic_portfolio.trades.append(
        Trade(
            symbol="ZZZ",
            quantity=Decimal(10.0),
            price=Decimal(10.0),
            side="BUY",
            timestamp=datetime(2026, 2, 1, 13, 4, 56),
        )
    )
    with pytest.raises(ValueError, match="price missing for: ZZZ"):
        _ = sample_historic_portfolio.historic_market_value(sample_market_making_prices)
