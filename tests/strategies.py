from datetime import datetime, timedelta

from hypothesis import strategies as st

from finlib import Trade


def trade_strategy():
    return st.builds(
        Trade,
        symbol=st.text(alphabet=st.characters(categories=["Lu"]), min_size=1, max_size=10),
        quantity=st.floats(min_value=0, max_value=1e9, exclude_min=True),
        price=st.floats(min_value=0, max_value=1e9, exclude_min=True),
        side=st.sampled_from(['BUY', 'SELL']),
    )

@st.composite
def ordered_trades_list(draw, min_trades=1, max_trades=20):
    symbols = draw(st.lists(
        st.text(alphabet=st.characters(categories=["Lu"]), min_size=1, max_size=10),
        min_size=1, max_size=5, unique=True
    ))

    n_trades = draw(st.integers(min_value=min_trades, max_value=max_trades))

    timestamp = draw(st.datetimes(min_value=datetime(2020,1,1), max_value=datetime(2030,1,1)))
    res = []
    for _ in range(n_trades):
        offset = draw(st.integers(min_value=1, max_value=3600))
        timestamp += timedelta(offset)
        res.append(
            Trade(
                symbol=draw(st.sampled_from(symbols)),
                quantity=draw(st.floats(min_value=0, max_value=1e9, exclude_min=True)),
                price=draw(st.floats(min_value=0, max_value=1e9, exclude_min=True)),
                side=draw(st.sampled_from(['BUY', 'SELL'])),
                timestamp=timestamp
            )
        )

    return res

