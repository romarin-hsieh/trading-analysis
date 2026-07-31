# -*- coding: utf-8 -*-
"""TR-51 -- GP survivorship FINAL VERDICT (docs/27 B1; TR-27's still-open half)
+ the regime-vs-crowding autopsy (docs/25 attack 8).

The GP honest chain (headline ICIR +0.30 -> members-only +0.23 -> membership-PIT
+0.13, TR-27) was measured on a price store MISSING the delisted/merged members.
The Tiingo rotation restores their prices; the EDGAR backfill (Form-4 CIK bridge)
restores their fundamentals. This TR closes the chain's last open caveat.

SCOPE FACT (stated before assembly): the panel window is 2015-07+, so the only
absences that can matter are members who died AFTER 2015-07 (FRC/SIVB/TWTR/ATVI
cohort) -- all inside the XBRL era (2009+), hence fundamentally patchable. Names
dead before the window never enter a members-masked 2015+ cross-section; names
dead before ~2009 have no XBRL facts and are declared out of patch reach.

BIAS DIRECTIONS (both pre-stated):
  UP  : bankruptcies/forced exits cluster in LOW-GP names with terrible terminal
        returns; their absence flatters the low-GP bucket -> unpatched chain
        UNDERSTATES GP -> patch strengthens.
  DOWN: acquisition targets (often profitable, bid premium) vanish too; their
        absence removes high-GP winners -> patch weakens.

F0 DECLARATION (pre-committed while both drips are still running)
  Trials : +0 (same GP family, corrected universe -- the TR-39b/b1 convention).
  Seat   : S&P 500 members-only, monthly + 63d clocks, 2015-07+, TR-27/34
           machinery verbatim. Baseline = store universe MINUS the Tiingo-restored
           names; patched = full universe. Same code path for both.
  CAL (fail any -> STOP):
    a) machinery fidelity on the UNPATCHED set: GP-only FM slope > 0 AND the 63d
       members-only rank ICIR in [0.03, 0.25] (the TR-34 CAL-a band, anchored to
       TR-33's +0.097).
    b) the patch bites: >= 40 restored names enter the members-masked GP panel
       (gp + fwd + membership) in >= 1 month.
    c) delisting reality: at least one of {FRC, SBNY, SIVBQ, ENDP, BBBYQ} is
       restored with a terminal close < $10 (the collapse tails are really there).
  C1 (decisive) : patched 63d members-only GP ICIR vs the unpatched same-code
       value. Tiers on the PATCHED ICIR:
         >= 0.10                        -> SURVIVES-SURVIVORSHIP (chain endpoint
                                           ~+0.13 stands)
         0.05 <= x < 0.10               -> WEAKENED (chain endpoint revised down)
         <  0.05                        -> SURVIVORSHIP-ARTIFACT (the honest
                                           chain ends at ~0)
         > unpatched + 0.03             -> STRENGTHENED (bankruptcy-loser
                                           direction dominated)
  C2 : six-characteristic joint FM (TR-34 spec) on the patched universe: GP
       slope/t full-window + 2015-2020 / 2021+ split -- this becomes the new
       F10 WATCH baseline.
  C3 (attack-8 autopsy, descriptive, no new family): the patched univariate
       monthly GP slope series vs (i) HML state: mean slope in HML>0 vs HML<0
       months, difference t; (ii) a linear time trend, t. Pre-committed labels:
         REGIME    if |state difference| t >= 2 and trend ns
         CROWDING  if trend t <= -2 and state difference ns
         MIXED/INCONCLUSIVE otherwise
       (regime => reopen condition = value-regime flip; crowding => never).
  C4 : the restored cohort's story (descriptive): n entering panel, median GP
       rank in their final 6 member months, median following-6m return vs the
       member EW -- who exactly was the absence hiding.
  GATE: tiingo done >= 300 AND the EDGAR backfill has processed every currently
        priced name (todo == 0).
Run: uv run python scripts/tests/tr51_gp_survivorship.py
Chart: docs/tests/img/tr51_gp_survivorship.png
"""

from __future__ import annotations

import json
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

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402

