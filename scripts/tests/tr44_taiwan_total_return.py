"""TR-44 -- do the Taiwan verdicts survive total-return prices? (docs/27 b6)

TR-39/39b/40/41 all ran on RAW closes. Taiwan cash yields are large (the allocation lab
measured +2.49%/yr on 0050) and -- this is the part that matters -- they are NOT uniform
across the liquidity ladder. If high-yield names cluster in one decile, the price-only
panel has a SYSTEMATIC level error in exactly the dimension TR-41 sorted on.

Direction is NOT obvious a priori, and the F0 says so before the data is seen:
  - if illiquid small caps are HIGH yield, the raw panel UNDERSTATES D1 -> the premium
    is even bigger than TR-40/41 reported;
  - if they are LOW yield (growth/loss-making micro caps often pay nothing) while the
    liquid megacaps pay well, the raw panel OVERSTATES D1 -> part of the "premium" was
    simply dividends missing from the benchmark's competitors.
Both are live hypotheses. This TR measures it instead of assuming.

ADJUSTMENT: FinMind TaiwanStockDividendResult gives official before/after reference
prices per ex-date; factor = after/before; back-adjusted total-return price =
raw / (product of factors strictly after t). Same convention as Yahoo auto_adjust.

F0 DECLARATION (pre-committed)
  claim  : the Taiwan verdicts (TR-39b's three confirmed characteristics, TR-40's cost
         gate, TR-41's concentration) are level-sensitive but VERDICT-STABLE under
         total-return prices.
  CAL    : (a) adjustment sanity -- the panel-median annualized dividend drag must land
         in [0.5%, 6%]/yr (Taiwan market yield is ~2-4%); (b) 0050's own adjusted-vs-raw
         CAGR gap must reproduce the allocation lab's +2.49%/yr within +-1.0pp.
         Fail -> STOP (adjustment machinery wrong).
  C1     : yield BY LIQUIDITY DECILE -- the diagnostic that decides which way the bias
         runs. Reported first because it makes everything else interpretable.
  C2 (decisive): re-run TR-39b's joint FM panel on total-return prices. Verdict-stable
         iff mom122/avol/logdv keep sign AND |t| >= 2 (the TR-39b confirmation bar).
  C3     : re-run TR-40's cost gate and TR-41's decile ladder on total-return prices:
         does logdv still survive costs, and is the premium still CONCENTRATED?
  C4     : bp (book-to-price) was the one characteristic that just missed at t=1.87 in
         TR-39 -- dividends bias value factors most, so this is where a verdict could
         legitimately FLIP. Reported; promotion still requires the pre-registered
         |t| >= 2 AND it must be labelled a fresh finding, not a rescued one.
  anti-HARKing : all thresholds inherited unchanged from TR-39b/40/41; no re-tuning;
         trials +0 (same Taiwan family, corrected price basis).

Run: uv run python scripts/tests/tr44_taiwan_total_return.py   (after the dividend drip)
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
sys.path.insert(0, "scripts/collect")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from finmind_tw_dividends import adjustment_panel  # noqa: E402
from tr34_fama_macbeth import fm_slopes, nw_mean_t  # noqa: E402
from tr39_taiwan_panel import DATA, load_panels  # noqa: E402
from tr39b_taiwan_delisted import FIVE, build_chars  # noqa: E402
from tr40_taiwan_cost_gate import CANDIDATES  # signed dict {name: +/-1}  # noqa: E402
from tr40_taiwan_cost_gate import (  # noqa: E402
    COMMISSION_FULL,
    TAX_SELL,
    decile_portfolio,
    load_hilo,
    tick_spread_monthly,
)

MULT = 2.0


def main():
    div_state = Path("data/_finmind_tw_div_state.json")
    if not div_state.exists():
        print("dividend drip not started -- run scripts/collect/finmind_tw_dividends.py")
        return
    st = json.loads(div_state.read_text())
    covered = len(st["done"]) + len(st["none"])
    if covered < 1200:
        print(f"dividend drip incomplete ({covered}/1220 attempted) -- F0 gate: TR-44 "
              f"fires only on full coverage.")
        return

    man = pd.read_csv(DATA / "delisted.csv", dtype={"stock_id": str})
    px_raw, dv, pbr, per = load_panels()
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px_raw.columns:
            px_raw.loc[px_raw.index > dd, sid] = np.nan
            dv.loc[dv.index > dd, sid] = np.nan
    adj = adjustment_panel(px_raw.index, px_raw.columns)
    px_tr = px_raw * adj          # back-adjusted total-return price (multiply; see CAL-a)

    print("=" * 104)
    print("TR-44  台股判定在還原股價下還成立嗎?(docs/27 b6)")
    print("=" * 104)

    # ---- CAL ----
    yrs = (px_raw.index[-1] - px_raw.index[0]).days / 365.25
    # annualized dividend "lift" of TR over raw = (1/factor_at_start)^(1/yrs) - 1, since
    # factor(start) <= 1 scales the oldest price down. Positive by construction if events exist.
    drag = (1.0 / adj.iloc[0].replace(0, np.nan)) ** (1 / yrs) - 1
    med_drag = float(drag.median())
    cal_a = 0.005 <= med_drag <= 0.06
    print(f"CAL a:面板中位股利拖累 {med_drag*100:.2f}%/yr(帶 0.5-6%) -> "
          f"{'PASS' if cal_a else 'FAIL'}")
    cal_b = True
    if "0050" in px_raw.columns:
        g_raw = float((px_raw["0050"].dropna().iloc[-1] / px_raw["0050"].dropna().iloc[0])
                      ** (1 / yrs) - 1)
        g_tr = float((px_tr["0050"].dropna().iloc[-1] / px_tr["0050"].dropna().iloc[0])
                     ** (1 / yrs) - 1)
        gap = g_tr - g_raw
        cal_b = abs(gap - 0.0249) <= 0.010
        print(f"CAL b:0050 還原 vs 未還原 CAGR 差 {gap*100:+.2f}%/yr(錨 +2.49%,±1.0pp) "
              f"-> {'PASS' if cal_b else 'FAIL'}")
    else:
        print("CAL b:0050 不在面板(ETF 不在普通股宇宙)——以 CAL a 為準")
    if not (cal_a and cal_b):
        print("VERDICT: INVALID-TEST -- 還原機器有誤,先修再判。")
        return

    # ---- C1 yield by liquidity decile (the interpretive key) ----
    chars_raw, fwd_raw, _rm, dv_p, _me = build_chars(px_raw, dv, pbr, include_bp=False)
    liq = chars_raw["logdv"]
    print("-" * 104)
    print("C1 股利率 × 流動性分位(決定偏誤方向的診斷):")
    last = liq.iloc[-1].dropna()
    for d, (lo, hi) in enumerate([(0.9, 1.0), (0.5, 0.9), (0.1, 0.5), (0.0, 0.1)], 1):
        sel = last[(last >= last.quantile(lo)) & (last <= last.quantile(hi))].index if lo < hi else []
        vals = drag.reindex(sel).dropna()
        lab = {1: "D10 最流動", 2: "中上", 3: "中下", 4: "D1 最不流動"}[d]
        if len(vals):
            print(f"  {lab:<12}: 中位股利拖累 {vals.median()*100:5.2f}%/yr(n={len(vals)})")

    # ---- C2 joint FM on total-return ----
    chars_tr, fwd_tr, *_ = build_chars(px_tr, dv, pbr, include_bp=False)
    sl_raw = fm_slopes({k: chars_raw[k] for k in FIVE}, fwd_raw, min_n=300)
    sl_tr = fm_slopes({k: chars_tr[k] for k in FIVE}, fwd_tr, min_n=300)
    print("-" * 104)
    print("C2 聯合 FM:未還原 → 還原")
    stable = True
    for k in FIVE:
        m0, t0 = nw_mean_t(sl_raw[k])
        m1, t1 = nw_mean_t(sl_tr[k])
        tag = ""
        if k in CANDIDATES:
            ok = (np.sign(m1) == np.sign(m0)) and abs(t1) >= 2
            stable &= ok
            tag = "  <-- 候選:" + ("穩定" if ok else "**判定改變**")
        print(f"  {k:7s}: {m0*1e4:+7.1f}bps (t={t0:+.2f}) → {m1*1e4:+7.1f}bps "
              f"(t={t1:+.2f}){tag}")

    # ---- C3 cost gate + ladder on total-return ----
    H, L, C = load_hilo(set(chars_tr["logdv"].columns))
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        for X in (H, L, C):
            if sid in X.columns:
                X.loc[X.index > dd, sid] = np.nan
    spread_m = tick_spread_monthly(C, MULT).reindex(chars_tr["logdv"].index) \
        .reindex(columns=chars_tr["logdv"].columns)
    ew_tr = fwd_tr.mean(axis=1)
    print("-" * 104)
    print("C3 成本關卡(還原後)與十分位階梯:")
    for name, sign in CANDIDATES.items():
        d = decile_portfolio(chars_tr[name], fwd_tr, sign, spread_m, 1, COMMISSION_FULL)
        net = (d["gross"] - ew_tr.reindex(d.index)) - d["cost"]
        m, t = nw_mean_t(net)
        print(f"  {name:7s}: 淨超額 {m*12*100:+6.2f}%/yr (t={t:+.2f})")
    illiq = -chars_tr["logdv"]
    ladder = []
    for dd_ in range(1, 11):
        def pick(s, d=dd_):
            return s[(s <= s.quantile(1 - (d - 1) * 0.1)) & (s > s.quantile(1 - d * 0.1))].index
        r = decile_portfolio(illiq, fwd_tr, 1, spread_m, 1, COMMISSION_FULL) if False else None
        del r
        from tr41_taiwan_bucket_economics import bucket_returns
        rr = bucket_returns(illiq, fwd_tr, spread_m, pick)
        m, _t = nw_mean_t(rr["net"] - ew_tr.reindex(rr.index))
        ladder.append(m * 12)
    print("  階梯 D1→D10: " + " | ".join(f"{v*100:+.1f}" for v in ladder))
    concentrated = ladder[0] > 0 and sum(1 for v in ladder[1:5] if v < ladder[0] / 2) >= 3

    # ---- C4 bp ----
    chars_bp_raw, fwd_b_raw, *_ = build_chars(px_raw, dv, pbr, include_bp=True)
    chars_bp_tr, fwd_b_tr, *_ = build_chars(px_tr, dv, pbr, include_bp=True)
    b0 = nw_mean_t(fm_slopes(chars_bp_raw, fwd_b_raw, min_n=300)["bp"])
    b1 = nw_mean_t(fm_slopes(chars_bp_tr, fwd_b_tr, min_n=300)["bp"])
    print("-" * 104)
    print(f"C4 bp 價值因子(TR-39 差一步,t=1.87):{b0[0]*1e4:+.1f}bps (t={b0[1]:+.2f}) → "
          f"{b1[0]*1e4:+.1f}bps (t={b1[1]:+.2f})"
          + ("  **過線但屬全新發現,需獨立樣本確認**" if abs(b1[1]) >= 2 else "  (仍未過線)"))

    v = ("VERDICT-STABLE -- 三候選在還原股價下維持符號與 |t|>=2;量級修正已記錄。"
         if stable and concentrated else
         "VERDICT-CHANGED -- 還原股價改變了台股結論,以本 TR 為準。")
    print("-" * 104)
    print(f"VERDICT: {v}")
    print("=" * 104)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    ks = list(FIVE)
    x = np.arange(len(ks))
    ax.bar(x - 0.2, [nw_mean_t(sl_raw[k])[1] for k in ks], 0.4, label="未還原",
           color="#90a4ae", alpha=0.9)
    ax.bar(x + 0.2, [nw_mean_t(sl_tr[k])[1] for k in ks], 0.4, label="還原(總報酬)",
           color="#1565c0", alpha=0.9)
    ax.axhline(2, color="#c62828", ls="--", lw=1)
    ax.axhline(-2, color="#c62828", ls="--", lw=1)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(ks, fontsize=9)
    ax.set_ylabel("聯合 FM NW t")
    ax.set_title("C2:還原前後的判定是否改變", fontsize=10.5)
    ax.legend(fontsize=9)
    ax = axes[1]
    ax.bar([f"D{i}" for i in range(1, 11)], [v * 100 for v in ladder],
           color=["#c62828"] + ["#90a4ae"] * 9, alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("淨超額 %/年")
    ax.set_title("C3:還原後的十分位階梯", fontsize=10.5)
    for a in axes:
        a.grid(alpha=0.3, axis="y")
    fig.suptitle("TR-44:台股判定 × 還原股價(總報酬基準)", fontsize=12.5)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr44_taiwan_total_return.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
