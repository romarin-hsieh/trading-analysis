"""TR-28 -- Quarterly ROE (HXZ construction): the TR-24B priced reopen, executed.

F0 DECLARATION (pre-committed)
  reopen basis : TR-24B found ANNUAL EDGAR ROE weak (ICIR ~ +0.11) and SUBSUMED by GP
               (orthogonal increment flipped sign). It scoped the honest caveat that
               HXZ's q-factor uses QUARTERLY earnings over lagged book equity -- annual
               may simply be too stale. The 10-Q panel turns out to be already ingested
               (43k quarterly NetIncomeLoss rows, 495 names, as_of 2009+), so the reopen
               costs $0. Construction hazard identified up front: stored 10-Q income
               values are YTD-cumulative (verified on AAPL FY2024: Q2 = 57.6B = H1, not
               the quarter), so quarterly NI must be recovered by within-fiscal-year
               YTD differencing; Q4 = 10-K FY minus Q3-YTD. Book equity is a point
               value (no YTD issue). PIT clock: each quarterly figure becomes known at
               the LATER filing date of its two pieces.
  seat         : same ~495-name panel as TR-24/26/27, 63d rank-IC gate.
  PRE-COMMITTED CHECKS
    CAL         : annual EDGAR ROE must reproduce TR-24B's weak reading
                  (ICIR within +-0.05 of +0.11). Fail -> STOP, no verdict.
    C1 standalone: quarterly ROE 63d rank-IC. ICIR >= 0.15 and mean IC > 0 -> real;
                  0 < ICIR < 0.15 -> WEAK; else FAIL.
    C2 subsumption (the reopen question): per-date cross-sectional OLS of quarterly-ROE
                  ranks on GP ranks; residual's IC vs forward returns. Residual
                  mean IC > 0 AND ICIR >= 0.10 -> NOT subsumed; else GP subsumes the
                  quarterly construction too.
  SUPPLEMENTARY (reported, not gated -- TR-27 lesson): members-only masked ICIR for
                  quarterly ROE, for the inclusion-look-ahead-adjusted reading.
  VERDICT RULE (pre-committed):
    C1(real|weak) & C2 pass -> QUARTERLY-SIGNAL-REAL (TR-24B's subsumption does NOT
                               extend to the faithful HXZ clock; registry updated)
    C1(real|weak) & C2 fail -> SUBSUMED-CONFIRMED (GP subsumes ROE at BOTH clocks;
                               q-factor chapter closes for this panel)
    C1 fail                  -> NO-STANDALONE-SIGNAL (dead regardless of GP)
  anti-HARKing : construction fixed as specified above before results were seen;
               zero new F5 trials (single pre-registered configuration).

Run: uv run python scripts/tests/tr28_quarterly_roe.py   (~3-5 min)
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
sys.path.insert(0, "scripts/collect")

from sp500_constituents import load_membership  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.fundamentals import build_all  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
)

FP_ORD = {"Q1": 1, "Q2": 2, "Q3": 3}


def _current_rows(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol, fy, fp): the CURRENT-period figure (latest period_end),
    dropping prior-year comparatives filed in the same document."""
    return (df.sort_values("period_end")
              .groupby(["symbol", "fy", "fp"], as_index=False).tail(1))


