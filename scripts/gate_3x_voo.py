"""The /goal target gate, measured: beat 3x VOO every year AND never lose more than VOO.

Gate per calendar year y:
  if VOO(y) >= 0 :  pass iff strat(y) >= 3 * VOO(y)
  if VOO(y) <  0 :  pass iff strat(y) >= VOO(y)          (loss not worse than VOO)

Applied to the project's best validated strategies (2016-2025). This quantifies the target the
same way docs/14 quantified the 2x gate -- measure, don't assert.

Run: uv run python scripts/gate_3x_voo.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
import horizon_slots as hs  # noqa: E402
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

YEARS = list(range(2016, 2026))


def main():
    s = DuckStore("./data")
    voo = s.load_close_pivot(["VOO"], column="adj_close").iloc[:, 0].pct_change().dropna()
    rf = s.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0].pct_change().fillna(0.0)
    qqq = s.load_close_pivot(["QQQ"], column="adj_close").iloc[:, 0].pct_change().dropna()
    px = ss._px(sorted({x for v in ss.SECTORS.values() for x in v}))

    m_hi, _ = hs.xsect_momentum(px, k=10, hold=21, lb=126, skip=21)
    m_lo, _ = hs.xsect_momentum(px, k=5, hold=63, lb=252, skip=21)
    l_lo, _ = hs.annual_ew(px)
    rp, _, _ = vr.build_combo()
    lev2 = (2.0 * rp - (rf.reindex(rp.index).fillna(0.0) + 0.015 / 252)).dropna()

    strats = {
        "QQQ buy&hold": qqq,
        "annual EW 47 (L-lo)": l_lo,
        "mom 6-1 top10 mthly": m_hi,
        "mom 12-1 top5 qtrly": m_lo,
        "combo (L=1)": rp,
        "combo levered 2x": lev2,
    }

    print("=" * 100)
    print("GOAL GATE: strat(y) >= 3*VOO(y) in up years AND strat(y) >= VOO(y) in down years")
    print("=" * 100)
    hdr = f"{'year':6s} {'VOO':>8s} {'3xVOO':>8s} " + " ".join(f"{n.split()[0][:10]:>12s}" for n in strats)
    print(hdr)
    print("-" * 100)
    passes = dict.fromkeys(strats, 0)
    for y in YEARS:
        v = hs.yr_ret(voo, y)
        bar = 3 * v if v >= 0 else v
        cells = []
        for name, r in strats.items():
            sr = hs.yr_ret(r, y)
            if np.isfinite(sr) and np.isfinite(v):
                ok = sr >= bar
                passes[name] += int(ok)
                cells.append(f"{sr:+8.1%}{'*' if ok else ' '}")
            else:
                cells.append(f"{'n/a':>9s}")
        print(f"{y:<6d} {v:+8.1%} {bar:+8.1%} " + " ".join(f"{c:>12s}" for c in cells))
    print("-" * 100)
    print("PASS COUNT (out of 10 years):  " +
          "  ".join(f"{n.split()[0][:10]}:{passes[n]}" for n in strats))
    best = max(passes, key=passes.get)
    print(f"BEST: {best} with {passes[best]}/10 -- NO strategy passes every year.")
    print("For calibration: the 2x-VOO gate (docs/14) topped out at 7/10 and that was beta+curation;")
    print("3x + loss-dominance is strictly harder. A 10/10 pass would require Calmar/Sharpe levels")
    print("(~3+ sustained) that docs/07's investable-frontier proof shows do not exist in this data.")
    print("=" * 100)


if __name__ == "__main__":
    main()
