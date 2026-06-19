"""High-vol-FRIENDLY ablations of the momentum rulebook on the USER watchlist (2025).

The baseline momentum rulebook (uptrend filter + daily 50-SMA stop + SPY-200SMA regime gate, k=10)
made only +6.2% in 2025 on this ~137-name hyper-vol watchlist, badly LOSING to the equal-weight
buy&hold of the whole universe (+62.8%). Why? On 48-54%-vol names the daily 50-SMA stop gets
whipsawed (sold at local bottoms) and the SPY-200SMA regime gate went to cash in the spring-2025
selloff and missed the V-recovery. This script peels the rules off one at a time to answer:

  can ANY high-vol-friendly variant at least NOT lose to buy&hold? And does removing rules
  MONOTONICALLY walk the return back up toward the +62.8% buy&hold limit?

All variants are fully LEAK-FREE: momentum, SMAs, regime are all lagged >=1 bar; top-k is recomputed
only on monthly rebalance bars then ffilled. Returns are net of 10bps on daily turnover.

  >>> SELECTION-BIAS CAVEAT (unchanged) <<<
The universe is hand-picked 2026-hot names (ASTS/RKLB/OKLO/IONQ/PLTR/HIMS...). Backtesting on a
hindsight-curated winners list is textbook look-ahead bias; the +62.8% buy&hold is the universe being
pre-selected, NOT skill. NONE of these numbers is a forward/deployable estimate.

Run: uv run python scripts/custom_universe_variants.py
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
    px: pd.DataFrame,
    spy: pd.Series,
    k: int = 10,
    hold: int = 21,
    *,
    use_uptrend: bool = True,
    use_stop: bool = True,
    use_regime: bool = True,
    stop_win: int = 50,
    mom_lb: int = 126,
    mom_skip: int = 21,
    hysteresis: bool = False,
) -> pd.DataFrame:
    """Flexible, leak-free daily 0/1 holdings matrix. Each rule is independently toggleable.

    momentum = (log(px).shift(mom_skip) - log(px).shift(mom_lb)).shift(1)   # point-in-time
    SMAs computed then .shift(1); top-k recomputed only on rebalance bars (::hold) then ffilled.
    use_uptrend: require price>50sma AND 50sma>150sma (all lagged).
    use_stop:    drop a name intramonth when px.shift(1) < its stop_win-SMA.shift(1).
    use_regime:  AND with (SPY>SPY200sma).shift(1).
    hysteresis:  hold a name until it falls OUT of the top-2k by momentum (low-turnover), instead of
                 the fixed monthly top-k membership.
    """
    lp = np.log(px)
    mom = (lp.shift(mom_skip) - lp.shift(mom_lb)).shift(1)            # leak-free momentum
    sma50 = px.rolling(50, min_periods=50).mean().shift(1)
    sma150 = px.rolling(150, min_periods=120).mean().shift(1)
    stop_sma = px.rolling(stop_win, min_periods=stop_win).mean().shift(1)
    px_lag = px.shift(1)

    # candidate momentum: gate by uptrend filter if requested
    if use_uptrend:
        up = (px_lag > sma50) & (sma50 > sma150)
        cand = mom.where(up)
    else:
        cand = mom.where(px_lag.notna())                             # any name with a valid price

    rebal = pd.Series(False, index=px.index)
    rebal.iloc[::hold] = True

    rank = cand.rank(axis=1, ascending=False, method="first")
    if not hysteresis:
        # numeric (1.0/NaN) carry-forward so monthly membership holds between rebalances (no object downcast)
        topk_daily = (rank <= k).astype(float)
        held = topk_daily.where(rebal).ffill().fillna(0.0) > 0.0
    else:
        # hysteresis: ENTER the top-k on a rebalance bar, then KEEP a held name daily as long as it
        # stays within the top-2k by (lagged) momentum; drop only when it exits the wider 2k band.
        enter = ((rank <= k).astype(float).where(rebal).fillna(0.0) > 0.0)
        keep_band = (rank <= 2 * k).fillna(False).astype(bool)       # daily wide retention band
        prev = pd.Series(False, index=px.columns)
        e_vals, k_vals = enter.to_numpy(), keep_band.to_numpy()
        out = np.zeros((len(px.index), len(px.columns)), dtype=bool)
        prev_arr = prev.to_numpy()
        for i in range(len(px.index)):
            cur = (prev_arr & k_vals[i]) | e_vals[i]                 # keep if still in band, or re-enter
            out[i] = cur
            prev_arr = cur
        held = pd.DataFrame(out, index=px.index, columns=px.columns)

    if use_stop:
        held = held & (px_lag > stop_sma)
    if use_regime:
        spy_sma = spy.rolling(200, min_periods=150).mean()
        on = (spy > spy_sma).astype(float).shift(1).reindex(px.index).ffill().fillna(0.0) > 0.0
        held = held & np.asarray(on)[:, None]
    return held.astype(int)


def evaluate(px: pd.DataFrame, held: pd.DataFrame, k: int):
    """Leak-free strategy return + net-of-cost daily series + diagnostics, per the primer spec.

    weight = held.shift(1) * (1/k) (so <k held => cash residual), lagged 1 bar.
    ret = (weight * px.pct_change()).sum(axis=1); charge 10bps on daily turnover.
    """
    w = held.shift(1) * (1.0 / k)
    rets = px.pct_change(fill_method=None)
    gross = (w * rets).sum(axis=1)
    turn = w.diff().abs().sum(axis=1)                                # daily one-sided turnover
    net = gross - turn * (COST_BPS / 1e4)
    avg_names = (held.shift(1) > 0).sum(axis=1)                      # names held each day
    return net, turn, avg_names


def seg(s: pd.Series) -> pd.Series:
    return s.loc[(s.index >= Y0) & (s.index <= Y1)].dropna()


def stat(net: pd.Series, turn: pd.Series, names: pd.Series):
    r = seg(net)
    if len(r) < 20:
        return None
    eq = (1.0 + r).cumprod()
    tot = float(eq.iloc[-1] - 1.0)
    sh = sharpe(r)
    vol = float(r.std() * np.sqrt(252))
    mdd = max_drawdown(eq)
    ann_turn = float(seg(turn).mean() * 252)
    avg_held = float(seg(names).mean())
    return tot, sh, vol, mdd, ann_turn, avg_held


def main():
    store = DuckStore("./data")
    avail = [t for t in UNIVERSE if t in store.list_symbols()]
    px = ss._px(avail)
    spy = ss._spy().reindex(px.index).ffill()

    print("=" * 104)
    print(f"USER WATCHLIST -- high-vol-friendly momentum ABLATIONS, 2025 (data through {px.index.max().date()})")
    print(f"  universe {len(avail)} names | net {COST_BPS:.0f}bps daily turnover | leak-free (signals lagged >=1 bar)")
    print("=" * 104)

    variants = [
        ("V1 baseline (uptrend+stop+regime, k=10)",
         dict(k=10, use_uptrend=True, use_stop=True, use_regime=True)),
        ("V2 no daily stop (uptrend+regime, k=10)",
         dict(k=10, use_uptrend=True, use_stop=False, use_regime=True)),
        ("V3 no regime / always-in (uptrend+stop, k=10)",
         dict(k=10, use_uptrend=True, use_stop=True, use_regime=False)),
        ("V4 no stop+no regime (uptrend only, k=10)",
         dict(k=10, use_uptrend=True, use_stop=False, use_regime=False)),
        ("V5 pure momentum (no rules, k=10)",
         dict(k=10, use_uptrend=False, use_stop=False, use_regime=False)),
        ("V6 pure momentum k=20 (diversified)",
         dict(k=20, use_uptrend=False, use_stop=False, use_regime=False)),
        ("V7 wider 150-SMA stop (uptrend+regime, k=10)",
         dict(k=10, use_uptrend=True, use_stop=True, use_regime=True, stop_win=150)),
        ("V8 hysteresis top-2k, no daily stop (uptrend, k=10)",
         dict(k=10, use_uptrend=True, use_stop=False, use_regime=False, hysteresis=True)),
    ]

    rows = []
    for name, kw in variants:
        kk = kw["k"]
        held = momentum_variant(px, spy, hold=21, **kw)
        net, turn, names = evaluate(px, held, kk)
        st = stat(net, turn, names)
        if st:
            rows.append((name, *st))

    # benchmarks
    ew = px.pct_change(fill_method=None).mean(axis=1)
    eq = (1.0 + seg(ew)).cumprod()
    rows.append(("equal-wt buy&hold (WHOLE universe)", float(eq.iloc[-1] - 1.0),
                 sharpe(seg(ew)), float(seg(ew).std() * np.sqrt(252)), max_drawdown(eq), 0.0,
                 float(len(avail))))
    voo = (store.load_close_pivot(["VOO"], column="adj_close")
           .reindex(px.index).ffill().iloc[:, 0].pct_change().fillna(0.0))
    eqv = (1.0 + seg(voo)).cumprod()
    rows.append(("VOO (S&P 500)", float(eqv.iloc[-1] - 1.0), sharpe(seg(voo)),
                 float(seg(voo).std() * np.sqrt(252)), max_drawdown(eqv), 0.0, 1.0))

    rows.sort(key=lambda r: r[1], reverse=True)                      # order by 2025 return

    hdr = f"{'variant':52s} {'2025 ret':>9s} {'Sharpe':>7s} {'vol':>6s} {'MDD':>7s} {'annTurn':>8s} {'avgN':>6s}"
    print(hdr)
    print("-" * 104)
    for name, tot, sh, vol, mdd, turn, avgn in rows:
        print(f"{name:52s} {tot:+9.1%} {sh:+7.2f} {vol:6.1%} {mdd:+7.1%} {turn:7.0%} {avgn:6.1f}")
    print("=" * 104)
    print("READ: every rule the baseline adds COSTS return on this hyper-vol list; the limit (no rules, high")
    print("k) converges toward equal-wt buy&hold. The buy&hold +62.8% is hindsight selection, not skill --")
    print("none of this is a forward estimate.")
    print("=" * 104)
    return rows


if __name__ == "__main__":
    main()
