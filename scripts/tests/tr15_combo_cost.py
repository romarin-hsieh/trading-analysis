"""TR-15 -- v1.2-A3/F2 v2: full-cost accounting + 2x stress for the FLAGSHIP combo.

F0 DECLARATION: mechanism = cost-stress of the one PASSED(borderline) alpha claim. Classification:
verification. Seat: the 5-sleeve risk-parity combo exactly as built by validate_recommendation.
Mis-application risk: LOW. Pre-committed claim: the original build charges engine costs (10bps/side)
on the two equity sleeves but ZERO cost on TQQQ trend flips, GLD/IEF holds, and the monthly
risk-parity reweight; charging those honestly at 1x will trim the headline slightly; at 2x the
Carhart alpha-t may fall below the HLZ 3.0 bar it already misses -- report where it lands.

Cost model here (documented):
  equity sleeves  : engine fees+slippage = 5+5 bps/side (x multiplier m via re-run)
  TQQQ trend      : 10bps x m per on/off flip (ETF leg, generous vs its real spread)
  GLD/IEF         : buy-and-hold, 0 turnover cost
  RP reweight     : |dW| x 10bps x m monthly at the combo level

Run: uv run python scripts/tests/tr15_combo_cost.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import leveraged_strategies as ls  # noqa: E402
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.engine import run_backtest  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.config import BacktestConfig  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402


def build_combo_cost(m: float):
    """validate_recommendation.build_combo with a cost multiplier m on every cost channel."""
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    px = ss._px(allsyms)
    spy = ss._spy().reindex(px.index).ffill()

    def engine(px_, direction, k):
        cfg = BacktestConfig(fees_bps=5.0 * m, slippage_bps=5.0 * m, cash=100_000.0,
                             benchmark="SPY", target_percent=1.0 / k, price_field="adj_close")
        return run_backtest(px_, direction.reindex_like(px_).fillna(0), cfg, benchmark_close=spy)

    div_ret = engine(px, ss.momentum_trend_direction(px, spy, k=10, hold=21, regime=True), 10).returns
    # defensive dual momentum -- rebuild with engine costs (strat_dual_momentum hardcodes engine)
    def_ret = ss.strat_dual_momentum("def", allsyms, k=4)[1].returns if m == 1.0 else None
    if def_ret is None:
        # re-run its selection with the scaled engine
        syms = list(dict.fromkeys([*allsyms, "IEF", "TLT", "GLD"]))
        pxd = ss._px(syms)
        lp = np.log(pxd)
        mom12 = (lp.shift(1) - lp.shift(252))
        defv = ["IEF", "TLT", "GLD"]
        spy_off = ~((spy > spy.rolling(200, min_periods=150).mean()).shift(1)
                    .reindex(pxd.index).ffill().fillna(False))
        reb = pd.Series(False, index=pxd.index)
        reb.iloc[::21] = True
        sel = pd.DataFrame(0.0, index=pxd.index, columns=pxd.columns)
        for t in pxd.index[reb.to_numpy()]:
            row = mom12.loc[t]
            drow = row[defv].dropna().sort_values(ascending=False)
            if bool(spy_off.loc[t]):
                win = [s for s in drow.index if drow[s] > 0][:4]
            else:
                rk = row[[s for s in allsyms if s in pxd.columns]].dropna().sort_values(ascending=False)
                bar = float(drow.max()) if len(drow) else 0.0
                win = [s for s in rk.index[:4] if rk[s] > 0 and rk[s] > bar]
                if len(win) < 4 and len(drow):
                    win += [s for s in drow.index if drow[s] > 0][: 4 - len(win)]
            if win:
                sel.loc[t, win] = 1.0
        direction = (sel.where(reb).ffill().fillna(0.0) > 0).astype(int)
        def_ret = engine(pxd, direction, 4).returns

    tq = ss._px(["TQQQ"]).iloc[:, 0]
    on = ls._trend("QQQ", 200).reindex(tq.index).ffill().fillna(False)
    on_f = on.astype(float)
    tq_ret = (tq.pct_change() * on_f).fillna(0.0) - on_f.diff().abs().fillna(0.0) * 0.0010 * m
    idx = div_ret.index.intersection(def_ret.index).intersection(tq_ret.index)
    gld = ss._px(["GLD"]).iloc[:, 0].pct_change().reindex(idx).fillna(0)
    ief = ss._px(["IEF"]).iloc[:, 0].pct_change().reindex(idx).fillna(0)
    sleeves = pd.DataFrame({"equity_mom": div_ret.reindex(idx).fillna(0),
                            "defensive": def_ret.reindex(idx).fillna(0),
                            "lev_trend": tq_ret.reindex(idx).fillna(0),
                            "gold": gld, "bonds": ief}).dropna()
    W = rebalance(sleeves, lookback=126, step=21, method="risk_parity")
    Wd = W.reindex(sleeves.index).ffill().shift(1).fillna(0.0)
    rp = (Wd * sleeves).sum(axis=1) - Wd.diff().abs().sum(axis=1).fillna(0.0) * 0.0010 * m
    return rp.iloc[126:]


def main():
    print("=" * 96)
    print("TR-15  FLAGSHIP COMBO FULL-COST + 2x STRESS (F2 v2)")
    print("=" * 96)
    print(f"{'cost model':38s} {'CAGR':>8s} {'Sharpe':>7s} {'MDD':>8s} {'Carhart a (t)':>16s}")
    rows = {}
    for label, m in (("m=1 full cost (all channels)", 1.0), ("m=2 STRESS (2x everything)", 2.0)):
        rp = build_combo_cost(m)
        eq = (1 + rp).cumprod()
        att = vr.attribution(rp)
        a, t = att.get("alpha", np.nan) * 252, att.get("alpha_tstat", np.nan)
        rows[m] = (cagr(eq), sharpe(rp), t)
        print(f"{label:38s} {cagr(eq):>+8.2%} {sharpe(rp):>+7.2f} {max_drawdown(eq):>+8.1%} "
              f"{a:>+8.2%} ({t:+.2f})")
    # documented baseline for reference
    rp0, _, _ = vr.build_combo()
    eq0 = (1 + rp0).cumprod()
    att0 = vr.attribution(rp0)
    print(f"{'[ref] original build (engine-only cost)':38s} {cagr(eq0):>+8.2%} {sharpe(rp0):>+7.2f} "
          f"{max_drawdown(eq0):>+8.1%} {att0.get('alpha', np.nan)*252:>+8.2%} ({att0.get('alpha_tstat', np.nan):+.2f})")
    print("-" * 96)
    t1, t2 = rows[1.0][2], rows[2.0][2]
    print(f"READ: original build omitted TQQQ-flip + RP-reweight costs. Full-cost t={t1:+.2f}; at 2x")
    print(f"stress t={t2:+.2f}. The PASSED(borderline) label {'SURVIVES' if t2 > 2 else 'WEAKENS FURTHER'} the stress")
    print("in the t>2 legacy sense; it already sits below the HLZ 3.0 bar either way (docs/17 A1).")
    print("=" * 96)


if __name__ == "__main__":
    main()
