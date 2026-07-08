"""TR-18 -- inference robustness of the flagship's one PASSED alpha (reading-plan wave 1).

F0 DECLARATION (pre-committed)
  mechanism  : Newey-West HAC (1987) + Politis-Romano stationary bootstrap (1994), applied as
               a stress test of the flagship 5-sleeve combo's Carhart alpha t-stat.
  seat       : the exact full-cost daily returns from tr15_combo_cost.build_combo_cost(1.0),
               regressed on Carhart-4 (Mkt-RF, SMB, HML, UMD), 2015-2026.
  why it matters : attribution.factor_alpha ALREADY uses daily HAC with the Andrews lag
               (~8 lags at n~2800). But the book rebalances monthly, so daily returns carry
               rebalance-induced autocorrelation a short daily lag may under-correct. If the
               headline t=3.38 is an artifact of the lag choice / daily frequency, a longer
               HAC lag, monthly aggregation, or a block bootstrap will expose it.
  FALSIFIABLE CLAIM : the flagship alpha clears the Harvey-Liu-Zhu t>=3.0 bar under EVERY
               inference method below.
  VERDICT RULE (pre-committed):
     min-t across all methods >= 3.0            -> PASSED-robust (flagship verdict stands)
     min-t in [2.0, 3.0)                        -> PARTIAL (downgrade to borderline; t was lag-sensitive)
     min-t < 2.0 on any core method             -> FAILED-inference (headline was an artifact)
  mis-application risk : LOW (same seat as the PASSED claim; this only changes the SE, not the book).

POST-RUN NOTE (added after results; the pre-commitment above is NOT edited):
  An adversarial audit caught two things. (1) The verdict tree originally shipped with an extra
  "BORDERLINE >=2.5 keep-PASSED" tier that was NOT in the F0 rule above -- goalpost-moving; it is
  removed, and the F0 3-bucket rule is applied as written (min-t 2.95 in [2.0,3.0) -> PARTIAL/
  downgrade). (2) The F0 *rationale* ("daily under-corrects autocorrelation, inflating t") was
  wrong: daily residual autocorrelation is ~0/slightly negative, so longer HAC lags RAISE t. The
  real inflation channel is a Dimson lagged-beta effect (daily mkt-beta 0.22 << monthly 0.35, so
  the daily regression mis-attributes factor return as alpha) plus grading a daily t against HLZ's
  monthly-calibrated 3.0 bar. The falsifiable CLAIM and VERDICT RULE stand and are honoured.

Run: uv run python scripts/tests/tr18_inference_robustness.py
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

from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402

COLS = ["Mkt-RF", "SMB", "HML", "UMD"]
HLZ = 3.0


def load_ff_monthly(start="2015-01-01"):
    """Real monthly Ken French Carhart-4 factors (not compounded from daily), for method C."""
    import io
    import urllib.request
    import zipfile

    def direct(ds):
        url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{ds}_CSV.zip"
        raw = urllib.request.urlopen(url, timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
        lines = text.splitlines()
        hdr = next(i for i, ln in enumerate(lines) if ln.strip().startswith(","))
        df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), index_col=0)
        df.index = df.index.astype(str).str.strip()
        df = df[df.index.str.fullmatch(r"\d{6}")]           # keep YYYYMM monthly rows only
        df.index = pd.to_datetime(df.index, format="%Y%m").to_period("M")
        return df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")

    try:
        from pandas_datareader import data as pdr
        ff = pdr.DataReader("F-F_Research_Data_Factors", "famafrench", start)[0] / 100.0
        mom = pdr.DataReader("F-F_Momentum_Factor", "famafrench", start)[0] / 100.0
        mom.columns = ["UMD"]
        ff = ff.join(mom)
        ff.index = ff.index.astype("period[M]")
    except Exception:
        ff = direct("F-F_Research_Data_Factors") / 100.0
        mom = direct("F-F_Momentum_Factor") / 100.0
        mom.columns = ["UMD"]
        ff = ff.join(mom)
        ff.columns = [str(c).strip() for c in ff.columns]
    return ff.loc[ff.index >= pd.Period(start, "M")]


def aligned():
    rp = tr15.build_combo_cost(1.0)
    ff = load_ff_factors(start="2015-01-01")
    cmn = rp.index.intersection(ff.index)
    rp = rp.reindex(cmn).astype(float)
    ff = ff.reindex(cmn).astype(float)
    y = rp - ff["RF"]                       # daily excess return of the book
    X = ff[COLS]
    return y, X, ff, rp


def hac_alpha(y, X, lags):
    d = sm.add_constant(X)
    m = sm.OLS(y, d).fit(cov_type="HAC", cov_kwds={"maxlags": max(int(lags), 1)})
    return float(m.params["const"]), float(m.tvalues["const"])


def andrews_lag(n):
    return int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def stationary_bootstrap_alpha(y, X, n_boot=3000, exp_block=21, seed=0):
    """Politis-Romano (1994): resample consecutive blocks of geometric length ~exp_block,
    refit OLS each draw, return the distribution of the intercept (alpha)."""
    rng = np.random.default_rng(seed)
    Xc = sm.add_constant(X).to_numpy()
    yv = y.to_numpy()
    n = len(yv)
    p = 1.0 / exp_block
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, dtype=np.int64)
        i = int(rng.integers(0, n))
        for t in range(n):
            idx[t] = i
            i = int(rng.integers(0, n)) if rng.random() < p else (i + 1 if i + 1 < n else 0)
        beta, *_ = np.linalg.lstsq(Xc[idx], yv[idx], rcond=None)
        out[b] = beta[0]
    return out


def main():
    y, X, _ff, rp = aligned()
    n = len(y)
    print("=" * 100)
    print("TR-18  INFERENCE ROBUSTNESS OF THE FLAGSHIP CARHART ALPHA (Newey-West + stationary bootstrap)")
    print(f"seat: full-cost 5-sleeve combo, {rp.index[0].date()}..{rp.index[-1].date()}, n={n} daily obs")
    print("=" * 100)
    print(f"{'inference method':46s} {'ann alpha':>10s} {'t':>7s} {'>=3.0?':>7s}")

    rows = []

    def add(label, a_daily, t):
        ok = "yes" if t >= HLZ else "NO"
        rows.append((label, a_daily * 252, t))
        print(f"{label:46s} {a_daily*252:>+9.2%} {t:>+7.2f} {ok:>7s}")

    # A. baseline: daily HAC, Andrews lag (this is what attribution.py reports)
    la = andrews_lag(n)
    a0, t0 = hac_alpha(y, X, la)
    add(f"A. daily HAC, Andrews lag ({la})  [baseline]", a0, t0)
    # B. daily HAC, longer lags (1mo, 3mo of trading days)
    for lg in (21, 63):
        a, t = hac_alpha(y, X, lg)
        add(f"B. daily HAC, lag={lg} ({lg//21}mo)", a, t)
    # daily market beta (for the Dimson/lagged-beta diagnostic)
    md = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": max(la, 1)})
    beta_d = float(md.params["Mkt-RF"])
    # C. monthly frequency with REAL Ken French monthly factors (not compounded daily).
    #    Book monthly return = exact compound of daily book returns; RHS = true monthly Carhart-4.
    #    This is the FREQUENCY-APPROPRIATE test: it matches BOTH the monthly rebalance clock AND
    #    HLZ's native calibration frequency (published factor t-stats are monthly). Report OLS + HAC.
    rpm = (1 + rp).groupby(rp.index.to_period("M")).prod() - 1     # exact monthly book return
    ffm = load_ff_monthly("2015-01-01")
    cmn = rpm.index.intersection(ffm.index)
    ym = (rpm.reindex(cmn) - ffm.reindex(cmn)["RF"]).dropna()
    Xm = ffm.reindex(ym.index)[COLS]
    ym.index = ym.index.to_timestamp()
    Xm.index = Xm.index.to_timestamp()
    m_ols = sm.OLS(ym, sm.add_constant(Xm)).fit()
    tm_ols = float(m_ols.tvalues["const"])
    beta_m = float(m_ols.params["Mkt-RF"])
    am, tm = hac_alpha(ym, Xm, andrews_lag(len(ym)))

    def add_monthly(label, t):
        ok = "yes" if t >= HLZ else "NO"
        rows.append((label, am * 12, t))
        print(f"{label:46s} {am*12:>+9.2%} {t:>+7.2f} {ok:>7s}")

    add_monthly(f"C1. MONTHLY OLS, real KF factors (n={len(ym)})", tm_ols)
    add_monthly(f"C2. MONTHLY HAC, real KF factors (n={len(ym)})", tm)
    # D. stationary bootstrap (Politis-Romano). NOTE: t = alpha_hat/SE_boot is a bootstrap-SE
    #    ECHO of the daily HAC (same point alpha, SE_boot~=SE_HAC), resampling DAILY pairs -- it
    #    operates at the inflated daily frequency, so it confirms A, it is NOT independent evidence.
    boot = stationary_bootstrap_alpha(y, X, n_boot=3000, exp_block=21, seed=0)
    a_pt, _ = hac_alpha(y, X, la)
    t_boot = a_pt / boot.std(ddof=1)
    p_le0 = float((boot <= 0).mean())
    add("D. daily stationary bootstrap (echoes A, not independent)", a_pt, t_boot)
    print(f"{'   bootstrap P(alpha<=0)':46s} {'':>10s} {p_le0:>7.3f}")
    print(f"\nDIMSON DIAGNOSTIC: market beta = {beta_d:.2f} daily vs {beta_m:.2f} monthly. The daily")
    print("regression UNDER-states the leveraged+trend book's true market exposure (lagged beta),")
    print(f"so it mis-attributes factor return as alpha: the daily alpha {a0*252:+.2%}/t {t0:.2f} is")
    print(f"INFLATED; the honest monthly alpha is {am*12:+.2%}/yr (OLS t={tm_ols:.2f}, HAC t={tm:.2f}).")

    print("-" * 100)
    # VERDICT per the PRE-COMMITTED F0 rule (3 buckets). The frequency-appropriate (monthly)
    # estimates are the ones held against HLZ's monthly-calibrated bar.
    ts = [t for _, _, t in rows]
    mint = min(ts)
    if mint >= HLZ:
        verdict = "PASSED-robust (flagship clears HLZ 3.0 under every method)"
    elif mint >= 2.0:
        verdict = (f"PARTIAL -- DOWNGRADE. Per the pre-committed F0 rule, min-t={mint:.2f} in [2.0,3.0) "
                   f"means the flagship's 'clears HLZ 3.0' claim does NOT stand. The monthly (frequency-"
                   f"appropriate) t is {tm_ols:.2f} OLS / {tm:.2f} HAC, both < 3.0; the daily t=3.4 was "
                   f"inflated by understated daily beta ({beta_d:.2f} vs {beta_m:.2f} monthly) and by "
                   f"grading a daily t against HLZ's monthly bar. Reverts to the docs/08 reading (t~2.64).")
    else:
        verdict = "FAILED-inference (headline was an artifact of the SE method)"
    print(f"min t across methods = {mint:+.2f}  ->  VERDICT: {verdict}")
    print("READ: the alpha is REAL and robustly positive (bootstrap P(a<=0)=0.001); it only misses")
    print("HLZ 3.0 at the frequency-appropriate MONTHLY clock (t=2.64 OLS / 2.95 HAC, n=131), which")
    print("matches both the monthly rebalance and HLZ's monthly calibration. The daily t=3.4 is the")
    print("inflated one (Dimson lagged-beta). Honest: a real alpha that does NOT clear HLZ 3.0.")
    print("=" * 100)

    # chart
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [r[0].split("  [")[0].split(" (n=")[0] for r in rows]
    tv = [r[2] for r in rows]
    colors = ["#2e7d32" if t >= HLZ else "#c62828" for t in tv]
    ax.barh(range(len(rows))[::-1], tv, color=colors, height=0.6)
    ax.axvline(HLZ, color="#1b5e20", ls="--", lw=1.5)
    ax.text(HLZ + 0.03, len(rows) - 0.6, "HLZ t=3.0 bar", color="#1b5e20", fontsize=9, va="top")
    for i, t in enumerate(tv[::-1]):
        ax.text(t + 0.03 if t >= 0 else t - 0.03, i, f"{t:+.2f}",
                va="center", ha="left" if t >= 0 else "right", fontweight="bold", fontsize=9)
    ax.set_yticks(range(len(rows))[::-1])
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Carhart alpha t-statistic")
    ax.set_xlim(0, max(max(tv) + 0.6, HLZ + 0.6))
    ax.set_title("TR-18: the flagship's t=3.38 is a DAILY-frequency artifact\n"
                 "at the frequency-appropriate monthly clock (matches HLZ's calibration) it is 2.64-2.95, "
                 "below HLZ 3.0", fontsize=10.5)
    ax.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr18_inference.png")
    outp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
