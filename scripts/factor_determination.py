"""Operationalize "how to determine variables/factors" (planning answer, section A).

For each candidate price/volume factor we run the gate that separates a real factor from a
data-mined one:
  1. IC / ICIR / hit-rate at multiple horizons (predictive power),
  2. cross-SUB-PERIOD stability (2016-19 AND 2020-24 — a real factor holds in both),
  3. quantile-spread MONOTONICITY (Q1->Q5 rising = economically coherent),
  4. INCREMENTAL IC after orthogonalizing against 12-1 momentum (does it add beyond the
     factor everyone already trades?),
  5. a robust PASS/FAIL verdict, with a note on the multiple-testing penalty.

Honest caveat printed below: with overlapping forward windows the raw t-stat is inflated, so
we judge on mean-IC sign-stability + monotonicity + incremental IC, not the headline t.

Run: uv run python scripts/factor_determination.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
from trading_analysis.config import load_config  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.validation import (  # noqa: E402
    cross_sectional_ic,
    forward_returns,
    ic_summary,
    quantile_spread,
)

HORIZON = 21
SPLIT = "2020-01-01"


def candidate_factors(px, vol):
    lp = np.log(px)
    ret = px.pct_change()
    return {
        "mom_12_1": lp.shift(21) - lp.shift(252),
        "mom_6_1": lp.shift(21) - lp.shift(126),
        "mom_3_1": lp.shift(21) - lp.shift(63),
        "rev_5": -(lp.shift(1) - lp.shift(6)),
        "lowvol": -ret.rolling(60).std().shift(1),
        "prox_52w_high": (px.shift(1) / px.rolling(252, min_periods=180).max().shift(1)),
        "vol_accum": (vol.rolling(20).mean() / vol.rolling(60).mean()).shift(1),
    }


def residual_ic(fac, base, fwd):
    """Incremental IC: cross-sectionally rank-residualize `fac` against `base` each date,
    then IC of the residual vs forward return. Measures signal beyond `base` (=momentum)."""
    idx = fac.index.intersection(base.index).intersection(fwd.index)
    out = {}
    for ts in idx:
        f, b, r = fac.loc[ts], base.loc[ts], fwd.loc[ts]
        m = f.notna() & b.notna() & r.notna()
        if int(m.sum()) < 10:
            continue
        fr, br = f[m].rank(), b[m].rank()
        beta = np.cov(fr, br)[0, 1] / np.var(br) if np.var(br) > 0 else 0.0
        resid = fr - beta * br
        out[ts] = resid.corr(r[m].rank())
    s = pd.Series(out, dtype=float).dropna()
    return float(s.mean()) if len(s) else np.nan


def run_gate(syms, label):
    store = DuckStore("./data")
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    oh = store.load_ohlcv(syms)
    vol = oh.pivot_table(index="ts", columns="symbol", values="volume", aggfunc="last").reindex(px.index)
    fwd = forward_returns(px, HORIZON)
    mom = np.log(px).shift(21) - np.log(px).shift(252)
    facs = candidate_factors(px, vol)

    print("=" * 96)
    print(f"FACTOR DETERMINATION — {label} ({px.shape[1]} names), forward {HORIZON}d return, 2015-2024")
    print("  (raw t inflated by overlapping windows; judge on IC sign-stability + monotonicity + incremental)")
    print("=" * 96)
    print(f"{'factor':16s} {'IC':>7s} {'ICIR':>6s} {'hit%':>5s} {'IC16-19':>8s} {'IC20-24':>8s} {'mono':>5s} {'incrIC':>7s} {'verdict'}")
    out = {}
    for name, fw in facs.items():
        ic = cross_sectional_ic(fw, fwd)
        summ = ic_summary(ic)
        m1, m2 = float(ic[ic.index < SPLIT].mean()), float(ic[ic.index >= SPLIT].mean())
        qs = quantile_spread(fw, fwd)["mean_fwd_ret"]
        mono = bool(qs.is_monotonic_increasing or qs.is_monotonic_decreasing) if len(qs) >= 3 else False
        incr = residual_ic(fw, mom, fwd) if name != "mom_12_1" else float("nan")
        stable = (np.sign(m1) == np.sign(m2)) and abs(summ["mean_ic"]) > 0.01
        verdict = "PASS" if (stable and mono) else ("weak" if stable or mono else "FAIL")
        out[name] = {"ic": summ["mean_ic"], "icir": summ["icir"], "m1": m1, "m2": m2, "verdict": verdict}
        print(f"{name:16s} {summ['mean_ic']:+7.3f} {summ['icir']:+6.2f} {summ['hit_rate']*100:4.0f}% "
              f"{m1:+8.3f} {m2:+8.3f} {mono!s:>5s} {incr:+7.3f} {verdict}")
    keep = [k for k, v in out.items() if v["verdict"] == "PASS"]
    print(f"KEEP (survives the gate): {keep if keep else 'NONE'}")
    return out


def main():
    import yaml
    study = [s for s in load_config("configs/study.yaml").universe.symbols if s != "SPY"]
    with open("configs/universe_sp500.yaml", encoding="utf-8") as f:
        sp = [s for s in yaml.safe_load(f)["symbols"] if s != "SPY"]
    small = run_gate(study, "us_study")
    big = run_gate(sp, "S&P 500")
    print("\n" + "=" * 96)
    print("BREADTH TEST — does going 51 -> ~500 names tighten ICIR and stabilize factor signs?")
    print(f"{'factor':16s} {'ICIR 51':>9s} {'ICIR 500':>9s} {'sign-stable 51':>15s} {'sign-stable 500':>16s}")
    for k in small:
        s51 = "yes" if np.sign(small[k]["m1"]) == np.sign(small[k]["m2"]) else "NO (flips)"
        s500 = "yes" if np.sign(big[k]["m1"]) == np.sign(big[k]["m2"]) else "NO (flips)"
        print(f"{k:16s} {small[k]['icir']:+9.2f} {big[k]['icir']:+9.2f} {s51:>15s} {s500:>16s}")
    print("=" * 96)


if __name__ == "__main__":
    main()
