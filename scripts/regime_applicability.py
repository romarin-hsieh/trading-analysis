"""Filter/factor applicability map on real data — where does each factor actually predict?

Runs the regime-conditional attribution module on us_study: for momentum and low-vol, the IC
WITHIN each regime (trend / vol / drawdown), with bootstrap CIs and an effective-sample warning.

Run: uv run python scripts/regime_applicability.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger

logger.remove()
from trading_analysis.config import load_config  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.regime.conditional_attribution import (  # noqa: E402
    applicability_map,
    drawdown_regime,
    trend_regime,
    vol_regime,
)

HORIZON = 21


def main():
    cfg = load_config("configs/study.yaml")
    store = DuckStore("./data")
    syms = [s for s in cfg.universe.symbols if s != "SPY"]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    spy = store.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    lp = np.log(px)
    factors = {
        "momentum_6_1": lp.shift(21) - lp.shift(126),
        "lowvol": -px.pct_change().rolling(60).std().shift(1),
    }
    regimes = {"trend": trend_regime(spy), "vol": vol_regime(spy), "drawdown": drawdown_regime(spy)}

    # effective-sample warning: count independent regime episodes
    print("=" * 80)
    print("FACTOR / FILTER APPLICABILITY MAP — us_study 51 names, forward 21d IC")
    print("  (CI from stationary bootstrap; CI straddling 0 => edge not distinguishable from noise)")
    for rn, reg in regimes.items():
        flips = int((reg.dropna() != reg.dropna().shift()).sum())
        print(f"  regime '{rn}': {reg.dropna().value_counts().to_dict()}  | ~{flips} switches (few independent episodes!)")
    print("=" * 80)

    for fname, fw in factors.items():
        amap = applicability_map(fw, px, spy, horizon=HORIZON, regimes=regimes)
        print(f"\n### {fname}")
        for rn, tbl in amap.items():
            print(f"  [{rn}]")
            for regime_label, row in tbl.iterrows():
                ci = f"[{row['ic_lo']:+.3f}, {row['ic_hi']:+.3f}]" if np.isfinite(row.get("ic_lo", np.nan)) else "[n/a]"
                star = " *APPLY" if row.get("significant_fdr") else ""
                # n_eff << n_days: overlapping 21d windows -> few independent obs (honesty)
                print(f"     {regime_label:10s} n={int(row['n_days']):4d} (n_eff~{int(row['n_eff']):3d})  "
                      f"IC {row['mean_ic']:+.3f}  CI90 {ci}{star}")
    print("\n" + "=" * 80)
    print("  '*APPLY' = FDR-corrected significant (Benjamini-Hochberg across the whole regime")
    print("  family). Read: apply the factor only in *APPLY regimes; gate it OFF elsewhere.")
    print("  n_eff = n_days / autocorrelation-inflation — a 350-day regime may hold ~30 indep obs,")
    print("  so even a *APPLY star rests on few independent episodes. ICIR omitted (overlap-inflated).")
    print("=" * 80)


if __name__ == "__main__":
    main()
