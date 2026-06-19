"""Leakage/causality perturbation audit of custom_universe_variants.py.

Strategy under test: V5/V6 pure-momentum winners and the regime-gated baselines.

TEST LOGIC:
  - extra_lag=L shifts EVERY signal (momentum, SMAs, regime, holdings) by an ADDITIONAL L bars.
    A genuine (leak-free) ordering is robust to +1 bar: the rank ordering is driven by 6-month
    momentum, which barely changes day-to-day, so +1 bar of lag should move 2025 return only a
    little. A LEAKAGE artifact (signal peeking at same/next bar) COLLAPSES toward ~0 / buy&hold
    when you push it back a bar.
  - LEAK CONTROL: a deliberately-leaky variant (holdings NOT shifted before multiplying returns,
    i.e. trade today on today's close-to-close move) is included to PROVE the perturbation can
    actually detect leakage -- it should print a hugely inflated return that collapses under +1 lag.

Run: uv run python scripts/custom_universe_leakcheck.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import sector_strategies as ss  # noqa: E402
from custom_universe_2025 import UNIVERSE  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

Y0, Y1 = "2025-01-01", "2025-12-31"
COST_BPS = 10.0


def momentum_variant(
    px, spy, k=10, hold=21, *,
    use_uptrend=True, use_stop=True, use_regime=True,
    stop_win=50, mom_lb=126, mom_skip=21, extra_lag=0,
):
    """Same logic as custom_universe_variants.momentum_variant, with an extra_lag knob applied
    to EVERY signal (momentum, SMAs, regime). extra_lag=0 reproduces the original exactly."""
    L = extra_lag
    lp = np.log(px)
    mom = (lp.shift(mom_skip) - lp.shift(mom_lb)).shift(1 + L)
    sma50 = px.rolling(50, min_periods=50).mean().shift(1 + L)
    sma150 = px.rolling(150, min_periods=120).mean().shift(1 + L)
    stop_sma = px.rolling(stop_win, min_periods=stop_win).mean().shift(1 + L)
    px_lag = px.shift(1 + L)

    if use_uptrend:
        up = (px_lag > sma50) & (sma50 > sma150)
        cand = mom.where(up)
    else:
        cand = mom.where(px_lag.notna())

    rebal = pd.Series(False, index=px.index)
    rebal.iloc[::hold] = True
    rank = cand.rank(axis=1, ascending=False, method="first")
    topk_daily = (rank <= k).astype(float)
    held = topk_daily.where(rebal).ffill().fillna(0.0) > 0.0

    if use_stop:
        held = held & (px_lag > stop_sma)
    if use_regime:
        spy_sma = spy.rolling(200, min_periods=150).mean()
        on = (spy > spy_sma).astype(float).shift(1 + L).reindex(px.index).ffill().fillna(0.0) > 0.0
        held = held & np.asarray(on)[:, None]
    return held.astype(int)


def evaluate(px, held, k, *, leak=False):
    """leak=False: correct, holdings lagged 1 bar before multiplying returns (primer spec).
    leak=True:  DELIBERATE leak -- multiply today's holdings by today's return (no shift)."""
    rets = px.pct_change(fill_method=None)
    w = (held if leak else held.shift(1)) * (1.0 / k)
    gross = (w * rets).sum(axis=1)
    turn = w.diff().abs().sum(axis=1)
    net = gross - turn * (COST_BPS / 1e4)
    return net, turn


def seg(s):
    return s.loc[(s.index >= Y0) & (s.index <= Y1)].dropna()


def stat(net, turn):
    r = seg(net)
    if len(r) < 20:
        return None
    eq = (1.0 + r).cumprod()
    return (float(eq.iloc[-1] - 1.0), sharpe(r),
            float(r.std() * np.sqrt(252)), max_drawdown(eq),
            float(seg(turn).mean() * 252))


def main():
    store = DuckStore("./data")
    avail = [t for t in UNIVERSE if t in store.list_symbols()]
    px = ss._px(avail)
    spy = ss._spy().reindex(px.index).ffill()

    ew = px.pct_change(fill_method=None).mean(axis=1)
    bh = stat(ew, pd.Series(0.0, index=px.index))

    print("=" * 100)
    print(f"LEAKAGE PERTURBATION AUDIT -- universe {len(avail)} | 2025 | net {COST_BPS:.0f}bps")
    print("  test: +1 extra bar of lag on ALL signals. Leak-free -> stable. Leakage -> collapses.")
    print("=" * 100)
    print(f"{'variant':46s} {'lag':>4s} {'2025 ret':>9s} {'Sharpe':>7s} {'vol':>6s} {'MDD':>7s} {'annTurn':>8s}")
    print("-" * 100)
    print(f"{'equal-wt buy&hold (reference)':46s} {'--':>4s} {bh[0]:+9.1%} {bh[1]:+7.2f} {bh[2]:6.1%} {bh[3]:+7.1%} {0.0:7.0%}")
    print("-" * 100)

    cfgs = [
        ("V6 pure-mom k=20", dict(k=20, use_uptrend=False, use_stop=False, use_regime=False)),
        ("V5 pure-mom k=10", dict(k=10, use_uptrend=False, use_stop=False, use_regime=False)),
        ("V1 baseline (up+stop+regime)", dict(k=10, use_uptrend=True, use_stop=True, use_regime=True)),
        ("V3 no-regime (up+stop)", dict(k=10, use_uptrend=True, use_stop=True, use_regime=False)),
    ]
    deltas = {}
    for name, kw in cfgs:
        kk = kw["k"]
        for L in (0, 1, 2):
            held = momentum_variant(px, spy, hold=21, extra_lag=L, **kw)
            net, turn = evaluate(px, held, kk)
            st = stat(net, turn)
            tag = "base" if L == 0 else f"+{L}"
            print(f"{name:46s} {tag:>4s} {st[0]:+9.1%} {st[1]:+7.2f} {st[2]:6.1%} {st[3]:+7.1%} {st[4]:7.0%}")
            if L == 0:
                deltas[name] = st[0]
            elif L == 1:
                deltas[name] = (deltas[name], st[0])
        print("-" * 100)

    # LEAK CONTROL: prove the perturbation CAN detect a leak.
    print("LEAK CONTROL (deliberate same-bar leak; should be huge at base, collapse under +1):")
    kw = dict(k=10, use_uptrend=False, use_stop=False, use_regime=False)
    for L in (0, 1):
        held = momentum_variant(px, spy, hold=21, extra_lag=L, **kw)
        net, turn = evaluate(px, held, 10, leak=True)
        st = stat(net, turn)
        tag = "base" if L == 0 else f"+{L}"
        print(f"{'  LEAKY V5 (no holdings.shift)':46s} {tag:>4s} {st[0]:+9.1%} {st[1]:+7.2f} {st[2]:6.1%} {st[3]:+7.1%} {st[4]:7.0%}")
    print("=" * 100)
    print("VERDICT BASIS -- base vs +1 lag (real ordering = small move; leak = collapse):")
    for n, (b, p) in deltas.items():
        print(f"  {n:40s} base {b:+7.1%} -> +1lag {p:+7.1%}  (delta {p - b:+.1%})")
    print("=" * 100)


if __name__ == "__main__":
    main()
