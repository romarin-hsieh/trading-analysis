"""Data-snooping tests via the stationary bootstrap (Politis-Romano):
White's Reality Check (2000) and Hansen's SPA (2005).

Given N models' per-period performance differentials vs a benchmark (d = model - benchmark),
test H0: no model truly beats the benchmark (max_k E[d_k] <= 0). A high p-value means the
best backtest is consistent with luck across the N strategies tried. SPA is preferred over
RC: it studentizes and drops clearly-inferior models from the null, so a pile of junk
strategies can't dilute the test's power.
"""

from __future__ import annotations

import numpy as np


def stationary_bootstrap_indices(n: int, avg_block: float, n_boot: int, rng) -> np.ndarray:
    """[n_boot x n] resample indices; geometric block lengths with mean `avg_block`."""
    p = 1.0 / max(avg_block, 1.0)
    starts = rng.integers(0, n, size=n_boot)
    new_block = rng.random((n_boot, n)) < p
    rand_idx = rng.integers(0, n, size=(n_boot, n))      # precomputed restart positions
    idx = np.empty((n_boot, n), dtype=np.int64)
    for b in range(n_boot):
        i = starts[b]
        nb, ri, row = new_block[b], rand_idx[b], idx[b]
        for t in range(n):
            row[t] = i
            i = ri[t] if nb[t] else (i + 1) % n
    return idx


def reality_check_pvalue(d, avg_block: float = 10.0, n_boot: int = 1000, seed: int = 0) -> float:
    """White's Reality Check. d: [T x N] performance differentials (model - benchmark)."""
    d = np.asarray(d, dtype=float)
    t = d.shape[0]
    rng = np.random.default_rng(seed)
    dbar = d.mean(axis=0)
    v = np.sqrt(t) * dbar.max()
    idx = stationary_bootstrap_indices(t, avg_block, n_boot, rng)
    boot_means = d[idx].mean(axis=1)                      # [n_boot x N]
    vstar = np.sqrt(t) * (boot_means - dbar).max(axis=1)  # recentered
    return float(np.mean(vstar >= v))


def spa_pvalue(d, avg_block: float = 10.0, n_boot: int = 1000, seed: int = 0) -> float:
    """Hansen's SPA (consistent variant): studentized + sample-dependent recentering."""
    d = np.asarray(d, dtype=float)
    t = d.shape[0]
    rng = np.random.default_rng(seed)
    dbar = d.mean(axis=0)
    w = d.std(axis=0, ddof=1)
    w_safe = np.where(w > 0, w, np.inf)                   # zero-variance models contribute nothing
    v = max(float((np.sqrt(t) * dbar / w_safe).max()), 0.0)
    # consistent recentering: keep only models not clearly inferior under the null
    thr = w * np.sqrt(2.0 * np.log(np.log(t)) / t) if t > np.e**np.e else np.zeros_like(w)
    mu_c = np.where(dbar >= -thr, dbar, 0.0)
    idx = stationary_bootstrap_indices(t, avg_block, n_boot, rng)
    boot_means = d[idx].mean(axis=1)                      # [n_boot x N]
    z = np.sqrt(t) * (boot_means - mu_c) / w_safe
    vstar = np.maximum(z.max(axis=1), 0.0)
    return float(np.mean(vstar >= v))
