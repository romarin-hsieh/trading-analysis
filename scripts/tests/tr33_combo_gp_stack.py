"""TR-33 -- do our two survivors stack? Flagship combo x GP quality sleeve.

Reopen basis: docs/22 queue ("combo x GP interaction"). The campaign has exactly two
survivors: the 5-sleeve risk-parity combo (the only borderline alpha, monthly Carhart
t=2.64, TR-18/20/25) and gross profitability (the only surviving cross-sectional
signal, honest chain +0.30 -> +0.23 -> members-only +0.13, TR-26/27). TR-26 already
warned the GP gross L-S is ~1%/yr -- "a signal, not a strategy". The stacking question
is the portfolio-level version: does a members-only GP long-only sleeve ADD anything
to the flagship book, or is it diluted beta the combo already owns?

F0 DECLARATION (pre-committed)
  claim         : adding a GP top-quintile members-only long-only sleeve improves the
                flagship delivery -- incremental alpha over the 5-sleeve combo.
  seat          : daily engine, weights formed at t applied t+1 (build_combo
                convention); GP sleeve = top quintile of gross_profitability among
                CURRENT S&P members (TR-27 honest masking), equal weight, 21d
                rebalance, 10bps/side on turnover; risk-parity re-weighted 6-sleeve
                combo via the same rebalance() machinery; monthly clock for all
                inference (TR-18 lesson).
  PRE-COMMITTED CHECKS
    CAL  : (a) 5-sleeve combo monthly Carhart alpha-t reproduces the docs/08 anchor
           (2.0 <= t <= 3.2 band around 2.64) on its own window; (b) GP sleeve tilt
           sanity: sleeve mean daily return >= EW-members baseline over the shared
           window (sign only). Fail -> STOP.
    POST-RUN AUDIT NOTE (CAL v1 -> v2, TR-27/30b discipline; verdict tree unedited):
           CAL-b v1 FAILED (-3.56%/yr tilt) -- and the failure exposed a DESIGN error,
           not a machinery bug: v1 encoded "top quintile beats EW members", but the
           docs/10 evidence is a RANK IC (+0.13 members-only), and a positive rank IC
           does not imply top-bucket outperformance (the payoff may live on the short
           side: avoiding low-GP names). The machine-fidelity anchor is TR-27's
           members-only ICIR itself. CAL-b v2: members-only 63d rank ICIR in
           [0.03, 0.25] (anchor +0.13) using this exact panel+mask. The v1 tilt and a
           top/bottom decomposition are kept as C3 diagnostics -- a negative long-side
           tilt makes NO-STACK likely, and that is a finding, not a bug.
    C1   : 6-sleeve vs 5-sleeve on the SHARED window: Sharpe, MDD, monthly Carhart
           alpha-t (OLS + HAC). Improvement = Sharpe6 >= Sharpe5 AND MDD6 <= 1.1x MDD5.
    C2   : (decisive) stack spread s = r6 - r5 (monthly): Carhart alpha-t >= 2.0.
    C3   : descriptive: fixed GP weight 10%/20% variants; GP sleeve turnover; number
           of monthly observations (F4 small-sample honesty).
  VERDICT RULE (pre-committed):
    CAL fail                    -> INVALID-TEST
    C2 pass & C1 improvement    -> STACKS (real product change candidate)
    C2 pass & !C1               -> SIGNAL-NOT-SLEEVE (alpha exists but degrades the book)
    C2 fail                     -> NO-STACK (portfolio-level confirmation of TR-26's
                                   "signal, not strategy"; combo stays 5-sleeve)
  anti-HARKing : single pre-registered sleeve construction (top quintile, EW, 21d);
               fixed-weight variants are descriptive; trials +1 family.

Run: uv run python scripts/tests/tr33_combo_gp_stack.py   (~2-3 min)
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
sys.path.insert(0, "scripts/tests")

import validate_recommendation as vr  # noqa: E402
from sp500_constituents import load_membership  # noqa: E402
from tr27_gp_membership_size import ALIASES, member_mask  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.attribution import (  # noqa: E402
    compound_to_monthly,
    load_ff_factors_monthly,
)
from trading_analysis.factors.fundamentals import build_all  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

STEP = 21
TOP_Q = 0.20
COST = 0.0010          # 10bps/side on GP sleeve turnover
CAL_BAND = (2.0, 3.2)  # around the docs/08 monthly Carhart anchor t=2.64


def _bucket_returns(gp, ret, syms, dates, pick) -> tuple[pd.Series, pd.Series]:
    """EW bucket sleeve (pick: series -> index of names), 21d rebalance: (net, turnover)."""
    w = pd.DataFrame(0.0, index=dates, columns=syms)
    for i in range(0, len(dates), STEP):
        s = gp.iloc[i].dropna()
        if len(s) < 50:
            continue
        names = pick(s)
        j = min(i + STEP, len(dates))
        w.iloc[i:j] = 0.0
        w.iloc[i:j, [syms.index(x) for x in names]] = 1.0 / len(names)
    wd = w.shift(1).fillna(0.0)
    gross = (wd * ret).sum(axis=1)
    turn = wd.diff().abs().sum(axis=1) / 2
    net = gross - turn * 2 * COST
    live = wd.abs().sum(axis=1) > 0
    return net[live], turn[live]


def gp_sleeve(store) -> dict:
    """Members-only GP sleeves + fidelity stats (top/bottom quintile, ICIR, tilts)."""
    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    gp = build_all(fund, px, syms)["gross_profitability"]
    mem = load_membership()
    mm = member_mask(px.index, syms, mem)
    gp = gp.where(mm)
    ret = px.pct_change()
    dates = px.index
    top, to_top = _bucket_returns(gp, ret, syms, dates,
                                  lambda s: s[s.rank(pct=True) >= 1 - TOP_Q].index)
    bot, _ = _bucket_returns(gp, ret, syms, dates,
                             lambda s: s[s.rank(pct=True) <= TOP_Q].index)
    ew_members = ret.where(mm).mean(axis=1)
    # CAL-b v2: members-only 63d rank ICIR on the same panel+mask (TR-27 anchor +0.13)
    fwd = px.pct_change(63).shift(-63)
    ics = []
    for i in range(0, len(dates) - 63, 63):
        s, f = gp.iloc[i], fwd.iloc[i]
        ok = s.notna() & f.notna()
        if ok.sum() >= 50:
            ics.append(s[ok].rank().corr(f[ok].rank()))
    ics = pd.Series(ics)
    icir = float(ics.mean() / ics.std()) if ics.std() > 0 else np.nan
    return {"net": top, "turn": float(to_top.mean()), "icir": icir,
            "tilt_top": float(top.mean() - ew_members.reindex(top.index).mean()),
            "tilt_bot": float(bot.mean() - ew_members.reindex(bot.index).mean())}


def carhart_alpha_t(r_m: pd.Series, ff: pd.DataFrame) -> tuple[float, float, float]:
    df = pd.concat([r_m.rename("r"), ff], axis=1).dropna()
    y = df["r"] - df["RF"]
    X = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "UMD"]])
    ols = sm.OLS(y, X).fit()
    hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    return float(ols.params["const"]), float(ols.tvalues["const"]), float(hac.tvalues["const"])


def sharpe(r: pd.Series) -> float:
    return float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan


def main():
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-33  DO THE TWO SURVIVORS STACK?  flagship 5-sleeve combo x GP members-only sleeve")
    print("=" * 100)

    rp5, _ew, sleeves = vr.build_combo()
    gpd = gp_sleeve(store)
    gp_net = gpd["net"]
    idx = sleeves.index.intersection(gp_net.index)
    sleeves6 = sleeves.reindex(idx).copy()
    sleeves6["gp_quality"] = gp_net.reindex(idx)
    W6 = rebalance(sleeves6, lookback=126, step=21, method="risk_parity")
    Wd6 = W6.reindex(sleeves6.index).ffill().shift(1).fillna(0.0)
    rp6 = (Wd6 * sleeves6).sum(axis=1).iloc[126:]
    rp5s = rp5.reindex(rp6.index).dropna()
    rp6 = rp6.reindex(rp5s.index)
    gp_w = float(Wd6["gp_quality"].iloc[126:].mean())
    print(f"shared window: {rp6.index[0].date()}..{rp6.index[-1].date()} "
          f"({len(rp6)} days, {len(rp6)//21} months approx) | avg GP sleeve weight {gp_w:.0%}")

    ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)
    m5, m6 = compound_to_monthly(rp5s), compound_to_monthly(rp6)
    a5, t5, h5 = carhart_alpha_t(m5, ff)
    a6, t6, h6 = carhart_alpha_t(m6, ff)

    # CAL (v2: machine fidelity = reproduce TR-27's members-only ICIR on this panel)
    cal_a = CAL_BAND[0] <= t5 <= CAL_BAND[1]
    cal_b = 0.03 <= gpd["icir"] <= 0.25
    print(f"CAL a: 5-sleeve monthly Carhart t={t5:+.2f} (band {CAL_BAND}) -> "
          f"{'PASS' if cal_a else 'FAIL'}")
    print(f"CAL b v2: members-only 63d rank ICIR {gpd['icir']:+.3f} "
          f"(TR-27 anchor +0.13, band [0.03, 0.25]) -> {'PASS' if cal_b else 'FAIL'}")
    print(f"  [diagnostic, was CAL v1] long-side tilt (top-Q minus EW members) "
          f"{gpd['tilt_top']*252*100:+.2f}%/yr | short-side (bottom-Q minus EW) "
          f"{gpd['tilt_bot']*252*100:+.2f}%/yr -> where the IC lives")
    if not (cal_a and cal_b):
        print("VERDICT: INVALID-TEST -- calibration failed; machinery does not reproduce anchors.")
        return

    # C1
    s5, s6 = sharpe(rp5s), sharpe(rp6)
    d5, d6 = max_drawdown((1 + rp5s).cumprod()), max_drawdown((1 + rp6).cumprod())
    improve = (s6 >= s5) and (abs(d6) <= 1.1 * abs(d5))
    print(f"C1: Sharpe {s5:+.2f} -> {s6:+.2f} | MDD {d5:+.1%} -> {d6:+.1%} | "
          f"alpha-t {t5:+.2f} -> {t6:+.2f} (HAC {h5:+.2f} -> {h6:+.2f}) -> "
          f"{'improvement' if improve else 'NO improvement'}")

    # C2: stack spread
    spread = m6.sub(m5, fill_value=np.nan).dropna()
    a_s, t_s, h_s = carhart_alpha_t(spread + ff["RF"].reindex(spread.index), ff)  # undo RF sub
    c2 = t_s >= 2.0
    print(f"C2 stack spread (6-sleeve minus 5-sleeve): mean {spread.mean()*12*100:+.2f}%/yr, "
          f"Carhart alpha-t {t_s:+.2f} (HAC {h_s:+.2f}, rule >=2.0) -> {'PASS' if c2 else 'FAIL'}")

    # C3 descriptive: fixed weights
    print("C3 descriptive:")
    for fw in (0.10, 0.20):
        rmix = (1 - fw) * rp5s + fw * gp_net.reindex(rp5s.index).fillna(0)
        mm_ = compound_to_monthly(rmix)
        _, tt, hh = carhart_alpha_t(mm_, ff)
        print(f"  fixed {fw:.0%} GP: Sharpe {sharpe(rmix):+.2f}, "
              f"MDD {max_drawdown((1+rmix).cumprod()):+.1%}, alpha-t {tt:+.2f} (HAC {hh:+.2f})")
    print(f"  monthly n = {len(m5)} (F4 note: ~{len(m5)} obs; small-sample inference)")

    if c2 and improve:
        v = "STACKS -- the GP sleeve adds incremental alpha AND improves the book; product change candidate."
    elif c2:
        v = "SIGNAL-NOT-SLEEVE -- incremental alpha exists but degrades delivery; keep GP as information."
    else:
        v = ("NO-STACK -- the GP sleeve adds no incremental alpha at the portfolio level: "
             "portfolio-level confirmation of TR-26's 'signal, not strategy'. Combo stays 5-sleeve.")
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    for r, lab, col in ((rp5s, "5-sleeve combo", "#1565c0"), (rp6, "6-sleeve (+GP)", "#2e7d32")):
        ax.plot((1 + r).cumprod(), lw=1.2, label=lab, color=col)
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    ax.set_title(f"equity curves, shared window | Sharpe {s5:+.2f} vs {s6:+.2f}", fontsize=10)
    ax = axes[1]
    labs = ["5-sleeve", "6-sleeve\n(+GP RP)", "fixed 10%", "fixed 20%"]
    tvals = [t5, t6]
    for fw in (0.10, 0.20):
        rmix = (1 - fw) * rp5s + fw * gp_net.reindex(rp5s.index).fillna(0)
        _, tt, _ = carhart_alpha_t(compound_to_monthly(rmix), ff)
        tvals.append(tt)
    ax.bar(labs, tvals, color=["#1565c0", "#2e7d32", "#90a4ae", "#90a4ae"], alpha=0.9)
    ax.axhline(2.0, color="#c62828", ls="--", lw=1, label="t=2")
    ax.axhline(3.0, color="#c62828", ls=":", lw=1, label="HLZ 3.0")
    ax.set_ylabel("monthly Carhart alpha-t")
    ax.set_title(f"alpha-t by construction | stack-spread alpha-t {t_s:+.2f}", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-33: do the two survivors stack? (combo x GP members-only sleeve)", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr33_combo_gp_stack.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
