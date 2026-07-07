"""Generate the README results-gallery figures into docs/img/.

Four figures, regenerated from the same code paths the docs cite:
  fig_scoreboard.png    -- the honest funnel: 226 variants -> 26 families -> 5 PASSED -> 1 alpha
  fig_combo.png         -- flagship 5-sleeve risk-parity combo vs VOO (equity + drawdown)
  fig_markov_static.png -- most famous failure: Markov regime gate vs a CONSTANT 57% dial
  fig_ensemble.png      -- mixing beats picking: holdout Sharpe/MDD of E1 vote vs IS-best rule
The fifth gallery image (IBS fill-time reversal) reuses docs/tests/img/tr16_ibs.png as-is.

Sourced constants (not recomputed here) are labeled with the script that produced them.
Run: uv run python scripts/readme_figures.py            (repo root; Markov refits take ~2-5 min)
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

OUT = Path("docs/img")
OUT.mkdir(parents=True, exist_ok=True)
GREEN, AMBER, RED, BLUE, GREY = "#2e7d32", "#f9a825", "#c62828", "#1565c0", "#757575"


def dd(eq: pd.Series) -> pd.Series:
    return eq / eq.cummax() - 1.0


def fig_scoreboard():
    # counts from docs/18 verdict tables + docs/trial-registry.md (2026-07 state)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.5, 4.2), gridspec_kw={"width_ratios": [1.6, 1.0]}
    )
    stages = [
        ("named strategy variants registered", 226, GREY),
        ("mechanism families tested (fabric)", 26, BLUE),
        ("PASSED the acceptance gate", 5, GREEN),
        ("statistically significant alpha", 1, "#1b5e20"),
    ]
    y = np.arange(len(stages))[::-1]
    for yi, (label, v, c) in zip(y, stages, strict=True):
        ax1.barh(yi, v, color=c, height=0.55)
        ax1.text(v + 4, yi, f"{v}", va="center", fontweight="bold")
        ax1.text(2, yi + 0.42, label, va="bottom", fontsize=9.5)
    ax1.set_xlim(0, 260)
    ax1.set_ylim(-0.55, len(stages) - 1 + 1.05)
    ax1.set_yticks([])
    ax1.set_title("11 years of daily data, $0/month budget: the survival funnel",
                  fontsize=11, pad=14)
    ax1.spines[["top", "right", "left"]].set_visible(False)

    fam = [("PASSED", 5, GREEN), ("PARTIAL\n(risk/engineering\nvalue, no alpha)", 10, AMBER),
           ("FAILED", 11, RED)]
    left = 0.0
    for name, v, c in fam:
        ax2.barh(0, v, left=left, color=c, height=0.5)
        ax2.text(left + v / 2, 0, f"{v}", ha="center", va="center",
                 color="white", fontweight="bold", fontsize=13)
        ax2.text(left + v / 2, -0.42, name, ha="center", va="top", fontsize=8.5)
        left += v
    ax2.set_xlim(0, 26)
    ax2.set_ylim(-1.7, 0.9)
    ax2.set_yticks([])
    ax2.set_xticks([])
    ax2.set_title("verdicts across 26 mechanism families (docs/18)", fontsize=11, pad=14)
    ax2.spines[["top", "right", "left", "bottom"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_scoreboard.png", dpi=150)
    plt.close(fig)
    print("[ok] fig_scoreboard.png")


def fig_combo():
    import sector_strategies as ss
    from validate_recommendation import build_combo

    rp, _ew, _sleeves = build_combo()
    voo = ss._px(["VOO"]).iloc[:, 0].pct_change().reindex(rp.index).fillna(0.0)
    bil = ss._px(["BIL"]).iloc[:, 0].pct_change().reindex(rp.index).fillna(0.0)
    eq_rp, eq_voo = (1 + rp).cumprod(), (1 + voo).cumprod()

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12.5, 7), sharex=True, gridspec_kw={"height_ratios": [2.4, 1.0]}
    )
    ax1.plot(eq_rp.index, eq_rp, color=BLUE, lw=1.6, label="5-sleeve risk-parity combo")
    ax1.plot(eq_voo.index, eq_voo, color=GREY, lw=1.4, label="VOO buy & hold")
    ax1.set_yscale("log")
    ax1.set_title("The one survivor: 5-sleeve risk-parity combo, 2015-2026 "
                  "(full-cost Carhart t=3.38, still t=3.14 at 2x costs -- TR-15)", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(alpha=0.3)
    ex = rp - bil
    sh = float(ex.mean() / ex.std() * np.sqrt(252))  # F3: Sharpe on excess-over-T-bill
    ax1.text(0.985, 0.04,
             f"combo: excess-over-T-bill Sharpe {sh:.2f}  MDD {dd(eq_rp).min():+.0%}   |   "
             f"VOO: MDD {dd(eq_voo).min():+.0%}\n"
             "the edge is the drawdown, not the return -- lever it to taste "
             "(scripts/defensive_overlay.py)",
             transform=ax1.transAxes, ha="right", va="bottom", fontsize=8.5,
             bbox={"boxstyle": "round", "fc": "white", "ec": GREY, "alpha": 0.85})
    ax2.fill_between(eq_rp.index, dd(eq_rp), 0, color=BLUE, alpha=0.55,
                     label="combo drawdown")
    ax2.fill_between(eq_voo.index, dd(eq_voo), 0, color=GREY, alpha=0.35,
                     label="VOO drawdown")
    ax2.legend(loc="lower left", fontsize=9)
    ax2.grid(alpha=0.3)
    ax2.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    fig.tight_layout()
    fig.savefig(OUT / "fig_combo.png", dpi=150)
    plt.close(fig)
    print("[ok] fig_combo.png")

    # annual return table for the README (printed, pasted as markdown)
    yr = pd.DataFrame({"combo": rp, "VOO": voo})
    ann = (1 + yr).groupby(yr.index.year).prod() - 1
    print("\nyear | combo | VOO")
    for y, row in ann.iterrows():
        print(f"{y} | {row['combo']:+.1%} | {row['VOO']:+.1%}")


def fig_markov_static():
    """TR-02b logic, README-sized: the famous regime model vs a constant."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    from trading_analysis.data.store import DuckStore

    store = DuckStore("./data")
    qqq = store.load_close_pivot(["QQQ"], column="adj_close").iloc[:, 0].pct_change()
    bil = (store.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0]
           .reindex(qqq.index).ffill().pct_change().fillna(0.0))

    r = qqq.dropna().loc["2015-01-01":]
    month = pd.Series(r.index.to_period("M"), index=r.index)
    sig = pd.Series(np.nan, index=r.index)
    state, prev = 0.0, None
    for t in r.index:
        m = month.loc[t]
        if m != prev:
            hist = r.loc[:t].iloc[:-1]
            if len(hist) >= 750:
                try:
                    mod = MarkovRegression(hist.to_numpy() * 100, k_regimes=2,
                                           trend="c", switching_variance=True)
                    res = mod.fit(disp=False)
                    fp = res.filtered_marginal_probabilities[:, :]
                    low = int(np.argmin([res.params[-2], res.params[-1]]))
                    state = float(fp[-1, low] > 0.5)
                except Exception:
                    pass
            prev = m
        sig.loc[t] = state
    sig = sig.fillna(0.0).reindex(qqq.index).fillna(0.0)

    oos = sig.loc["2017-12-29":].index
    q, b, s_ = qqq.loc[oos].fillna(0.0), bil.loc[oos], sig.loc[oos]
    expo = float(s_.mean())
    p = s_.shift(1).fillna(0.0)
    markov = p * q + (1 - p) * b - p.diff().abs().fillna(0.0) * 0.0005
    static = expo * q + (1 - expo) * b
    bh = q

    fig, ax = plt.subplots(figsize=(12.5, 5.2))
    for ret, c, lw, label in (
        (bh, GREY, 1.2, "QQQ buy & hold"),
        (markov, RED, 1.5, f"Markov regime gate (avg exposure {expo:.0%}, ~monthly refits)"),
        (static, GREEN, 1.8, f"CONSTANT {expo:.0%} QQQ / {1 - expo:.0%} T-bills -- no model at all"),
    ):
        eq = (1 + ret).cumprod()
        ax.plot(eq.index, eq, color=c, lw=lw,
                label=f"{label}   [MDD {dd(eq).min():+.0%}]")
    ax.set_yscale("log")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title('Most famous failure: the regime model\'s celebrated "MDD halving" is '
                 "reproduced by a constant (Cederburg control, TR-02b)", fontsize=11)
    ax.text(0.985, 0.03,
            "the static dial has the same drawdown, higher excess Sharpe, and zero trades\n"
            "-> the Markov model adds nothing over a constant for exposure decisions",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5,
            bbox={"boxstyle": "round", "fc": "white", "ec": GREY, "alpha": 0.85})
    fig.tight_layout()
    fig.savefig(OUT / "fig_markov_static.png", dpi=150)
    plt.close(fig)
    print("[ok] fig_markov_static.png")


