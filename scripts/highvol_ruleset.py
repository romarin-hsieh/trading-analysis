"""Purpose-built ruleset for a MECHANICAL, point-in-time, survivorship-aware HIGH-VOL cohort.

Goal: avoid the two biases that invalidated the user's hand-picked list:
  (1) HINDSIGHT SELECTION -> universe is defined MECHANICALLY & PIT (top-30% trailing vol, monthly).
  (2) SURVIVORSHIP       -> use the 610-name survivorship-AWARE set (blown-up / delisted included;
                            survivors go NaN after delist and are NOT carried forward).

Then test a purpose-built ruleset (R1) vs the OLD failed rulebook (R0), ablations (R2-R4),
and an INVESTABLE benchmark (equal-wt buy&hold of the SAME cohort, + VOO). Honest reporting:
CAGR / Sharpe / MDD / Calmar / sub-period Sharpe / PSR-vs-0 / annualized turnover, plus a thin
2025 OOS slice with a coverage caveat, and a deflation note for the ~5 variants tried.

ASCII-only prints (cp950 console).
"""

from __future__ import annotations

from loguru import logger

logger.remove()

import json  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from trading_analysis.backtest.deflated_sharpe import (  # noqa: E402
    expected_max_sharpe,
    probabilistic_sharpe_ratio,
)
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

REBAL = 21  # monthly
COST_BPS = 10.0  # net 10bps per leg on turnover
VOL_LOOKBACK = 126
MIN_HISTORY = 200
PRICE_FLOOR = 5.0
TOP_VOL_PCT = 0.30  # high-vol cohort = top 30% trailing vol
VOL_TARGET = 0.25  # 25%/yr book vol target (no leverage)
TD = 252


# ----------------------------- data / signals -----------------------------


def calmar(eq: pd.Series, c: float) -> float:
    mdd = max_drawdown(eq)
    return float(c / abs(mdd)) if mdd < 0 else 0.0


def build(px: pd.DataFrame):
    """Return ret, lagged trailing vol, lagged price, 6m-skip-1m momentum, 126d-low flag."""
    ret = px.pct_change(fill_method=None)
    logpx = np.log(px)
    vol = ret.rolling(VOL_LOOKBACK).std() * np.sqrt(TD)
    vol_lag = vol.shift(1)
    px_lag = px.shift(1)
    n_hist = px.notna().cumsum()
    enough_hist = (n_hist >= MIN_HISTORY).shift(1)
    # 6m-skip-1m momentum, lagged
    mom = (logpx.shift(21) - logpx.shift(126)).shift(1)
    # death spiral flag: yesterday's price below its own trailing 126d low (lagged)
    low126 = px.rolling(126).min()
    below_low = (px < low126.shift(1)).shift(1)
    return ret, vol_lag, px_lag, enough_hist, mom, below_low


def cohort_mask(px_lag, vol_lag, enough_hist, day):
    """Eligible & high-vol membership on a rebalance day (all inputs already lagged)."""
    elig = enough_hist.loc[day] & (px_lag.loc[day] > PRICE_FLOOR) & vol_lag.loc[day].notna()
    elig_names = elig.index[elig.fillna(False)]
    if len(elig_names) < 10:
        return elig_names, pd.Index([])
    v = vol_lag.loc[day, elig_names].dropna()
    if len(v) < 10:
        return elig_names, pd.Index([])
    thresh = v.quantile(1.0 - TOP_VOL_PCT)
    cohort = v.index[v >= thresh]
    return elig_names, cohort


# ----------------------------- backtest engine -----------------------------