START = "2015-07-01"
DEATH_CHECK = ("FRC", "SBNY", "SIVBQ", "ENDP", "BBBYQ")
plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def nwt(x, lags=3):
    import statsmodels.api as sm
    x = pd.Series(x).dropna()
    if len(x) < 8:
        return np.nan, np.nan
    r = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(r.params[0]), float(r.tvalues[0])


def icir_63d(gp_d: pd.DataFrame, px: pd.DataFrame, mm_d: pd.DataFrame) -> float:
    fwd63 = px.pct_change(63).shift(-63)
    gp_m = gp_d.where(mm_d)
    ics = []
    for i in range(0, len(px.index) - 63, 63):
        s, f = gp_m.iloc[i], fwd63.iloc[i]
        ok = s.notna() & f.notna()
        if ok.sum() >= 50:
            ics.append(s[ok].rank().corr(f[ok].rank()))
    ics = pd.Series(ics, dtype=float)
    return float(ics.mean() / ics.std()) if len(ics) > 3 and ics.std() > 0 else np.nan


def build_leg(store, syms):
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms_f = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms_f]
    gp_d = build_all(fund, px, syms_f)["gross_profitability"]
    mem = load_membership()
    mm_d = member_mask(px.index, syms_f, mem)
    me = px.resample("ME").last().loc[START:]
    mm = mm_d.resample("ME").last().reindex(me.index).astype(bool)
    fwd = me.pct_change().shift(-1).where(mm)
    gp_m = gp_d.resample("ME").last().reindex(me.index)
    return dict(px=px, fund=fund, syms=syms_f, gp_d=gp_d, mm_d=mm_d, me=me,
                mm=mm, fwd=fwd, gp_m=gp_m)


