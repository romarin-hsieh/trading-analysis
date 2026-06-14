import numpy as np
import pandas as pd

from trading_analysis.backtest.costs import (
    amihud_illiquidity,
    expected_cost_drag_bps,
    implementation_shortfall,
    kyle_lambda,
    size_dependent_cost_bps,
)


def test_amihud_higher_when_volume_lower():
    n = 60
    r = np.random.default_rng(0).normal(0, 0.01, n)
    a_high = amihud_illiquidity(r, pd.Series(np.full(n, 1e8))).iloc[-1]
    a_low = amihud_illiquidity(r, pd.Series(np.full(n, 1e6))).iloc[-1]
    assert a_low > a_high > 0


def test_kyle_lambda_proxy_monotone():
    assert kyle_lambda(0.02, 1e6) > kyle_lambda(0.02, 1e8)  # less volume -> more impact


def test_size_cost_monotone_and_spread_floor():
    small = float(size_dependent_cost_bps(1e4, 1e8))   # tiny participation
    big = float(size_dependent_cost_bps(1e7, 1e8))     # 10% of ADV
    assert big > small
    assert abs(float(size_dependent_cost_bps(1.0, 1e8)) - 2.5) < 0.05  # ~half-spread as trade->0
    # sqrt-law: 4x the trade is 2x the impact component (above the spread floor)
    c1 = float(size_dependent_cost_bps(1e6, 1e8, half_spread_bps=0.0))
    c4 = float(size_dependent_cost_bps(4e6, 1e8, half_spread_bps=0.0))
    assert abs(c4 / c1 - 2.0) < 1e-6


def test_implementation_shortfall_sign():
    assert implementation_shortfall(100.0, 101.0, side=1) > 0   # bought above arrival = cost
    assert implementation_shortfall(100.0, 99.0, side=1) < 0    # bought cheaper = gain
    assert implementation_shortfall(100.0, 99.0, side=-1) > 0   # sold below arrival = cost


def test_expected_cost_drag_scales_with_turnover():
    d1 = expected_cost_drag_bps(50, 1e6, 1e8)
    d2 = expected_cost_drag_bps(100, 1e6, 1e8)
    assert d2 > d1 > 0
    assert abs(d2 / d1 - 2.0) < 1e-9
