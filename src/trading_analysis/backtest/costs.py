"""Size-dependent transaction costs (docs/03 §O2).

A flat-bps haircut understates impact — Perold's example turns a 20%/yr paper portfolio
into a 2.5%/yr live fund (Bertsimas-Lo). Cost model:

    cost_bps(trade) = half_spread_bps + impact_coef_bps * (trade_$ / ADV_$) ** exponent

with `exponent=0.5` the Almgren-Chriss square-root impact law. Liquidity (the Amihud
illiquidity ratio and a Kyle-lambda proxy) is estimated from the OHLCV/feature data we
already hold, so this adds no data cost. The headline diagnostic is implementation
shortfall (realized fills vs the arrival/decision price).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def amihud_illiquidity(returns, dollar_volume, window: int = 21) -> pd.Series:
    """Rolling Amihud ILLIQ = mean(|return| / dollar_volume); higher = less liquid. Causal."""
    r = pd.Series(np.asarray(returns, dtype=float)).abs()
    dv = pd.Series(np.asarray(dollar_volume, dtype=float)).replace(0.0, np.nan)
    r.index = dv.index
    return (r / dv).rolling(window, min_periods=max(2, window // 2)).mean()


def kyle_lambda(daily_vol, dollar_volume):
    """Kyle price-impact proxy lambda ~ daily return vol / daily dollar volume
    (price move per $ of order flow); higher = more impact."""
    dv = np.asarray(dollar_volume, dtype=float)
    vol = np.asarray(daily_vol, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(dv > 0, vol / dv, np.nan)


def size_dependent_cost_bps(
    trade_dollars,
    adv_dollars,
    half_spread_bps: float = 2.5,
    impact_coef_bps: float = 10.0,
    exponent: float = 0.5,
):
    """Per-trade cost in basis points: half-spread + market impact (sqrt-law by default)."""
    trade = np.abs(np.asarray(trade_dollars, dtype=float))
    adv = np.asarray(adv_dollars, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        participation = np.where(adv > 0, trade / adv, np.nan)
    return half_spread_bps + impact_coef_bps * np.power(participation, exponent)


def implementation_shortfall(arrival_price, fill_price, side: int = 1):
    """Realized cost vs the decision/arrival price (Perold), as a fraction; positive = cost.
    side=+1 buy, -1 sell."""
    return side * (np.asarray(fill_price, dtype=float) / np.asarray(arrival_price, dtype=float) - 1.0)


def expected_cost_drag_bps(annual_turnover: float, avg_trade_dollars, avg_adv_dollars, **kwargs) -> float:
    """Rough annual cost drag (bps) = one-way turnover count x per-trade cost bps."""
    per_trade = float(size_dependent_cost_bps(avg_trade_dollars, avg_adv_dollars, **kwargs))
    return float(annual_turnover * per_trade)
