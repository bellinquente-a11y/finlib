from datetime import date, datetime
from decimal import Decimal

from finlib import Trade
from finlib.report import daily_trade_summary


def test_daily_trade_summary_calculation() -> None:
    t1 = Trade(
        symbol="BBB",
        quantity=Decimal(10),
        price=Decimal(100),
        side="BUY",
        timestamp=datetime(2026, 6, 1, 2, 0, 0),
    )
    t2 = Trade(
        symbol="AAA",
        quantity=Decimal(10),
        price=Decimal(100),
        side="SELL",
        timestamp=datetime(2026, 6, 2, 3, 0, 0),
    )
    t3 = Trade(
        symbol="AAA",
        quantity=Decimal(10),
        price=Decimal(100),
        side="BUY",
        timestamp=datetime(2026, 6, 3, 4, 0, 0),
    )
    summary = daily_trade_summary([t1, t2, t3])
    assert summary == {
        ("AAA", date(2026, 6, 2)): {"count": 1, "abs_notional": Decimal(1000)},
        ("AAA", date(2026, 6, 3)): {"count": 1, "abs_notional": Decimal(1000)},
        ("BBB", date(2026, 6, 1)): {"count": 1, "abs_notional": Decimal(1000)},
    }
