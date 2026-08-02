"""TR-31 -- Campbell-Thompson (2008) sign-restricted equity-premium prediction.

Reopen basis: docs/22 marked this "information cost paid" -- GW predictors already
ingested (TR-17b). CT (RFS 2008, "Can Anything Beat the Historical Average?") answers
the Goyal-Welch out-of-sample failure: most predictors DO lose to the prevailing mean
OOS, but imposing two ECONOMIC sign restrictions -- (a) zero out a slope whose sign is
contrary to theory, (b) truncate the equity-premium forecast at zero -- rescues a small
but (CT argue) economically meaningful OOS R^2. This is the single-asset market-timing
predictive regression, the native habitat of the Goyal-Welch / Campbell-Thompson line.

F0 DECLARATION (pre-committed)
  claim        : sign restrictions turn the OOS R^2 (vs the expanding prevailing mean)
               POSITIVE for a meaningful set of GW predictors, AND that predictability
               carries economic value net of costs.
  seat         : US market monthly excess return, 1926-2024, 15 GW predictors, expanding
               window, 20yr (240m) burn-in before OOS evaluation begins.
  PRE-COMMITTED CHECKS
    CAL         : the UNRESTRICTED OOS R^2 must reproduce the Goyal-Welch result --
                  MEDIAN across predictors <= 0 (most lose to the mean). Fail -> STOP.
    C1 (CT core): with both sign restrictions, count predictors with R^2_OS > 0.
                  PASS iff >= 6 of 15 turn positive AND the best is >= +0.5% (monthly,
                  CT's "economically meaningful" scale).
    C2 (economic value): a mean-variance timer weight_t = clip( (1/gamma) * f_t / var_t,
                  0, 1.5) on the sign-restricted forecast, net 5bps/turn. PASS iff its
                  excess-over-RF Sharpe > the buy-and-hold AND > the prevailing-mean timer.
    C3 (NAGEL control, fabric requirement): does the CT timer beat the vol-timing triple
                  (constant-position vol-std market / 1-over-svar Moreira-Muir /
                  vol-timed momentum)? Report alpha-t of the CT timer vs each. PASS iff
                  Sharpe > all three AND alpha-t >= 2 vs the vol-std market.
  VERDICT RULE (pre-committed):
    C1 & C2 & C3 -> REPLICATED-AND-ADDS (CT predictability is real AND not just vol-timing)
    C1 & C2 & !C3 -> REPLICATED-BUT-EXPLAINED (sign-restricted predictability is real but
                     spanned by vol-timing -- Nagel confirmed at the source, as in TR-17b)
    C1 & !C2     -> STATISTICAL-ONLY (positive R^2_OS, no economic value net of costs)
    !C1          -> NO-OOS-RESCUE (sign restrictions do not turn R^2_OS positive here)
  anti-HARKing : expected signs fixed below BEFORE running (standard CT/GW theory signs);
               single pre-registered configuration; trials +1 family.

Run: uv run python scripts/tests/tr31_campbell_thompson.py   (~1-2 min)
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
sys.path.insert(0, "scripts/tests")
from tr17b_kmz_native import gw_panel  # noqa: E402

BURN = 240            # 20-year expanding-window burn-in before OOS evaluation
COST = 0.0005
GAMMA = 3.0           # mean-variance risk aversion
# theory-expected slope signs (standard CT/GW), fixed pre-run:
SIGN = {"dp": +1, "dy": +1, "ep": +1, "de": +1, "svar": +1, "bm": +1, "ntis": -1,
        "tbl": -1, "lty": -1, "ltr": +1, "tms": +1, "dfy": +1, "dfr": +1,
        "infl": -1, "lag_ex": +1}


def oos_forecasts(x: pd.Series, y: pd.Series):
    """Expanding-window OOS forecasts: prevailing mean, unrestricted reg, sign-restricted."""
    idx = x.index
    fm = np.full(len(idx), np.nan)     # prevailing mean
    fu = np.full(len(idx), np.nan)     # unrestricted regression
    fr = np.full(len(idx), np.nan)     # sign-restricted (CT)
    xv, yv = x.to_numpy(), y.to_numpy()
    s = SIGN[x.name]
    for t in range(BURN, len(idx)):
        yh = yv[:t]
        xh = xv[:t]
        m = float(np.nanmean(yh))
        fm[t] = m
        ok = ~np.isnan(xh) & ~np.isnan(yh)
        if ok.sum() < 60:
            fu[t] = fr[t] = m
            continue
        b1, b0 = np.polyfit(xh[ok], yh[ok], 1)   # slope, intercept
        pred = b0 + b1 * xv[t]
        fu[t] = pred
        # CT restriction (a): wrong-sign slope -> use prevailing mean
        f = pred if np.sign(b1) == s else m
        # CT restriction (b): non-negative equity premium
        fr[t] = max(f, 0.0)
    return pd.Series(fm, idx), pd.Series(fu, idx), pd.Series(fr, idx)


def r2_os(y, f, fm):
    m = ~np.isnan(f) & ~np.isnan(fm) & ~np.isnan(y)
    num = np.sum((y[m] - f[m]) ** 2)
    den = np.sum((y[m] - fm[m]) ** 2)
    return 1.0 - num / den


def sharpe_m(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 24 and x.std() > 0 else np.nan


def alpha_t(y_s, ctrls):
    df = pd.DataFrame({"s": y_s})
    for i, c in enumerate(ctrls):
        df[f"c{i}"] = c
    df = df.dropna()
    ys = df["s"] / df["s"].std()
    X = np.column_stack([np.ones(len(df))] + [df[f"c{i}"] / df[f"c{i}"].std() for i in range(len(ctrls))])
    res = sm.OLS(ys.to_numpy(), X).fit()
    return float(res.tvalues[0])


def main():
    raw, ex_next, sig12, svar = gw_panel()
    ok = raw.dropna().index.intersection(ex_next.dropna().index).intersection(sig12.dropna().index)
    raw, y = raw.loc[ok], ex_next.loc[ok]
    sig12, svar = sig12.loc[ok], svar.loc[ok]
    var = (sig12 ** 2)

    print("=" * 100)
    print(f"TR-31  CAMPBELL-THOMPSON sign-restricted equity premium -- {ok[0].date()}..{ok[-1].date()}, "
          f"n={len(ok)}, burn={BURN}m")
    print("=" * 100)

    rows = []
    best_fr = None
    best_r2 = -1e9
    for p in raw.columns:
        fm, fu, fr = oos_forecasts(raw[p], y)
        r2u = r2_os(y.to_numpy(), fu.to_numpy(), fm.to_numpy())
        r2r = r2_os(y.to_numpy(), fr.to_numpy(), fm.to_numpy())
        rows.append((p, r2u, r2r))
        if r2r > best_r2:
            best_r2, best_fr, best_fm = r2r, fr, fm
    tbl = pd.DataFrame(rows, columns=["pred", "r2_unrestricted", "r2_restricted"])
    print(tbl.to_string(index=False, float_format=lambda v: f"{v*100:+.2f}%"))

    med_u = tbl["r2_unrestricted"].median()
    cal = med_u <= 0
    print(f"\nCAL: median UNRESTRICTED R2_OS = {med_u*100:+.2f}% (rule <=0, GW result) -> "
          f"{'PASS' if cal else 'FAIL'}")
    if not cal:
        print("CALIBRATION FAILED -- machinery doesn't reproduce Goyal-Welch; stop.")
        return

    n_pos = int((tbl["r2_restricted"] > 0).sum())
    best = tbl["r2_restricted"].max()
    c1 = (n_pos >= 6) and (best >= 0.005)
    print(f"C1 (CT core): {n_pos}/15 predictors R2_OS>0 with sign restrictions; "
          f"best {best*100:+.2f}% (rules >=6 and best>=+0.50%) -> {'PASS' if c1 else 'FAIL'}")

    # C2: mean-variance timer on the best sign-restricted forecast
    w = (1.0 / GAMMA) * best_fr / var
    w = w.clip(0, 1.5).shift(0).fillna(0)   # forecast known at t, applied to ex_next at t
    strat = (w * y - w.diff().abs().fillna(0) * COST).dropna()
    rf0 = pd.Series(0.0, index=strat.index)   # y is already excess-over-RF
    bh = sharpe_m(y.loc[strat.index])
    wm = (1.0 / GAMMA) * best_fm / var
    wm = wm.clip(0, 1.5).fillna(0)
    mean_strat = (wm * y - wm.diff().abs().fillna(0) * COST).dropna()
    s_ct, s_mean = sharpe_m(strat), sharpe_m(mean_strat)
    c2 = (s_ct > bh) and (s_ct > s_mean)
    print(f"C2 (economic value): CT timer exSharpe {s_ct:+.2f} vs B&H {bh:+.2f} vs "
          f"prevailing-mean timer {s_mean:+.2f} -> {'PASS' if c2 else 'FAIL'}")

    # C3: Nagel controls
    vs = y / sig12                                        # const-position vol-std market
    mm = (1.0 / svar).replace([np.inf, -np.inf], np.nan) * y
    ww = np.arange(12, 0, -1).astype(float); ww /= ww.sum()
    yv = (y / sig12).to_numpy()
    vtm_pos = np.full(len(y), np.nan)
    for t in range(12, len(y)):
        vtm_pos[t] = float((ww * yv[t - 12:t][::-1]).sum())
    vtm = pd.Series(vtm_pos, index=y.index) * (y / sig12)
    s_vs, s_mm, s_vtm = sharpe_m(vs), sharpe_m(mm), sharpe_m(vtm)
    t_vs = alpha_t(strat, [vs.reindex(strat.index)])
    c3 = (s_ct > max(s_vs, s_mm, s_vtm)) and (t_vs >= 2.0)
    print(f"C3 (Nagel): CT {s_ct:+.2f} vs vol-std mkt {s_vs:+.2f} / MM {s_mm:+.2f} / "
          f"VTM {s_vtm:+.2f}; alpha-t vs vol-std mkt {t_vs:+.2f} -> {'PASS' if c3 else 'FAIL'}")

    if c1 and c2 and c3:
        v = "REPLICATED-AND-ADDS -- sign-restricted CT predictability is real AND beats vol-timing."
    elif c1 and c2:
        v = ("REPLICATED-BUT-EXPLAINED -- sign restrictions do rescue OOS R^2 and economic "
             "value, but the timer is spanned by vol-timing controls: Nagel confirmed at the "
             "source (as in TR-17b/KMZ). Free-data market timing stays a beta/vol story.")
    elif c1:
        v = "STATISTICAL-ONLY -- positive R^2_OS under sign restrictions, no economic value net of costs."
    else:
        v = "NO-OOS-RESCUE -- sign restrictions do not turn OOS R^2 positive on this seat."
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    order = tbl.sort_values("r2_restricted")
    yy = np.arange(len(order))
    ax.barh(yy - 0.2, order["r2_unrestricted"] * 100, 0.4, color="#c62828", alpha=0.8, label="unrestricted")
    ax.barh(yy + 0.2, order["r2_restricted"] * 100, 0.4, color="#2e7d32", alpha=0.85, label="sign-restricted")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(yy); ax.set_yticklabels(order["pred"], fontsize=8)
    ax.set_xlabel("OOS R^2 vs prevailing mean (%, monthly)")
    ax.set_title("C1: sign restrictions rescue OOS R^2?", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    names = ["CT timer", "B&H", "mean timer", "vol-std mkt", "1/svar MM", "VTM"]
    vals = [s_ct, bh, s_mean, s_vs, s_mm, s_vtm]
    cols = ["#1565c0", "#757575", "#90a4ae", "#2e7d32", "#c62828", "#f9a825"]
    ax.bar(names, vals, color=cols, alpha=0.9)
    ax.set_ylabel("excess Sharpe (ann.)")
    ax.set_title(f"C2/C3: CT timer vs benchmarks & Nagel controls\nalpha-t vs vol-std mkt = {t_vs:+.2f}",
                 fontsize=10)
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    for a in axes:
        a.grid(alpha=0.3, axis="x" if a is axes[0] else "y")
    fig.suptitle("TR-31: Campbell-Thompson sign-restricted equity-premium prediction", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr31_campbell_thompson.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
