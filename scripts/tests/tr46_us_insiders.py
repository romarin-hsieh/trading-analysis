# -*- coding: utf-8 -*-
"""TR-46 -- US insider trading, Form 4 (docs/28 p2): does opportunistic insider
net buying price the cross-section on OUR seat (S&P 500 members, 2015+)?

The US large-cap seat's death certificates (TR-23/32/34) cover PRICE and
FUNDAMENTAL characteristics; insider filings are a different information channel,
untested here. Literature: Lakonishok-Lee 2001 (NPR predicts, mostly small caps),
Cohen-Malloy-Pomorski 2012 JF "Decoding Inside Information" (only OPPORTUNISTIC
trades -- those not part of a routine same-month-every-year pattern -- carry
information). Honest prior stated up front: on LARGE caps post-2015 the size
dependence works against us; a clean NO-SIGNAL is a legitimate and useful verdict
(it scopes the p3 small-cap leg).

F0 DECLARATION (this file was written while the quarterly download was still
running and is committed BEFORE any signal panel is assembled or inspected --
the raw quarter parquets exist, no npr/opp/rou series has been computed)
  Family : +1 (US insider trio; single spec, no grid). C3 trades the fitted sign.
  Seat   : S&P 500 members-only (TR-27 mask), monthly 2015-07+, TR-34 machinery
           verbatim (rank_std, fm_slopes, NW 3 lags); fwd = next-month member-
           masked return; min_n=100 for npr6/opp6, 50 for rou6 (declared: the
           routine subset is structurally thinner).
  Filters (locked): Form 4 ORIGINALS only (doc_type == "4"; amendments excluded
           against double counting), non-derivative open-market codes P/S,
           officers & directors only (relationship contains officer/director;
           pure 10%-owners excluded), shares > 0. Event unit = unique (symbol,
           owner, filing_date, code) -- multi-lot executions collapse to one
           event so block sales don't overweight. ALL clocks = FILING_DATE (the
           public-information time; the probe found filings reporting years-old
           transactions). Symbol map: upper + '.'->'-'.
  Characteristics (exactly three):
    npr6 = (nP - nS)/(nP + nS), trailing 6 months of events, count-based
           (Lakonishok-Lee); NaN when no events. Prior: +.
    opp6 = npr6 over OPPORTUNISTIC traders only. Prior: + (the CMP channel).
    rou6 = npr6 over ROUTINE traders only. Prior: ~0 (in-family placebo).
    CMP classification (PIT, per owner-issuer pair, assigned per calendar year Y
    from history strictly before Y): eligible if the pair has >=1 event in EACH
    of Y-1, Y-2, Y-3; ROUTINE if some single calendar month M has an event in
    all three of those years; else OPPORTUNISTIC; ineligible pairs (young
    histories) enter npr6 only. Deviation declared: CMP classify on transaction
    months; we use FILING months uniformly for PIT cleanliness.
  CAL (fail any -> STOP):
    a) parse sanity: yearly market-wide insider sell/buy DOLLAR ratio median in
       [2, 20] (insiders are structural net sellers; inversion = A/D-code bug);
    b) join fidelity: >= 99% of kept transaction rows carry filing_date, symbol
       and relationship after the two joins;
    c) coverage + crisis anchor: median month >= 250 members with npr6; AND the
       2020-03 market-wide monthly NPR (all issuers, count-based) >= its own
       90th percentile over 2006-2026 (the documented COVID insider-buying wave
       -- missing it means the window/clock machinery is broken).
  C1 : three univariate FMs. Candidate tier: opp6 t >= 2. Pre-stated
       identification readout: CMP pattern = opp6 slope > rou6 slope with rou6
       insignificant; if rou6 is comparable to opp6, the honest verdict is
       GENERIC-ACTIVITY (not an information channel).
  C2 : opp6 jointly with the TR-34 six characteristics (gp, logmcap, bm, mom122,
       str1m, beta252) on common months -- is it independently priced?
  C3 : cost gate on the C1 candidate, EXCESS basis (TR-45 convention): top-decile
       long-only at fitted sign, monthly step, excess over the member-masked EW
       universe, 10bps flat round trip (commission-free US large caps, 2-4bps
       half-spreads) + mandatory 2x stress row (F2). Tiers: excess-net mean>0 and
       t>=2 SURVIVES-COSTS; net>0 or t>=1 MARGINAL; else FAILS-COSTS.
  C4 : subperiod 2015-2020 vs 2021+ (F7 decay watch) + activity diagnostics
       (events/month, classified share).
  Verdict routing (pre-committed):
    opp6 t>=2 + CMP pattern + C3 clean   -> SIGNAL
    opp6 t>=2 + CMP pattern, C3 not clean-> MECHANISM-CONFIRMED / MARGINAL
    opp6 t>=2 but rou6 comparable        -> GENERIC-ACTIVITY
    opp6 t<2                             -> NO-SIGNAL (this seat; the small-cap
                                            leg belongs to p3, no re-spec here)
  Honest bounds: large-cap 2015+ = the literature's WEAKEST habitat for insider
  signals; single macro arc; count-NPR ignores trade size (declared); delisting
  bounds inherited from the price store (TR-13); trials +1.
  GATE: abort unless >= 81 quarterly parquets (2006q1..2026q1) exist.

Run: uv run python scripts/tests/tr46_us_insiders.py   (after the download)
Chart: docs/tests/img/tr46_us_insiders.png
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

from sec_form4 import OUT as F4DIR  # noqa: E402
from sec_form4 import load_all  # noqa: E402
from sp500_constituents import load_membership  # noqa: E402
from tr27_gp_membership_size import member_mask, shares_panel  # noqa: E402
from tr34_fama_macbeth import (  # noqa: E402
    fm_slopes, nw_mean_t, pit_panel, rank_std)

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402

START = "2015-07-01"
TRIO = ("npr6", "opp6", "rou6")
RT_COST = 0.0010                      # 10bps flat round trip; 2x stress below
plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def load_events():
    df = load_all()
    df = df[df["doc_type"].astype(str) == "4"]
    df = df[df["code"].isin(["P", "S"])]
    df = df[df["shares"] > 0]
    df = df[df["symbol"].notna() & df["filing_date"].notna()]
    rel = df["relationship"].astype(str).str.lower()
    keep_rel = rel.str.contains("officer") | rel.str.contains("director")
    df = df[keep_rel]
    df["symbol"] = (df["symbol"].astype(str).str.upper().str.strip()
                    .str.replace(".", "-", regex=False))
    ev = df.drop_duplicates(subset=["symbol", "owner_cik", "filing_date", "code"]).copy()
    ev["fy"] = ev["filing_date"].dt.year
    ev["fmo"] = ev["filing_date"].dt.month
    ev["me"] = ev["filing_date"] + pd.offsets.MonthEnd(0)
    return ev, df


def classify(ev: pd.DataFrame) -> pd.Series:
    """Per event: 'R' routine / 'O' opportunistic / 'U' unclassified (PIT)."""
    hist = ev.groupby(["owner_cik", "issuer_cik", "fy"])["fmo"].agg(set)
    cls = {}
    for (o, i), yrs in hist.groupby(level=[0, 1]):
        ymap = {y: m for (_, _, y), m in yrs.items()}
        for y in range(min(ymap) + 3, 2027):
            prev = [ymap.get(y - k) for k in (1, 2, 3)]
            if all(p is not None for p in prev):
                cls[(o, i, y)] = "R" if set.intersection(*prev) else "O"
    idx = pd.MultiIndex.from_frame(ev[["owner_cik", "issuer_cik", "fy"]])
    return pd.Series([cls.get(k, "U") for k in idx], index=ev.index)


def npr_panel(ev: pd.DataFrame, me_index, syms) -> pd.DataFrame:
    c = ev.groupby(["me", "symbol", "code"]).size().unstack("code").fillna(0)
    P = c.get("P", pd.Series(dtype=float)).unstack("symbol") if "P" in c else None
    S = c.get("S", pd.Series(dtype=float)).unstack("symbol") if "S" in c else None
    P = (P if P is not None else pd.DataFrame()).reindex(index=me_index, columns=syms).fillna(0)
    S = (S if S is not None else pd.DataFrame()).reindex(index=me_index, columns=syms).fillna(0)
    P6, S6 = P.rolling(6).sum(), S.rolling(6).sum()
    tot = P6 + S6
    return ((P6 - S6) / tot.where(tot > 0)), tot


def decile_excess(char, fwd, sign, rt):
    held, rows = set(), []
    for t in char.index:
        s = (char.loc[t] * sign).dropna()
        if len(s) < 100:
            continue
        k = max(10, int(len(s) * 0.10))
        new = set(s.nlargest(k).index)
        f = fwd.loc[t, list(new)].dropna()
        ewm = fwd.loc[t].dropna()
        if f.empty or len(ewm) < 100:
            continue
        churn = (len(new - held) / max(len(new), 1)) if held else 1.0
        rows.append({"date": t, "ex_g": float(f.mean() - ewm.mean()),
                     "cost": churn * rt, "churn": churn})
        held = new
    return pd.DataFrame(rows).set_index("date")


def nwt(x):
    import statsmodels.api as sm
    x = pd.Series(x).dropna()
    r = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    return float(r.params[0]), float(r.tvalues[0])


def main():
    files = sorted(F4DIR.glob("*.parquet"))
    if len(files) < 81:
        print(f"form4 download incomplete ({len(files)}/81 quarters) -- F0 gate.")
        return

    print("=" * 104)
    print("TR-46  美國內部人 Form 4:機會型內部人淨買在本座位(S&P 500 成員,2015+)有定價力嗎?(docs/28 p2)")
    print("=" * 104)
    print("[trial accounting] +1 family(內部人三特徵,單一預先登記規格)")

    ev, raw = load_events()
    ev["cls"] = classify(ev)

    # ---- price panel (TR-34 verbatim) ----
    store = DuckStore("./data")
    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    me = px.resample("ME").last().loc[START:]
    ret_m = me.pct_change()
    fwd = ret_m.shift(-1)
    mem = load_membership()
    mm = member_mask(px.index, syms, mem).resample("ME").last().reindex(me.index).astype(bool)
    fwd = fwd.where(mm)

    # ---- CAL ----
    df_v = raw.assign(val=lambda d: d["shares"] * d["price"].fillna(0))
    yearly = df_v.groupby([df_v["filing_date"].dt.year, "code"])["val"].sum().unstack()
    ratio = (yearly["S"] / yearly["P"]).replace([np.inf, -np.inf], np.nan).dropna()
    cal_a = 2 <= float(ratio.median()) <= 20
    print(f"CAL a:年度市場賣/買金額比中位 {ratio.median():.1f}(帶 [2,20]) -> "
          f"{'PASS' if cal_a else 'FAIL'}")
    joined = raw["filing_date"].notna() & raw["symbol"].notna() & raw["relationship"].notna()
    cal_b = float(joined.mean()) >= 0.99
    print(f"CAL b:三表 join 完整率 {joined.mean()*100:.2f}%(門檻 99%) -> "
          f"{'PASS' if cal_b else 'FAIL'}")
    me_all = pd.date_range("2006-01-31", ev["me"].max(), freq="ME")
    mc = ev.groupby(["me", "code"]).size().unstack().reindex(me_all).fillna(0)
    npr_mkt = (mc["P"] - mc["S"]) / (mc["P"] + mc["S"]).where(lambda x: x > 0)
    v2003 = float(npr_mkt.loc["2020-03-31"])
    q90 = float(npr_mkt.quantile(0.90))
    npr6, act6 = npr_panel(ev[ev["symbol"].isin(syms)], me.index, syms)
    npr6 = npr6.where(mm)
    cov = npr6.notna().sum(axis=1)
    cal_c = (float(cov.median()) >= 250) and (v2003 >= q90)
    print(f"CAL c:npr6 覆蓋中位 {int(cov.median())} 檔/月(門檻 250);2020-03 全市場 NPR "
          f"{v2003:+.3f} vs P90 {q90:+.3f}({'≥' if v2003 >= q90 else '<'}) -> "
          f"{'PASS' if cal_c else 'FAIL'}")
    if not (cal_a and cal_b and cal_c):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 ----
    sub = ev[ev["symbol"].isin(syms)]
    opp6, _ = npr_panel(sub[sub["cls"] == "O"], me.index, syms)
    rou6, _ = npr_panel(sub[sub["cls"] == "R"], me.index, syms)
    trio = {"npr6": rank_std(npr6),
            "opp6": rank_std(opp6.where(mm)),
            "rou6": rank_std(rou6.where(mm))}
    print("-" * 104)
    print("C1 三個單變量 FM(月頻,NW t):")
    c1 = {}
    for k, mn in (("npr6", 100), ("opp6", 100), ("rou6", 50)):
        sl = fm_slopes({k: trio[k]}, fwd, min_n=mn)
        m, t = (nw_mean_t(sl[k]) if k in sl else (np.nan, np.nan))
        nmed = int(trio[k].notna().sum(axis=1).median())
        c1[k] = (m, t)
        tag = " <-- 候選(|t|>=2)" if (np.isfinite(t) and abs(t) >= 2) else ""
        print(f"  {k:<6} 斜率 {m*1e4:+7.1f} bps/mo  t={t:+5.2f}(中位覆蓋 {nmed}/mo){tag}")
    cmp_pattern = (np.isfinite(c1['opp6'][1]) and abs(c1['opp6'][1]) >= 2
                   and c1['opp6'][0] > c1['rou6'][0] and abs(c1['rou6'][1]) < 2)

    # ---- C2 opp6 + TR-34 six characteristics ----
    print("-" * 104)
    print("C2 opp6 × TR-34 六特徵聯合 FM(獨立性):")
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0]
    fund = store.load_fundamentals(syms)
    syms_f = [s for s in syms if s in set(fund["symbol"])]
    gp = build_all(fund, px, syms_f)["gross_profitability"].resample("ME").last().reindex(me.index)
    sh = shares_panel(fund, px.index, syms_f)
    mcap = (sh * px[syms_f]).resample("ME").last().reindex(me.index)
    se = pit_panel(fund, "StockholdersEquity", px.index, syms_f)
    bm = (se.resample("ME").last().reindex(me.index) / mcap).where(lambda x: x > 0)
    beta = (px[syms_f].pct_change().rolling(252).cov(spy.pct_change())
            .div(spy.pct_change().rolling(252).var(), axis=0)
            .resample("ME").last().reindex(me.index))
    six_raw = {"gp": gp, "logmcap": np.log(mcap.where(mcap > 0)), "bm": bm,
               "mom122": me[syms_f].shift(2) / me[syms_f].shift(12) - 1,
               "str1m": ret_m[syms_f], "beta252": beta}
    six = {k: rank_std(v.where(mm[syms_f])) for k, v in six_raw.items()}
    sl8 = fm_slopes({**six, "opp6": trio["opp6"][syms_f]}, fwd[syms_f], min_n=100)
    for k in list(six) + ["opp6"]:
        m, t = nw_mean_t(sl8[k])
        print(f"  {k:<8} {m*1e4:+7.1f} bps/mo  t={t:+5.2f}")
    m8, t8 = nw_mean_t(sl8["opp6"])

    # ---- C3 cost gate (excess basis) ----
    print("-" * 104)
    print("C3 成本關卡(超額基準,10bps RT + 2x 壓力):")
    c3 = {}
    for k in TRIO:
        if not (np.isfinite(c1[k][1]) and abs(c1[k][1]) >= 2):
            continue
        sgn = int(np.sign(c1[k][0]))
        base = decile_excess(trio[k], fwd, sgn, RT_COST)
        for lab, rt in (("base 10bps", RT_COST), ("stress 20bps", 2 * RT_COST)):
            net = base["ex_g"] - base["churn"] * rt
            nm, nt = nwt(net)
            gm, gt = nwt(base["ex_g"])
            tier = ("SURVIVES-COSTS" if (nt >= 2 and nm > 0) else
                    "MARGINAL" if (nm > 0 or nt >= 1) else "FAILS-COSTS")
            if lab.startswith("base"):
                c3[k] = (gm * 12, nm * 12, nt, tier, base)
            print(f"  {k:<6} [{lab}] 超額毛 {gm*12*100:+5.2f}%/yr(t={gt:+.2f}) "
                  f"淨 {nm*12*100:+5.2f}%/yr(t={nt:+.2f}) -> {tier}"
                  f"(中位換手 {base['churn'].median()*100:.0f}%/mo)")

    # ---- C4 subperiod + activity ----
    print("-" * 104)
    print("C4 分期(F7)與活動診斷:")
    c4 = {}
    for k in TRIO:
        sl = fm_slopes({k: trio[k]}, fwd, min_n=(50 if k == "rou6" else 100))
        if k not in sl:
            continue
        a = sl[k].loc[:"2020-12-31"]
        b = sl[k].loc["2021-01-01":]
        ma, ta = nwt(a)
        mb, tb = nwt(b)
        c4[k] = (ma, ta, mb, tb)
        print(f"  {k:<6} 2015-2020:{ma*1e4:+7.1f}(t={ta:+.2f}) | 2021+:{mb*1e4:+7.1f}(t={tb:+.2f})")
    share = ev["cls"].value_counts(normalize=True)
    print(f"  事件分類占比:O {share.get('O',0)*100:.0f}% / R {share.get('R',0)*100:.0f}% / "
          f"U {share.get('U',0)*100:.0f}%(U 僅入 npr6);officer/director 事件總數 {len(ev):,}")

    # ---- verdict ----
    print("=" * 104)
    opp_t = c1["opp6"][1]
    if np.isfinite(opp_t) and abs(opp_t) >= 2 and cmp_pattern:
        tier = c3.get("opp6", (0, 0, 0, "FAILS-COSTS", None))[3]
        v = (f"SIGNAL -- opp6 過成本關卡" if tier == "SURVIVES-COSTS"
             else f"MECHANISM-CONFIRMED / {tier} -- CMP 型態成立但成本後不乾淨")
    elif np.isfinite(opp_t) and abs(opp_t) >= 2:
        v = "GENERIC-ACTIVITY -- opp 與 rou 相當,是活動效應不是資訊通道"
    else:
        v = ("NO-SIGNAL -- opp6 |t|<2:機會型內部人淨買在本座位(美大型股 2015+)無定價力;"
             "與文獻的規模依賴一致,小型股腿屬 p3")
    print(f"VERDICT: {v}")

    # ---- chart ----
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    ax = axes[0, 0]
    ts = [c1[k][1] for k in TRIO]
    ax.bar(TRIO, ts, color=["#2e7d32" if (np.isfinite(t) and abs(t) >= 2) else "#90a4ae" for t in ts])
    ax.axhline(2, ls="--", c="k", lw=0.8); ax.axhline(-2, ls="--", c="k", lw=0.8)
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title("C1 內部人三特徵單變量 FM t 值(npr/opp/rou)")
    ax = axes[0, 1]
    ax.bar(["opp6 單變量", "opp6+六控制"], [c1["opp6"][0] * 1e4, m8 * 1e4], color="#1565c0")
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title(f"C2 opp6 斜率:單變量 vs 加控制(t={c1['opp6'][1]:+.2f} → {t8:+.2f})")
    ax = axes[1, 0]
    if "opp6" in c3:
        cum = (1 + c3["opp6"][4]["ex_g"] - c3["opp6"][4]["churn"] * RT_COST).cumprod()
        ax.plot(cum.index, cum, color="#1565c0")
        ax.set_title("C3 opp6 頂十分位超額淨值(vs 成員等權)")
    else:
        ax.text(0.5, 0.5, "無 |t|>=2 候選 → 無成本關卡", ha="center", va="center")
        ax.set_title("C3 成本關卡")
    ax = axes[1, 1]
    labs, v15, v21 = [], [], []
    for k in TRIO:
        if k in c4:
            labs.append(k); v15.append(c4[k][0] * 1e4); v21.append(c4[k][2] * 1e4)
    x = np.arange(len(labs)); w = 0.38
    ax.bar(x - w / 2, v15, w, label="2015-2020", color="#546e7a")
    ax.bar(x + w / 2, v21, w, label="2021+", color="#f9a825")
    ax.set_xticks(x); ax.set_xticklabels(labs); ax.legend(); ax.axhline(0, c="k", lw=0.6)
    ax.set_title("C4 分期斜率(bps/mo)")
    fig.suptitle("TR-46 美國內部人 Form 4:CMP 機會型/例行拆解(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr46_us_insiders.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
