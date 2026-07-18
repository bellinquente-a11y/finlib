from finlib.sizing import kelly_fraction
import pytest
from hypothesis import given, strategies as st

def test_kelly_criterion_calculation_without_cap():
    assert kelly_fraction(0.5, 2.0, 0.5) == pytest.approx(0.25)

def test_kelly_criterion_calculation_with_cap():
    assert kelly_fraction(0.9, 1.0, 0.5) == pytest.approx(0.5)

def test_kelly_criterion_probability_out_of_bounds_raises():
    with pytest.raises(ValueError, match="Input p of kelly_criterion needs to satisfy 0<=p<=1"):
        _ = kelly_fraction(1.1, 1.0, 0.5)
    with pytest.raises(ValueError, match="Input p of kelly_criterion needs to satisfy 0<=p<=1"):
        _ = kelly_fraction(-0.1, 1.0, 0.5)

def test_kelly_criterion_b_not_strictly_positive_raises():
    with pytest.raises(ValueError, match="Input b of kelly_criterion needs to satisfy b>0"):
        _ = kelly_fraction(0.5, 0, 0.5)

def test_kelly_criterion_non_positive_cap_raises():
    with pytest.raises(ValueError, match="Input cap of kelly_criterion needs to satisfy cap>0"):
        _ = kelly_fraction(0.5, 2, 0)

def test_kelly_criterion_no_hedge_output_zero():
    assert kelly_fraction(0.5, 1, 0.5) == pytest.approx(0)

@given(
    p=st.floats(min_value=0., max_value=1.),
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_criterion_output_between_0_and_1(p, b, cap):
    k = kelly_fraction(p,b,cap)
    assert k>=0 and k<=1 

@given(
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_criterion_p_eq_1_ouputs_cap(b, cap):
    assert kelly_fraction(1,b,cap) == min(cap, 1)