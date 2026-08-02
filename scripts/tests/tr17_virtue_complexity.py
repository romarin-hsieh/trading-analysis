"""TR-17 -- Kelly-Malamud-Zhou "Virtue of Complexity" (JF 2024) replicated on our data + Nagel control.

F0 DECLARATION (pre-committed BEFORE running):
- Mechanism: single-asset market timing via Random Fourier Features (Rahimi-Recht) of a fixed
  signal set, ROLLING T=12 monthly window, ridge(less) regression, position = forecast.
  KMZ prove E[OOS performance] increases in P even for P >> T; empirically +0.47 Sharpe
  improvement on 1926-2020 US market, R^2 negative and irrelevant.
- NATIVE HABITAT: aggregate US equity, MONTHLY, 95 years, Goyal-Welch 15 predictors, NO costs,
  UNCONSTRAINED positions. OUR SEAT: SPY 1993-2026 (~400m) + QQQ 1999-2026 (~330m) replication,
  15 price/rate-constructible predictors (no macro series). Mis-application risk: MEDIUM
  (shorter sample, technical signal set) -- this is a MECHANISM replication, not an alpha claim.
- Pre-committed verdict rules:
  R1 mechanism: VoC curve replicates if OOS Sharpe at P=12,000 > P=12 for the ridge rows.
  R2 Nagel/Buncic control: the high-P strategy is a "vol-timing artifact" if its Sharpe <=
     Moreira-Muir vol-managed control OR its alpha-t vs that control < 2.
  R3 fabric reality: net 5bps/leg + positions clipped to [0,2] + vol-normalized -- does it still
     beat B&H excess Sharpe?
  PASSED = R1+R2+R3; PARTIAL = R1 only (mechanism real, edge explained/killed); FAILED = no R1.
- F4 honesty: ~730 OOS month-obs across two ~0.8-correlated assets (n_eff ~ 500) < 3,000 floor:
  UNDERPOWERED for an alpha claim by design; powered enough for the SHAPE of the VoC curve.
- Design registry: P grid {2,6,12,24,100,400,1200,6000,12000}; ridge z in {1e-3 (ridgeless-ish),
  10 (heavy)}; RFF gamma=1, seed=3, weights fixed per P; signals standardized in-window.
  Family = 18 variants -> trial registry.

Run: uv run python scripts/tests/tr17_virtue_complexity.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

SEED = 3
T_WIN = 12
P_GRID = [2, 6, 12, 24, 100, 400, 1200, 6000, 12000]
Z_GRID = {"ridgeless~": 1e-3, "heavy": 10.0}
COST = 0.0005


def monthly_panel(store, tkr):
    oh = store.load_ohlcv([tkr]).set_index("ts").sort_index()
    adj, close = oh["adj_close"], oh["close"]
    irx = store.load_ohlcv(["^IRX"]).set_index("ts")["close"].reindex(oh.index).ffill()
    m = adj.resample("ME").last()
    mr = m.pct_change()                                   # next-month target uses shift later
    rf_m = ((1 + irx / 100) ** (1 / 12) - 1).resample("ME").last()
    # 15 predictors, all computable from prices/rates, month-end sampled, lag handled at use
    daily_ret = adj.pct_change()
    vol21 = (daily_ret.rolling(21).std() * np.sqrt(252)).resample("ME").last()
    vol252 = (daily_ret.rolling(252).std() * np.sqrt(252)).resample("ME").last()
    volvol = (daily_ret.rolling(21).std().rolling(252).std() * np.sqrt(252)).resample("ME").last()
    hi52 = (close / close.rolling(252).max()).resample("ME").last()
    dd = (adj / adj.cummax()).resample("ME").last() - 1
    dy = (adj.pct_change(252) - close.pct_change(252)).resample("ME").last()   # dividend-yield proxy
    sig = pd.DataFrame({
        **{f"lag{k}": mr.shift(k - 1) for k in range(1, 7)},                    # lags 1..6
        "mom12": m.pct_change(12).shift(1),
        "vol21": vol21, "vol252": vol252, "volvol": volvol,
        "hi52": hi52, "dd": dd, "dy": dy,
        "rf": rf_m, "drf": rf_m.diff(12),
    })
    y = (mr - rf_m).shift(-1)                              # next-month EXCESS return (target)
    return sig, y, mr, rf_m, vol21


def rff(x, W, b):
    return np.sqrt(2.0) * np.cos(x @ W + b)


def voc_curve(sig, y, seed=SEED):
    """Rolling T=12 ridge forecasts for each (P, z). Returns dict[(P,zname)] -> forecast series."""
    rs = np.random.RandomState(seed)
    d = sig.shape[1]
    ok = sig.dropna().index.intersection(y.dropna().index)
    sig, y = sig.loc[ok], y.loc[ok]
    n = len(sig)
    out = {}
    feats = {P: (rs.normal(0, 1, size=(d, P)), rs.uniform(0, 2 * np.pi, size=P)) for P in P_GRID}
    X = sig.to_numpy()
    Y = y.to_numpy()
    for P in P_GRID:
        W, b = feats[P]
        preds = {zn: np.full(n, np.nan) for zn in Z_GRID}
        for t in range(T_WIN, n):
            win = slice(t - T_WIN, t)
            mu, sd = X[win].mean(0), X[win].std(0) + 1e-9
            Xw = (X[win] - mu) / sd
            xt = (X[t] - mu) / sd
            S = rff(Xw, W, b) / np.sqrt(P)                # T x P, kernel-scaled
            st = rff(xt[None, :], W, b) / np.sqrt(P)      # 1 x P
            K = S @ S.T                                    # T x T
            kt = (st @ S.T).ravel()                        # T
            for zn, z in Z_GRID.items():
                alpha = np.linalg.solve(K + z * np.eye(T_WIN), Y[win])
                preds[zn][t] = float(kt @ alpha)
        for zn in Z_GRID:
            out[(P, zn)] = pd.Series(preds[zn], index=sig.index)
    return out, y


def sharpe_m(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 24 and x.std() > 0 else np.nan


def main():
    store = DuckStore("./data")
    rows = {}
    curves = {}
    for tkr in ("SPY", "QQQ"):
        sig, y, _mr, _rf_m, vol21 = monthly_panel(store, tkr)
        fc, y_al = voc_curve(sig, y)
        ex = y_al                                          # next-month excess return (aligned)
        bh = sharpe_m(ex)
        # Moreira-Muir vol-managed control: pos ~ c/sigma^2 (lagged), same eval months
        volm = (1.0 / (vol21.reindex(y_al.index) ** 2)).replace([np.inf, -np.inf], np.nan)
        mm = (volm * ex).dropna()
        mm_sh = sharpe_m(mm)
        curves[tkr] = {}
        for (P, zn), f in fc.items():
            strat = (f * ex).dropna()                      # unconstrained KMZ timing
            curves[tkr][(P, zn)] = sharpe_m(strat)
        rows[tkr] = dict(bh=bh, mm=mm_sh, ex=ex, fc=fc, volm=volm)

    print("=" * 110)
    print("TR-17  VIRTUE OF COMPLEXITY (KMZ JF 2024) -- rolling T=12 RFF kernel-ridge, monthly, OOS")
    print("=" * 110)
    for tkr in ("SPY", "QQQ"):
        print(f"[{tkr}]  B&H excess Sharpe {rows[tkr]['bh']:+.2f} | Moreira-Muir vol-managed {rows[tkr]['mm']:+.2f}")
        print(f"  {'P':>7s} | " + " | ".join(f"{zn:>10s}" for zn in Z_GRID))
        for P in P_GRID:
            print(f"  {P:>7d} | " + " | ".join(f"{curves[tkr][(P, zn)]:>+10.2f}" for zn in Z_GRID))
    # ---- pre-committed checks on SPY (primary) -----------------------------------
    tkr = "SPY"
    sh_hiP = curves[tkr][(12000, "heavy")]
    sh_loP = curves[tkr][(12, "heavy")]
    r1 = sh_hiP > sh_loP
    # Nagel control: alpha of high-P strategy on vol-managed control
    f_hi = rows[tkr]["fc"][(12000, "heavy")]
    ex = rows[tkr]["ex"]
    strat = (f_hi * ex).dropna()
    mm_r = (rows[tkr]["volm"] * ex).reindex(strat.index).dropna()
    both = pd.concat([strat, mm_r], axis=1, keys=["s", "m"]).dropna()
    X = np.column_stack([np.ones(len(both)), both["m"] / both["m"].std()])
    beta, _res, *_ = np.linalg.lstsq(X, both["s"] / both["s"].std(), rcond=None)
    resid = both["s"] / both["s"].std() - X @ beta
    se = np.sqrt(np.sum(resid**2) / (len(both) - 2) / len(both))
    t_alpha = float(beta[0] / se)
    corr_mm = float(both["s"].corr(both["m"]))
    r2_ok = (sharpe_m(strat) > rows[tkr]["mm"]) and (t_alpha >= 2)
    # fabric reality: clip [0,2], vol-normalize, 5bps monthly turnover
    posn = (f_hi / f_hi.rolling(36).std()).clip(0, 2)
    net = (posn * ex - posn.diff().abs().fillna(0) * COST).dropna()
    r3 = sharpe_m(net) > rows[tkr]["bh"]
    print("-" * 110)
    print(f"CHECKS (SPY): R1 VoC curve (P=12k > P=12, heavy ridge): {r1}  ({sh_hiP:+.2f} vs {sh_loP:+.2f})")
    print(f"  R2 Nagel control: strat Sharpe {sharpe_m(strat):+.2f} vs vol-managed {rows[tkr]['mm']:+.2f}; "
          f"corr={corr_mm:+.2f}; alpha-t vs vol-managed = {t_alpha:+.2f}  -> pass: {r2_ok}")
    print(f"  R3 net+clipped reality: Sharpe {sharpe_m(net):+.2f} vs B&H {rows[tkr]['bh']:+.2f} -> pass: {r3}")
    verdict = "PASSED" if (r1 and r2_ok and r3) else ("PARTIAL" if r1 else "FAILED")
    print(f"VERDICT: {verdict}")
    print("F4 note: ~{:.0f} OOS months x2 correlated assets (n_eff<3000) -- mechanism-shape test,".format(
        len(rows['SPY']['ex'].dropna())))
    print("not an alpha claim. Family = 18 (P,z) variants -> trial registry.")
    print("=" * 110)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for i, tkr in enumerate(("SPY", "QQQ")):
        for zn in Z_GRID:
            ax[i].plot(P_GRID, [curves[tkr][(P, zn)] for P in P_GRID], marker="o", label=f"ridge {zn}")
        ax[i].axhline(rows[tkr]["bh"], color="gray", ls="--", lw=1, label="B&H excess")
        ax[i].axhline(rows[tkr]["mm"], color="green", ls=":", lw=1.2, label="vol-managed ctrl")
        ax[i].set_xscale("log")
        ax[i].set_xlabel("P (random features)")
        ax[i].set_title(f"{tkr}: OOS Sharpe vs complexity (T=12)")
        ax[i].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr17_voc.png", dpi=120)
    print("chart -> docs/tests/img/tr17_voc.png")


if __name__ == "__main__":
    main()
