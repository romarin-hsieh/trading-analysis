"""Leveraged sector-ETF trend strategies — the realistic retail path to 50-100% CAGR.

The daily-reset decay of 3x ETFs is baked into adj_close, so this is a realistic backtest.
The whole point: a trend/regime filter is what prevents the -80/-90% leveraged wipeout you get
from buy-and-hold. Each strategy: hold the leveraged ETF only while its underlying is in an
uptrend (above its 200-SMA, lagged); otherwise sit in cash. Reproducible, point-in-time.

Run: uv run python scripts/leveraged_strategies.py
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
SPLITS = {"2016-2019": ("2016-01-01", "2019-12-31"), "2020-2024": ("2020-01-01", "2024-12-31")}


def _px(syms):
    return STORE.load_close_pivot(syms, column="adj_close").ffill()


def _spy(idx):
    return _px(["SPY"]).iloc[:, 0].reindex(idx).ffill()


def _trend(sym, win=200):
    u = _px([sym]).iloc[:, 0]
    mp = max(2, int(win * 0.75))
    return (u > u.rolling(win, min_periods=mp).mean()).shift(1)


def _metrics(eq, ret):
    return {"CAGR": cagr(eq), "Sharpe": sharpe(ret), "MDD": max_drawdown(eq),
            "total": float(eq.iloc[-1] / eq.iloc[0] - 1.0)}


def _run(close_df, direction, label):
    spy = _spy(close_df.index)
    cfg = BacktestConfig(fees_bps=5.0, slippage_bps=5.0, cash=100_000.0,
                         benchmark="SPY", target_percent=1.0, price_field="adj_close")
    res = run_backtest(close_df, direction.reindex_like(close_df).fillna(0), cfg, benchmark_close=spy)
    out = {"strategy": label, "full": _metrics(res.equity, res.returns)}
    for sp, (a, b) in SPLITS.items():
        m = (res.equity.index >= a) & (res.equity.index <= b)
        if m.sum() > 60:
            eq = res.equity[m] / res.equity[m].iloc[0]
            out[sp] = _metrics(eq, res.returns[m])
    return out


def buyhold(etf):
    p = _px([etf])
    d = pd.DataFrame({etf: 1}, index=p.index)
    return _run(p, d, f"{etf} buy&hold (no filter)")


def regime_filtered(etf, underlying, dual=False):
    p = _px([etf])
    on = _trend(underlying, 200).reindex(p.index).ffill().fillna(False)
    label = f"{etf} + {underlying}>200SMA"
    if dual:  # add a faster 50-SMA exit on the underlying to cut drawdown harder
        on = on & _trend(underlying, 50).reindex(p.index).ffill().fillna(False)
        label += " + 50SMA"
    d = pd.DataFrame({etf: on.astype(int)}, index=p.index)
    return _run(p, d, label)


def lev_momentum(etfs, underlyings, k=1, hold=21):
    """Rotate into the top-k leveraged ETFs by 3-month momentum, only while SPY>200SMA."""
    p = _px(etfs)
    lp = np.log(p)
    mom = (lp.shift(1) - lp.shift(63))                       # 3m momentum, lagged
    rebal = pd.Series(False, index=p.index)
    rebal.iloc[::hold] = True
    topk = (mom.rank(axis=1, ascending=False, method="first") <= k).where(rebal).ffill().fillna(False)
    spy_on = _trend("SPY", 200).reindex(p.index).ffill().fillna(False)
    direction = topk.mul(np.asarray(spy_on).astype(int), axis=0).astype(int)
    # normalize so k held => fully invested
    cfg = BacktestConfig(fees_bps=5.0, slippage_bps=5.0, cash=100_000.0,
                         benchmark="SPY", target_percent=1.0 / k, price_field="adj_close")
    spy = _spy(p.index)
    res = run_backtest(p, direction, cfg, benchmark_close=spy)
    out = {"strategy": f"lev-momentum top{k} (SPY-gated)", "full": _metrics(res.equity, res.returns)}
    for sp, (a, b) in SPLITS.items():
        m = (res.equity.index >= a) & (res.equity.index <= b)
        if m.sum() > 60:
            eq = res.equity[m] / res.equity[m].iloc[0]
            out[sp] = _metrics(eq, res.returns[m])
    return out


def _print(o):
    f = o["full"]
    print(f"\n### {o['strategy']}")
    print(f"  FULL 2015-24 : CAGR {f['CAGR']:+.1%}  Sharpe {f['Sharpe']:+.2f}  MDD {f['MDD']:+.1%}  total {f['total']:+.0%}")
    for sp in SPLITS:
        if sp in o:
            s = o[sp]
            print(f"  {sp}    : CAGR {s['CAGR']:+.1%}  Sharpe {s['Sharpe']:+.2f}  MDD {s['MDD']:+.1%}")


def main():
    print("=" * 80)
    print("LEVERAGED SECTOR-ETF TREND STRATEGIES — the path to 50-100% CAGR (and its real risk)")
    print("=" * 80)
    res = [
        buyhold("SOXL"),
        regime_filtered("SOXL", "SOXX"),
        regime_filtered("SOXL", "SOXX", dual=True),
        regime_filtered("TQQQ", "QQQ"),
        regime_filtered("TQQQ", "QQQ", dual=True),
        lev_momentum(["SOXL", "TQQQ", "TECL", "SPXL", "USD"], None, k=1),
    ]
    for o in res:
        _print(o)
    print("\n" + "=" * 80)
    print("Hit 50%+ CAGR full-window:", [o["strategy"][:28] for o in res if o["full"]["CAGR"] >= 0.50])
    print("...of those, MDD:", [(o["strategy"][:18], f"{o['full']['MDD']:.0%}") for o in res if o["full"]["CAGR"] >= 0.50])
    print("=" * 80)


if __name__ == "__main__":
    main()
