"""TR-26 -- Gross-profitability depth grid: does the last surviving factor sit on a plateau?

F0 DECLARATION (pre-committed)
  claim        : the GP (GrossProfit/Assets, Novy-Marx 2013) headline -- mean rank-IC ~ +0.03,
               ICIR ~ +0.30 at the 63d horizon (docs/10) -- is a PLATEAU across (C1) holding
               horizon, (C2) portfolio construction, (C3) calendar years, and (C4) random
               universe halves; not an artifact of the one horizon/construction we happened
               to publish. Depth series report #2 (after TR-25).
  seat         : ~500 S&P names with SEC point-in-time fundamentals (filed-date aligned),
               2015-2026 daily; same panel as docs/10 / TR-23 calibration.
  PRE-COMMITTED CHECKS
    CAL calibration : the 63d rank-IC summary must reproduce the docs/10 headline
                      (mean IC within +-0.01 of +0.03, ICIR within +-0.10 of +0.30);
                      if CAL fails, STOP -- machinery is broken, no verdict may be issued.
    C1 horizon      : forward horizons {21, 63, 126, 252}d. PASS iff mean IC > 0 at ALL
                      four AND ICIR >= 0.15 at >= 3 of 4.
    C2 construction : three daily-rebalanced gross long-short streams from the same factor
                      values -- (a) rank-weighted, (b) quintile Q5-Q1 equal-weight,
                      (c) decile D10-D1 equal-weight. PASS iff all three have positive
                      annualized mean return.
    C3 years        : calendar-year mean 63d IC, 2016..2025 (10 full years). PASS iff
                      >= 65% of years positive.
    C4 breadth      : 40 random half-universes (fixed seeds). PASS iff >= 90% keep
                      positive full-period mean 63d IC.
  DESCRIPTIVE (reported, NOT gated -- the registry WATCH item, quantified):
    D1 recent decay : 2025-01..latest mean IC and the rolling-252d IC path. The WATCH
                      escalation rule stays as pre-committed in TR-24 (full-2026 negative
                      -> F10 re-test); this TR only measures, it does not re-judge.
  VERDICT RULE (pre-committed):
    all four PASS  -> ROBUST-PLATEAU (factor-level; says nothing about tradability net
                      of costs, which docs/10 already scoped)
    any FAIL       -> named sensitivity (HORIZON- / CONSTRUCTION- / ERA- / BREADTH-
                      SENSITIVE) recorded as a standing caveat on the GP registry row
  anti-HARKing : grid cells are probes, not candidates; the published configuration
               (63d rank-IC) stays the reference regardless of which cell scores best.
               No selection -> zero new F5 trials.

Run: uv run python scripts/tests/tr26_gp_depth_grid.py   (~3-6 min)
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
)

HORIZONS = (21, 63, 126, 252)
N_HALVES = 40
SEED = 0


def ls_stream(fw: pd.DataFrame, rets: pd.DataFrame, kind: str) -> pd.Series:
    """Daily-rebalanced gross long-short return stream from factor values known at t,
    applied to day t+1 simple returns."""
    r_next = rets.shift(-1)
    out = {}
    for ts, row in fw.iterrows():
        v = row.dropna()
        if len(v) < 50 or ts not in r_next.index:
            continue
        rr = r_next.loc[ts, v.index].dropna()
        v = v.reindex(rr.index).dropna()
        rr = rr.reindex(v.index)
        if len(v) < 50:
            continue
        if kind == "rank":
            w = v.rank() - (len(v) + 1) / 2.0
            w = w / w.abs().sum()
        else:
            q = 0.2 if kind == "quintile" else 0.1
            k = max(int(len(v) * q), 5)
            top, bot = v.nlargest(k).index, v.nsmallest(k).index
            w = pd.Series(0.0, index=v.index)
            w[top], w[bot] = 0.5 / k, -0.5 / k
        out[ts] = float((w * rr).sum())
    return pd.Series(out).dropna()


def main():
    rng = np.random.default_rng(SEED)
    store = DuckStore("./data")
    syms = [s for s in store.list_symbols("1d") if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    gp = build_all(fund, px, syms)["gross_profitability"]
    rets = px.pct_change()

    print("=" * 100)
    print(f"TR-26  GP DEPTH GRID -- {len(syms)} names, {px.index[0].date()}..{px.index[-1].date()}")
    print("=" * 100)

    # ---- CAL: reproduce the published 63d headline ----
    ic63 = cross_sectional_ic(gp, forward_returns(px, 63))
    s63 = ic_summary(ic63)
    cal = (abs(s63["mean_ic"] - 0.03) <= 0.01) and (abs(s63["icir"] - 0.30) <= 0.10)
    print(f"CAL 63d: mean IC {s63['mean_ic']:+.3f} (target +0.03+-0.01) | "
          f"ICIR {s63['icir']:+.2f} (target +0.30+-0.10) -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("CALIBRATION FAILED -- machinery does not reproduce the published headline; "
              "NO VERDICT issued. Debug before interpreting anything below.")

    # ---- C1: horizons ----
    hor = {}
    for h in HORIZONS:
        s = ic_summary(cross_sectional_ic(gp, forward_returns(px, h)))
        hor[h] = (s["mean_ic"], s["icir"])
        print(f"C1 h={h:>3d}d: mean IC {s['mean_ic']:+.3f} | ICIR {s['icir']:+.2f}")
    c1 = all(v[0] > 0 for v in hor.values()) and sum(v[1] >= 0.15 for v in hor.values()) >= 3
    print(f"C1 horizon: all-positive={all(v[0] > 0 for v in hor.values())}, "
          f"ICIR>=0.15 in {sum(v[1] >= 0.15 for v in hor.values())}/4 -> {'PASS' if c1 else 'FAIL'}")

    # ---- C2: construction ----
    cons = {}
    for kind in ("rank", "quintile", "decile"):
        s = ls_stream(gp, rets, kind)
        ann = float(s.mean() * 252)
        shp = float(s.mean() / s.std() * np.sqrt(252))
        cons[kind] = (ann, shp)
        print(f"C2 {kind:>9s}: gross L-S {ann:+.2%}/yr | Sharpe {shp:+.2f}")
    c2 = all(v[0] > 0 for v in cons.values())
    print(f"C2 construction: -> {'PASS' if c2 else 'FAIL'}")

    # ---- C3: calendar years ----
    yr = ic63.groupby(ic63.index.year).mean()
    yr_full = yr.loc[(yr.index >= 2016) & (yr.index <= 2025)]
    frac_pos = float((yr_full > 0).mean())
    for y, v in yr.items():
        print(f"C3 {y}: mean IC {v:+.3f}")
    c3 = frac_pos >= 0.65
    print(f"C3 years: {int((yr_full > 0).sum())}/{len(yr_full)} full years positive "
          f"({frac_pos:.0%}, rule >=65%) -> {'PASS' if c3 else 'FAIL'}")

    # ---- C4: random half-universes ----
    halves = []
    for k in range(N_HALVES):
        sub = list(rng.choice(syms, size=len(syms) // 2, replace=False))
        ich = cross_sectional_ic(gp[sub], forward_returns(px[sub], 63))
        halves.append(float(ich.mean()))
        if (k + 1) % 10 == 0:
            print(f"  [C4 {k + 1}/{N_HALVES}]")
    halves = np.array(halves)
    frac_h = float((halves > 0).mean())
    c4 = frac_h >= 0.90
    print(f"C4 breadth: {frac_h:.0%} of {N_HALVES} half-universes positive "
          f"(range [{halves.min():+.3f},{halves.max():+.3f}]) -> {'PASS' if c4 else 'FAIL'}")

    # ---- D1: recent decay (reported, not gated) ----
    recent = ic63.loc["2025-01-01":]
    roll = ic63.rolling(252).mean()
    print(f"D1 recent: 2025-01..latest mean IC {recent.mean():+.3f} (n={len(recent)}); "
          f"rolling-252d now {roll.iloc[-1]:+.3f} vs peak {roll.max():+.3f}")

    fails = [n for ok, n in ((c1, "HORIZON-SENSITIVE"), (c2, "CONSTRUCTION-SENSITIVE"),
                             (c3, "ERA-SENSITIVE"), (c4, "BREADTH-SENSITIVE")) if not ok]
    verdict = ("NO VERDICT (calibration failed)" if not cal
               else ("ROBUST-PLATEAU" if not fails else " + ".join(fails)))
    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    ax = axes[0]
    hs = list(hor)
    ax.bar([str(h) + "d" for h in hs], [hor[h][1] for h in hs], color="#1565c0", alpha=0.85)
    ax.axhline(0.15, color="#c62828", ls="--", lw=1.2, label="ICIR 0.15")
    ax.set_title("C1: ICIR by holding horizon", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    colors = ["#2e7d32" if v > 0 else "#c62828" for v in yr.values]
    ax.bar(yr.index.astype(str), yr.values, color=colors, alpha=0.85)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("C3: mean 63d IC by calendar year", fontsize=10)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax = axes[2]
    ax.plot(roll.index, roll.values, color="#1565c0", lw=1.2)
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(pd.Timestamp("2025-01-01"), color="#c62828", ls=":", lw=1.2, label="2025 (WATCH)")
    ax.set_title("D1: rolling 252d mean IC (the WATCH item)", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-26: gross-profitability depth grid -- horizon x construction x era x breadth",
                 fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr26_gp_grid.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
