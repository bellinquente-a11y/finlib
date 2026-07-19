from finlib.sizing import kelly_fraction
import pytest
from hypothesis import given, strategies as st, settings
import math

MAX_HYPOTHESIS_SAMPLES = 100

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

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@given(
    p=st.floats(min_value=0., max_value=1.),
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_criterion_output_between_0_and_1(p, b, cap):
    k = kelly_fraction(p,b,cap)
    assert k>=0 and k<=cap

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@given(
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_criterion_p_eq_1_ouputs_cap(b, cap):
    assert kelly_fraction(1,b,cap) == min(cap, 1)

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@given(
    p1=st.floats(min_value=0., max_value=1.),
    p2=st.floats(min_value=0., max_value=1.),
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_criterion_monotone_non_decreasing_in_p_at_fixed_b(p1, p2, b, cap):
    p_min, p_max = min(p1, p2), max(p1, p2)
    k_p_min = kelly_fraction(p_min, b, cap)
    k_p_max = kelly_fraction(p_max, b, cap)
    assert k_p_min<=k_p_max

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@st.composite
def p_b_resulting_in_negative_edge(draw):
    p = draw(st.floats(min_value=0, max_value=1, exclude_min=True, exclude_max=True))
    b_max = (1-p)/p
    b = draw(st.floats(min_value=0, max_value=b_max, exclude_min=True))
    return {"p": p, "b": b}

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@given(
    inputs = p_b_resulting_in_negative_edge(),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_fraction_non_positive_edge_result_zero(inputs, cap):
    assert kelly_fraction(inputs["p"], inputs["b"], cap) == pytest.approx(0)

@settings(max_examples=MAX_HYPOTHESIS_SAMPLES)
@given(
    p=st.floats(min_value=0., max_value=1.),
    b=st.floats(min_value=0, exclude_min=True),
    cap=st.floats(min_value=0, exclude_min=True)
)
def test_kelly_fraction_result_finite(p, b, cap):
    assert math.isfinite(kelly_fraction(p, b, cap))