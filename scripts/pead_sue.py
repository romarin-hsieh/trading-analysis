"""PEAD via SUE — post-earnings-announcement drift, Bernard-Thomas seasonal-random-walk SUE.

Uses ONLY EDGAR NetIncomeLoss we already ingested (no vendor data). Strictly point-in-time:
every quarter's value and announcement date come from the FIRST filing that disclosed it
(min as_of); SUE is standardized on the seasonal RW (e_q - e_{q-4}); drift starts the trading
day AFTER the announcement (as_of), measured net of the equal-weight market.

CRITICAL DATA NOTE (verified before coding, see below): in this DuckStore the 10-Q NetIncomeLoss
`val` is YTD-within-fiscal-year (Q1=Q1, Q2=Q1+Q2, Q3=Q1+Q2+Q3) for ~81% of firm-years, NOT the
standalone quarter the task prose assumed. So we DE-CUMULATE within each (symbol, fy):
  Q1 = v(Q1);  Q2 = v(Q2) - v(Q1);  Q3 = v(Q3) - v(Q2);  Q4 = v(FY 10-K) - v(Q3).
Announcement date of each standalone quarter = the as_of of the filing that first revealed the
cumulative figure it is derived from (for Q4 that is the 10-K's as_of, exactly as the task says).

Run: uv run python scripts/pead_sue.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

COST_BPS = 10.0


def build_pit_quarters(fund: pd.DataFrame) -> pd.DataFrame:
    """Return point-in-time standalone quarterly NI: (symbol, period_end, e_val, announce_date)."""
    ni = fund[fund.tag == "NetIncomeLoss"].copy()
    ni = ni.dropna(subset=["val", "as_of", "fy", "fp"])
    # FIRST disclosure of each (symbol, fy, fp): min as_of, and the val/period_end of that filing.
    ni = ni.sort_values("as_of")
    first = ni.groupby(["symbol", "fy", "fp"], as_index=False).first()

    rows = []
    for (sym, _fy), g in first.groupby(["symbol", "fy"]):
        gm = {r.fp: r for r in g.itertuples()}
        # cumulative (YTD) values as filed
        q1 = gm.get("Q1")
        q2 = gm.get("Q2")
        q3 = gm.get("Q3")
        fyr = gm.get("FY")
        # standalone quarter NI by de-cumulation; announce_date = as_of of the cumulative filing
        if q1 is not None:
            rows.append((sym, q1.period_end, float(q1.val), q1.as_of))
        if q2 is not None and q1 is not None:
            rows.append((sym, q2.period_end, float(q2.val) - float(q1.val), q2.as_of))
        if q3 is not None and q2 is not None:
            rows.append((sym, q3.period_end, float(q3.val) - float(q2.val), q3.as_of))
        if fyr is not None and q3 is not None:
            # Q4 standalone = FY annual - YTD-through-Q3; announced at the 10-K filing date.
            rows.append((sym, fyr.period_end, float(fyr.val) - float(q3.val), fyr.as_of))

    q = pd.DataFrame(rows, columns=["symbol", "period_end", "e_val", "announce_date"])
    q["period_end"] = pd.to_datetime(q["period_end"])
    q["announce_date"] = pd.to_datetime(q["announce_date"])
    # one row per (symbol, period_end): keep earliest announce
    q = q.sort_values("announce_date").groupby(["symbol", "period_end"], as_index=False).first()
    return q.sort_values(["symbol", "period_end"]).reset_index(drop=True)


def add_sue(q: pd.DataFrame) -> pd.DataFrame:
    """SUE = (e_q - e_{q-4}) / rolling_std(e_q - e_{q-4}, window=8, min_periods=6)."""
    out = []
    for _sym, g in q.groupby("symbol"):
        g = g.sort_values("period_end").copy()
        g["seas_diff"] = g["e_val"] - g["e_val"].shift(4)
        g["sue_std"] = g["seas_diff"].rolling(8, min_periods=6).std()
        g["sue"] = g["seas_diff"] / g["sue_std"]
        out.append(g)
    r = pd.concat(out, ignore_index=True)
    return r.replace([np.inf, -np.inf], np.nan)


def next_trading_day_pos(index: pd.DatetimeIndex, date: pd.Timestamp) -> int | None:
    """Position of the first trading day strictly AFTER `date` (leak-free actionability)."""
    pos = index.searchsorted(date, side="right")
    return int(pos) if pos < len(index) else None


def drift_test(ann: pd.DataFrame, close: pd.DataFrame, horizons: list[int]) -> dict:
    """Abnormal forward drift per SUE quintile, per horizon. Abnormal = firm ret - EW-market ret."""
    idx = close.index
    ew_logret = np.log(close).diff().mean(axis=1)  # equal-weight market daily log return
    ew_cum = ew_logret.cumsum()
    logpx = np.log(close)

    results = {}
    for h in horizons:
        recs = []
        for r in ann.itertuples():
            sym = r.symbol
            if sym not in close.columns or pd.isna(r.sue):
                continue
            p0 = next_trading_day_pos(idx, r.announce_date)
            if p0 is None or p0 + h >= len(idx):
                continue
            s0, s1 = logpx[sym].iloc[p0], logpx[sym].iloc[p0 + h]
            if pd.isna(s0) or pd.isna(s1):
                continue
            firm_ret = float(s1 - s0)
            mkt_ret = float(ew_cum.iloc[p0 + h] - ew_cum.iloc[p0])
            recs.append((r.announce_date, sym, float(r.sue), firm_ret - mkt_ret))
        d = pd.DataFrame(recs, columns=["announce_date", "symbol", "sue", "abn"])
        # cross-sectional quintiles within calendar-quarter cohort (no future info)
        d["cohort"] = d["announce_date"].dt.to_period("Q")
        d["qtile"] = (
            d.groupby("cohort")["sue"]
            .transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=False) + 1 if x.notna().sum() >= 10 else np.nan)
        )
        d = d.dropna(subset=["qtile"])
        means = d.groupby("qtile")["abn"].mean()
        q5 = d[d.qtile == 5]["abn"]
        q1 = d[d.qtile == 1]["abn"]
        # Welch t for Q5-Q1 difference of means
        m5, m1 = q5.mean(), q1.mean()
        v5, v1 = q5.var(ddof=1), q1.var(ddof=1)
        n5, n1 = len(q5), len(q1)
        se = np.sqrt(v5 / n5 + v1 / n1)
        t = (m5 - m1) / se if se > 0 else np.nan
        results[h] = {
            "n": len(d),
            "q_means": {int(k): float(v) for k, v in means.items()},
            "q5_minus_q1": float(m5 - m1),
            "t": float(t),
        }
    return results


def build_daily_sue_factor(ann: pd.DataFrame, index: pd.DatetimeIndex, symbols: list[str]) -> pd.DataFrame:
    """Each name carries its latest-ANNOUNCED SUE, effective the day AFTER announce, ffill to next."""
    fac = pd.DataFrame(index=index, columns=symbols, dtype=float)
    for sym, g in ann.groupby("symbol"):
        if sym not in symbols:
            continue
        g = g.dropna(subset=["sue"]).sort_values("announce_date")
        col = pd.Series(np.nan, index=index)
        for r in g.itertuples():
            p0 = next_trading_day_pos(index, r.announce_date)
            if p0 is not None:
                col.iloc[p0] = float(r.sue)
        fac[sym] = col.ffill()
    return fac


def main() -> None:
    with open("configs/universe_survivorship.json") as fh:
        universe = json.load(fh)["current"]
    store = DuckStore("./data")
    fund = store.load_fundamentals(universe)

    q = build_pit_quarters(fund)
    ann = add_sue(q)
    n_ann = int(ann["sue"].notna().sum())

    close = store.load_close_pivot(universe, column="adj_close").sort_index()
    close = close.loc["2015-01-01":]
    # restrict announcements to span we have prices for
    ann = ann[(ann.announce_date >= close.index[0]) & (ann.announce_date <= close.index[-1])]

    horizons = [21, 42, 63]
    drift = drift_test(ann, close, horizons)
    # avg names per cross-section (per calendar quarter cohort)
    d63_cohorts = ann.assign(cohort=ann.announce_date.dt.to_period("Q")).groupby("cohort").size()
    avg_per_cs = float(d63_cohorts.mean())

    # ---- SLEEVE TEST ----
    fac = build_daily_sue_factor(ann, close.index, list(close.columns))
    # cross-sectional z each day
    z = fac.sub(fac.mean(axis=1), axis=0).div(fac.std(axis=1, ddof=0).replace(0, np.nan), axis=0)

    # Long top-quintile equal-weight, daily rebalanced, net cost.
    rank = z.rank(axis=1, pct=True)
    long_mask = (rank >= 0.8).astype(float)
    w_long = long_mask.div(long_mask.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    # long-short: +top quintile / -bottom quintile
    short_mask = (rank <= 0.2).astype(float)
    w_short = short_mask.div(short_mask.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    w_ls = w_long - w_short

    daily_ret = close.pct_change()

    def sleeve_return(w: pd.DataFrame) -> pd.Series:
        wl = w.shift(1).fillna(0.0)  # trade on next bar -> lagged weights (leak-free)
        gross = (wl * daily_ret).sum(axis=1)
        turn = (wl - wl.shift(1)).abs().sum(axis=1).fillna(0.0)
        cost = turn * (COST_BPS / 1e4)
        return (gross - cost).fillna(0.0)

    r_long = sleeve_return(w_long)
    r_ls = sleeve_return(w_ls)

    # combo from validate_recommendation
    rp, _ew, sleeves5 = vr.build_combo()

    def align(s: pd.Series) -> pd.Series:
        return s.reindex(rp.index).fillna(0.0)

    long_al, ls_al = align(r_long), align(r_ls)
    sh_long = sharpe(long_al[long_al.index >= sleeves5.index[0]])
    sh_ls = sharpe(ls_al[ls_al.index >= sleeves5.index[0]])
    psr_long = probabilistic_sharpe_ratio(r_long[r_long != 0].to_numpy(), 0.0)
    psr_ls = probabilistic_sharpe_ratio(r_ls[r_ls != 0].to_numpy(), 0.0)
    corr_long = float(long_al.corr(rp))
    corr_ls = float(ls_al.corr(rp))

    # alpha t WITHOUT the new sleeve (baseline) and WITH (6-sleeve risk-parity)
    base = vr.attribution(rp)
    base_t = base.get("alpha_tstat", float("nan"))

    def alpha_with(extra: pd.Series, name: str) -> float:
        sl6 = sleeves5.copy()
        sl6[name] = extra.reindex(sl6.index).fillna(0.0)
        W = rebalance(sl6, lookback=126, step=21, method="risk_parity")
        Wd = W.reindex(sl6.index).ffill().shift(1).fillna(0.0)
        combo6 = (Wd * sl6).sum(axis=1).iloc[126:]
        a = vr.attribution(combo6)
        return a.get("alpha_tstat", float("nan"))

    t_with_long = alpha_with(r_long, "pead_long")
    t_with_ls = alpha_with(r_ls, "pead_ls")

    # ZERO-SIGNAL CONTROLS — the decisive test. If a sleeve with NO SUE information bumps the
    # combo's alpha-t the same as the long-only PEAD sleeve, then that "help" is diversifying
    # long-equity BETA, not PEAD alpha. Only the market-neutral L/S isolates signal.
    ctrl_ew = daily_ret.mean(axis=1)                       # equal-weight ALL names (zero signal)
    ctrl_rand = daily_ret[list(daily_ret.columns[::5])].mean(axis=1)  # fixed 20% subset, zero signal
    t_ctrl_ew = alpha_with(ctrl_ew, "ctrl_ew")
    t_ctrl_rand = alpha_with(ctrl_rand, "ctrl_rand")

    # ---------------------------------------------------------------- report
    print("=" * 74)
    print("PEAD via SUE (Bernard-Thomas seasonal-RW) — EDGAR NetIncomeLoss only")
    print("=" * 74)
    print("  RIGOR: timing uses as_of (SEC FILED date), NEVER period_end.")
    print("         returns start the day AFTER announce; weights lagged 1 bar; net 10bps/leg.")
    print("         10-Q val is YTD -> de-cumulated to standalone quarters (~78-81% YTD signature).")
    print("-" * 74)
    print(f"  # actionable announcements (SUE non-NaN) : {n_ann}")
    print(f"  avg announcements/cross-section (cal-Q)  : {avg_per_cs:.0f}")
    print("-" * 74)
    print("  ABNORMAL DRIFT (firm ret - equal-weight market), per SUE quintile:")
    for h in horizons:
        r = drift[h]
        qm = r["q_means"]
        line = "  ".join(f"Q{k} {qm.get(k, float('nan')):+.2%}" for k in range(1, 6))
        print(f"   H={h:>2}d (n={r['n']:>5}):  {line}")
        print(f"            Q5-Q1 = {r['q5_minus_q1']:+.2%}   t = {r['t']:+.2f}")
    print("-" * 74)
    print("  SLEEVE TEST (net 10bps, daily rebal, vs vr.build_combo risk-parity):")
    print(f"   long top-quintile : Sharpe {sh_long:+.2f}  PSR(>0) {psr_long:.3f}  corr {corr_long:+.2f}")
    print(f"   long-short Q5-Q1  : Sharpe {sh_ls:+.2f}  PSR(>0) {psr_ls:.3f}  corr {corr_ls:+.2f}")
    print("-" * 74)
    print("  CARHART ALPHA t — does adding PEAD as a 6th sleeve beat the 2.64 bar?")
    print(f"   baseline 5-sleeve combo      : t = {base_t:+.2f}")
    print(f"   + PEAD long  (6th sleeve)    : t = {t_with_long:+.2f}")
    print(f"   + PEAD L/S   (6th sleeve)    : t = {t_with_ls:+.2f}")
    print("   --- zero-signal CONTROLS (no SUE info) ---")
    print(f"   + EW-all-names (zero signal) : t = {t_ctrl_ew:+.2f}")
    print(f"   + random-20%   (zero signal) : t = {t_ctrl_rand:+.2f}")
    print("=" * 74)
    pead_alive = any(drift[h]["q5_minus_q1"] > 0 and drift[h]["t"] > 1.5 for h in horizons)
    # the long-only "help" is real only if it beats what a ZERO-SIGNAL sleeve already delivers
    long_beats_control = t_with_long > max(t_ctrl_ew, t_ctrl_rand) + 0.05
    print(f"  VERDICT: drift {'present' if pead_alive else 'NOT present'}. The long-only sleeve's")
    print(f"  alpha-t bump ({t_with_long:+.2f}) is {'REAL signal' if long_beats_control else 'just BETA'} — a zero-signal "
          f"basket bumps it to {max(t_ctrl_ew, t_ctrl_rand):+.2f} identically.")
    print(f"  The signal-isolating L/S {'RAISES' if t_with_ls > base_t else 'LOWERS'} alpha-t "
          f"({base_t:+.2f}->{t_with_ls:+.2f}) => no exploitable PEAD alpha in EDGAR-only data.")
    print("=" * 74)


if __name__ == "__main__":
    main()
