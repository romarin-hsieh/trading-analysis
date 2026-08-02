# -*- coding: utf-8 -*-
"""TR-50 -- Hou-Moskowitz 2005 price delay (docs/27 paper queue #4, the last one).

Delay = how slowly a stock's price incorporates market-wide information:
regress weekly returns on the market's contemporaneous + 4 lagged weekly returns;
D1 = 1 - R2(lags restricted to 0)/R2(unrestricted). HM: high-delay stocks earn a
premium -- but it lives almost entirely in small, neglected stocks (their own
size-quintile table shows ~0 in the largest quintile). Honest prior for OUR seat
(S&P 500 members): near-zero delay, tiny dispersion, NO premium.

F0 DECLARATION (pre-committed; single spec; trials +1 family)
  Construction (locked): W-WED weekly returns from adj close; market = SPY weekly;
  each JUNE (HM annual convention) per stock: trailing 52 weeks, OLS with 4 market
  lags; require >= 45 valid weeks and unrestricted R2 > 0.01 else NaN; D1 clipped
  to [0,1]; the June value is held for the following 12 months.
  Seat : S&P 500 members-only, monthly 2015-07+, TR-34 machinery verbatim.
  CAL (fail any -> STOP):
    a) delay levels: panel median D1 < 0.4 (large caps are fast) AND the top
       market-cap decile's median D1 < the panel median (the HM size gradient
       must exist even inside the S&P 500, sign only);
    b) regression sanity: median unrestricted R2 in [0.05, 0.8].
  C1 : (decisive) univariate FM slope of delay. Prior +(HM). |t| >= 2 -> candidate.
  C2 : joint with the TR-34 six characteristics.
  C3 : descriptive -- median D1 by within-panel size quintile (the gradient our
       CAL-a checks at the extremes).
  C4 : subperiod 2015-2020 vs 2021+ (F7).
  Verdict routing: |t|>=2 at prior sign -> CANDIDATE (cost gate next); else
  NO-SIGNAL on this seat (completes the information-diffusion channel; the
  small-cap leg belongs to p3).
Run: uv run python scripts/tests/tr50_price_delay.py
Chart: docs/tests/img/tr50_price_delay.png
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


def delay_at(ret_w: pd.DataFrame, mkt_w: pd.Series, asof: pd.Timestamp):
    """D1 and unrestricted R2 per symbol from the trailing 52 weeks ending at asof."""
    win = ret_w.loc[:asof].tail(52)
    mk = mkt_w.reindex(ret_w.index)
    lags = pd.concat({k: mk.shift(k) for k in range(5)}, axis=1).loc[win.index]
    out_d, out_r2 = {}, {}
    X_full = lags.to_numpy()
    for s in ret_w.columns:
        y = win[s].to_numpy()
        ok = np.isfinite(y) & np.isfinite(X_full).all(axis=1)
        if ok.sum() < 45:
            continue
        yy, XX = y[ok], X_full[ok]
        XX1 = np.column_stack([np.ones(len(yy)), XX])          # unrestricted
        XX0 = np.column_stack([np.ones(len(yy)), XX[:, 0]])    # contemporaneous only
        b1, *_ = np.linalg.lstsq(XX1, yy, rcond=None)
        b0, *_ = np.linalg.lstsq(XX0, yy, rcond=None)
        sst = ((yy - yy.mean()) ** 2).sum()
        if sst <= 0:
            continue
        r2u = 1 - ((yy - XX1 @ b1) ** 2).sum() / sst
        r2r = 1 - ((yy - XX0 @ b0) ** 2).sum() / sst
        if r2u <= 0.01:
            continue
        out_d[s] = float(np.clip(1 - r2r / r2u, 0, 1))
        out_r2[s] = float(r2u)
    return pd.Series(out_d), pd.Series(out_r2)


def main():
    store = DuckStore("./data")
    print("=" * 104)
    print("TR-50  Hou-Moskowitz price delay:資訊擴散速度(論文佇列 #4,最後一篇)")
    print("=" * 104)
    print("[trial accounting] +1 family(delay 單一規格)")

    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0]
    px_w = px.resample("W-WED").last()
    ret_w = px_w.pct_change()
    mkt_w = spy.resample("W-WED").last().pct_change()

    me = px.resample("ME").last().loc[START:]
    ret_m = me.pct_change()
    fwd = ret_m.shift(-1)
    mem = load_membership()
    mm = member_mask(px.index, syms, mem).resample("ME").last().reindex(me.index).astype(bool)
    fwd = fwd.where(mm)

    # annual June estimation, held 12 months
    junes = [pd.Timestamp(f"{y}-06-30") for y in range(2014, 2027)
             if pd.Timestamp(f"{y}-06-30") <= ret_w.index.max()]
    d_rows, r2_rows = {}, {}
    for j in junes:
        d, r2 = delay_at(ret_w, mkt_w, j)
        d_rows[j], r2_rows[j] = d, r2
    d_ann = pd.DataFrame(d_rows).T.reindex(columns=syms)
    delay_m = d_ann.reindex(me.index, method="ffill")
    delay = rank_std(delay_m.where(mm))
    r2_all = pd.DataFrame(r2_rows).T.stack()

    fund = store.load_fundamentals(syms)
    syms_f = [s for s in syms if s in set(fund["symbol"])]
    sh = shares_panel(fund, px.index, syms_f)
    mcap = (sh * px[syms_f]).resample("ME").last().reindex(me.index)

    # ---- CAL ----
    med_all = float(delay_m.where(mm).stack().median())
    mc_r = mcap.where(mm[syms_f]).rank(axis=1, pct=True)
    big = delay_m[syms_f].where(mc_r >= 0.9).stack().median()
    ok_a = (med_all < 0.4) and (big < med_all)
    print(f"CAL a:面板中位 D1 {med_all:.3f}(需 <0.4);市值前十分位中位 {big:.3f}"
          f"(需 < 面板中位=規模梯度存在) -> {'PASS' if ok_a else 'FAIL'}")
    med_r2 = float(r2_all.median())
    ok_b = 0.05 <= med_r2 <= 0.8
    print(f"CAL b:週頻迴歸中位 R²(全模){med_r2:.2f}(帶 [0.05,0.8]) -> "
          f"{'PASS' if ok_b else 'FAIL'}")
    if not (ok_a and ok_b):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 ----
    print("-" * 104)
    sl1 = fm_slopes({"delay": delay}, fwd, min_n=100)
    m1, t1 = nw_mean_t(sl1["delay"])
    print(f"C1(決定性):delay 單變量 FM {m1*1e4:+7.1f} bps/mo  t={t1:+5.2f}"
          f"(覆蓋 {int(delay.notna().sum(axis=1).median())}/mo)")

    # ---- C2 joint ----
    gp = build_all(fund, px, syms_f)["gross_profitability"].resample("ME").last().reindex(me.index)
    se = pit_panel(fund, "StockholdersEquity", px.index, syms_f)
    bm = (se.resample("ME").last().reindex(me.index) / mcap).where(lambda x: x > 0)
    beta = (px[syms_f].pct_change().rolling(252).cov(spy.pct_change())
            .div(spy.pct_change().rolling(252).var(), axis=0)
            .resample("ME").last().reindex(me.index))
    me_f = me[syms_f]
    six_raw = {"gp": gp, "logmcap": np.log(mcap.where(mcap > 0)), "bm": bm,
               "mom122": me_f.shift(2) / me_f.shift(12) - 1, "str1m": ret_m[syms_f],
               "beta252": beta}
    six = {k: rank_std(v.where(mm[syms_f])) for k, v in six_raw.items()}
    sl7 = fm_slopes({**six, "delay": delay[syms_f]}, fwd[syms_f], min_n=100)
    print("C2 七特徵聯合:")
    for k in list(six) + ["delay"]:
        m, t = nw_mean_t(sl7[k])
        print(f"  {k:<8} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}")
    m7, t7 = nw_mean_t(sl7["delay"])

    # ---- C3 size gradient ----
    print("C3 面板內規模五分位的中位 D1(HM 梯度):")
    grads = []
    for q in range(5):
        sel = delay_m[syms_f].where((mc_r >= q / 5) & (mc_r < (q + 1) / 5))
        v = float(sel.stack().median())
        grads.append(v)
        print(f"  Q{q+1}(小→大){v:.3f}")

    # ---- C4 subperiod ----
    ma, ta = nwt(sl1["delay"].loc[:"2020-12-31"])
    mb, tb = nwt(sl1["delay"].loc["2021-01-01":])
    print(f"C4 分期:2015-2020 {ma*1e4:+.1f}(t={ta:+.2f}) | 2021+ {mb*1e4:+.1f}(t={tb:+.2f})")

    # ---- verdict ----
    print("=" * 104)
    if t1 >= 2:
        v = "CANDIDATE -- delay 溢酬在本座位存活(後續成本關卡)"
    elif t1 <= -2:
        v = "INVERTED -- 符號與 HM 相反,如實記錄"
    else:
        v = ("NO-SIGNAL -- price delay 在本座位(美大型股 2015+)無定價力;"
             "與 HM 自己的規模表一致(最大市值五分位溢酬≈0);資訊擴散通道關閉,小型股腿屬 p3")
    print(f"VERDICT: {v}")

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
    ax = axes[0]
    ax.bar([f"Q{i+1}" for i in range(5)], grads, color="#1565c0")
    ax.set_title("C3 面板內規模五分位中位 D1(小→大)")
    ax = axes[1]
    ax.bar(["C1 單變量", "C2 加六控制"], [m1 * 1e4, m7 * 1e4],
           color=["#2e7d32" if abs(t1) >= 2 else "#90a4ae",
                  "#2e7d32" if abs(t7) >= 2 else "#90a4ae"])
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title(f"delay FM 斜率(bps/mo;t={t1:+.2f} → {t7:+.2f})")
    fig.suptitle("TR-50 Hou-Moskowitz price delay(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr50_price_delay.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
