"""Factor validation harness (Alphalens-equivalent gate).

Before a factor (a column of the feature panel) is trusted in a backtest or fed to the
ML layer, it must show a predictive Information Coefficient (IC) and a monotonic
quantile spread vs forward returns. This is the cheap, decisive "is this factor real?"
check — the factor-level analogue of the backtest rigor scorecard.

IC = per-date cross-sectional rank correlation of the factor with forward returns.
ICIR = mean(IC)/std(IC); t_stat = ICIR·sqrt(n). All causal (forward returns are the
*target*, never fed back into the factor).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def forward_returns(close_wide: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Forward simple return over `horizon` bars, [ts x symbol] (last `horizon` rows NaN)."""
    return close_wide.shift(-horizon) / close_wide - 1.0


def to_wide(panel: pd.DataFrame, col: str) -> pd.DataFrame:
    """Pivot a long [symbol, ts, ...] panel to a wide [ts x symbol] frame for one column."""
    return panel.pivot_table(index="ts", columns="symbol", values=col).sort_index()


def cross_sectional_ic(
    factor_wide: pd.DataFrame,
    fwd_wide: pd.DataFrame,
    method: str = "spearman",
    min_names: int = 5,
) -> pd.Series:
    """Per-date cross-sectional IC (rank corr) between factor and forward return."""
    idx = factor_wide.index.intersection(fwd_wide.index)
    cols = factor_wide.columns.intersection(fwd_wide.columns)
    f = factor_wide.loc[idx, cols]
    r = fwd_wide.loc[idx, cols]
    out: dict = {}
    for ts in idx:
        fr, rr = f.loc[ts], r.loc[ts]
        valid = fr.notna() & rr.notna()
        if int(valid.sum()) >= min_names:
            out[ts] = fr[valid].corr(rr[valid], method=method)
    return pd.Series(out, dtype=float).dropna()


def ic_summary(ic: pd.Series) -> dict:
    """Summary stats of an IC time series: mean, std, ICIR, t-stat, hit-rate, n."""
    ic = ic.dropna()
    n = len(ic)
    mean = float(ic.mean()) if n else np.nan
    std = float(ic.std(ddof=1)) if n > 1 else np.nan
    if not n or std is None or np.isnan(std) or std < 1e-12:
        icir = np.nan
        tstat = np.nan
    else:
        icir = mean / std
        tstat = icir * np.sqrt(n)
    return {
        "n": n,
        "mean_ic": mean,
        "ic_std": std,
        "icir": icir,
        "t_stat": tstat,
        "hit_rate": float((ic > 0).mean()) if n else np.nan,
    }


def quantile_spread(
    factor_wide: pd.DataFrame, fwd_wide: pd.DataFrame, q: int = 5
) -> pd.DataFrame:
    """Mean forward return per factor quantile (bucketed cross-sectionally each date,
    then averaged over time). Q1 = lowest factor, Q{q} = highest — a monotone rising
    spread is the sign of a real factor."""
    idx = factor_wide.index.intersection(fwd_wide.index)
    cols = factor_wide.columns.intersection(fwd_wide.columns)
    rows = []
    for ts in idx:
        fr, rr = factor_wide.loc[ts, cols], fwd_wide.loc[ts, cols]
        valid = fr.notna() & rr.notna()
        if int(valid.sum()) < q:
            continue
        try:
            buckets = pd.qcut(fr[valid].rank(method="first"), q, labels=False)
        except ValueError:
            continue
        rows.append(rr[valid].groupby(buckets).mean())
    if not rows:
        return pd.DataFrame(columns=["mean_fwd_ret"])
    means = pd.concat(rows, axis=1).T.mean()
    means.index = [f"Q{int(i) + 1}" for i in means.index]
    return means.to_frame("mean_fwd_ret")


def validate_factor(
    panel: pd.DataFrame,
    close_wide: pd.DataFrame,
    factor_col: str,
    horizons=(1, 5, 20),
    q: int = 5,
    method: str = "spearman",
) -> dict:
    """The gate: IC summary at each horizon + a quantile spread (mid horizon).

    Returns {"factor", "ic": {h: ic_summary}, "quantiles": DataFrame}.
    """
    factor_wide = to_wide(panel, factor_col)
    out: dict = {"factor": factor_col, "ic": {}}
    for h in horizons:
        out["ic"][h] = ic_summary(cross_sectional_ic(factor_wide, forward_returns(close_wide, h), method=method))
    mid = horizons[len(horizons) // 2]
    out["quantiles"] = quantile_spread(factor_wide, forward_returns(close_wide, mid), q=q)
    return out
