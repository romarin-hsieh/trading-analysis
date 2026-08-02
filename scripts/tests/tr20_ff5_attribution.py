"""TR-20 -- does the flagship's (already-borderline) alpha survive a richer factor model?

F0 DECLARATION (pre-committed)
  mechanism  : Fama-French 5-factor (2015, +RMW profitability +CMA investment) and a 6-factor
               (FF5+UMD) benchmark, applied to the flagship 5-sleeve combo's MONTHLY returns.
  seat       : same book as TR-18 (tr15.build_combo_cost(1.0)), monthly frequency (the frequency-
               appropriate clock established in TR-18). Ken French monthly factors, 2015-2026.
  why it matters : TR-18 downgraded the flagship to PASSED-borderline -- monthly Carhart-4 alpha
               t=2.64 (below HLZ 3.0) but still real (bootstrap P(a<=0)=0.001). The next escalation
               of the F5/HLZ discipline: is even THAT residual alpha just unmodeled factor beta?
               RMW (profitability) and CMA (investment) are the obvious suspects a Carhart-4 model
               cannot see. If they absorb the alpha, the flagship's "alpha" was factor exposure.
  FALSIFIABLE CLAIM : adding RMW+CMA(+UMD) leaves a comparable positive alpha -- the FF6 alpha-t
               stays >= 2.0 and within ~30% of the Carhart-4 alpha.
  VERDICT RULE (pre-committed):
     FF6 alpha-t >= 2.0 and alpha within ~30% of C4 -> ROBUST (alpha is not RMW/CMA beta; flagship
                                                        stays PASSED-borderline, now vs a 6-factor bar)
     FF6 alpha-t in [1.0, 2.0) or alpha shrinks >30% -> WEAKENED (partly factor beta; note which factor)
     FF6 alpha-t < 1.0 (RMW/CMA absorb it)          -> SUBSUMED (downgrade flagship alpha to FAILED-vs-FF5)
  note: this is about whether a REAL positive alpha survives a richer model, NOT about clearing HLZ 3.0
        (TR-18 already showed it sits below 3.0 monthly). mis-application risk : LOW (same seat).

Run: uv run python scripts/tests/tr20_ff5_attribution.py
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

import tr15_combo_cost as tr15  # noqa: E402

HLZ = 3.0
GREY_L = "#9e9e9e"


def _direct_monthly(ds):
    import io
    import urllib.request
    import zipfile
    url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{ds}_CSV.zip"
    raw = urllib.request.urlopen(url, timeout=60).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
    lines = text.splitlines()
    hdr = next(i for i, ln in enumerate(lines) if ln.strip().startswith(","))
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), index_col=0)
    df.index = df.index.astype(str).str.strip()
    df = df[df.index.str.fullmatch(r"\d{6}")]
    df.index = pd.to_datetime(df.index, format="%Y%m").to_period("M")
    return df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")


def load_ff5_umd_monthly(start="2015-01-01"):
    """Monthly FF5 (Mkt-RF, SMB, HML, RMW, CMA, RF) + Carhart UMD, decimals."""
    try:
        from pandas_datareader import data as pdr
        ff = pdr.DataReader("F-F_Research_Data_5_Factors_2x3", "famafrench", start)[0] / 100.0
        mom = pdr.DataReader("F-F_Momentum_Factor", "famafrench", start)[0] / 100.0
        mom.columns = ["UMD"]
        ff = ff.join(mom)
        ff.index = ff.index.astype("period[M]")
    except Exception:
        ff = _direct_monthly("F-F_Research_Data_5_Factors_2x3") / 100.0
        mom = _direct_monthly("F-F_Momentum_Factor") / 100.0
        mom.columns = ["UMD"]
        ff = ff.join(mom)
        ff.columns = [str(c).strip() for c in ff.columns]
    return ff.loc[ff.index >= pd.Period(start, "M")]


def reg(y, X):
    d = sm.add_constant(X)
    ols = sm.OLS(y, d).fit()
    lag = int(np.floor(4 * (len(y) / 100.0) ** (2.0 / 9.0)))
    hac = sm.OLS(y, d).fit(cov_type="HAC", cov_kwds={"maxlags": max(lag, 1)})
    return {
        "alpha_m": float(ols.params["const"]),
        "t_ols": float(ols.tvalues["const"]),
        "t_hac": float(hac.tvalues["const"]),
        "r2": float(ols.rsquared),
        "betas": {c: (float(ols.params[c]), float(hac.tvalues[c])) for c in X.columns},
    }


def main():
    rp = tr15.build_combo_cost(1.0)
    ff = load_ff5_umd_monthly("2015-01-01")
    rpm = (1 + rp).groupby(rp.index.to_period("M")).prod() - 1
    cmn = rpm.index.intersection(ff.index)
    y = (rpm.reindex(cmn) - ff.reindex(cmn)["RF"]).dropna()
    F = ff.reindex(y.index)
    y.index = y.index.to_timestamp()
    F.index = F.index.to_timestamp()

    models = {
        "CAPM": ["Mkt-RF"],
        "FF3": ["Mkt-RF", "SMB", "HML"],
        "Carhart-4": ["Mkt-RF", "SMB", "HML", "UMD"],
        "FF5": ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
        "FF6 (FF5+UMD)": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"],
    }
    print("=" * 100)
    print(f"TR-20  FLAGSHIP ALPHA vs A RICHER FACTOR MODEL (monthly, n={len(y)}, Ken French factors)")
    print("=" * 100)
    print(f"{'benchmark':16s} {'ann alpha':>10s} {'t(OLS)':>8s} {'t(HAC)':>8s} {'R2':>6s}   RMW beta(t) / CMA beta(t)")
    res = {}
    for name, cols in models.items():
        r = reg(y, F[cols])
        res[name] = r
        rmw = f"{r['betas']['RMW'][0]:+.2f}({r['betas']['RMW'][1]:+.1f})" if "RMW" in r["betas"] else "  --"
        cma = f"{r['betas']['CMA'][0]:+.2f}({r['betas']['CMA'][1]:+.1f})" if "CMA" in r["betas"] else "  --"
        print(f"{name:16s} {r['alpha_m']*12:>+9.2%} {r['t_ols']:>+8.2f} {r['t_hac']:>+8.2f} "
              f"{r['r2']:>6.2f}   {rmw} / {cma}")

    c4, ff6 = res["Carhart-4"], res["FF6 (FF5+UMD)"]
    a_c4, a_ff6 = c4["alpha_m"] * 12, ff6["alpha_m"] * 12
    shrink = (a_c4 - a_ff6) / a_c4 if a_c4 else 0.0
    t6 = ff6["t_ols"]
    print("-" * 100)
    print(f"Carhart-4 ann alpha {a_c4:+.2%} (t {c4['t_ols']:.2f}) -> FF6 ann alpha {a_ff6:+.2%} "
          f"(t {t6:.2f}); alpha shrinks {shrink:+.0%} adding RMW+CMA.")
    if t6 >= 2.0 and abs(shrink) <= 0.30:
        verdict = ("ROBUST -- RMW+CMA do NOT explain the alpha; the flagship's residual alpha survives "
                   "a 6-factor model (still PASSED-borderline: below HLZ 3.0 per TR-18, but a real "
                   "positive alpha, not unmodeled profitability/investment beta).")
    elif t6 >= 1.0:
        _, rmw_t = ff6["betas"]["RMW"]
        _, cma_t = ff6["betas"]["CMA"]
        driver = "RMW" if abs(rmw_t) >= abs(cma_t) else "CMA"
        verdict = (f"WEAKENED -- adding RMW+CMA shrinks the alpha {shrink:+.0%} to t={t6:.2f}; part of the "
                   f"Carhart-4 alpha was {driver} (profitability/investment) beta the 4-factor model missed.")
    else:
        verdict = ("SUBSUMED -- RMW+CMA absorb the alpha (FF6 t<1.0). The flagship's residual 'alpha' "
                   "was factor exposure; downgrade the alpha claim to FAILED-vs-FF5.")
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # chart: alpha-t ladder across benchmarks
    fig, ax = plt.subplots(figsize=(11, 4.8))
    names = list(models)
    tv = [res[n]["t_ols"] for n in names]
    colors = ["#2e7d32" if t >= HLZ else ("#f9a825" if t >= 2.0 else "#c62828") for t in tv]
    ax.bar(range(len(names)), tv, color=colors, width=0.6)
    ax.axhline(HLZ, color="#1b5e20", ls="--", lw=1.4)
    ax.text(len(names) - 0.5, HLZ + 0.03, "HLZ 3.0", color="#1b5e20", fontsize=9, ha="right")
    ax.axhline(2.0, color=GREY_L, ls=":", lw=1.0)
    for i, t in enumerate(tv):
        ax.text(i, t + 0.03, f"{t:+.2f}", ha="center", va="bottom", fontweight="bold", fontsize=9.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("monthly alpha t-stat (OLS)")
    ax.set_ylim(0, max(max(tv) + 0.5, HLZ + 0.4))
    ax.set_title("TR-20: does the flagship's monthly alpha survive richer factor models?\n"
                 "adding RMW (profitability) + CMA (investment) to Carhart-4 -- is the alpha real "
                 "or unmodeled factor beta?", fontsize=10.5)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr20_ff5.png")
    outp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
