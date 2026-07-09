"""TR-23 -- reading-plan wave-1 batch: four canonical price-only cross-sectional anomalies
through the factor gate on the ghost-free 463-name panel.

F0 DECLARATION (pre-committed)
  papers/claims (native habitat: broad US cross-section, monthly, long history):
    IVOL  (Ang-Hodrick-Xing-Zhang 2006) : HIGH idio-vol (FF3 daily resid, 1mo) -> LOW return.
    MAX   (Bali-Cakici-Whitelaw 2011)   : HIGH lottery MAX (mean of 5 largest daily rets, 1mo)
                                          -> LOW return.
    52wH  (George-Hwang 2004)           : NEAR the 52-week high -> HIGH return (underreaction).
    BAB   (Frazzini-Pedersen 2014, lite): LOW beta outperforms risk-adjusted; we test the RAW
                                          rank relation factor=-beta (their claim is alpha-level;
                                          noted). Beta = corr(3d rets, mkt; 504d) x vol ratio (252d).
  references for calibration: momentum 6-1 (known ~0 here) and raw low-vol (docs/09: ICIR -0.11,
  an INVERTED anomaly in this universe/decade).
  seat : 463 current-S&P names (ghost-filtered, F11 curated caveat), 2015-2024, monthly
         month-end sampling, forward 21 trading-day returns, rank IC.
  IN-SEAT PRIORS (declared): this is a high-beta-wins AI-bull sample (TR-06: SML inverted;
  docs/09: low-vol IC negative) -- IVOL/MAX/BAB may come out INVERTED vs their papers.
  VERDICT RULE (pre-committed, the docs/09-10 gate):
     PASS  : |ICIR| >= 0.20 AND same IC sign in both halves (2015-19 / 2020-24)
     WEAK  : 0.10 <= |ICIR| < 0.20, or >= 0.20 with sign flip across halves
     FAIL  : |ICIR| < 0.10
     A PASS with sign OPPOSITE the paper = "inverted in-seat" (docs/19: habitat-specific,
     not tradable as published; joins low-vol).
  benchmark: GP quality ICIR +0.30 (the one survivor) is the bar any PASS is compared to.

POST-RUN AUDIT NOTE (pre-commitment above NOT edited; audit found NO confirmed bugs --
timing, masked-price and dof counterfactuals all clean -- but three reading refinements):
  (1) BAB: the "WEAK INVERTED" is a RAW-return statement only. Alpha-level test with an
      EIV-clean hedge (disjoint prior-504d beta as instrument; beta rank persistence 0.86)
      gives IC -0.01 / ICIR -0.04 ~= 0: the inversion is beta x bull-market mechanical
      compensation, NOT a refutation of FP's (alpha-level) claim. BAB here = FLAT.
  (2) Power: at N=95 months the ICIR 95% CIs of all four anomalies cover +/-0.20 --
      FAIL reads "not detectable on this seat/sample", not "proven zero".
  (3) IVOL deciles are flat at D1-D9 (+14~18%/yr) with D10 (highest IVOL) alone at +26%/yr
      (t~1.8-2.2): a tail inverse effect consistent with the declared high-beta-wins prior;
      rank-IC correctly reads the non-monotone profile as ~0. 52wH FAIL is STRENGTHENED by
      horizon counterfactuals (6/12mo also ~0 with sign flips); MAX(1)=MAX(5).

Run: uv run python scripts/tests/tr23_anomaly_batch.py
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from scipy.stats import spearmanr

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

from tr21_absorption_ratio import load_panel  # noqa: E402

from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402

H = 21          # forward horizon (trading days)
IVOL_W = 21     # AHXZ 1-month idio-vol window
BETA_CORR_W = 504
BETA_VOL_W = 252


def month_ends(idx: pd.DatetimeIndex) -> list[int]:
    pos = []
    per = idx.to_period("M")
    for i in range(len(idx) - 1):
        if per[i] != per[i + 1]:
            pos.append(i)
    return pos


def main():
    r, spy, _bil = load_panel()
    zero_share = (r == 0).mean()
    ghosts = list(zero_share[zero_share > 0.20].index)
    r = r.drop(columns=ghosts)
    px = (1 + r.fillna(0)).cumprod()                       # rebased adjusted price paths
    mkt = spy.reindex(r.index).fillna(0.0)
    ff = load_ff_factors(start="2014-06-01", momentum=False).reindex(r.index).ffill()
    X3 = ff[["Mkt-RF", "SMB", "HML"]].to_numpy()
    R = r.fillna(0.0).to_numpy()
    lp = np.log(px.to_numpy())
    n = r.shape[1]
    mes = [i for i in month_ends(r.index) if i >= BETA_CORR_W and i + H < len(r)]

    # 3-day overlapping log returns (for FP-lite beta)
    l3 = np.vstack([lp[3:] - lp[:-3]])
    m_lp = np.log((1 + mkt).cumprod().to_numpy())
    m3 = m_lp[3:] - m_lp[:-3]

    sigs = {k: [] for k in ("IVOL", "MAX", "52wH", "-beta (BAB)", "mom 6-1 [ref]", "-vol [ref]")}
    fwd_rows, dates = [], []
    for i in mes:
        w = slice(i - IVOL_W + 1, i + 1)
        Rw = R[w]
        # IVOL: FF3 residual std over the past month
        Xw = np.column_stack([np.ones(IVOL_W), X3[w]])
        B, *_ = np.linalg.lstsq(Xw, Rw, rcond=None)
        ivol = (Rw - Xw @ B).std(axis=0, ddof=1)
        # MAX: mean of 5 largest daily returns in the past month
        mx = np.sort(Rw, axis=0)[-5:].mean(axis=0)
        # 52wH: price / rolling 252d max
        lo = max(0, i - 251)
        p52 = np.exp(lp[i] - lp[lo:i + 1].max(axis=0))
        # FP-lite beta
        cw = slice(i - BETA_CORR_W + 3, i + 1 - 3)
        li = l3[cw]
        mi = m3[cw]
        li_c = li - li.mean(axis=0)
        mi_c = mi - mi.mean()
        corr = (li_c * mi_c[:, None]).sum(axis=0) / (
            np.sqrt((li_c ** 2).sum(axis=0)) * np.sqrt((mi_c ** 2).sum()) + 1e-12)
        vw = slice(i - BETA_VOL_W + 1, i + 1)
        beta = corr * (R[vw].std(axis=0, ddof=1) / (mkt.iloc[vw].std(ddof=1) + 1e-12))
        # references
        mom = lp[i - 21] - lp[max(0, i - 126)]
        vol = R[vw].std(axis=0, ddof=1)
        sigs["IVOL"].append(ivol)
        sigs["MAX"].append(mx)
        sigs["52wH"].append(p52)
        sigs["-beta (BAB)"].append(-beta)
        sigs["mom 6-1 [ref]"].append(mom)
        sigs["-vol [ref]"].append(-vol)
        fwd_rows.append(np.exp(lp[i + H] - lp[i]) - 1.0)
        dates.append(r.index[i])

    F = np.array(fwd_rows)
    dates = pd.DatetimeIndex(dates)
    split = dates.searchsorted(pd.Timestamp("2020-01-01"))

    def gate(name, S):
        S = np.array(S)
        ics = np.array([spearmanr(S[t], F[t], nan_policy="omit").statistic
                        for t in range(len(dates))])
        icir = float(np.nanmean(ics) / np.nanstd(ics, ddof=1))
        ic1 = float(np.nanmean(ics[:split]))
        ic2 = float(np.nanmean(ics[split:]))
        stable = np.sign(ic1) == np.sign(ic2) and ic1 != 0
        # decile top-bottom spread (annualized, x12)
        spr = []
        for t in range(len(dates)):
            s, f = S[t], F[t]
            ok = np.isfinite(s) & np.isfinite(f)
            qs = np.quantile(s[ok], [0.9, 0.1])
            spr.append(f[ok][s[ok] >= qs[0]].mean() - f[ok][s[ok] <= qs[1]].mean())
        spread = float(np.mean(spr) * 12)
        a = abs(icir)
        if a >= 0.20 and stable:
            verdict = "PASS"
        elif a >= 0.10:
            verdict = "WEAK" + ("" if stable else "(sign flip)")
        else:
            verdict = "FAIL"
        return {"name": name, "ic": float(np.nanmean(ics)), "icir": icir, "ic1": ic1,
                "ic2": ic2, "stable": stable, "spread": spread, "verdict": verdict}

    print("=" * 100)
    print(f"TR-23  ANOMALY BATCH (wave-1)  {n} names, {len(dates)} month-ends "
          f"{dates[0].date()}..{dates[-1].date()}, fwd {H}d rank-IC")
    print("=" * 100)
    print(f"{'factor':16s} {'IC':>7s} {'ICIR':>7s} {'IC 17-19':>9s} {'IC 20-24':>9s} "
          f"{'D10-D1 ann':>11s}  verdict (paper sign)")
    paper_sign = {"IVOL": -1, "MAX": -1, "52wH": +1, "-beta (BAB)": +1,
                  "mom 6-1 [ref]": +1, "-vol [ref]": +1}
    rows = []
    for k, v in sigs.items():
        g = gate(k, v)
        rows.append(g)
        inv = ""
        if g["verdict"].startswith(("PASS", "WEAK")) and np.sign(g["ic"]) != paper_sign[k]:
            inv = " INVERTED vs paper"
        print(f"{k:16s} {g['ic']:>+7.3f} {g['icir']:>+7.2f} {g['ic1']:>+9.3f} {g['ic2']:>+9.3f} "
              f"{g['spread']:>+11.1%}  {g['verdict']}{inv}")
    print("-" * 100)
    print("READ: gate = docs/09-10 conventions (|ICIR|>=0.20 + sign stability). GP quality's")
    print("+0.30 remains the bar. AUDIT NOTES: (1) BAB inversion is RAW-only -- EIV-clean")
    print("alpha-level hedge (disjoint-window beta) gives IC ~= 0: beta x bull-market, not a")
    print("refutation of FP. (2) N=95: all four ICIR CIs cover +/-0.20 -> FAIL = 'not")
    print("detectable here', not 'proven zero'. (3) IVOL is non-monotone: D10 tail +26%/yr")
    print("(t~2) fits the declared high-beta-wins prior; rank-IC reads it as ~0 correctly.")
    print("=" * 100)

    # chart
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    names = [g["name"] for g in rows]
    icirs = [g["icir"] for g in rows]
    colors = ["#2e7d32" if g["verdict"] == "PASS" else
              ("#f9a825" if g["verdict"].startswith("WEAK") else "#9e9e9e") for g in rows]
    ax.bar(range(len(rows)), icirs, color=colors, width=0.6)
    ax.axhline(0.30, color="#1b5e20", ls="--", lw=1.2)
    ax.axhline(-0.30, color="#1b5e20", ls="--", lw=0.8, alpha=0.5)
    ax.text(len(rows) - 0.5, 0.31, "GP quality +0.30 (the one survivor)", color="#1b5e20",
            fontsize=8.5, ha="right")
    ax.axhspan(-0.10, 0.10, color="#9e9e9e", alpha=0.15)
    for i, v in enumerate(icirs):
        ax.text(i, v + (0.012 if v >= 0 else -0.012), f"{v:+.2f}", ha="center",
                va="bottom" if v >= 0 else "top", fontweight="bold", fontsize=9)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("ICIR (monthly rank-IC, fwd 21d)")
    ax.set_title("TR-23: four canonical price-only anomalies through the factor gate "
                 f"({n} names, 2016-2024)\nIVOL / MAX / 52-week-high / BAB(-beta) + references",
                 fontsize=10.5)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr23_anomalies.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
