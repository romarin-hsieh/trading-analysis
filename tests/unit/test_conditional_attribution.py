import numpy as np
import pandas as pd

from trading_analysis.regime.conditional_attribution import (
    applicability_map,
    bh_reject,
    conditional_ic,
    drawdown_regime,
    trend_regime,
    vol_regime,
)


def _bench(n=400, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2016-01-04", periods=n, freq="B")
    drift = np.concatenate([np.full(n // 2, 0.0008), np.full(n - n // 2, -0.0010)])
    return pd.Series(100 * np.exp(np.cumsum(drift + rng.normal(0, 0.01, n))), index=idx)


def test_trend_regime_is_lagged_and_leakfree():
    s = _bench()
    full = trend_regime(s, window=50)
    k = 300
    trunc = trend_regime(s.iloc[: k + 1], window=50)
    assert full.iloc[k] == trunc.iloc[k]
    assert pd.isna(full.iloc[0])           # warmup + lag => NaN, never peeks at its own bar


def test_vol_regime_buckets_by_fixed_threshold():
    v = vol_regime(_bench(seed=1), window=21, low=0.12, high=0.22)
    assert set(v.dropna().unique()) <= {"low_vol", "mid_vol", "high_vol"}
    assert v.isna().iloc[0]


def test_drawdown_regime_flags_deep_declines():
    dd = drawdown_regime(_bench(seed=2), threshold=0.10)
    assert (dd == "drawdown").sum() > 0
    assert dd.isna().iloc[0]


def test_bh_reject_controls_fdr():
    # classic BH example: smallest p passes, large ones rejected
    rej = bh_reject([0.001, 0.5, 0.04, 0.2], alpha=0.10)
    assert rej.tolist() == [True, False, True, False]
    assert not bh_reject([0.6, 0.7], alpha=0.10).any()        # all null -> none rejected
    assert not bh_reject([np.nan, np.nan]).any()              # NaN never rejected


def test_conditional_ic_separates_by_regime_with_fdr():
    rng = np.random.default_rng(3)
    n, m = 300, 20
    idx = pd.date_range("2016-01-04", periods=n, freq="B")
    cols = [f"S{i}" for i in range(m)]
    factor = pd.DataFrame(rng.normal(size=(n, m)), index=idx, columns=cols)
    regime = pd.Series(["bull"] * (n // 2) + ["bear"] * (n - n // 2), index=idx)
    fwd = factor * 0.0
    bull = regime == "bull"
    fwd[bull] = factor[bull] * 0.02 + rng.normal(0, 0.01, (int(bull.sum()), m))
    fwd[~bull] = rng.normal(0, 0.01, (int((~bull).sum()), m))
    table = conditional_ic(factor, fwd, regime, horizon=1, seed=0)
    assert table.loc["bull", "mean_ic"] > 0.3
    assert abs(table.loc["bear", "mean_ic"]) < 0.1
    assert {"n_eff", "pvalue", "significant_fdr"}.issubset(table.columns)
    # the FDR-corrected decision flag: apply in bull, NOT in bear
    assert bool(table.loc["bull", "significant_fdr"])
    assert not bool(table.loc["bear", "significant_fdr"])


def test_conditional_ic_empty_bucket_no_keyerror():
    # benchmark/regime with no date overlap must return an empty frame, not raise
    idx = pd.date_range("2020-01-01", periods=50, freq="B")
    factor = pd.DataFrame(np.random.default_rng(0).normal(size=(50, 6)), index=idx)
    fwd = factor * 0.0
    regime = pd.Series("bull", index=pd.date_range("2010-01-01", periods=50, freq="B"))
    table = conditional_ic(factor, fwd, regime)
    assert table.empty


def test_applicability_map_runs_family_fdr():
    rng = np.random.default_rng(4)
    n, m = 400, 15
    idx = pd.date_range("2016-01-04", periods=n, freq="B")
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.012, (n, m)), axis=0)), index=idx,
                      columns=[f"S{i}" for i in range(m)])
    factor = np.log(px).shift(5) - np.log(px).shift(21)
    bench = px.mean(axis=1)
    amap = applicability_map(factor, px, bench, horizon=5, seed=0)
    assert set(amap) == {"trend", "vol", "drawdown"}
    for t in amap.values():
        assert "significant_fdr" in t.columns
