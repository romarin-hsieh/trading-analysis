"""Probabilistic / Deflated Sharpe Ratio — selection-bias control (Bailey & Lopez de Prado).

PurgedKFold prevents leakage; it does NOT prevent the inflation from trying many configs.
- PSR: confidence the true (per-period) Sharpe exceeds a benchmark, adjusting for track
  length, skew, and kurtosis.
- DSR: PSR against the EXPECTED MAXIMUM Sharpe under N zero-skill trials — the bar rises
  with the number of configs tried. Feed the REAL trial count N (grid cells x feature
  subsets x model configs). DSR > 0.95 => survives multiple testing.
- Min track-record length: observations needed to be confident at a given level.

All Sharpes here are PER-PERIOD (not annualized); be consistent with `trials_sharpe_std`.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import kurtosis as _kurt
from scipy.stats import norm
from scipy.stats import skew as _skew

_EULER = 0.5772156649015329


def _moments(returns):
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    n = len(r)
    if n < 4:
        return n, np.nan, np.nan, np.nan
    sd = r.std(ddof=1)
    if sd == 0:
        return n, np.nan, np.nan, np.nan
    sr = r.mean() / sd
    skew = float(_skew(r, bias=False))
    kurt = float(_kurt(r, fisher=False, bias=False))  # non-excess kurtosis
    return n, sr, skew, kurt


def probabilistic_sharpe_ratio(returns, sr_benchmark: float = 0.0) -> float:
    """P(true per-period Sharpe > sr_benchmark)."""
    n, sr, skew, kurt = _moments(returns)
    if not np.isfinite(sr):
        return np.nan
    denom = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    if denom <= 0:
        return np.nan
    z = (sr - sr_benchmark) * np.sqrt(n - 1) / denom
    return float(norm.cdf(z))


def expected_max_sharpe(n_trials: int, trials_sharpe_std: float) -> float:
    """E[max per-period Sharpe] across `n_trials` zero-skill trials whose Sharpes have
    cross-trial std `trials_sharpe_std` (Bailey-LdP expected-maximum approximation)."""
    if n_trials < 2 or trials_sharpe_std <= 0:
        return 0.0
    z1 = norm.ppf(1.0 - 1.0 / n_trials)
    z2 = norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(trials_sharpe_std * ((1.0 - _EULER) * z1 + _EULER * z2))


def deflated_sharpe_ratio(returns, n_trials: int, trials_sharpe_std: float) -> float:
    """PSR against the expected-max Sharpe under N zero-skill trials. > 0.95 => survives."""
    return probabilistic_sharpe_ratio(returns, sr_benchmark=expected_max_sharpe(n_trials, trials_sharpe_std))


def min_track_record_length(returns, sr_benchmark: float = 0.0, prob: float = 0.95) -> float:
    """Minimum #observations for PSR(sr_benchmark) >= prob, given observed moments."""
    _, sr, skew, kurt = _moments(returns)
    if not np.isfinite(sr) or sr <= sr_benchmark:
        return np.nan
    var_term = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2
    return float(1.0 + var_term * (norm.ppf(prob) / (sr - sr_benchmark)) ** 2)
