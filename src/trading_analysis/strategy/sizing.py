"""Position sizing helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def fixed_fraction_size(
    cash: float, fraction: float, price: float, max_dollars: float | None = None
) -> int:
    """Allocate `fraction` of `cash` to one position, return whole-share quantity."""
    if price <= 0 or fraction <= 0:
        return 0
    target_dollars = cash * fraction
    if max_dollars is not None:
        target_dollars = min(target_dollars, max_dollars)
    return int(target_dollars // price)


def vol_target_fraction(
    target_vol: float, realized_vol: float, max_fraction: float = 0.2
) -> float:
    """Scale position fraction inversely to realized volatility."""
    if realized_vol <= 0:
        return 0.0
    return float(np.clip(target_vol / realized_vol, 0.0, max_fraction))


def kelly_fraction(win_prob: float, win_loss_ratio: float, cap: float = 0.25) -> float:
    """Half-Kelly is industry standard; we cap further by `cap` to avoid blowups."""
    if win_loss_ratio <= 0:
        return 0.0
    full = win_prob - (1 - win_prob) / win_loss_ratio
    half = max(0.0, full / 2)
    return float(np.clip(half, 0.0, cap))


def equal_weight_pivot(direction_pivot: pd.DataFrame, max_positions: int) -> pd.DataFrame:
    """Convert a -1/0/+1 direction pivot into target weights with equal weight per active name.

    Caps active positions at `max_positions` (longs prioritized over shorts when over capacity).
    """
    if direction_pivot.empty:
        return direction_pivot
    weights = direction_pivot.astype(float).copy()
    for ts, row in direction_pivot.iterrows():
        active_long = row[row > 0].index.tolist()
        active_short = row[row < 0].index.tolist()
        if len(active_long) + len(active_short) > max_positions:
            keep_long = active_long[:max_positions]
            remaining = max_positions - len(keep_long)
            keep_short = active_short[: max(0, remaining)]
            weights.loc[ts, :] = 0.0
            for s in keep_long:
                weights.loc[ts, s] = 1.0
            for s in keep_short:
                weights.loc[ts, s] = -1.0
        active_count = (weights.loc[ts] != 0).sum()
        if active_count > 0:
            weights.loc[ts] = weights.loc[ts] / active_count
    return weights
