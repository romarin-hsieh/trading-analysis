# -*- coding: utf-8 -*-
"""TR-48 -- Lakonishok-Shleifer-Vishny 1994 contrarian value (docs/27 paper queue #2).

LSV: value works because glamour (high past growth, low yield) stocks embed
extrapolation errors -- E/P, C/P, B/M positive, past SALES GROWTH negative, and
two-way sorts (growth x cash-yield) sharpen it. Honest prior for OUR seat
(S&P 500 members 2015+): value is dead here (TR-34 bm ~0); the LSV question is
whether the CONTRARIAN combination (growth side included) sees anything the
single chars miss.

F0 DECLARATION (pre-committed; single spec, no grid; trials +1 family)
  Chars (four, constructions locked):
    ep  = FY NetIncomeLoss / mcap (PIT, existing builder). Prior +.
    cp  = FY NetCashProvidedByUsedInOperatingActivities / mcap. Prior +.
    bm  = StockholdersEquity / mcap (existing builder). Prior +.
    gs3 = FY Revenues (with ASC-606 tag fallback RevenueFromContractWith
          CustomerExcludingAssessedTax) / its value 3 years earlier - 1.
          LSV use a 5y weighted rank; 3y level growth declared as the
          EDGAR-depth-constrained simplification. Prior NEGATIVE (glamour loses).
  Seat : S&P 500 members-only, monthly 2015-07+, TR-34 machinery verbatim.
  CAL (fail any -> STOP):
    a) value ranges (unit/tag fidelity): panel median ep in [0.01, 0.10],
       cp in [0.02, 0.20], gs3 in [0.03, 0.80];
    b) structure: mean cross-sectional corr(ep, bm) > 0 (value chars cohere)
       AND corr(gs3, bm) < 0 (growth stocks are low-B/M).
  C1 : four univariate FMs. Candidate tier: |t| >= 2 at the PRIOR sign.
  C2 : LSV two-way 3x3 (gs3 terciles x cp terciles): contrarian corner (low
       growth, high C/P) minus glamour corner (high growth, low C/P), monthly
       EW, mean/NW-t -- the paper's signature table on our seat.
  C3 : four chars joint FM (internal horse race; which one carries, if any).
  C4 : subperiod 2015-2020 vs 2021+ (F7).
  Verdict routing: any C1 char at prior sign |t|>=2 -> CANDIDATE (cost gate
  next); C2 corner spread t>=2 without C1 -> COMBINATION-ONLY (reported, no
  upgrade without fresh pre-registration); else NO-SIGNAL on this seat.
  Honest bounds: large caps 2015+ = value's documented dead zone; EDGAR depth
  limits GS to 3y; FY flows (no TTM interpolation, declared).
Run: uv run python scripts/tests/tr48_lsv_value.py
Chart: docs/tests/img/tr48_lsv_value.png
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
from tr27_gp_membership_size import member_mask  # noqa: E402
from tr34_fama_macbeth import fm_slopes, nw_mean_t, rank_std  # noqa: E402

from trading_analysis.data.connectors.edgar import point_in_time  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import (  # noqa: E402
    _fy, _shares, book_to_market, earnings_yield)

START = "2015-07-01"
plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
PRIOR = {"ep": +1, "cp": +1, "bm": +1, "gs3": -1}


def nwt(x, lags=3):
    import statsmodels.api as sm
    x = pd.Series(x).dropna()
    if len(x) < 8:
        return np.nan, np.nan
    r = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(r.params[0]), float(r.tvalues[0])


def main():
    store = DuckStore("./data")
    print("=" * 104)
    print("TR-48  LSV 1994 價值反向:E/P、C/P、B/M、銷售成長(論文佇列 #2)")
    print("=" * 104)
    print("[trial accounting] +1 family(LSV 四特徵,單一規格)")

    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    me = px.resample("ME").last().loc[START:]
    ret_m = me.pct_change()
    fwd = ret_m.shift(-1)
    mem = load_membership()
    mm = member_mask(px.index, syms, mem).resample("ME").last().reindex(me.index).astype(bool)
    fwd = fwd.where(mm)

    mcap_d = px * _shares(fund, px.index, syms)
    ep_d = earnings_yield(fund, px, syms)
    bm_d = book_to_market(fund, px, syms)
    cfo_d = point_in_time(_fy(fund), "NetCashProvidedByUsedInOperatingActivities",
                          px.index, syms)
    cp_d = cfo_d / mcap_d.where(mcap_d > 0)
    rev_d = point_in_time(_fy(fund), "Revenues", px.index, syms)
    rev2_d = point_in_time(_fy(fund), "RevenueFromContractWithCustomerExcludingAssessedTax",
                           px.index, syms)
    rev_d = rev_d.where(rev_d.notna(), rev2_d)
    gs3_d = (rev_d / rev_d.shift(756).where(lambda x: x > 0) - 1)

    raw = {"ep": ep_d, "cp": cp_d, "bm": bm_d, "gs3": gs3_d}
    chars_m = {k: v.resample("ME").last().reindex(me.index) for k, v in raw.items()}
    chars = {k: rank_std(v.where(mm)) for k, v in chars_m.items()}

    # ---- CAL a: value ranges ----
    med = {k: float(chars_m[k].where(mm).stack().median()) for k in raw}
    ok_a = (0.01 <= med["ep"] <= 0.10 and 0.02 <= med["cp"] <= 0.20
            and 0.03 <= med["gs3"] <= 0.80)
    print(f"CAL a:面板中位 ep {med['ep']:.3f}(帶[0.01,0.10])、cp {med['cp']:.3f}"
          f"([0.02,0.20])、gs3 {med['gs3']:.2f}([0.03,0.80]) -> {'PASS' if ok_a else 'FAIL'}")
    # ---- CAL b: structure ----
    cs = lambda a, b: float(np.nanmean(  # noqa: E731
        [chars[a].loc[t].corr(chars[b].loc[t], method="spearman") for t in me.index[::3]]))
    c_epbm, c_gsbm = cs("ep", "bm"), cs("gs3", "bm")
    ok_b = (c_epbm > 0) and (c_gsbm < 0)
    print(f"CAL b:corr(ep,bm)={c_epbm:+.2f}(需>0);corr(gs3,bm)={c_gsbm:+.2f}(需<0,"
          f"成長股=低B/M) -> {'PASS' if ok_b else 'FAIL'}")
    if not (ok_a and ok_b):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 four univariate FMs ----
    print("-" * 104)
    print("C1 四個單變量 FM(先驗符號:ep+ cp+ bm+ gs3−):")
    c1 = {}
    for k in raw:
        sl = fm_slopes({k: chars[k]}, fwd, min_n=100)
        m, t = nw_mean_t(sl[k])
        c1[k] = (m, t)
        hit = np.sign(m) == PRIOR[k] and abs(t) >= 2
        nmed = int(chars[k].notna().sum(axis=1).median())
        print(f"  {k:<4} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}(覆蓋 {nmed}/mo)"
              f"{' <-- 候選(先驗符號)' if hit else ''}")

    # ---- C2 LSV two-way 3x3 ----
    print("-" * 104)
    spread = []
    for t in me.index:
        g, c = chars["gs3"].loc[t], chars["cp"].loc[t]
        df = pd.DataFrame({"g": g, "c": c, "f": fwd.loc[t]}).dropna()
        if len(df) < 100:
            continue
        gq = df["g"].rank(pct=True)
        cq = df["c"].rank(pct=True)
        contra = df[(gq <= 1 / 3) & (cq >= 2 / 3)]["f"]
        glam = df[(gq >= 2 / 3) & (cq <= 1 / 3)]["f"]
        if len(contra) >= 8 and len(glam) >= 8:
            spread.append(contra.mean() - glam.mean())
    m2, t2 = nwt(spread)
    print(f"C2 LSV 雙向格(低成長高C/P − 高成長低C/P):{m2*1e4:+.1f} bps/mo  t={t2:+.2f}"
          f"(n={len(spread)} 月)")

    # ---- C3 joint horse race ----
    sl4 = fm_slopes(chars, fwd, min_n=100)
    print("C3 四特徵聯合(內部賽馬):")
    c3 = {}
    for k in raw:
        m, t = nw_mean_t(sl4[k])
        c3[k] = (m, t)
        print(f"  {k:<4} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}")

    # ---- C4 subperiod ----
    print("C4 分期:")
    for k in raw:
        sl = fm_slopes({k: chars[k]}, fwd, min_n=100)[k]
        ma, ta = nwt(sl.loc[:"2020-12-31"])
        mb, tb = nwt(sl.loc["2021-01-01":])
        print(f"  {k:<4} 2015-2020:{ma*1e4:+7.1f}(t={ta:+.2f}) | 2021+:{mb*1e4:+7.1f}(t={tb:+.2f})")

    # ---- verdict ----
    print("=" * 104)
    cands = [k for k in raw if np.sign(c1[k][0]) == PRIOR[k] and abs(c1[k][1]) >= 2]
    if cands:
        v = f"CANDIDATE -- {','.join(cands)} 以先驗符號過 |t|>=2(後續成本關卡)"
    elif abs(t2) >= 2 and m2 > 0:
        v = ("COMBINATION-ONLY -- 單特徵全零但 LSV 雙向格價差顯著;"
             "依 F0 僅列報,升級需新的預先登記")
    else:
        v = ("NO-SIGNAL -- 四路價值與反向成長在本座位(美大型股 2015+)全數無定價力;"
             "LSV 組合也救不回(C2)")
    print(f"VERDICT: {v}")

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
    ax = axes[0]
    ks = list(raw)
    ts = [c1[k][1] for k in ks]
    ax.bar(ks, ts, color=["#2e7d32" if (np.sign(c1[k][0]) == PRIOR[k] and abs(c1[k][1]) >= 2)
                          else "#90a4ae" for k in ks])
    ax.axhline(2, ls="--", c="k", lw=0.8); ax.axhline(-2, ls="--", c="k", lw=0.8)
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title("C1 四特徵單變量 FM t 值(ep/cp/bm/gs3)")
    ax = axes[1]
    ax.bar(["LSV 雙向格價差"], [m2 * 1e4],
           color="#2e7d32" if (abs(t2) >= 2 and m2 > 0) else "#90a4ae")
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title(f"C2 反向角 − 魅力角(bps/mo,t={t2:+.2f})")
    fig.suptitle("TR-48 LSV 價值反向(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr48_lsv_value.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
