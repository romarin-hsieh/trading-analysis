"""TR-25 -- Flagship robustness grid: is the deliverable a PLATEAU or a POINT?

F0 DECLARATION (pre-committed)
  claim        : the flagship 5-sleeve risk-parity book's headline metrics (excess-over-RF
               Sharpe; monthly Carhart alpha-t; drawdown-vs-VOO) do NOT depend on (C1) the
               exact sleeve weights, (C2) the rebalance frequency, or (C3) the single
               realized 2015-2026 path. Depth complement to the breadth-first TR series:
               weights x frequency x path dispersion in one report.
  seat         : same data as TR-15/18/22 (5 sleeve daily returns, 2015-2026); baseline =
               risk-parity lookback 126 / step 21 (the registry config).
  PRE-COMMITTED CHECKS
    C1 weights   : 200 random multiplicative sleeve tilts, per-sleeve factor ~ U[0.80, 1.25]
                   applied to the whole RP weight path (rows renormalized), plus 10
                   systematic single-sleeve +/-20% corners. PASS iff the 5th percentile of
                   variant excess Sharpe >= baseline - 0.15 AND >= 90% of variants keep
                   monthly OLS alpha-t >= 2.0.
    C2 frequency : rebalance step in {5, 21, 63} trading days (weekly/monthly/quarterly),
                   lookback fixed at 126. PASS iff (max-min) excess Sharpe spread <= 0.15
                   AND all three alpha-t >= 2.0.
    C3 path      : 1,000 stationary-bootstrap draws (mean block 21d, Politis-Romano),
                   resampling (combo, VOO) rows JOINTLY. PASS iff P(MDD_combo <= MDD_VOO)
                   >= 0.90 AND the 5th percentile of bootstrapped excess Sharpe > 0.
  VERDICT RULE (pre-committed):
    all three PASS      -> ROBUST-PLATEAU (registry note: headline is weight/frequency/
                           path-insensitive within the tested ranges)
    any single FAIL     -> named downgrade (WEIGHT- / FREQUENCY- / PATH-SENSITIVE);
                           the failed dimension becomes a standing caveat on docs/18
  anti-HARKing : variants are sensitivity probes, NOT candidates. The registry baseline
               stays risk-parity 126/21 REGARDLESS of whether some variant scores higher.
               No selection happens, so this grid adds ZERO trials to F5 accounting.
  scope caveat : C1/C2 dispersion is conditional on the one realized path (C3 addresses
               the path itself); tilt range +/-20-25% probes the plateau, not far-corner
               allocations -- claims are scoped to that neighborhood.

Run: uv run python scripts/tests/tr25_robustness_grid.py   (~2-4 min)
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import validate_recommendation as vr  # noqa: E402
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown  # noqa: E402
from trading_analysis.backtest.spa import stationary_bootstrap_indices  # noqa: E402
from trading_analysis.factors.attribution import (  # noqa: E402
    compound_to_monthly,
    load_ff_factors,
    load_ff_factors_monthly,
)
from trading_analysis.portfolio import rebalance  # noqa: E402

N_TILTS = 200
TILT_LO, TILT_HI = 0.80, 1.25
STEPS = (5, 21, 63)
N_BOOT = 1000
AVG_BLOCK = 21
SEED = 0


def ex_sharpe(r: pd.Series, rf: pd.Series) -> float:
    ex = (r - rf.reindex(r.index).fillna(0.0)).dropna()
    return float(ex.mean() / ex.std() * np.sqrt(252))


class MonthlyAlpha:
    """factor_alpha_monthly's OLS core with the FF panel loaded once (210+ calls)."""

    def __init__(self):
        ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)
        self.ff = ff
        self.cols = [c for c in ["Mkt-RF", "SMB", "HML", "UMD"] if c in ff.columns]

    def t_ols(self, daily: pd.Series) -> float:
        rm = compound_to_monthly(daily)
        cmn = rm.index.intersection(self.ff.index)
        y = (rm.reindex(cmn) - self.ff.reindex(cmn)["RF"]).dropna()
        x = self.ff.reindex(y.index)[self.cols]
        res = sm.OLS(y.to_numpy(), sm.add_constant(x.to_numpy())).fit()
        return float(res.tvalues[0])


