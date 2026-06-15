"""Five+ reproducible industry strategies (selection + entry/exit), honestly backtested.

Each strategy is a fully-specified rule: a UNIVERSE, a SELECTION (top-K by momentum among
trend-qualified names), and ENTRY/EXIT (enter monthly when in the top-K AND in an uptrend AND
the market regime is risk-on; exit intraday if price breaks its 50-SMA, drops out of the top-K,
or the regime turns off). Equal-weight the held names (1/K each), so K held => fully invested,
fewer => the remainder sits in cash (drawdown control). All signals are point-in-time (lagged).

We also (a) run a defensive DUAL-MOMENTUM rotation (the low-drawdown design), (b) validate the
Minervini Trend Template and measure ALPHA DECAY (2016-19 vs 2020-24), and (c) gate every
headline number through the corrected order-independent engine + costs.

Run: uv run python scripts/sector_strategies.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from trading_analysis.backtest.engine import run_backtest
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
from trading_analysis.config import BacktestConfig
from trading_analysis.data.store import DuckStore

logger.remove()

STORE = DuckStore("./data")
SECTORS = {
    "AI_semis": ["NVDA","AMD","AVGO","TSM","ASML","MU","AMAT","LRCX","KLAC","MRVL","QCOM","TXN","INTC","ADI","ANET","SMCI"],
    "software_AI": ["MSFT","GOOGL","META","CRM","ADBE","NOW","PANW","CRWD","PLTR","SNOW"],
    "space_defense": ["LMT","RTX","NOC","GD","LHX","BA","HII","LDOS","TDG","HEI","AVAV","KTOS","IRDM"],
    "robotics": ["ISRG","ROK","EMR","TER","ZBRA","PTC","KEYS","HON"],
}
SPLITS = {"2016-2019": ("2016-01-01", "2019-12-31"), "2020-2024": ("2020-01-01", "2024-12-31")}


def _px(syms):
    return STORE.load_close_pivot(syms, column="adj_close").ffill()


def _spy():
    return STORE.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]


def _metrics(eq, ret, label=""):
    return {
        "label": label, "CAGR": cagr(eq), "Sharpe": sharpe(ret),
        "MDD": max_drawdown(eq), "total": float(eq.iloc[-1] / eq.iloc[0] - 1.0),
    }


def momentum_trend_direction(px, spy, k=5, mom_lb=126, mom_skip=21, hold=21, regime=True):
    """Selection: top-k by (mom_lb-skip) momentum among uptrend names. Entry/exit per docstring."""
    lp = np.log(px)
    mom = (lp.shift(mom_skip) - lp.shift(mom_lb)).shift(1)            # point-in-time momentum
    sma50 = px.rolling(50, min_periods=50).mean().shift(1)
    sma150 = px.rolling(150, min_periods=120).mean().shift(1)
    up = (px.shift(1) > sma50) & (sma50 > sma150)                    # uptrend filter
    # monthly top-k among uptrend names (recompute only on rebalance bars, hold between)
    cand = mom.where(up)
    topk_daily = cand.rank(axis=1, ascending=False, method="first") <= k
    rebal = pd.Series(False, index=px.index)
    rebal.iloc[::hold] = True
    topk_month = topk_daily.where(rebal).ffill().fillna(False).astype(bool)
    # daily exit if price loses its 50-SMA; market regime gate
    held = topk_month & (px.shift(1) > sma50)
    if regime:
        spy_sma = spy.rolling(200, min_periods=150).mean()
        on = (spy > spy_sma).shift(1).reindex(px.index).ffill().fillna(False)
        held = held & np.asarray(on)[:, None]
    return held.astype(int)


def run_engine(px, direction, spy, k):
    cfg = BacktestConfig(fees_bps=5.0, slippage_bps=5.0, cash=100_000.0,
                         benchmark="SPY", target_percent=1.0 / k, price_field="adj_close")
    res = run_backtest(px, direction.reindex_like(px).fillna(0), cfg, benchmark_close=spy)
    return res


def strat_momentum(name, syms, k=5, hold=21, regime=True):
    px = _px(syms)
    spy = _spy().reindex(px.index).ffill()
    d = momentum_trend_direction(px, spy, k=k, hold=hold, regime=regime)
    res = run_engine(px, d, spy, k)
    out = {"strategy": name, "k": k, "hold": hold, "regime": regime,
           "full": _metrics(res.equity, res.returns, "full")}
    for sp, (a, b) in SPLITS.items():
        m = (res.equity.index >= a) & (res.equity.index <= b)
        if m.sum() > 60:
            eq = res.equity[m] / res.equity[m].iloc[0]
            out[sp] = _metrics(eq, res.returns[m], sp)
    out["avg_exposure"] = float((d.reindex_like(px).fillna(0) > 0).sum(axis=1).mean() / k)
    return out, res


def strat_dual_momentum(name, risk_syms, defensive=("IEF", "TLT", "GLD"), k=4, hold=21):
    """Antonacci-style dual momentum: hold the top-k risk assets with POSITIVE 12m absolute
    momentum; otherwise rotate into the best defensive (bonds/gold). Caps drawdown by exiting
    risk in downtrends. Universe = sector leaders + defensives."""
    syms = list(dict.fromkeys(list(risk_syms) + list(defensive)))
    px = _px(syms)
    spy = _spy().reindex(px.index).ffill()
    lp = np.log(px)
    mom12 = (lp.shift(1) - lp.shift(252))                            # 12m absolute momentum, lagged
    risk = [s for s in risk_syms if s in px.columns]
    defv = [s for s in defensive if s in px.columns]
    # fast risk-off signal (CAN SLIM "M"): SPY below its 200-SMA -> de-risk to defensives/cash
    spy_off = ~((spy > spy.rolling(200, min_periods=150).mean()).shift(1).reindex(px.index).ffill().fillna(False))
    rebal = pd.Series(False, index=px.index)
    rebal.iloc[::hold] = True
    sel = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    for t in px.index[rebal.values]:
        row = mom12.loc[t]
        drow = row[defv].dropna().sort_values(ascending=False) if defv else pd.Series(dtype=float)
        if bool(spy_off.loc[t]):                                       # risk-off: bonds/gold only, else cash
            winners = [s for s in drow.index if drow[s] > 0][:k]
        else:
            rk = row[risk].dropna().sort_values(ascending=False)
            bond_mom = float(drow.max()) if len(drow) else 0.0         # relative bar = best defensive
            winners = [s for s in rk.index[:k] if rk[s] > 0 and rk[s] > bond_mom]
            n_empty = k - len(winners)
            if n_empty > 0 and len(drow):
                winners += [s for s in drow.index if drow[s] > 0][:n_empty]
        if winners:
            sel.loc[t, winners] = 1.0                                 # remaining empty slots => cash
    direction = sel.where(rebal).ffill().fillna(0.0)
    res = run_engine(px, (direction > 0).astype(int), spy, k)
    out = {"strategy": name, "k": k, "hold": hold,
           "full": _metrics(res.equity, res.returns, "full")}
    for sp, (a, b) in SPLITS.items():
        m = (res.equity.index >= a) & (res.equity.index <= b)
        if m.sum() > 60:
            eq = res.equity[m] / res.equity[m].iloc[0]
            out[sp] = _metrics(eq, res.returns[m], sp)
    return out, res


def vol_target(returns, target=0.12, lookback=20, lev_cap=1.5):
    """Ex-ante vol targeting: scale by target/trailing-vol (lagged), capped leverage. The
    standard institutional drawdown-control lever — lowers MDD at the cost of upside."""
    tv = (returns.rolling(lookback).std() * np.sqrt(252)).shift(1)
    scale = (target / tv).clip(upper=lev_cap).fillna(0.0)
    return returns * scale


def strat_diversified_voltarget(name="S7_diversified_voltarget"):
    """Lowest-drawdown design: top-10 momentum across ALL sectors, regime-gated, then the whole
    book is vol-targeted to 12% annual. Diversification (k=10) + de-leveraging in turbulence."""
    syms = sorted({s for v in SECTORS.values() for s in v})
    px = _px(syms)
    spy = _spy().reindex(px.index).ffill()
    d = momentum_trend_direction(px, spy, k=10, hold=21, regime=True)
    res = run_engine(px, d, spy, 10)
    vt = vol_target(res.returns, target=0.12)
    eq = (1 + vt).cumprod()
    out = {"strategy": name, "full": _metrics(eq, vt, "full")}
    for sp, (a, b) in SPLITS.items():
        m = (eq.index >= a) & (eq.index <= b)
        if m.sum() > 60:
            e = eq[m] / eq[m].iloc[0]
            out[sp] = _metrics(e, vt[m], sp)
    return out, res


def strat_minervini(name="S6_Minervini_broad"):
    """Validate the Minervini Trend Template + measure decay (2016-19 vs 2020-24)."""
    from trading_analysis.strategy.rules.minervini_trend import MinerviniTrendRule, rs_rating
    syms = sorted({s for v in SECTORS.values() for s in v})
    oh = STORE.load_ohlcv(syms)
    px = _px(syms)
    spy = _spy().reindex(px.index).ffill()
    direction = MinerviniTrendRule().to_pivot(oh).reindex(index=px.index, columns=px.columns).fillna(0)
    spy_sma = spy.rolling(200, min_periods=150).mean()
    on = (spy > spy_sma).shift(1).reindex(px.index).ffill().fillna(False)
    direction = direction.mul(np.asarray(on).astype(int), axis=0)
    rs = rs_rating(px).shift(1).reindex(index=px.index, columns=px.columns)
    keep = rs.where(direction > 0).rank(axis=1, ascending=False, method="first") <= 10
    direction = direction.where(keep, 0).astype(int)
    res = run_engine(px, direction, spy, 10)
    out = {"strategy": name, "full": _metrics(res.equity, res.returns, "full")}
    for sp, (a, b) in SPLITS.items():
        m = (res.equity.index >= a) & (res.equity.index <= b)
        if m.sum() > 60:
            eq = res.equity[m] / res.equity[m].iloc[0]
            out[sp] = _metrics(eq, res.returns[m], sp)
    return out, res


def _print(out):
    f = out["full"]
    print(f"\n### {out['strategy']}")
    print(f"  FULL 2015-24 : CAGR {f['CAGR']:+.1%}  Sharpe {f['Sharpe']:+.2f}  MDD {f['MDD']:+.1%}  total {f['total']:+.0%}")
    for sp in SPLITS:
        if sp in out:
            s = out[sp]
            print(f"  {sp}    : CAGR {s['CAGR']:+.1%}  Sharpe {s['Sharpe']:+.2f}  MDD {s['MDD']:+.1%}")


def main():
    print("=" * 78)
    print("INDUSTRY STRATEGY STUDY — selection + entry/exit, honest metrics + decay split")
    print("target: 50-100% CAGR with LOW drawdown @ $100k.  (read the verdict at the end)")
    print("=" * 78)
    results = []
    results.append(strat_momentum("S1_AI_semis_mom (k=5, monthly)", SECTORS["AI_semis"], k=5)[0])
    results.append(strat_momentum("S2_AI_semis_concentrated (k=3)", SECTORS["AI_semis"], k=3)[0])
    results.append(strat_momentum("S3_space_defense_mom (k=5)", SECTORS["space_defense"], k=5)[0])
    results.append(strat_momentum("S4_robotics_mom (k=4)", SECTORS["robotics"], k=4)[0])
    allrisk = sorted({s for kk in ["AI_semis", "software_AI", "space_defense", "robotics"] for s in SECTORS[kk]})
    results.append(strat_dual_momentum("S5_dual_momentum_defensive (bonds/gold rotation)", allrisk, k=4)[0])
    results.append(strat_minervini("S6_Minervini_validation")[0])
    results.append(strat_diversified_voltarget("S7_diversified_voltarget (12% vol, k=10)")[0])

    for out in results:
        _print(out)
    print("\n" + "=" * 78)
    print("Pass 50% CAGR @ full window:",
          [r["strategy"].split("_")[0] for r in results if r["full"]["CAGR"] >= 0.50])
    print("Pass MDD<10% @ full window :",
          [r["strategy"].split("_")[0] for r in results if r["full"]["MDD"] > -0.10])
    print("=" * 78)


if __name__ == "__main__":
    main()
