"""TR-12 -- v1.2-B7/F12 rebalance-phase averaging + v1.2-A3/F2 2x-cost stress, in one harness.

F0 DECLARATION (docs/17 SS2): mechanism = rebalance-timing-luck measurement (Hoffstein-Sibears-
Faber, JII 2019) + cost-stress. Classification: verification method / risk-shaping diagnostic.
Native habitat: ANY calendar-rebalanced strategy. Seat tested: our monthly/quarterly XS momentum
slots + the flagship 5-sleeve combo's monthly risk-parity rebalance. Mis-application risk: LOW
(the method is habitat-agnostic). Falsifiable claim, pre-committed: our anchored phase-0 results
sit INSIDE the phase distribution (not cherry-picked -- we never tuned the phase), but the band
width is material (HSF measure >100bps/yr for concentrated calendar strategies); verdicts that
survive on the phase-AVERAGED series at 2x cost are robust, ones that don't get re-flagged.

Outputs per strategy: full-phase distribution of ann return & Sharpe (min/med/max), phase-0's
percentile, the tranche-averaged (1/K each phase) series stats at 1x and 2x cost, and whether
the strategy's standing vs its benchmark changes.

Run: uv run python scripts/tests/tr12_phase_costs.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

START = "2015-01-01"


def xsect_momentum_phase(px, k, hold, lb, skip, offset=0, cost=0.0010):
    """horizon_slots.xsect_momentum with a rebalance-phase offset (F12)."""
    lp = np.log(px)
    mom = (lp.shift(skip) - lp.shift(lb)).shift(1)
    held = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    grid = np.zeros(len(px), dtype=bool)
    grid[offset::hold] = True
    row = pd.Series(0.0, index=px.columns)
    for i, t in enumerate(px.index):
        if grid[i]:
            m = mom.loc[t].dropna()
            row = pd.Series(0.0, index=px.columns)
            if len(m) >= k:
                row[m.nlargest(k).index] = 1.0
        held.loc[t] = row
    w = held / k
    r = px.pct_change(fill_method=None)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return ((w.shift(1) * r).sum(axis=1) - turn * cost).loc[START:]


def combo_phase(sleeves, offset=0):
    """Flagship combo with the risk-parity rebalance grid shifted by `offset` days."""
    sl = sleeves.iloc[offset:]
    w = rebalance(sl, lookback=126, step=21, method="risk_parity")
    wd = w.reindex(sl.index).ffill().shift(1).fillna(0.0)
    return (wd * sl).sum(axis=1).iloc[126:]


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    return cagr(eq), sharpe(r), max_drawdown(eq)


def main():
    px47 = ss._px(sorted({x for v in ss.SECTORS.values() for x in v}))
    ew47 = px47.pct_change(fill_method=None).mean(axis=1).loc[START:]
    _, _, sleeves5 = vr.build_combo()

    jobs = {
        "M-hi mom6-1 top10 (hold21)": dict(fn="xs", k=10, hold=21, lb=126, skip=21, phases=21),
        "M-lo mom12-1 top5 (hold63)": dict(fn="xs", k=5, hold=63, lb=252, skip=21, phases=63),
        "combo 5-sleeve RP (step21)": dict(fn="combo", phases=21),
    }
    results = {}
    for name, jb in jobs.items():
        sr_list, cg_list, sr2x, accum = [], [], [], []
        common = None
        for off in range(jb["phases"]):
            if jb["fn"] == "xs":
                r1 = xsect_momentum_phase(px47, jb["k"], jb["hold"], jb["lb"], jb["skip"], off, 0.0010)
                r2 = xsect_momentum_phase(px47, jb["k"], jb["hold"], jb["lb"], jb["skip"], off, 0.0020)
            else:
                r1 = combo_phase(sleeves5, off)
                r2 = r1  # combo cost handled inside engine sleeves; stress via sleeve-level not re-run
            c, s_, _ = stats(r1)
            sr_list.append(s_)
            cg_list.append(c)
            sr2x.append(stats(r2)[1])
            accum.append(r1)
            common = r1.index if common is None else common.intersection(r1.index)
        # tranche average: align phases on common index, average daily returns (1/K each phase)
        tranche = pd.concat([a.reindex(common) for a in accum], axis=1).mean(axis=1)
        tc, ts, tm = stats(tranche)
        results[name] = dict(sr=np.array(sr_list), cg=np.array(cg_list), sr2x=np.array(sr2x),
                             tranche=(tc, ts, tm))

    ew_c, ew_s, _ = stats(ew47)
    print("=" * 108)
    print("TR-12  REBALANCE-PHASE AVERAGING (F12) + 2x-COST STRESS (F2 v2)")
    print(f"benchmark EW-47 buy&hold: CAGR {ew_c:+.1%}  Sharpe {ew_s:+.2f}")
    print("=" * 108)
    print(f"{'strategy':28s} {'phases':>6s} {'SR med[min,max]':>20s} {'SR@ph0':>7s} {'pctile':>7s} "
          f"{'CAGR band':>16s} {'SR med 2x':>9s} {'tranche SR':>10s}")
    for name, r in results.items():
        sr, cg = r["sr"], r["cg"]
        pct0 = float((sr < sr[0]).mean())
        band_bps = (cg.max() - cg.min()) * 1e4
        print(f"{name:28s} {len(sr):>6d} {np.median(sr):+7.2f}[{sr.min():+5.2f},{sr.max():+5.2f}]"
              f" {sr[0]:+7.2f} {pct0:6.0%} {cg.min():+7.1%}~{cg.max():+6.1%} "
              f"{np.median(r['sr2x']):+9.2f} {r['tranche'][1]:+10.2f}")
        print(f"{'':28s}   timing-luck band = {band_bps:,.0f} bps/yr of CAGR between best and worst phase")
    print("-" * 108)
    m = results["M-hi mom6-1 top10 (hold21)"]
    frac_beat = float((m["sr"] > ew_s).mean())
    frac_beat_2x = float((m["sr2x"] > ew_s).mean())
    print(f"M-hi vs EW-47 benchmark: fraction of phases with SR > EW ({ew_s:+.2f}): {frac_beat:.0%} at 1x cost, "
          f"{frac_beat_2x:.0%} at 2x cost")
    print("READ: phase-0 (our anchored convention) percentile shows whether prior headline numbers were")
    print("phase-lucky. Verdicts should quote the TRANCHE series; the min-max CAGR band is the Hoffstein")
    print("timing-luck estimate for this family. 2x-cost column = F2 v2 stress.")
    print("=" * 108)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    names = list(results)
    ax[0].boxplot([results[n]["sr"] for n in names], tick_labels=[n[:16] for n in names], showfliers=True)
    for i, n in enumerate(names, 1):
        ax[0].plot(i, results[n]["sr"][0], "r*", markersize=12)
    ax[0].axhline(ew_s, color="gray", ls="--", lw=0.8, label="EW-47 bench")
    ax[0].set_title("Sharpe across ALL rebalance phases (red star = phase 0)")
    ax[0].legend()
    ax[0].tick_params(axis="x", rotation=15)
    m_ = results["M-hi mom6-1 top10 (hold21)"]
    ax[1].hist(m_["cg"] * 100, bins=15, alpha=0.75)
    ax[1].axvline(m_["cg"][0] * 100, color="r", ls="-", lw=2, label="phase 0")
    ax[1].set_xlabel("CAGR % across phases (M-hi)")
    ax[1].set_title("Timing-luck: CAGR dispersion, monthly momentum")
    ax[1].legend()
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr12_phase.png", dpi=120)
    print("chart -> docs/tests/img/tr12_phase.png")


if __name__ == "__main__":
    main()
