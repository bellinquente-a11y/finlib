from finlib import Trade
from datetime import date
from decimal import Decimal
from itertools import groupby

def daily_trade_summary(trades: list[Trade]) -> dict[tuple[str, date], dict[str, int | Decimal]]:
    """Return a dict with the daily summary of a list of Trade objects"""
    trades = sorted(trades, key=lambda t: (t.symbol, t.timestamp.date()))
    summary = {}
    for key, group in \
        groupby(trades, key=lambda t: (t.symbol, t.timestamp.date())):
        trades_group = list(group)
        summary[key] = {"count": len(trades_group), 
                        "abs_notional": sum(abs(t.notional) 
                        for t in trades_group)}
    return summary