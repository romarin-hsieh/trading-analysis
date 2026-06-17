"""Seasonality sleeve — turn-of-month + overnight effect, and does it diversify the combo?

From the strategy catalog (docs/13): calendar/seasonal anomalies are free with daily data and
low-correlated to cross-sectional factors. We build two market-timing overlays on SPY:
  turn_of_month  — hold only the last trading day + first 3 of each month (the TOM premium)
  overnight      — capture the close->open drift (hold overnight, flat intraday)
All calendar-based and leak-free. The real question: do they DIVERSIFY the multi-sleeve combo
(docs/08, the only significant-alpha strategy)?

Run: uv run python scripts/seasonality_sleeve.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

COST = 0.0005  # 5 bps per traded leg (SPY is ultra-liquid)


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def main():
    s = DuckStore("./data")
    oh = s.load_ohlcv(["SPY"]).set_index("ts").sort_index()
    o, c, adj = oh["open"], oh["close"], oh["adj_close"]
    cc = adj.pct_change().fillna(0.0)                       # total-return close-to-close

    # turn-of-month mask: first 3 + last trading day of each calendar month
    ym = oh.index.to_period("M")
    pos = pd.Series(np.arange(len(oh)), index=oh.index).groupby(ym).cumcount()
    cnt = pd.Series(1, index=oh.index).groupby(ym).transform("size")
    tom_hold = ((pos <= 2) | (cnt - 1 - pos == 0))
    tom = cc.where(tom_hold, 0.0)
    tom = tom - tom_hold.ne(tom_hold.shift()).astype(float) * COST   # cost on enter/exit

    overnight = (o / c.shift(1) - 1).fillna(0.0)            # close->open drift (price-only)

    print("=" * 80)
    print("SEASONALITY SLEEVE — SPY calendar overlays, 2015-2024")
    print("=" * 80)
    print(f"{'strategy':18s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'%days in mkt':>12s}")
    streams = {"buy & hold": cc, "turn_of_month": tom, "overnight": overnight}
    for name, r in streams.items():
        st = stats(r)
        inmkt = (r != 0).mean()
        print(f"{name:18s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {inmkt:11.0%}")

    # diversification test: correlation to the multi-sleeve combo + does adding it help?
    _, _, sleeves5 = vr.build_combo()
    combo5 = (lambda sl: (rebalance(sl, 126, 21, "risk_parity").reindex(sl.index).ffill().shift(1).fillna(0.0) * sl).sum(axis=1))(sleeves5)
    idx = sleeves5.index.intersection(tom.index)
    print("-" * 80)
    print("DIVERSIFICATION vs the 5-sleeve combo:")
    for name, r in [("turn_of_month", tom), ("overnight", overnight)]:
        rr = r.reindex(idx).fillna(0.0)
        corr = float(np.corrcoef(rr, combo5.reindex(idx).fillna(0.0))[0, 1])
        print(f"  corr({name}, combo) = {corr:+.2f}")

    # add turn_of_month (the low-exposure, likely low-corr one) as a 6th sleeve
    s6 = sleeves5.join(tom.rename("seasonality"), how="inner").dropna()
    def rp(sl):
        w = rebalance(sl, 126, 21, "risk_parity")
        return (w.reindex(sl.index).ffill().shift(1).fillna(0.0) * sl).sum(axis=1)
    print("-" * 80)
    for name, r in [("5-sleeve (docs/08)", rp(sleeves5.loc[s6.index])), ("6-sleeve (+seasonality)", rp(s6))]:
        r = r.loc[r.index >= "2016-01-01"]
        st = stats(r)
        attr = vr.attribution(r)
        a = "" if "error" in attr else f"alpha {attr['alpha']*252:+.2%} (t={attr['alpha_tstat']:+.2f})"
        print(f"  {name:24s} Sharpe {st['Sharpe']:+.2f}  Calmar {st['Calmar']:.2f}  PSR {probabilistic_sharpe_ratio(r.to_numpy(),0.0):.2f}  {a}")
    print("=" * 80)


if __name__ == "__main__":
    main()
