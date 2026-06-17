"""Kalman filtering for trading — minimum-variance recursive state estimation.

A Kalman filter tracks an unobserved state x and the covariance P of that estimate. Each step:
  PREDICT  x <- F x ;            P <- F P Fᵀ + Q       (model advances; uncertainty grows by Q)
  UPDATE   x <- x + K (y - H x); P <- (I - K H) P      (revise by Kalman gain K times innovation)
with K = P Hᵀ / (H P Hᵀ + R). Under Gaussian process noise Q and measurement noise R this is the
minimum-variance estimate. The Q/R ratio is the only real knob: high Q/R = trusts data (fast,
noisy); low Q/R = trusts the model (smooth, laggy).

Two trading workhorses:
  local_linear_trend  — a smoother/trend filter with LESS LAG than an SMA (adaptive, not fixed
                        window). Useful as a faster regime signal than the 200-SMA gate.
  dynamic_regression  — time-VARYING regression coefficients: dynamic market beta, or the
                        dynamic hedge ratio for pairs/stat-arb (Elliott-Van der Hoek-Malcolm 2005).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def local_linear_trend(y, q_level: float = 1e-3, q_slope: float = 1e-4, r: float = 1.0):
    """Local-linear-trend Kalman filter. State = [level, slope]; F = [[1,1],[0,1]]; H = [1,0].
    Returns (level, slope) arrays — the filtered estimate of the smooth level and its slope.
    Operate on a scale where `r` ~ the measurement-noise variance (e.g. log-price)."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([1.0, 0.0])
    Q = np.diag([q_level, q_slope])
    first = y[np.isfinite(y)][0] if np.isfinite(y).any() else 0.0
    x = np.array([first, 0.0])
    P = np.eye(2)
    lvl = np.full(n, np.nan)
    slp = np.full(n, np.nan)
    for t in range(n):
        x = F @ x
        P = F @ P @ F.T + Q
        if np.isfinite(y[t]):
            s = float(H @ P @ H + r)
            k = (P @ H) / s
            x = x + k * (y[t] - H @ x)
            P = P - np.outer(k, H) @ P
        lvl[t], slp[t] = x[0], x[1]
    return lvl, slp


def dynamic_regression(y, X, q: float = 1e-4, r: float = 1.0):
    """Time-varying linear regression via Kalman: y_t = X_t · beta_t + noise, beta a random walk.
    State = beta (one per regressor); F = I; H_t = X_t (row). Returns a [t x regressor] DataFrame
    of the filtered coefficients — e.g. a dynamic hedge ratio (X = [const, other_asset]) or a
    time-varying market beta (X = [const, market])."""
    y = np.asarray(y, dtype=float)
    Xm = np.asarray(X, dtype=float)
    if Xm.ndim == 1:
        Xm = Xm[:, None]
    n, k = Xm.shape
    beta = np.zeros(k)
    P = np.eye(k) * 1.0
    Q = np.eye(k) * q
    out = np.full((n, k), np.nan)
    for t in range(n):
        P = P + Q                                   # F = I: predict only inflates covariance
        h = Xm[t]
        if np.isfinite(y[t]) and np.isfinite(h).all():
            s = float(h @ P @ h + r)
            kk = (P @ h) / s
            beta = beta + kk * (y[t] - h @ beta)
            P = P - np.outer(kk, h) @ P
        out[t] = beta
    cols = list(X.columns) if isinstance(X, pd.DataFrame) else [f"b{i}" for i in range(k)]
    idx = X.index if isinstance(X, (pd.DataFrame, pd.Series)) else None
    return pd.DataFrame(out, index=idx, columns=cols)
