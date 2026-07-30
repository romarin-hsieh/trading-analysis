# -*- coding: utf-8 -*-
"""TR-47 -- De Bondt-Thaler 1985 long-term reversal (docs/27 paper queue #1).

The oldest behavioral anomaly: 3-5yr LOSERS beat WINNERS (overreaction). Modern
convention (KF): prior return t-60..t-13. Literature arc honestly stated up front:
the premium lived in 1926-1982 (DBT sample), shrank after publication, and much of
it loads on value (Fama-French absorb it with HML) and on small caps. Prior for OUR
seat (S&P 500 members 2015+): dead/zero, possibly value-absorbed.

F0 DECLARATION (pre-committed; single spec, no grid; trials +1 family)
  Char : ltrev = cumulative return t-60..t-13 (me.shift(13)/me.shift(60)-1),
         KF convention so the long-history leg anchors the same construction.
         Prior sign: NEGATIVE FM slope (losers win) in the classic era.
  Seat : S&P 500 members-only, monthly 2015-07+, TR-34 machinery verbatim
         (rank_std, fm_slopes min_n=100, NW 3 lags), fwd = next-month member-
         masked return. Price store depth 1990+ covers the 60m formation.
  CAL (fail any -> STOP):
    a) construction sanity on OUR panel: cross-sectional Spearman corr(ltrev
       ranks, mom122 ranks) averaged over months is POSITIVE (both are past-
       return measures over overlapping horizons at |corr| < 0.9 (not the same
       char); and corr(ltrev, bm) is NEGATIVE (LT losers are value stocks --
       the documented HML overlap, sign only).
    b) long-history leg reads the classic effect: on the KF 6 size x prior(60,13)
       portfolios, the small-stock Low-minus-High prior spread over 1931-1982
       (the DBT-era sample) has mean > 0 with t >= 2 (machinery reproduces the
       textbook premium where it lived).
  C1 : (decisive, our seat) univariate FM slope of ltrev:
         t <= -2           -> REVERSAL-CANDIDATE (proceeds to cost gate logic)
         -2 < t < +2       -> NO-SIGNAL on this seat
         t >= +2           -> CONTINUATION (anti-DBT; report as-is)
  C2 : joint with the TR-34 six characteristics -- the Fama-French absorption
       readout (does bm's presence kill any ltrev slope?).
  C3 : KF era table, small & big legs: 1931-1982 (DBT era), 1983-2000 (post-
       publication), 2001-2014, 2015+ -- the McLean-Pontiff decay arc for THIS
       anomaly, reported.
  C4 : subperiod on our seat 2015-2020 vs 2021+ (F7).
  Honest bounds: large-cap members panel = the habitat where DBT was always
  weakest (their effect concentrated in small losers); one spec; no cost gate
  unless C1 fires (nothing to cost).
Run: uv run python scripts/tests/tr47_longterm_reversal.py
Chart: docs/tests/img/tr47_longterm_reversal.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
sys.path.insert(0, "scripts/tests")

from sp500_constituents import load_membership  # noqa: E402
from tr27_gp_membership_size import member_mask, shares_panel  # noqa: E402
from tr34_fama_macbeth import (  # noqa: E402
    fm_slopes, nw_mean_t, pit_panel, rank_std)

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402

START = "2015-07-01"
plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def nwt(x, lags=3):
    import statsmodels.api as sm
    x = pd.Series(x).dropna()
    if len(x) < 8:
        return np.nan, np.nan
    r = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(r.params[0]), float(r.tvalues[0])


def kf_prior6013():
    import pandas_datareader.data as pdr
    raw = pdr.DataReader("6_Portfolios_ME_Prior_60_13", "famafrench", "1931-01-01")[0] / 100.0
    raw.index = raw.index.to_timestamp("M")
    return raw  # columns like 'SMALL LoPRIOR', 'ME1 PRIOR2', 'SMALL HiPRIOR', 'BIG ...'


def main():
    store = DuckStore("./data")
    print("=" * 104)
    print("TR-47  De Bondt-Thaler 長期反轉:60-13 月形成期,本座位+KF 長史(論文佇列 #1)")
    print("=" * 104)
    print("[trial accounting] +1 family(ltrev 單一規格)")

    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    me_full = px.resample("ME").last()
    me = me_full.loc[START:]
    ret_m = me.pct_change()
    fwd = ret_m.shift(-1)
    mem = load_membership()
    mm = member_mask(px.index, syms, mem).resample("ME").last().reindex(me.index).astype(bool)
    fwd = fwd.where(mm)

    ltrev = (me_full.shift(13) / me_full.shift(60) - 1).loc[START:].reindex(me.index)
    mom122 = (me_full.shift(2) / me_full.shift(12) - 1).loc[START:].reindex(me.index)
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0]
    fund = store.load_fundamentals(syms)
    syms_f = [s for s in syms if s in set(fund["symbol"])]
    sh = shares_panel(fund, px.index, syms_f)
    mcap = (sh * px[syms_f]).resample("ME").last().reindex(me.index)
    se = pit_panel(fund, "StockholdersEquity", px.index, syms_f)
    bm = (se.resample("ME").last().reindex(me.index) / mcap).where(lambda x: x > 0)

    lt_r = rank_std(ltrev.where(mm))
    mo_r = rank_std(mom122.where(mm))
    bm_r = rank_std(bm.where(mm[syms_f]))

    # ---- CAL a: construction sanity ----
    cs_mom = [lt_r.loc[t].corr(mo_r.loc[t], method="spearman") for t in me.index[::3]]
    cs_bm = [lt_r[syms_f].loc[t].corr(bm_r.loc[t], method="spearman") for t in me.index[::3]]
    c_mom, c_bm = float(np.nanmean(cs_mom)), float(np.nanmean(cs_bm))
    cal_a = (0 < c_mom < 0.9) and (c_bm < 0)
    print(f"CAL a:corr(ltrev,mom122)={c_mom:+.2f}(需 (0,0.9));corr(ltrev,bm)={c_bm:+.2f}"
          f"(需 <0,長期輸家=價值股) -> {'PASS' if cal_a else 'FAIL'}")

    # ---- CAL b: KF classic-era anchor ----
    kf = kf_prior6013()
    lo_s = kf["SMALL LoPRIOR"] if "SMALL LoPRIOR" in kf.columns else kf.iloc[:, 0]
    hi_s = kf["SMALL HiPRIOR"] if "SMALL HiPRIOR" in kf.columns else kf.iloc[:, 2]
    lo_b = kf["BIG LoPRIOR"] if "BIG LoPRIOR" in kf.columns else kf.iloc[:, 3]
    hi_b = kf["BIG HiPRIOR"] if "BIG HiPRIOR" in kf.columns else kf.iloc[:, 5]
    spread_s, spread_b = lo_s - hi_s, lo_b - hi_b
    m_dbt, t_dbt = nwt(spread_s.loc["1931":"1982"], lags=6)
    cal_b = (m_dbt > 0) and (t_dbt >= 2)
    print(f"CAL b:KF 小型股 Lo-Hi prior 價差 1931-1982 平均 {m_dbt*1e4:+.0f}bps/mo"
          f"(t={t_dbt:+.2f};需 >0 且 t>=2) -> {'PASS' if cal_b else 'FAIL'}")
    if not (cal_a and cal_b):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 decisive: our seat ----
    print("-" * 104)
    sl1 = fm_slopes({"ltrev": lt_r}, fwd, min_n=100)
    m1, t1 = nw_mean_t(sl1["ltrev"])
    print(f"C1(決定性,本座位):ltrev 單變量 FM 斜率 {m1*1e4:+7.1f} bps/mo  t={t1:+5.2f}"
          f"(中位覆蓋 {int(lt_r.notna().sum(axis=1).median())}/mo)")

    # ---- C2 joint with six chars ----
    gp = build_all(fund, px, syms_f)["gross_profitability"].resample("ME").last().reindex(me.index)
    beta = (px[syms_f].pct_change().rolling(252).cov(spy.pct_change())
            .div(spy.pct_change().rolling(252).var(), axis=0)
            .resample("ME").last().reindex(me.index))
    six_raw = {"gp": gp, "logmcap": np.log(mcap.where(mcap > 0)), "bm": bm,
               "mom122": mom122[syms_f], "str1m": ret_m[syms_f], "beta252": beta}
    six = {k: rank_std(v.where(mm[syms_f])) for k, v in six_raw.items()}
    sl7 = fm_slopes({**six, "ltrev": lt_r[syms_f]}, fwd[syms_f], min_n=100)
    print("C2 七特徵聯合(FF 吸收判讀):")
    for k in list(six) + ["ltrev"]:
        m, t = nw_mean_t(sl7[k])
        print(f"  {k:<8} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}")
    m7, t7 = nw_mean_t(sl7["ltrev"])

    # ---- C3 KF era table ----
    print("-" * 104)
    print("C3 KF 6 組合 Lo-Hi prior 價差的年代弧(McLean-Pontiff 型衰退表):")
    eras = [("1931-1982(DBT 樣本)", "1931", "1982"), ("1983-2000(發表後)", "1983", "2000"),
            ("2001-2014", "2001", "2014"), ("2015+(本座位窗)", "2015", "2026")]
    c3 = {}
    for lab, a, b in eras:
        ms, ts = nwt(spread_s.loc[a:b], lags=6)
        mb, tb = nwt(spread_b.loc[a:b], lags=6)
        c3[lab] = (ms, ts, mb, tb)
        print(f"  {lab:<18} 小型 {ms*1e4:+6.0f}bps/mo(t={ts:+5.2f}) | "
              f"大型 {mb*1e4:+6.0f}bps/mo(t={tb:+5.2f})")

    # ---- C4 subperiod ----
    a15, _ = (sl1["ltrev"].loc[:"2020-12-31"], None)
    b21 = sl1["ltrev"].loc["2021-01-01":]
    ma, ta = nwt(a15)
    mb_, tb_ = nwt(b21)
    print(f"C4 分期(本座位):2015-2020 {ma*1e4:+.1f}(t={ta:+.2f}) | 2021+ {mb_*1e4:+.1f}(t={tb_:+.2f})")

    # ---- verdict ----
    print("=" * 104)
    if t1 <= -2:
        v = "REVERSAL-CANDIDATE -- 長期反轉在本座位存活(後續成本關卡)"
    elif t1 >= 2:
        v = "CONTINUATION -- 符號反轉(anti-DBT),如實記錄"
    else:
        v = ("NO-SIGNAL -- 長期反轉在本座位(美大型股 2015+)無定價力;"
             "與 C3 的年代衰退弧一致(大型股腿在任何年代都最弱)")
    print(f"VERDICT: {v}")

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    labs = [e[0] for e in eras]
    x = np.arange(len(labs)); w = 0.38
    ax.bar(x - w / 2, [c3[k][0] * 1e4 for k in labs], w, label="小型股腿", color="#546e7a")
    ax.bar(x + w / 2, [c3[k][2] * 1e4 for k in labs], w, label="大型股腿", color="#f9a825")
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8)
    ax.axhline(0, c="k", lw=0.6); ax.legend()
    ax.set_title("C3 KF Lo-Hi prior(60,13)價差:年代衰退弧(bps/mo)")
    ax = axes[1]
    ax.bar(["C1 單變量", "C2 加六控制"], [m1 * 1e4, m7 * 1e4],
           color=["#2e7d32" if abs(t1) >= 2 else "#90a4ae",
                  "#2e7d32" if abs(t7) >= 2 else "#90a4ae"])
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title(f"本座位 ltrev 斜率(t={t1:+.2f} → {t7:+.2f})")
    fig.suptitle("TR-47 De Bondt-Thaler 長期反轉(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr47_longterm_reversal.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
