"""Generate README figures: TR verdict map grouped by mechanism type (zh + en).

All verdicts are transcribed from committed TR docs (docs/tests/TR-*.md) and the
registry (docs/18) -- no data pipeline is run here. Rerun after major registry updates.
The reader-facing grouping is by WHAT KIND of mechanism each test judges (not TR order).

Run: uv run python scripts/readme_figs.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# verdict classes: P=passed/method, M=partial (diagnostic/engineering), F=failed/explained, X=n/a
GROUPS = [
    ("擇時與波動 regime", "Timing & volatility regimes", [
        ("TR-02", "Markov regime", "Markov regime", "M"),
        ("TR-16", "IBS 均值回歸", "IBS mean-reversion", "F"),
        ("TR-17", "KMZ 複雜度(本座位)", "KMZ complexity (our seat)", "M"),
        ("TR-17b", "KMZ 原生座位", "KMZ native seat", "F"),
        ("TR-31", "Campbell-Thompson", "Campbell-Thompson", "F"),
        ("TR-21", "吸收比率(個股)", "Absorption ratio (stocks)", "F"),
        ("TR-21b", "吸收比率(產業)", "Absorption ratio (industries)", "M"),
        ("TR-42", "相關 regime 煞車", "Correlation brake", "F"),
    ]),
    ("橫斷面選股與因子", "Cross-sectional picking & factors", [
        ("TR-08", "ML 報酬預測", "ML return forecasting", "F"),
        ("TR-11", "隨機森林+隨機視窗", "Random forest + random windows", "M"),
        ("TR-23", "四個經典異象", "Four classic anomalies", "F"),
        ("TR-24", "q-factor 雙重檢驗", "q-factor double check", "P"),
        ("TR-26", "GP 因子深度網格", "GP factor depth grid", "P"),
        ("TR-27", "GP 成員資格×市值", "GP membership x size", "M"),
        ("TR-28", "季頻 ROE(HXZ)", "Quarterly ROE (HXZ)", "F"),
        ("TR-32", "產業動量(M-G)", "Industry momentum (M-G)", "F"),
        ("TR-34", "Fama-MacBeth 面板", "Fama-MacBeth panel", "M"),
        ("TR-39", "台股棲地面板", "Taiwan habitat panel", "M"),
        ("TR-39b", "台股去倖存補丁", "Taiwan delisting patch", "M"),
        ("TR-40", "台股成本關卡", "Taiwan cost gate", "M"),
        ("TR-41", "台股桶經濟性", "Taiwan bucket economics", "M"),
        ("TR-44", "台股還原股價", "Taiwan total-return", "M"),
    ]),
    ("組合建構與風險模型", "Portfolio construction & risk models", [
        ("TR-03", "PCA 統計因子", "PCA statistical factors", "M"),
        ("TR-03b", "共變異矩陣清理", "Covariance cleaning", "M"),
        ("TR-04", "VaR", "VaR", "M"),
        ("TR-04b", "Student-t 厚尾", "Student-t fat tails", "M"),
        ("TR-43", "EVT 尾部挑戰者", "EVT tail challenger", "F"),
        ("TR-07", "HRP 階層風險平價", "HRP", "M"),
        ("TR-22", "組合家族 PBO", "Combo-family PBO", "P"),
        ("TR-25", "穩健度網格", "Robustness grid", "P"),
        ("TR-29", "持有期×換手曲線", "Holding x turnover", "P"),
        ("TR-33", "組合×GP 疊加", "Combo x GP stacking", "F"),
        ("TR-35", "機制 50 年回放", "Mechanism 50yr replay", "M"),
    ]),
    ("定價模型與模擬", "Pricing models & simulation", [
        ("TR-05", "GBM 蒙地卡羅", "GBM Monte Carlo", "F"),
        ("TR-06", "CAPM", "CAPM", "M"),
        ("TR-09", "Black-Scholes", "Black-Scholes", "X"),
        ("TR-36", "賣權溢酬(指數層)", "Put-write premium (index)", "F"),
    ]),
    ("推論誠實度與偏誤控制", "Inference honesty & bias control", [
        ("TR-12", "再平衡相位運氣", "Rebalance-phase luck", "P"),
        ("TR-13", "下市偏誤區間", "Delisting bias bounds", "P"),
        ("TR-14", "有效樣本數", "Effective sample size", "P"),
        ("TR-15", "全成本壓力", "Full-cost stress", "P"),
        ("TR-18", "推論穩健性", "Inference robustness", "M"),
        ("TR-19", "隔夜/日內拆解", "Overnight/intraday split", "M"),
        ("TR-20", "FF5/6 歸因", "FF5/6 attribution", "P"),
        ("TR-37", "戰役 deflated alpha", "Campaign deflated alpha", "M"),
        ("TR-38", "狀態相依成本", "State-dependent costs", "P"),
    ]),
    ("套利與 LLM agent", "Arbitrage & LLM agents", [
        ("TR-01", "配對交易統計套利", "Pairs stat-arb", "F"),
        ("TR-10", "LLM agent 框架", "LLM agent frameworks", "M"),
        ("TR-30", "外包線反轉", "Outside-bar reversal", "F"),
        ("TR-30b", "外包線忠實引擎", "Outside bar, faithful", "F"),
    ]),
]
COLORS = {"P": "#2e7d32", "M": "#f9a825", "F": "#c62828", "X": "#90a4ae"}
LEGEND = {
    "zh": {"P": "通過/方法確立", "M": "部分成立(僅診斷或工程價值)",
           "F": "失敗/被對照組解釋", "X": "無資料"},
    "en": {"P": "passed / method established", "M": "partial (diagnostic or engineering value)",
           "F": "failed / explained by controls", "X": "no data"},
}
TITLES = {
    "zh": "50 份標準化測試,依機制類型分組\n"
          "(每一份都經過對抗式稽核;擇時類一格綠色都沒有,綠色集中在方法與推論誠實度)",
    "en": "All 50 standardized tests, grouped by mechanism type\n"
          "(every report adversarially audited; the timing row has no green at all)",
}


def verdict_map(lang: str, outfile: str) -> None:
    ncol = max(len(items) for _, _, items in GROUPS)
    nrow = len(GROUPS)
    fig, ax = plt.subplots(figsize=(12.5, 6.6))
    for r, (zh_label, en_label, items) in enumerate(GROUPS):
        y = nrow - 1 - r
        ax.text(-0.15, y + 0.5, zh_label if lang == "zh" else en_label,
                ha="right", va="center", fontsize=10.5, fontweight="bold", color="#263238")
        for c, (code, zh_name, en_name, cls) in enumerate(items):
            ax.add_patch(Rectangle((c + 0.04, y + 0.06), 0.92, 0.88,
                                   color=COLORS[cls], alpha=0.9))
            ax.text(c + 0.5, y + 0.62, code, ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
            ax.text(c + 0.5, y + 0.3, zh_name if lang == "zh" else en_name,
                    ha="center", va="center", fontsize=7.6, color="white")
    counts = {k: sum(1 for _, _, items in GROUPS for *_, c in items if c == k) for k in COLORS}
    handles = [Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in ("P", "M", "F", "X")]
    ax.legend(handles, [f"{LEGEND[lang][k]}({counts[k]})" for k in ("P", "M", "F", "X")],
              loc="upper center", bbox_to_anchor=(0.44, -0.01), ncol=4, fontsize=9,
              frameon=False)
    ax.set_xlim(-2.6, ncol)
    ax.set_ylim(-0.15, nrow)
    ax.axis("off")
    ax.set_title(TITLES[lang], fontsize=12)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"[chart] {outfile}")


if __name__ == "__main__":
    verdict_map("zh", "docs/img/readme_verdict_map.png")
    verdict_map("en", "docs/img/readme_verdict_map_en.png")
