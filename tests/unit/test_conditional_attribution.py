import numpy as np
import pandas as pd

from trading_analysis.regime.conditional_attribution import (
    conditional_ic,
    drawdown_regime,
    trend_regime,
    vol_regime,
)


def _bench(n=400, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2016-01-04", periods=n, freq="B")
    # a series with a clear up-then-down shape to exercise all regimes
    drift = np.concatenate([np.full(n // 2, 0.0008), np.full(n - n // 2, -0.0010)])
    return pd.Series(100 * np.exp(np.cumsum(drift + rng.normal(0, 0.01, n))), index=idx)


def test_trend_regime_is_lagged_and_leakfree():
    s = _bench()
    full = trend_regime(s, window=50)
    # truncation invariance: the label at an interior date uses only prior data
    k = 300
    trunc = trend_regime(s.iloc[: k + 1], window=50)
    assert full.iloc[k] == trunc.iloc[k]
    # first value is NaN (shifted) — no peeking at its own bar
    assert pd.isna(full.iloc[0])


def test_vol_regime_buckets_by_fixed_threshold():
    s = _bench(seed=1)
    v = vol_regime(s, window=21, low=0.12, high=0.22)
    assert set(v.dropna().unique()) <= {"low_vol", "mid_vol", "high_vol"}
    assert v.isna().iloc[0]  # lagged


def test_drawdown_regime_flags_deep_declines():
    s = _bench(seed=2)
    dd = drawdown_regime(s, threshold=0.10)
    # the down-leg should produce some 'drawdown' labels
    assert (dd == "drawdown").sum() > 0
    assert dd.isna().iloc[0]


def test_conditional_ic_separates_by_regime():
    rng = np.random.default_rng(3)
    n, m = 300, 20
    idx = pd.date_range("2016-01-04", periods=n, freq="B")
    cols = [f"S{i}" for i in range(m)]
    factor = pd.DataFrame(rng.normal(size=(n, m)), index=idx, columns=cols)
    regime = pd.Series(["bull"] * (n // 2) + ["bear"] * (n - n // 2), index=idx)
    # forward return tracks the factor in bull, is pure noise in bear
    fwd = factor * 0.0
    bull = regime == "bull"
    fwd[bull] = factor[bull] * 0.02 + rng.normal(0, 0.01, (int(bull.sum()), m))
    fwd[~bull] = rng.normal(0, 0.01, (int((~bull).sum()), m))
    table = conditional_ic(factor, fwd, regime, bootstrap=True, seed=0)
    assert table.loc["bull", "mean_ic"] > 0.3          # strong IC where it should work
    assert abs(table.loc["bear", "mean_ic"]) < 0.1     # ~no IC where it shouldn't
    # the bull CI should exclude 0; the bear CI should straddle 0
    assert bool(table.loc["bull", "ci_excludes_0"])
    assert not bool(table.loc["bear", "ci_excludes_0"])
