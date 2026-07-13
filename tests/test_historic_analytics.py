import pandas as pd
import pytest
from finlib.historic_analytics import resample_dataframe, add_rolling_stats, maximum_drawdown
from hypothesis import given, strategies as st

_COLUMNS = [
    "timestamp", "open", "high", "low", "close", "volume",
]

def _make_binance_df(rows):
    return pd.DataFrame(rows, columns=_COLUMNS)

_INTRADAY_ROWS = [
    [pd.Timestamp("2026-01-01 06:00"), 100.0, 110.0,  90.0, 105.0, 1000.0],
    [pd.Timestamp("2026-01-01 12:00"), 105.0, 115.0,  95.0, 108.0,  500.0],
    [pd.Timestamp("2026-01-02 00:00"), 108.0, 120.0, 100.0, 115.0,  800.0],
]


# --- resample_binance_data ---

def test_resample_preserves_columns():
    df = _make_binance_df(_INTRADAY_ROWS)
    result = resample_dataframe(df, freq="D")
    assert list(result.columns) == _COLUMNS

def test_resample_row_count():
    df = _make_binance_df(_INTRADAY_ROWS)
    result = resample_dataframe(df, freq="D")
    assert len(result) == 2

def test_resample_ohlcv_aggregation():
    df = _make_binance_df(_INTRADAY_ROWS)
    result = resample_dataframe(df, freq="D")
    day1 = result.iloc[0]
    assert day1["open"]   == pytest.approx(100.0)   # first open
    assert day1["high"]   == pytest.approx(115.0)   # max high
    assert day1["low"]    == pytest.approx(90.0)    # min low
    assert day1["close"]  == pytest.approx(108.0)   # last close
    assert day1["volume"] == pytest.approx(1500.0)  # summed volume

def test_resample_volume():
    df = _make_binance_df(_INTRADAY_ROWS)
    result = resample_dataframe(df, freq="D")
    assert result.iloc[0]["volume"] == 1500

def test_resample_open_time_is_first():
    df = _make_binance_df(_INTRADAY_ROWS)
    result = resample_dataframe(df, freq="D")
    assert result.iloc[0]["timestamp"] == pd.Timestamp("2026-01-02 00:00")


# --- add_rolling_stats ---

def _close_df(closes):
    return pd.DataFrame({"close": closes})

def test_rolling_stats_adds_columns():
    result = add_rolling_stats(_close_df([100.0, 110.0, 99.0, 109.0]), intervals_per_year=252, window=2)
    assert {"returns", "rolling_vol", "rolling_sharpe"}.issubset(result.columns)

def test_rolling_stats_preserves_original_columns():
    df = _close_df([100.0, 110.0, 99.0])
    df["extra"] = 1
    result = add_rolling_stats(df, intervals_per_year=4, window=2)
    assert "close" in result.columns
    assert "extra" in result.columns

def test_rolling_stats_returns_values():
    result = add_rolling_stats(_close_df([100.0, 110.0, 99.0]), intervals_per_year=4, window=2)
    assert pd.isna(result["returns"].iloc[0])
    assert result["returns"].iloc[1] == pytest.approx(0.1)
    assert result["returns"].iloc[2] == pytest.approx(-0.1)

def test_rolling_stats_vol_calculation():
    # returns at indices 1,2 = [0.1, -0.1]; sample std = sqrt(0.02); intervals_per_year=4
    result = add_rolling_stats(_close_df([100.0, 110.0, 99.0]), intervals_per_year=4, window=2)
    expected = 2.0 * (0.02 ** 0.5)  # sqrt(4) * sqrt(0.02)
    assert result["rolling_vol"].iloc[2] == pytest.approx(expected)

def test_rolling_stats_sharpe_zero_when_mean_return_zero():
    # returns [0.1, -0.1] have mean=0, so Sharpe=0
    result = add_rolling_stats(_close_df([100.0, 110.0, 99.0]), intervals_per_year=4, window=2)
    assert result["rolling_sharpe"].iloc[2] == pytest.approx(0.0)

def test_rolling_stats_first_rows_are_nan():
    result = add_rolling_stats(_close_df([100.0, 110.0, 99.0, 109.0]), intervals_per_year=252, window=3)
    assert pd.isna(result["rolling_vol"].iloc[0])
    assert pd.isna(result["rolling_vol"].iloc[1])

## max drawdown

def test_maximum_drawdown_zeros():
    returns = pd.Series(5*[0.])
    assert maximum_drawdown(returns)==0.

def test_maximum_drawdown_calc():
    cumpnl = [100., 120., 110., 80., 140., 130., 150.]
    returns = pd.Series([cumpnl[i]/cumpnl[i-1]-1. for i in range(1, len(cumpnl))])
    assert abs(maximum_drawdown(returns) - (80./120.-1.)) <1.e-14


@given(st.lists(st.floats(min_value=-0.5, max_value=0.5), min_size=1))
def test_maximum_drawdown_negative(returns):
    assert maximum_drawdown(pd.Series(returns))<=0.

@given(st.lists(st.floats(min_value=0., max_value=0.5), min_size=1))
def test_maximum_drawdown_zero_for_positive_returns(returns):
    assert maximum_drawdown(pd.Series(returns))==0.

@given(st.lists(st.floats(min_value=-0.5, max_value=0.5), min_size=1, max_size=1))
def test_maximum_drawdown_zero_for_one_elements(returns):
    assert maximum_drawdown(pd.Series(returns))==0.