"""Kalman pairs trading — the one MARKET-NEUTRAL candidate (could genuinely diversify the combo).

Every sleeve tested so far is equity-beta (momentum, quality, seasonality) so adding them dilutes
more than diversifies. A market-neutral stat-arb sleeve is different. We use the Kalman dynamic
hedge ratio (models.kalman, docs/12) on robust pairs, z-score the spread, mean-revert, and ask:
(1) is it profitable standalone net of cost? (2) is it ~uncorrelated to the combo? (3) does adding
it help? All causal (Kalman is a filter; signal lagged one bar).

Run: uv run python scripts/kalman_pairs.py
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
from trading_analysis.models.kalman import dynamic_regression  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

PAIRS = [("V", "MA"), ("KO", "PEP"), ("XOM", "CVX"), ("GS", "MS"), ("HD", "LOW"), ("MSFT", "GOOGL")]
COST = 0.0010


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def pair_return(a, b, win=60):
    """Kalman dynamic-hedge-ratio mean-reversion return for one pair (dollar-normalized, net cost)."""
    beta = dynamic_regression(a.to_numpy(), pd.DataFrame({"const": 1.0, "b": b.to_numpy()}),
                              q=1e-4, r=1e-3)["b"]
    beta.index = a.index
    spread = a - beta * b
    z = (spread - spread.rolling(win).mean()) / spread.rolling(win).std()
    pos = (-z).clip(-1.5, 1.5).shift(1)                          # mean-revert, lagged
    pnl = pos * (a.diff() - beta.shift(1) * b.diff())            # dollar P&L of long-1a / short-beta-b
    gross = (a.abs() + beta.abs() * b).shift(1)                  # gross $ per unit spread
    ret = (pnl / gross).fillna(0.0)
    ret -= pos.diff().abs().fillna(0.0) * COST                   # turnover cost
    return ret


def main():
    s = DuckStore("./data")
    syms = sorted({x for p in PAIRS for x in p})
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    avail = [p for p in PAIRS if p[0] in px.columns and p[1] in px.columns]

    print("=" * 80)
    print("KALMAN PAIRS TRADING — market-neutral, 2015-2024, net 10bps")
    print("=" * 80)
    print(f"{'pair':12s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s}")
    rets = {}
    for a, b in avail:
        r = pair_return(px[a], px[b]).iloc[60:]
        rets[f"{a}/{b}"] = r
        st = stats(r)
        print(f"{a+'/'+b:12s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%}")
    sleeve = pd.DataFrame(rets).mean(axis=1)                     # equal-weight pairs
    st = stats(sleeve)
    print("-" * 80)
    print(f"{'PAIRS SLEEVE':12s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%}  "
          f"PSR {probabilistic_sharpe_ratio(sleeve.dropna().to_numpy(), 0.0):.2f}")

    # diversification: correlation to the combo + does adding it help?
    _, _, sleeves5 = vr.build_combo()
    def rp(sl):
        w = rebalance(sl, 126, 21, "risk_parity")
        return (w.reindex(sl.index).ffill().shift(1).fillna(0.0) * sl).sum(axis=1)
    combo5 = rp(sleeves5)
    idx = sleeves5.index.intersection(sleeve.index)
    corr = float(np.corrcoef(sleeve.reindex(idx).fillna(0.0), combo5.reindex(idx).fillna(0.0))[0, 1])
    print("-" * 80)
    print(f"  corr(pairs sleeve, combo) = {corr:+.2f}  (market-neutral => should be ~0)")
    s6 = sleeves5.join(sleeve.rename("pairs"), how="inner").dropna()
    for name, r in [("5-sleeve (docs/08)", rp(sleeves5.loc[s6.index])), ("6-sleeve (+pairs)", rp(s6))]:
        r = r.loc[r.index >= "2016-01-01"]
        stt = stats(r)
        attr = vr.attribution(r)
        a = "" if "error" in attr else f"alpha {attr['alpha']*252:+.2%} (t={attr['alpha_tstat']:+.2f})"
        print(f"  {name:22s} Sharpe {stt['Sharpe']:+.2f}  Calmar {stt['Calmar']:.2f}  {a}")
    print("=" * 80)


if __name__ == "__main__":
    main()
