"""Feature engineering: a causal feature panel + leakage-aware selection tools.

`build_features` is point-in-time safe (use it freely). `stationary_columns` and
`mdi_importance` are SELECTION tools — run them inside CV folds, never on the full
sample, or they leak.
"""

from trading_analysis.features.build import FEATURE_COLUMNS, build_features
from trading_analysis.features.importance import mdi_importance
from trading_analysis.features.stationarity import adf_pvalue, stationary_columns
from trading_analysis.features.timeseries import (
    half_life,
    hurst_exponent,
    rolling_half_life,
    rolling_hurst,
    rolling_variance_ratio,
    variance_ratio,
)

__all__ = [
    "FEATURE_COLUMNS",
    "adf_pvalue",
    "build_features",
    "half_life",
    "hurst_exponent",
    "mdi_importance",
    "rolling_half_life",
    "rolling_hurst",
    "rolling_variance_ratio",
    "stationary_columns",
    "variance_ratio",
]
