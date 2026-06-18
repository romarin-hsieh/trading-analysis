"""Core-business ("operating") fundamental factor panel — does anything EXTEND our one winner?

We have exactly one robust fundamental factor so far: gross_profitability (Novy-Marx,
ICIR +0.30). Everything else (roa/accruals/value/asset_growth/momentum/PEAD) is buried.
This script tests a panel of NEW core-OPERATING factors (operating margin level & trend,
quality momentum, cash-based profitability, top-line growth, a quality interaction) to see
whether any beats the bar.

The signal-isolating test is the MARKET-NEUTRAL quintile long-short, NOT long-only. A
long-only sleeve raising combo alpha-t is BETA not signal -- so for EACH factor we report:
  - mean_ic / icir / t_stat  (full sample, leak-free: factor shifted 1 bar, forward 21d)
  - icir on 2016-2019 and 2020-2024 separately (sub-period sign stability)
  - MARKET-NEUTRAL quintile L/S Sharpe, net 10bps/leg (top minus bottom quintile, EW, daily)
  - corr of that L/S return to vr.build_combo() risk-parity combo
  - alpha_t_with_ls       : Carhart alpha-t of the combo + L/S as a 6th risk-parity sleeve
  - alpha_t_zero_signal_control : same but + an equal-weight-ALL-names (zero-signal) sleeve
                                   -- the BETA baseline the L/S sleeve must BEAT to be real.
  VERDICT WIN iff  L/S Sharpe>0  AND  icir_2016_19 & icir_2020_24 SAME sign
                   AND  alpha_t_with_ls > alpha_t_zero_signal_control.

Run: uv run python scripts/core_business_factors.py
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import validate_recommendation as vr  # noqa: E402

from trading_analysis.data.connectors.edgar import point_in_time  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import (  # noqa: E402
    _fy,
    _zscore,
    gross_profitability,
)
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
)
from trading_analysis.portfolio import rebalance  # noqa: E402

HORIZON = 21
COST = 0.0010  # 10 bps per leg
SP_A = ("2016-01-01", "2019-12-31")
SP_B = ("2020-01-01", "2024-12-31")


def revenue(fund, dates, syms):
    """Core top-line: Revenues, coalesced with the newer ASC606 revenue tag."""
    rev = point_in_time(_fy(fund), "Revenues", dates, syms)
    rev606 = point_in_time(_fy(fund), "RevenueFromContractWithCustomerExcludingAssessedTax", dates, syms)
    return rev.where(rev.notna(), rev606)


def build_factors(fund, dates, syms):
    """All core-business factors as point-in-time wide frames (HIGHER = predicted-better)."""
    rev = revenue(fund, dates, syms)
    opinc = point_in_time(_fy(fund), "OperatingIncomeLoss", dates, syms)
    assets = point_in_time(fund, "Assets", dates, syms)
    cfo = point_in_time(_fy(fund), "NetCashProvidedByUsedInOperatingActivities", dates, syms)

    op_margin_level = opinc / rev.where(rev > 0)
    op_margin_trend = op_margin_level - op_margin_level.shift(252)
    gp_level = gross_profitability(fund, dates, syms)
    gp_trend = gp_level - gp_level.shift(252)
    cfo_profitability = cfo / assets
    revenue_growth = rev / rev.shift(252) - 1.0
    quality_improving = _zscore(gp_level) + _zscore(gp_trend)
    return {
        "op_margin_level": op_margin_level,
        "op_margin_trend": op_margin_trend,
        "gp_level": gp_level,
        "gp_trend": gp_trend,
        "cfo_profitability": cfo_profitability,
        "revenue_growth": revenue_growth,
        "quality_improving": quality_improving,
    }


def ls_daily_return(factor, daily_ret, q=5):
    """Market-neutral quintile long-short DAILY return, net `COST`/leg.

    Each date: rank names into q buckets by the (already 1-bar-shifted) factor, go EW long the
    top bucket and EW short the bottom bucket (dollar-neutral), held one day. Cost charged on the
    turnover of each leg's holdings day-over-day. Returns a daily L/S return series.
    """
    f = factor.reindex(daily_ret.index)
    cols = f.columns.intersection(daily_ret.columns)
    f, r = f[cols], daily_ret[cols]
    long_prev: pd.Series | None = None
    short_prev: pd.Series | None = None
    out: dict = {}
    for ts in f.index:
        fr = f.loc[ts].dropna()
        if len(fr) < q * 3:
            continue
        try:
            b = pd.qcut(fr.rank(method="first"), q, labels=False)
        except ValueError:
            continue
        longs = fr.index[b == q - 1]
        shorts = fr.index[b == 0]
        lw = pd.Series(1.0 / len(longs), index=longs)
        sw = pd.Series(1.0 / len(shorts), index=shorts)
        rr = r.loc[ts]
        gross = float(rr.reindex(longs).fillna(0).mean()) - float(rr.reindex(shorts).fillna(0).mean())
        # turnover cost on each leg (|w_t - w_{t-1}| summed, both legs)
        if long_prev is None:
            to = 2.0  # initial build of both legs
        else:
            to = float(lw.subtract(long_prev, fill_value=0).abs().sum()) + \
                 float(sw.subtract(short_prev, fill_value=0).abs().sum())
        out[ts] = gross - COST * to
        long_prev, short_prev = lw, sw
    return pd.Series(out, dtype=float).dropna()


def sharpe(r):
    r = pd.Series(r).dropna()
    s = r.std(ddof=1)
    return float(r.mean() / s * np.sqrt(252)) if s and s > 1e-12 else float("nan")


def alpha_t_with_sleeve(sleeves, extra):
    """Carhart alpha-t of the risk-parity combo when `extra` is added as another sleeve."""
    cols = [*list(sleeves.columns), "extra"]
    sl = sleeves.copy()
    sl["extra"] = extra.reindex(sl.index).fillna(0.0)
    sl = sl[cols].dropna()
    W = rebalance(sl, lookback=126, step=21, method="risk_parity")
    Wd = W.reindex(sl.index).ffill().shift(1).fillna(0.0)
    rp = (Wd * sl).sum(axis=1).iloc[126:]
    attr = vr.attribution(rp)
    return float(attr.get("alpha_tstat", float("nan")))


def main():
    store = DuckStore("./data")
    with open("configs/universe_survivorship.json") as fh:
        syms = json.load(fh)["current"]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    syms = [s for s in syms if s in px.columns]
    px = px[syms]
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    dates = px.index

    fwd = forward_returns(px, HORIZON)
    daily_ret = px.pct_change()
    factors = build_factors(fund, dates, syms)

    # combo sleeves to extend, and the zero-signal control (EW of all names, daily)
    rp_combo, _, sleeves = vr.build_combo()
    zero_signal = daily_ret.mean(axis=1)  # equal-weight-ALL-names: pure beta, no cross-sectional signal
    base_alpha_t = float(vr.attribution(rp_combo).get("alpha_tstat", float("nan")))
    ctrl_alpha_t = alpha_t_with_sleeve(sleeves, zero_signal)

    print("=" * 118)
    print(f"CORE-BUSINESS FUNDAMENTAL FACTOR PANEL  --  {len(syms)} S&P500 names, 2015-2024, "
          f"leak-free (factor shift 1, fwd {HORIZON}d)")
    print(f"  combo base Carhart alpha-t = {base_alpha_t:+.2f}   |   "
          f"zero-signal (EW-all) control sleeve alpha-t = {ctrl_alpha_t:+.2f}  (the BETA baseline to beat)")
    print(f"  market-neutral quintile L/S, net {COST*1e4:.0f}bps/leg; net cost charged on daily turnover")
    print("=" * 118)
    hdr = (f"{'factor':18s} {'IC':>7s} {'ICIR':>6s} {'t':>6s} {'IR16-19':>8s} {'IR20-24':>8s} "
           f"{'LSshrp':>7s} {'corrCmb':>8s} {'a_t+LS':>7s} {'a_tCtrl':>8s}  verdict")
    print(hdr)
    print("-" * 118)

    rows = []
    for name, fac in factors.items():
        facs = fac.shift(1)  # leak-free: factor known 1 bar before the forward window
        ic = cross_sectional_ic(facs, fwd)
        if len(ic) < 100:
            print(f"{name:18s}  (insufficient IC obs: {len(ic)})")
            continue
        summ = ic_summary(ic)
        ic_a = ic[(ic.index >= SP_A[0]) & (ic.index <= SP_A[1])]
        ic_b = ic[(ic.index >= SP_B[0]) & (ic.index <= SP_B[1])]
        icir_a = float(ic_a.mean() / ic_a.std(ddof=1)) if len(ic_a) > 1 else float("nan")
        icir_b = float(ic_b.mean() / ic_b.std(ddof=1)) if len(ic_b) > 1 else float("nan")

        ls = ls_daily_return(facs, daily_ret)
        ls_sharpe = sharpe(ls)
        cmn = ls.index.intersection(rp_combo.index)
        corr = float(ls.reindex(cmn).corr(rp_combo.reindex(cmn))) if len(cmn) > 30 else float("nan")
        a_ls = alpha_t_with_sleeve(sleeves, ls)

        same_sign = (not np.isnan(icir_a) and not np.isnan(icir_b)
                     and np.sign(icir_a) == np.sign(icir_b))
        win = (ls_sharpe > 0) and same_sign and (a_ls > ctrl_alpha_t)
        if win:
            verdict = "WIN"
        elif (ls_sharpe > 0) or same_sign:
            verdict = "WEAK"
        else:
            verdict = "FAIL"

        print(f"{name:18s} {summ['mean_ic']:+7.3f} {summ['icir']:+6.2f} {summ['t_stat']:+6.2f} "
              f"{icir_a:+8.2f} {icir_b:+8.2f} {ls_sharpe:+7.2f} {corr:+8.2f} {a_ls:+7.2f} "
              f"{ctrl_alpha_t:+8.2f}  {verdict}")
        rows.append({
            "name": name, "mean_ic": summ["mean_ic"], "icir": summ["icir"], "t_stat": summ["t_stat"],
            "icir_2016_19": icir_a, "icir_2020_24": icir_b, "ls_sharpe": ls_sharpe, "corr": corr,
            "a_ls": a_ls, "verdict": verdict,
        })

    print("-" * 118)
    wins = [r["name"] for r in rows if r["verdict"] == "WIN"]
    print(f"  WIN = L/S Sharpe>0 AND both sub-period ICIRs same sign AND alpha_t_with_ls > "
          f"control({ctrl_alpha_t:+.2f}).")
    if wins:
        print(f"  GENUINE WINNERS: {wins}")
    else:
        print("  GENUINE WINNERS: NONE -- every core-business factor here is beta/noise, not a real "
              "cross-sectional signal that beats the zero-signal control. Honest negative result.")
    print("=" * 118)
    return rows, ctrl_alpha_t, base_alpha_t


if __name__ == "__main__":
    main()
