"""Regime-conditional attribution — the "filter / factor applicability map".

The session's finding: a factor or filter's edge is NOT universal — it is regime-specific
(momentum IC was +0.039 in bull, -0.032 in bear). This module measures, for a factor, its
predictive IC CONDITIONAL on each market regime, with bootstrap confidence intervals and the
honest controls a *selection* rule needs:

  - regime labels are LAGGED one bar (computed from data through t-1, applied to t) and use
    FIXED thresholds (not whole-sample quantiles) so the bucketing never peeks;
  - the stationary-bootstrap block is matched to the IC's autocorrelation (overlapping
    `horizon`-day forward returns make daily ICs strongly autocorrelated — a short block
    under-covers and over-fires the "edge survives" flag);
  - an EFFECTIVE sample size (n_days / autocorrelation-inflation) is reported, because a regime
    with 357 raw days may hold only ~30 independent observations;
  - the decision flag is FDR-corrected across the whole (regime x bucket) family — an
    uncorrected per-cell CI stars a zero-edge factor somewhere ~70% of the time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.backtest.spa import stationary_bootstrap_indices
from trading_analysis.factors.validation import cross_sectional_ic, forward_returns

# ---------- regime classifiers (each returns a lagged categorical Series) ----------


def trend_regime(benchmark_close: pd.Series, window: int = 200) -> pd.Series:
    """bull / bear by price vs its own SMA(window), lagged one bar. Warmup bars are NaN."""
    s = pd.Series(benchmark_close).sort_index()
    ma = s.rolling(window, min_periods=window // 2).mean()
    label = pd.Series(np.where(s > ma, "bull", "bear"), index=s.index)
    return label.where(ma.notna()).shift(1).rename("trend")


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


# ---------- statistics ----------


def _vif(ic: np.ndarray) -> float:
    """Autocorrelation inflation factor 1 + 2*sum(positive acf lags) — how many raw obs make
    one effectively-independent one. Overlapping forward returns push this well above 1."""
    x = ic - ic.mean()
    denom = float((x * x).sum())
    n = len(x)
    if denom <= 0 or n < 10:
        return 1.0
    vif = 1.0
    for k in range(1, min(n // 2, 100)):
        ac = float((x[k:] * x[:-k]).sum() / denom)
        if ac <= 0:
            break
        vif += 2.0 * ac
    return max(1.0, vif)


def _bootstrap_ic_stats(ic: np.ndarray, avg_block: float, n_boot: int = 1000,
                        seed: int = 0, alpha: float = 0.10) -> tuple[float, float, float]:
    """Stationary-bootstrap CI + two-sided p-value for the mean of an autocorrelated IC series."""
    if len(ic) < 20:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = stationary_bootstrap_indices(len(ic), avg_block, n_boot, rng)
    means = ic[idx].mean(axis=1)
    lo, hi = float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))
    p = 2.0 * min(float(np.mean(means <= 0)), float(np.mean(means >= 0)))
    return (lo, hi, min(p, 1.0))


def bh_reject(pvalues, alpha: float = 0.10) -> np.ndarray:
    """Benjamini-Hochberg FDR: boolean mask of rejected (significant) hypotheses at level alpha.
    NaN p-values are never rejected."""
    p = np.asarray(pvalues, dtype=float)
    out = np.zeros(len(p), dtype=bool)
    valid = np.isfinite(p)
    pv = p[valid]
    if len(pv) == 0:
        return out
    order = np.argsort(pv)
    m = len(pv)
    passed = pv[order] <= alpha * (np.arange(1, m + 1) / m)
    rej = np.zeros(m, dtype=bool)
    if passed.any():
        rej[order[: np.where(passed)[0].max() + 1]] = True
    out[np.where(valid)[0]] = rej
    return out


# ---------- conditional attribution ----------

_IC_COLS = ["n_days", "n_eff", "mean_ic", "icir", "ic_lo", "ic_hi", "pvalue",
            "ci_excludes_0", "significant_fdr"]


def conditional_ic(factor_wide: pd.DataFrame, fwd_wide: pd.DataFrame, regime: pd.Series,
                   bootstrap: bool = True, horizon: int = 21, seed: int = 0) -> pd.DataFrame:
    """Mean IC / ICIR / n_days / n_EFF of a factor WITHIN each regime bucket, with a bootstrap
    CI (block matched to the IC autocorrelation) and an FDR-corrected `significant_fdr` flag
    across this taxonomy's buckets.

    Use `significant_fdr` (not the raw `ci_excludes_0`) as the "apply the factor here" decision.
    """
    ic = cross_sectional_ic(factor_wide, fwd_wide)
    reg = regime.reindex(ic.index)
    df = pd.DataFrame({"ic": ic, "regime": reg}).dropna()
    if df.empty:
        return pd.DataFrame(columns=_IC_COLS).rename_axis("regime")
    rows = []
    for label, grp in df.groupby("regime"):
        g = grp["ic"].to_numpy()
        sd = g.std(ddof=1) if len(g) > 1 else np.nan
        vif = _vif(g)
        row = {"regime": label, "n_days": len(g), "n_eff": int(max(1, round(len(g) / vif))),
               "mean_ic": float(g.mean()), "icir": float(g.mean() / sd) if sd and sd > 0 else np.nan,
               "ic_lo": np.nan, "ic_hi": np.nan, "pvalue": np.nan,
               "ci_excludes_0": False, "significant_fdr": False}
        if bootstrap:
            lo, hi, p = _bootstrap_ic_stats(g, avg_block=max(horizon, round(vif)), seed=seed)
            row["ic_lo"], row["ic_hi"], row["pvalue"] = lo, hi, p
            row["ci_excludes_0"] = bool(np.isfinite(lo) and (lo > 0 or hi < 0))
        rows.append(row)
    out = pd.DataFrame(rows).set_index("regime")
    if bootstrap:
        out["significant_fdr"] = bh_reject(out["pvalue"].to_numpy())
    return out


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
                      regimes: dict | None = None, seed: int = 0,
                      family_fdr: bool = True) -> dict[str, pd.DataFrame]:
    """For each regime taxonomy, the factor's conditional IC table — the applicability map.

    factor_wide: [ts x symbol] factor values (already point-in-time / lagged).
    price_wide:  [ts x symbol] prices, used for the forward-return target.
    benchmark_close: index series (e.g. SPY) used to build the regime labels.
    family_fdr: re-run Benjamini-Hochberg across ALL cells of ALL taxonomies (the true family a
      decision-maker scans) and overwrite each `significant_fdr` accordingly.
    """
    fwd = forward_returns(price_wide, horizon)
    if regimes is None:
        regimes = {
            "trend": trend_regime(benchmark_close),
            "vol": vol_regime(benchmark_close),
            "drawdown": drawdown_regime(benchmark_close),
        }
    tables = {name: conditional_ic(factor_wide, fwd, reg, horizon=horizon, seed=seed)
              for name, reg in regimes.items()}
    if family_fdr:
        nonempty = [t for t in tables.values() if len(t)]
        if nonempty:
            pooled = np.concatenate([t["pvalue"].to_numpy() for t in nonempty])
            rej = bh_reject(pooled)
            i = 0
            for t in nonempty:
                t["significant_fdr"] = rej[i:i + len(t)]
                i += len(t)
    return tables
