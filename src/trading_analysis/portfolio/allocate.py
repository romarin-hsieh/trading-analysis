"""Unified allocation adapter — the single entry point that feeds vectorbt sizing.

`allocate(returns, method=...)` ALWAYS estimates a SHRUNK covariance first (O5 mandate),
then computes long-only weights by the chosen method. Swap `method` without touching the
rest of the pipeline. The output is a weights Series indexed by asset.
"""

from __future__ import annotations

import pandas as pd

from trading_analysis.portfolio.allocators import (
    equal_weight,
    max_sharpe,
    min_variance,
    risk_parity,
)
from trading_analysis.portfolio.covariance import shrunk_covariance

_METHODS = ("equal_weight", "min_variance", "risk_parity", "max_sharpe")


def allocate(
    returns: pd.DataFrame,
    method: str = "risk_parity",
    cov_method: str = "ledoit_wolf",
    expected_returns=None,
    rf: float = 0.0,
) -> pd.Series:
    """Return long-only weights (sum=1) for the asset columns of `returns`.

    method: equal_weight | min_variance | risk_parity | max_sharpe.
    cov_method: shrinkage estimator (default ledoit_wolf) — keep it shrunk.
    """
    if method not in _METHODS:
        raise ValueError(f"unknown method: {method}. options: {_METHODS}")
    r = returns.dropna()
    cols = r.columns
    if method == "equal_weight":
        w = equal_weight(len(cols))
    else:
        cov = shrunk_covariance(r, method=cov_method)
        if method == "min_variance":
            w = min_variance(cov)
        elif method == "risk_parity":
            w = risk_parity(cov)
        else:  # max_sharpe
            mu = r.mean().to_numpy() if expected_returns is None else expected_returns
            w = max_sharpe(mu, cov, rf=rf)
    return pd.Series(w, index=cols, name="weight")
