"""Leverage-ratio figure for the README (zh + en): the fixed allocation at L in
{0.5, 1.0, 1.5, 2.0} versus VOO, as (1) cumulative value on a log scale and
(2) a max-drawdown / annualized-return summary.

Presentation contract (reader-facing, so kept neutral and professional):
- terminology: "leverage ratio L", "annualized return", "maximum drawdown" --
  no metaphors on the chart;
- L is ORDINAL, so the series use a single-hue light->dark ramp (validated
  ordinal palette), not categorical/status colors; VOO is a dashed gray reference;
- the allocation table, selection guidance, and operating notes live in README
  prose, not inside the figure.

Financing convention (fixed here and in the one-pager): spare cash at L<1 earns
the T-bill WITHOUT the borrow spread; only L>1 pays rf + 60bps. The single-formula
version used earlier credited the spread to cash and overstated L=0.5 by ~30bps/yr.

Run: uv run python scripts/leverage_ladder.py   (~2 min)
Outputs: docs/img/leverage_ladder.png (zh), docs/img/leverage_ladder_en.png (en)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
# ordinal single-hue ramp (validated: monotone lightness, adjacent dL>=0.06,
# light end 2.1:1 on white) -- L is an ordered quantity, not four categories
RAMP = {0.5: "#86b6ef", 1.0: "#3987e5", 1.5: "#1c5cab", 2.0: "#0d366b"}
INK = "#0b0b0b"          # primary text
INK2 = "#52514e"         # secondary text / VOO reference
MUTED = "#898781"        # axis labels
GRID = "#e1e0d9"         # hairline gridlines
AXIS = "#c3c2b7"         # baseline / spines

TEXT = {
    "zh": {
        "nav_title": "固定配方在四種槓桿比率下的累積淨值(2015–2026,對數尺度,已扣成本與融資利率)",
        "nav_ylab": "淨值(期初 = 1,對數尺度)",
        "voo": "VOO(美股大盤,對照)",
        "series": lambda L: f"L = {L:.1f}(曝險 {L:.1f}×)",
        "risk_title": "最大回撤與年化報酬",
        "risk_xlab": "自高點之最大跌幅(%)",
        "bar": lambda m, c: f"−{m:.0f}%(年化 {c:+.0%})",
        "voo_line": lambda m: f"VOO 最大回撤 −{m:.0f}%",
        "foot": "月頻再平衡;融資慣例:L<1 之閒置資金按 T-bill 利率計息,L>1 融資成本為 T-bill + 60 bps;已含交易成本。",
        "out": "docs/img/leverage_ladder.png",
    },
    "en": {
        "nav_title": "Cumulative value of the fixed allocation at four leverage ratios "
                     "(2015–2026, log scale, net of costs and financing)",
        "nav_ylab": "Growth of $1 (log scale)",
        "voo": "VOO (US large-cap benchmark)",
        "series": lambda L: f"L = {L:.1f} ({L:.1f}x exposure)",
        "risk_title": "Maximum drawdown and annualized return",
        "risk_xlab": "Maximum decline from peak (%)",
        "bar": lambda m, c: f"−{m:.0f}% (CAGR {c:+.0%})",
        "voo_line": lambda m: f"VOO max drawdown −{m:.0f}%",
        "foot": "Monthly rebalancing. Financing convention: cash at L<1 earns the T-bill rate; "
                "borrowing at L>1 costs T-bill + 60 bps. Trading costs included.",
        "out": "docs/img/leverage_ladder_en.png",
    },
}


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


def style(ax):
    ax.grid(alpha=1.0, color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=MUTED, labelsize=9.5)


def render(lang: str, series: dict, voo_nav: pd.Series, rows: list, cv: float, mv: float):
    t = TEXT[lang]
    fig = plt.figure(figsize=(12.6, 7.6), facecolor="white")
    gs = fig.add_gridspec(2, 1, height_ratios=[2.0, 1.0], hspace=0.42)

    # ---- top: cumulative value, log scale ----
    ax = fig.add_subplot(gs[0])
    handles = []
    ax.plot(voo_nav, lw=1.6, color=INK2, ls="--", label=t["voo"])
    for L, nav in series.items():
        ax.plot(nav, lw=1.9, color=RAMP[L], label=t["series"](L))
    ax.set_yscale("log")
    # legend ordered by final value (matches the visual top-to-bottom order)
    hs, ls_ = ax.get_legend_handles_labels()
    finals = [voo_nav.iloc[-1]] + [nav.iloc[-1] for nav in series.values()]
    order = sorted(range(len(finals)), key=lambda i: -finals[i])
    ax.legend([hs[i] for i in order], [ls_[i] for i in order],
              loc="upper left", fontsize=9.5, frameon=False, labelcolor=INK)
    ax.set_ylabel(t["nav_ylab"], color=INK2, fontsize=10)
    ax.set_title(t["nav_title"], fontsize=12, color=INK, pad=10)
    style(ax)

    # ---- bottom: max drawdown bars with annualized-return labels ----
    ax = fig.add_subplot(gs[1])
    ys = range(len(rows))
    for y, (L, c, m) in zip(ys, rows):
        ax.barh(y, abs(m) * 100, height=0.58, color=RAMP[L])
        ax.text(abs(m) * 100 + 0.8, y, t["bar"](abs(m) * 100, c),
                va="center", fontsize=9.5, color=INK,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
    ax.axvline(abs(mv) * 100, color=INK2, ls="--", lw=1.4)
    ax.text(abs(mv) * 100, -0.62, t["voo_line"](abs(mv) * 100),
            fontsize=9, color=INK2, ha="center", va="bottom")
    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"L = {L:.1f}" for L, *_ in rows], fontsize=10.5, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 62)
    ax.set_xlabel(t["risk_xlab"], color=MUTED, fontsize=10)
    ax.set_title(t["risk_title"], fontsize=11, color=INK, loc="left", pad=8)
    style(ax)
    ax.grid(axis="y", alpha=0)

    fig.text(0.01, 0.005, t["foot"], ha="left", fontsize=8.5, color=MUTED)
    outp = Path(t["out"])
    fig.savefig(outp, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] {outp}")


def main():
    rp, _ew, _s = vr.build_combo()
    store = DuckStore("./data")
    voo = store.load_close_pivot(["VOO"], column="adj_close").iloc[:, 0].pct_change()
    voo = voo.reindex(rp.index).fillna(0.0)
    rf = load_ff_factors(start="2015-01-01", momentum=False)["RF"].reindex(rp.index).ffill().fillna(0)
    cv, mv = stats(voo)

    series, rows = {}, []
    for L in RAMP:
        r = lever(rp, rf, L)
        c, m = stats(r)
        series[L] = (1 + r).cumprod()
        rows.append((L, c, m))
    voo_nav = (1 + voo).cumprod()

    for lang in ("zh", "en"):
        render(lang, series, voo_nav, rows, cv, mv)
    for L, c, m in rows:
        print(f"  L={L}: CAGR {c:+.1%}, MDD {m:+.0%}")
    print(f"  VOO : CAGR {cv:+.1%}, MDD {mv:+.0%}")


if __name__ == "__main__":
    main()