def run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_ma_gate,
                 *, universe="cohort", weight="inv_vol", k=20, vol_target=True,
                 sma_stop=False, cash_gate=False, death_cut=True):
    """Generic monthly engine. Returns (port_ret series, ann_turnover)."""
    idx = px.index
    rebals = list(range(MIN_HISTORY, len(idx), REBAL))
    # inverse trailing-vol weight uses lagged vol; daily SMA50 for the old stop
    sma50 = px.rolling(50).mean()

    port_ret = pd.Series(0.0, index=idx)
    book_scale = 1.0
    turnover_sum = 0.0
    n_rebals = 0
    prev_weights = pd.Series(dtype=float)

    # rolling realized port vol for vol-target (computed from realized port_ret)
    for bi, start_i in enumerate(rebals):
        day = idx[start_i]
        end_i = rebals[bi + 1] if bi + 1 < len(rebals) else len(idx)

        # ---- selection on `day` (all signals lagged) ----
        if universe == "cohort":
            _, pool = cohort_mask(px_lag, vol_lag, enough_hist, day)
        else:  # whole 610 universe, same eligibility (price>5, history) but no vol screen
            elig = enough_hist.loc[day] & (px_lag.loc[day] > PRICE_FLOOR) & vol_lag.loc[day].notna()
            pool = elig.index[elig.fillna(False)]

        if cash_gate and spy_ma_gate is not None and not bool(spy_ma_gate.get(day, False)):
            pool = pd.Index([])  # risk-off -> cash

        if len(pool) > 0:
            m = mom.loc[day, pool].dropna()
            picks = m.sort_values(ascending=False).head(k).index
        else:
            picks = pd.Index([])

        # ---- weights ----
        if len(picks) == 0:
            w = pd.Series(dtype=float)
        elif weight == "inv_vol":
            iv = 1.0 / vol_lag.loc[day, picks].replace(0, np.nan)
            iv = iv.dropna()
            w = iv / iv.sum() if iv.sum() > 0 else pd.Series(1.0 / len(picks), index=picks)
        else:  # equal weight
            w = pd.Series(1.0 / len(picks), index=picks)

        # ---- vol-target book scaling (no leverage): use realized port vol to date ----
        if vol_target and start_i > MIN_HISTORY + 60:
            recent = port_ret.iloc[max(0, start_i - 60):start_i]
            rv = recent.std() * np.sqrt(TD)
            book_scale = float(min(1.0, VOL_TARGET / rv)) if rv > 0 else 1.0
        elif not vol_target:
            book_scale = 1.0

        # ---- turnover (vs previous applied weights, scaled) ----
        applied = w * book_scale
        all_names = prev_weights.index.union(applied.index)
        pw = prev_weights.reindex(all_names).fillna(0.0)
        aw = applied.reindex(all_names).fillna(0.0)
        turnover = float((aw - pw).abs().sum())
        turnover_sum += turnover
        n_rebals += 1

        cost = turnover * COST_BPS / 1e4

        # ---- hold for the period, day by day, applying daily stop if enabled ----
        active = applied.copy()
        for di in range(start_i, end_i):
            d = idx[di]
            if len(active) == 0:
                # cash; first day still pays the rebalance cost
                if di == start_i:
                    port_ret.iloc[di] -= cost
                continue
            r = ret.loc[d, active.index].fillna(0.0)
            day_ret = float((active * r).sum())
            if di == start_i:
                day_ret -= cost
            port_ret.iloc[di] = day_ret
            # drift weights
            active = active * (1.0 + r)

            # daily SMA50 stop (old rulebook): drop names that closed below their 50-SMA
            if sma_stop:
                below = px.loc[d, active.index] < sma50.loc[d, active.index]
                stop_names = active.index[below.fillna(False)]
                if len(stop_names) > 0:
                    active = active.drop(stop_names)
            # wide death-spiral cut (monthly-style but checked daily, very wide)
            if death_cut:
                dn = [s for s in active.index if s in below_low.columns and bool(below_low.loc[d, s])]
                if dn:
                    active = active.drop(dn)

        prev_weights = applied

    ann_turnover = (turnover_sum / n_rebals) * (TD / REBAL) if n_rebals else 0.0
    return port_ret, ann_turnover


def buyhold_cohort(px, ret, vol_lag, px_lag, enough_hist):
    """Equal-wt buy&hold of the high-vol cohort, re-formed monthly (the fair bar)."""
    idx = px.index
    rebals = list(range(MIN_HISTORY, len(idx), REBAL))
    port_ret = pd.Series(0.0, index=idx)
    prev = pd.Series(dtype=float)
    tsum = 0.0
    nr = 0
    for bi, start_i in enumerate(rebals):
        day = idx[start_i]
        end_i = rebals[bi + 1] if bi + 1 < len(rebals) else len(idx)
        _, cohort = cohort_mask(px_lag, vol_lag, enough_hist, day)
        if len(cohort) == 0:
            continue
        w = pd.Series(1.0 / len(cohort), index=cohort)
        names = prev.index.union(w.index)
        turnover = float((w.reindex(names).fillna(0) - prev.reindex(names).fillna(0)).abs().sum())
        tsum += turnover
        nr += 1
        cost = turnover * COST_BPS / 1e4
        active = w.copy()
        for di in range(start_i, end_i):
            d = idx[di]
            r = ret.loc[d, active.index].fillna(0.0)
            dr = float((active * r).sum())
            if di == start_i:
                dr -= cost
            port_ret.iloc[di] = dr
            active = active * (1.0 + r)
        prev = w
    ann_turnover = (tsum / nr) * (TD / REBAL) if nr else 0.0
    return port_ret, ann_turnover


# ----------------------------- reporting -----------------------------


