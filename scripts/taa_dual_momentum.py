"""Canonical multi-asset TAA — Antonacci Dual Momentum + Faber GTAA on broad asset classes.

The catalog's TAA candidate, done RIGHT this time: on a proper multi-asset-class universe (US/intl/
EM equity, REIT, commodities, gold, bonds, cash) rather than the concentrated stocks that failed
earlier (docs/07 S5). These have a genuine real-world OOS record (Faber 2007, Antonacci 2014).

  Antonacci dual momentum — hold the top-K risky assets by 12m return that ALSO beat cash
                            (absolute+relative momentum); fill empty slots with bonds. Monthly.
  Faber GTAA            — hold each risky asset (1/N) only while above its 10-month SMA, else cash.

Run: uv run python scripts/taa_dual_momentum.py
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

RISKY = ["SPY", "QQQ", "EFA", "EEM", "VNQ", "DBC", "GLD"]
DEFENSIVE = ["AGG", "IEF", "TLT"]
CASH = "BIL"
COST = 0.0010
SPLITS = {"2016-2019": ("2016-01-01", "2019-12-31"), "2020-2024": ("2020-01-01", "2024-12-31")}


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    sh = {sp: (sharpe(r[(r.index >= a) & (r.index <= b)]) if ((r.index >= a) & (r.index <= b)).sum() > 60 else np.nan)
          for sp, (a, b) in SPLITS.items()}
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan, **sh}


def weighted_ret(w, ret):
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return (w.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * COST


def main():
    s = DuckStore("./data")
    syms = RISKY + DEFENSIVE + [CASH]
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    ret = px.pct_change()
    mom12 = px / px.shift(252) - 1
    reb = pd.Series(False, index=px.index)
    reb.iloc[::21] = True

    # Antonacci dual momentum, K=3
    K = 3
    sel = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    for t in px.index[reb.to_numpy()]:
        m = mom12.loc[t]
        cm = m[CASH] if np.isfinite(m[CASH]) else 0.0
        winners = [a for a in RISKY if np.isfinite(m[a]) and m[a] > cm and m[a] > 0]
        winners = sorted(winners, key=lambda a: m[a], reverse=True)[:K]
        if len(winners) < K:
            dwin = sorted([d for d in DEFENSIVE if np.isfinite(m[d]) and m[d] > 0], key=lambda a: m[a], reverse=True)
            winners += dwin[: K - len(winners)]
        if winners:
            sel.loc[t, winners] = 1.0
    held = sel.where(pd.Series(reb.to_numpy(), index=px.index), np.nan).ffill().fillna(0.0)
    anto = weighted_ret(held.div(held.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0), ret)

    # Faber GTAA: each risk asset 1/N while above its 10mo (200d) SMA, else cash
    sma = px.rolling(200, min_periods=150).mean()
    above = (px[RISKY] > sma[RISKY]).shift(1).reindex(px.index).fillna(False)
    fw = above.astype(float) / len(RISKY)
    fw = fw.where(pd.Series(reb.to_numpy(), index=px.index), np.nan).ffill().fillna(0.0)
    fw = fw.reindex(columns=px.columns, fill_value=0.0)
    faber = weighted_ret(fw, ret)

    # benchmarks
    w6040 = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    w6040["SPY"] = 0.6
    w6040["AGG"] = 0.4
    bench = weighted_ret(w6040.where(pd.Series(reb.to_numpy(), index=px.index)).ffill().fillna(0.0), ret)
    spy = ret["SPY"]

    print("=" * 92)
    print("MULTI-ASSET TAA — Antonacci dual momentum + Faber GTAA, 2015-2024, net 10bps")
    print("=" * 92)
    print(f"{'strategy':22s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'Calmar':>7s} {'16-19 Sh':>9s} {'20-24 Sh':>9s}")
    streams = {"Antonacci dual-mom": anto, "Faber GTAA": faber, "60/40 (SPY/AGG)": bench, "SPY buy&hold": spy}
    for name, r in streams.items():
        st = stats(r.iloc[252:])
        print(f"{name:22s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {st['Calmar']:7.2f} "
              f"{st['2016-2019']:+9.2f} {st['2020-2024']:+9.2f}")

    # does the best TAA diversify / improve the multi-sleeve combo?
    _, _, sleeves5 = vr.build_combo()
    def rp(sl):
        w = rebalance(sl, 126, 21, "risk_parity")
        return (w.reindex(sl.index).ffill().shift(1).fillna(0.0) * sl).sum(axis=1)
    best = anto if stats(anto.iloc[252:])["Calmar"] >= stats(faber.iloc[252:])["Calmar"] else faber
    idx = sleeves5.index.intersection(best.index)
    corr = float(np.corrcoef(best.reindex(idx).fillna(0.0), rp(sleeves5).reindex(idx).fillna(0.0))[0, 1])
    print("-" * 92)
    print(f"  corr(best TAA, combo) = {corr:+.2f}")
    s6 = sleeves5.join(best.rename("taa"), how="inner").dropna()
    for name, r in [("5-sleeve (docs/08)", rp(sleeves5.loc[s6.index])), ("6-sleeve (+TAA)", rp(s6))]:
        r = r.loc[r.index >= "2016-01-01"]
        st = stats(r)
        attr = vr.attribution(r)
        a = "" if "error" in attr else f"alpha {attr['alpha']*252:+.2%} (t={attr['alpha_tstat']:+.2f})"
        print(f"  {name:22s} Sharpe {st['Sharpe']:+.2f}  Calmar {st['Calmar']:.2f}  {a}")
    print("=" * 92)


if __name__ == "__main__":
    main()
