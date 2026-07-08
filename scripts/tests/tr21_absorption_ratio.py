"""TR-21 -- Absorption Ratio (Kritzman-Li-Page-Rigobon 2010) as fragility diagnostic + gate.

F0 DECLARATION (pre-committed)
  mechanism  : Absorption Ratio AR = fraction of total variance captured by the top n/5
               eigenvectors of the trailing covariance matrix (KLPR, "Principal Components as
               a Measure of Systemic Risk", JPM 2011). Standardized shift dAR = (15d mean -
               1yr mean)/1yr std as the risk signal. Source lead: IG reel -> primary-source
               framing verified against the published KLPR design (500d window, top 1/5, dAR>1).
  native habitat : ~50 US industry/sector portfolios, 1998-2010, monthly evaluation, systemic-
               risk monitoring. OUR SEAT: 502 current S&P constituents (curated, survivorship
               -- F11: relative/diagnostic claims only), daily 2015-2026, gate on SPY.
  mis-application risk : MEDIUM (stocks not industries; shorter, calmer sample missing 2008).
  FALSIFIABLE CLAIMS (judged SEPARATELY -- the reel conflates them):
    C1 DIAGNOSTIC "AR leads drawdowns": in the month BEFORE the 10 worst monthly SPY drawdowns,
       the AR percentile is elevated. PASS if median pre-drawdown AR percentile >= 70 with
       permutation p < 0.05 (10,000 random month draws).
    C2 DIVERGENCE "AR sees what average correlation can't": report corr(AR, avg pairwise corr)
       and at least one episode where they diverge (descriptive, no pass/fail).
    C3 GATE "dAR>1 risk-off beats passive": exposure 1 -> 0 (to BIL) when dAR > 1, back when
       dAR < 1; 5bps per switch. PASS only if it (a) beats the mean-exposure STATIC control on
       MDD at comparable excess Sharpe or on exSharpe at comparable MDD (Cederburg / F6 v2),
       AND (b) beats the block-shuffled random-gate placebo distribution (>= p95 exSharpe).
  VERDICT RULE (pre-committed):
     C1 pass & C3 pass  -> PASSED (diagnostic real AND tradable)
     C1 pass & C3 fail  -> PARTIAL (risk-identification value only; joins TR-02's shelf --
                            expected under the iron law: timing-to-cash loses)
     C1 fail            -> FAILED (not even a diagnostic on our seat)
  reopen conditions : industry-portfolio panel (proper habitat) / longer history incl. 2008
               (PIT universe = information cost) / intraday AR.

POST-RUN AUDIT NOTE (adversarial audit; pre-commitment above NOT edited):
  (1) CONFIRMED anti-AR bias: C1 originally used FULL-SAMPLE percentile ranks -- the post-COVID
      structural AR shift mechanically depressed 2018-2020 event ranks (2020-02: 33 full-sample
      vs 78 point-in-time). Fixed below to POINT-IN-TIME expanding percentiles: median rises
      44 -> ~62, still FAIL (rule >=70 & p<0.05).
  (2) Faithfulness: KLPR's claim is a dAR>1 SPIKE before crashes, not a level percentile. Added
      C1b: spike in prior month for 4/10 worst months vs 34% all-month base rate (perm p~0.46)
      -- the faithful test also FAILs. Caveat kept: on the ONE systemic event in sample (COVID)
      the faithful signal DID fire (dAR +1.8 in 2020-01/02); 2018Q4 and all of 2022 were misses
      (AR was FALLING through the 2022 bear).
  (3) C3 was UNFAITHFUL in the flattering direction: single-threshold re-entry (dAR<=1) caught
      V-bottoms; the faithful KLPR 3-state rule (dAR>1 -> 0%, dAR<-1 -> 100%, else 50%) is added
      and scores WORSE -- so C3's FAIL is conservative.
  (4) Dimensionality (465 stocks, q~0.93, noise floor AR_iid~0.52): auditor re-ran with 465 names
      grouped into 51 random equal-weight portfolios (KLPR-like q) -- all conclusions unchanged.
      True GICS industry panel remains a valid reopen condition.

Run: uv run python scripts/tests/tr21_absorption_ratio.py
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")

from trading_analysis.backtest.metrics import cagr, max_drawdown  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

WIN = 500          # KLPR trailing covariance window (days)
STEP = 5           # recompute eigendecomposition every STEP days
TOPFRAC = 0.2      # top n/5 eigenvectors
COST = 0.0005      # 5 bps per gate switch
SEED = 0


def load_panel():
    store = DuckStore("./data")
    with open("configs/universe_sp500.yaml") as fh:
        syms = yaml.safe_load(fh)["symbols"]
    px = store.load_close_pivot(syms, column="adj_close").ffill(limit=5)
    px = px.loc["2015-01-05":]
    # coverage judged on the 2015-2024 core window (most of the SP500 ingest ends 2024;
    # only a subset was extended to 2026 -- filtering on the full span would keep ~84 names)
    core = px.loc[:"2024-12-31"]
    keep = core.columns[core.notna().mean() > 0.95]
    px = px[keep]
    # truncate the panel where cross-sectional coverage collapses (end of the broad ingest)
    cov = px.notna().mean(axis=1)
    last = cov[cov >= 0.90].index.max()
    px = px.loc[:last]
    r = px[keep].pct_change().iloc[1:]
    spy = store.load_close_pivot(["SPY"], column="adj_close").iloc[:, 0].pct_change()
    bil = (store.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0]
           .reindex(spy.index).ffill().pct_change().fillna(0.0))
    return r, spy, bil


def absorption_series(r: pd.DataFrame) -> pd.Series:
    """AR_t = share of total variance in the top n/5 eigenvalues of the trailing WIN-day cov."""
    dates, vals = [], []
    X = r.to_numpy()
    idx = r.index
    ntop = max(1, int(np.ceil(r.shape[1] * TOPFRAC)))
    for t in range(WIN, len(idx), STEP):
        w = X[t - WIN:t]
        if np.isnan(w).mean() > 0.02:
            continue
        w = np.nan_to_num(w, nan=0.0)
        c = np.cov(w, rowvar=False)
        ev = np.linalg.eigvalsh(c)              # ascending
        vals.append(ev[-ntop:].sum() / ev.sum())
        dates.append(idx[t])
    ar = pd.Series(vals, index=pd.DatetimeIndex(dates)).reindex(r.index).ffill()
    return ar.dropna()


def avg_corr_series(r: pd.DataFrame) -> pd.Series:
    dates, vals = [], []
    X = r.to_numpy()
    idx = r.index
    for t in range(WIN, len(idx), STEP * 4):    # coarser: descriptive only
        w = np.nan_to_num(X[t - WIN:t], nan=0.0)
        c = np.corrcoef(w, rowvar=False)
        n = c.shape[0]
        vals.append((c.sum() - n) / (n * (n - 1)))
        dates.append(idx[t])
    return pd.Series(vals, index=pd.DatetimeIndex(dates))


def main():
    rng = np.random.default_rng(SEED)
    r, spy, bil = load_panel()
    print("=" * 100)
    print(f"TR-21  ABSORPTION RATIO (KLPR 2010)  panel {r.shape[1]} names x {len(r)} days, "
          f"window {WIN}d, top {int(TOPFRAC*100)}% eigenvectors")
    print("=" * 100)

    ar = absorption_series(r)
    d15 = ar.rolling(15).mean()
    d253 = ar.rolling(253).mean()
    s253 = ar.rolling(253).std()
    dar = ((d15 - d253) / s253).dropna()

    # ---- C1 diagnostic: POINT-IN-TIME AR percentile before the worst monthly drawdowns ----
    # (audit fix: full-sample ranks let the post-COVID AR shift depress earlier events' ranks)
    spy_al = spy.reindex(ar.index).fillna(0.0)
    spym = (1 + spy_al).groupby(spy_al.index.to_period("M")).prod() - 1
    worst = spym.nsmallest(10)
    arv = ar.to_numpy()
    pct = pd.Series([(arv[: i + 1] <= arv[i]).mean() for i in range(len(arv))], index=ar.index)
    pre = []
    for pm in worst.index:
        anchor = (pm - 1).to_timestamp(how="end")        # end of the PRIOR month
        window = pct.loc[:anchor].tail(5)
        if len(window):
            pre.append(float(window.mean()) * 100)
    pre_med = float(np.median(pre))
    # permutation null: random months' prior-month AR percentile
    ends = pct.groupby(pct.index.to_period("M")).apply(lambda s: float(s.tail(5).mean()) * 100)
    ends = ends.iloc[12:]                                 # skip warmup
    null = np.array([np.median(rng.choice(ends.to_numpy(), size=len(pre), replace=False))
                     for _ in range(10_000)])
    p_c1 = float((null >= pre_med).mean())
    c1 = pre_med >= 70 and p_c1 < 0.05
    print(f"C1 DIAGNOSTIC (PIT pctile): median AR percentile in month before 10 worst SPY months "
          f"= {pre_med:.0f} (perm p={p_c1:.4f}) -> {'PASS' if c1 else 'FAIL'} (rule: >=70 & p<0.05)")
    print(f"   worst months: {', '.join(str(m) for m in worst.index)}")
    # C1b faithful-KLPR spike test: dAR>1 anywhere in the PRIOR month, vs the all-month base rate
    spike_m = (dar > 1.0).groupby(dar.index.to_period("M")).max()
    hits = [bool(spike_m.get(pm - 1, False)) for pm in worst.index if (pm - 1) in spike_m.index]
    base = spike_m.iloc[12:].astype(float)
    null_b = np.array([rng.choice(base.to_numpy(), size=len(hits), replace=False).mean()
                       for _ in range(10_000)])
    p_c1b = float((null_b >= np.mean(hits)).mean())
    print(f"C1b FAITHFUL SPIKE (dAR>1 in prior month): {sum(hits)}/{len(hits)} worst months vs "
          f"base rate {base.mean():.0%} (perm p={p_c1b:.2f}) -> "
          f"{'PASS' if p_c1b < 0.05 else 'FAIL'}")

    # ---- C2 divergence vs average correlation (descriptive) ----
    ac = avg_corr_series(r)
    cmn = ar.reindex(ac.index).dropna()
    corr_ar_ac = float(np.corrcoef(cmn.to_numpy(), ac.reindex(cmn.index).to_numpy())[0, 1])
    print(f"C2 DIVERGENCE: corr(AR, avg pairwise corr) = {corr_ar_ac:+.2f} (descriptive)")

    # ---- C3 gate vs Nagel controls ----
    sig = (dar <= 1.0).astype(float)                      # 1 = invested, 0 = risk-off
    # evaluate ONLY where the AR panel is alive (no stale-signal carry into 2025-26)
    spy_eval = spy.loc[dar.index[0]:dar.index[-1]]
    sig = sig.reindex(spy_eval.index).ffill().dropna()
    common = sig.index.intersection(spy_eval.index).intersection(bil.index)
    sig, q, b = sig.loc[common], spy.loc[common].fillna(0.0), bil.loc[common]
    pos = sig.shift(1).fillna(1.0)
    gate = pos * q + (1 - pos) * b - pos.diff().abs().fillna(0.0) * COST
    expo = float(pos.mean())
    static = expo * q + (1 - expo) * b
    volm_raw = (q - b) / q.rolling(21).std().shift(1).pow(2).clip(lower=1e-6)
    volm = b + volm_raw * ((q - b).std() / volm_raw.std())          # 1/sigma^2 scaled to SPY vol
    bh = q

    def ex_sharpe(x):
        e = (x - b).dropna()
        return float(e.mean() / e.std() * np.sqrt(252))

    # random-gate placebo: block-shuffle the exposure series (preserve on/off run lengths)
    runs = [(k, len(list(g))) for k, g in __import__("itertools").groupby(pos.to_numpy())]
    def shuffle_gate():
        order = rng.permutation(len(runs))
        arr = np.concatenate([np.full(runs[i][1], runs[i][0]) for i in order])
        p = pd.Series(arr[: len(q)], index=q.index)
        return ex_sharpe(p * q + (1 - p) * b - p.diff().abs().fillna(0.0) * COST)
    placebo = np.array([shuffle_gate() for _ in range(200)])

    # faithful KLPR 3-state rule (audit fix: the single-threshold version flattered the gate)
    dar_al = dar.reindex(common).ffill()
    expo3 = pd.Series(np.where(dar_al > 1, 0.0, np.where(dar_al < -1, 1.0, 0.5)), index=common)
    p3 = expo3.shift(1).fillna(0.5)
    gate3 = p3 * q + (1 - p3) * b - p3.diff().abs().fillna(0.0) * COST

    print(f"\nC3 GATE (dAR>1 -> BIL; avg exposure {expo:.0%}; "
          f"{common.min().date()}..{common.max().date()}):")
    print(f"{'book':34s} {'CAGR':>8s} {'exSharpe':>9s} {'MDD':>8s}")
    stats = {}
    for name, ret in (("SPY buy&hold", bh), ("AR gate", gate),
                      ("AR gate faithful 3-state (KLPR)", gate3),
                      (f"STATIC {expo:.0%} (Cederburg)", static), ("1/sigma^2 vol-managed", volm)):
        eq = (1 + ret.dropna()).cumprod()
        stats[name] = (ex_sharpe(ret), max_drawdown(eq))
        print(f"{name:34s} {cagr(eq):>+8.2%} {stats[name][0]:>+9.2f} {stats[name][1]:>+8.1%}")
    g_sh, g_dd = stats["AR gate"]
    s_sh, s_dd = stats[f"STATIC {expo:.0%} (Cederburg)"]
    beats_static = (g_dd > s_dd + 0.01 and g_sh >= s_sh - 0.05) or (g_sh > s_sh + 0.10 and g_dd >= s_dd - 0.01)
    beats_placebo = g_sh >= np.percentile(placebo, 95)
    c3 = beats_static and beats_placebo
    print(f"placebo: random-gate exSharpe p95 = {np.percentile(placebo, 95):+.2f} "
          f"(gate {'>=' if beats_placebo else '<'} p95)")
    print(f"C3 -> {'PASS' if c3 else 'FAIL'} (beats static: {beats_static}; beats placebo p95: {beats_placebo})")

    print("-" * 100)
    if c1 and c3:
        verdict = "PASSED -- diagnostic real AND tradable"
    elif c1:
        verdict = ("PARTIAL -- AR is a real fragility DIAGNOSTIC on this seat, but the gate adds "
                   "nothing over a constant/simple controls (iron law holds). Shelve with TR-02: "
                   "risk-identification value; candidate input for the E1 health dashboard.")
    else:
        verdict = "FAILED -- not even a diagnostic on this seat"
    print(f"VERDICT: {verdict}")
    print(f"panel end ({ar.index[-1].date()}): AR={float(ar.iloc[-1]):.2f} "
          f"(pctile {float(pct.iloc[-1])*100:.0f}), dAR={float(dar.iloc[-1]):+.2f}")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.5), sharex=False,
                             gridspec_kw={"height_ratios": [1.4, 1.0]})
    ax = axes[0]
    ax.plot(ar.index, ar, color="#1565c0", lw=1.2, label=f"absorption ratio (top {int(TOPFRAC*100)}% eigenvalues)")
    for pm in worst.index:
        t0 = pm.to_timestamp()
        ax.axvspan(t0, t0 + pd.offsets.MonthEnd(0), color="#c62828", alpha=0.18)
    ax.set_ylabel("AR")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_title(f"TR-21: absorption ratio on {r.shape[1]} S&P names -- red bands = 10 worst SPY months\n"
                 f"C1: median pre-drawdown AR percentile {pre_med:.0f} (perm p={p_c1:.3f})", fontsize=10.5)
    ax2 = axes[1]
    for ret, c, label in ((bh, "#757575", "SPY B&H"), (gate, "#c62828", "AR gate"),
                          (static, "#2e7d32", f"static {expo:.0%}"), (volm, "#f9a825", "1/sigma^2")):
        eq = (1 + ret.dropna()).cumprod()
        ax2.plot(eq.index, eq, color=c, lw=1.3,
                 label=f"{label} [exSR {ex_sharpe(ret):+.2f}, MDD {max_drawdown((1+ret.dropna()).cumprod()):+.0%}]")
    ax2.set_yscale("log")
    ax2.legend(loc="upper left", fontsize=8.5)
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr21_absorption.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
