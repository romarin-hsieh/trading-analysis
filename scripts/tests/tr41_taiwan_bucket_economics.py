"""TR-41 -- where does the Taiwan illiquidity premium live? (docs/27 b3)

TR-40 left one tradable candidate: the illiquid decile, net +6.75%/yr (t=2.33) but
capped at ~NT$15M of capacity. Two implementations are possible and they differ by an
order of magnitude in capacity:
  A "buy the coldest"   = long the most-illiquid decile (TR-40's book)
  B "avoid the hottest" = long everything EXCEPT the most-liquid decile
If the premium is a smooth gradient across deciles, B captures a slice of it with ~100x
the capacity. If it is concentrated in the last decile, only A works and the ceiling is
real. This TR settles that, and prices the capacity-return frontier at real book sizes.

F0 DECLARATION (pre-committed)
  claim  : the illiquidity premium is a gradient, so a higher-capacity implementation
         ("avoid the hottest") retains a usable share of it.
  seat   : survivorship-patched TWSE panel (TR-39b engine), 2015-07..2026, monthly,
         long-only EW, full-rate costs (0.1425%x2 + 0.30% sell tax + 2-tick spread).
  CAL    : decile 1 (most illiquid) net excess must reproduce TR-40's +6.75%/yr within
         +-1.5pp. Fail -> STOP (machinery drift).
  C1 (decisive for the claim): decile ladder D1..D10 net excess over the EW universe.
         monotone-ish gradient (>=6 of 9 adjacent steps declining, and D2+D3 jointly
         positive) -> GRADIENT; premium only in D1 -> CONCENTRATED.
  C2  : the two implementations head to head -- net excess AND capacity.
  C3  : TR-33-style gold diagnostic: do BOTH extremes lag the EW middle (D4-D7)?
  C4  : capacity-constrained frontier. For book sizes NT$5M/15M/50M/150M/500M, cap each
         position at 10% of that name's median daily TWD volume x 5 trading days (a week
         to build and a week to exit); the unfillable share is parked in the EW universe.
         Report realized net excess per book size for A and B.
  anti-HARKing : deciles/EW/monthly/cost model all inherited from TR-40 unchanged; the
         two implementations were named in TR-40's write-up before this test; C4's cap
         rule is stated above before running; trials +0 (same family).
  KNOWN CAVEAT (declared, not fixable at $0): illiquid names' closing prices are stale
         and carry bid-ask bounce, which inflates measured close-to-close returns. A
         skip-a-month variant is reported in C3 as the cheapest available check; a true
         fix needs execution data we do not have.

Run: uv run python scripts/tests/tr41_taiwan_bucket_economics.py   (~4 min)
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
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from tr39_taiwan_panel import DATA, load_panels  # noqa: E402
from tr39b_taiwan_delisted import build_chars  # noqa: E402
from tr40_taiwan_cost_gate import (  # noqa: E402
    COMMISSION_FULL,
    TAX_SELL,
    load_hilo,
    nw_t,
    tick_spread_monthly,
)

MULT = 2.0
BOOK_SIZES = (5e6, 15e6, 50e6, 150e6, 500e6)
PARTICIPATION, BUILD_DAYS = 0.10, 5


def bucket_returns(rank: pd.DataFrame, fwd: pd.DataFrame, spread_m: pd.DataFrame,
                   pick, dv_m: pd.DataFrame | None = None, book: float | None = None,
                   ew_universe: pd.Series | None = None):
    """EW long-only book of `pick(row)` names, monthly, net of costs.
    If book/dv_m given, cap each position at PARTICIPATION x median daily volume x
    BUILD_DAYS and park the unfillable share in the EW universe."""
    held: set[str] = set()
    rows = []
    for t in rank.index:
        s = rank.loc[t].dropna()
        if len(s) < 100:
            continue
        new = set(pick(s))
        if not new:
            continue
        f = fwd.loc[t, list(new)].dropna()
        if f.empty:
            continue
        gross = float(f.mean())
        churn = len(new - held) / max(len(new), 1) if held else 1.0
        sp = spread_m.loc[t, list(new)].dropna()
        half = float(sp.mean()) / 2 if len(sp) else 0.0
        cost = churn * ((COMMISSION_FULL + half) + (COMMISSION_FULL + TAX_SELL + half))
        net = gross - cost
        if book is not None and dv_m is not None and ew_universe is not None:
            caps = (PARTICIPATION * BUILD_DAYS * dv_m.loc[t, list(new)].dropna())
            if len(caps):
                target = book / len(new)
                filled = float(np.minimum(caps, target).sum())
                share = min(1.0, filled / book)
                net = share * net + (1 - share) * float(ew_universe.get(t, 0.0))
                rows.append({"date": t, "net": net, "fill": share})
                held = new
                continue
        rows.append({"date": t, "net": net, "fill": 1.0})
        held = new
    return pd.DataFrame(rows).set_index("date")


def main():
    man = pd.read_csv(DATA / "delisted.csv", dtype={"stock_id": str})
    px, dv, pbr, per = load_panels()
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px.columns:
            px.loc[px.index > dd, sid] = np.nan
            dv.loc[dv.index > dd, sid] = np.nan
    chars, fwd, ret_m, dv_p, me = build_chars(px, dv, pbr, include_bp=False)
    ew_universe = fwd.mean(axis=1)
    H, L, C = load_hilo(set(chars["logdv"].columns))
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        for X in (H, L, C):
            if sid in X.columns:
                X.loc[X.index > dd, sid] = np.nan
    spread_m = tick_spread_monthly(C, MULT).reindex(chars["logdv"].index) \
        .reindex(columns=chars["logdv"].columns)
    dv_m = dv.resample("ME").mean().reindex(chars["logdv"].index) \
        .reindex(columns=chars["logdv"].columns)
    illiq = -chars["logdv"]          # high = most illiquid

    print("=" * 104)
    print("TR-41  台股低流動性溢酬住在哪?買最冷門 vs 避開最熱門(docs/27 b3)")
    print("=" * 104)

    # ---- C1 decile ladder ----
    def decile_pick(d):                       # d=1 most illiquid .. 10 most liquid
        def f(s):
            q_hi = s.quantile(1 - (d - 1) * 0.1)
            q_lo = s.quantile(1 - d * 0.1)
            return s[(s <= q_hi) & (s > q_lo)].index
        return f

    ladder = {}
    for d in range(1, 11):
        r = bucket_returns(illiq, fwd, spread_m, decile_pick(d))
        ex = r["net"] - ew_universe.reindex(r.index)
        m, t = nw_t(ex)
        cap = float((PARTICIPATION * BUILD_DAYS * dv_m.iloc[-1][
            decile_pick(d)(illiq.iloc[-1].dropna())].dropna()).sum())
        ladder[d] = (m * 12, t, cap)
    d1_net = ladder[1][0]
    cal = abs(d1_net - 0.0675) <= 0.015
    print(f"CAL: D1(最不流動)淨超額 {d1_net*100:+.2f}%/yr vs TR-40 的 +6.75% "
          f"(容許 ±1.5pp) -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: INVALID-TEST -- machinery drift vs TR-40.")
        return

    print("-" * 104)
    print("C1 十分位階梯(D1=最不流動 → D10=最流動;淨超額 vs 等權宇宙):")
    for d in range(1, 11):
        m, t, cap = ladder[d]
        bar = "█" * max(0, int(m * 100))
        print(f"  D{d:<2}: {m*100:+6.2f}%/yr (t={t:+5.2f})  容量 NT${cap/1e6:>8,.0f}M  {bar}")
    steps = [ladder[d][0] - ladder[d + 1][0] for d in range(1, 10)]
    declining = sum(1 for s in steps if s > 0)
    gradient = declining >= 6 and (ladder[2][0] + ladder[3][0]) > 0
    print(f"  相鄰遞減步數 {declining}/9;D2+D3 合計 {(ladder[2][0]+ladder[3][0])*100:+.2f}%/yr "
          f"-> {'GRADIENT(梯度)' if gradient else 'CONCENTRATED(只在最尾端)'}")

    # ---- C2 the two implementations ----
    print("-" * 104)
    print("C2 兩種做法對決:")
    impls = {
        "A 買最冷門(D1)": lambda s: s[s >= s.quantile(0.90)].index,
        "B 避開最熱門(D1-D9)": lambda s: s[s >= s.quantile(0.10)].index,
        "B' 只買冷門半邊(D1-D5)": lambda s: s[s >= s.quantile(0.50)].index,
    }
    res = {}
    for lab, pick in impls.items():
        r = bucket_returns(illiq, fwd, spread_m, pick)
        ex = r["net"] - ew_universe.reindex(r.index)
        m, t = nw_t(ex)
        names_now = pick(illiq.iloc[-1].dropna())
        cap = float((PARTICIPATION * BUILD_DAYS * dv_m.iloc[-1][names_now].dropna()).sum())
        res[lab] = (m * 12, t, cap, len(names_now))
        print(f"  {lab:<22}: 淨超額 {m*12*100:+6.2f}%/yr (t={t:+5.2f}) | "
              f"{len(names_now):>4} 檔 | 容量 NT${cap/1e6:>8,.0f}M")

    # ---- C3 gold diagnostic + skip-a-month ----
    mid = bucket_returns(illiq, fwd, spread_m,
                         lambda s: s[(s >= s.quantile(0.30)) & (s <= s.quantile(0.70))].index)
    mid_ex = mid["net"] - ew_universe.reindex(mid.index)
    m_mid, t_mid = nw_t(mid_ex)
    top = bucket_returns(illiq, fwd, spread_m, lambda s: s[s >= s.quantile(0.90)].index)
    bot = bucket_returns(illiq, fwd, spread_m, lambda s: s[s <= s.quantile(0.10)].index)
    m_top, _ = nw_t(top["net"] - ew_universe.reindex(top.index))
    m_bot, _ = nw_t(bot["net"] - ew_universe.reindex(bot.index))
    print("-" * 104)
    print(f"C3 黃金診斷(TR-33 式):最冷門 {m_top*12*100:+.2f}% | 中段 D4-D7 "
          f"{m_mid*12*100:+.2f}% | 最熱門 {m_bot*12*100:+.2f}%(全為 vs 等權宇宙)")
    fwd_skip = fwd.shift(-1)                    # skip one month between form and hold
    r_skip = bucket_returns(illiq, fwd_skip, spread_m, impls["A 買最冷門(D1)"])
    m_sk, t_sk = nw_t(r_skip["net"] - ew_universe.shift(-1).reindex(r_skip.index))
    print(f"C3 跳一個月(對抗停滯價/買賣價差彈跳):D1 淨超額 {m_sk*12*100:+.2f}%/yr "
          f"(t={t_sk:+.2f}) vs 原始 {d1_net*100:+.2f}%")

    # ---- C4 capacity frontier ----
    print("-" * 104)
    print("C4 容量-報酬前緣(部位上限=該檔 10% 日量 × 5 日;裝不下的部分放等權宇宙):")
    print(f"{'資金規模':>12} | {'A 買最冷門':>16} | {'B 避開最熱門':>16}")
    frontier = {}
    for book in BOOK_SIZES:
        cells = []
        for lab in ("A 買最冷門(D1)", "B 避開最熱門(D1-D9)"):
            r = bucket_returns(illiq, fwd, spread_m, impls[lab], dv_m, book, ew_universe)
            ex = r["net"] - ew_universe.reindex(r.index)
            m, t = nw_t(ex)
            cells.append((m * 12, t, float(r["fill"].mean())))
        frontier[book] = cells
        print(f"  NT${book/1e6:>7,.0f}M | {cells[0][0]*100:+6.2f}% (填滿 {cells[0][2]:>3.0%}) "
              f"| {cells[1][0]*100:+6.2f}% (填滿 {cells[1][2]:>3.0%})")

    a_net, b_net = res["A 買最冷門(D1)"][0], res["B 避開最熱門(D1-D9)"][0]
    ratio = b_net / a_net if a_net > 0 else np.nan
    if gradient and b_net > 0.01:
        v = (f"GRADIENT -- 溢酬是梯度而非只在尾端:B「避開最熱門」保留 {ratio:.0%} 的溢酬"
             f"({b_net*100:+.2f}%/yr),容量放大約 "
             f"{res['B 避開最熱門(D1-D9)'][2]/res['A 買最冷門(D1)'][2]:.0f} 倍。")
    elif gradient:
        v = "GRADIENT 但 B 的殘值過薄:高容量版本不值得實作。"
    else:
        v = "CONCENTRATED -- 溢酬只在最尾端;NT$15M 的容量天花板是真的,無高容量替代方案。"
    print("-" * 104)
    print(f"VERDICT: {v}")
    print("=" * 104)

    # chart
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    ax = axes[0]
    ds = list(range(1, 11))
    vals = [ladder[d][0] * 100 for d in ds]
    cols = ["#c62828" if d == 1 else "#1565c0" if d <= 5 else "#90a4ae" for d in ds]
    ax.bar([f"D{d}" for d in ds], vals, color=cols, alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("淨超額 %/年(vs 等權宇宙)")
    ax.set_title("C1:十分位階梯(D1=最不流動)", fontsize=10.5)
    ax = axes[1]
    labs = list(res)
    ax.bar(range(len(labs)), [res[k][0] * 100 for k in labs],
           color=["#c62828", "#2e7d32", "#1565c0"], alpha=0.9)
    for i, k in enumerate(labs):
        ax.text(i, res[k][0] * 100 + 0.2,
                f"容量\nNT${res[k][2]/1e6:,.0f}M", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(labs)))
    ax.set_xticklabels(["A 買最冷門", "B 避開最熱門", "B' 冷門半邊"], fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("淨超額 %/年")
    ax.set_title("C2:兩種做法 × 容量", fontsize=10.5)
    ax = axes[2]
    xs = [b / 1e6 for b in BOOK_SIZES]
    ax.plot(xs, [frontier[b][0][0] * 100 for b in BOOK_SIZES], "o-", color="#c62828",
            label="A 買最冷門")
    ax.plot(xs, [frontier[b][1][0] * 100 for b in BOOK_SIZES], "s-", color="#2e7d32",
            label="B 避開最熱門")
    ax.set_xscale("log")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("資金規模(NT$ 百萬,對數)")
    ax.set_ylabel("實現淨超額 %/年")
    ax.set_title("C4:容量-報酬前緣", fontsize=10.5)
    ax.legend(fontsize=9)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-41:低流動性溢酬住在哪?(買最冷門 vs 避開最熱門)", fontsize=12.5)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr41_taiwan_buckets.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
