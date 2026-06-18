"""2025 OUT-OF-SAMPLE performance of the recommended combo vs VOO — a single-path sanity check.

Every parameter of the 5-sleeve combo (sleeve definitions, k, lookbacks, risk-parity) was chosen on
2015-2024. 2025 is the FIRST fully out-of-sample year. This measures what the combo actually did in
2025 vs just holding VOO. STRONG CAVEAT: one year is a single realized path, NOT statistically
significant — it can neither confirm nor refute the strategy. Read it as a sanity check (did it blow
up? behave as designed?), not as evidence of edge.

Run: uv run python scripts/oos_2025.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

Y0, Y1 = "2025-01-01", "2025-12-31"


def seg(s):
    return s.loc[(s.index >= Y0) & (s.index <= Y1)].dropna()


def line(name, r):
    r = seg(r)
    if len(r) < 20:
        return f"{name:28s} {'(insufficient 2025 data)':>40s}"
    eq = (1 + r).cumprod()
    tot = float(eq.iloc[-1] - 1.0)
    vol = r.std() * np.sqrt(252)
    mdd = max_drawdown(eq)
    return (f"{name:28s} {tot:+8.1%} {sharpe(r):+8.2f} {vol:7.1%} {mdd:+8.1%}  "
            f"${10000*(1+tot):>9,.0f}")


def _ensure_voo(s):
    """VOO must extend through 2025 for the benchmark; ingest if stale (it wasn't in the 2025 batch)."""
    import datetime as _dt

    from trading_analysis.data.connectors.yahoo import YahooConnector
    px = s.load_close_pivot(["VOO"], column="adj_close")
    if not len(px) or px.index.max() < pd.Timestamp("2025-12-30"):
        df = YahooConnector().fetch_ohlcv(["VOO"], start=_dt.date(2024, 6, 1), end=_dt.date(2026, 6, 19), bar="1d")
        s.upsert_ohlcv(df)


def main():
    s = DuckStore("./data")
    _ensure_voo(s)
    rp, ew, sleeves5 = vr.build_combo()
    idx = rp.index
    voo = s.load_close_pivot(["VOO"], column="adj_close").reindex(idx).ffill().iloc[:, 0].pct_change().fillna(0.0)
    rf = s.load_close_pivot(["BIL"], column="adj_close").reindex(idx).ffill().pct_change().iloc[:, 0].fillna(0.0)

    last = seg(rp).index.max()
    n25 = len(seg(rp))
    print("=" * 92)
    print(f"2025 OUT-OF-SAMPLE — recommended combo vs VOO  (2025 trading days available: {n25}, through {last.date() if n25 else 'n/a'})")
    print("=" * 92)
    print(f"{'strategy':28s} {'2025 ret':>8s} {'Sharpe':>8s} {'vol':>7s} {'MDD':>8s}  {'$10k->':>10s}")
    print("-" * 92)
    print(line("VOO (S&P 500)", voo))
    print(line("combo (L=1, no leverage)", rp))
    # levered variants from the frontier (financed at BIL+1.5%/yr)
    for L in (1.5, 2.0):
        lev = L * rp - (L - 1) * (rf + 0.015 / 252)
        print(line(f"combo levered x{L:.1f}", lev))
    print(line("equal-weight 5-sleeve (1/N)", ew))

    # honest counterfactual: how much of 2025 was just gold's monster year?
    def rp_of(sl):
        w = rebalance(sl, 126, 21, "risk_parity")
        return (w.reindex(sl.index).ffill().shift(1).fillna(0.0) * sl).sum(axis=1)
    print(line("combo EX-GOLD (4-sleeve)", rp_of(sleeves5.drop(columns=["gold"]))))

    # per-sleeve 2025 contribution (which sleeve drove it)
    print("-" * 92)
    print("PER-SLEEVE 2025 total return (what worked / dragged):")
    for col in sleeves5.columns:
        r = seg(sleeves5[col])
        if len(r) >= 20:
            print(f"    {col:14s} {float((1+r).cumprod().iloc[-1]-1):+8.1%}")

    # monthly path of combo vs VOO
    print("-" * 92)
    print("MONTHLY returns 2025 (combo / VOO):")
    cm = seg(rp).resample("ME").apply(lambda x: (1 + x).prod() - 1)
    vm = seg(voo).resample("ME").apply(lambda x: (1 + x).prod() - 1)
    for ts in cm.index:
        v = vm.get(ts, np.nan)
        print(f"    {ts.strftime('%Y-%m')}   combo {cm[ts]:+6.1%}    VOO {v:+6.1%}")

    print("=" * 92)
    print("HONEST CAVEAT: 2025 is ONE out-of-sample path — not statistically significant. It shows whether")
    print("the combo behaved as designed (lower vol/drawdown than VOO), not whether it has edge. The combo is")
    print("built to trade raw return for risk control, so under-performing VOO on raw 2025 return is EXPECTED")
    print("in an up year; the levered variant is the matched-risk comparison. Judge by behaviour, not the number.")
    print("=" * 92)


if __name__ == "__main__":
    main()
