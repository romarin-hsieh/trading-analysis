"""Deliverable C — the drawdown-budget frontier: what you CAN actually hold.

The research arc proved the user's goal splits in two: (1) 50-100% CAGR at low risk is IMPOSSIBLE
(Calmar wall ~0.7; 50%/15% needs Calmar 3.3), but (2) the OTHER half — "don't suffer large loss of
principal" — IS deliverable. The multi-decade TAA test (scripts/taa_long_history.py) showed a defensive
overlay caps drawdown (-55% -> -35%) and stays flat-to-positive through the GFC and dot-com bust.

This turns that into something usable: take the only statistically-significant-alpha strategy we found
(the 5-sleeve risk-parity combo, docs/08, Carhart alpha t=2.64) and show the EXACT drawdown/return
frontier you get by dialing in defense. Two honest defensive dials, compared head to head:

  static de-lever   — hold fraction L in the combo, (1-L) in cash (BIL). No timing risk; guaranteed to
                      scale MDD down linearly. The floor on what defense costs.
  trend overlay     — hold the combo only while SPY > its 200-day SMA, else de-risk to `floor` exposure.
                      Times the de-risking; can beat static IF it doesn't whipsaw (prior work warns it can).

Output: the frontier table (pick your max-drawdown tolerance -> the allocation + its CAGR/Sharpe cost),
plus TODAY's target sleeve weights so it's directly actionable.

Run: uv run python scripts/defensive_overlay.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

COST = 0.0010
SPLITS = {"2016-19": ("2016-01-01", "2019-12-31"), "2020-24": ("2020-01-01", "2024-12-31")}


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    sub = {k: (sharpe(r[(r.index >= a) & (r.index <= b)])
               if ((r.index >= a) & (r.index <= b)).sum() > 60 else np.nan)
           for k, (a, b) in SPLITS.items()}
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd,
            "Calmar": c / abs(mdd) if mdd else np.nan, **sub}


def main():
    s = DuckStore("./data")
    rp, _ew, sleeves5 = vr.build_combo()
    idx = rp.index
    rf = s.load_close_pivot(["BIL"], column="adj_close").reindex(idx).ffill().pct_change().iloc[:, 0].fillna(0.0)
    spy = s.load_close_pivot(["SPY"], column="adj_close").reindex(idx).ffill().iloc[:, 0]
    above = (spy > spy.rolling(200, min_periods=150).mean()).shift(1).fillna(False)  # leak-free trend state

    print("=" * 96)
    print("DELIVERABLE C — drawdown-budget frontier on the 5-sleeve combo (docs/08, alpha t=2.64)")
    print(f"period {idx.min().date()}..{idx.max().date()}, net {COST*1e4:.0f}bps on overlay turnover")
    print("=" * 96)

    base = stats(rp)
    print(f"{'allocation':30s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'Calmar':>7s} {'16-19':>7s} {'20-24':>7s}")
    print(f"{'combo (100%, no defense)':30s} {base['CAGR']:+7.1%} {base['Sharpe']:+7.2f} "
          f"{base['MDD']:+7.1%} {base['Calmar']:7.2f} {base['2016-19']:+7.2f} {base['2020-24']:+7.2f}")

    print("-" * 96)
    print("DIAL 1 — static de-lever (combo fraction L, rest in cash/BIL):")
    for lev in (0.8, 0.6, 0.4):
        port = lev * rp + (1 - lev) * rf
        st = stats(port)
        label = f"  L={lev*100:.0f}% combo / {(1-lev)*100:.0f}% cash"
        print(f"{label:30s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {st['Calmar']:7.2f} "
              f"{st['2016-19']:+7.2f} {st['2020-24']:+7.2f}")

    print("-" * 96)
    print("DIAL 2 — trend overlay (full combo while SPY>200SMA, else de-risk to `floor`; net cost on switches):")
    pct_derisk = float((~above).mean())
    for floor in (0.5, 0.3, 0.0):
        expo = pd.Series(np.where(above, 1.0, floor), index=idx)
        port = expo * rp + (1 - expo) * rf
        port = port - expo.diff().abs().fillna(0.0) * COST  # turnover cost on de-risk/re-risk
        st = stats(port)
        label = f"  trend, floor={floor*100:.0f}% ({pct_derisk*100:.0f}% derisk)"
        print(f"{label:30s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {st['Calmar']:7.2f} "
              f"{st['2016-19']:+7.2f} {st['2020-24']:+7.2f}")

    # head-to-head at MATCHED drawdown: the fair comparison (cheapest CAGR for the same MDD floor)
    print("-" * 96)
    e2 = pd.Series(np.where(above, 1.0, 0.0), index=idx)               # best trend row (floor=0)
    p2 = (e2 * rp + (1 - e2) * rf) - e2.diff().abs().fillna(0.0) * COST
    d2 = stats(p2)
    lev_match = abs(d2["MDD"]) / abs(base["MDD"])                       # static L giving the SAME MDD as trend
    d1 = stats(lev_match * rp + (1 - lev_match) * rf)
    print(f"FAIR head-to-head at MDD~{d2['MDD']:+.1%}:")
    print(f"  trend overlay floor=0%      CAGR {d2['CAGR']:+.1%}  Calmar {d2['Calmar']:.2f}")
    print(f"  static de-lever L={lev_match*100:.0f}%       CAGR {d1['CAGR']:+.1%}  Calmar {d1['Calmar']:.2f}")
    gap = d2["CAGR"] - d1["CAGR"]
    print(f"  => at equal drawdown the trend overlay yields {gap:+.1%} CAGR vs static "
          f"({'trend wins in-sample' if gap > 0 else 'static wins'}).")
    print("  CAVEAT (honest): this trend-timing edge is IN-SAMPLE/period-specific — scripts/taa_long_history.py")
    print("  showed trend timing does NOT improve full-cycle Sharpe. Static de-lever has ZERO timing risk and is")
    print("  the safe default; the trend overlay is the 'if you trust the 200SMA signal' option, not a free lunch.")

    # TODAY's actionable target weights (latest risk-parity sleeve weights + trend state)
    print("-" * 96)
    W = rebalance(sleeves5, lookback=126, step=21, method="risk_parity")
    w_now = W.reindex(sleeves5.index).ffill().iloc[-1]
    print(f"TODAY'S TARGET — 5-sleeve risk-parity weights (as of {sleeves5.index[-1].date()}):")
    for k, v in w_now.sort_values(ascending=False).items():
        print(f"    {k:12s} {v:6.1%}")
    print(f"  trend state: SPY {'ABOVE' if bool(above.iloc[-1]) else 'BELOW'} 200SMA "
          f"-> overlay says hold {'FULL' if bool(above.iloc[-1]) else 'DE-RISKED'} combo exposure")

    print("=" * 96)
    print("HONEST FRAME: none of these rows reaches 50% CAGR — that corner needs ~3x leverage and -50%+ MDD")
    print("(scripts/leveraged_strategies.py). What this frontier DELIVERS is the user's other goal: choose a")
    print("max-drawdown you can live with, read off the allocation, accept the (honest) CAGR it implies.")
    print("=" * 96)


if __name__ == "__main__":
    main()
