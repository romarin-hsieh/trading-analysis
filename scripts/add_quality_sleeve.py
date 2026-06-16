"""Does adding the gross-profitability (quality) sleeve improve the validated multi-sleeve combo?

The multi-sleeve risk-parity combo is the session's only significant-alpha strategy (docs/08,
Carhart alpha t=2.64). Gross profitability is the best fundamental factor (docs/10) and is
low-correlated to the existing sleeves. Here we add it as a 6th sleeve and re-run the rigor gate.

Run: uv run python scripts/add_quality_sleeve.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import validate_recommendation as vr  # noqa: E402  (build_combo, attribution, stats)

from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import gross_profitability  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402


def stats(r):
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def quality_sleeve(hold: int = 21) -> pd.Series:
    """Gross-profitability long-short (z-weighted, monthly), net of 10bps, on S&P 500 names."""
    s = DuckStore("./data")
    syms = [x for x in s.list_symbols("1d") if x not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    fund = s.load_fundamentals(syms)
    syms = [x for x in syms if x in set(fund["symbol"])]
    px = px[syms]
    ret = px.pct_change()
    gp = gross_profitability(fund, px.index, syms)
    z = gp.sub(gp.mean(axis=1), axis=0).div(gp.std(axis=1).replace(0, np.nan), axis=0)
    w = z.div(z.abs().sum(axis=1).replace(0, np.nan), axis=0)
    reb = np.zeros(len(px), bool)
    reb[::hold] = True
    wh = w.where(pd.Series(reb, index=px.index), np.nan).ffill().fillna(0.0)
    turn = wh.diff().abs().sum(axis=1).fillna(0.0)
    r = (wh.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * 0.0010
    r.name = "quality"
    return r


def rp_combo(sleeves: pd.DataFrame) -> pd.Series:
    w = rebalance(sleeves, lookback=126, step=21, method="risk_parity")
    wd = w.reindex(sleeves.index).ffill().shift(1).fillna(0.0)
    return (wd * sleeves).sum(axis=1)


def report(name, r):
    r = r.dropna().loc[lambda x: x.index >= "2016-01-01"]
    st = stats(r)
    psr0 = probabilistic_sharpe_ratio(r.to_numpy(), 0.0)
    attr = vr.attribution(r)
    a = "" if "error" in attr else f"alpha {attr['alpha']*252:+.2%} (t={attr['alpha_tstat']:+.2f})"
    print(f"  {name:18s} CAGR {st['CAGR']:+.1%}  Sharpe {st['Sharpe']:+.2f}  MDD {st['MDD']:+.1%}  "
          f"Calmar {st['Calmar']:.2f}  PSR {psr0:.2f}  {a}")
    return r


def main():
    _, _, sleeves5 = vr.build_combo()           # the 5-sleeve DataFrame
    q = quality_sleeve()
    sleeves6 = sleeves5.join(q, how="inner").dropna()
    sleeves5 = sleeves5.loc[sleeves6.index]      # same window for a fair comparison

    print("=" * 92)
    print("ADD QUALITY SLEEVE — does gross profitability improve the validated multi-sleeve combo?")
    print("=" * 92)
    corr = pd.concat([rp_combo(sleeves5).rename("combo5"), q.reindex(sleeves6.index)], axis=1).corr().iloc[0, 1]
    print(f"  corr(quality sleeve, 5-sleeve combo) = {corr:+.2f}  (low => additive)")
    print("-" * 92)
    base = rp_combo(sleeves5)
    report("5-sleeve (docs/08)", base)
    report("6-sleeve RP(+qual)", rp_combo(sleeves6))
    # risk-parity over-weights the low-vol quality sleeve; test a MODEST manual tilt instead
    q_al = q.reindex(base.index).fillna(0.0)
    report("5-sleeve + 15% qual", 0.85 * base + 0.15 * q_al)
    print("=" * 92)
    print("  Verdict: a higher alpha t-stat / Calmar on the 6-sleeve => the alt-data quality factor")
    print("  earned its place in the portfolio (the alt-data effort turned into real alpha).")
    print("=" * 92)


if __name__ == "__main__":
    main()