def main():
    tiingo = json.loads(Path("data/_tiingo_backfill_state.json").read_text())
    eb_p = Path("data/_edgar_backfill_state.json")
    if len(tiingo["done"]) < 300 or not eb_p.exists():
        print(f"gate closed: tiingo {len(tiingo['done'])}/300, edgar state "
              f"{'missing' if not eb_p.exists() else 'ok'}")
        return
    eb = json.loads(eb_p.read_text())
    processed = set(eb["done"]) | set(eb["no_cik"]) | set(eb["no_facts"])
    todo = [s for s in tiingo["done"] if s not in processed]
    if todo:
        print(f"gate closed: edgar backfill todo {len(todo)} -- re-run edgar_backfill.py")
        return

    store = DuckStore("./data")
    restored = set(tiingo["done"])
    all_syms = [s for s in store.list_symbols("1d")
                if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    base_syms = [s for s in all_syms if s not in restored]

    print("=" * 104)
    print("TR-51  GP 去倖存終判(docs/27 B1)+ regime-vs-crowding 驗屍(docs/25 攻擊 8)")
    print("=" * 104)
    print(f"[trial accounting] +0(同一 GP 家族,宇宙修正;b1 慣例)")
    print(f"[universe] 全 {len(all_syms)} | 基線(未補) {len(base_syms)} | 修復名單 {len(restored)}")

    base = build_leg(store, base_syms)
    pat = build_leg(store, all_syms)

    # ---- CAL a: machinery fidelity on the unpatched set ----
    sl_u = fm_slopes({"gp": rank_std(base["gp_m"].where(base["mm"]))}, base["fwd"], min_n=100)
    m_u, t_u = nw_mean_t(sl_u["gp"])
    icir_u = icir_63d(base["gp_d"], base["px"], base["mm_d"])
    ok_a = (m_u > 0) and (0.03 <= icir_u <= 0.25)
    print(f"CAL a:未補集 GP-only FM {m_u*1e4:+.1f}bps/mo(需>0);63d 成員 ICIR "
          f"{icir_u:+.3f}(帶 [0.03,0.25]) -> {'PASS' if ok_a else 'FAIL'}")

    # ---- CAL b: the patch bites ----
    in_panel = [s for s in restored if s in pat["syms"]
                and bool((pat["gp_m"][s].notna() & pat["mm"][s] & pat["fwd"][s].notna()).any())]
    ok_b = len(in_panel) >= 40
    print(f"CAL b:修復名單進入成員面板 {len(in_panel)} 檔(門檻 40) -> "
          f"{'PASS' if ok_b else 'FAIL'}")

    # ---- CAL c: delisting reality ----
    # POST-RUN AUDIT NOTE (v1 -> v2): v1 FAILED with an empty hit list -- two
    # implementation errors, not missing data. (1) the probe list guessed SIVBQ;
    # Tiingo carries the tail under SIVB (last $0.01) and SBNY ($0.40). (2) the
    # lookup ran on the FUNDAMENTALS-FILTERED panel, which silently drops any
    # collapse name lacking facts (SBNY is no_cik). v2 queries the PRICE STORE
    # directly with the alias-expanded list; the declared threshold (>=1 name,
    # terminal close < $10) is unchanged.
    hits = []
    for s in DEATH_CHECK + ("SIVB",):
        try:
            ser = store.load_close_pivot([s], column="adj_close").iloc[:, 0].dropna()
        except Exception:
            continue
        if len(ser) and float(ser.iloc[-1]) < 10:
            hits.append((s, float(ser.iloc[-1]), ser.index[-1]))
    ok_c = len(hits) >= 1
    print(f"CAL c:崩潰尾巴實在(終價<$10):{[(s, round(v,2), str(d.date())) for s,v,d in hits]}"
          f" -> {'PASS' if ok_c else 'FAIL'}")
    if not (ok_a and ok_b and ok_c):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 decisive: patched vs unpatched ICIR ----
    print("-" * 104)
    icir_p = icir_63d(pat["gp_d"], pat["px"], pat["mm_d"])
    d = icir_p - icir_u
    if icir_p > icir_u + 0.03:
        tier = "STRENGTHENED(破產輸家方向主導)"
    elif icir_p >= 0.10:
        tier = "SURVIVES-SURVIVORSHIP(誠實鏈終點 ~+0.13 成立)"
    elif icir_p >= 0.05:
        tier = "WEAKENED(誠實鏈終點下修)"
    else:
        tier = "SURVIVORSHIP-ARTIFACT(誠實鏈終點 ~0)"
    print(f"C1(決定性):63d 成員 ICIR 未補 {icir_u:+.3f} -> 補後 {icir_p:+.3f}"
          f"(Δ{d:+.3f}) -> {tier}")

    # ---- C2 joint FM on patched universe ----
    px, me, mm, fwd, fund, syms_f = (pat["px"], pat["me"], pat["mm"], pat["fwd"],
                                     pat["fund"], pat["syms"])
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0]
    from tr27_gp_membership_size import shares_panel
    from tr34_fama_macbeth import pit_panel
    sh = shares_panel(fund, px.index, syms_f)
    mcap = (sh * px).resample("ME").last().reindex(me.index)
    se = pit_panel(fund, "StockholdersEquity", px.index, syms_f)
    bm = (se.resample("ME").last().reindex(me.index) / mcap).where(lambda x: x > 0)
    beta = (px.pct_change().rolling(252).cov(spy.pct_change())
            .div(spy.pct_change().rolling(252).var(), axis=0)
            .resample("ME").last().reindex(me.index))
    ret_m = me.pct_change()
    six = {"gp": pat["gp_m"], "logmcap": np.log(mcap.where(mcap > 0)), "bm": bm,
           "mom122": me.shift(2) / me.shift(12) - 1, "str1m": ret_m, "beta252": beta}
    chars = {k: rank_std(v.where(mm)) for k, v in six.items()}
    sl6 = fm_slopes(chars, fwd, min_n=100)
    print("C2 六特徵聯合(補後宇宙;新的 F10 WATCH 基準):")
    for k in six:
        m, t = nw_mean_t(sl6[k])
        print(f"  {k:<8} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}")
    ga, ta_ = nwt(sl6["gp"].loc[:"2020-12-31"])
    gb, tb_ = nwt(sl6["gp"].loc["2021-01-01":])
    print(f"  gp 分期:2015-2020 {ga*1e4:+.1f}(t={ta_:+.2f}) | 2021+ {gb*1e4:+.1f}(t={tb_:+.2f})")

    # ---- C3 autopsy: regime vs crowding ----
    print("-" * 104)
    sl_gp = fm_slopes({"gp": chars["gp"]}, fwd, min_n=100)["gp"]
    ff = load_ff_factors(start="2015-01-01", momentum=False)
    hml_m = (1 + ff["HML"]).resample("ME").prod() - 1
    hml = hml_m.reindex(sl_gp.index)
    up, dn = sl_gp[hml > 0], sl_gp[hml <= 0]
    mu_up, _ = nwt(up)
    mu_dn, _ = nwt(dn)
    import statsmodels.api as sm
    dfab = pd.DataFrame({"y": sl_gp, "h": (hml > 0).astype(float)}).dropna()
    rs = sm.OLS(dfab["y"], sm.add_constant(dfab["h"])).fit(
        cov_type="HAC", cov_kwds={"maxlags": 3})
    t_state = float(rs.tvalues["h"])
    tt = np.arange(len(sl_gp), dtype=float)
    rt = sm.OLS(sl_gp.to_numpy(), sm.add_constant(tt)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 3})
    t_trend = float(rt.tvalues[1])
    if abs(t_state) >= 2 and abs(t_trend) < 2:
        label = "REGIME(價值 regime 條件化;翻案條件=HML regime 翻轉)"
    elif t_trend <= -2 and abs(t_state) < 2:
        label = "CROWDING(單調時間衰退;永不翻案)"
    else:
        label = "MIXED/INCONCLUSIVE"
    print(f"C3 驗屍:GP 斜率 HML>0 月 {mu_up*1e4:+.1f} vs HML<=0 月 {mu_dn*1e4:+.1f}"
          f"(狀態差 t={t_state:+.2f});時間趨勢 t={t_trend:+.2f} -> {label}")

    # ---- C4 restored-cohort story ----
    ranks, fwd6 = [], []
    ew6 = (1 + fwd.mean(axis=1)).rolling(6).apply(np.prod, raw=True) - 1
    gp_rank = pat["gp_m"].where(mm).rank(axis=1, pct=True)
    ret6 = (1 + me.pct_change()).rolling(6).apply(np.prod, raw=True).shift(-6) - 1
    for s in in_panel:
        alive = pat["mm"][s][pat["mm"][s]].index
        if len(alive) < 3:
            continue
        tail = alive[-6:]
        ranks.append(float(gp_rank.loc[tail, s].median()))
        v = ret6.loc[tail[0], s] if tail[0] in ret6.index else np.nan
        b = ew6.loc[tail[-1]] if tail[-1] in ew6.index else np.nan
        if np.isfinite(v) and np.isfinite(b):
            fwd6.append(float(v - b))
    print(f"C4 修復名單(n={len(in_panel)}):最後 6 個成員月的 GP 分位中位 "
          f"{np.nanmedian(ranks):+.2f};退場前 6 月相對報酬中位 {np.nanmedian(fwd6)*100:+.1f}%")

    # ---- verdict ----
    print("=" * 104)
    m6, t6 = nw_mean_t(sl6["gp"])
    print(f"VERDICT: {tier};C2 聯合 GP t={t6:+.2f}(新 WATCH 基準);驗屍:{label}")

    # ---- chart ----
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    ax = axes[0]
    ax.bar(["未補", "補後"], [icir_u, icir_p], color=["#90a4ae", "#1565c0"])
    ax.axhline(0.10, ls="--", c="k", lw=0.8); ax.axhline(0.05, ls=":", c="k", lw=0.8)
    ax.set_title("C1 63d 成員 GP ICIR(虛線=判定級距)")
    ax = axes[1]
    roll = sl_gp.rolling(36).mean() * 1e4
    ax.plot(roll.index.to_timestamp() if hasattr(roll.index, "to_timestamp") else roll.index,
            roll, color="#1565c0")
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title("C3 GP 月斜率 36 個月滾動均(bps/mo)")
    ax = axes[2]
    ax.bar(["HML>0 月", "HML≤0 月"], [mu_up * 1e4, mu_dn * 1e4], color="#6a1b9a")
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title(f"C3 GP 斜率×價值 regime(狀態差 t={t_state:+.2f})")
    fig.suptitle("TR-51 GP 去倖存終判+驗屍(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr51_gp_survivorship.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