def fig_ensemble():
    # holdout (2021+) numbers from scripts/ensemble_mix.py, re-run 2026-07-08
    rows = [
        ("QQQ buy & hold", 0.84, -0.351, GREY),
        ("E1 vote-fraction ensemble\n(52 rules vote -> exposure)", 0.99, -0.158, GREEN),
        ("E4 triple-filter AND", 0.94, -0.137, "#66bb6a"),
        ("in-sample BEST single rule\n(picked on 2015-20, held 2021+)", 0.63, -0.223, RED),
    ]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.4))
    x = np.arange(len(rows))
    for ax, idx, title, fmt in (
        (ax1, 1, "holdout Sharpe (2021+)", "{:+.2f}"),
        (ax2, 2, "holdout max drawdown (2021+)", "{:+.0%}"),
    ):
        vals = [r[idx] for r in rows]
        ax.bar(x, vals, color=[r[3] for r in rows], width=0.62)
        for xi, v in zip(x, vals, strict=True):
            ax.text(xi, v + (0.02 if v >= 0 else -0.005) * (1 if idx == 1 else 10),
                    fmt.format(v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=9, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([r[0] for r in rows], fontsize=8)
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3, axis="y")
        if idx == 2:
            ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    fig.suptitle("Mixing beats picking: the ensemble's win is robustness, not return "
                 "(scripts/ensemble_mix.py)", fontsize=11, y=1.0)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ensemble.png", dpi=150)
    plt.close(fig)
    print("[ok] fig_ensemble.png")


if __name__ == "__main__":
    figs = {"scoreboard": fig_scoreboard, "ensemble": fig_ensemble,
            "combo": fig_combo, "markov": fig_markov_static}
    picked = [a for a in sys.argv[1:] if a in figs] or list(figs)
    for name in picked:
        figs[name]()
    print("done -> docs/img/")
