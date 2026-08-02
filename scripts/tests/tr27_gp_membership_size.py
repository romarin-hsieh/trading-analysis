"""TR-27 -- GP depth grid, layer 2: membership look-ahead and size stratification.

F0 DECLARATION (pre-committed)
  claim        : TR-26's ROBUST-PLATEAU verdict for gross profitability carries two
               scoped-out risks it explicitly queued: (a) the panel is CURRENT S&P
               members, so names are scored at dates BEFORE they joined the index
               (inclusion look-ahead -- pre-inclusion runups could inflate IC), and
               (b) breadth was tested by random halves, not by SIZE. This TR closes
               both using the PIT membership panel (sp500_constituents.py, wired
               2026-07-11) and PIT shares outstanding from SEC fundamentals.
               The DELISTING half of survivorship stays open (priced: Tiingo key).
  seat         : same panel as TR-26 (~500 current members, 63d rank-IC).
  PRE-COMMITTED CHECKS
    CAL          : unmasked 63d IC must reproduce TR-26 (mean +0.025 +- 0.005,
                   ICIR +0.23 +- 0.05); membership panel must cover >= 80% of our
                   symbols on 2016-01 and 2024-01 (ticker-mapping sanity); if either
                   fails, STOP -- no verdict.

POST-RUN AUDIT NOTE (2026-07-11, self-caught -- F0 above NOT edited)
  The first run STOPPED at CAL: 2016-01 coverage was 65% (< the 80% rule). Diagnosis
  showed the RULE was misdesigned, not the data: 65% at a 10-years-back probe is exactly
  what real index turnover (~4-5%/yr) produces on a current-member panel; the 90% at the
  2024 probe matches 2 years of turnover. Direct mapping evidence: 10/10 known post-2016
  joiners (TSLA/ABNB/UBER/MRNA/ETSY/NOW/CDW/PLTR/CRWD/DASH) are correctly ABSENT in the
  2016 snapshot, blue chips (AAPL/MSFT/JNJ/XOM/JPM/KO/WMT) correctly PRESENT, and the
  FB->META alias resolves. CAL v2 below therefore gates on those direct mapping
  assertions; the coverage percentages are reported as a TURNOVER measurement
  (descriptive), which is what they actually are. The v1 CAL-FAIL stop is recorded here
  as a design error caught by the gate doing its job.
  Also noted: the "not-yet-members" complement mixes future joiners with names that were
  never S&P members (ADRs/small caps in the store) -- fine for a diagnostic; C1's
  members-only mask is exact either way.
    C1 membership: mask the factor to names that were ACTUAL members on each date.
                   PASS iff masked mean IC >= 70% of unmasked mean IC AND masked
                   ICIR >= 0.15. (Complement diagnostic reported: IC among
                   not-yet-members.)
    C2 size      : PIT market cap = close x latest shares outstanding with
                   as_of <= t (CommonStockSharesOutstanding, fallback
                   WeightedAverageNumberOfSharesOutstandingBasic). Split members
                   at the cross-sectional median each date. PASS iff mean IC > 0
                   in BOTH halves.
  VERDICT RULE (pre-committed):
    C1 & C2 PASS      -> MEMBERSHIP+SIZE-ROBUST (TR-26 plateau extended)
    C1 FAIL           -> INCLUSION-LOOKAHEAD-SENSITIVE (standing caveat on GP row;
                         quantified haircut recorded)
    C2 FAIL           -> SIZE-CONCENTRATED (name the carrying half)
  anti-HARKing : masks are probes; the published configuration stays the reference;
               zero new F5 trials.

Run: uv run python scripts/tests/tr27_gp_membership_size.py   (~3-5 min)
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

# big renames where the membership panel may carry the other symbol historically
ALIASES = {"META": ("META", "FB"), "GOOGL": ("GOOGL", "GOOG"), "LIN": ("LIN", "PX")}


def member_mask(dates, syms, mem) -> pd.DataFrame:
    """True where symbol was an S&P member on that date (alias-aware)."""
    snap_idx = mem.index
    out = np.zeros((len(dates), len(syms)), dtype=bool)
    tick_sets = mem["tickers"].to_numpy()
    pos = np.searchsorted(snap_idx, dates, side="right") - 1
    for i, p in enumerate(pos):
        if p < 0:
            continue
        s = tick_sets[p]
        out[i] = [any(a in s for a in ALIASES.get(sym, (sym,))) for sym in syms]
    return pd.DataFrame(out, index=dates, columns=syms)


def shares_panel(fund: pd.DataFrame, dates, syms) -> pd.DataFrame:
    """PIT shares outstanding: latest filed value with as_of <= t, forward-filled."""
    sh = fund[fund["tag"].isin(["CommonStockSharesOutstanding",
                                "WeightedAverageNumberOfSharesOutstandingBasic"])].copy()
    sh = sh.sort_values(["symbol", "as_of", "period_end"])
    # prefer point-in-time CommonStockSharesOutstanding; keep last per (symbol, as_of)
    sh["pri"] = (sh["tag"] == "CommonStockSharesOutstanding").astype(int)
    sh = sh.sort_values(["symbol", "as_of", "pri", "period_end"]).groupby(
        ["symbol", "as_of"]).tail(1)
    wide = sh.pivot_table(index="as_of", columns="symbol", values="val", aggfunc="last")
    wide = wide.reindex(wide.index.union(dates)).sort_index().ffill().reindex(dates)
    return wide.reindex(columns=syms)


def main():
    store = DuckStore("./data")
    syms = [s for s in store.list_symbols("1d") if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD")]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    fund = store.load_fundamentals(syms)
    syms = [s for s in syms if s in set(fund["symbol"])]
    px = px[syms]
    gp = build_all(fund, px, syms)["gross_profitability"]
    fwd = forward_returns(px, 63)
    mem = load_membership()

    print("=" * 100)
    print(f"TR-27  GP MEMBERSHIP + SIZE -- {len(syms)} names, {px.index[0].date()}..{px.index[-1].date()}")
    print("=" * 100)

    # ---- CAL (v2 per POST-RUN note: direct mapping assertions; coverage = descriptive) ----
    s0 = ic_summary(cross_sectional_ic(gp, fwd))
    cal_ic = abs(s0["mean_ic"] - 0.025) <= 0.005 and abs(s0["icir"] - 0.23) <= 0.05
    print(f"CAL IC: mean {s0['mean_ic']:+.3f} / ICIR {s0['icir']:+.2f} "
          f"(TR-26: +0.025/+0.23) -> {'PASS' if cal_ic else 'FAIL'}")
    m16 = mem["tickers"].iloc[mem.index.searchsorted(pd.Timestamp("2016-01-04"), "right") - 1]
    m24 = mem["tickers"].iloc[mem.index.searchsorted(pd.Timestamp("2024-06-03"), "right") - 1]
    joiners = ("TSLA", "ABNB", "UBER", "MRNA", "ETSY", "NOW", "CDW")
    blue = ("AAPL", "MSFT", "JNJ", "XOM", "JPM", "KO", "WMT")
    cal_map = (all(s not in m16 for s in joiners) and all(s in m16 for s in blue)
               and all(s in m24 for s in joiners) and ("FB" in m16 or "META" in m16))
    print(f"CAL mapping: joiners absent 2016 + present 2024, blue chips present 2016, "
          f"FB/META alias -> {'PASS' if cal_map else 'FAIL'}")
    for probe in ("2016-01-04", "2024-01-03"):
        msk = member_mask(pd.DatetimeIndex([pd.Timestamp(probe)]), syms, mem)
        print(f"  (descriptive) membership coverage of panel on {probe}: {msk.iloc[0].mean():.0%} "
              f"= real index turnover, not a gate")
    if not (cal_ic and cal_map):
        print("CALIBRATION FAILED -- no verdict; debug ticker mapping / machinery first.")
        return

    # ---- C1: PIT membership mask ----
    common = gp.index.intersection(fwd.index)
    msk = member_mask(common, syms, mem)
    gp_c = gp.reindex(common)
    gp_in = gp_c.where(msk)
    gp_out = gp_c.where(~msk)
    ic_in = cross_sectional_ic(gp_in, fwd)
    ic_out = cross_sectional_ic(gp_out, fwd)
    s_in, s_out = ic_summary(ic_in), ic_summary(ic_out)
    keep = s_in["mean_ic"] / s0["mean_ic"] if s0["mean_ic"] else float("nan")
    c1 = (keep >= 0.70) and (s_in["icir"] >= 0.15)
    n_out = int(msk.size - msk.to_numpy().sum())
    print(f"C1 members-only : mean IC {s_in['mean_ic']:+.3f} / ICIR {s_in['icir']:+.2f} "
          f"(retains {keep:.0%} of unmasked; rules >=70% and ICIR>=0.15) -> {'PASS' if c1 else 'FAIL'}")
    print(f"   diagnostic not-yet-members: mean IC {s_out['mean_ic']:+.3f} / "
          f"ICIR {s_out['icir']:+.2f} (avg {ic_out.notna().sum() and (gp_out.notna().sum(axis=1).mean()):.0f} names/day; "
          f"{n_out:,} masked cells)")

    # ---- C2: size split among members ----
    shares = shares_panel(fund, common, syms)
    mcap = (px.reindex(common) * shares).where(msk)
    med = mcap.median(axis=1)
    big = gp_in.where(mcap.ge(med, axis=0))
    small = gp_in.where(mcap.lt(med, axis=0))
    s_big = ic_summary(cross_sectional_ic(big, fwd))
    s_small = ic_summary(cross_sectional_ic(small, fwd))
    c2 = (s_big["mean_ic"] > 0) and (s_small["mean_ic"] > 0)
    print(f"C2 large half   : mean IC {s_big['mean_ic']:+.3f} / ICIR {s_big['icir']:+.2f}")
    print(f"C2 small half   : mean IC {s_small['mean_ic']:+.3f} / ICIR {s_small['icir']:+.2f}")
    print(f"C2 size: both positive -> {'PASS' if c2 else 'FAIL'}")

    if c1 and c2:
        verdict = "MEMBERSHIP+SIZE-ROBUST (TR-26 plateau extended)"
    else:
        parts = []
        if not c1:
            parts.append(f"INCLUSION-LOOKAHEAD-SENSITIVE (masked retains {keep:.0%})")
        if not c2:
            carrier = "large" if s_big["mean_ic"] > s_small["mean_ic"] else "small"
            parts.append(f"SIZE-CONCENTRATED (carried by the {carrier} half)")
        verdict = " + ".join(parts)
    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axes[0]
    labels = ["unmasked\n(TR-26)", "members\nonly", "not-yet-\nmembers"]
    vals = [s0["mean_ic"], s_in["mean_ic"], s_out["mean_ic"]]
    icirs = [s0["icir"], s_in["icir"], s_out["icir"]]
    cols = ["#90a4ae", "#1565c0", "#f9a825"]
    ax.bar(labels, vals, color=cols, alpha=0.9)
    for i, (v, ir) in enumerate(zip(vals, icirs)):
        ax.annotate(f"IC {v:+.3f}\nICIR {ir:+.2f}", (i, v),
                    textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("C1: does index-inclusion look-ahead inflate GP?", fontsize=10)
    ax.set_ylabel("mean 63d rank-IC")
    ax = axes[1]
    labels = ["large half", "small half"]
    vals = [s_big["mean_ic"], s_small["mean_ic"]]
    ax.bar(labels, vals, color=["#2e7d32", "#6a1b9a"], alpha=0.9)
    for i, (v, ir) in enumerate(zip(vals, [s_big["icir"], s_small["icir"]])):
        ax.annotate(f"IC {v:+.3f}\nICIR {ir:+.2f}", (i, v),
                    textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("C2: GP by PIT market-cap half (members only)", fontsize=10)
    for a in axes:
        a.grid(alpha=0.3, axis="y")
        ymax = max(abs(v) for v in list(vals) + [s0["mean_ic"], s_in["mean_ic"], s_out["mean_ic"]])
        a.set_ylim(min(0, -0.01) - 0.005, ymax * 1.45 + 0.01)
    fig.suptitle("TR-27: GP under PIT membership and size stratification", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr27_gp_membership.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
