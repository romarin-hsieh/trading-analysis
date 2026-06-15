"""Portfolio construction: shrunk-covariance allocators + leverage sizing.

Covariance shrinkage is mandated (Ledoit-Wolf); 1/N (equal_weight) is the benchmark every
optimizer must beat OOS net of turnover (DeMiguel-Garlappi-Uppal). Use `allocate()`.
"""

from trading_analysis.portfolio.allocate import allocate, rebalance
from trading_analysis.portfolio.allocators import (
    equal_weight,
    max_sharpe,
    min_variance,
    risk_parity,
)
from trading_analysis.portfolio.covariance import james_stein_mean, shrunk_covariance
from trading_analysis.portfolio.sizing import kelly_leverage, vol_target_scale

__all__ = [
    "allocate",
    "equal_weight",
    "james_stein_mean",
    "kelly_leverage",
    "max_sharpe",
    "min_variance",
    "rebalance",
    "risk_parity",
    "shrunk_covariance",
    "vol_target_scale",
]
