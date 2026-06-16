"""Run the fundamental factors through the determination gate on the S&P 500.

For each point-in-time fundamental factor: coverage, IC / ICIR / hit-rate, cross-SUB-PERIOD
sign stability, quantile monotonicity. The same gate as scripts/factor_determination.py, now on
real SEC fundamentals across ~500 names (the breadth the factor inference needed).

Run: uv run python scripts/fundamental_factors.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
    quantile_spread,
)

HORIZON = 63
SPLIT = "2020-01-01"


def main():
    store = DuckStore("./data")
    syms = store.list_symbols("1d")
    syms = [s for s in syms if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    if fund.empty:
        print("no fundamentals ingested yet — run scripts/ingest_fundamentals.py first")
        return
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    facs = build_all(fund, px, syms)
    fwd = forward_returns(px, HORIZON)

    print("=" * 92)
    print(f"FUNDAMENTAL FACTOR GATE — {len(syms)} names w/ fundamentals, forward {HORIZON}d, 2015-2024")
    print(f"  (fundamentals: {len(fund):,} facts; point-in-time via SEC filed date)")
    print("=" * 92)
    print(f"{'factor':20s} {'cover':>6s} {'IC':>7s} {'ICIR':>6s} {'hit%':>5s} {'IC16-19':>8s} {'IC20-24':>8s} {'mono':>5s} {'verdict'}")
    for name, fw in facs.items():
        cover = int((~fw.isna()).any().sum())
        ic = cross_sectional_ic(fw, fwd)
        if len(ic) < 100:
            print(f"{name:20s} {cover:6d}  (insufficient data)")
            continue
        summ = ic_summary(ic)
        m1, m2 = float(ic[ic.index < SPLIT].mean()), float(ic[ic.index >= SPLIT].mean())
        qs = quantile_spread(fw, fwd)["mean_fwd_ret"]
        mono = bool(qs.is_monotonic_increasing or qs.is_monotonic_decreasing) if len(qs) >= 3 else False
        stable = (np.sign(m1) == np.sign(m2)) and abs(summ["mean_ic"]) > 0.01
        verdict = "PASS" if (stable and mono) else ("weak" if stable or mono else "FAIL")
        print(f"{name:20s} {cover:6d} {summ['mean_ic']:+7.3f} {summ['icir']:+6.2f} {summ['hit_rate']*100:4.0f}% "
              f"{m1:+8.3f} {m2:+8.3f} {mono!s:>5s} {verdict}")
    print("-" * 92)
    print("  PASS = same-sign IC in BOTH sub-periods AND monotone quantiles. Breadth (~500 names)")
    print("  gives these ICs far smaller error bars than the 51-name run (docs/09).")
    print("=" * 92)


if __name__ == "__main__":
    main()
