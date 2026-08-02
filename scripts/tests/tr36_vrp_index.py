"""TR-36 -- VRP at the index-benchmark level: CBOE PUT / BXM (docs/25 breakout #1, plan A5).

Why this now: six independent proofs say the $0 US-large-cap-daily seat is mined out.
The one literature-backed NEW risk premium reachable at $0 is the variance/option-
selling premium (Carr-Wu 2009: a priced risk premium, NOT market timing -- compatible
with the timing iron law). CBOE's PUT index (systematic cash-secured ATM SPX
put-writing, monthly roll) embeds REAL option prices at the rolls, so index-level
existence is testable TODAY; own-chain implementability follows in phase B3.

THE HONEST QUESTION (and the iron-law trap to avoid): option selling is mechanically
short volatility. A premium that is merely "short vol beta" would be SPANNED by the
same volatility-timing controls that killed every timing claim (TR-17b/31). So the
decisive check is spanning vs the Nagel control triple, not raw Sharpe.

F0 DECLARATION (pre-committed)
  claim : systematic index option selling earns a premium beyond (a) equity beta and
        (b) the volatility-timing control triple, at the index-benchmark level.
  seat  : CBOE PUT 1991-06..latest (primary; official daily history), BXM 2002+
        (cross-check); monthly EOM returns; controls built from FF DAILY market
        (vol-std market, 1/RV Moreira-Muir, linear-decay-12m VTM); monthly HAC
        inference (TR-18 clock).
  PRE-COMMITTED CHECKS
    CAL : parse fidelity vs documented stylized facts: PUT ann vol in [8%, 14%] AND
          CAPM beta vs market in [0.45, 0.80] AND monthly coverage gap-free.
          Fail -> STOP.
    C1  : existence beyond equity beta: PUT CAPM alpha (monthly, HAC) t >= 2.
    C2  : (decisive) spanning vs Nagel triple + market: alpha-t >= 2 -> NEW premium;
          < 2 -> SPANNED (the iron law reaches option selling at index level).
    C3  : the premium's price: crash profile (worst month, MDD, down-beta vs up-beta
          asymmetry) -- reported, no gate.
    C4  : BXM same battery + FF5+UMD spanning robustness on PUT.
  VERDICT RULE (pre-committed):
    CAL fail            -> INVALID-TEST
    C1 & C2             -> PREMIUM-CONFIRMED (B3 implementability phase green-lit)
    C1 & !C2            -> SPANNED-BY-VOL-CONTROLS (iron law extended; B3 deprioritized)
    !C1                 -> NO-PREMIUM (beyond equity beta, at index level)
  anti-HARKing : single pre-registered battery; no window/spec search; trials +1 family.
  honest scope : index excludes an implementer's costs (spreads/fees) -- existence
        test only; implementability = B3 with our own chains. PUT file starts 1991
        (CBOE's own backfill), not the 1986 inception cited in white papers.

Run: uv run python scripts/tests/tr36_vrp_index.py   (~1 min)
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from trading_analysis.factors.attribution import load_ff_factors, load_ff_factors_monthly  # noqa: E402

UA = {"User-Agent": "trading-analysis research (romarinhsieh@gmail.com)"}
HAC = {"maxlags": 3}


def load_cboe(name: str) -> pd.Series:
    cache = Path(f"data/cboe_{name.lower()}.parquet")
    if cache.exists():
        s = pd.read_parquet(cache)[name]
        s.index = pd.to_datetime(s.index)
        return s
    url = f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{name}_History.csv"
    req = urllib.request.Request(url, headers=UA)
    d = pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=60).read().decode()))
    s = pd.Series(pd.to_numeric(d[name], errors="coerce").to_numpy(),
                  index=pd.to_datetime(d["DATE"]), name=name).dropna()
    pd.DataFrame({name: s.to_numpy()}, index=s.index.astype(str)).to_parquet(cache)
    return s


def monthly_ret(level: pd.Series) -> pd.Series:
    m = level.groupby(level.index.to_period("M")).last()
    return m.pct_change().dropna()


def reg(y: pd.Series, X: pd.DataFrame) -> tuple[float, float]:
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    res = sm.OLS(df["y"], sm.add_constant(df.drop(columns="y"))).fit(
        cov_type="HAC", cov_kwds=HAC)
    return float(res.params["const"]), float(res.tvalues["const"])


def beta_of(y: pd.Series, x: pd.Series) -> float:
    df = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    return float(sm.OLS(df["y"], sm.add_constant(df["x"])).fit().params["x"])


def main():
    # DATA-TRUTH NOTE (first-run CAL catch): the free CBOE file carries only 7 scattered
    # points before 2007 (143 month gaps -> fake 25% "monthly" vol). Usable daily era =
    # 2007+; the 1986-2006 white-paper era is NOT in the free file (info cost if ever
    # needed). Seat re-declared to the gap-free daily span -- a data limitation, not a
    # goalpost move (CAL did its job).
    put = load_cboe("PUT").loc["2007-01-01":]
    bxm = load_cboe("BXM").loc["2002-04-01":]
    ffd = load_ff_factors(start="1988-01-01", momentum=False)
    mkt_d, rf_d = ffd["Mkt-RF"] + ffd["RF"], ffd["RF"]
    ffm = load_ff_factors_monthly(start="1988-01-01", momentum=True)

    print("=" * 100)
    print(f"TR-36  VRP AT INDEX LEVEL -- CBOE PUT {put.index[0].date()}..{put.index[-1].date()}, "
          f"BXM {bxm.index[0].date()}..")
    print("=" * 100)

    put_m = monthly_ret(put)
    bxm_m = monthly_ret(bxm)
    mkt_m = (1 + mkt_d).groupby(mkt_d.index.to_period("M")).prod() - 1
    rf_m = (1 + rf_d).groupby(rf_d.index.to_period("M")).prod() - 1
    rv_m = (mkt_d - rf_d).pow(2).groupby(mkt_d.index.to_period("M")).sum()

    # coverage check + trim to full months
    gaps = pd.period_range(put_m.index[1], put_m.index[-2], freq="M").difference(put_m.index)
    put_x = (put_m - rf_m).dropna()
    mkt_x = (mkt_m - rf_m).reindex(put_x.index)

    # ---- CAL ----
    vol_ann = float(put_m.std() * np.sqrt(12))
    beta = beta_of(put_x, mkt_x)
    cal = (0.08 <= vol_ann <= 0.14) and (0.45 <= beta <= 0.80) and (len(gaps) == 0)
    print(f"CAL: PUT ann vol {vol_ann:.1%} (band 8-14%), CAPM beta {beta:.2f} "
          f"(band 0.45-0.80), month gaps {len(gaps)} -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: INVALID-TEST -- parse/stylized-fact fidelity failed.")
        return

    sh_put = float(put_x.mean() / put_x.std() * np.sqrt(12))
    sh_mkt = float(mkt_x.mean() / mkt_x.std() * np.sqrt(12))
    print(f"headline: PUT exSharpe {sh_put:+.2f} vs market {sh_mkt:+.2f} | "
          f"PUT CAGR {(1+put_m).prod()**(12/len(put_m))-1:+.1%} vol {vol_ann:.1%}")

    # ---- C1 CAPM alpha ----
    a1, t1 = reg(put_x, mkt_x.rename("mkt"))
    c1 = t1 >= 2
    print(f"C1 CAPM alpha: {a1*12*100:+.2f}%/yr (HAC t={t1:+.2f}, rule >=2) -> "
          f"{'PASS' if c1 else 'FAIL'}")

    # ---- C2 Nagel triple spanning (the decisive check) ----
    sig12 = mkt_x.rolling(12).std()
    volstd = (mkt_x / sig12).rename("volstd")
    mm = (mkt_x / rv_m.reindex(mkt_x.index).replace(0, np.nan)).rename("mm")
    wgt = np.arange(12, 0, -1, dtype=float)
    wgt /= wgt.sum()
    yv = (mkt_x / sig12).to_numpy()
    pos = np.full(len(mkt_x), np.nan)
    for i in range(12, len(mkt_x)):
        pos[i] = float((wgt * yv[i - 12:i][::-1]).sum())
    vtm = (pd.Series(pos, index=mkt_x.index) * (mkt_x / sig12)).rename("vtm")
    X2 = pd.concat([mkt_x.rename("mkt"), volstd, mm, vtm], axis=1)
    X2 = X2.div(X2.std())                        # scale-free controls
    a2, t2 = reg(put_x, X2)
    c2 = t2 >= 2
    print(f"C2 spanning (mkt + vol-std + MM + VTM): alpha {a2*12*100:+.2f}%/yr "
          f"(HAC t={t2:+.2f}, rule >=2) -> {'PASS' if c2 else 'FAIL'}")

    # ---- C3 crash profile ----
    nav = (1 + put_m).cumprod()
    mddv = float((nav / nav.cummax() - 1).min())
    worst = put_m.min()
    up = put_x[mkt_x > 0]
    dn = put_x[mkt_x < 0]
    b_up = beta_of(up, mkt_x.reindex(up.index))
    b_dn = beta_of(dn, mkt_x.reindex(dn.index))
    print(f"C3 the premium's price: MDD {mddv:+.1%}, worst month {worst:+.1%} "
          f"({put_m.idxmin()}), up-beta {b_up:.2f} vs down-beta {b_dn:.2f} "
          f"(asymmetry {b_dn-b_up:+.2f})")

    # ---- C4 BXM + FF5/UMD robustness ----
    bxm_x = (bxm_m - rf_m).dropna()
    a4, t4 = reg(bxm_x, mkt_x.reindex(bxm_x.index).rename("mkt"))
    X4 = X2.reindex(bxm_x.index)
    a4b, t4b = reg(bxm_x, X4)
    ff5 = ffm.drop(columns=[c for c in ("RF",) if c in ffm.columns])
    y5 = put_x.copy()
    a5, t5 = reg(y5, ff5.reindex(y5.index))
    print(f"C4 BXM: CAPM alpha {a4*12*100:+.2f}%/yr (t={t4:+.2f}); triple-spanned alpha "
          f"{a4b*12*100:+.2f}%/yr (t={t4b:+.2f}) | PUT FF3+UMD alpha {a5*12*100:+.2f}%/yr "
          f"(t={t5:+.2f})")

    if c1 and c2:
        v = "PREMIUM-CONFIRMED -- option-selling premium survives equity beta AND the vol-timing triple; B3 implementability green-lit."
    elif c1:
        v = ("SPANNED-BY-VOL-CONTROLS -- a CAPM alpha exists but the vol-timing triple "
             "absorbs it: at index level, option selling is vol-managed equity in "
             "disguise. The iron law extends; B3 deprioritized.")
    else:
        v = "NO-PREMIUM -- no alpha beyond equity beta at the index-benchmark level."
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))
    ax = axes[0]
    t = put_m.index.to_timestamp()
    ax.plot(t, (1 + put_m).cumprod(), lw=1.2, color="#1565c0", label="PUT (put-write)")
    mm_nav = (1 + mkt_m.reindex(put_m.index)).cumprod()
    ax.plot(t, mm_nav, lw=1.0, color="#757575", label="market TR")
    bt = bxm_m.index.to_timestamp()
    ax.plot(bt, (1 + bxm_m).cumprod() * float((1 + put_m).cumprod().reindex(bxm_m.index).iloc[0] or 1),
            lw=1.0, color="#2e7d32", alpha=0.8, label="BXM (covered call, rebased)")
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    ax.set_title(f"index level 1991-2026 | PUT exSharpe {sh_put:+.2f} vs mkt {sh_mkt:+.2f}",
                 fontsize=10)
    ax = axes[1]
    labs = ["CAPM\nalpha-t", "+ vol-timing\ntriple", "FF3+UMD\nalpha-t", "BXM CAPM\nalpha-t",
            "BXM triple\nalpha-t"]
    vals = [t1, t2, t5, t4, t4b]
    ax.bar(labs, vals, color=["#1565c0", "#c62828", "#90a4ae", "#2e7d32", "#f9a825"], alpha=0.9)
    ax.axhline(2, color="#c62828", ls="--", lw=1, label="t=2")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("alpha t (HAC, monthly)")
    ax.set_title("does the premium survive the controls?", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-36: option-selling premium at the index-benchmark level (CBOE PUT/BXM)",
                 fontsize=12)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr36_vrp_index.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
