"""Mean-reversion / persistence statistics (rolling, causal).

Hurst exponent, half-life of mean reversion, and the Lo-MacKinlay variance ratio.
Reimplemented from standard formulas (extraction reference: letianzj/QuantResearch
`mean_reversion.py`). Each scalar function takes a 1-D array; the `rolling_*` wrappers
apply it over a trailing window (`min_periods=window`), so the result at bar t uses
only the prior `window` bars — point-in-time safe.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def hurst_exponent(ts, min_lag: int = 2, max_lag: int = 20) -> float:
    """H from the lagged-difference dispersion: std(ts[lag:]-ts[:-lag]) ~ lag**H.
    H>0.5 trending/persistent, ~0.5 random walk, <0.5 mean-reverting."""
    ts = np.asarray(ts, dtype=float)
    if len(ts) < max_lag + 2 or not np.all(np.isfinite(ts)):
        return np.nan
    lags = np.arange(min_lag, max_lag)
    tau = np.array([np.std(ts[lag:] - ts[:-lag]) for lag in lags])
    if np.any(tau <= 0):
        return np.nan
    return float(np.polyfit(np.log(lags), np.log(tau), 1)[0])


def half_life(ts) -> float:
    """Half-life of mean reversion via OLS of Δx on lagged x (`-ln2/beta`).
    NaN when not mean-reverting (beta >= 0)."""
    ts = np.asarray(ts, dtype=float)
    if len(ts) < 10 or not np.all(np.isfinite(ts)):
        return np.nan
    lag = ts[:-1]
    delta = ts[1:] - ts[:-1]
    xmat = np.column_stack([np.ones(len(lag)), lag])
    beta, *_ = np.linalg.lstsq(xmat, delta, rcond=None)
    if beta[1] >= -1e-8:  # not meaningfully mean-reverting (also guards constant-delta trends)
        return np.nan
    return float(-np.log(2.0) / beta[1])


def variance_ratio(ts, q: int = 2) -> float:
    """Lo-MacKinlay VR(q) on log prices: Var(q-period rtn)/(q·Var(1-period rtn)).
    ~1 random walk, >1 trending, <1 mean-reverting."""
    ts = np.asarray(ts, dtype=float)
    if len(ts) < 2 * q + 2 or not np.all(np.isfinite(ts)) or np.any(ts <= 0):
        return np.nan
    r = np.diff(np.log(ts))
    var1 = np.var(r, ddof=1)
    if var1 == 0:
        return np.nan
    rq = np.convolve(r, np.ones(q), mode="valid")  # q-period summed returns
    return float(np.var(rq, ddof=1) / (q * var1))


def _rolling(series: pd.Series, window: int, func) -> pd.Series:
    return series.rolling(window, min_periods=window).apply(func, raw=True)


def rolling_hurst(close: pd.Series, window: int = 100, max_lag: int = 20) -> pd.Series:
    return _rolling(close, window, lambda x: hurst_exponent(x, max_lag=max_lag))


def rolling_half_life(close: pd.Series, window: int = 60) -> pd.Series:
    return _rolling(close, window, half_life)


def rolling_variance_ratio(close: pd.Series, window: int = 40, q: int = 2) -> pd.Series:
    return _rolling(close, window, lambda x: variance_ratio(x, q=q))
