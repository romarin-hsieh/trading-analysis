"""TR-29 -- Holding-period x turnover curves for the flagship's momentum sleeves.

F0 DECLARATION (pre-committed)
  claim        : the flagship's two selection sleeves (equity momentum k=10 and defensive
               dual momentum k=4) use hold=21 by construction. Depth question (the
               generalized holding-period x turnover curve the depth series promised):
               does hold=21 sit ON the net-of-cost plateau, or did we leave a better
               holding period on the table / pick a fragile point?
  seat         : same sleeve construction as vr.build_combo (sector universe, 2015-2026,
               net of 5bps fee + 5bps slippage per side via the backtest engine).
  PRE-COMMITTED CHECKS
    CAL          : the hold=21 sweep cell must equal the flagship's actual sleeve input
                   (same code path; corr > 0.999 vs vr.build_combo's series).
    C1 (equity_mom, k=10): hold in {5, 10, 21, 42, 63}. PASS iff
                   net excess Sharpe(21) >= max over grid - 0.10  (plateau membership).
    C2 (defensive dual momentum, k=4): same grid and rule.
    D1 (descriptive, not gated): annual one-way turnover and estimated cost drag
                   (turnover x 10bps round-trip) per hold -- the turnover-cost story
                   quantified per sleeve.
  VERDICT RULE (pre-committed):
    C1 & C2 PASS -> HOLD-PLATEAU (flagship holding choice robust; curves published)
    any FAIL     -> HOLD-SENSITIVE(named sleeve) -- the better cell is recorded but the
                   flagship configuration is NOT changed mid-flight (anti-HARKing);
                   any change would require its own F0 + out-of-sample discipline.
  anti-HARKing : sweep cells are probes; zero new F5 trials; flagship config unchanged
               regardless of outcome.

Run: uv run python scripts/tests/tr29_holding_turnover.py   (~2-4 min)
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
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402

HOLDS = (5, 10, 21, 42, 63)
COST_RT = 0.0010          # 5bps fee + 5bps slippage, per side -> 10bps one-way notional


def ex_sharpe(r: pd.Series, rf: pd.Series) -> float:
    ex = (r - rf.reindex(r.index).fillna(0.0)).dropna()
    return float(ex.mean() / ex.std() * np.sqrt(252))


def turnover_ann(direction: pd.DataFrame, k: int) -> float:
    w = direction.fillna(0) / k
    dt = w.diff().abs().sum(axis=1) / 2.0        # one-way fraction of book per day
    return float(dt.mean() * 252)


def sweep_equity_mom(px, spy, rf):
    rows = {}
    for h in HOLDS:
        d = ss.momentum_trend_direction(px, spy, k=10, hold=h, regime=True)
        res = ss.run_engine(px, d, spy, 10)
        rows[h] = {"sr": ex_sharpe(res.returns, rf), "to": turnover_ann(d, 10)}
    return rows


def sweep_dual_mom(allsyms, rf):
    rows = {}
    for h in HOLDS:
        _cfg, res = ss.strat_dual_momentum("def", allsyms, k=4, hold=h)
        rows[h] = {"sr": ex_sharpe(res.returns, rf), "to": np.nan}
    return rows


def main():
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    px = ss._px(allsyms)
    spy = ss._spy().reindex(px.index).ffill()
    rf = load_ff_factors(start="2015-01-01")["RF"]

    print("=" * 100)
    print(f"TR-29  HOLDING x TURNOVER -- momentum sleeves, {px.index[0].date()}..{px.index[-1].date()}")
    print("=" * 100)

    # CAL: hold=21 equals the flagship sleeve input
    d21 = ss.momentum_trend_direction(px, spy, k=10, hold=21, regime=True)
    r21 = ss.run_engine(px, d21, spy, 10).returns
    _rp, _ew, sleeves = vr.build_combo()
    flag = sleeves["equity_mom"]
    cmn = r21.index.intersection(flag.index)
    corr = float(r21.reindex(cmn).corr(flag.reindex(cmn)))
    cal = corr > 0.999
    print(f"CAL: hold=21 sweep cell vs flagship equity_mom corr = {corr:.4f} -> "
          f"{'PASS' if cal else 'FAIL'}")
    if not cal:
        print("CALIBRATION FAILED -- sweep does not reproduce the flagship sleeve; stop.")
        return

    # C1 equity momentum
    eq = sweep_equity_mom(px, spy, rf)
    for h in HOLDS:
        drag = eq[h]["to"] * COST_RT * 1e4
        print(f"C1 equity_mom hold={h:>2d}: net exSharpe {eq[h]['sr']:+.2f} | "
              f"turnover {eq[h]['to']:.1f}x/yr | est. cost drag {drag:.0f} bps/yr")
    best1 = max(v["sr"] for v in eq.values())
    c1 = eq[21]["sr"] >= best1 - 0.10
    print(f"C1: SR(21)={eq[21]['sr']:+.2f} vs grid max {best1:+.2f} (rule: within 0.10) -> "
          f"{'PASS' if c1 else 'FAIL'}")

    # C2 defensive dual momentum
    dm = sweep_dual_mom(allsyms, rf)
    for h in HOLDS:
        print(f"C2 dual_mom  hold={h:>2d}: net exSharpe {dm[h]['sr']:+.2f}")
    best2 = max(v["sr"] for v in dm.values())
    c2 = dm[21]["sr"] >= best2 - 0.10
    print(f"C2: SR(21)={dm[21]['sr']:+.2f} vs grid max {best2:+.2f} (rule: within 0.10) -> "
          f"{'PASS' if c2 else 'FAIL'}")

    fails = [n for ok, n in ((c1, "equity_mom"), (c2, "dual_mom")) if not ok]
    verdict = "HOLD-PLATEAU" if not fails else "HOLD-SENSITIVE(" + "+".join(fails) + ")"
    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axes[0]
    xs = list(HOLDS)
    ax.plot(xs, [eq[h]["sr"] for h in xs], "o-", color="#1565c0", label="equity_mom (k=10)")
    ax.plot(xs, [dm[h]["sr"] for h in xs], "s-", color="#2e7d32", label="dual_mom (k=4)")
    ax.axvline(21, color="#c62828", ls=":", lw=1.4, label="flagship hold=21")
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{h}d" for h in xs])
    ax.set_xlabel("holding period")
    ax.set_ylabel("net excess Sharpe")
    ax.set_title("net-of-cost Sharpe vs holding period", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    ax.plot(xs, [eq[h]["to"] for h in xs], "o-", color="#1565c0", label="turnover (x/yr)")
    ax2 = ax.twinx()
    ax2.plot(xs, [eq[h]["to"] * COST_RT * 1e4 for h in xs], "^--", color="#f9a825",
             label="est. cost drag (bps/yr)")
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{h}d" for h in xs])
    ax.set_xlabel("holding period")
    ax.set_ylabel("annual one-way turnover (x)")
    ax2.set_ylabel("cost drag (bps/yr)")
    ax.set_title("equity_mom: turnover and cost drag", fontsize=10)
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-29: holding-period x turnover curves (flagship momentum sleeves)",
                 fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr29_holding.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
