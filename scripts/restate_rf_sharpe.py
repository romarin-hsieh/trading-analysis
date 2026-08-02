"""v1.2-B3 restatement: rf-aware Sharpe (flat days earn BIL; Sharpe on excess-over-BIL; Lo adj).

The adversarial review's critical finding: sharpe() was called with rf=0 everywhere and flat
positions earned 0%, inflating every absolute Sharpe in a 4-5% bill world and taxing timing
rules twice (they sat in fictional 0% cash). This restates the timing family under the corrected
convention and answers: does the "gating to cash subtracts" iron law survive?

  OLD: ret = pos*r - cost*turn                ; Sharpe = mean(ret)/std(ret)*sqrt(252)
  NEW: ret = pos*r + (1-pos)*bil - cost*turn  ; Sharpe = mean(ret-bil)/std(ret-bil)*sqrt(252)
  LO : annualization deflated for lag-1..5 autocorrelation (Lo 2002, FAJ 58(4))

Run: uv run python scripts/restate_rf_sharpe.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

from trading_analysis.data.store import DuckStore  # noqa: E402

COST = 0.0005
RULES = ["close_above_SMA200", "Vegas_loose", "VIX_riskoff_25", "TSmom_126d",
         "IBS_02_08", "TurnOfMonth", "VolTarget_12pct", "Chandelier_22_3ATR"]


def lo_factor(x: pd.Series, q: int = 5) -> float:
    """Lo (2002) annualization deflator: sqrt(252)/sqrt(252 + 2*sum (252-k) rho_k) ~ per-year basis."""
    rhos = [x.autocorr(k) for k in range(1, q + 1)]
    denom = 252 + 2 * sum((252 - k) * r for k, r in enumerate(rhos, 1) if np.isfinite(r))
    return float(np.sqrt(252 / max(denom, 1e-9)))


def sr(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan


def main():
    store = DuckStore("./data")
    pos = pd.read_parquet("data/_zoo_positions.parquet")
    r = pd.read_parquet("data/_zoo_qqq_ret.parquet")["qqq_ret"]
    bil = (store.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0]
           .reindex(r.index).ffill().pct_change().fillna(0.0))
    idx = r.loc["2015-01-01":].index
    r, bil, pos = r.loc[idx], bil.loc[idx], pos.reindex(idx).fillna(0.0)

    print("=" * 108)
    print("v1.2-B3 RESTATEMENT -- rf-aware Sharpe (flat days earn BIL; excess-over-BIL; Lo lag-5 adj)")
    print(f"period {idx[0].date()}..{idx[-1].date()} | BIL ann mean {bil.mean()*252:+.2%}")
    print("=" * 108)

    bh_old = sr(r)
    bh_new = sr(r - bil)
    lo_bh = lo_factor(r - bil)
    print(f"{'strategy':24s} {'expo':>5s} {'SR_old':>7s} {'SR_new':>7s} {'d':>6s} "
          f"{'gap_old':>8s} {'gap_new':>8s} {'rho1':>6s} {'SR_Lo':>7s}")
    print("-" * 108)
    print(f"{'QQQ buy&hold':24s} {'100%':>5s} {bh_old:+7.2f} {bh_new:+7.2f} {bh_new-bh_old:+6.2f} "
          f"{'--':>8s} {'--':>8s} {(r-bil).autocorr(1):6.2f} {bh_new*lo_bh/np.sqrt(1):+7.2f}")

    flips = []
    for name in RULES:
        if name not in pos.columns:
            continue
        p = pos[name].shift(1).fillna(0.0).clip(0, 1)
        turn = p.diff().abs().fillna(0.0)
        old = p * r - turn * COST
        new = p * r + (1 - p) * bil - turn * COST
        so, sn = sr(old), sr(new - bil)
        go, gn = so - bh_old, sn - bh_new
        rho1 = (new - bil).autocorr(1)
        lo = lo_factor(new - bil)
        expo = float(p.mean())
        if go < 0 <= gn:
            flips.append(name)
        print(f"{name:24s} {expo:5.0%} {so:+7.2f} {sn:+7.2f} {sn-so:+6.2f} "
              f"{go:+8.2f} {gn:+8.2f} {rho1:6.2f} {sn*lo:+7.2f}")

    print("-" * 108)
    print("READ: SR_old = rf=0 & flat-earns-0 (the pre-v1.2 convention). SR_new = flat-earns-BIL,")
    print("Sharpe on excess-over-BIL. gap_* = strategy minus buy&hold under the same convention --")
    print("the 'iron law' margin. SR_Lo = SR_new with Lo (2002) autocorrelation-adjusted annualization.")
    if flips:
        print(f"IRON-LAW FLIPS under the honest convention: {flips}")
    else:
        print("NO rule flips from losing to beating B&H -- the iron law's DIRECTION survives the")
        print("correction; only its MARGIN narrows (gates were being taxed with fictional 0% cash).")
    print("=" * 108)


if __name__ == "__main__":
    main()
