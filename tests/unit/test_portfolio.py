import numpy as np
import pandas as pd
import pytest

from trading_analysis.portfolio.allocate import allocate, rebalance
from trading_analysis.portfolio.allocators import (
    equal_weight,
    max_sharpe,
    min_variance,
    risk_parity,
)
from trading_analysis.portfolio.covariance import james_stein_mean, shrunk_covariance
from trading_analysis.portfolio.sizing import kelly_leverage, vol_target_scale


def _returns(t=300, n=6, seed=0):
    rng = np.random.default_rng(seed)
    f = rng.normal(0, 0.01, (t, 1))                 # common factor -> correlated assets
    loadings = rng.uniform(0.5, 1.5, (1, n))
    data = f @ loadings + rng.normal(0, 0.008, (t, n))
    cols = [f"A{i}" for i in range(n)]
    return pd.DataFrame(data, index=pd.date_range("2022-01-03", periods=t, freq="B"), columns=cols)


def test_shrunk_cov_is_pd_and_better_conditioned():
    r = _returns(t=25, n=10, seed=1)                # T close to N -> sample ill-conditioned
    lw = shrunk_covariance(r, "ledoit_wolf").to_numpy()
    samp = shrunk_covariance(r, "sample").to_numpy()
    assert np.allclose(lw, lw.T)
    assert np.linalg.eigvalsh(lw).min() > 0         # positive definite
    assert np.linalg.cond(lw) < np.linalg.cond(samp)


def test_equal_weight():
    w = equal_weight(5)
    assert abs(w.sum() - 1) < 1e-12
    assert np.allclose(w, 0.2)


def test_min_variance_beats_equal_weight_variance():
    cov = shrunk_covariance(_returns(seed=2))
    s = cov.to_numpy()
    w = min_variance(cov)
    ew = equal_weight(len(cov))
    assert abs(w.sum() - 1) < 1e-6 and (w >= -1e-6).all()
    assert w @ s @ w <= ew @ s @ ew + 1e-12         # min-var <= equal-weight variance


def test_risk_parity_equalizes_risk_contributions():
    cov = shrunk_covariance(_returns(seed=3))
    s = cov.to_numpy()
    w = risk_parity(cov)
    rc = w * (s @ w)
    assert abs(w.sum() - 1) < 1e-6 and (w > 0).all()
    assert rc.std() / rc.mean() < 0.1               # contributions ~ equal


def test_max_sharpe_favours_high_sharpe_asset():
    rng = np.random.default_rng(4)
    t, n = 400, 5
    means = np.array([0.0016, 0.0003, 0.0003, 0.0003, 0.0003])
    vols = np.array([0.008, 0.016, 0.016, 0.016, 0.016])
    r = pd.DataFrame(rng.normal(means, vols, (t, n)), columns=[f"A{i}" for i in range(n)])
    w = max_sharpe(r.mean().to_numpy(), shrunk_covariance(r))
    assert abs(w.sum() - 1) < 1e-6 and (w >= -1e-6).all()
    assert int(np.argmax(w)) == 0                   # the high mean / low vol asset wins weight


def test_allocate_adapter_all_methods():
    r = _returns(seed=5)
    for method in ("equal_weight", "min_variance", "risk_parity", "max_sharpe"):
        w = allocate(r, method=method)
        assert list(w.index) == list(r.columns)
        assert abs(w.sum() - 1) < 1e-6
    assert np.allclose(allocate(r, method="equal_weight").to_numpy(), 1.0 / r.shape[1])


def test_sizing_kelly_and_vol_target():
    assert kelly_leverage(0.001, 0.0004, fraction=0.5, cap=2.0) == 0.5 * 0.001 / 0.0004
    assert kelly_leverage(0.001, 0.0) == 0.0                 # zero variance -> no leverage
    assert kelly_leverage(10.0, 0.0001, cap=1.0) == 1.0      # capped
    assert abs(vol_target_scale(0.20, 0.10, max_leverage=2.0) - 0.5) < 1e-9
    assert vol_target_scale(0.05, 0.10, max_leverage=1.0) == 1.0  # capped


# ---------- adversarial-review fixes (C1/C2/R1) ----------


def test_shrunk_cov_rejects_zero_variance_column():
    r = _returns(seed=7)
    r["A0"] = 0.0  # a constant column would silently capture min-var/risk-parity
    with pytest.raises(ValueError, match="zero-variance"):
        shrunk_covariance(r)


def test_james_stein_mean_shrinks_toward_grand_mean():
    rng = np.random.default_rng(8)
    means = np.array([0.002, -0.001, 0.0005, 0.001, -0.0008, 0.0003])
    r = pd.DataFrame(rng.normal(means, 0.01, (300, 6)), columns=[f"A{i}" for i in range(6)])
    js = james_stein_mean(r)
    raw = r.mean().to_numpy()
    grand = raw.mean()
    assert np.sum((js - grand) ** 2) < np.sum((raw - grand) ** 2)  # shrunk toward the grand mean


def test_rebalance_is_leak_free():
    r = _returns(t=400, seed=9)
    cut = r.index[300]
    full = rebalance(r, lookback=120, step=20, method="risk_parity")
    trunc = rebalance(r[r.index <= cut], lookback=120, step=20, method="risk_parity")
    common = full.index[full.index <= cut].intersection(trunc.index)
    assert len(common) > 0
    # weights at a rebalance date use only prior data, so future bars can't change them
    pd.testing.assert_frame_equal(full.loc[common], trunc.loc[common])
