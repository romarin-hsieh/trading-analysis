"""Factor attribution (docs/03 §O3): report ALPHA net of factor exposure, not raw Sharpe.

A trend/momentum system loads hard on UMD and HML; judging it by raw Sharpe mis-attributes
factor beta as skill (Fama's joint-hypothesis problem). We regress strategy excess returns
on the Carhart-4 factors (Mkt-RF, SMB, HML, UMD) with Newey-West (HAC) robust standard
errors — heteroskedasticity/autocorrelation-robust, per §O7 — and read off the intercept
(alpha) and its t-stat. The factor returns come pre-built from the Ken French Data Library,
so no fundamentals are needed on our side.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def factor_alpha(strategy_returns, factor_returns: pd.DataFrame, rf=0.0, hac_lags: int | None = None) -> dict:
    """OLS of (strategy - rf) on factor_returns with HAC (Newey-West) SE.

    factor_returns: DataFrame of factor columns (e.g. Mkt-RF, SMB, HML, UMD) indexed to align
    with strategy_returns. Returns alpha (per-period intercept), its t-stat/p-value, factor
    betas + t-stats, R^2, n.
    """
    y = pd.Series(strategy_returns, dtype=float)
    x = factor_returns.astype(float)
    df = pd.concat([y.rename("_y"), x], axis=1).dropna()
    rf_series = rf if np.isscalar(rf) else pd.Series(rf).reindex(df.index)
    y_excess = df["_y"] - rf_series
    cols = list(x.columns)
    design = sm.add_constant(df[cols])
    if hac_lags is None:
        hac_lags = int(np.floor(4 * (len(df) / 100.0) ** (2.0 / 9.0)))
    model = sm.OLS(y_excess, design).fit(cov_type="HAC", cov_kwds={"maxlags": max(hac_lags, 1)})
    return {
        "alpha": float(model.params["const"]),
        "alpha_tstat": float(model.tvalues["const"]),
        "alpha_pvalue": float(model.pvalues["const"]),
        "betas": {c: float(model.params[c]) for c in cols},
        "beta_tstats": {c: float(model.tvalues[c]) for c in cols},
        "r2": float(model.rsquared),
        "n": len(df),
    }


def load_ff_factors(start="2015-01-01", end=None, momentum: bool = True) -> pd.DataFrame:
    """Daily Fama-French 3 factors (+ Carhart momentum UMD) from the Ken French Data Library
    via pandas_datareader (NETWORK). Returns decimal returns [Mkt-RF, SMB, HML, (UMD), RF].
    The factors are pre-built — no fundamentals needed locally.
    """
    from pandas_datareader import data as pdr

    ff = pdr.DataReader("F-F_Research_Data_Factors_daily", "famafrench", start, end)[0] / 100.0
    if momentum:
        mom = pdr.DataReader("F-F_Momentum_Factor_daily", "famafrench", start, end)[0] / 100.0
        mom.columns = ["UMD"]
        ff = ff.join(mom)
    return ff
