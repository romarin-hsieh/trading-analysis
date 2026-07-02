"""ENSEMBLE / MIXING designs on the strategy zoo -- the user's "FILTER + weighted blend" ask.

Reads the 52 time-series position series saved by strategy_zoo.py and evaluates MIXING designs:
  E1 vote_fraction   position = mean of all rule positions (continuous 0..1 exposure)
  E2 vote_majority   long 100% when >=50% of rules are long, else flat
  E3 topN_walkfwd    each month, pick top-10 rules by TRAILING 252d Sharpe, hold their equal blend
                     (walk-forward: selection uses only past data -- deployable)
  E4 triple_filter   trend(SMA200) AND momentum(TSmom 126d) AND volume(OBV>SMA50) -- classic
                     "MA + momentum + volume" confirm stack
  E5 best_in_sample  the single rule with the best 2015-2020 Sharpe, held 2021+ (overfit reference)

Honest evaluation: full period AND the 2021+ holdout (selection-free zone). Benchmarks: QQQ B&H
and the equal-weight of ALL rules. The question is NOT "can mixing beat buy&hold" (mixing long/flat
rules on one asset mathematically caps upside at B&H); it is "does mixing deliver a better
RISK-ADJUSTED path (Sharpe/MDD) than any honest single rule, without in-sample selection?"

Run: uv run python scripts/ensemble_mix.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402

COST = 0.0005
SPLIT = "2021-01-01"


def run_pos(pos: pd.Series, r: pd.Series) -> pd.Series:
    pos = pos.reindex(r.index).fillna(0.0).shift(1).fillna(0.0)
    return pos * r - pos.diff().abs().fillna(0.0) * COST


def seg_stats(ret: pd.Series, a=None, b=None):
    seg = ret.loc[a:b].dropna() if (a or b) else ret.dropna()
    if len(seg) < 60:
        return None
    eq = (1 + seg).cumprod()
    return {"CAGR": cagr(eq), "Sharpe": sharpe(seg), "MDD": max_drawdown(eq)}


def line(name, ret):
    f = seg_stats(ret)
    h = seg_stats(ret, SPLIT, None)
    return (f"{name:26s} {f['CAGR']:+7.1%} {f['Sharpe']:+7.2f} {f['MDD']:+7.1%}   "
            f"{h['CAGR']:+7.1%} {h['Sharpe']:+7.2f} {h['MDD']:+7.1%}")


def main():
    posmat = pd.read_parquet("data/_zoo_positions.parquet")
    r = pd.read_parquet("data/_zoo_qqq_ret.parquet")["qqq_ret"]
    posmat = posmat.reindex(r.index).fillna(0.0)
    names = list(posmat.columns)

    # per-rule daily returns (for trailing-Sharpe selection and blends)
    rule_ret = pd.DataFrame({n: run_pos(posmat[n], r) for n in names})

    # E1 fraction-of-votes exposure
    e1 = run_pos(posmat.mean(axis=1), r)

    # E2 binary majority
    e2 = run_pos((posmat.mean(axis=1) >= 0.5).astype(float), r)

    # E3 walk-forward top-10 by trailing 252d Sharpe, monthly reselect (no lookahead)
    roll_mean = rule_ret.rolling(252).mean()
    roll_std = rule_ret.rolling(252).std()
    trail_sharpe = (roll_mean / roll_std.replace(0, np.nan)) * np.sqrt(252)
    month = pd.Series(r.index.to_period("M"), index=r.index)
    sel_w = pd.DataFrame(0.0, index=r.index, columns=names)
    cur = pd.Series(0.0, index=pd.Index(names))
    prev_m = None
    for t in r.index:
        m = month.loc[t]
        if m != prev_m:
            ts = trail_sharpe.loc[:t].iloc[:-1]          # strictly past data
            if len(ts) > 260:
                last = ts.iloc[-1].dropna()
                cur = pd.Series(0.0, index=pd.Index(names))
                if len(last) >= 10:
                    cur[last.nlargest(10).index] = 1.0 / 10
            prev_m = m
        sel_w.loc[t] = cur
    e3 = (sel_w.shift(1) * rule_ret).sum(axis=1)          # blend of net rule returns

    # E4 triple filter AND stack
    tf = (posmat["close_above_SMA200"].astype(bool)
          & posmat["TSmom_126d"].astype(bool)
          & posmat["OBV_above_SMA50"].astype(bool)).astype(float)
    e4 = run_pos(tf, r)

    # E5 best-in-sample single rule (2015-2020) held out-of-sample
    is_sharpe = {n: seg_stats(rule_ret[n], None, "2020-12-31") for n in names}
    best = max((k for k in is_sharpe if is_sharpe[k]), key=lambda k: is_sharpe[k]["Sharpe"])
    e5 = rule_ret[best]

    ew_all = rule_ret.mean(axis=1)

    print("=" * 100)
    print(f"ENSEMBLE / MIXING on {len(names)} zoo rules (QQQ)   left=FULL 2015-2026   right=HOLDOUT {SPLIT}+")
    print("=" * 100)
    print(f"{'design':26s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s}   {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s}")
    print("-" * 100)
    print(line("QQQ buy&hold", r))
    print(line("EW-all-rules blend", ew_all))
    print(line("E1 vote-fraction expo", e1))
    print(line("E2 vote-majority", e2))
    print(line("E3 top10 walk-forward", e3))
    print(line("E4 triple-filter AND", e4))
    print(line(f"E5 IS-best [{best[:16]}]", e5))
    print("-" * 100)
    hold_rows = {"QQQ B&H": seg_stats(r, SPLIT, None), "E1": seg_stats(e1, SPLIT, None),
                 "E2": seg_stats(e2, SPLIT, None), "E3": seg_stats(e3, SPLIT, None),
                 "E4": seg_stats(e4, SPLIT, None), "E5": seg_stats(e5, SPLIT, None)}
    best_hold = max((k for k in hold_rows if k != "QQQ B&H"), key=lambda k: hold_rows[k]["Sharpe"])
    print(f"HOLDOUT verdict: best mix by Sharpe = {best_hold} "
          f"(Sharpe {hold_rows[best_hold]['Sharpe']:+.2f} vs B&H {hold_rows['QQQ B&H']['Sharpe']:+.2f}); "
          f"IS-best single rule holdout Sharpe = {hold_rows['E5']['Sharpe']:+.2f}")
    print("READ: mixing long/flat rules on ONE asset cannot beat B&H CAGR by construction; the honest")
    print("wins to look for are (a) lower MDD at similar Sharpe, (b) ensemble > in-sample-best OOS")
    print("(selection robustness), (c) stability across the split. Anything else is overfit theater.")
    print("=" * 100)


if __name__ == "__main__":
    main()
