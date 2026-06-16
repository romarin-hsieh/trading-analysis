"""Regime-conditional attribution — the "filter / factor applicability map".

The session's finding: a factor or filter's edge is NOT universal — it is regime-specific
(momentum IC was +0.039 in bull, -0.032 in bear). This module measures, for a factor, its
predictive IC CONDITIONAL on each market regime, with bootstrap confidence intervals and an
honest effective-sample warning (a handful of independent bear episodes in a decade).

All regime labels are LAGGED one bar (computed from data through t-1, applied to t) so they
never peek at the return they are conditioning. Regime thresholds are FIXED / economically
meaningful (not whole-sample quantiles) to avoid look-ahead in the bucketing itself.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.backtest.spa import stationary_bootstrap_indices
from trading_analysis.factors.validation import cross_sectional_ic, forward_returns

# ---------- regime classifiers (each returns a lagged categorical Series) ----------


def trend_regime(benchmark_close: pd.Series, window: int = 200) -> pd.Series:
    """bull / bear by price vs its own SMA(window), lagged one bar."""
    s = pd.Series(benchmark_close).sort_index()
    label = np.where(s > s.rolling(window, min_periods=window // 2).mean(), "bull", "bear")
    return pd.Series(label, index=s.index).shift(1).rename("trend")


def vol_regime(benchmark_close: pd.Series, window: int = 21,
               low: float = 0.12, high: float = 0.22) -> pd.Series:
    """low / mid / high realized-vol regime by FIXED annualized-vol thresholds (leak-free),
    lagged one bar."""
    s = pd.Series(benchmark_close).sort_index()
    rv = s.pct_change().rolling(window).std() * np.sqrt(252)
    label = pd.Series(np.where(rv < low, "low_vol", np.where(rv > high, "high_vol", "mid_vol")),
                      index=s.index)
    return label.where(rv.notna()).shift(1).rename("vol")


def drawdown_regime(benchmark_close: pd.Series, threshold: float = 0.10) -> pd.Series:
    """normal / drawdown (>threshold below the running peak), lagged one bar."""
    s = pd.Series(benchmark_close).sort_index()
    dd = s / s.cummax() - 1.0
    label = np.where(dd <= -threshold, "drawdown", "normal")
    return pd.Series(label, index=s.index).shift(1).rename("drawdown")


# ---------- conditional attribution ----------


def _bootstrap_ic_ci(ic: np.ndarray, n_boot: int = 1000, avg_block: float = 10.0,
                     seed: int = 0, alpha: float = 0.10) -> tuple[float, float]:
    """Stationary-bootstrap CI for the mean of an (autocorrelated) IC series."""
    if len(ic) < 20:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = stationary_bootstrap_indices(len(ic), avg_block, n_boot, rng)
    means = ic[idx].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def conditional_ic(factor_wide: pd.DataFrame, fwd_wide: pd.DataFrame, regime: pd.Series,
                   bootstrap: bool = True, seed: int = 0) -> pd.DataFrame:
    """Mean IC / ICIR / n_days of a factor WITHIN each regime bucket, with a bootstrap CI.

    A CI that straddles 0 means the factor's edge in that regime is not distinguishable from
    noise — usually because the regime has too few independent observations.
    """
    ic = cross_sectional_ic(factor_wide, fwd_wide)
    reg = regime.reindex(ic.index)
    df = pd.DataFrame({"ic": ic, "regime": reg}).dropna()
    rows = []
    for label, grp in df.groupby("regime"):
        g = grp["ic"].to_numpy()
        sd = g.std(ddof=1) if len(g) > 1 else np.nan
        row = {"regime": label, "n_days": len(g), "mean_ic": float(g.mean()),
               "icir": float(g.mean() / sd) if sd and sd > 0 else np.nan}
        if bootstrap:
            lo, hi = _bootstrap_ic_ci(g, seed=seed)
            row["ic_lo"], row["ic_hi"] = lo, hi
            row["ci_excludes_0"] = bool(np.isfinite(lo) and (lo > 0 or hi < 0))
        rows.append(row)
    return pd.DataFrame(rows).set_index("regime")


def conditional_sharpe(returns: pd.Series, regime: pd.Series) -> pd.DataFrame:
    """Annualized Sharpe / mean return of a strategy WITHIN each regime bucket — the direct
    'where does this strategy/filter earn its keep' view."""
    df = pd.DataFrame({"r": returns, "regime": regime.reindex(returns.index)}).dropna()
    rows = []
    for label, grp in df.groupby("regime"):
        r = grp["r"]
        sd = r.std(ddof=1)
        rows.append({"regime": label, "n_days": len(r),
                     "ann_return": float(r.mean() * 252),
                     "sharpe": float(np.sqrt(252) * r.mean() / sd) if sd > 0 else np.nan})
    return pd.DataFrame(rows).set_index("regime")


def applicability_map(factor_wide: pd.DataFrame, price_wide: pd.DataFrame,
                      benchmark_close: pd.Series, horizon: int = 21,
                      regimes: dict | None = None, seed: int = 0) -> dict[str, pd.DataFrame]:
    """For each regime taxonomy, the factor's conditional IC table — the applicability map.

    factor_wide: [ts x symbol] factor values (already point-in-time / lagged).
    price_wide:  [ts x symbol] prices, used for the forward-return target.
    benchmark_close: index series (e.g. SPY) used to build the regime labels.
    """
    fwd = forward_returns(price_wide, horizon)
    if regimes is None:
        regimes = {
            "trend": trend_regime(benchmark_close),
            "vol": vol_regime(benchmark_close),
            "drawdown": drawdown_regime(benchmark_close),
        }
    return {name: conditional_ic(factor_wide, fwd, reg, seed=seed) for name, reg in regimes.items()}
