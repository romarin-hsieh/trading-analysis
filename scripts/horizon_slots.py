"""Six strategy slots -- 3 horizons x 2 activity styles -- validated vs the 2x-VOO annual gate.

/goal framework: for EACH horizon (short 1-4wk / mid 1-12mo / long 1-3yr+) design BOTH a
low-trade-count-stable variant and a high-trade-count high-Sharpe variant, then gate every slot
per calendar year against 2x that year's VOO return. Sectors: tech/AI/software/space (user's ask).

Slots (all leak-free, signals lagged >=1 bar, net of cost):
  S-lo  SHORT  Donchian 20/10 breakout on QQQ            (few trades/yr, index = no selection bias)
  S-hi  SHORT  QQQ overnight (close->open daily)          (~250 round trips/yr; gross AND net shown)
  M-lo  MID    quarterly 12-1 momentum top-5 of 47 names  (no stops, no gate -- the "subtraction" lesson)
  M-hi  MID    monthly 6-1 momentum top-10 of 47 names    (no stops, no gate)
  L-lo  LONG   annual equal-weight rebalance of 47 names  (~1 decision/yr, pure sector beta)
  L-hi  LONG   5-sleeve risk-parity combo levered 2x      (monthly decisions, ~170 fills/yr)

HONEST CAVEATS printed with results: (1) the 47-name sector list was curated recently -> carries
hindsight bias (QQQ slots are clean); (2) one decade = few independent observations; (3) the 2x-VOO
gate is asymmetric (trivial in down years, brutal in up years).

Run: uv run python scripts/horizon_slots.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

YEARS = list(range(2016, 2026))
COST = 0.0010  # 10 bps per traded leg (stocks); 5 bps used for QQQ (ultra-liquid)


def yr_ret(r: pd.Series, y: int) -> float:
    seg = r.loc[f"{y}-01-01":f"{y}-12-31"].dropna()
    return float((1 + seg).prod() - 1) if len(seg) > 60 else np.nan


def full_stats(r: pd.Series, label: str, trades_yr: float) -> dict:
    r = r.dropna()
    eq = (1 + r).cumprod()
    return {"label": label, "CAGR": cagr(eq), "Sharpe": sharpe(r), "MDD": max_drawdown(eq),
            "trades_yr": trades_yr}


def donchian_qqq(px: pd.Series, n_hi=20, n_lo=10, cost=0.0005):
    hi = px.rolling(n_hi).max().shift(1)
    lo = px.rolling(n_lo).min().shift(1)
    sig = pd.Series(np.nan, index=px.index)
    sig[px > hi] = 1.0
    sig[px < lo] = 0.0
    pos = sig.ffill().fillna(0.0).shift(1).fillna(0.0)     # act next bar
    flips = pos.diff().abs().fillna(0.0)
    ret = pos * px.pct_change() - flips * cost
    trades_yr = float(flips.sum() / 2 / (len(px) / 252))   # round trips per year
    return ret, trades_yr


def overnight_qqq(store: DuckStore, cost=0.0005):
    oh = store.load_ohlcv(["QQQ"]).set_index("ts").sort_index()
    on = (oh["open"] / oh["close"].shift(1) - 1.0).fillna(0.0)
    gross = on
    net = on - 2 * cost                                    # enter close, exit open, 2 legs daily
    return gross, net


def xsect_momentum(px: pd.DataFrame, k: int, hold: int, lb: int, skip: int, cost=COST):
    """Top-k by (lb-skip) momentum, rebalanced every `hold` bars. No stops, no regime gate."""
    lp = np.log(px)
    mom = (lp.shift(skip) - lp.shift(lb)).shift(1)
    held = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    grid = np.zeros(len(px), dtype=bool)
    grid[::hold] = True
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
    ret = (w.shift(1) * r).sum(axis=1) - turn * cost
    fills_yr = float((held.diff().abs().sum(axis=1) > 0).pipe(
        lambda s: held.diff().abs().sum().sum()) / (len(px) / 252))
    return ret, fills_yr


def annual_ew(px: pd.DataFrame):
    """Equal-weight buy&hold, rebalanced once a year (first bar of each year). Exact within-year."""
    r = px.pct_change(fill_method=None)
    out = []
    years = sorted(set(px.index.year))
    n_names = []
    for y in years:
        seg = r.loc[f"{y}-01-01":f"{y}-12-31"]
        if seg.empty:
            continue
        # names with a price at year start (first 5 bars)
        alive = px.loc[seg.index[: min(5, len(seg))]].notna().any()
        cols = alive[alive].index
        n_names.append(len(cols))
        eq = (1 + seg[cols].fillna(0.0)).cumprod()         # each name's path, hold thru year
        port = eq.mean(axis=1)
        out.append(port.pct_change().fillna(port.iloc[0] - 1.0))
    ret = pd.concat(out)
    return ret, float(np.mean(n_names))


def main():
    store = DuckStore("./data")
    syms = sorted({x for v in ss.SECTORS.values() for x in v})
    px = ss._px(syms)
    qqq = store.load_close_pivot(["QQQ"], column="adj_close").iloc[:, 0].dropna()
    voo = store.load_close_pivot(["VOO"], column="adj_close").iloc[:, 0].pct_change().dropna()
    rf = store.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0].pct_change().fillna(0.0)

    # --- build the six slots -------------------------------------------------
    s_lo, s_lo_tr = donchian_qqq(qqq)
    on_gross, on_net = overnight_qqq(store)
    m_lo, m_lo_tr = xsect_momentum(px, k=5, hold=63, lb=252, skip=21)
    m_hi, m_hi_tr = xsect_momentum(px, k=10, hold=21, lb=126, skip=21)
    l_lo, _l_lo_n = annual_ew(px)
    rp, _, _ = vr.build_combo()
    l_hi = (2.0 * rp - (rf.reindex(rp.index).fillna(0.0) + 0.015 / 252)).dropna()

    slots = {
        "S-lo Donchian QQQ 20/10": (s_lo, s_lo_tr),
        "S-hi QQQ overnight (net)": (on_net, 250.0),
        "M-lo 12-1 mom top5 qtrly": (m_lo, m_lo_tr),
        "M-hi 6-1 mom top10 mthly": (m_hi, m_hi_tr),
        "L-lo annual EW 47 names": (l_lo, 1.0),
        "L-hi combo levered 2x": (l_hi, 171.0),
    }

    print("=" * 118)
    print("SIX HORIZON SLOTS vs THE 2x-VOO ANNUAL GATE   (tech/AI/software/space sectors; leak-free; net of cost)")
    print("=" * 118)

    # --- per-year gate table --------------------------------------------------
    hdr = f"{'year':6s} {'VOO':>8s} {'2xVOO':>8s} " + " ".join(f"{n.split()[0]:>12s}" for n in slots)
    print(hdr)
    print("-" * 118)
    passes = dict.fromkeys(slots, 0)
    valid = dict.fromkeys(slots, 0)
    for y in YEARS:
        v = yr_ret(voo, y)
        cells = []
        for name, (r, _) in slots.items():
            sr = yr_ret(r, y)
            if np.isfinite(sr) and np.isfinite(v):
                ok = sr > 2 * v
                valid[name] += 1
                passes[name] += int(ok)
                cells.append(f"{sr:+8.1%}{'*' if ok else ' '}")
            else:
                cells.append(f"{'n/a':>9s}")
        print(f"{y:<6d} {v:+8.1%} {2*v:+8.1%} " + " ".join(f"{c:>12s}" for c in cells))
    print("-" * 118)
    print("        (* = beats 2x VOO that year)")
    gate = "  ".join(f"{n.split()[0]}:{passes[n]}/{valid[n]}" for n in slots)
    print(f"GATE PASS COUNT: {gate}")

    # --- full-period stats ----------------------------------------------------
    print("-" * 118)
    print(f"{'slot':28s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'~trades/yr':>11s}  {'Sharpe>2?':>9s}  {'style':<22s}")
    styles = ["low-count stable", "HIGH-count hi-Sharpe", "low-count stable",
              "HIGH-count hi-Sharpe", "low-count stable", "HIGH-count hi-Sharpe"]
    for (name, (r, tr)), sty in zip(slots.items(), styles, strict=True):
        st = full_stats(r, name, tr)
        print(f"{name:28s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {tr:>11.0f}  "
              f"{'YES' if st['Sharpe'] > 2 else 'no':>9s}  {sty:<22s}")
    # overnight gross for reference (cost wall demo)
    g = full_stats(on_gross, "", 250)
    print(f"{'  (S-hi overnight GROSS ref)':28s} {g['CAGR']:+7.1%} {g['Sharpe']:+7.2f} {g['MDD']:+7.1%}"
          f" {'':>11s}  {'-':>9s}  cost-wall reference")

    print("=" * 118)
    print("HONEST NOTES: (1) 47-name sector list carries recency/curation bias (favor QQQ slots for clean")
    print("reads). (2) The 2x-VOO gate is asymmetric: near-automatic in down years, near-impossible in +20%")
    print("years. (3) One decade = ~10 yearly observations; no slot's pass-rate is statistically separable")
    print("from luck without more history. (4) Sharpe>2 sustained over the decade: see table -- be skeptical")
    print("of any YES driven by a single regime.")
    print("=" * 118)


if __name__ == "__main__":
    main()
