"""Factor research: the validation gate every factor must pass before it is trusted.

Build factors with `features.build_features`, then `validate_factor` (IC / ICIR /
quantile spread) decides whether they predict forward returns.
"""

from trading_analysis.factors.validation import (
    cross_sectional_ic,
    forward_returns,
    ic_summary,
    quantile_spread,
    to_wide,
    validate_factor,
)

__all__ = [
    "cross_sectional_ic",
    "forward_returns",
    "ic_summary",
    "quantile_spread",
    "to_wide",
    "validate_factor",
]
