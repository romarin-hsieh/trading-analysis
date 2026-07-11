"""Generate README figures: corrected-assumptions slope chart + TR verdict map.

All numbers are transcribed from committed TR docs (docs/tests/TR-*.md) and the
registry (docs/18) -- no data pipeline is run here. Rerun after major registry updates.

Run: uv run python scripts/readme_figs.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- corrections
# (label, wrong reading, honest reading, wrong value text, honest value text, source)
CASES = [
    ("旗艦 alpha 的 t 值\n(TR-18)", 3.38, 2.64, "3.38(日頻)", "2.64(月頻)",
     "日頻低估市場 beta,把因子報酬記成 alpha;月頻才是誠實時鐘"),
    ("IBS 均值回歸超額 Sharpe\n(TR-16)", 0.63, 0.44, "+0.63(same-close)", "+0.44(next-close)",
     "同收盤成交=用到未來資訊;誠實成交後輸給 B&H +0.45"),
    ("q-factor 使旗艦 alpha 縮水\n(TR-24)", 30, 2, "−30%(混窗)", "−2%(同窗)",
     "分子分母窗不同=比較錯位;同窗後判定翻轉為穩健"),
    ("KMZ 複雜度 P=12k Sharpe\n(TR-17b)", 0.01, 0.41, "+0.01(非忠實機器)", "+0.41(忠實建構)",
     "視窗內 z-score 使核退化=假陰性;複製後仍被波動控制 +0.50 蓋過"),
    ("AR 尖峰命中率(前月,10 大跌)\n(TR-21→21b)", 4, 7, "4/10(個股座位)", "7/10(產業座位)",
     "換到原生棲地診斷半條命回來;閘門在兩座位都輸靜態"),
]

fig, axes = plt.subplots(len(CASES), 1, figsize=(11, 8.2))
fig.suptitle("被自己抓出來的錯誤設想:第一次讀數 → 稽核後讀數(每一件都改寫了判定)",
             fontsize=13, y=0.985)
for ax, (label, v0, v1, t0, t1, why) in zip(axes, CASES):
    lo, hi = min(v0, v1), max(v0, v1)
    pad = (hi - lo) * 0.55 + 1e-9
    x0 = (v0 - lo + pad) / (hi - lo + 2 * pad)
    x1 = (v1 - lo + pad) / (hi - lo + 2 * pad)
    ax.add_patch(FancyArrowPatch((x0, 0.5), (x1, 0.5), arrowstyle="-|>",
                                 mutation_scale=18, lw=2.2, color="#546e7a"))
    ax.plot([x0], [0.5], "o", ms=13, color="#c62828", zorder=3)
    ax.plot([x1], [0.5], "o", ms=13, color="#2e7d32", zorder=3)
    ax.text(x0, 0.86, t0, ha="center", fontsize=10, color="#c62828", fontweight="bold")
    ax.text(x1, 0.86, t1, ha="center", fontsize=10, color="#2e7d32", fontweight="bold")
    ax.text(1.005, 0.5, why, ha="left", va="center", fontsize=8.6, color="#37474f",
            transform=ax.transAxes, wrap=True)
    ax.text(-0.02, 0.5, label, ha="right", va="center", fontsize=9.5,
            color="#263238", transform=ax.transAxes, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
fig.subplots_adjust(left=0.20, right=0.60, top=0.92, bottom=0.03, hspace=0.6)
fig.savefig("docs/img/readme_corrections.png", dpi=150)
plt.close(fig)
print("[chart] docs/img/readme_corrections.png")

# ---------------------------------------------------------------- verdict map
# (code, short label, class) -- class: P=passed, M=partial/diagnostic, F=failed/explained, X=n/a
TRS = [
    ("TR-01", "pairs 統計套利", "F"), ("TR-02", "Markov regime", "M"),
    ("TR-03", "PCA 因子", "M"), ("TR-03b", "共變異清理", "M"),
    ("TR-04", "VaR", "M"), ("TR-04b", "Student-t 尾部", "M"),
    ("TR-05", "GBM 蒙地卡羅", "F"), ("TR-06", "CAPM", "M"),
    ("TR-07", "HRP", "M"), ("TR-08", "ML 混合預測", "F"),
    ("TR-09", "Black-Scholes", "X"), ("TR-10", "LLM agent", "M"),
    ("TR-11", "bagged 回測+RF", "M"), ("TR-12", "相位平均", "P"),
    ("TR-13", "下市終端報酬", "P"), ("TR-14", "n_eff", "P"),
    ("TR-15", "全成本壓力", "P"), ("TR-16", "IBS 完整審判", "F"),
    ("TR-17", "複雜度美德(本座位)", "M"), ("TR-17b", "KMZ 原生座位", "F"),
    ("TR-18", "推論穩健性", "M"), ("TR-19", "隔夜/日內拆解", "M"),
    ("TR-20", "FF5/6 歸因", "P"), ("TR-21", "吸收比率(個股)", "F"),
    ("TR-21b", "AR 原生座位", "M"), ("TR-22", "combo PBO", "P"),
    ("TR-23", "四經典異象", "F"), ("TR-24", "q-factor 雙檢", "P"),
]
COLORS = {"P": "#2e7d32", "M": "#f9a825", "F": "#c62828", "X": "#90a4ae"}
LABELS = {"P": "通過/方法確立", "M": "部分成立/僅診斷或工程價值", "F": "失敗/被控制組解釋", "X": "無資料"}

ncol, nrow = 4, 7
fig, ax = plt.subplots(figsize=(11, 6.2))
for i, (code, name, cls) in enumerate(TRS):
    r, c = divmod(i, ncol)
    x, y = c, nrow - 1 - r
    ax.add_patch(Rectangle((x + 0.03, y + 0.05), 0.94, 0.9,
                           color=COLORS[cls], alpha=0.88))
    ax.text(x + 0.5, y + 0.62, code, ha="center", va="center",
            fontsize=10.5, color="white", fontweight="bold")
    ax.text(x + 0.5, y + 0.32, name, ha="center", va="center",
            fontsize=8.3, color="white")
counts = {k: sum(1 for *_, c in TRS if c == k) for k in COLORS}
handles = [Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in ("P", "M", "F", "X")]
ax.legend(handles, [f"{LABELS[k]}({counts[k]})" for k in ("P", "M", "F", "X")],
          loc="upper center", bbox_to_anchor=(0.5, -0.015), ncol=4, fontsize=9.5,
          frameon=False)
ax.set_xlim(0, ncol)
ax.set_ylim(-0.1, nrow)
ax.axis("off")
ax.set_title("28 份標準化測試(TR)的判定分布:通過的是「方法與風險塑形」,不是選股 alpha\n"
             "(每一份都經過對抗式稽核;綠色裡沒有任何一個擇時或選股訊號)", fontsize=12)
fig.tight_layout()
fig.savefig("docs/img/readme_verdict_map.png", dpi=150)
plt.close(fig)
print("[chart] docs/img/readme_verdict_map.png")
