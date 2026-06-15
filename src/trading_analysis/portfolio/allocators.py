"""Long-only allocators (weights >= 0, sum to 1) over a covariance / expected-return input.

equal_weight (the 1/N benchmark every optimizer must beat OOS net of turnover —
DeMiguel-Garlappi-Uppal 2009), min_variance, risk_parity (equal risk contribution),
and max_sharpe (tangency). Feed these a SHRUNK covariance (see covariance.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

_SUM_TO_ONE = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}


def _as_matrix(cov) -> np.ndarray:
    return cov.to_numpy(dtype=float) if isinstance(cov, pd.DataFrame) else np.asarray(cov, dtype=float)


def equal_weight(n_or_cov) -> np.ndarray:
    n = n_or_cov if isinstance(n_or_cov, int) else len(n_or_cov)
    return np.full(n, 1.0 / n)


def min_variance(cov) -> np.ndarray:
    s = _as_matrix(cov)
    n = s.shape[0]
    res = minimize(
        lambda w: float(w @ s @ w),
        np.full(n, 1.0 / n),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[_SUM_TO_ONE],
        options={"ftol": 1e-12, "maxiter": 500},
    )
    return res.x


def risk_parity(cov) -> np.ndarray:
    """Equal Risk Contribution via the convex log-barrier objective (Maillard 2010 / Spinu
    2013): minimize 0.5 w'Sw - (1/n) sum(log w) over w>0, then normalize. Its optimum
    satisfies w_i (Sw)_i = const, i.e. equal risk contributions — and it converges reliably
    (unlike the tiny-scale squared-deviation objective)."""
    s = _as_matrix(cov)
    n = s.shape[0]

    def obj(w):
        return 0.5 * float(w @ s @ w) - float(np.sum(np.log(w))) / n

    res = minimize(
        obj,
        np.full(n, 1.0 / n),
        method="SLSQP",
        bounds=[(1e-8, None)] * n,     # w > 0; no sum constraint (normalized after)
        options={"ftol": 1e-14, "maxiter": 2000},
    )
    return res.x / res.x.sum()


def max_sharpe(expected_returns, cov, rf: float = 0.0) -> np.ndarray:
    """Tangency portfolio (long-only). Must EARN its place vs equal_weight OOS net of turnover."""
    s = _as_matrix(cov)
    mu = np.asarray(expected_returns, dtype=float)
    n = len(mu)

    def neg_sharpe(w):
        vol = np.sqrt(float(w @ s @ w))
        return -(float(w @ mu) - rf) / vol if vol > 0 else 0.0

    res = minimize(
        neg_sharpe,
        np.full(n, 1.0 / n),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[_SUM_TO_ONE],
        options={"ftol": 1e-12, "maxiter": 500},
    )
    return res.x
