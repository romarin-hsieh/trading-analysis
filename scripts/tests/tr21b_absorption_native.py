"""TR-21b -- Absorption Ratio RE-OPENED on its NATIVE seat (docs/24 action #2).

F0 DECLARATION (pre-committed)
  reopen basis : TR-21's priced reopen condition -- "true industry-portfolio panel + long
               history incl. 2008" -- is now satisfied at $0 by the Ken French 49-industry
               DAILY portfolios (1926+, CRSP-built, survivorship-free, updated 2026-07-01).
               KLPR's own habitat was ~51 US industries 1998-2010; this panel nests it and
               adds 1987, 2000-02, 2008, 2020, 2022.
  seat         : 49 industries, daily, 1970-2026 (all industries populated); AR machinery
               reused from TR-21 (500d window, top 20% eigenvalues, dAR = (15d-1yr)/1yr sd).
               Market = KF Mkt-RF + RF; cash leg = RF.
  PRE-COMMITTED CHECKS (same rules as TR-21, verbatim):
    C1  PIT-percentile diagnostic: median AR percentile in the month BEFORE the 10 worst
        market months >= 70 with permutation p < 0.05.
    C1b faithful KLPR spike: dAR>1 in the prior month vs the all-month base rate (perm p<0.05).
    C3  gate (dAR>1 -> cash; faithful 3-state also shown) must beat the mean-exposure static
        control (Cederburg) AND the block-shuffled random-gate p95.
  VERDICT RULE (pre-committed):
    C1 pass & C3 pass -> PASSED on native seat (upgrade AR: diagnostic real AND tradable there)
    C1 pass & C3 fail -> PARTIAL on native seat (real fragility DIAGNOSTIC in its habitat;
                         timing iron law still holds) -- TR-21's stock-seat FAILED stands,
                         registry row gains the native-seat split
    C1 fail           -> KLPR's own claim does not replicate even at home (strong FAILED;
                         scrutinize construction before claiming)
  mis-application risk : LOW (this IS the native habitat; residual: 49 vs 51 industries,
               equal treatment of the 2010+ era KLPR never saw).

POST-RUN AUDIT NOTE (2026-07-11, appended -- F0 above NOT edited, code NOT changed)
  Run outcome: C1 FAIL (median pre-event PIT percentile 37, p=0.746 -- KLPR's LEVEL claim
  is directionally INVERTED at home), C1b PASS (dAR>1 spike 7/10 vs 33% base, iid p=0.020),
  C3 FAIL (gate exSR 0.28 vs static-70.8% 0.46; random-gate p95 0.55).
  The pre-committed verdict tree keyed only on C1/C3 and had NO branch for the
  C1-fail + C1b-pass combination, so the script printed "does not replicate even at home"
  -- audit ruled this a MIS-KILL (contradicted by its own C1b PASS, and C1b IS the KLPR
  2011 signature exhibit). Per TR-18 lesson the tree is not edited post-hoc; the verdict
  OF RECORD is the audited three-way split:
    "gate FAILED (timing iron law, 5th confirmation) / diagnostic WEAK-PARTIAL --
     KLPR level claim inverted; the dAR>1 spike weakly replicates (7/10 vs 33%,
     iid p=0.020, cluster-fair circular-shift null p=0.034, passes only at the
     pre-committed K=10; lead is ~one quarter wide, 3/7 hits partly coincident);
     but AR-SPECIFIC -- same-mechanism placebos: 21d realized vol 3/10 (p=0.54),
     avg pairwise corr 5/10 (p=0.26), despite corr(AR, avg-corr) = +0.92."
  Robustness caveats bound to C1b: worst-K sensitivity (K=5 p=0.056 / K=15 p=0.106 /
  K=20 p=0.064 under the fair null); Bonferroni x2 over {C1, C1b}: iid 0.040, fair null
  0.068. Report as SUGGESTIVE, never as a clean p=0.02 point.
  C3 audit extras (no bug found): gate sits at the 7th percentile of 1000 run-length-
  preserving random gates; zero-cost exSR still 0.28; faithful 3-state MDD -25.7% but
  exSR 0.26 vs any-static 0.46 (leverage invariance) -- the gate dodged 4.5/10 of the
  worst months and STILL lost: cleanest "diagnostic true, timing dead" demo to date.

Run: uv run python scripts/tests/tr21b_absorption_native.py   (~2-4 min)
"""

from __future__ import annotations

import itertools
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

from tr21_absorption_ratio import absorption_series, avg_corr_series  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown  # noqa: E402
from trading_analysis.factors.attribution import _ff_csv_direct  # noqa: E402

COST = 0.0005
SEED = 0
START = "1970-01-01"


