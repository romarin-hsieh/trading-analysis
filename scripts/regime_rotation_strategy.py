"""Regime-rotation strategy: buy momentum leaders in bull/calm, quality leaders in bear/stress.

Synthesizes the session's two surviving signals (docs/10): concentrated momentum works in
bull/calm; quality (gross profitability) works everywhere and is strongest in bear/stress
(flight-to-quality). A long-only top-K book that SWITCHES its selection criterion by regime —
vs always-momentum, always-quality, and SPY.

In-sample-bias note: the "momentum in bull / quality in bear" rule was informed by the in-sample
applicability map, so the full window is partly in-sample; the 2016-19 vs 2020-24 split + PSR-vs-
SPY are the real evidence. All signals point-in-time; regime labels lagged.

Run: uv run python scripts/regime_rotation_strategy.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import quality_composite  # noqa: E402
from trading_analysis.regime.conditional_attribution import (  # noqa: E402
    drawdown_regime,
    trend_regime,
    vol_regime,
)

K = 20
HOLD = 21
COST = 0.0010
SPLITS = {"2016-2019": ("2016-01-01", "2019-12-31"), "2020-2024": ("2020-01-01", "2024-12-31")}


def topk_long(score, ret, k=K, hold=HOLD):
    """Long-only equal-weight top-k by `score`, monthly rebalance, net of turnover."""
    rank = score.rank(axis=1, ascending=False, method="first")
    held = (rank <= k)
    reb = np.zeros(len(score), bool)
    reb[::hold] = True
    held = held.where(pd.Series(reb, index=score.index), np.nan).ffill().fillna(False)
    w = held.astype(float).div(held.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return (w.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * COST


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def main():
    s = DuckStore("./data")
    syms = [x for x in s.list_symbols("1d") if x not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    spy = s.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    fund = s.load_fundamentals(syms)
    syms = [x for x in syms if x in set(fund["symbol"])]
    px = px[syms]
    ret = px.pct_change()

    mom = np.log(px).shift(21) - np.log(px).shift(126)
    qual = quality_composite(fund, px.index, syms)
    fav = ((trend_regime(spy) == "bull")
           & (vol_regime(spy) != "high_vol")
           & (drawdown_regime(spy) == "normal")).reindex(px.index).fillna(False)
    favmat = pd.DataFrame(np.broadcast_to(fav.to_numpy()[:, None], mom.shape), index=mom.index, columns=mom.columns)
    # rotation score: momentum where regime favors it, quality otherwise (both rank-normalized first)
    mom_r = mom.rank(axis=1, pct=True)
    qual_r = qual.rank(axis=1, pct=True)
    rot = mom_r.where(favmat, qual_r)

    spy_ret = spy.pct_change().reindex(px.index).fillna(0.0)
    variants = {
        "always_momentum": topk_long(mom, ret),
        "always_quality": topk_long(qual, ret),
        "regime_rotation": topk_long(rot, ret),
        "SPY (benchmark)": spy_ret,
    }
    print("=" * 88)
    print(f"REGIME-ROTATION STRATEGY — long-only top-{K}, S&P 500 ({len(syms)} names), net 10bps")
    print("=" * 88)
    print(f"{'variant':20s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'Calmar':>7s} {'16-19 Sh':>9s} {'20-24 Sh':>9s}")
    rr = {}
    for name, r in variants.items():
        rr[name] = r
        st = stats(r)
        sh = {sp: (sharpe(r[(r.index >= a) & (r.index <= b)]) if ((r.index >= a) & (r.index <= b)).sum() > 60 else np.nan)
              for sp, (a, b) in SPLITS.items()}
        print(f"{name:20s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {st['Calmar']:7.2f} "
              f"{sh['2016-2019']:+9.2f} {sh['2020-2024']:+9.2f}")
    # rigor: does rotation beat SPY?
    r = rr["regime_rotation"].loc[rr["regime_rotation"].index >= "2016-01-01"]
    spy_pp = float(spy_ret.loc[r.index].mean() / spy_ret.loc[r.index].std())
    print("-" * 88)
    print(f"  rotation PSR P(Sharpe>0): {probabilistic_sharpe_ratio(r.to_numpy(), 0.0):.3f}  "
          f"P(Sharpe>SPY): {probabilistic_sharpe_ratio(r.to_numpy(), spy_pp):.3f}")
    print("=" * 88)


if __name__ == "__main__":
    main()
