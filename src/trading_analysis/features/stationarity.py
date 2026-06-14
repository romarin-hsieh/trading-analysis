"""ADF stationarity test + feature selection.

ML inputs should be stationary; non-stationary (unit-root) features mislead tree/linear
models. `stationary_columns` is a SELECTION step — the kept set is data-dependent, so it
must be decided WITHIN each CV fold's training data (deciding it on the full sample
leaks). It is deliberately NOT part of the causal `build_features`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def adf_pvalue(series) -> float:
    """Augmented Dickey-Fuller p-value. Low p (< alpha) ⇒ reject unit root ⇒ stationary."""
    s = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()
    if len(s) < 20 or s.nunique() < 5:
        return np.nan
    try:
        return float(adfuller(s.values, autolag="AIC")[1])
    except Exception:
        return np.nan


def stationary_columns(
    features: pd.DataFrame, alpha: float = 0.05, cols: list[str] | None = None
) -> tuple[list[str], pd.Series]:
    """Return (kept_columns, pvalues). Apply within CV folds, not on the full sample."""
    if cols is None:
        cols = [c for c in features.columns if c not in ("symbol", "ts")]
    pvals = pd.Series({c: adf_pvalue(features[c]) for c in cols})
    kept = [c for c in cols if pd.notna(pvals[c]) and pvals[c] < alpha]
    return kept, pvals
