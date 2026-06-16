"""Run the insider net-purchase-ratio factor through the determination gate on the S&P 500.

Insider open-market net buying (Lakonishok-Lee 2001) is a documented positive predictor. We
build it point-in-time (trailing 6-month net-purchase ratio, conditioned on SEC filing dates)
and run it through the same gate as the price/fundamental factors.

Run: uv run python scripts/insider_factor.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
from trading_analysis.data.connectors.insider import net_purchase_ratio  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
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
    syms = [s for s in store.list_symbols("1d") if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    ins = store.load_insider(syms)
    if ins.empty:
        print("no insider data ingested yet — run scripts/ingest_insider.py first")
        return
    syms = [s for s in syms if s in set(ins["symbol"])]
    px = px[syms]
    fwd = forward_returns(px, HORIZON)

    print("=" * 88)
    print(f"INSIDER FACTOR GATE — {len(syms)} names w/ insider activity, forward {HORIZON}d, 2015-2024")
    print(f"  ({len(ins):,} (symbol,filing-date) rows; net-purchase ratio over trailing 6mo, point-in-time)")
    print("=" * 88)
    print(f"{'factor':22s} {'cover':>6s} {'IC':>7s} {'ICIR':>6s} {'hit%':>5s} {'IC16-19':>8s} {'IC20-24':>8s} {'mono':>5s} {'verdict'}")
    for win, label in [(126, "insider_npr_6mo"), (252, "insider_npr_12mo")]:
        fw = net_purchase_ratio(ins, px.index, syms, window=win)
        cover = int((~fw.isna()).any().sum())
        ic = cross_sectional_ic(fw, fwd)
        if len(ic) < 100:
            print(f"{label:22s} {cover:6d}  (insufficient overlap)")
            continue
        summ = ic_summary(ic)
        m1, m2 = float(ic[ic.index < SPLIT].mean()), float(ic[ic.index >= SPLIT].mean())
        qs = quantile_spread(fw, fwd)["mean_fwd_ret"]
        mono = bool(qs.is_monotonic_increasing or qs.is_monotonic_decreasing) if len(qs) >= 3 else False
        stable = (np.sign(m1) == np.sign(m2)) and abs(summ["mean_ic"]) > 0.01
        verdict = "PASS" if (stable and mono) else ("weak" if stable or mono else "FAIL")
        print(f"{label:22s} {cover:6d} {summ['mean_ic']:+7.3f} {summ['icir']:+6.2f} {summ['hit_rate']*100:4.0f}% "
              f"{m1:+8.3f} {m2:+8.3f} {mono!s:>5s} {verdict}")
    print("=" * 88)


if __name__ == "__main__":
    main()
