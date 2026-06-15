"""Portfolio-level leverage sizing: fractional Kelly and volatility targeting.

Kelly (1956) gives the growth-optimal leverage; in practice use a FRACTION of it (half-Kelly
default) and a hard cap — full Kelly is too aggressive under estimation error. Vol targeting
scales exposure so realized portfolio vol hits a target.
"""

from __future__ import annotations

import numpy as np


def kelly_leverage(expected_return: float, variance: float, fraction: float = 0.5, cap: float = 1.0) -> float:
    """Growth-optimal leverage = fraction * mu / variance, clipped to [0, cap]. mu, variance
    are per-period (consistent units). fraction=0.5 => half-Kelly."""
    if variance <= 0:
        return 0.0
    return float(np.clip(fraction * expected_return / variance, 0.0, cap))


def vol_target_scale(realized_vol: float, target_vol: float, max_leverage: float = 1.0) -> float:
    """Leverage to hit `target_vol` given `realized_vol`, clipped to [0, max_leverage]."""
    if realized_vol <= 0:
        return 0.0
    return float(np.clip(target_vol / realized_vol, 0.0, max_leverage))
