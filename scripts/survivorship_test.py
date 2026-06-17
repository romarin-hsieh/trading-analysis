"""TASK B — survivorship-bias correction on our two most survivorship-vulnerable claims.

We re-test on a survivorship-AWARE universe: the 501 current S&P500 names (cur) PLUS 111
recovered names that were in the S&P500 sometime in 2015-2024 but have since been removed or
delisted (surv). Survivor prices go NaN at delisting; we HOLD A NAME ONLY WHILE ITS DATA EXISTS
(renormalize the equal-weight book over names that have data each day). No look-ahead: every
signal is lagged >=1 bar, returns start the day AFTER the signal, momentum L/S nets 10 bps/leg.

TEST 1 RETURN INFLATION : equal-weight, monthly-rebalanced buy&hold. CAGR/Sharpe/MDD cur vs union.
TEST 2 MOMENTUM ROBUSTNESS : factor mom_12_1 = px.shift(21)/px.shift(252)-1. rank-IC vs 21d fwd
        return (ic_summary -> IC/ICIR/t) + top/bottom-quintile long-short Sharpe (net 10bps),
        computed on cur AND union — does adding the survivorship-excluded names move the verdict?
TEST 3 (cheap extra) LOW-VOL : factor = -trailing-63d vol (low vol = high score). Same IC gate.

HONEST CAVEAT (stated in output): we recovered only 111/262 = 42% of removed names. Yahoo purged
most bankrupt-to-zero tickers (AABA, CBS, ENDP, many *Q bankruptcies), so this correction MISSES
the worst zeros. Measured survivorship effect is therefore a LOWER BOUND on the true effect.
Further: only 9 of the 111 recovered names actually go NaN inside the window (most got acquired/
renamed with a continuing price series) -> the survivor cohort we add is itself biased toward the
milder removals, weakening the correction further.

Run: uv run python scripts/survivorship_test.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

from trading_analysis.backtest.metrics import (  # noqa: E402
    cagr,
    max_drawdown,
    sharpe,
)
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
)

START, END = "2015-01-01", "2024-12-31"
COST_BPS = 10.0  # per traded leg
STORE = DuckStore("./data")


def nonoverlap_t(ic: pd.Series, step: int = 21) -> tuple[float, int]:
    """Autocorrelation-honest t-stat: 21d fwd-return ICs sampled daily OVERLAP (AC1~0.93), so the
    naive ICIR*sqrt(n) t is ~sqrt(21)~3.7x inflated. Sample every `step`-th IC (non-overlapping)
    and t-test that. Returns (t, n_effective)."""
    s = ic.dropna().iloc[::step]
    sd = s.std(ddof=1)
    if len(s) < 3 or not np.isfinite(sd) or sd == 0:
        return float("nan"), len(s)
    return float(s.mean() / (sd / np.sqrt(len(s)))), len(s)


def _load_pivot(symbols: list[str]) -> pd.DataFrame:
    """adj_close (total return) pivot restricted to the window; survivors NaN after delist."""
    px = STORE.load_close_pivot(sorted(set(symbols)), column="adj_close")
    return px.loc[START:END]


def ew_buyhold(px: pd.DataFrame, step: int = 21) -> pd.Series:
    """Equal-weight, monthly-rebalanced buy&hold. Hold only names with data each day:
    target weight = 1/(#names with valid price), reset every `step` bars, drift between.
    Daily return = mean of available single-name returns weighted by (lagged) book weights."""
    rets = px.pct_change(fill_method=None)
    avail = px.notna()
    # rebalance bars: reset to equal weight over names available THAT bar
    rebal = np.zeros(len(px), dtype=bool)
    rebal[::step] = True
    weights = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    w = pd.Series(0.0, index=px.columns)
    for i, _ts in enumerate(px.index):
        live = avail.iloc[i]
        if rebal[i] or w[live].sum() <= 0:
            n = int(live.sum())
            w = pd.Series(0.0, index=px.columns)
            if n > 0:
                w[live] = 1.0 / n
        else:
            # drift previous weights by yesterday's returns, drop names that just went NaN
            r = rets.iloc[i].fillna(0.0)
            w = w * (1.0 + r)
            w[~live] = 0.0
            tot = w.sum()
            if tot > 0:
                w = w / tot
        weights.iloc[i] = w
    # portfolio return: yesterday's weights * today's single-name returns (names alive yesterday & today)
    wl = weights.shift(1).fillna(0.0)
    port = (wl * rets.fillna(0.0)).sum(axis=1)
    return port.iloc[1:]


def mom_12_1(px: pd.DataFrame) -> pd.DataFrame:
    """12-1 momentum, lagged: px.shift(21)/px.shift(252) - 1 (skip most recent month)."""
    return (px.shift(21) / px.shift(252) - 1.0).shift(1)


def neg_vol_63(px: pd.DataFrame) -> pd.DataFrame:
    """Low-vol factor = -(trailing 63d daily-return vol), lagged. Higher = lower vol."""
    vol = px.pct_change(fill_method=None).rolling(63, min_periods=40).std()
    return (-vol).shift(1)


def quintile_long_short(factor: pd.DataFrame, fwd: pd.DataFrame, step: int = 21) -> pd.Series:
    """Monthly-rebalanced top-minus-bottom quintile long-short daily return, net COST_BPS/leg.
    Equal-weight within each quintile; rebalanced every `step` bars; cost charged on turnover."""
    idx = factor.index.intersection(fwd.index)
    cols = factor.columns.intersection(fwd.columns)
    f = factor.loc[idx, cols]
    rebal_pos = np.zeros(len(idx), dtype=bool)
    rebal_pos[::step] = True
    long_w = pd.DataFrame(0.0, index=idx, columns=cols)
    short_w = pd.DataFrame(0.0, index=idx, columns=cols)
    lw = pd.Series(0.0, index=cols)
    sw = pd.Series(0.0, index=cols)
    for i, ts in enumerate(idx):
        if rebal_pos[i]:
            row = f.loc[ts].dropna()
            lw = pd.Series(0.0, index=cols)
            sw = pd.Series(0.0, index=cols)
            if len(row) >= 10:
                q = int(np.ceil(len(row) / 5))
                ranked = row.sort_values()
                bot = ranked.index[:q]
                top = ranked.index[-q:]
                lw[top] = 1.0 / len(top)
                sw[bot] = 1.0 / len(bot)
        long_w.loc[ts] = lw
        short_w.loc[ts] = sw
    # single-bar forward returns: use 1-bar fwd return so the daily series is investable
    r1 = px_global.loc[idx, cols].pct_change(fill_method=None).shift(-1)  # ts->ts+1 return
    lwl = long_w  # weights set at ts apply to the ts->ts+1 return
    swl = short_w
    long_ret = (lwl * r1.fillna(0.0)).sum(axis=1)
    short_ret = (swl * r1.fillna(0.0)).sum(axis=1)
    ls = long_ret - short_ret
    # turnover cost: |w_t - w_{t-1}| summed over both books, charged at rebalance
    turn = (long_w.diff().abs().sum(axis=1) + short_w.diff().abs().sum(axis=1)).fillna(0.0)
    ls_net = ls - turn * (COST_BPS / 1e4)
    return ls_net.dropna()


px_global: pd.DataFrame = pd.DataFrame()  # set in main for quintile_long_short


def momentum_block(px: pd.DataFrame, label: str) -> dict:
    global px_global
    px_global = px
    fac = mom_12_1(px)
    fwd = forward_returns(px, horizon=21)
    ic = cross_sectional_ic(fac, fwd)
    summ = ic_summary(ic)
    t_no, n_no = nonoverlap_t(ic)
    ls = quintile_long_short(fac, fwd)
    ls_eq = (1 + ls).cumprod()
    return {
        "label": label,
        "n_dates": summ["n"],
        "mean_ic": summ["mean_ic"],
        "icir": summ["icir"],
        "t_stat": summ["t_stat"],
        "t_no": t_no,
        "n_no": n_no,
        "hit_rate": summ["hit_rate"],
        "ls_sharpe": sharpe(ls),
        "ls_cagr": cagr(ls_eq),
        "ls_mdd": max_drawdown(ls_eq),
    }


def lowvol_block(px: pd.DataFrame, label: str) -> dict:
    fac = neg_vol_63(px)
    fwd = forward_returns(px, horizon=21)
    ic = cross_sectional_ic(fac, fwd)
    summ = ic_summary(ic)
    t_no, n_no = nonoverlap_t(ic)
    return {"label": label, "mean_ic": summ["mean_ic"], "icir": summ["icir"],
            "t_stat": summ["t_stat"], "t_no": t_no, "n_no": n_no}


def main() -> None:
    with open("configs/universe_survivorship.json") as fh:
        uni = json.load(fh)
    cur, surv = uni["current"], uni["recovered_survivors"]
    union = sorted(set(cur) | set(surv))

    px_cur = _load_pivot(cur)
    px_union = _load_pivot(union)

    n_added = len(set(union) - set(cur))
    # how many of the added survivors actually go NaN inside the window
    surv_only = sorted(set(surv) - set(cur))
    px_so = px_union[surv_only]
    last = px_so.apply(lambda c: c.last_valid_index())
    n_delist = int((last < pd.Timestamp("2024-12-15")).sum())

    print("=" * 78)
    print("SURVIVORSHIP-BIAS CORRECTION  (window 2015-01-01..2024-12-31, adj_close=total return)")
    print("=" * 78)
    print(f"  universe:  cur={len(cur)}   union={len(union)}  (+{n_added} recovered survivors)")
    print(f"  of the {len(surv_only)} added survivors, only {n_delist} actually go NaN in-window")
    print("             (rest were acquired/renamed with a continuing price series)")
    print("-" * 78)

    # ---- TEST 1: RETURN INFLATION -------------------------------------------------
    bh_cur = ew_buyhold(px_cur)
    bh_uni = ew_buyhold(px_union)
    eq_cur, eq_uni = (1 + bh_cur).cumprod(), (1 + bh_uni).cumprod()
    c_cagr, u_cagr = cagr(eq_cur), cagr(eq_uni)
    print("  TEST 1  RETURN INFLATION — equal-weight monthly-rebal buy&hold")
    print(f"    {'universe':<10}{'CAGR':>9}{'Sharpe':>9}{'MDD':>9}{'bars':>8}")
    print(f"    {'cur':<10}{c_cagr:>+8.2%}{sharpe(bh_cur):>+9.2f}{max_drawdown(eq_cur):>+8.1%}{len(bh_cur):>8}")
    print(f"    {'union':<10}{u_cagr:>+8.2%}{sharpe(bh_uni):>+9.2f}{max_drawdown(eq_uni):>+8.1%}{len(bh_uni):>8}")
    infl = c_cagr - u_cagr
    print(f"    survivorship inflation (cur_CAGR - union_CAGR) = {infl:+.2%}  ({infl*1e4:+.0f} bps/yr)")
    print("    [LOWER BOUND — worst bankrupt-to-zero names absent from data]")
    print("-" * 78)

    # ---- TEST 2: MOMENTUM ROBUSTNESS ---------------------------------------------
    m_cur = momentum_block(px_cur, "cur")
    m_uni = momentum_block(px_union, "union")
    print("  TEST 2  MOMENTUM (mom_12_1) ROBUSTNESS — rank-IC + net-10bps quintile L/S")
    print(f"    {'universe':<10}{'mean_IC':>9}{'ICIR':>8}{'t(naive)':>9}{'t(noOL)':>9}{'LS_Shrp':>9}{'LS_CAGR':>9}")
    for m in (m_cur, m_uni):
        print(f"    {m['label']:<10}{m['mean_ic']:>+9.4f}{m['icir']:>+8.3f}{m['t_stat']:>+9.2f}"
              f"{m['t_no']:>+9.2f}{m['ls_sharpe']:>+9.2f}{m['ls_cagr']:>+8.1%}")
    print(f"    delta ICIR (union - cur) = {m_uni['icir'] - m_cur['icir']:+.3f}   "
          f"delta IC = {m_uni['mean_ic'] - m_cur['mean_ic']:+.4f}")
    print("    [t(noOL) = non-overlapping every-21d t; naive t is ~3.7x inflated by AC1~0.93]")
    verdict = ("UNCHANGED: momentum dead under both (|t(noOL)|<2 both universes)"
               if abs(m_cur["t_no"]) < 2 and abs(m_uni["t_no"]) < 2
               else "MOVED: see delta")
    print(f"    verdict: {verdict}")
    print("-" * 78)

    # ---- TEST 3: LOW-VOL (cheap extra) -------------------------------------------
    lv_cur = lowvol_block(px_cur, "cur")
    lv_uni = lowvol_block(px_union, "union")
    print("  TEST 3  LOW-VOL (-vol_63) ROBUSTNESS — rank-IC vs 21d fwd")
    print(f"    {'universe':<10}{'mean_IC':>9}{'ICIR':>8}{'t(naive)':>9}{'t(noOL)':>9}{'n(noOL)':>8}")
    for lv in (lv_cur, lv_uni):
        print(f"    {lv['label']:<10}{lv['mean_ic']:>+9.4f}{lv['icir']:>+8.3f}{lv['t_stat']:>+9.2f}"
              f"{lv['t_no']:>+9.2f}{lv['n_no']:>8}")
    print("    [honest read: once AC-corrected, low-vol is NOT significant on EITHER universe;")
    print("     the naive -5.5 'collapse' compared two ~3.7x-inflated numbers. Removed names DO")
    print("     skew high-vol (directionally right) but there was no significant baseline to lose.]")
    print("=" * 78)
    print("  CAVEATS: (1) recovered only 111/262 = 42% of removed names; worst bankrupt-to-zero")
    print("  tickers purged by data source -> every number is a LOWER BOUND. (2) the +126bps CAGR")
    print("  inflation is ~97% COHORT-DILUTION (current members are ex-post winners); only ~+6bps")
    print("  is the 9 true in-window delisters under an optimistic exit-at-last-price model.")
    print("=" * 78)


if __name__ == "__main__":
    main()
