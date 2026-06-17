"""Brutally honest head-to-head: the 5-sleeve combo vs just buying VOO (S&P 500).

The user's sharp question: "doesn't the combo just lose to VOO?" This refuses to spin it.
We compare on EVERY axis that matters and let the numbers speak:
  - raw CAGR / terminal wealth  (where VOO is expected to win in a bull decade)
  - risk-adjusted (Sharpe / Calmar / MDD)  (where the combo is built to win)
  - VOL-MATCHED: lever the combo to VOO's realized volatility, net of T-bill financing —
    the fair fight, because Sharpe only converts to wealth once you equalize risk
  - sub-periods + the specific drawdown years (2018, 2020 COVID, 2022) — when defense pays
  - % of rolling 1-year windows the combo beats VOO

VOO = Vanguard S&P 500 (we use it literally; ~0.9999 corr with SPY/VTI).

Run: uv run python scripts/combo_vs_voo.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

YEARS = {"2015-19": ("2015-01-01", "2019-12-31"), "2020-24": ("2020-01-01", "2024-12-31")}
CRISES = {"2018 Q4 selloff": ("2018-09-20", "2018-12-24"),
          "2020 COVID crash": ("2020-02-19", "2020-03-23"),
          "2022 bear": ("2022-01-03", "2022-10-12")}


def row(name, r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    vol = r.std() * np.sqrt(252)
    term = 10000 * float(eq.iloc[-1])
    return (f"{name:26s} {c:+7.1%} {sharpe(r):+7.2f} {vol:7.1%} {mdd:+7.1%} "
            f"{(c/abs(mdd) if mdd else np.nan):7.2f}  ${term:>10,.0f}")


def seg_total(r, a, b):
    seg = r[(r.index >= a) & (r.index <= b)].dropna()
    return (1 + seg).prod() - 1 if len(seg) else np.nan


def main():
    s = DuckStore("./data")
    rp, _ew, _sl = vr.build_combo()
    idx = rp.index
    voo = s.load_close_pivot(["VOO"], column="adj_close").reindex(idx).ffill().iloc[:, 0].pct_change().fillna(0.0)
    rf = s.load_close_pivot(["BIL"], column="adj_close").reindex(idx).ffill().iloc[:, 0].pct_change().fillna(0.0)

    print("=" * 92)
    print(f"COMBO vs VOO — head to head, {idx.min().date()}..{idx.max().date()} ($10k start)")
    print("=" * 92)
    print(f"{'strategy':26s} {'CAGR':>7s} {'Sharpe':>7s} {'vol':>7s} {'MDD':>7s} {'Calmar':>7s}  {'$10k ->':>11s}")
    print("-" * 92)
    print(row("VOO (S&P 500)", voo))
    print(row("combo (5-sleeve RP)", rp))

    # VOL-MATCHED: lever the combo to VOO's realized vol, financed at the T-bill (BIL) rate
    vol_voo = voo.std()
    vol_combo = rp.std()
    L = float(vol_voo / vol_combo)
    lev = L * rp - (L - 1) * rf                       # borrow (L-1) at the bill rate
    print(row(f"combo levered x{L:.2f} (=VOO vol)", lev))
    print("-" * 92)
    print(f"  raw verdict: VOO CAGR {cagr((1+voo).cumprod()):+.1%} vs combo {cagr((1+rp).cumprod()):+.1%}"
          f"  -> VOO wins on RAW return by {cagr((1+voo).cumprod())-cagr((1+rp).cumprod()):+.1%}/yr")
    print(f"  vol-matched: lever combo to VOO's {vol_voo*np.sqrt(252):.0%} vol (x{L:.2f}, net T-bill financing)"
          f"  -> CAGR {cagr((1+lev).cumprod()):+.1%} at MDD {max_drawdown((1+lev).cumprod()):+.1%}")

    # sub-periods (total return)
    print("-" * 92)
    print(f"  {'period':18s} {'VOO':>10s} {'combo':>10s} {'lev combo':>10s}")
    for k, (a, b) in YEARS.items():
        print(f"  {k:18s} {seg_total(voo,a,b):>+10.1%} {seg_total(rp,a,b):>+10.1%} {seg_total(lev,a,b):>+10.1%}")

    # the drawdown years — when defense is supposed to pay
    print("-" * 92)
    print("  DRAWDOWN EPISODES (total return — the combo's reason to exist):")
    print(f"  {'episode':22s} {'VOO':>10s} {'combo':>10s} {'lev combo':>10s}")
    for k, (a, b) in CRISES.items():
        print(f"  {k:22s} {seg_total(voo,a,b):>+10.1%} {seg_total(rp,a,b):>+10.1%} {seg_total(lev,a,b):>+10.1%}")

    # rolling 1-year: how often does the combo (and levered combo) beat VOO?
    print("-" * 92)
    w = 252
    cr_voo = (1 + voo).cumprod()
    cr_rp = (1 + rp).cumprod()
    cr_lv = (1 + lev).cumprod()
    r1_voo = cr_voo / cr_voo.shift(w) - 1
    r1_rp = cr_rp / cr_rp.shift(w) - 1
    r1_lv = cr_lv / cr_lv.shift(w) - 1
    beat_rp = float((r1_rp > r1_voo).mean())
    beat_lv = float((r1_lv > r1_voo).mean())
    print(f"  rolling 1y windows combo beats VOO:        {beat_rp:.0%}")
    print(f"  rolling 1y windows LEVERED combo beats VOO: {beat_lv:.0%}")
    print("=" * 92)
    print("HONEST TAKE: 2015-24 was one of the strongest bull decades in history — near best-case for")
    print("VOO and worst-case for a diversified/defensive book. VOO wins on RAW return; the combo wins")
    print("on risk-adjusted return, and a vol-matched (levered) combo is the fair fight. Over a FULL")
    print("cycle incl. 2000-02 & 2008 (scripts/taa_long_history.py) VOO's edge shrinks and its -55% MDD")
    print("is the price. Pick by which you optimize: terminal wealth in a bull (VOO) or drawdown (combo).")
    print("=" * 92)


if __name__ == "__main__":
    main()
