"""Flagship one-pager -- a single shareable PNG explaining the 5-sleeve combo.

Panels: (A) current risk-parity weights, (B) NAV vs VOO with drawdown strip,
(C) the L-scale menu (drawdown-budget leverage), (D) the honest-numbers box
(state-cost alpha t, selection-honest probability, the TR-35 regime scope).

Run: uv run python scripts/flagship_onepager.py   (~2 min)
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

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

import validate_recommendation as vr  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402

FIN_SPREAD = 0.006
SLEEVE_ZH = {"equity_mom": "科技/AI 動能輪動", "defensive": "防禦性輪動",
             "lev_trend": "趨勢閘門 TQQQ", "gold": "黃金 GLD", "bonds": "美債 IEF"}


def stats(r: pd.Series) -> tuple[float, float, float]:
    nav = (1 + r).cumprod()
    yrs = len(r) / 252
    cagr = float(nav.iloc[-1] ** (1 / yrs) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    sharpe = float(r.mean() / r.std() * np.sqrt(252))
    return cagr, mdd, sharpe


def main():
    meta = json.loads(Path("exports/dashboard/flagship_combo.json").read_text(encoding="utf-8"))
    weights = meta["weights"]
    rp, _ew, _s = vr.build_combo()
    store = DuckStore("./data")
    voo = store.load_close_pivot(["VOO"], column="adj_close").iloc[:, 0].pct_change()
    voo = voo.reindex(rp.index).fillna(0.0)
    rf_d = load_ff_factors(start="2015-01-01", momentum=False)["RF"].reindex(rp.index).ffill().fillna(0)

    fig = plt.figure(figsize=(14, 9.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], width_ratios=[1, 1.5],
                          hspace=0.33, wspace=0.22)

    # A: weights
    ax = fig.add_subplot(gs[0, 0])
    names = [SLEEVE_ZH.get(k, k) for k in weights]
    vals = [v * 100 for v in weights.values()]
    cols = ["#1565c0", "#2e7d32", "#c62828", "#f9a825", "#607d8b"]
    ax.barh(names[::-1], vals[::-1], color=cols[::-1], alpha=0.9)
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=10)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_title("A|五 sleeve 現行風險平價權重(逆波動,月再平衡)", fontsize=11)
    ax.grid(alpha=0.3, axis="x")

    # B: NAV + drawdown
    ax = fig.add_subplot(gs[0, 1])
    nav_c = (1 + rp).cumprod()
    nav_v = (1 + voo).cumprod()
    ax.plot(nav_c.index, nav_c, lw=1.4, color="#1565c0",
            label=f"主力組合(Sharpe {stats(rp)[2]:.2f})")
    ax.plot(nav_v.index, nav_v, lw=1.1, color="#757575",
            label=f"VOO(Sharpe {stats(voo)[2]:.2f})")
    ax.set_yscale("log")
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title(f"B|2015–2026 淨值(log)—— 回撤 {stats(rp)[1]:+.0%} vs VOO {stats(voo)[1]:+.0%}",
                 fontsize=11)
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    dd = nav_c / nav_c.cummax() - 1
    ddv = nav_v / nav_v.cummax() - 1
    ax2.fill_between(dd.index, dd * 100, 0, color="#1565c0", alpha=0.25)
    ax2.plot(ddv.index, ddv * 100, lw=0.7, color="#757575", alpha=0.7)
    ax2.set_ylim(-80, 0)
    ax2.set_ylabel("回撤(%)", fontsize=8)

    # C: L-scale menu
    ax = fig.add_subplot(gs[1, 0])
    ax.axis("off")
    rows = [["L", "CAGR", "MDD", "定位"]]
    tags = {0.5: "睡得著", 1.0: "基準", 1.5: "≈VOO 報酬/一半回撤", 2.0: "≈VOO 波動"}
    for L in (0.5, 1.0, 1.5, 2.0):
        rl = L * rp - (L - 1) * (rf_d + FIN_SPREAD / 252)
        c, m, _ = stats(rl)
        rows.append([f"{L:.1f}×", f"{c:+.1%}", f"{m:+.0%}", tags[L]])
    tbl = ax.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.7)
    ax.set_title("C|L 刻度:用「回撤預算」選槓桿(含融資成本)", fontsize=11)

    # D: honesty box
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    txt = (
        "D|誠實數字(45 份對抗式測試的完整檔案)\n"
        "──────────────────────────────\n"
        "• 月頻 Carhart alpha:+5.3%/yr,t=2.35(含狀態相依成本;\n"
        "   不過學術嚴格線 3.0=「大概率為真,但沒有角度能說確定」)\n"
        "• 選擇誠實化:P(alpha 為真) 約 0.87(實跑 17 次組合層級試驗)\n"
        "• 50 年機制回放:股災回撤=市場的 0.07–0.16 倍;\n"
        "   【注意】利率主導 regime(1970s 型)零超額保護——扛通膨的是金不是債\n"
        "• 權重高原:±20-25% 微調不影響結論(210 變體);配置器可互換\n"
        "──────────────────────────────\n"
        "用法:選 L(表 C)→ 月再平衡照權重(表 A)→ 不擇時進出\n"
        "禁令:不 gate 到現金(7 次測試)、不賣權收租、不追去年冠軍"
    )
    ax.text(0.02, 0.95, txt, va="top", ha="left", fontsize=10.5, family="Microsoft JhengHei",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#f5f5f5", edgecolor="#90a4ae"))

    fig.suptitle("主力 5-sleeve 風險平價組合 —— 一頁說明(2026-07)", fontsize=14)
    outp = Path("docs/img/flagship_onepager.png")
    fig.savefig(outp, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