def stats(port_ret: pd.Series, label: str, turnover: float, sl: slice | None = None):
    r = port_ret if sl is None else port_ret.loc[sl]
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return None
    eq = (1.0 + r).cumprod()
    c = cagr(eq)
    sh = sharpe(r)
    mdd = max_drawdown(eq)
    cal = calmar(eq, c)
    psr = probabilistic_sharpe_ratio(r.values, 0.0)
    # sub-period sharpes
    sh1 = sharpe(r.loc["2016-01-01":"2019-12-31"].dropna()) if sl is None else np.nan
    sh2 = sharpe(r.loc["2020-01-01":"2024-12-31"].dropna()) if sl is None else np.nan
    return dict(name=label, cagr=c, sharpe=sh, mdd=mdd, calmar=cal,
               sh1=sh1, sh2=sh2, psr=psr, turnover=turnover)


def fmt(d):
    return (f"{d['name']:<30} CAGR {d['cagr']*100:6.1f}%  Sh {d['sharpe']:5.2f}  "
            f"MDD {d['mdd']*100:6.1f}%  Cal {d['calmar']:4.2f}  "
            f"Sh16-19 {d['sh1']:5.2f}  Sh20-24 {d['sh2']:5.2f}  "
            f"PSR {d['psr']:4.2f}  Turn {d['turnover']*100:5.0f}%")