def quarterly_roe_events(fund: pd.DataFrame) -> pd.DataFrame:
    """Long frame: symbol, known (as_of), roe_q -- HXZ construction with YTD differencing."""
    ni_q = _current_rows(fund[(fund["form"] == "10-Q") & (fund["tag"] == "NetIncomeLoss")])
    ni_y = _current_rows(fund[(fund["form"] == "10-K") & (fund["tag"] == "NetIncomeLoss")])
    be = _current_rows(fund[fund["tag"] == "StockholdersEquity"])

    rows = []
    for sym, g in ni_q.groupby("symbol"):
        gy = ni_y[ni_y["symbol"] == sym].set_index("fy")
        for fy, q in g.groupby("fy"):
            q = q[q["fp"].isin(FP_ORD)].copy()
            q["o"] = q["fp"].map(FP_ORD)
            q = q.sort_values("o")
            prev_val, prev_asof = 0.0, pd.Timestamp.min
            for _, r in q.iterrows():
                rows.append({"symbol": sym, "fy": fy, "o": r["o"],
                             "period_end": r["period_end"],
                             "known": max(r["as_of"], prev_asof),
                             "ni_q": r["val"] - prev_val})
                prev_val, prev_asof = r["val"], r["as_of"]
            if fy in gy.index and len(q) and q["o"].max() == 3:
                y = gy.loc[fy]
                y = y.iloc[-1] if isinstance(y, pd.DataFrame) else y
                rows.append({"symbol": sym, "fy": fy, "o": 4,
                             "period_end": y["period_end"],
                             "known": max(y["as_of"], q["as_of"].max()),
                             "ni_q": y["val"] - prev_val})
    niq = pd.DataFrame(rows)

    # lagged book equity: latest BE with period_end strictly BEFORE the quarter's end
    be_s = be.sort_values("period_end")
    out = []
    for sym, g in niq.groupby("symbol"):
        b = be_s[be_s["symbol"] == sym]
        if b.empty:
            continue
        pe = b["period_end"].to_numpy()
        for _, r in g.iterrows():
            i = np.searchsorted(pe, np.datetime64(r["period_end"])) - 1
            if i < 0:
                continue
            brow = b.iloc[i]
            if brow["val"] == 0 or pd.isna(brow["val"]):
                continue
            out.append({"symbol": sym,
                        "known": max(r["known"], brow["as_of"]),
                        "roe_q": r["ni_q"] / brow["val"]})
    ev = pd.DataFrame(out).dropna()
    return ev[np.isfinite(ev["roe_q"])]


def wide_from_events(ev: pd.DataFrame, dates, syms) -> pd.DataFrame:
    """Daily wide frame: last event value known at or before each date (PIT ffill)."""
    w = (ev.sort_values("known")
           .pivot_table(index="known", columns="symbol", values="roe_q", aggfunc="last"))
    w = (w.reindex(pd.DatetimeIndex(sorted(set(w.index).union(dates))))
          .sort_index().ffill().reindex(dates))
    return w.reindex(columns=syms)


def ortho_residual(y_wide: pd.DataFrame, x_wide: pd.DataFrame) -> pd.DataFrame:
    """Per-date cross-sectional rank OLS residual of y on x."""
    idx = y_wide.index.intersection(x_wide.index)
    cols = y_wide.columns.intersection(x_wide.columns)
    out = pd.DataFrame(np.nan, index=idx, columns=cols)
    Y, X = y_wide.loc[idx, cols], x_wide.loc[idx, cols]
    for ts in idx:
        yv, xv = Y.loc[ts], X.loc[ts]
        ok = yv.notna() & xv.notna()
        if int(ok.sum()) < 30:
            continue
        yr = yv[ok].rank()
        xr = xv[ok].rank()
        b = np.polyfit(xr, yr, 1)
        out.loc[ts, ok.index[ok]] = yr - (b[0] * xr + b[1])
    return out


