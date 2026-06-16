"""Test the regime-complementary configuration: momentum (bull/calm) + quality (bear/stress).

The session's two surviving signals are complementary across regimes (docs/10 4e): momentum works
in bull/low-vol/normal, quality works everywhere but is STRONGEST in bear/drawdown/high-vol. We
test whether switching between them by regime beats (a) each alone and (b) a static 50/50 blend.
All on the S&P 500 universe with fundamentals; signals point-in-time; regime labels lagged.

Run: uv run python scripts/regime_complementary.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import quality_composite  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
)
from trading_analysis.regime.conditional_attribution import (  # noqa: E402
    drawdown_regime,
    trend_regime,
    vol_regime,
)

SPLIT = "2020-01-01"


def main():
    s = DuckStore("./data")
    syms = [x for x in s.list_symbols("1d") if x not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    spy = s.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    fund = s.load_fundamentals(syms)
    syms = [x for x in syms if x in set(fund["symbol"])]
    px = px[syms]
    ret = px.pct_change()
    fwd = forward_returns(px, 63)

    def z(f):
        return f.sub(f.mean(axis=1), axis=0).div(f.std(axis=1).replace(0, np.nan), axis=0)

    mz = z(np.log(px).shift(21) - np.log(px).shift(126))      # 6-1 momentum
    qz = z(quality_composite(fund, px.index, syms))           # quality composite
    # momentum-favorable regime (lagged, market-wide): bull AND not-high-vol AND not-drawdown
    fav = ((trend_regime(spy) == "bull")
           & (vol_regime(spy) != "high_vol")
           & (drawdown_regime(spy) == "normal")).reindex(px.index).fillna(False)
    favmat = pd.DataFrame(np.broadcast_to(fav.to_numpy()[:, None], mz.shape), index=mz.index, columns=mz.columns)
    switched = mz.where(favmat, qz)                           # momentum in fav, quality otherwise
    blend = (mz + qz) / 2

    def ls(f, hold=21):
        w = f.div(f.abs().sum(axis=1).replace(0, np.nan), axis=0)
        reb = np.zeros(len(px), bool)
        reb[::hold] = True
        wh = w.where(pd.Series(reb, index=px.index), np.nan).ffill().fillna(0.0)
        turn = wh.diff().abs().sum(axis=1).fillna(0.0)
        return (wh.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * 0.0010

    print("=" * 86)
    print(f"REGIME-COMPLEMENTARY CONFIG — S&P 500 ({len(syms)} names), forward 63d, net 10bps")
    print("=" * 86)
    print(f"{'factor':18s} {'IC':>7s} {'IC16-19':>8s} {'IC20-24':>8s} | {'LS ann':>7s} {'LS Sh':>6s} {'LS MDD':>7s} {'Calmar':>7s}")
    for name, f in [("momentum", mz), ("quality", qz), ("static_blend", blend), ("regime_switched", switched)]:
        ic = cross_sectional_ic(f, fwd)
        summ = ic_summary(ic)
        m1, m2 = float(ic[ic.index < SPLIT].mean()), float(ic[ic.index >= SPLIT].mean())
        r = ls(f).iloc[252:]
        eq = (1 + r).cumprod()
        mdd = max_drawdown(eq)
        cal = cagr(eq) / abs(mdd) if mdd else np.nan
        print(f"{name:18s} {summ['mean_ic']:+7.3f} {m1:+8.3f} {m2:+8.3f} | "
              f"{r.mean()*252:+7.1%} {sharpe(r):+6.2f} {mdd:+7.1%} {cal:7.2f}")
    print("=" * 86)
    print("  If regime_switched ~ static_blend, the timing adds nothing over just blending the two")
    print("  complementary factors (consistent with the session's 'timing subtracts value' finding).")
    print("=" * 86)


if __name__ == "__main__":
    main()
