"""Covariance estimation — shrinkage is MANDATED (docs/03 §O5).

The raw sample covariance is an "estimation-error maximizer" (Michaud 1989): mean-variance
optimizers load onto its most error-prone eigen-directions. Ledoit-Wolf shrinks it toward a
well-conditioned target, which is the single highest-value fix before any optimizer runs.
Every allocator in this package consumes a shrunk covariance by default; `sample` exists only
for comparison/tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.covariance import OAS, LedoitWolf


def shrunk_covariance(returns: pd.DataFrame, method: str = "ledoit_wolf") -> pd.DataFrame:
    """Estimate an [N x N] covariance from a [T x N] returns frame.

    method: 'ledoit_wolf' (default, identity-target LW), 'oas' (Oracle Approximating
    Shrinkage), or 'sample' (raw — for comparison only; do not feed to optimizers).
    """
    r = returns.dropna()
    cols = r.columns
    x = r.to_numpy(dtype=float)
    if x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError("need >=2 rows and >=1 column of returns")
    if method == "ledoit_wolf":
        cov = LedoitWolf().fit(x).covariance_
    elif method == "oas":
        cov = OAS().fit(x).covariance_
    elif method == "sample":
        cov = np.cov(x, rowvar=False, ddof=1)
    else:
        raise ValueError(f"unknown method: {method}")
    return pd.DataFrame(np.atleast_2d(cov), index=cols, columns=cols)