def main():
    store = DuckStore("./data")
    syms = [s for s in store.list_symbols("1d") if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    facs = build_all(fund, px, syms)
    gp = facs["gross_profitability"]
    fwd = forward_returns(px, 63)

    print("=" * 100)
    print(f"TR-28  QUARTERLY ROE (HXZ construction) -- {len(syms)} names")
    print("=" * 100)

    # ---- CAL: annual ROE reproduces TR-24B weak reading ----
    if "roe" in facs:
        s_ann = ic_summary(cross_sectional_ic(facs["roe"], fwd))
    else:  # build annual ROE = FY NI / lagged BE via same helpers
        ni_y = _current_rows(fund[(fund["form"] == "10-K") & (fund["tag"] == "NetIncomeLoss")])
        ev = []
        be = _current_rows(fund[fund["tag"] == "StockholdersEquity"]).sort_values("period_end")
        for sym, g in ni_y.groupby("symbol"):
            b = be[be["symbol"] == sym]
            if b.empty:
                continue
            pe = b["period_end"].to_numpy()
            for _, r in g.iterrows():
                i = np.searchsorted(pe, np.datetime64(r["period_end"])) - 1
                if i < 0 or b.iloc[i]["val"] == 0:
                    continue
                ev.append({"symbol": sym, "known": max(r["as_of"], b.iloc[i]["as_of"]),
                           "roe_q": r["val"] / b.iloc[i]["val"]})
        ann_wide = wide_from_events(pd.DataFrame(ev), px.index, syms)
        s_ann = ic_summary(cross_sectional_ic(ann_wide, fwd))
    cal = abs(s_ann["icir"] - 0.11) <= 0.05
    print(f"CAL annual ROE: mean IC {s_ann['mean_ic']:+.3f} / ICIR {s_ann['icir']:+.2f} "
          f"(TR-24B: ~+0.11+-0.05) -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("CALIBRATION FAILED -- no verdict; reconcile with TR-24B machinery first.")
        return

    # ---- quarterly ROE ----
    ev = quarterly_roe_events(fund)
    print(f"quarterly events: {len(ev):,} across {ev['symbol'].nunique()} names, "
          f"known {ev['known'].min().date()}..{ev['known'].max().date()}")
    roeq = wide_from_events(ev, px.index, syms)

    s_q = ic_summary(cross_sectional_ic(roeq, fwd))
    c1 = "real" if (s_q["icir"] >= 0.15 and s_q["mean_ic"] > 0) else (
         "weak" if (s_q["icir"] > 0 and s_q["mean_ic"] > 0) else "fail")
    print(f"C1 quarterly ROE standalone: mean IC {s_q['mean_ic']:+.3f} / ICIR {s_q['icir']:+.2f} "
          f"-> {c1.upper()}")

    # ---- C2: GP-orthogonal residual ----
    resid = ortho_residual(roeq, gp)
    s_r = ic_summary(cross_sectional_ic(resid, fwd))
    c2 = (s_r["mean_ic"] > 0) and (s_r["icir"] >= 0.10)
    print(f"C2 GP-orthogonal residual: mean IC {s_r['mean_ic']:+.3f} / ICIR {s_r['icir']:+.2f} "
          f"(rules mean>0 & ICIR>=0.10) -> {'NOT SUBSUMED' if c2 else 'SUBSUMED'}")

    # ---- supplementary: members-only (TR-27 lesson) ----
    mem = load_membership()
    common = roeq.index.intersection(fwd.index)
    snap = mem.index
    tsets = mem["tickers"].to_numpy()
    pos = np.searchsorted(snap, common, side="right") - 1
    msk = pd.DataFrame(
        [[any(a in tsets[p] for a in {"META": ("META", "FB"), "GOOGL": ("GOOGL", "GOOG")}.get(s, (s,)))
          if p >= 0 else False for s in syms] for p in pos],
        index=common, columns=syms)
    s_qm = ic_summary(cross_sectional_ic(roeq.reindex(common).where(msk), fwd))
    print(f"supplementary members-only quarterly ROE: mean IC {s_qm['mean_ic']:+.3f} / "
          f"ICIR {s_qm['icir']:+.2f} (reported, not gated)")

    if c1 == "fail":
        verdict = "NO-STANDALONE-SIGNAL"
    elif c2:
        verdict = "QUARTERLY-SIGNAL-REAL (subsumption does NOT extend to the HXZ clock)"
    else:
        verdict = "SUBSUMED-CONFIRMED (GP subsumes ROE at both clocks)"
    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # chart
    fig, ax = plt.subplots(figsize=(9, 4.4))
    labels = ["annual ROE\n(CAL, TR-24B)", "quarterly ROE\n(HXZ clock)",
              "quarterly ROE\nmembers-only", "GP-orthogonal\nresidual"]
    vals = [s_ann["icir"], s_q["icir"], s_qm["icir"], s_r["icir"]]
    cols = ["#90a4ae", "#1565c0", "#6a1b9a", "#f9a825"]
    ax.bar(labels, vals, color=cols, alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(0.10, color="#c62828", ls="--", lw=1.2, label="C2 bar (0.10)")
    for i, v in enumerate(vals):
        ax.annotate(f"{v:+.2f}", (i, v), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=10)
    ax.set_ylabel("ICIR (63d rank-IC)")
    ax.set_title("TR-28: quarterly ROE (HXZ construction) vs GP subsumption", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr28_qroe.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
