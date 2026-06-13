import numpy as np
import pandas as pd

from trading_analysis.backtest.metrics import (
    cagr,
    hit_rate,
    information_ratio,
    max_drawdown,
    sharpe,
)


def test_cagr_known_doubling():
    """5 years to double => CAGR ≈ 2^(1/5) - 1 ≈ 14.87%."""
    n = 252 * 5
    eq = pd.Series(np.linspace(100, 200, n))
    expected = 2 ** (1 / 5) - 1
    assert abs(cagr(eq) - expected) < 0.005


def test_max_drawdown_simple():
    eq = pd.Series([100, 120, 90, 95, 130])
    # Peak 120 -> trough 90 = -25%
    assert abs(max_drawdown(eq) - (-0.25)) < 1e-9


def test_sharpe_zero_vol():
    r = pd.Series([0.0, 0.0, 0.0])
    assert sharpe(r) == 0.0


def test_hit_rate():
    r = pd.Series([0.01, -0.005, 0.02, 0.0, -0.01])
    # Non-zero: 4 entries, 2 positive => 0.5
    assert hit_rate(r) == 0.5


def test_information_ratio_zero_when_identical():
    r = pd.Series([0.001, 0.002, -0.001])
    assert information_ratio(r, r) == 0.0
