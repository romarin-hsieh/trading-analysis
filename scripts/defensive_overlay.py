"""Deliverable C — the BIDIRECTIONAL combo frontier: the full menu, de-lever <-> lever up, vs VOO.

The research arc proved the user's goal splits in two: 50-100% CAGR at low risk is IMPOSSIBLE
(Calmar wall ~0.7), but the combo's high Sharpe (1.18 vs VOO 0.80) means you can dial it either way.
The earlier version only showed the DE-LEVER (defense) direction, which made the combo look like a
lower-return-than-VOO product. That was one-sided. This shows BOTH directions on one leverage axis L:

  L < 1  — de-lever: hold L in the combo, (1-L) in cash/BIL. Scales MDD down. To sleep through bears.
  L = 1  — the combo itself: beats VOO on risk-adjusted return (Sharpe/Calmar), loses on raw CAGR.
  L > 1  — lever up: borrow (L-1) at BIL+1.5%/yr. At L~VOO-vol the combo BEATS VOO on terminal wealth.

Each row is flagged vs VOO: BEATS-VOO ($ terminal) and DOMINATES (also >= VOO Calmar). Plus a timed-
defense alternative (trend overlay) and TODAY's target sleeve weights so it's directly actionable.

Honest frame baked in: leverage is a Calmar-near-invariant amplifier; the BEATS-VOO rows take on
margin/gap/financing risk and deeper drawdown. 2015-24 was near best-case for VOO. No free lunch.

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


def fmt(name, r, flag=""):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    vol = r.std() * np.sqrt(252)
    cal = c / abs(mdd) if mdd else np.nan
    term = 10000 * float(eq.iloc[-1])
    return (f"{name:24s} {c:+7.1%} {sharpe(r):+7.2f} {vol:6.1%} {mdd:+7.1%} {cal:6.2f}  "
            f"${term:>9,.0f}  {flag}")


def main():
    s = DuckStore("./data")
    rp, _ew, sleeves5 = vr.build_combo()
    idx = rp.index
    rf = s.load_close_pivot(["BIL"], column="adj_close").reindex(idx).ffill().pct_change().iloc[:, 0].fillna(0.0)
    spy = s.load_close_pivot(["SPY"], column="adj_close").reindex(idx).ffill().iloc[:, 0]
    voo = s.load_close_pivot(["VOO"], column="adj_close").reindex(idx).ffill().iloc[:, 0].pct_change().fillna(0.0)
    above = (spy > spy.rolling(200, min_periods=150).mean()).shift(1).fillna(False)  # leak-free trend state
    fin_spread = 0.015 / 252.0  # borrow the levered $ at BIL + 1.5%/yr (retail-margin proxy)

    def levered(lev):
        return (lev * rp - (lev - 1) * (rf + fin_spread)) if lev >= 1 else (lev * rp + (1 - lev) * rf)

    # VOO reference + dominance thresholds
    voo_eq = (1 + voo).cumprod()
    voo_cagr, voo_cal = cagr(voo_eq), cagr(voo_eq) / abs(max_drawdown(voo_eq))
    voo_term = 10000 * float(voo_eq.iloc[-1])
    vol_match = float(voo.std() / rp.std())  # leverage that matches VOO's volatility

    print("=" * 100)
    print("COMBO LEVERAGE FRONTIER — the full two-way menu (de-lever <-> lever up) vs just buying VOO")
    print(f"period {idx.min().date()}..{idx.max().date()}; borrowed $ financed at BIL+1.5%/yr; $10k start")
    print("=" * 100)
    print(f"{'allocation':24s} {'CAGR':>7s} {'Sharpe':>7s} {'vol':>6s} {'MDD':>7s} {'Calmar':>6s}  {'$10k->':>10s}  flag")
    print("-" * 100)
    print(fmt("VOO (S&P 500)", voo, "<- benchmark"))
    print("-" * 100)
    print("LEVERAGE DIAL  (L<1 = de-lever to cash/BIL ; L=1 = the combo ; L>1 = borrow & lever up):")
    for lev in (0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0):
        r = levered(lev)
        eq = (1 + r).cumprod()
        c, cal, term = cagr(eq), cagr(eq) / abs(max_drawdown(eq)), 10000 * float(eq.iloc[-1])
        flag = ""
        if term > voo_term:
            flag = "BEATS-VOO ($)" + (" + DOMINATES (>=VOO Calmar)" if (c > voo_cagr and cal >= voo_cal) else "")
        if abs(lev - round(vol_match, 2)) < 0.13 or (lev == 2.0 and vol_match > 1.9):
            flag = (flag + "  ~VOO-vol").strip()
        print(fmt(f"  L={lev:.2f}", r, flag))
    print("-" * 100)
    print(f"  read: L={vol_match:.2f} exactly matches VOO's volatility. Rows tagged BEATS-VOO end with more")
    print("  terminal wealth than VOO; DOMINATES = also >= VOO's Calmar (more return AND better risk-adj).")

    # timed-defense alternative (kept from the drawdown-budget view) — one compact line
    print("-" * 100)
    e0 = pd.Series(np.where(above, 1.0, 0.0), index=idx)
    p0 = (e0 * rp + (1 - e0) * rf) - e0.diff().abs().fillna(0.0) * COST
    st0 = stats(p0)
    print(f"ALT (timed defense): trend overlay, full combo while SPY>200SMA else cash -> "
          f"CAGR {st0['CAGR']:+.1%} MDD {st0['MDD']:+.1%} Calmar {st0['Calmar']:.2f}")
    print("  (in-sample edge; scripts/taa_long_history.py shows trend timing doesn't help full-cycle -> "
          "static de-lever is the zero-timing-risk default.)")

    # TODAY's actionable target weights
    print("-" * 100)
    W = rebalance(sleeves5, lookback=126, step=21, method="risk_parity")
    w_now = W.reindex(sleeves5.index).ffill().iloc[-1]
    weights = "  ".join(f"{k} {v:.1%}" for k, v in w_now.sort_values(ascending=False).items())
    print(f"TODAY'S TARGET (as of {sleeves5.index[-1].date()}) — risk-parity sleeve weights, then scale by your L:")
    print(f"    {weights}")

    print("=" * 100)
    print("HONEST FRAME: leverage is a Calmar-near-invariant amplifier — the BEATS-VOO rows buy more return")
    print("with margin/gap/financing risk and DEEPER drawdown (L~2 MDD ~ -36% vs VOO -34%). 2015-24 was near")
    print("best-case for VOO; over a full cycle (taa_long_history.py) VOO's -55% MDD bites. No free lunch:")
    print("de-lever to sleep, hold L=1 to beat VOO risk-adjusted, lever up to beat VOO on wealth at more risk.")
    print("=" * 100)


if __name__ == "__main__":
    main()
