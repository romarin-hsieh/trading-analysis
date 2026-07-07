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


def _ff_csv_direct(dataset: str) -> pd.DataFrame:
    """Robust direct download/parse of a Ken French daily CSV zip. pandas_datareader's parser
    breaks when the library appends footer notes (e.g. "Missing data are indicated by -99.99"),
    so we parse defensively: keep only rows whose index is a valid YYYYMMDD date."""
    import io
    import urllib.request
    import zipfile

    url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{dataset}_CSV.zip"
    raw = urllib.request.urlopen(url, timeout=60).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
    lines = text.splitlines()
    hdr = next(i for i, ln in enumerate(lines) if ln.strip().startswith(","))
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), index_col=0)
    df.index = df.index.astype(str).str.strip()
    df = df[df.index.str.fullmatch(r"\d{8}")]
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df[(df > -99).all(axis=1)]


def load_ff_factors(start="2015-01-01", end=None, momentum: bool = True) -> pd.DataFrame:
    """Daily Fama-French 3 factors (+ Carhart momentum UMD) from the Ken French Data Library.
    Tries pandas_datareader first; falls back to a defensive direct-CSV parser when the
    library file format breaks pdr (footer-note rows). Returns decimal [Mkt-RF, SMB, HML, (UMD), RF].
    """
    try:
        from pandas_datareader import data as pdr

        ff = pdr.DataReader("F-F_Research_Data_Factors_daily", "famafrench", start, end)[0] / 100.0
        if momentum:
            mom = pdr.DataReader("F-F_Momentum_Factor_daily", "famafrench", start, end)[0] / 100.0
            mom.columns = ["UMD"]
            ff = ff.join(mom)
    except Exception:
        ff = _ff_csv_direct("F-F_Research_Data_Factors_daily") / 100.0
        if momentum:
            mom = _ff_csv_direct("F-F_Momentum_Factor_daily") / 100.0
            mom.columns = ["UMD"]
            ff = ff.join(mom)
    ff = ff.loc[ff.index >= pd.Timestamp(start)]
    if end is not None:
        ff = ff.loc[ff.index <= pd.Timestamp(end)]
    return ff
