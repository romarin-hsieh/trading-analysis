"""Deepen the one signal that worked — fundamental quality.

(1) Does a quality COMPOSITE (gross_profitability + roa + accruals, z-averaged) beat gross
    profitability alone on robustness (sub-period sign stability, ICIR)?
(2) Is quality regime-universal or regime-specific? Run it through the regime-conditional
    applicability map (FDR-corrected) — unlike momentum (bull-only), a real quality premium
    should survive in most regimes.

Run: uv run python scripts/quality_research.py
"""

from __future__ import annotations

from loguru import logger

logger.remove()
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import (  # noqa: E402
    gross_profitability,
    quality_composite,
)
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
    quantile_spread,
)
from trading_analysis.regime.conditional_attribution import applicability_map  # noqa: E402

HORIZON = 63
SPLIT = "2020-01-01"


def main():
    store = DuckStore("./data")
    syms = [s for s in store.list_symbols("1d") if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    spy = store.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    fwd = forward_returns(px, HORIZON)

    gp = gross_profitability(fund, px.index, syms)
    qc = quality_composite(fund, px.index, syms)

    print("=" * 84)
    print(f"QUALITY RESEARCH — {len(syms)} names, forward {HORIZON}d, 2015-2024")
    print("=" * 84)
    print(f"{'factor':22s} {'cover':>6s} {'IC':>7s} {'ICIR':>6s} {'IC16-19':>8s} {'IC20-24':>8s} {'mono':>5s}")
    for name, fw in [("gross_profitability", gp), ("quality_composite", qc)]:
        ic = cross_sectional_ic(fw, fwd)
        summ = ic_summary(ic)
        m1, m2 = float(ic[ic.index < SPLIT].mean()), float(ic[ic.index >= SPLIT].mean())
        qs = quantile_spread(fw, fwd)["mean_fwd_ret"]
        mono = bool(qs.is_monotonic_increasing or qs.is_monotonic_decreasing) if len(qs) >= 3 else False
        cover = int((~fw.isna()).any().sum())
        print(f"{name:22s} {cover:6d} {summ['mean_ic']:+7.3f} {summ['icir']:+6.2f} {m1:+8.3f} {m2:+8.3f} {mono!s:>5s}")

    print("-" * 84)
    print("REGIME APPLICABILITY of quality_composite (FDR-corrected; does it work in ALL regimes?)")
    amap = applicability_map(qc, px, spy, horizon=HORIZON)
    for rn, tbl in amap.items():
        cells = ", ".join(f"{r}:{tbl.loc[r, 'mean_ic']:+.3f}{'*' if tbl.loc[r, 'significant_fdr'] else ''}"
                          for r in tbl.index)
        print(f"  [{rn:9s}] {cells}")
    print("-" * 84)
    print("  '*' = FDR-significant. Quality surviving across MANY regimes (vs momentum's bull-only)")
    print("  would make it the more dependable factor — the payoff of the alt-data effort.")
    print("=" * 84)


if __name__ == "__main__":
    main()