def main():
    s = DuckStore("./data")
    with open("configs/universe_survivorship.json") as fh:
        uni = json.load(fh)
    SA = uni["current"] + uni["recovered_survivors"]
    px_all = s.load_close_pivot(SA, column="adj_close")

    # primary window 2015-2024 (full data); 2025 thin OOS handled separately
    px = px_all.loc["2014-06-01":"2024-12-31"].copy()  # extra lead-in for 126d vol/mom
    ret, vol_lag, px_lag, enough_hist, mom, below_low = build(px)

    # SPY 200-SMA cash gate (for R0): is yesterday's SPY > its 200-SMA?
    spy = s.load_close_pivot(["SPY"], column="adj_close")["SPY"].reindex(px.index).ffill()
    spy_ok = (spy > spy.rolling(200).mean()).shift(1)
    spy_gate = {d: bool(spy_ok.get(d, False)) for d in px.index}

    voo = s.load_close_pivot(["VOO"], column="adj_close")["VOO"].reindex(px.index)
    voo_ret = voo.pct_change(fill_method=None)

    print("=" * 110)
    print("MECHANICAL PIT HIGH-VOL COHORT (top 30% trailing 126d vol, monthly) on 610 survivorship-aware names")
    print("Primary validation window 2015-2024 | net 10bps/leg | benchmarks: cohort buy&hold + VOO")
    print("=" * 110)

    # diagnostic: typical cohort size
    sizes = []
    for start_i in range(MIN_HISTORY, len(px.index), REBAL):
        _, ch = cohort_mask(px_lag, vol_lag, enough_hist, px.index[start_i])
        sizes.append(len(ch))
    print(f"cohort size: median {int(np.median(sizes))}, min {min(sizes)}, max {max(sizes)} per month")
    print("-" * 110)

    results = {}

    # R0 old rulebook on the cohort
    r0, t0 = run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                          universe="cohort", weight="equal", k=10, vol_target=False,
                          sma_stop=True, cash_gate=True, death_cut=False)
    results["R0_old_rulebook"] = (r0, t0)

    # R1 purpose-built full
    r1, t1 = run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                          universe="cohort", weight="inv_vol", k=20, vol_target=True,
                          sma_stop=False, cash_gate=False, death_cut=True)
    results["R1_purpose_built"] = (r1, t1)

    # R2 R1 minus vol-target
    r2, t2 = run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                          universe="cohort", weight="inv_vol", k=20, vol_target=False,
                          sma_stop=False, cash_gate=False, death_cut=True)
    results["R2_minus_voltarget"] = (r2, t2)

    # R3 R1 minus inverse-vol (equal weight)
    r3, t3 = run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                          universe="cohort", weight="equal", k=20, vol_target=True,
                          sma_stop=False, cash_gate=False, death_cut=True)
    results["R3_minus_invvol"] = (r3, t3)

    # R4 R1 minus cohort screen (whole 610 universe)
    r4, t4 = run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                          universe="all", weight="inv_vol", k=20, vol_target=True,
                          sma_stop=False, cash_gate=False, death_cut=True)
    results["R4_minus_cohortscreen"] = (r4, t4)

    # BENCH cohort buy&hold
    bh, tbh = buyhold_cohort(px, ret, vol_lag, px_lag, enough_hist)
    results["BENCH_cohort_buyhold"] = (bh, tbh)

    # VOO
    results["VOO"] = (voo_ret.fillna(0.0), 0.0)

    print("\n2015-2024 PRIMARY:")
    out_rows = {}
    for name, (rr, tt) in results.items():
        d = stats(rr, name, tt)
        if d:
            out_rows[name] = d
            print(fmt(d))

    # ----- 2025 thin OOS -----
    print("-" * 110)
    px25 = px_all.loc["2024-06-01":"2026-12-31"].copy()
    ret25, vlag25, pxlag25, eh25, mom25, bl25 = build(px25)
    spy25 = s.load_close_pivot(["SPY"], column="adj_close")["SPY"].reindex(px25.index).ffill()
    spyok25 = (spy25 > spy25.rolling(200).mean()).shift(1)
    sg25 = {d: bool(spyok25.get(d, False)) for d in px25.index}
    voo25 = s.load_close_pivot(["VOO"], column="adj_close")["VOO"].reindex(px25.index).pct_change(fill_method=None)

    cov_names = (px_all.loc["2025-01-01":].notna().sum() >= 20).sum()
    print(f"2025 OOS COVERAGE CAVEAT: only {int(cov_names)}/610 names have >=20 obs in 2025 "
          f"(combo/custom batches only). Thin slice -- directional, not conclusive.")

    r1_25, t1_25 = run_backtest(px25, ret25, vlag25, pxlag25, eh25, mom25, bl25, sg25,
                                universe="cohort", weight="inv_vol", k=20, vol_target=True,
                                sma_stop=False, cash_gate=False, death_cut=True)
    bh_25, _ = buyhold_cohort(px25, ret25, vlag25, pxlag25, eh25)
    sl25 = slice("2025-01-01", "2025-12-31")
    for nm, rr, tt in [("R1_2025", r1_25, t1_25), ("BENCH_2025", bh_25, 0.0), ("VOO_2025", voo25, 0.0)]:
        d = stats(rr, nm, tt, sl=sl25)
        if d:
            print(f"{d['name']:<18} CAGR {d['cagr']*100:6.1f}%  Sh {d['sharpe']:5.2f}  "
                  f"MDD {d['mdd']*100:6.1f}%  Cal {d['calmar']:4.2f}  PSR {d['psr']:4.2f}")

    # ----- deflation note -----
    print("-" * 110)
    n_trials = 5  # R0..R4
    r1d = stats(r1, "R1", t1)
    bhd = stats(bh, "BH", tbh)
    # per-period sharpe std across the 5 variants (rough cross-trial dispersion)
    pp_sharpes = []
    for nm in ["R0_old_rulebook", "R1_purpose_built", "R2_minus_voltarget",
               "R3_minus_invvol", "R4_minus_cohortscreen"]:
        rr = results[nm][0].dropna()
        pp = rr.mean() / rr.std() if rr.std() > 0 else 0.0
        pp_sharpes.append(pp)
    trials_std = float(np.std(pp_sharpes, ddof=1))
    emax = expected_max_sharpe(n_trials, trials_std)  # per-period
    r1_pp = r1.dropna().mean() / r1.dropna().std()
    dsr_r1 = probabilistic_sharpe_ratio(r1.dropna().values, sr_benchmark=emax)
    # PSR of R1 vs the cohort buy&hold (does it add value over the fair bar?)
    diff = (r1 - bh).dropna()
    psr_vs_bh = probabilistic_sharpe_ratio(diff.values, 0.0) if diff.std() > 0 else np.nan
    print(f"DEFLATION (N={n_trials} variants): trials_sharpe_std(per-period)={trials_std:.4f}  "
          f"E[max Sharpe]/period={emax:.4f}  R1 Sharpe/period={r1_pp:.4f}")
    print(f"  R1 DSR (PSR vs expected-max under {n_trials} trials) = {dsr_r1:.3f}  (>0.95 => survives)")
    print(f"  PSR of (R1 - cohort buyhold) daily diff vs 0 = {psr_vs_bh:.3f}  "
          f"(does R1 add value over the fair bar?)")

    # quick verdicts to stdout
    print("-" * 110)
    print("VERDICTS:")
    print(f"  R1 Sharpe {r1d['sharpe']:.2f} vs BENCH {bhd['sharpe']:.2f}  | "
          f"R1 Calmar {r1d['calmar']:.2f} vs BENCH {bhd['calmar']:.2f}")
    print(f"  R0 (old) Sharpe {out_rows['R0_old_rulebook']['sharpe']:.2f} -- gating/stop drag check")
    print("=" * 110)


if __name__ == "__main__":
    main()
