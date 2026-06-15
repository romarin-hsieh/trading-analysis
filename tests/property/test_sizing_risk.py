"""Property tests on sizing & risk: invariants must hold for any reasonable input."""


import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from trading_analysis.strategy.risk import apply_position_cap, drawdown_breach
from trading_analysis.strategy.sizing import fixed_fraction_size, kelly_fraction


@given(
    cash=st.floats(min_value=1.0, max_value=1e8, allow_nan=False, allow_infinity=False),
    fraction=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    price=st.floats(min_value=0.01, max_value=1e6, allow_nan=False),
)
@settings(max_examples=200)
def test_fixed_fraction_never_exceeds_cash(cash, fraction, price):
    qty = fixed_fraction_size(cash, fraction, price)
    assert qty >= 0
    assert qty * price <= cash + 1e-6


@given(
    win_prob=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    win_loss_ratio=st.floats(min_value=0.01, max_value=10.0, allow_nan=False),
    cap=st.floats(min_value=0.01, max_value=0.5, allow_nan=False),
)
@settings(max_examples=200)
def test_kelly_in_bounds(win_prob, win_loss_ratio, cap):
    f = kelly_fraction(win_prob, win_loss_ratio, cap)
    assert 0.0 <= f <= cap + 1e-9


def test_drawdown_breach_triggers():
    # 110 -> 80 is a -27.27% drawdown, well past the 20% threshold.
    eq = pd.Series([100, 110, 105, 80, 92], index=pd.date_range("2024-01-01", periods=5))
    assert drawdown_breach(eq, max_dd=0.20) == eq.index[3]


def test_drawdown_breach_safe():
    eq = pd.Series([100, 110, 105, 95, 92], index=pd.date_range("2024-01-01", periods=5))
    assert drawdown_breach(eq, max_dd=0.50) is None


def test_position_cap_clips_and_renormalizes():
    w = pd.DataFrame({"A": [0.6], "B": [0.6], "C": [0.6]})
    capped = apply_position_cap(w, cap=0.5)
    assert (capped.abs() <= 0.5 + 1e-9).all().all()
    # absolute weights sum to <= 1
    assert capped.abs().sum(axis=1).iloc[0] <= 1.0 + 1e-9
