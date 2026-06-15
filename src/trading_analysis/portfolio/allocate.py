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
from trading_analysis.portfolio.covariance import james_stein_mean, shrunk_covariance

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

    LEAKAGE WARNING: this estimates mu/Sigma from ALL rows of `returns`. In a backtest
    call `rebalance()` (trailing point-in-time windows) instead — never `allocate(all_history)`.
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
            # default mu is James-Stein-shrunk (raw sample mean dominates tangency error)
            mu = james_stein_mean(r) if expected_returns is None else expected_returns
            w = max_sharpe(mu, cov, rf=rf)
    return pd.Series(w, index=cols, name="weight")


def rebalance(
    returns: pd.DataFrame,
    lookback: int = 126,
    step: int = 21,
    method: str = "risk_parity",
    min_obs: int | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Leak-free walk-forward weights — the safe way to size a backtest.

    The weights effective at date t use ONLY returns strictly BEFORE t (a trailing
    `lookback` window); apply each row to FORWARD returns. Rebalances every `step` bars;
    degenerate windows (too few rows, zero-variance, non-convergence) are skipped.
    Returns a [rebalance_date x asset] weight frame. Use this, not allocate(all_history).
    """
    r = returns.sort_index()
    idx = r.index
    if min_obs is None:
        min_obs = max(2, lookback // 2)
    rows = {}
    for i in range(lookback, len(idx), step):
        window = r.iloc[i - lookback : i].dropna(axis=1, how="any")  # rows strictly before idx[i]
        if window.shape[0] < min_obs or window.shape[1] < 1:
            continue
        try:
            rows[idx[i]] = allocate(window, method=method, **kwargs)
        except (RuntimeError, ValueError):
            continue
    return pd.DataFrame(rows).T.reindex(columns=returns.columns)
