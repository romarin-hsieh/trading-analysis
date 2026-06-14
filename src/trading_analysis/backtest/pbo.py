"""Probability of Backtest Overfitting via Combinatorially Symmetric Cross-Validation
(Bailey, Borwein, Lopez de Prado, Zhu 2017).

Input: a [T x N] matrix of per-period performance for N strategy configs. Split time into
S even blocks; over every C(S, S/2) way to choose half as in-sample, pick the IS-best
config and look at its OUT-of-sample rank. PBO = P(the IS-best ranks below the OOS median)
= the chance your "winner" is an artifact of selection. PBO >= 0.5 => do not promote.
"""

from __future__ import annotations

import itertools

import numpy as np
from scipy.stats import rankdata


def _sharpe_cols(block: np.ndarray) -> np.ndarray:
    mu = block.mean(axis=0)
    sd = block.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 0, mu / sd, 0.0)


def probability_of_backtest_overfitting(returns_matrix, n_splits: int = 16) -> dict:
    """returns_matrix: [T x N] (rows=time, cols=configs). n_splits S must be even."""
    m = np.asarray(returns_matrix, dtype=float)
    if m.ndim != 2:
        raise ValueError("returns_matrix must be 2-D [T x N]")
    t, n = m.shape
    if n < 2 or t < n_splits or n_splits % 2 != 0:
        raise ValueError("need N>=2 configs, T>=n_splits, and an even n_splits")
    groups = np.array_split(np.arange(t), n_splits)
    logits = []
    for is_combo in itertools.combinations(range(n_splits), n_splits // 2):
        is_set = set(is_combo)
        is_rows = np.concatenate([groups[g] for g in is_combo])
        oos_rows = np.concatenate([groups[g] for g in range(n_splits) if g not in is_set])
        n_star = int(np.argmax(_sharpe_cols(m[is_rows])))     # best in-sample config
        oos_sr = _sharpe_cols(m[oos_rows])
        omega = rankdata(oos_sr)[n_star] / (n + 1)            # OOS relative rank in (0,1)
        omega = min(max(omega, 1e-6), 1.0 - 1e-6)
        logits.append(np.log(omega / (1.0 - omega)))
    logits = np.asarray(logits)
    return {
        "pbo": float(np.mean(logits <= 0.0)),                 # IS-best below OOS median
        "n_combinations": len(logits),
        "mean_logit": float(logits.mean()),
    }
