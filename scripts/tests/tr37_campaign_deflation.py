"""TR-37 -- campaign-level deflated alpha for the flagship (docs/25 attacks #1+#7, plan A2).

The flagship's monthly Carhart t=2.64 has never been charged for the SELECTION process
that produced it. TR-22's PBO covered 12 allocator configs; TR-25 covered weights; but
the sleeve-candidate family (streams evaluated across docs/07-15 and rejected) and the
campaign-wide search were never rolled into one deflated number. This TR does that with
the Bailey-Lopez de Prado Deflated Sharpe Ratio applied to the flagship's ALPHA stream
(Carhart residual + alpha), plus a Harvey-Liu-style skeptical-prior posterior.

TRIAL INVENTORY (pre-committed; sources: docs/trial-registry.md + docs/07-15):
  combo-level evaluations actually run (the honest point estimate N*):
    TR-22 allocator/config family ................ 12
    quality-tilt combo variants (docs/10 4c) .....  2   (6-sleeve RP, 5-sleeve+15% tilt)
    TAA-vs-combo evaluation (docs/13 7) ..........  1
    defensive-overlay L-scale is a POST-selection deliverable (not a combo trial) .. 0
    six-slot combo-2x (docs/14) ..................  1
    ensemble mixes E1-E5 touching combo (docs/15).  1   (E-vs-combo comparison)
    ---------------------------------------------------
    N* = 17
  curve endpoints for the reader: N in {2, 4, 8, 17, 50, 100, 226}
  (226 = all named campaign variants -- a deliberate paranoid upper bound; most of
  those 226 never competed to BE the flagship, so the curve, not one cell, is the
  honest exhibit. Family n_eff 3-4 from the registry is the lower end.)

F0 DECLARATION (pre-committed)
  claim  : the flagship's alpha survives honest selection-deflation at the
         inventoried combo-level trial count.
  seat   : flagship monthly returns (build_combo, TR-18 monthly clock), Carhart
         four-factor residual+alpha stream, full window.
  CAL    : monthly Carhart alpha t reproduces the docs/08/TR-18 anchor (2.0..3.2).
  C1     : DSR curve over N; VERDICT judged AT N*=17:
             DSR >= 0.95            -> SURVIVES-DEFLATION
             0.50 <= DSR < 0.95     -> FRAGILE-SURVIVES (README states the number)
             DSR < 0.50             -> DEFLATED-AWAY (downgrade the flagship row)
  C2     : skeptical-prior posterior: P(true alpha > 0 | t, p0) using the Edwards
         minimum-Bayes-factor bound exp(-t^2/2) (most favorable to the alpha) and a
         realistic BF with delta=2; curve over p0 in [0.50, 0.99]. Reported, no gate
         (C1 is the gate); README quotes p0=0.90 cell.
  C3     : Sidak-adjusted alpha p-value at N* and 226 (frequentist cross-check).
  anti-HARKing : inventory fixed above BEFORE computing; single spec; trials +1
         family (meta-inference).

Run: uv run python scripts/tests/tr37_campaign_deflation.py   (~2 min)
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger
from scipy import stats

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

import matplotlib.pyplot as plt  # noqa: E402

import validate_recommendation as vr  # noqa: E402

from trading_analysis.factors.attribution import (  # noqa: E402
    compound_to_monthly,
    load_ff_factors_monthly,
)

N_STAR = 17
N_GRID = (2, 4, 8, 17, 50, 100, 226)
EULER = 0.5772156649


def dsr(alpha_stream: pd.Series, n_trials: int) -> float:
    """Bailey-Lopez de Prado Deflated Sharpe Ratio of a return stream vs N trials."""
    x = alpha_stream.dropna().to_numpy()
    T = len(x)
    sr = x.mean() / x.std(ddof=1)                       # per-period SR
    g3 = float(stats.skew(x))
    g4 = float(stats.kurtosis(x, fisher=False))
    se = np.sqrt((1 - g3 * sr + (g4 - 1) / 4 * sr**2) / (T - 1))
    if n_trials <= 1:
        sr0 = 0.0
    else:
        z1 = stats.norm.ppf(1 - 1.0 / n_trials)
        z2 = stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
        sr0 = se * ((1 - EULER) * z1 + EULER * z2)
    return float(stats.norm.cdf((sr - sr0) / se))


def main():
    print("=" * 100)
    print("TR-37  CAMPAIGN-LEVEL DEFLATED ALPHA (flagship) -- selection honesty, plan A2")
    print("=" * 100)

    rp, _ew, _s = vr.build_combo()
    m = compound_to_monthly(rp)
    m.index = pd.PeriodIndex(m.index, freq="M")
    ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)
    df = pd.concat([m.rename("r"), ff], axis=1).dropna()
    y = df["r"] - df["RF"]
    X = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "UMD"]])
    ols = sm.OLS(y, X).fit()
    t_alpha = float(ols.tvalues["const"])
    alpha_m = float(ols.params["const"])
    resid_stream = ols.resid + alpha_m                  # alpha + epsilon
    T = len(y)

    cal = 2.0 <= t_alpha <= 3.2
    print(f"CAL: monthly Carhart alpha {alpha_m*12*100:+.2f}%/yr, t={t_alpha:+.2f} "
          f"(anchor band 2.0-3.2), T={T} months -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: INVALID-TEST")
        return

    ir_ann = float(resid_stream.mean() / resid_stream.std(ddof=1) * np.sqrt(12))
    print(f"alpha stream: annualized IR {ir_ann:+.2f}, skew {stats.skew(resid_stream):+.2f}, "
          f"kurt {stats.kurtosis(resid_stream, fisher=False):.1f}")

    # ---- C1 DSR curve ----
    print("-" * 100)
    print("C1 Deflated Sharpe Ratio of the alpha stream vs number of trials:")
    curve = {}
    for n in N_GRID:
        curve[n] = dsr(resid_stream, n)
        tag = "  <- N* (inventoried combo-level trials)" if n == N_STAR else ""
        print(f"  N={n:>3d}: DSR = {curve[n]:.3f}{tag}")
    d_star = curve[N_STAR]
    if d_star >= 0.95:
        c1v = "SURVIVES-DEFLATION"
    elif d_star >= 0.50:
        c1v = "FRAGILE-SURVIVES"
    else:
        c1v = "DEFLATED-AWAY"

    # ---- C2 skeptical-prior posterior ----
    print("C2 skeptical-prior posterior P(true alpha>0 | t, p0):")
    mbf = np.exp(-t_alpha**2 / 2)                       # Edwards bound, H0/H1 form (favors the alpha)
    delta = 2.0
    # realistic Bayes factor in the SAME H0/H1 form: P(t|H0)/P(t|H1), H1: t~N(delta,1).
    # (first run had the ratio inverted -- posterior collapsed to 0 and contradicted the
    # MBF bound, which is the alpha-favorable ceiling; direction fixed, consistency
    # restored: realistic posterior must be <= MBF posterior.)
    bf_real = stats.norm.pdf(t_alpha) / stats.norm.pdf(t_alpha - delta)
    rows = []
    for p0 in (0.50, 0.75, 0.90, 0.95, 0.99):
        post_mbf = 1 - 1 / (1 + (1 - p0) / p0 / mbf)
        post_real = 1 - 1 / (1 + (1 - p0) / p0 / bf_real)
        rows.append((p0, post_mbf, post_real))
        print(f"  p0(null)={p0:.2f}: posterior P(alpha>0) = {post_mbf:.2f} (MBF bound) / "
              f"{post_real:.2f} (delta=2 BF)")

    # ---- C3 Sidak ----
    p_raw = float(2 * (1 - stats.t.cdf(abs(t_alpha), df=T - 5)))
    for n in (N_STAR, 226):
        p_adj = 1 - (1 - p_raw) ** n
        print(f"C3 Sidak-adjusted alpha p-value at N={n}: raw {p_raw:.4f} -> adj {p_adj:.3f}")

    print("-" * 100)
    print(f"VERDICT: {c1v} -- DSR at the inventoried N*={N_STAR} is {d_star:.2f}; "
          f"paranoid N=226 gives {curve[226]:.2f}. The flagship's 'borderline' label now "
          f"has a selection-honest number.")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
    ax = axes[0]
    ns = list(N_GRID)
    ax.plot(ns, [curve[n] for n in ns], "o-", color="#1565c0")
    ax.axvline(N_STAR, color="#c62828", ls="--", lw=1.2, label=f"N*={N_STAR} (inventoried)")
    ax.axhline(0.95, color="#2e7d32", ls=":", lw=1, label="0.95")
    ax.axhline(0.50, color="#757575", ls=":", lw=1, label="0.50")
    ax.set_xscale("log")
    ax.set_xlabel("assumed number of trials N (log)")
    ax.set_ylabel("Deflated Sharpe Ratio")
    ax.set_title(f"C1: DSR of the flagship alpha stream\n(t={t_alpha:+.2f}, IR {ir_ann:+.2f}, "
                 f"T={T}m)", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    p0s = np.linspace(0.5, 0.99, 50)
    ax.plot(p0s, [1 - 1 / (1 + (1 - p) / p / mbf) for p in p0s], color="#1565c0",
            label="MBF bound (favors alpha)")
    ax.plot(p0s, [1 - 1 / (1 + (1 - p) / p / bf_real) for p in p0s], color="#c62828",
            label="delta=2 Bayes factor")
    ax.axvline(0.90, color="#757575", ls=":", lw=1)
    ax.set_xlabel("prior P(strategy is null)")
    ax.set_ylabel("posterior P(true alpha > 0)")
    ax.set_title("C2: skeptical-prior posterior", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-37: what selection honesty does to the flagship's borderline alpha",
                 fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr37_campaign_deflation.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
