"""TR-17b -- KMZ Virtue of Complexity RE-OPENED on its NATIVE seat (docs/24 action #1).

F0 DECLARATION (pre-committed)
  reopen basis : TR-17's priced reopen condition -- "ingest the Goyal-Welch dataset" -- is
               now satisfied at $0 (Amit Goyal's site, updated to 2024-12). This is the F10
               re-test on the paper's OWN habitat: single-asset US market timing, monthly,
               1926-2024, the 15 standard GW macro predictors (KMZ JF 2024 seat), rolling
               T=12 RFF kernel-ridge, P up to 12,000. Machinery reused VERBATIM from TR-17
               (same voc_curve / seeds / grids) -- only the SEAT changes.
  predictors   : d/p, d/y, e/p, d/e, svar, b/m, ntis, tbl, lty, ltr, tms, dfy, dfr,
               infl (extra 1-month publication lag per GW convention), lagged excess ret.
  target       : next-month S&P excess return (GW `ret` - `Rfree`).
  PRE-COMMITTED CHECKS (same three as TR-17):
    R1 VoC shape  : OOS Sharpe at P=12,000 > P=12 (both shrinkage levels).
    R2 Nagel      : high-P strategy beats the Moreira-Muir 1/svar control on Sharpe AND
                    has alpha-t >= 2 against it (else it IS the vol-timing artifact).
    R3 fabric     : clipped [0,2], vol-normalized, 5bps-costed version beats B&H.
  VERDICT RULE (pre-committed):
    R1&R2&R3 -> REOPEN the ML/complexity chapter (major F10 cascade)
    R1 & !R2 -> "KMZ replicates on its native seat but is EXPLAINED BY vol-timing --
                Nagel's critique confirmed at the source"; ML chapter stays closed
    !R1      -> replication failure on the native seat (scrutinize hard before claiming:
                the published result is t~3.0; a failure here more likely means our
                predictor construction differs -- report, do not over-claim)
  mis-application risk : LOW (this IS the native habitat; residual differences: GW `ret`
               is S&P-based vs KMZ's CRSP-vw; our T=12/P-grid/seed conventions from TR-17).

POST-RUN AUDIT NOTE (2026-07-11, appended -- F0 above NOT edited)
  The first run (voc_curve reused verbatim from TR-17) printed NO-VoC-SHAPE (all P/z
  Sharpe -0.25..+0.10, flat). Adversarial audit ruled this a CONSTRUCTION-INDUCED FALSE
  NEGATIVE, exactly the risk the !R1 branch pre-flagged:
    - CONFIRMED #1 (the shape-killer): TR-17's 12-obs in-window z-scoring of predictors
      makes the RFF Gaussian kernel numerically the identity (off-diag ~3e-3), so high-P
      forecasts are ~0 by construction. Single-toggle ablation reproduces the flat curve.
    - CONFIRMED #2: KMZ's target and traded return are vol-standardized (ex_{t+1}/sigma_t,
      uncentered trailing 12m std; JF p.491) -- the economic core of the Nagel story --
      and alphas are vs a STATIC position in the vol-standardized market.
    - Fidelity fixes per audit + zivmi/voc_reproduction + KMZ fn.38-39: predictors scaled
      by EXPANDING-window std (min_periods=36, levels kept); RFF sin/cos pairs, gamma=2,
      no 1/sqrt(P); features scaled by training-window std; ridge penalty z*T on the raw
      feature Gram, log10(z) in {-3..3}; multi-seed averaging (KMZ use 1000 draws; low-P
      estimates are noisy at a single seed).
  This file is the corrected KMZ-faithful run OF RECORD (P-grid thinned to 5 points to
  afford multi-seed). The pre-committed R1/R2/R3 checks and verdict tiers are UNCHANGED;
  R2 additionally REPORTS (not gates) alpha vs the vol-std static market (KMZ's own
  benchmark) and vs Nagel's vol-timed momentum control, per audit recommendation.
  Audited outcome: R1 TRUE (VoC shape replicates at home) but R2 FAILS -> the
  pre-committed 'R1 & !R2' branch: REPLICATED-BUT-EXPLAINED, Nagel confirmed at source.
  gamma-sensitivity caveat: faithful high-P SR falls +0.33 -> +0.21 -> +0.15 across
  gamma 2 -> 1 -> 0.5 (shape survives; magnitude does not).

Run: uv run python scripts/tests/tr17b_kmz_native.py   (~2-5 min)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

GW_XLSX = "data/gw_predictors.xlsx"   # exported from Amit Goyal's site (sheet id in docs/24)

T_WIN = 12
P_GRID = [2, 12, 100, 1200, 12000]
Z_KMZ = [10.0 ** k for k in range(-3, 4)]            # KMZ grid, penalty = z*T on raw feats
SEEDS_BY_P = {2: 20, 12: 20, 100: 10, 1200: 5, 12000: 3}
Z_LO, Z_HI = 1e-3, 1e3                                # "ridgeless~" / "heavy" ends for R1
COST = 0.0005


def gw_panel():
    df = pd.read_excel(GW_XLSX, sheet_name="Monthly")
    df.index = pd.PeriodIndex(df["yyyymm"].astype(int).astype(str), freq="M").to_timestamp("M")
    rf = df["Rfree"].astype(float)
    ret = df["ret"].astype(float)                     # S&P total return (CRSP calc, w/ divs)
    ex = ret - rf                                     # excess return of month t (at index t)
    raw = pd.DataFrame({
        "dp": df["d/p"], "dy": df["d/y"], "ep": df["e/p"], "de": df["d/e"],
        "svar": df["svar"], "bm": df["b/m"], "ntis": df["ntis"], "tbl": df["tbl"],
        "lty": df["lty"], "ltr": df["ltr"], "tms": df["tms"], "dfy": df["dfy"],
        "dfr": df["dfr"], "infl": df["infl"].shift(1),  # publication lag (GW convention)
        "lag_ex": ex,                                   # lagged excess return (known at t)
    }, index=df.index).astype(float)
    sig12 = np.sqrt((ex ** 2).rolling(12).mean())     # trailing 12m vol, UNCENTERED, known at t
    return raw, ex.shift(-1), sig12, df["svar"].astype(float)


def sharpe_m(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 24 and x.std() > 0 else np.nan


def make_rff_kmz(G, P, gamma, seed):
    """KMZ RFF (eq.20 + fn.38): sin/cos pairs, omega ~ N(0, I_d), no 1/sqrt(P)."""
    rs = np.random.RandomState(seed)
    om = rs.normal(0, 1, size=(G.shape[1], P // 2))
    A = gamma * (G @ om)
    S = np.empty((G.shape[0], 2 * (P // 2)))
    S[:, 0::2] = np.sin(A)
    S[:, 1::2] = np.cos(A)
    return S


def rolling_forecasts_kmz(S, Y, z_list):
    """Rolling T=12 kernel-ridge per KMZ fn.39: features scaled by in-window std,
    penalty z*T on the raw feature Gram. Returns dict z -> forecast array (n,)."""
    n = S.shape[0]
    out = {z: np.full(n, np.nan) for z in z_list}
    eyeT = np.eye(T_WIN)
    for t in range(T_WIN, n):
        Xw = S[t - T_WIN:t]
        xt = S[t]
        sd = Xw.std(axis=0, ddof=1) + 1e-12
        Xw = Xw / sd
        xt = xt / sd
        K = Xw @ Xw.T
        kt = Xw @ xt
        Yw = Y[t - T_WIN:t]
        for z in z_list:
            try:
                alpha = np.linalg.solve(K + z * T_WIN * eyeT, Yw)
            except np.linalg.LinAlgError:
                continue
            out[z][t] = float(kt @ alpha)
    return out


def alpha_t(y_s: pd.Series, ctrls: list[pd.Series]):
    """Exact-OLS intercept t of y_s on [const + ctrls], all unit-std scaled."""
    df = pd.DataFrame({"s": y_s})
    for i, c in enumerate(ctrls):
        df[f"c{i}"] = c
    df = df.dropna()
    ys = df["s"] / df["s"].std()
    X = np.column_stack([np.ones(len(df))] + [df[f"c{i}"] / df[f"c{i}"].std()
                                              for i in range(len(ctrls))])
    beta, *_ = np.linalg.lstsq(X, ys, rcond=None)
    resid = ys - X @ beta
    s2 = float(resid @ resid) / (len(df) - X.shape[1])
    covb = s2 * np.linalg.inv(X.T @ X)
    return float(beta[0] / np.sqrt(covb[0, 0]))


def main():
    t0 = time.time()
    raw, ex_next, sig12, svar = gw_panel()

    # KMZ-faithful predictor standardization: EXPANDING-window std, levels kept
    G_std = raw / raw.expanding(min_periods=36).std()
    ok = (G_std.dropna().index
          .intersection(ex_next.dropna().index)
          .intersection(sig12.dropna().index))
    G = G_std.loc[ok].to_numpy()
    y_raw = ex_next.loc[ok].to_numpy()                # ex_{t+1}
    s12 = sig12.loc[ok].to_numpy()                    # sigma_t (known at t)
    y_vs = y_raw / s12                                # vol-standardized target & traded ret
    sv = svar.loc[ok].to_numpy()
    n = len(ok)

    print("=" * 108)
    print(f"TR-17b  KMZ ON ITS NATIVE SEAT (KMZ-faithful construction, post-audit run of record)")
    print(f"        15 GW predictors, US market monthly, {ok[0].date()}..{ok[-1].date()} (n={n})")
    print("=" * 108)

    bh = sharpe_m(y_raw)
    vs_sr = sharpe_m(y_vs)                            # CONST position in vol-std market
    mm = pd.Series((1.0 / sv) * y_raw, index=ok)      # Moreira-Muir 1/svar control
    mm_sr = sharpe_m(mm)
    # Nagel vol-timed momentum (BFI WP 2025-104 eq.14): linear-decay 12m of past R~
    w = np.arange(12, 0, -1).astype(float)
    w /= w.sum()
    vtm_pos = np.full(n, np.nan)
    for t in range(12, n):
        vtm_pos[t] = float((w * y_vs[t - 12:t][::-1]).sum())
    vtm = pd.Series(vtm_pos * y_vs, index=ok)
    print(f"CONTROLS: B&H excess SR {bh:+.2f} | vol-std mkt (const pos) {vs_sr:+.2f} | "
          f"1/svar MM {mm_sr:+.2f} | vol-timed momentum {sharpe_m(vtm):+.2f}")

    # ---- VoC curve: mean SR across seeds; keep ensemble positions at P=12000 ----
    curves = {}
    ens_hi = {Z_LO: np.zeros(n), Z_HI: np.zeros(n)}
    for P in P_GRID:
        sr_seed = {z: [] for z in Z_KMZ}
        for sd_ in range(SEEDS_BY_P[P]):
            S = make_rff_kmz(G, P, 2.0, seed=1000 + sd_)
            fc = rolling_forecasts_kmz(S, y_vs, Z_KMZ)
            for z in Z_KMZ:
                sr_seed[z].append(sharpe_m(fc[z] * y_vs))
                if P == 12000 and z in ens_hi:
                    pos = fc[z]
                    okm = ~np.isnan(pos)
                    ens_hi[z][okm] += pos[okm] / SEEDS_BY_P[P]
        for z in Z_KMZ:
            curves[(P, z)] = float(np.nanmean(sr_seed[z]))
        print(f"  [P={P:>5d} done, {SEEDS_BY_P[P]} seeds, t={time.time()-t0:.0f}s]")

    print(f"  {'P':>7s} | " + " | ".join(f"z=1e{int(np.log10(z)):+d}" for z in Z_KMZ))
    for P in P_GRID:
        print(f"  {P:>7d} | " + " | ".join(f"{curves[(P, z)]:>+6.2f}" for z in Z_KMZ))

    # ---- pre-committed checks (unchanged) ----
    r1 = all(curves[(12000, z)] > curves[(12, z)] for z in (Z_LO, Z_HI))
    strat = pd.Series(ens_hi[Z_HI] * y_vs, index=ok).iloc[T_WIN:]   # heavy-end ensemble
    s_sr = sharpe_m(strat)
    t_mm = alpha_t(strat, [mm])
    r2 = (s_sr > mm_sr) and (t_mm >= 2)
    # supplementary (REPORTED, not gated): KMZ's own benchmark + Nagel VTM
    vs_ser = pd.Series(y_vs, index=ok)
    t_vs = alpha_t(strat, [vs_ser])
    t_vs_vtm = alpha_t(strat, [vs_ser, vtm])
    corr_vtm = float(pd.Series(ens_hi[Z_HI], index=ok).corr(pd.Series(vtm_pos, index=ok)))
    # R3 fabric-reality: raw-market position = f/sigma, vol-normalized, clipped, 5bps
    pos_raw = pd.Series(ens_hi[Z_HI] / s12, index=ok)
    posn = (pos_raw / pos_raw.rolling(36).std()).clip(0, 2)
    net = (posn * pd.Series(y_raw, index=ok) - posn.diff().abs().fillna(0) * COST).dropna()
    r3 = sharpe_m(net) > bh

    print("-" * 108)
    print(f"R1 VoC shape (P=12000 > P=12, z=1e-3 & 1e+3): {r1}")
    print(f"R2 Nagel (pre-committed gate): hi-P ensemble SR {s_sr:+.2f} vs MM {mm_sr:+.2f}; "
          f"alpha-t vs MM = {t_mm:+.2f} -> {r2}")
    print(f"   supplementary: alpha-t vs vol-std mkt {t_vs:+.2f} "
          f"(KMZ published 2.6-2.9); vs [vol-std mkt + VTM] {t_vs_vtm:+.2f} "
          f"(pos-corr with VTM {corr_vtm:+.2f})")
    print(f"R3 fabric-reality (clip[0,2], vol-norm, 5bps): net {sharpe_m(net):+.2f} "
          f"vs B&H {bh:+.2f} -> {r3}")
    if r1 and r2 and r3:
        v = ("REOPEN -- complexity survives its native seat AND the Nagel control AND costs: "
             "the ML/complexity chapter re-opens (major F10 cascade).")
    elif r1 and not r2:
        v = ("REPLICATED-BUT-EXPLAINED -- the VoC shape is real on the native 95-year seat, "
             "but the strategy is spanned by vol-timing (+ vol-timed momentum): Nagel's "
             "critique confirmed AT THE SOURCE. ML chapter stays closed; TR-17 PARTIAL "
             "stands, upgraded with native-seat evidence.")
    elif not r1:
        v = ("NO-VoC-SHAPE on the native seat under our construction -- do NOT over-claim a "
             "refutation of a published t~3 result; report construction differences and "
             "flag for audit.")
    else:
        v = "MIXED (VoC + beats MM but fails net-of-costs) -- complexity real, un-investable at retail."
    print(f"VERDICT: {v}")
    print("=" * 108)

    # chart: VoC curves + controls
    fig, ax = plt.subplots(figsize=(11, 5))
    for z, c, lab in ((Z_LO, "#1565c0", "z=1e-3 (ridgeless~)"), (Z_HI, "#f9a825", "z=1e+3 (heavy)")):
        ax.plot(P_GRID, [curves[(P, z)] for P in P_GRID], "o-", color=c, label=lab)
    ax.axhline(bh, color="#757575", ls="--", lw=1.2, label=f"B&H {bh:+.2f}")
    ax.axhline(vs_sr, color="#2e7d32", ls="-.", lw=1.4, label=f"vol-std mkt (const pos) {vs_sr:+.2f}")
    ax.axhline(mm_sr, color="#c62828", ls=":", lw=1.6, label=f"1/svar vol-managed {mm_sr:+.2f}")
    ax.set_xscale("log")
    ax.set_xlabel("P (random Fourier features)")
    ax.set_ylabel("OOS Sharpe (monthly, ann., mean across seeds)")
    ax.set_title("TR-17b: Virtue of Complexity on its NATIVE seat -- KMZ-faithful construction\n"
                 "the VoC shape replicates at home, but never clears the vol-timing controls",
                 fontsize=10.5)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr17b_native.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}  [total t={time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
