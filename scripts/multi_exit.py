"""MULTI-DIMENSIONAL EXIT DISCIPLINE -- the user's 5-factor stop (goal part 2).

Five exit dimensions, each casts one VOTE per day (all lagged 1 bar, leak-free):
  V1 VIX panic     : VIX rolling-1y percentile > 0.80
  V2 position loss : drawdown from the position's running peak > 10%   ("開倉位置")
  V3 bias rate     : (close - SMA50)/SMA50 < -5%                        ("乖離率")
  V4 RSI           : RSI14 < 45                                          (momentum lost)
  V5 MACD          : histogram < 0 AND falling                           (trend rolling over)

EXIT when votes >= K (default 3/5); RE-ENTER when votes <= 1. Compared against: buy&hold,
each single dimension used alone as a stop, and the multi-vote overlay -- on QQQ (core) and
TQQQ (3x leveraged, where stop discipline actually matters). Net 5bps/leg.

The honest question: does the MULTI-dimension confirm-stack cut drawdown with LESS whipsaw
than any single indicator? (Project prior: single daily stops whipsaw; confirmation stacking
is the standard fix -- measure, don't assume.)

Run: uv run python scripts/multi_exit.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

COST = 0.0005
START = "2015-01-01"


def rsi(px: pd.Series, n: int = 14) -> pd.Series:
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def votes_frame(c: pd.Series, vix: pd.Series) -> pd.DataFrame:
    """The five daily exit votes, each already lagged 1 bar."""
    sma50 = c.rolling(50).mean()
    bias = (c - sma50) / sma50
    r14 = rsi(c)
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    hist = macd - macd.ewm(span=9, adjust=False).mean()
    dd = c / c.rolling(252, min_periods=20).max() - 1.0        # drawdown from running peak
    vix_pct = vix.reindex(c.index).ffill().rolling(252).rank(pct=True)
    V = pd.DataFrame({
        "V1_vix": (vix_pct > 0.80),
        "V2_posloss": (dd < -0.10),
        "V3_bias": (bias < -0.05),
        "V4_rsi": (r14 < 45),
        "V5_macd": (hist < 0) & (hist.diff() < 0),
    }, index=c.index)
    return V.shift(1).fillna(False)


def apply_overlay(base_r: pd.Series, out_flag: pd.Series) -> pd.Series:
    pos = (~out_flag).astype(float).shift(1).fillna(1.0)
    return pos * base_r - pos.diff().abs().fillna(0.0) * COST


def vote_exit_state(V: pd.DataFrame, k_exit=3, k_reenter=1) -> pd.Series:
    """Stateful: exit when votes>=k_exit, re-enter when votes<=k_reenter."""
    n = V.sum(axis=1)
    sig = pd.Series(np.nan, index=V.index)
    sig[n >= k_exit] = 1.0          # 1 = OUT
    sig[n <= k_reenter] = 0.0       # 0 = IN
    return sig.ffill().fillna(0.0).astype(bool)


def block(tkr: str, store: DuckStore, vix: pd.Series):
    c = store.load_close_pivot([tkr], column="adj_close").iloc[:, 0].dropna()
    r = c.pct_change().fillna(0.0).loc[START:]
    c = c.loc[c.index >= "2014-06-01"]
    V = votes_frame(c, vix).loc[START:]
    rows = []

    def add(name, ret, texit):
        ret = ret.dropna()
        eq = (1 + ret).cumprod()
        rows.append((name, cagr(eq), sharpe(ret), max_drawdown(eq), texit))

    add(f"{tkr} buy&hold (no stop)", r, 0.0)
    for col in V.columns:                                  # single-dimension stops
        flag = V[col]
        ret = apply_overlay(r, flag.reindex(r.index).fillna(False))
        yrs = len(r) / 252
        add(f"  single {col}", ret, float(flag.astype(int).diff().clip(lower=0).sum() / yrs))
    for k in (2, 3, 4):                                    # multi-vote confirm stack
        out = vote_exit_state(V.reindex(r.index).fillna(False), k_exit=k, k_reenter=1)
        ret = apply_overlay(r, out)
        yrs = len(r) / 252
        add(f"  MULTI vote>={k}/5", ret, float(out.astype(int).diff().clip(lower=0).sum() / yrs))

    print(f"\n{tkr} ({START}..{c.index[-1].date()}):")
    print(f"  {'exit rule':28s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'exits/yr':>9s}")
    for name, cg, sh, md, tx in rows:
        print(f"  {name:28s} {cg:+7.1%} {sh:+7.2f} {md:+7.1%} {tx:9.1f}")
    return rows


def main():
    store = DuckStore("./data")
    vix = store.load_close_pivot(["^VIX"], column="close").iloc[:, 0]
    print("=" * 88)
    print("MULTI-DIMENSIONAL EXIT (VIX + position + bias + RSI + MACD votes) vs single-indicator stops")
    print("=" * 88)
    q = block("QQQ", store, vix)
    t = block("TQQQ", store, vix)
    print("-" * 88)

    def pick(rows, key):
        return next(x for x in rows if key in x[0])
    for label, rows in (("QQQ", q), ("TQQQ", t)):
        bh = pick(rows, "buy&hold")
        m3 = pick(rows, ">=3/5")
        best_single = max((x for x in rows if "single" in x[0]), key=lambda x: x[2])
        print(f"{label}: B&H Sharpe {bh[2]:+.2f} MDD {bh[3]:+.1%} | MULTI>=3 Sharpe {m3[2]:+.2f} "
              f"MDD {m3[3]:+.1%} ({m3[4]:.1f} exits/yr) | best single [{best_single[0].strip()[:18]}] "
              f"Sharpe {best_single[2]:+.2f} MDD {best_single[3]:+.1%} ({best_single[4]:.1f} exits/yr)")
    print("=" * 88)
    print("READ: the vote stack is a CONFIRMATION filter -- it should exit less often than any single")
    print("trigger while catching the real regime breaks. Judge on: MDD cut per unit of CAGR given up,")
    print("and exits/yr (whipsaw). This module feeds the Telegram exit-monitor (scripts/notify/).")
    print("=" * 88)


if __name__ == "__main__":
    main()
