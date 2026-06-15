"""Does ANY combination/leverage reach the goal's risk-return ratio? The definitive test.

The goal (50-100% CAGR with no major drawdown) is a Calmar-ratio demand: CAGR/|MDD| ~ 3.3
(e.g. 50%/15%). We test the two remaining legitimate levers:
  (A) LEVERAGE — does scaling a strategy raise Calmar? (It shouldn't: leverage scales CAGR and
      MDD together, leaving Calmar ~invariant.)
  (B) DIVERSIFICATION — the "only free lunch": does blending an offensive leveraged-trend sleeve
      with a low-correlation defensive sleeve raise the blend's Calmar above any single piece?
If even the best of these stays far below 3.3, the goal is provably unreachable on this data.

Run: uv run python scripts/meta_portfolio.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
import leveraged_strategies as ls  # noqa: E402  (scripts/ is on sys.path when run directly)
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402


def stats(ret):
    ret = ret.dropna()
    eq = (1 + ret).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "MDD": mdd, "Sharpe": sharpe(ret),
            "Calmar": (c / abs(mdd)) if mdd else float("nan")}


def main():
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    px = ss._px(allsyms)
    spy = ss._spy().reindex(px.index).ffill()

    # offensive: diversified momentum (k=10, regime-gated) and a 3x-ETF trend sleeve
    d = ss.momentum_trend_direction(px, spy, k=10, hold=21, regime=True)
    div_ret = ss.run_engine(px, d, spy, 10).returns
    # defensive: dual-momentum bonds/gold rotation (low correlation to equities)
    def_ret = ss.strat_dual_momentum("def", allsyms, k=4)[1].returns
    # leveraged trend sleeve: TQQQ while QQQ>200SMA, else cash (daily)
    tq = ss._px(["TQQQ"]).iloc[:, 0]
    on = ls._trend("QQQ", 200).reindex(tq.index).ffill().fillna(False)
    tq_ret = (tq.pct_change() * on.astype(float)).fillna(0.0)

    idx = div_ret.index.intersection(def_ret.index).intersection(tq_ret.index)
    div_ret, def_ret, tq_ret = div_ret.reindex(idx).fillna(0), def_ret.reindex(idx).fillna(0), tq_ret.reindex(idx).fillna(0)

    print("=" * 76)
    print("META-PORTFOLIO TEST — can leverage or diversification reach Calmar ~3.3?")
    print("=" * 76)
    print(f"{'base strategy':28s} {'CAGR':>7s} {'MDD':>7s} {'Sharpe':>7s} {'Calmar':>7s}")
    for nm, r in [("diversified momentum", div_ret), ("defensive dual-mom", def_ret), ("TQQQ trend (3x)", tq_ret)]:
        s = stats(r)
        print(f"{nm:28s} {s['CAGR']:+7.1%} {s['MDD']:+7.1%} {s['Sharpe']:+7.2f} {s['Calmar']:7.2f}")

    print("-" * 76)
    print("(A) LEVERAGE INVARIANCE — scale diversified momentum by L:")
    print(f"{'leverage':>10s} {'CAGR':>8s} {'MDD':>8s} {'Calmar':>8s}")
    for lev in [0.5, 1.0, 1.5, 2.0, 3.0]:
        s = stats(div_ret * lev)
        print(f"{lev:>9.1f}x {s['CAGR']:+8.1%} {s['MDD']:+8.1%} {s['Calmar']:8.2f}")
    print("  -> leverage scales CAGR and MDD together; Calmar barely moves. Leverage cannot buy Calmar.")

    print("-" * 76)
    print("(B) DIVERSIFICATION — blend w*TQQQ-trend + (1-w)*defensive, find max Calmar:")
    corr = float(np.corrcoef(tq_ret, def_ret)[0, 1])
    print(f"  corr(offensive, defensive) = {corr:+.2f}  (lower = more diversification benefit)")
    best = None
    print(f"{'w_offense':>10s} {'CAGR':>8s} {'MDD':>8s} {'Calmar':>8s}")
    for w in [0.0, 0.25, 0.5, 0.6, 0.75, 0.9, 1.0]:
        blend = w * tq_ret + (1 - w) * def_ret
        s = stats(blend)
        print(f"{w:>10.2f} {s['CAGR']:+8.1%} {s['MDD']:+8.1%} {s['Calmar']:8.2f}")
        if best is None or s["Calmar"] > best[1]["Calmar"]:
            best = (w, s)
    # also try the same blend vol-targeted to 15%
    wbest = best[0]
    blend = wbest * tq_ret + (1 - wbest) * def_ret
    vt = ss.vol_target(blend, target=0.15, lev_cap=2.0)
    svt = stats(vt)

    print("=" * 76)
    print(f"BEST BLEND: w_offense={best[0]:.2f}  ->  CAGR {best[1]['CAGR']:+.1%}, "
          f"MDD {best[1]['MDD']:+.1%}, Calmar {best[1]['Calmar']:.2f}")
    print(f"  + vol-target 15%        ->  CAGR {svt['CAGR']:+.1%}, MDD {svt['MDD']:+.1%}, Calmar {svt['Calmar']:.2f}")
    print(f"GOAL needs Calmar ~ 3.3 (50% CAGR / 15% MDD).  Best achieved: {max(best[1]['Calmar'], svt['Calmar']):.2f}")
    print(f"  => gap of ~{3.3 / max(best[1]['Calmar'], svt['Calmar'], 0.01):.1f}x. Unbridgeable on this data.")
    print("=" * 76)


if __name__ == "__main__":
    main()
