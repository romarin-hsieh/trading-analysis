"""TR-19 -- Lou-Polk-Skouras (JFE 2019) overnight/intraday decomposition of OUR books.

F0 DECLARATION (pre-committed)
  mechanism  : split every daily return into overnight (prev adj close -> adj open) and
               intraday (adj open -> adj close); attribute each book's return to the two
               clocks. LPS claim (their seat: CRSP broad, 1993-2013): momentum premium is
               ~ALL overnight (+0.98%/mo overnight vs negative intraday); risk premia in
               large caps accrue overnight.
  seat       : 47-name sector universe (the momentum book's home, TR-11 seat), monthly
               top-10 6-1 momentum book, equal weight, 1-bar lag; EW-47 and SPY as
               references. GROSS returns (a decomposition, not a strategy -- costs would
               hit whichever leg one tried to trade; the overnight COST WALL from docs/13
               stands regardless).
  purpose    : DIAGNOSTIC (attribution), not a gate. Two pre-committed questions:
     Q1 where does the momentum book's raw return live (overnight vs intraday)?
     Q2 where does its EXCESS over EW-47 (the selection component) live?
  verdict rule (pre-committed): no PASS/FAIL -- record the split + implications:
     if the book's edge is overnight-dominated, monthly close-fill backtests are fine
     (positions held overnight capture it), but any intraday-exit variant would bleed it;
     also sharpens F1: same-close vs next-close matters more when overnight >> intraday.
  mis-application risk : LOW-MED (our 47 tech names vs CRSP broad; decayed era 2015-26).
  adj-open construction: adj_open = open * (adj_close/close) -- splits/dividends land in
  the overnight leg (same convention as LPS).

POST-RUN AUDIT NOTE (pre-commitment above NOT edited):
  Mechanics all verified clean by adversarial audit: no dividend double-count (ex-div-day
  check: raw overnight -0.40% + factor +0.53% = adjusted +0.12% ~ normal day; dividends
  contribute only +0.78pp/yr of the momentum book's overnight leg), open-price quality fine
  (0 missing, open==close 0.43%, removing them moves the headline -12bps), no lookahead
  (shift(2) counterfactual ~unchanged), recomposition residual 2e-16, and the arithmetic
  annualization is CONSERVATIVE here (compound overnight share is 89% > 81%). Rebalance-
  phase sweep: overnight excess +9.7%..+13.0%/yr across all 21 phases (21/21 positive).
  TWO NARRATIVE CORRECTIONS (implemented below):
  (a) the overnight excess is NOT momentum "selection": a pure trailing-vol top-10 control
      book (no momentum signal at all) replicates +11.2%/yr of it (vs momentum's +11.4%).
      The subject is HIGH-VOL/BETA TILT carrying the universe's overnight premium -- fully
      consistent with TR-11's verdict (momentum = beta, FAILED as selection).
  (b) "consistent with LPS" is qualitative and in-seat only: construct/universe/survivorship
      differ from LPS, and the 2023-26 sub-period intraday excess turned POSITIVE (+6.4%/yr),
      deviating from the LPS pattern. Not evidence of "no decay".

Run: uv run python scripts/tests/tr19_overnight_intraday.py
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")

import sector_strategies as ss  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402


def legs(symbols):
    """Per-name overnight and intraday simple-return panels (adjusted)."""
    store = DuckStore("./data")
    ac = store.load_close_pivot(symbols, column="adj_close")
    c = store.load_close_pivot(symbols, column="close")
    o = store.load_close_pivot(symbols, column="open")
    f = (ac / c).replace([np.inf, -np.inf], np.nan)
    ao = o * f
    on = (ao / ac.shift(1) - 1.0)
    intr = (ac / ao - 1.0)
    return on, intr, ac


def ann(x: pd.Series) -> float:
    return float(x.mean() * 252)


def sh(x: pd.Series) -> float:
    s = x.std()
    return float(x.mean() / s * np.sqrt(252)) if s > 0 else float("nan")


def main():
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    on, intr, ac = legs(allsyms)
    on, intr = on.loc["2015-06-01":], intr.loc["2015-06-01":]
    total = (1 + on) * (1 + intr) - 1

    # monthly top-10 6-1 momentum weights (1-bar lag), same seat as TR-11
    lp = np.log(ac)
    mom = (lp.shift(21) - lp.shift(126)).reindex(total.index)
    vol = ac.pct_change().rolling(126).std().shift(1).reindex(total.index)   # audit control
    reb = pd.Series(False, index=total.index)
    reb.iloc[::21] = True

    def top10_weights(score: pd.DataFrame) -> pd.DataFrame:
        w = pd.DataFrame(0.0, index=total.index, columns=total.columns)
        for t in total.index[reb.to_numpy()]:
            row = score.loc[t].dropna().sort_values(ascending=False)
            top = row.index[:10]
            if len(top):
                w.loc[t, top] = 1.0 / len(top)
        return w.where(reb.reindex(total.index), np.nan).ffill().shift(1).fillna(0.0)

    w = top10_weights(mom)
    wv = top10_weights(vol)                                                  # vol-tilt control

    def book(panel, weights=None):
        return ((w if weights is None else weights) * panel).sum(axis=1)

    ew_on, ew_id = on.mean(axis=1), intr.mean(axis=1)
    mo_on, mo_id = book(on), book(intr)
    vo_on, vo_id = book(on, wv), book(intr, wv)
    spy_on, spy_id, _ = legs(["SPY"])
    spy_on, spy_id = spy_on.iloc[:, 0].reindex(mo_on.index), spy_id.iloc[:, 0].reindex(mo_on.index)

    print("=" * 96)
    print(f"TR-19  OVERNIGHT / INTRADAY DECOMPOSITION (LPS 2019)  47-name seat, "
          f"{total.index[0].date()}..{total.index[-1].date()}  [arith ann = mean*252]")
    print("=" * 96)
    print(f"{'book':26s} {'ann OVERNIGHT':>14s} {'ann INTRADAY':>14s} {'SR on':>7s} {'SR id':>7s}")
    rows = {}
    for name, o_, i_ in (("momentum top-10", mo_on, mo_id),
                         ("vol top-10 (control)", vo_on, vo_id),
                         ("EW-47", ew_on, ew_id), ("SPY", spy_on, spy_id)):
        rows[name] = (ann(o_), ann(i_), sh(o_), sh(i_))
        print(f"{name:26s} {ann(o_):>+13.2%} {ann(i_):>+13.2%} {sh(o_):>+7.2f} {sh(i_):>+7.2f}")
    ex_on, ex_id = mo_on - ew_on, mo_id - ew_id
    xv_on, xv_id = vo_on - ew_on, vo_id - ew_id
    print("-" * 96)
    print(f"{'momentum MINUS EW':26s} {ann(ex_on):>+13.2%} {ann(ex_id):>+13.2%} "
          f"{sh(ex_on):>+7.2f} {sh(ex_id):>+7.2f}")
    print(f"{'vol-control MINUS EW':26s} {ann(xv_on):>+13.2%} {ann(xv_id):>+13.2%} "
          f"{sh(xv_on):>+7.2f} {sh(xv_id):>+7.2f}")
    on_share_mo = ann(mo_on) / (ann(mo_on) + ann(mo_id)) if (ann(mo_on) + ann(mo_id)) else np.nan
    print(f"\nQ1: momentum book raw return: {ann(mo_on):+.2%}/yr overnight vs {ann(mo_id):+.2%}/yr "
          f"intraday (overnight share {on_share_mo:.0%} arith; ~89% compound). The universe itself")
    print("    is overnight-tilted too (EW-47 72%, SPY 63%) -- a market-level clock phenomenon.")
    print(f"Q2 (audit-corrected attribution): the top-10 book's overnight excess over EW "
          f"({ann(ex_on):+.2%}/yr) is")
    print(f"    ~fully replicated by a NO-momentum trailing-vol top-10 control ({ann(xv_on):+.2%}/yr):")
    print("    the subject is HIGH-VOL/BETA TILT carrying the universe overnight premium, NOT momentum")
    print("    selection -- consistent with TR-11 (momentum = beta; selection increment FAILED).")
    print("    Qualitatively in the LPS direction (in-seat only; 2023-26 intraday excess turned +).")
    print("READ: diagnostic only. The overnight COST WALL (docs/13: gross 0.89 -> net -0.97) still")
    print("kills trading the split directly; the value is attribution + F1 fill-convention sharpening")
    print("(a book whose return accrues ~85-90% overnight makes same-close-vs-next-close conventions")
    print("first-order; monthly close-fill backtests capture the overnight leg by holding positions).")
    print("=" * 96)

    # chart: cumulative legs
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=False)
    for ax, (name, o_, i_) in zip(axes, (("momentum top-10 book", mo_on, mo_id),
                                         ("momentum MINUS EW-47", ex_on, ex_id)), strict=True):
        ax.plot((1 + o_.fillna(0)).cumprod(), color="#1565c0", lw=1.4,
                label=f"overnight [{ann(o_):+.1%}/yr]")
        ax.plot((1 + i_.fillna(0)).cumprod(), color="#c62828", lw=1.4,
                label=f"intraday [{ann(i_):+.1%}/yr]")
        ax.set_yscale("log")
        ax.set_title(name, fontsize=10.5)
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)
    axes[1].plot((1 + xv_on.fillna(0)).cumprod(), color="#757575", lw=1.2, ls="--",
                 label=f"vol-control overnight [{ann(xv_on):+.1%}/yr]")
    axes[1].legend(fontsize=8.5)
    axes[1].set_title("momentum MINUS EW-47 -- and the no-momentum vol control", fontsize=10)
    fig.suptitle("TR-19: which clock hosts the return? (LPS 2019 decomposition, 47-name seat)",
                 fontsize=11, y=1.0)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr19_overnight.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
