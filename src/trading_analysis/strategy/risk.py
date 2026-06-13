"""Risk filters: drawdown circuit-breaker, position caps."""

from __future__ import annotations

import pandas as pd


def apply_position_cap(weights: pd.DataFrame, cap: float) -> pd.DataFrame:
    """Clip per-name weights to ±cap, then renormalize so absolute weights sum to <=1."""
    if weights.empty:
        return weights
    w = weights.clip(lower=-cap, upper=cap)
    abs_total = w.abs().sum(axis=1)
    factor = (abs_total.where(abs_total <= 1.0, 1.0 / abs_total)).fillna(1.0)
    return w.mul(factor, axis=0)


def drawdown_breach(equity_curve: pd.Series, max_dd: float) -> pd.Timestamp | None:
    """Return the first timestamp at which drawdown breaches `max_dd` (e.g. 0.20)."""
    if equity_curve.empty:
        return None
    running_max = equity_curve.cummax()
    dd = equity_curve / running_max - 1.0
    breached = dd[dd <= -abs(max_dd)]
    return breached.index[0] if not breached.empty else None
