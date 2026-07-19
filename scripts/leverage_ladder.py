"""Leverage ladder -- the plain-language DECISION figure (companion to the evidence figure).

Why this exists: the flagship's evidence figure answers "what did we find"; a reader
who wants to USE the book needs a different picture -- "the recipe is fixed, L is the
throttle, pick it from the drawdown you can stomach". Written for someone with zero
background: no Sharpe, no alpha, no jargon on the chart.

Financing convention (fixed here and in the one-pager): spare cash at L<1 earns the
T-bill WITHOUT the borrow spread; only L>1 pays rf + 60bps. The single-formula version
used earlier credited the spread to cash and overstated L=0.5 by ~30bps/yr.

Run: uv run python scripts/leverage_ladder.py   (~2 min)
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

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

import validate_recommendation as vr  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.attribution import load_ff_factors  # noqa: E402

FIN_SPREAD = 0.006
LADDER = [
    (0.5, "#4caf50", "只投一半,另一半放定存", "50萬配方 + 50萬定存"),
    (1.0, "#1565c0", "錢全部照配方買", "100萬 全買配方"),
    (1.5, "#f9a825", "借半份(要付利息)", "借50萬 → 買150萬"),
    (2.0, "#c62828", "借一倍(要付利息)", "借100萬 → 買200萬"),
]


def lever(rp: pd.Series, rf: pd.Series, L: float) -> pd.Series:
    """L<=1: spare cash earns T-bill (no spread). L>1: borrow at T-bill + spread."""
    if L <= 1:
        return L * rp + (1 - L) * rf
    return L * rp - (L - 1) * (rf + FIN_SPREAD / 252)


def stats(r: pd.Series) -> tuple[float, float]:
    nav = (1 + r).cumprod()
    cagr = float(nav.iloc[-1] ** (252 / len(r)) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    return cagr, mdd


def main():
    rp, _ew, _s = vr.build_combo()
    store = DuckStore("./data")
    voo = store.load_close_pivot(["VOO"], column="adj_close").iloc[:, 0].pct_change()
    voo = voo.reindex(rp.index).fillna(0.0)
    rf = load_ff_factors(start="2015-01-01", momentum=False)["RF"].reindex(rp.index).ffill().fillna(0)
    cv, mv = stats(voo)

    fig = plt.figure(figsize=(13.5, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1.0], width_ratios=[1.05, 1],
                          hspace=0.30, wspace=0.20)

    # ---- top: the ladder of NAV curves ----
    ax = fig.add_subplot(gs[0, :])
    ax.plot((1 + voo).cumprod(), lw=1.6, color="#616161", ls="--",
            label=f"VOO 美股大盤(年化 {cv:+.0%},最慘 {mv:+.0%})")
    rows = []
    for L, col, plain, money in LADDER:
        r = lever(rp, rf, L)
        c, m = stats(r)
        rows.append((L, col, plain, money, c, m))
        ax.plot((1 + r).cumprod(), lw=1.7, color=col,
                label=f"L={L}(年化 {c:+.0%},最慘 {m:+.0%}) — {plain}")
    ax.set_yscale("log")
    ax.legend(fontsize=9.5, loc="upper left")
    ax.grid(alpha=0.3)
    ax.set_ylabel("每 1 元變成幾元(對數尺度)")
    ax.set_title("同一份配方,四種油門 —— 2015～2026 實際走勢", fontsize=12.5)

    # ---- bottom-left: the pain bars ----
    ax = fig.add_subplot(gs[1, 0])
    labels = [f"L={r[0]}" for r in rows]
    mdds = [abs(r[5]) * 100 for r in rows]
    cols = [r[1] for r in rows]
    y = np.arange(len(rows))
    ax.barh(y, mdds, color=cols, alpha=0.9)
    for i, (m, c) in enumerate(zip(mdds, [r[4] for r in rows])):
        ax.text(m + 0.8, i, f"最慘 −{m:.0f}%   年化 {c:+.0%}", va="center", fontsize=10)
    ax.axvline(abs(mv) * 100, color="#616161", ls="--", lw=1.6,
               label=f"VOO 美股大盤最慘 {mv:+.0%}")
    ax.legend(fontsize=9.5, loc="lower right", framealpha=0.95)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, max(mdds + [abs(mv) * 100]) * 1.42)
    ax.set_xlabel("帳面從高點最多掉多少 (%)")
    ax.set_title("你能忍多痛,就選哪一格", fontsize=11.5)
    ax.grid(alpha=0.3, axis="x")

    # ---- bottom-right: the plain-language table ----
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    cell = [[f"L={r[0]}", r[3], f"{r[4]:+.0%}", f"{r[5]:+.0%}"] for r in rows]
    tbl = ax.table(cellText=cell,
                   colLabels=["油門", "100 萬本金怎麼放", "年化", "最慘"],
                   loc="upper center", cellLoc="center",
                   colWidths=[0.15, 0.45, 0.18, 0.18])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.65)
    for i, r in enumerate(rows):
        tbl[(i + 1, 0)].set_facecolor(r[1])
        tbl[(i + 1, 0)].set_text_props(color="white", weight="bold")
    ax.text(0.5, 0.30,
            "怎麼選?問自己一句:\n「帳戶從高點掉 __%,我會不會嚇到全部賣掉?」\n"
            "你能忍的那個數字,就是你的油門。\n\n"
            "新手一律 L 不超過 1(不用借錢、普通帳戶就能做)。",
            ha="center", va="top", fontsize=11, family="Microsoft JhengHei",
            bbox=dict(boxstyle="round,pad=0.55", facecolor="#f5f5f5", edgecolor="#90a4ae"))

    fig.suptitle("L 是油門,不是策略 —— 配方固定,你只決定踩多用力", fontsize=14)
    fig.text(0.5, 0.012,
             "日常操作:每月挑一天,把帳戶調回配方比例(漲多的賣一點、跌少的補一點),其餘時間不看盤。"
             "我們測過 7 種「聰明進出場」,全部輸給「什麼都不做」。",
             ha="center", fontsize=10, color="#37474f")
    outp = Path("docs/img/leverage_ladder.png")
    fig.savefig(outp, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] {outp}")
    for L, _c, _p, _m, c, m in rows:
        print(f"  L={L}: CAGR {c:+.1%}, MDD {m:+.0%}")
    print(f"  VOO : CAGR {cv:+.1%}, MDD {mv:+.0%}")


if __name__ == "__main__":
    main()