def main():
    rng = np.random.default_rng(SEED)
    rp, _ew, sleeves = vr.build_combo()
    W = rebalance(sleeves, lookback=126, step=21, method="risk_parity")
    Wd = W.reindex(sleeves.index).ffill().shift(1).fillna(0.0)
    ff_d = load_ff_factors(start="2015-01-01")
    rf_d = ff_d["RF"].reindex(sleeves.index).fillna(0.0)
    voo = ss._px(["VOO"]).iloc[:, 0].pct_change().reindex(rp.index).fillna(0.0)
    ma = MonthlyAlpha()

    base_sr = ex_sharpe(rp, rf_d)
    base_t = ma.t_ols(rp)
    print("=" * 100)
    print(f"TR-25  FLAGSHIP ROBUSTNESS GRID -- {rp.index[0].date()}..{rp.index[-1].date()} "
          f"(n={len(rp)} days)")
    print(f"baseline (RP 126/21): exSharpe {base_sr:+.2f} | monthly Carhart alpha-t {base_t:+.2f}")
    print("=" * 100)

    # ---- C1: weight-perturbation grid ----
    tilts = rng.uniform(TILT_LO, TILT_HI, size=(N_TILTS, sleeves.shape[1]))
    corners = []
    for j in range(sleeves.shape[1]):
        for f in (TILT_LO, TILT_HI):
            v = np.ones(sleeves.shape[1])
            v[j] = f
            corners.append(v)
    tilts = np.vstack([tilts, np.array(corners)])
    srs, ts = [], []
    for k, tv in enumerate(tilts):
        Wt = Wd * tv
        Wt = Wt.div(Wt.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        r = (Wt * sleeves).sum(axis=1).iloc[126:]
        srs.append(ex_sharpe(r, rf_d))
        ts.append(ma.t_ols(r))
        if (k + 1) % 50 == 0:
            print(f"  [C1 {k + 1}/{len(tilts)} variants]")
    srs, ts = np.array(srs), np.array(ts)
    c1_sr5 = float(np.percentile(srs, 5))
    c1_frac_t = float((ts >= 2.0).mean())
    c1 = (c1_sr5 >= base_sr - 0.15) and (c1_frac_t >= 0.90)
    print(f"C1 weights: exSharpe 5th pct {c1_sr5:+.2f} (rule >= {base_sr - 0.15:+.2f}); "
          f"alpha-t>=2.0 in {c1_frac_t:.0%} (rule >=90%); range t=[{ts.min():.2f},{ts.max():.2f}]"
          f" -> {'PASS' if c1 else 'FAIL'}")

    # ---- C2: rebalance frequency ----
    freq_rows = {}
    for step in STEPS:
        Ws = rebalance(sleeves, lookback=126, step=step, method="risk_parity")
        Wsd = Ws.reindex(sleeves.index).ffill().shift(1).fillna(0.0)
        r = (Wsd * sleeves).sum(axis=1).iloc[126:]
        freq_rows[step] = (ex_sharpe(r, rf_d), ma.t_ols(r))
    spread = max(v[0] for v in freq_rows.values()) - min(v[0] for v in freq_rows.values())
    c2 = (spread <= 0.15) and all(v[1] >= 2.0 for v in freq_rows.values())
    for step, (s, t) in freq_rows.items():
        print(f"C2 step={step:>2d}d: exSharpe {s:+.2f} | alpha-t {t:+.2f}")
    print(f"C2 frequency: spread {spread:.2f} (rule <=0.15) -> {'PASS' if c2 else 'FAIL'}")

    # ---- C3: joint stationary bootstrap of (combo, VOO) ----
    ex_c = (rp - rf_d.reindex(rp.index).fillna(0.0)).to_numpy()
    raw_c = rp.to_numpy()
    raw_v = voo.to_numpy()
    n = len(raw_c)
    idx = stationary_bootstrap_indices(n, AVG_BLOCK, N_BOOT, rng)
    bs_sr = np.empty(N_BOOT)
    bs_mdd_c = np.empty(N_BOOT)
    bs_mdd_v = np.empty(N_BOOT)
    eq_paths = np.empty((N_BOOT, n))
    for b in range(N_BOOT):
        e = ex_c[idx[b]]
        bs_sr[b] = e.mean() / e.std() * np.sqrt(252)
        eq_c = np.cumprod(1 + raw_c[idx[b]])
        eq_v = np.cumprod(1 + raw_v[idx[b]])
        eq_paths[b] = eq_c
        bs_mdd_c[b] = (eq_c / np.maximum.accumulate(eq_c) - 1).min()
        bs_mdd_v[b] = (eq_v / np.maximum.accumulate(eq_v) - 1).min()
    p_dd = float((bs_mdd_c >= bs_mdd_v).mean())          # MDD is negative: >= means shallower
    sr5 = float(np.percentile(bs_sr, 5))
    c3 = (p_dd >= 0.90) and (sr5 > 0)
    print(f"C3 path: P(MDD_combo shallower than VOO) {p_dd:.1%} (rule >=90%); "
          f"exSharpe 5-95% band [{sr5:+.2f}, {np.percentile(bs_sr, 95):+.2f}] "
          f"-> {'PASS' if c3 else 'FAIL'}")

    fails = [name for ok, name in ((c1, "WEIGHT-SENSITIVE"), (c2, "FREQUENCY-SENSITIVE"),
                                   (c3, "PATH-SENSITIVE")) if not ok]
    verdict = "ROBUST-PLATEAU" if not fails else " + ".join(fails)
    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # ---- chart: 3 panels ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    ax.hist(ts, bins=30, color="#1565c0", alpha=0.8)
    ax.axvline(base_t, color="#2e7d32", lw=2, label=f"baseline t={base_t:.2f}")
    ax.axvline(2.0, color="#c62828", ls="--", lw=1.5, label="t=2.0")
    ax.set_title(f"C1: alpha-t across {len(tilts)} weight tilts (±20-25%)", fontsize=10)
    ax.set_xlabel("monthly Carhart alpha-t (OLS)")
    ax.legend(fontsize=8)
    ax = axes[1]
    xs = list(freq_rows)
    ax.plot(xs, [freq_rows[s][0] for s in xs], "o-", color="#1565c0", label="excess Sharpe")
    ax.axhline(base_sr, color="#757575", ls=":", lw=1)
    for s in xs:
        ax.annotate(f"t={freq_rows[s][1]:.2f}", (s, freq_rows[s][0]),
                    textcoords="offset points", xytext=(0, 8), fontsize=8, ha="center")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{s}d" for s in xs])
    ax.set_title("C2: rebalance frequency (weekly/monthly/quarterly)", fontsize=10)
    ax.set_xlabel("rebalance step")
    ax.legend(fontsize=8)
    ax = axes[2]
    t_axis = np.arange(n)
    for lo, hi, a in ((5, 95, 0.18), (25, 75, 0.35)):
        ax.fill_between(t_axis, np.percentile(eq_paths, lo, axis=0),
                        np.percentile(eq_paths, hi, axis=0), color="#1565c0", alpha=a,
                        label=f"{lo}-{hi}%")
    ax.plot(t_axis, np.median(eq_paths, axis=0), color="#0d47a1", lw=1.4, label="median")
    ax.plot(t_axis, np.cumprod(1 + raw_c), color="#2e7d32", lw=1.2, label="realized")
    ax.set_yscale("log")
    ax.set_title(f"C3: bootstrap equity fan ({N_BOOT} paths, block~{AVG_BLOCK}d)", fontsize=10)
    ax.set_xlabel("trading days")
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-25: flagship robustness grid -- weights x frequency x path", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr25_robustness.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
