import numpy as np
import pandas as pd

from trading_analysis.features.build import FEATURE_COLUMNS, build_features
from trading_analysis.features.importance import mdi_importance
from trading_analysis.features.stationarity import adf_pvalue, stationary_columns
from trading_analysis.features.timeseries import (
    half_life,
    hurst_exponent,
    variance_ratio,
)


def _ohlcv_one(symbol: str = "AAA", n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
    ts = pd.date_range("2023-01-02", periods=n, freq="B")
    vol = np.clip(1_000_000 + rng.normal(0, 100_000, n), 1.0, None)
    return pd.DataFrame(
        {
            "symbol": symbol,
            "ts": ts,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": vol,
            "adj_close": close,
            "bar": "1d",
        }
    )


# ---------- the acceptance test: build() is point-in-time / leak-free ----------


def test_build_features_is_point_in_time_leakfree():
    df = _ohlcv_one()
    cut = df["ts"].iloc[280]
    full = build_features(df)
    full_to_cut = full[full["ts"] <= cut].reset_index(drop=True)
    rebuilt_on_truncated = build_features(df[df["ts"] <= cut]).reset_index(drop=True)
    # Every feature value up to `cut` must be identical whether or not future bars exist.
    pd.testing.assert_frame_equal(full_to_cut, rebuilt_on_truncated)


def test_build_features_shape_and_columns():
    df = pd.concat([_ohlcv_one("AAA", seed=1), _ohlcv_one("BBB", seed=2)], ignore_index=True)
    feats = build_features(df)
    assert list(feats.columns) == ["symbol", "ts", *FEATURE_COLUMNS]
    assert set(feats["symbol"]) == {"AAA", "BBB"}
    assert len(feats) == len(df)
    # warm-up is NaN; always-defined features are populated after warm-up
    # (half_life/hurst/vratio may legitimately be NaN when their condition isn't met)
    core = ["ret_1d", "ret_5d", "px_to_sma20", "px_to_sma50", "rsi_14", "rvol_20", "vol_ratio_20"]
    assert feats[core].tail(20).notna().all().all()


def test_build_features_empty():
    assert build_features(pd.DataFrame()).empty


# ---------- mean-reversion statistics ----------


def test_hurst_orders_meanrev_below_persistent():
    rng = np.random.default_rng(1)
    n = 600
    rw = np.cumsum(rng.normal(0, 1, n))                  # random walk -> H ~ 0.5
    ou = np.empty(n)
    ou[0] = 0.0
    for i in range(1, n):
        ou[i] = 0.7 * ou[i - 1] + rng.normal(0, 1)       # mean-reverting level -> H < 0.5
    e = np.empty(n)
    e[0] = 0.0
    for i in range(1, n):
        e[i] = 0.6 * e[i - 1] + rng.normal(0, 1)         # positively autocorrelated increments
    persistent = np.cumsum(e)                            # super-diffusive -> H > 0.5
    h_ou, h_rw, h_pers = hurst_exponent(ou), hurst_exponent(rw), hurst_exponent(persistent)
    assert h_ou < h_rw < h_pers
    assert h_ou < 0.5 < h_pers


def test_half_life_meanreverting_positive_trend_nan():
    rng = np.random.default_rng(2)
    x = np.empty(300)
    x[0] = 100.0
    for i in range(1, 300):
        x[i] = 100 + 0.8 * (x[i - 1] - 100) + rng.normal(0, 1)  # OU, mean-reverting
    hl = half_life(x)
    assert np.isfinite(hl) and hl > 0
    assert np.isnan(half_life(100 + 0.5 * np.arange(300)))  # pure up-trend -> not MR


def test_variance_ratio_regimes():
    rng = np.random.default_rng(3)
    rw = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 600)))
    trend = 100 * np.exp(np.cumsum(0.003 + rng.normal(0, 0.001, 600)))
    assert 0.6 < variance_ratio(rw, q=2) < 1.5     # random walk ~ 1
    assert variance_ratio(trend, q=4) > 1.0        # persistent drift > 1


# ---------- selection tools ----------


def test_adf_pvalue_stationary_vs_unit_root():
    rng = np.random.default_rng(4)
    stationary = rng.normal(0, 1, 300)
    unit_root = np.cumsum(rng.normal(0, 1, 300))
    assert adf_pvalue(stationary) < 0.05
    assert adf_pvalue(unit_root) > 0.05


def test_stationary_columns_keeps_only_stationary():
    rng = np.random.default_rng(6)
    df = pd.DataFrame(
        {
            "symbol": "A",
            "ts": pd.date_range("2023-01-02", periods=300, freq="B"),
            "stat": rng.normal(0, 1, 300),
            "unitroot": np.cumsum(rng.normal(0, 1, 300)),
        }
    )
    kept, pvals = stationary_columns(df, alpha=0.05)
    assert "stat" in kept
    assert "unitroot" not in kept
    assert set(pvals.index) == {"stat", "unitroot"}


def test_mdi_importance_ranks_informative_first():
    rng = np.random.default_rng(5)
    n = 400
    good = rng.normal(0, 1, n)
    y = (good + rng.normal(0, 0.3, n) > 0).astype(int)
    X = pd.DataFrame({"good": good, "noise": rng.normal(0, 1, n)})
    imp = mdi_importance(X, y, n_estimators=120)
    assert imp.index[0] == "good"
    assert list(imp.columns) == ["mdi_mean", "mdi_std"]