def load_kf49_daily() -> pd.DataFrame:
    import io
    import urllib.request
    import zipfile
    url = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
           "49_Industry_Portfolios_daily_CSV.zip")
    raw = urllib.request.urlopen(url, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
    lines = text.splitlines()
    hdr = next(i for i, ln in enumerate(lines)
               if ln.strip().startswith(",") or (ln.strip().lower().startswith("agric") is False and ln.count(",") > 40 and not ln.strip()[:8].isdigit()))
    # simpler: find the first line whose first token is a column header row (many commas, no date)
    hdr = next(i for i, ln in enumerate(lines) if ln.count(",") >= 48 and not ln.strip()[:8].isdigit())
    # value-weighted table ends at the first non-date line after data begins
    data = []
    cols = [c.strip() for c in lines[hdr].split(",")][1:]
    for ln in lines[hdr + 1:]:
        tok = ln.strip().split(",")[0].strip()
        if len(tok) == 8 and tok.isdigit():
            data.append(ln)
        elif data:
            break                                           # end of the first (VW) table
    df = pd.read_csv(io.StringIO("\n".join(data)), header=None)
    df.columns = ["date", *cols]
    df.index = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df = df.drop(columns="date").astype(float) / 100.0
    return df.where(df > -0.99)                             # -99.99 = missing


def main():
    rng = np.random.default_rng(SEED)
    r = load_kf49_daily().loc[START:]
    keep = r.columns[r.notna().mean() > 0.99]
    r = r[keep].dropna()
    ff = _ff_csv_direct("F-F_Research_Data_Factors_daily") / 100.0
    ff = ff.reindex(r.index).ffill()
    mkt = (ff["Mkt-RF"] + ff["RF"]).rename("mkt")
    rf = ff["RF"]
    print("=" * 100)
    print(f"TR-21b  ABSORPTION RATIO ON ITS NATIVE SEAT -- {r.shape[1]} KF industries daily, "
          f"{r.index[0].date()}..{r.index[-1].date()} ({len(r)} days)")
    print("=" * 100)

    ar = absorption_series(r)
    d15, d253, s253 = ar.rolling(15).mean(), ar.rolling(253).mean(), ar.rolling(253).std()
    dar = ((d15 - d253) / s253).dropna()

    # ---- C1: PIT percentile before the 10 worst market months ----
    mkt_al = mkt.reindex(ar.index).fillna(0.0)
    mm = (1 + mkt_al).groupby(mkt_al.index.to_period("M")).prod() - 1
    worst = mm.nsmallest(10)
    arv = ar.to_numpy()
    pct = pd.Series([(arv[: i + 1] <= arv[i]).mean() for i in range(len(arv))], index=ar.index)
    pre = []
    for pm in worst.index:
        anchor = (pm - 1).to_timestamp(how="end")
        w = pct.loc[:anchor].tail(5)
        if len(w):
            pre.append(float(w.mean()) * 100)
    pre_med = float(np.median(pre))
    ends = pct.groupby(pct.index.to_period("M")).apply(lambda s: float(s.tail(5).mean()) * 100)
    ends = ends.iloc[24:]
    null = np.array([np.median(rng.choice(ends.to_numpy(), size=len(pre), replace=False))
                     for _ in range(10_000)])
    p_c1 = float((null >= pre_med).mean())
    c1 = pre_med >= 70 and p_c1 < 0.05
    print(f"C1 (PIT pctile): median AR percentile in month before 10 worst market months = "
          f"{pre_med:.0f} (perm p={p_c1:.4f}) -> {'PASS' if c1 else 'FAIL'}")
    print(f"   worst months: {', '.join(str(m) for m in worst.index)}")
    # C1b faithful spike
    spike_m = (dar > 1.0).groupby(dar.index.to_period("M")).max()
    hits = [bool(spike_m.get(pm - 1, False)) for pm in worst.index if (pm - 1) in spike_m.index]
    base = spike_m.iloc[24:].astype(float)
    null_b = np.array([rng.choice(base.to_numpy(), size=len(hits), replace=False).mean()
                       for _ in range(10_000)])
    p_c1b = float((null_b >= np.mean(hits)).mean())
    print(f"C1b (faithful dAR>1 spike in prior month): {sum(hits)}/{len(hits)} vs base "
          f"{base.mean():.0%} (perm p={p_c1b:.2f}) -> {'PASS' if p_c1b < 0.05 else 'FAIL'}")
    ac = avg_corr_series(r)
    cmn = ar.reindex(ac.index).dropna()
    print(f"C2 corr(AR, avg pairwise corr) = "
          f"{float(np.corrcoef(cmn.to_numpy(), ac.reindex(cmn.index).to_numpy())[0,1]):+.2f}")

    # ---- C3 gate on the market, cash = RF ----
    sig = (dar <= 1.0).astype(float)
    common = mkt.loc[dar.index[0]:dar.index[-1]].index.intersection(dar.index.union(mkt.index))
    common = mkt.loc[dar.index[0]:dar.index[-1]].index
    s_ = sig.reindex(common).ffill().fillna(1.0)
    q, b = mkt.loc[common].fillna(0.0), rf.loc[common].fillna(0.0)
    pos = s_.shift(1).fillna(1.0)
    gate = pos * q + (1 - pos) * b - pos.diff().abs().fillna(0.0) * COST
    dar_al = dar.reindex(common).ffill()
    expo3 = pd.Series(np.where(dar_al > 1, 0.0, np.where(dar_al < -1, 1.0, 0.5)), index=common)
    p3 = expo3.shift(1).fillna(0.5)
    gate3 = p3 * q + (1 - p3) * b - p3.diff().abs().fillna(0.0) * COST
    expo = float(pos.mean())
    static = expo * q + (1 - expo) * b
    vraw = (q - b) / q.rolling(21).std().shift(1).pow(2).clip(lower=1e-8)
    volm = b + vraw * ((q - b).std() / vraw.std())
    bh = q

    def exsh(x):
        e = (x - b).dropna()
        return float(e.mean() / e.std() * np.sqrt(252))

    runs = [(k, len(list(g))) for k, g in itertools.groupby(pos.to_numpy())]
    def shuffle_gate():
        order = rng.permutation(len(runs))
        arr = np.concatenate([np.full(runs[i][1], runs[i][0]) for i in order])
        p = pd.Series(arr[: len(q)], index=q.index)
        return exsh(p * q + (1 - p) * b - p.diff().abs().fillna(0.0) * COST)
    placebo = np.array([shuffle_gate() for _ in range(200)])

    print(f"\nC3 GATE (avg exposure {expo:.0%}; {common.min().date()}..{common.max().date()}):")
    print(f"{'book':34s} {'CAGR':>8s} {'exSharpe':>9s} {'MDD':>8s}")
    stats = {}
    for name, ret in (("market buy&hold", bh), ("AR gate", gate),
                      ("AR gate faithful 3-state", gate3),
                      (f"STATIC {expo:.0%} (Cederburg)", static), ("1/sigma^2 vol-managed", volm)):
        eq = (1 + ret.dropna()).cumprod()
        stats[name] = (exsh(ret), max_drawdown(eq))
        print(f"{name:34s} {cagr(eq):>+8.2%} {stats[name][0]:>+9.2f} {stats[name][1]:>+8.1%}")
    g_sh, g_dd = stats["AR gate"]
    s_sh, s_dd = stats[f"STATIC {expo:.0%} (Cederburg)"]
    beats_static = (g_dd > s_dd + 0.01 and g_sh >= s_sh - 0.05) or (g_sh > s_sh + 0.10 and g_dd >= s_dd - 0.01)
    beats_placebo = g_sh >= np.percentile(placebo, 95)
    c3 = beats_static and beats_placebo
    print(f"placebo p95 = {np.percentile(placebo,95):+.2f}; beats static: {beats_static}; "
          f"beats placebo: {beats_placebo} -> C3 {'PASS' if c3 else 'FAIL'}")

    print("-" * 100)
    if c1 and c3:
        v = "PASSED on native seat -- AR upgrades to real AND tradable in its habitat"
    elif c1:
        v = ("PARTIAL on native seat -- AR is a REAL fragility diagnostic in its own habitat "
             "(the stock-panel FAILED of TR-21 stands as habitat-specific); the gate still "
             "adds nothing over a constant (timing iron law, 4th confirmation).")
    else:
        v = ("KLPR does not replicate even on its native seat under our construction -- "
             "strong FAILED, but scrutinize construction before claiming.")
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.5), gridspec_kw={"height_ratios": [1.3, 1.0]})
    ax = axes[0]
    ax.plot(ar.index, ar, color="#1565c0", lw=1.0)
    for pm in worst.index:
        t0 = pm.to_timestamp()
        ax.axvspan(t0, t0 + pd.offsets.MonthEnd(0), color="#c62828", alpha=0.25)
    ax.set_ylabel("AR (top 20% eigenvalues)")
    ax.grid(alpha=0.3)
    ax.set_title(f"TR-21b: absorption ratio on {r.shape[1]} KF industries, {r.index[0].year}-"
                 f"{r.index[-1].year} -- red = 10 worst market months\n"
                 f"C1 median pre-drawdown PIT percentile = {pre_med:.0f} (p={p_c1:.3f})", fontsize=10.5)
    ax2 = axes[1]
    for ret, c, lab in ((bh, "#757575", "market B&H"), (gate, "#c62828", "AR gate"),
                        (static, "#2e7d32", f"static {expo:.0%}"), (volm, "#f9a825", "1/sigma^2")):
        eq = (1 + ret.dropna()).cumprod()
        ax2.plot(eq.index, eq, color=c, lw=1.1,
                 label=f"{lab} [exSR {exsh(ret):+.2f}, MDD {max_drawdown((1+ret.dropna()).cumprod()):+.0%}]")
    ax2.set_yscale("log")
    ax2.legend(fontsize=8.5, loc="upper left")
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr21b_native.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
