# -*- coding: utf-8 -*-
"""TR-45 -- Taiwan chip line (docs/27 b7 / docs/28 p1): who drives the continuation
market, and is there one clean tradable candidate in it?

PRE-REGISTERED while the chip drip is still running (F0 committed before any chip
parquet was inspected beyond a 2330 schema probe). The Taiwan arc (TR-39..44) ended
with: mechanism real (mom122/avol/logdv all significant, cliff+barbell ladder), but
every candidate MARGINAL net of full costs on total-return prices. Two questions
remain, and this TR answers both with ONE pre-registered family:
  (1) ATTRIBUTION -- our "continuation market" story (mom+, avol+) implies herding.
      Whose? Institutional flow data shows the counterparty structure directly.
  (2) ONE MORE SHOT -- chip information is the strongest-prior UNUSED dimension in
      the only habitat where our cross-section is alive (Barber-Lee-Liu-Odean line).

F0 DECLARATION (pre-committed)
  Family : +1 (Taiwan chip trio; single spec, no grid). Trading direction in C3
           follows the FITTED C1 slope sign (declared now to kill HARKing room).
  Seat   : TWSE 4-digit commons, TR-39b machinery (delisted truncated at official
           dates), TOTAL-RETURN prices (TR-44 basis: px_tr = px_raw * adj),
           monthly FM 2014+, min_n=300. Same-window principle: identical panel
           window as TR-39..44.
  Chip characteristics (exactly three; constructions fixed):
    fnet60  = sum_60d[(foreign buy - sell shares) x raw close] / sum_60d[trading
              value], month-end sample, min 40/60 days. foreign = Foreign_Investor
              + Foreign_Dealer_Self. Prior: + (flow continuation).
    itnet60 = same for Investment_Trust. Prior: + (trust sponsorship).
    dmgn60  = margin utilization (TodayBalance/Limit, lots/lots) minus its value 60
              trading days earlier. Prior: - (retail leverage crowding reverses).
    Short-sale columns are collected but NOT in the family. Flow NaN on alive days
    -> 0 ONLY for names whose flow parquet exists (a missing row for a covered name
    means no institutional activity); names with no flow file at all stay NaN
    (data gap, not a true zero). Margin ffill limit 10 days, dead days masked.
  CAL (fail any -> STOP):
    a) bottom-up market foreign net-buy VALUE (sum shares x raw close, monthly) vs
       published TaiwanStockTotalInstitutionalInvestors aggregate: corr >= 0.90.
       Threshold set at 0.90 NOT 0.95 for a reason declared NOW: our panel is
       4-digit commons only, the published aggregate is ALL listed securities
       (ETFs/TDRs/preferred included) -- a known scope gap, not machine error.
    b) margin identity today = yesterday + buy - sell - cash_repayment within
       +/-5 lots on >= 99% of rows (unit/parse fidelity).
    c) joint 8-char coverage (trio + FIVE) >= 500 names/month in >= 90% of panel
       months (500 not 600: the margin-eligible subset is structurally smaller
       than the price universe; declared before seeing coverage).
  C1 : joint FM of the trio alone. Candidate tier: |t| >= 2.
  C2 : joint FM trio + FIVE on common months vs FIVE-only baseline. Pre-stated
       readout: does mom122/avol attenuate > 1/3 when flows enter? (= the
       continuation premium IS institutional-flow-carried).
  C3 : each C1 candidate -> top-decile portfolio at fitted-sign direction, tick
       spread model (TR-40, 2-tick base), full commission + sell tax, monthly step,
       total-return fwd. Tiers: net t >= 2 SURVIVES-COSTS; net > 0 or t in [1,2)
       MARGINAL; else FAILS-COSTS. Plus 10-decile gross ladder.
  C4 : descriptive attribution -- (i) mean cross-sectional Spearman corr of trio vs
       FIVE; (ii) median trio values inside the logdv-D1 (coldest) bucket: who
       trades the cold corner where the premium lives.
  Verdict routing (pre-committed):
    >=1 trio char |t|>=2 AND C3 SURVIVES  -> SIGNAL (first clean tradable candidate)
    >=1 trio char |t|>=2, C3 not clean    -> MECHANISM-CONFIRMED / MARGINAL
    none |t|>=2                           -> NO-SIGNAL (C2/C4 attribution stands)
  Honest bounds pre-stated: per-stock flow history starts 2012-05 (API-verified;
  shorter than the price panel needs nothing -- window 2014+ is fully covered);
  monthly clock rules out same-day flow-return endogeneity but intramonth feedback
  remains -- slopes are predictive associations, attribution is the primary
  deliverable; margin data only exists for marginable names (structural, not
  survivorship); trial accounting +1.
  GATE: abort unless chip state has >= 1150 attempted names.

Run: uv run python scripts/tests/tr45_taiwan_chips.py   (after the chip drip)
Chart: docs/tests/img/tr45_taiwan_chips.png
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
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")
sys.path.insert(0, "scripts/collect")

from finmind_tw_chips import flow_panels, margin_panels, total_instit_monthly  # noqa: E402
from finmind_tw_dividends import adjustment_panel  # noqa: E402
from tr34_fama_macbeth import fm_slopes, nw_mean_t, rank_std  # noqa: E402
from tr39_taiwan_panel import DATA, load_panels  # noqa: E402
from tr39b_taiwan_delisted import FIVE, build_chars  # noqa: E402
from tr40_taiwan_cost_gate import (  # noqa: E402
    COMMISSION_FULL, decile_portfolio, nw_t, tick_spread_monthly)

TRIO = ("fnet60", "itnet60", "dmgn60")
MULT = 2.0                     # tick-spread base (TR-40 convention)
plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def build_chip_chars(px_raw, dv, idx, cols):
    """Monthly chip characteristics on the daily trading-day index of px_raw."""
    dates = px_raw.index
    alive = px_raw.notna()
    fnet, itnet = flow_panels(dates, px_raw.columns)
    bal, lim, resid_ok, resid_n = margin_panels(dates, px_raw.columns)

    def alive_zero_fill(x):
        loaded = x.columns[x.notna().any()]
        x = x.copy()
        x[loaded] = x[loaded].fillna(0.0).where(alive[loaded])
        x.loc[:pd.Timestamp("2012-06-01")] = np.nan
        return x

    fnet, itnet = alive_zero_fill(fnet), alive_zero_fill(itnet)
    fval = fnet * px_raw            # net buy value, NT$ (raw close: actual prices)
    itval = itnet * px_raw
    dvv = dv.where(dv > 0)

    def ratio60(num):
        return (num.rolling(60, min_periods=40).sum()
                / dvv.rolling(60, min_periods=40).sum().where(lambda x: x > 0))

    u = (bal.ffill(limit=10) / lim.ffill(limit=10).where(lambda x: x > 0)).where(alive)
    chars = {
        "fnet60": ratio60(fval),
        "itnet60": ratio60(itval),
        "dmgn60": u - u.shift(60),
    }
    out = {k: rank_std(v.resample("ME").last().reindex(idx)[cols]) for k, v in chars.items()}
    return out, fval, resid_ok, resid_n


def main():
    st_p = Path("data/_finmind_tw_chips_state.json")
    if not st_p.exists():
        print("chip drip not started -- run scripts/collect/finmind_tw_chips.py")
        return
    st = json.loads(st_p.read_text())
    if len(st["done"]) < 1150:
        print(f"chip drip incomplete ({len(st['done'])} attempted) -- F0 gate: TR-45 "
              f"fires only on >=1150.")
        return

    # ---- panel assembly: byte-identical recipe to TR-44 ----
    man = pd.read_csv(DATA / "delisted.csv", dtype={"stock_id": str})
    px_raw, dv, pbr, per = load_panels()
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px_raw.columns:
            px_raw.loc[px_raw.index > dd, sid] = np.nan
            dv.loc[dv.index > dd, sid] = np.nan
    adj = adjustment_panel(px_raw.index, px_raw.columns)
    px_tr = px_raw * adj

    print("=" * 104)
    print("TR-45  台股籌碼線:誰在推「延續市場」?有沒有一個乾淨的可交易候選?(docs/27 b7)")
    print("=" * 104)
    print(f"[trial accounting] +1 family(籌碼三特徵,單一預先登記規格)")

    chars, fwd, _rm, dv_f, me = build_chars(px_tr, dv, pbr, include_bp=False)
    idx, cols = chars["mom122"].index, chars["mom122"].columns
    trio, fval, resid_ok, resid_n = build_chip_chars(
        px_raw[cols], dv[cols], idx, cols)

    # ---- CAL ----
    bottom_up = fval[cols].sum(axis=1).resample("ME").sum().loc["2014":]
    pub = total_instit_monthly()
    pub_f = sum(pub[c] for c in ("Foreign_Investor", "Foreign_Dealer_Self")
                if c in pub.columns).loc["2014":]
    common = bottom_up.index.intersection(pub_f.index)
    cal_a = float(np.corrcoef(bottom_up.loc[common], pub_f.loc[common])[0, 1])
    ok_a = cal_a >= 0.90
    print(f"CAL a:bottom-up 外資淨買金額 vs 官方聚合 corr {cal_a:+.3f}(門檻 0.90,"
          f"範圍差=普通股 vs 全部上市證券) -> {'PASS' if ok_a else 'FAIL'}")
    share_ok = resid_ok / max(resid_n, 1)
    ok_b = share_ok >= 0.99
    print(f"CAL b:融資逐日恆等式 |resid|<=5 張比率 {share_ok*100:.2f}%(n={resid_n:,},"
          f"門檻 99%) -> {'PASS' if ok_b else 'FAIL'}")
    # joint-coverage count: months where all 8 chars are present per name
    mask = None
    for k in list(FIVE) + list(TRIO):
        m = (chars[k] if k in FIVE else trio[k]).notna()
        mask = m if mask is None else (mask & m)
    per_month = mask.sum(axis=1)
    ok_c = (per_month >= 500).mean() >= 0.90
    print(f"CAL c:八特徵聯合覆蓋中位 {int(per_month.median())} 檔/月,"
          f">=500 的月份比率 {(per_month>=500).mean()*100:.0f}%(門檻 90%) -> "
          f"{'PASS' if ok_c else 'FAIL'}")
    if not (ok_a and ok_b and ok_c):
        print("VERDICT: INVALID-TEST -- CAL 未過,先修機器再判。")
        return

    # ---- C1 trio-only FM ----
    print("-" * 104)
    print("C1 籌碼三特徵聯合 FM(月頻,NW t):")
    sl1 = fm_slopes(dict(trio), fwd, min_n=300)
    c1 = {}
    for k in TRIO:
        m, t = nw_mean_t(sl1[k])
        c1[k] = (m, t)
        tag = " <-- 候選(|t|>=2)" if abs(t) >= 2 else ""
        print(f"  {k:<8} 斜率 {m*1e4:+7.1f} bps/mo  t={t:+5.2f}{tag}")

    # ---- C2 trio + FIVE vs FIVE-only ----
    print("-" * 104)
    print("C2 八特徵聯合 FM vs 五特徵基準(共同月份;預先陳述的判讀:mom/avol 衰減>1/3?):")
    sl8 = fm_slopes({**{k: chars[k] for k in FIVE}, **dict(trio)}, fwd, min_n=300)
    sl5 = fm_slopes({k: chars[k] for k in FIVE}, fwd, min_n=300)
    mm = sl8.index.intersection(sl5.index)
    atten = {}
    for k in FIVE:
        m5, t5 = nw_mean_t(sl5.loc[mm, k])
        m8, t8 = nw_mean_t(sl8.loc[mm, k])
        att = 1 - (m8 / m5) if m5 not in (0,) else np.nan
        atten[k] = (m5, t5, m8, t8, att)
        flag = "  <-- 衰減>1/3" if (np.isfinite(att) and att > 1/3 and abs(t5) >= 2) else ""
        print(f"  {k:<8} 五特徵 {m5*1e4:+7.1f}(t={t5:+5.2f}) -> 八特徵 "
              f"{m8*1e4:+7.1f}(t={t8:+5.2f})  衰減 {att*100:+5.0f}%{flag}")
    for k in TRIO:
        m8, t8 = nw_mean_t(sl8.loc[mm, k])
        print(f"  {k:<8} (八特徵內) {m8*1e4:+7.1f}(t={t8:+5.2f})")

    # ---- C3 cost gate on C1 candidates ----
    print("-" * 104)
    print("C3 成本關卡(tick 價差模型 2 跳、全額手續費+證交稅、月頻、總報酬 fwd):")
    spread_m = tick_spread_monthly(px_raw[cols], MULT).reindex(idx)
    c3 = {}
    for k in TRIO:
        if abs(c1[k][1]) < 2:
            continue
        sgn = int(np.sign(c1[k][0]))
        port = decile_portfolio(trio[k], fwd, sgn, spread_m, 1, COMMISSION_FULL)
        net = port["gross"] - port["cost"]
        g_ann, n_ann = float(port["gross"].mean() * 12), float(net.mean() * 12)
        _, t_net = nw_t(net)
        tier = ("SURVIVES-COSTS" if t_net >= 2 else
                "MARGINAL" if (n_ann > 0 or t_net >= 1) else "FAILS-COSTS")
        c3[k] = (g_ann, n_ann, t_net, tier, net)
        print(f"  {k:<8} 方向 {sgn:+d}  毛 {g_ann*100:+5.2f}%/yr  淨 {n_ann*100:+5.2f}%/yr"
              f"  t(淨)={t_net:+5.2f}  -> {tier}(中位換手 {port['churn'].median()*100:.0f}%/mo)")
        lad = []
        for d in range(10):
            lo, hi = d / 10, (d + 1) / 10
            r = []
            for t_ in trio[k].index:
                s = (trio[k].loc[t_] * sgn).dropna()
                if len(s) < 300:
                    continue
                sel = s[(s.rank(pct=True) > lo) & (s.rank(pct=True) <= hi)].index
                f = fwd.loc[t_, sel].dropna()
                if len(f):
                    r.append(f.mean())
            lad.append(np.mean(r) * 12 * 100 if r else np.nan)
        c3[k] = (*c3[k], lad)
        print(f"    十分位毛梯(D10 最強→D1):{' '.join(f'{v:+.1f}' for v in lad[::-1])}")

    # ---- C4 attribution ----
    print("-" * 104)
    print("C4 機制歸因(描述性):")
    corr_rows = {}
    for k in TRIO:
        cc = {}
        for f5 in FIVE:
            cs = [trio[k].loc[t_].corr(chars[f5].loc[t_], method="spearman")
                  for t_ in idx[::3]]
            cc[f5] = float(np.nanmean(cs))
        corr_rows[k] = cc
        print(f"  corr({k:<8} , FIVE): " + "  ".join(f"{f5} {v:+.2f}" for f5, v in cc.items()))
    d1 = {}
    liq = chars["logdv"]
    for k in TRIO:
        vals = []
        for t_ in idx:
            s = liq.loc[t_].dropna()
            if len(s) < 300:
                continue
            cold = s[s.rank(pct=True) <= 0.10].index
            v = trio[k].loc[t_, cold].dropna()
            if len(v):
                vals.append(v.median())
        d1[k] = float(np.nanmean(vals)) if vals else np.nan
        print(f"  logdv-D1 最冷門桶的 {k} 中位標準化值:{d1[k]:+.2f}"
              f"({'高於' if d1[k]>0 else '低於'}市場中位)")

    # ---- verdict ----
    print("=" * 104)
    cands = [k for k in TRIO if abs(c1[k][1]) >= 2]
    surv = [k for k in cands if k in c3 and c3[k][3] == "SURVIVES-COSTS"]
    if surv:
        v = f"SIGNAL -- {','.join(surv)} 過全額成本關卡(台股線第一個乾淨候選)"
    elif cands:
        v = f"MECHANISM-CONFIRMED / MARGINAL -- {','.join(cands)} |t|>=2 但成本後不乾淨"
    else:
        v = "NO-SIGNAL -- 三特徵皆 |t|<2;C2/C4 歸因為本 TR 的交付"
    print(f"VERDICT: {v}")

    # ---- chart ----
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    ax = axes[0, 0]
    ts = [c1[k][1] for k in TRIO]
    ax.bar(TRIO, ts, color=["#2e7d32" if abs(t) >= 2 else "#90a4ae" for t in ts])
    ax.axhline(2, ls="--", c="k", lw=0.8); ax.axhline(-2, ls="--", c="k", lw=0.8)
    ax.set_title("C1 籌碼三特徵 FM t 值"); ax.axhline(0, c="k", lw=0.6)
    ax = axes[0, 1]
    x = np.arange(len(FIVE)); w = 0.38
    ax.bar(x - w/2, [atten[k][0]*1e4 for k in FIVE], w, label="五特徵", color="#546e7a")
    ax.bar(x + w/2, [atten[k][2]*1e4 for k in FIVE], w, label="加籌碼後", color="#f9a825")
    ax.set_xticks(x); ax.set_xticklabels(FIVE, fontsize=8); ax.legend()
    ax.set_title("C2 既有候選斜率:加入籌碼前後(bps/mo)")
    ax = axes[1, 0]
    if c3:
        k0 = (surv or cands)[0]
        lad = c3[k0][5]
        ax.bar(range(1, 11), lad, color="#1565c0")
        ax.set_title(f"C3 {k0} 十分位毛報酬階梯(%/yr,D10=最強)")
        ax.set_xlabel("decile(依 fitted 方向)")
    else:
        ax.text(0.5, 0.5, "無 |t|>=2 候選 → 無成本關卡", ha="center", va="center")
        ax.set_title("C3 成本關卡")
    ax = axes[1, 1]
    ax.bar(TRIO, [d1[k] for k in TRIO], color="#6a1b9a")
    ax.axhline(0, c="k", lw=0.6)
    ax.set_title("C4 最冷門(logdv-D1)桶的籌碼特徵中位標準化值")
    fig.suptitle("TR-45 台股籌碼線:歸因+一發可交易候選(F0 預先登記)", fontsize=13)
    fig.tight_layout()
    out = Path("docs/tests/img/tr45_taiwan_chips.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"[chart] {out}")


if __name__ == "__main__":
    main()
