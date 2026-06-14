"""Labeling + leakage-aware cross-validation (de Prado AFML Ch.3/7).

The ML foundation: turn price paths into labels whose end-times (`t1`) let
PurgedKFold prevent train/test overlap leakage. Build factors/ML on top of this.
"""

from trading_analysis.labeling.cv import PurgedKFold
from trading_analysis.labeling.trend_scanning import trend_scanning_labels
from trading_analysis.labeling.triple_barrier import (
    get_bins,
    triple_barrier_events,
    triple_barrier_labels,
    vertical_barriers,
)
from trading_analysis.labeling.volatility import ewma_vol

__all__ = [
    "PurgedKFold",
    "ewma_vol",
    "get_bins",
    "trend_scanning_labels",
    "triple_barrier_events",
    "triple_barrier_labels",
    "vertical_barriers",
]
