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

Run: uv run python scripts/tests/tr17b_kmz_native.py   (~2-5 min)
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
sys.path.insert(0, "scripts/tests")

from tr17_virtue_complexity import COST, P_GRID, Z_GRID, sharpe_m, voc_curve  # noqa: E402

GW_XLSX = "data/gw_predictors.xlsx"   # exported from Amit Goyal's site (sheet id in docs/24)


def gw_panel():
    df = pd.read_excel(GW_XLSX, sheet_name="Monthly")
    df.index = pd.PeriodIndex(df["yyyymm"].astype(int).astype(str), freq="M").to_timestamp("M")
    rf = df["Rfree"].astype(float)
    ret = df["ret"].astype(float)                      # S&P total return (with dividends)
    ex_next = (ret - rf).shift(-1)                     # target: NEXT-month excess return
    sig = pd.DataFrame({
        "dp": df["d/p"], "dy": df["d/y"], "ep": df["e/p"], "de": df["d/e"],
        "svar": df["svar"], "bm": df["b/m"], "ntis": df["ntis"], "tbl": df["tbl"],
        "lty": df["lty"], "ltr": df["ltr"], "tms": df["tms"], "dfy": df["dfy"],
        "dfr": df["dfr"], "infl": df["infl"].shift(1),   # publication lag (GW convention)
        "lag_ex": (ret - rf),                            # lagged excess return (known at t)
    }, index=df.index).astype(float)
    # KMZ seat starts 1926; require all 15 predictors present
    sig = sig.loc["1926-01-31":]
    ex_next = ex_next.loc[sig.index]
    svar = df["svar"].astype(float).loc[sig.index]
    return sig, ex_next, svar


def main():
    sig, y, svar = gw_panel()
    ok = sig.dropna().index.intersection(y.dropna().index)
    print("=" * 108)
    print(f"TR-17b  KMZ ON ITS NATIVE SEAT -- 15 GW predictors, US market monthly, "
          f"{ok[0].date()}..{ok[-1].date()} (n={len(ok)} months)")
    print("=" * 108)

    fc, y_al = voc_curve(sig, y)                       # identical machinery to TR-17
    ex = y_al
    bh = sharpe_m(ex)
    # Moreira-Muir control on the native seat: pos = c / svar_t (lagged by construction)
    volm_pos = (1.0 / svar.reindex(ex.index)).replace([np.inf, -np.inf], np.nan)
    mm = (volm_pos * ex).dropna()
    mm_sh = sharpe_m(mm)

    print(f"B&H excess Sharpe {bh:+.2f} | Moreira-Muir 1/svar control {mm_sh:+.2f}")
    print(f"  {'P':>7s} | " + " | ".join(f"{zn:>10s}" for zn in Z_GRID))
    curves = {}
    for (P, zn), f in fc.items():
        curves[(P, zn)] = sharpe_m((f * ex).dropna())
    for P in P_GRID:
        print(f"  {P:>7d} | " + " | ".join(f"{curves[(P, zn)]:>+10.2f}" for zn in Z_GRID))

    # ---- pre-committed checks ----
    r1 = all(curves[(12000, zn)] > curves[(12, zn)] for zn in Z_GRID)
    f_hi = fc[(12000, "heavy")]
    strat = (f_hi * ex).dropna()
    mm_r = (volm_pos * ex).reindex(strat.index).dropna()
    both = pd.concat([strat, mm_r], axis=1, keys=["s", "m"]).dropna()
    X = np.column_stack([np.ones(len(both)), both["m"] / both["m"].std()])
    beta, *_ = np.linalg.lstsq(X, both["s"] / both["s"].std(), rcond=None)
    resid = both["s"] / both["s"].std() - X @ beta
    se = np.sqrt(np.sum(resid**2) / (len(both) - 2) / len(both))
    t_alpha = float(beta[0] / se)
    corr_mm = float(both["s"].corr(both["m"]))
    r2 = (sharpe_m(strat) > mm_sh) and (t_alpha >= 2)
    posn = (f_hi / f_hi.rolling(36).std()).clip(0, 2)
    net = (posn * ex - posn.diff().abs().fillna(0) * COST).dropna()
    r3 = sharpe_m(net) > bh
    print("-" * 108)
    print(f"R1 VoC shape (P=12000 > P=12, both z): {r1}")
    print(f"R2 Nagel: hi-P Sharpe {sharpe_m(strat):+.2f} vs MM {mm_sh:+.2f}; "
          f"alpha-t vs MM = {t_alpha:+.2f} (corr {corr_mm:+.2f}) -> {r2}")
    print(f"R3 fabric-reality (clip[0,2], vol-norm, 5bps): net {sharpe_m(net):+.2f} vs B&H {bh:+.2f} -> {r3}")
    if r1 and r2 and r3:
        v = ("REOPEN -- complexity survives its native seat AND the Nagel control AND costs: "
             "the ML/complexity chapter re-opens (major F10 cascade).")
    elif r1 and not r2:
        v = ("REPLICATED-BUT-EXPLAINED -- the VoC shape is real on the native 95-year seat, "
             "but the strategy is spanned by the 1/svar vol-timing control: Nagel's critique "
             "confirmed AT THE SOURCE. ML chapter stays closed; TR-17 PARTIAL stands, upgraded "
             "with native-seat evidence.")
    elif not r1:
        v = ("NO-VoC-SHAPE on the native seat under our construction -- do NOT over-claim a "
             "refutation of a published t~3 result; report construction differences (S&P vs "
             "CRSP-vw target, T/P/seed conventions) and flag for audit.")
    else:
        v = "MIXED (VoC + beats MM but fails net-of-costs) -- complexity real, un-investable at retail."
    print(f"VERDICT: {v}")
    print("=" * 108)

    # chart: VoC curves + controls
    fig, ax = plt.subplots(figsize=(11, 5))
    for zn, c in (("ridgeless~", "#1565c0"), ("heavy", "#f9a825")):
        ax.plot(P_GRID, [curves[(P, zn)] for P in P_GRID], "o-", color=c, label=f"z={zn}")
    ax.axhline(bh, color="#757575", ls="--", lw=1.2, label=f"B&H {bh:+.2f}")
    ax.axhline(mm_sh, color="#c62828", ls=":", lw=1.6, label=f"1/svar vol-managed {mm_sh:+.2f}")
    ax.set_xscale("log")
    ax.set_xlabel("P (random Fourier features)")
    ax.set_ylabel("OOS Sharpe (monthly, ann.)")
    ax.set_title("TR-17b: Virtue of Complexity on its NATIVE seat (15 GW predictors, 1926-2024)\n"
                 "does the VoC curve clear the Nagel 1/svar control where it was born?",
                 fontsize=10.5)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr17b_native.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
