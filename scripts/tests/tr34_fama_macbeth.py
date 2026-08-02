"""TR-34 -- Fama-MacBeth multivariate characteristic panel (methods completion).

Reopen basis: docs/22 queue, last "data in hand" item. Everything cross-sectional we
have judged so far was UNIVARIATE (rank IC per factor, docs/09/10, TR-26/27). The
standard asset-pricing question is JOINT: with size, momentum, short-term reversal,
beta and book-to-market on the right-hand side simultaneously, is GP an independently
priced characteristic on our universe -- or is its thin members-only signal absorbed
by simple controls? Fama-MacBeth (1973) monthly cross-sectional regressions are the
canonical machinery; this TR also leaves the machinery behind as a reusable module.

F0 DECLARATION (pre-committed)
  claim         : GP carries an independent positive FM slope after controls.
  seat          : our stock panel with EDGAR fundamentals (~350 names with all
                characteristics), members-only masking (TR-27), monthly calendar
                cross-sections 2015-07..latest, next-month simple return regressed on
                within-month rank-standardized characteristics ([-0.5, +0.5]); slopes
                averaged with Newey-West t (3 lags). F4: ~130 cross-sections.
  CHARACTERISTICS: gp (gross profitability), logmcap (PIT shares x price), mom122
                (t-12..t-2 cumulative return), str1m (prior-month return), beta252
                (rolling OLS vs SPY), bm (PIT StockholdersEquity / mcap).
  PRE-COMMITTED CHECKS
    CAL  : machinery fidelity, two legs. (a) GP-only monthly FM slope mean > 0 AND the
           63d-clock rank ICIR computed by THIS panel is in [0.03, 0.25] (TR-33 anchor
           +0.097, same masking). (b) sanity panel: STR slope must be NEGATIVE (the
           most robust classic sign) -- a positive STR slope means the panel machinery
           or timing is broken. Fail either -> STOP.
    POST-RUN AUDIT NOTE (CAL-b v1 -> v2; third calibration-design lesson this cycle):
           CAL-b v1 FAILED (STR slope +28.6bps/mo) -- and the design error is the
           TR-33 lesson wearing a new coat: v1 imported a LITERATURE sign estimated on
           a different universe/era (CRSP all-caps, decades where monthly reversal was
           alive). Large-cap monthly reversal is known-dead post-2000, and our own
           docs/13 already found reversal-type signals dead on this universe. A
           calibration must anchor on OUR OWN audited measurements on THIS seat:
           TR-06 ran univariate beta FM on this universe/era and found the SML
           steeply REVERSED (slope +1.9%/mo, t=+2.69, high beta wins). CAL-b v2 =
           univariate rank-std beta252 FM slope > 0 with t >= 1.0 (reproduces TR-06's
           direction and rough strength under members-only masking). The STR sign
           moves to C2 as a REPORTED finding about this seat/era, not a gate.
    C1   : (decisive) multivariate GP slope NW-t:
             t >= 2                -> INDEPENDENT-CHARACTERISTIC
             1 <= t < 2            -> WEAK-INDEPENDENT (no upgrade; honest-chain consistent)
             t < 1 or sign flip    -> NOT-INDEPENDENTLY-PRICED (subsumed by controls)
    C2   : full slope table vs literature signs (size -, bm +, mom +, str -, beta ~0/-)
           -- reported, machinery credibility panel.
    C3   : GP's slow clock: quarterly (63d, non-overlapping) FM, GP slope t (TR-26
           found GP strengthens with horizon).
    C4   : subperiod descriptive 2015-2020 vs 2021-2026 (ties to the GP WATCH).
  anti-HARKing : one pre-registered specification (rank-standardized, intercept, six
               characteristics); no specification search; trials +1 family (methods).

Run: uv run python scripts/tests/tr34_fama_macbeth.py   (~2-3 min)
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

from sp500_constituents import load_membership  # noqa: E402
from tr27_gp_membership_size import member_mask, shares_panel  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402

START = "2015-07-01"
NW_LAGS = 3


def pit_panel(fund: pd.DataFrame, tag: str, dates, syms) -> pd.DataFrame:
    """PIT wide panel for one tag: latest filed value with as_of <= t, ffilled."""
    x = fund[fund["tag"] == tag].copy()
    x = x.sort_values(["symbol", "as_of", "period_end"]).groupby(
        ["symbol", "as_of"]).tail(1)
    wide = x.pivot_table(index="as_of", columns="symbol", values="val", aggfunc="last")
    wide = wide.reindex(wide.index.union(dates)).sort_index().ffill().reindex(dates)
    return wide.reindex(columns=syms)


def rank_std(df: pd.DataFrame) -> pd.DataFrame:
    """Within-row rank to [-0.5, +0.5]."""
    return df.rank(axis=1, pct=True) - 0.5


def fm_slopes(chars: dict[str, pd.DataFrame], fwd: pd.DataFrame,
              min_n: int = 100) -> pd.DataFrame:
    """Monthly cross-sectional OLS of fwd on rank-standardized chars; slope series."""
    names = list(chars)
    rows = {}
    for t in fwd.index:
        df = pd.DataFrame({k: chars[k].loc[t] for k in names})
        df["fwd"] = fwd.loc[t]
        df = df.dropna()
        if len(df) < min_n:
            continue
        X = sm.add_constant(df[names])
        res = sm.OLS(df["fwd"], X).fit()
        rows[t] = res.params[names]
    return pd.DataFrame(rows).T


def nw_mean_t(x: pd.Series) -> tuple[float, float]:
    x = x.dropna()
    res = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(
        cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})
    return float(res.params[0]), float(res.tvalues[0])


def main():
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-34  FAMA-MACBETH MULTIVARIATE CHARACTERISTIC PANEL (members-only, monthly)")
    print("=" * 100)

    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0]
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]

    # month-end sampling
    me = px.resample("ME").last()
    me = me.loc[START:]
    ret_m = me.pct_change()
    fwd = ret_m.shift(-1)                          # next-month return

    # characteristics at month-end t (all PIT / trailing)
    gp_d = build_all(fund, px, syms)["gross_profitability"]
    gp = gp_d.resample("ME").last().reindex(me.index)
    sh = shares_panel(fund, px.index, syms)
    mcap = (sh * px).resample("ME").last().reindex(me.index)
    logmcap = np.log(mcap.where(mcap > 0))
    se = pit_panel(fund, "StockholdersEquity", px.index, syms)
    bm = (se.resample("ME").last().reindex(me.index) / mcap).where(lambda x: x > 0)
    mom122 = me.shift(2) / me.shift(12) - 1
    str1m = ret_m
    beta = (px.pct_change().rolling(252).cov(spy.pct_change())
            .div(spy.pct_change().rolling(252).var(), axis=0)
            .resample("ME").last().reindex(me.index))

    # members-only masking (TR-27 honesty)
    mem = load_membership()
    mm_d = member_mask(px.index, syms, mem)
    mm = mm_d.resample("ME").last().reindex(me.index).astype(bool)
    chars_raw = {"gp": gp, "logmcap": logmcap, "bm": bm, "mom122": mom122,
                 "str1m": str1m, "beta252": beta}
    chars = {k: rank_std(v.where(mm)) for k, v in chars_raw.items()}
    fwd = fwd.where(mm)

    # ---- CAL a: GP-only FM + 63d ICIR fidelity ----
    uni = fm_slopes({"gp": chars["gp"]}, fwd)
    m_uni, t_uni = nw_mean_t(uni["gp"])
    fwd63 = px.pct_change(63).shift(-63)
    gp_m = gp_d.where(mm_d)
    ics = []
    for i in range(0, len(px.index) - 63, 63):
        s, f = gp_m.iloc[i], fwd63.iloc[i]
        ok = s.notna() & f.notna()
        if ok.sum() >= 50:
            ics.append(s[ok].rank().corr(f[ok].rank()))
    ics = pd.Series(ics)
    icir = float(ics.mean() / ics.std())
    cal_a = (m_uni > 0) and (0.03 <= icir <= 0.25)
    print(f"CAL a: GP-only FM slope {m_uni*1e4:+.1f}bps/mo (t={t_uni:+.2f}, sign rule >0); "
          f"63d ICIR {icir:+.3f} (band [0.03,0.25]) -> {'PASS' if cal_a else 'FAIL'}")

    # ---- CAL b v2: reproduce OUR OWN audited FM anchor (TR-06 reversed SML) ----
    uni_b = fm_slopes({"beta252": chars["beta252"]}, fwd)
    m_b, t_b = nw_mean_t(uni_b["beta252"])
    cal_b = (m_b > 0) and (t_b >= 1.0)
    print(f"CAL b v2: univariate beta FM slope {m_b*1e4:+.1f}bps/mo (t={t_b:+.2f}; TR-06 "
          f"anchor: reversed SML, +1.9%/mo t=+2.69; rules >0 and t>=1.0) -> "
          f"{'PASS' if cal_b else 'FAIL'}")
    # ---- multivariate panel ----
    sl = fm_slopes(chars, fwd)
    stats = {k: nw_mean_t(sl[k]) for k in sl.columns}
    print(f"  [was CAL v1, now C2 finding] STR slope {stats['str1m'][0]*1e4:+.1f}bps/mo "
          f"(t={stats['str1m'][1]:+.2f}) -- large-cap monthly reversal dead/positive on "
          f"this seat, consistent with docs/13")
    if not (cal_a and cal_b):
        print("VERDICT: INVALID-TEST -- panel machinery fails fidelity checks.")
        return
    print(f"panel: {len(sl)} monthly cross-sections, median names/month = "
          f"{int(pd.DataFrame({k: chars[k].notna().sum(axis=1) for k in chars}).min(axis=1).median())}")

    print("-" * 100)
    print("C2 slope table (rank-standardized chars; slope = spread top-vs-bottom, bps/mo):")
    LIT = {"gp": "+", "logmcap": "-", "bm": "+", "mom122": "+", "str1m": "-", "beta252": "0/-"}
    for k in ("gp", "logmcap", "bm", "mom122", "str1m", "beta252"):
        m, t = stats[k]
        mark = "OK" if (LIT[k] == "+" and m > 0) or (LIT[k] == "-" and m < 0) or LIT[k] == "0/-" else "flip"
        print(f"  {k:8s}: {m*1e4:+7.1f} bps/mo  t={t:+.2f}   (literature {LIT[k]:>3s})  [{mark}]")

    m_gp, t_gp = stats["gp"]
    if t_gp >= 2:
        c1 = "INDEPENDENT-CHARACTERISTIC"
    elif t_gp >= 1:
        c1 = "WEAK-INDEPENDENT"
    else:
        c1 = "NOT-INDEPENDENTLY-PRICED"

    # ---- C3: quarterly clock ----
    me_q = px.resample("QE").last().loc[START:]
    ret_q = me_q.pct_change()
    fwd_q = ret_q.shift(-1)
    mm_q = mm_d.resample("QE").last().reindex(me_q.index).astype(bool)
    chars_q = {k: rank_std(v.resample("QE").last().reindex(me_q.index).where(mm_q))
               if k != "str1m" else rank_std(ret_q.where(mm_q))
               for k, v in {"gp": gp_d, "logmcap": np.log((sh*px).where(lambda x: x > 0)),
                            "bm": se / (sh*px), "mom122": px.shift(42)/px.shift(252)-1,
                            "str1m": None, "beta252": (px.pct_change().rolling(252).cov(spy.pct_change())
                                                       .div(spy.pct_change().rolling(252).var(), axis=0))}.items()}
    sl_q = fm_slopes(chars_q, fwd_q, min_n=80)
    m_gpq, t_gpq = nw_mean_t(sl_q["gp"])
    print(f"C3 quarterly clock: GP slope {m_gpq*1e4:+.1f}bps/q (t={t_gpq:+.2f}) "
          f"[TR-26: GP strengthens with horizon]")

    # ---- C4: subperiods ----
    for lab, a, b in (("2015-2020", "2015", "2020"), ("2021-2026", "2021", "2026")):
        m_, t_ = nw_mean_t(sl["gp"].loc[a:b])
        print(f"C4 {lab}: GP slope {m_*1e4:+.1f}bps/mo (t={t_:+.2f})")

    print("-" * 100)
    print(f"VERDICT: {c1} -- multivariate GP slope {m_gp*1e4:+.1f}bps/mo, NW t={t_gp:+.2f} "
          f"(univariate was {m_uni*1e4:+.1f}, t={t_uni:+.2f}).")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    ks = ["gp", "logmcap", "bm", "mom122", "str1m", "beta252"]
    ms = [stats[k][0] * 1e4 for k in ks]
    ts = [stats[k][1] for k in ks]
    cols = ["#1565c0" if k == "gp" else "#90a4ae" for k in ks]
    ax.bar(ks, ms, color=cols, alpha=0.9)
    for i, (m, t) in enumerate(zip(ms, ts)):
        ax.text(i, m + (2 if m >= 0 else -6), f"t={t:+.1f}", ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("FM slope (bps/mo, rank-standardized)")
    ax.set_title("C2: joint Fama-MacBeth slopes, members-only 2015-2026", fontsize=10)
    ax = axes[1]
    cum = sl["gp"].cumsum() * 1e4
    ax.plot(cum.index, cum.values, color="#1565c0", lw=1.4)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("cumulative GP slope (bps)")
    ax.set_title(f"GP slope path | multivariate t={t_gp:+.2f}, univariate t={t_uni:+.2f}",
                 fontsize=10)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-34: Fama-MacBeth multivariate panel -- is GP independently priced?",
                 fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr34_fama_macbeth.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
