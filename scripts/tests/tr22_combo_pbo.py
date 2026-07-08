"""TR-22 -- CSCV/PBO on the flagship combo FAMILY (the gap docs/20 flagged).

F0 DECLARATION (pre-committed)
  mechanism  : Bailey-Borwein-Lopez de Prado-Zhu CSCV. Question: was PICKING risk-parity-5
               out of the allocator x sleeve-set family an overfit selection? PBO = P(the
               in-sample-best config ranks below the OOS median).
  family     : reconstructable configs actually explored in the docs/08 era --
               allocators {equal-weight, risk-parity(log-barrier), inverse-vol, min-variance}
               x sleeve sets {5-sleeve, 4-no-leverage, 4-no-gold} = 12 configs, daily
               returns 2015-2026, same engine as validate_recommendation.
  VERDICT RULE (pre-committed; F5 heuristic now codified): PBO < 30% -> credible selection;
               30-50% -> caution; > 50% -> selection was noise (demote the flagship's
               "risk-parity beats alternatives" claim to luck -- note DGU already showed
               RP barely beats EW, so a mid PBO would be UNSURPRISING and NOT touch the
               alpha claim itself, which is family-independent per TR-18/20).
  scope note : this judges the ALLOCATOR/SLEEVE-SET selection, not the alpha's existence.
  mis-application risk : LOW (same data, same engine; family is the honest reconstruction).

POST-RUN AUDIT NOTE (pre-commitment above NOT edited):
  (1) CONFIRMED-BUG: the original inverse_vol fillna gave a ZERO-vol (dead) sleeve weight
      1/N and live sleeves 0 on 205 days (inf/inf=NaN artifact) -- an undeclared rule worth
      ~0.12 Sharpe on IV|5s, an order of magnitude larger than the 0.010 RP-vs-IV gap.
      Fixed to an explicit declared rule (dead sleeve dropped, live renormalized) + a
      weight-sum assertion; the alternative "all-in the flat sleeve" limit convention is
      reported as sensitivity.
  (2) CONFIRMED-BUG (composition): the 3 min_variance configs are straw men (IS-best in
      19/12,870 splits) that mechanically deflate PBO. The F0-committed headline stays the
      declared 12-config family, but layered PBO is now reported (full / ex-min-variance /
      finalists {RP,IV,EW}x5s): the allocator question among serious contenders reads
      ~40-50%+, i.e. "default to equal-weight-of-sleeves" is nearly as defensible as RP,
      and the RP-vs-IV #1 ranking is inside one-day-convention noise (auditor: giving IV
      the same signal lag as RP flips the order).
  (3) Alpha family-independence CONFIRMED by auditor: Carhart alpha exists for every
      allocator on 5 sleeves (EW t=2.92, IV 3.32, RP 3.44, even MV 2.16, daily freq --
      TR-18 monthly caveat applies to all).

Run: uv run python scripts/tests/tr22_combo_pbo.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.pbo import probability_of_backtest_overfitting  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402


def _inverse_vol(sub: pd.DataFrame, convention: str) -> pd.Series:
    """Explicit zero-vol rule (audit fix). 'renorm': dead (zero-vol) sleeve dropped, live
    sleeves renormalized. 'limit': all-in the flattest sleeve (the mathematical 1/sigma
    limit). Warmup / all-dead rows fall back to equal weight."""
    sd = sub.rolling(126).std().shift(1)
    iv = 1.0 / sd.clip(lower=1e-10) if convention == "limit" else (1.0 / sd).where(sd > 0)
    w = iv.div(iv.sum(axis=1), axis=0).fillna(0.0)
    dead = w.sum(axis=1) < 0.999
    w.loc[dead, :] = 1.0 / sub.shape[1]
    chk = (w.iloc[126:].sum(axis=1) - 1.0).abs().max()
    assert chk < 1e-9, f"inverse_vol weights do not sum to 1 (max err {chk:.2e})"
    return (w * sub).sum(axis=1)


def build_family(iv_convention: str = "renorm"):
    _rp, _ew, sleeves = vr.build_combo()          # 5 sleeve daily returns (gross-of-alloc)
    sets = {
        "5s": list(sleeves.columns),
        "4s-nolev": [c for c in sleeves.columns if c != "lev_trend"],
        "4s-nogold": [c for c in sleeves.columns if c != "gold"],
    }
    allocs = ("equal_weight", "risk_parity", "inverse_vol", "min_variance")
    fam = {}
    for sname, cols in sets.items():
        sub = sleeves[cols]
        for a in allocs:
            if a == "equal_weight":
                r = sub.mean(axis=1)
            elif a == "inverse_vol":
                r = _inverse_vol(sub, iv_convention)
            else:
                W = rebalance(sub, lookback=126, step=21, method=a)
                Wd = W.reindex(sub.index).ffill().shift(1).fillna(0.0)
                r = (Wd * sub).sum(axis=1)
            fam[f"{a}|{sname}"] = r
    F = pd.DataFrame(fam).iloc[126:].dropna()
    return F


def _pbo(F: pd.DataFrame, n_splits: int = 16) -> float:
    res = probability_of_backtest_overfitting(F.to_numpy(), n_splits=n_splits)
    return float(res["pbo"] if isinstance(res, dict) else res)


def main():
    F = build_family("renorm")
    print("=" * 96)
    print(f"TR-22  CSCV/PBO ON THE COMBO FAMILY  ({F.shape[1]} configs x {F.shape[0]} days, "
          f"{F.index[0].date()}..{F.index[-1].date()}; IV zero-vol rule = renorm)")
    print("=" * 96)
    sr = (F.mean() / F.std() * np.sqrt(252)).sort_values(ascending=False)
    print("full-sample Sharpe by config (NOTE: RP-vs-IV gap is inside 1-day-convention noise):")
    for k, v in sr.items():
        star = "  <- flagship" if k == "risk_parity|5s" else ""
        print(f"  {k:26s} {v:+.2f}{star}")
    finalists = ["risk_parity|5s", "inverse_vol|5s", "equal_weight|5s"]
    ex_mv = [c for c in F.columns if not c.startswith("min_variance")]
    pbo_full = _pbo(F)
    print("-" * 96)
    print("LAYERED PBO (S=16, C(16,8)=12,870 splits; audit fix -- composition sensitivity):")
    print(f"  L1 declared family (12, F0 headline)      = {pbo_full:.1%}")
    print(f"  L2 ex-min-variance straw men (9)          = {_pbo(F[ex_mv]):.1%}")
    print(f"  L3 finalists RP/IV/EW x 5-sleeve (3)      = {_pbo(F[finalists]):.1%}")
    Fl = build_family("limit")
    print(f"  [sensitivity, IV=limit convention] L1 = {_pbo(Fl):.1%}, "
          f"L2 = {_pbo(Fl[ex_mv]):.1%}, L3 = {_pbo(Fl[finalists]):.1%}")
    if pbo_full < 0.30:
        verdict = ("CREDIBLE on the F0-committed family (<30%) -- but layered PBO shows the "
                   "allocator pick among SERIOUS contenders is partly luck; honest operating rule: "
                   "RP and IV and EW-of-sleeves are near-interchangeable (DGU), do not sell the "
                   "allocator as edge. Alpha claim unaffected (family-independent: even EW-5s has "
                   "the alpha, TR-18/20 caveats apply).")
    elif pbo_full <= 0.50:
        verdict = ("CAUTION (30-50%) -- selection partly luck; consistent with DGU: optimizer "
                   "margins over EW are thin. Default to EW-of-sleeves as the honest baseline. "
                   "Alpha claim unaffected (family-independent, TR-18/20).")
    else:
        verdict = ("SELECTION=NOISE (>50%) -- the 'risk-parity beats alternatives' pick is not "
                   "defensible; default to equal-weight-of-sleeves. Alpha claim unaffected.")
    print(f"VERDICT (on F0 headline L1): {verdict}")
    print("=" * 96)


if __name__ == "__main__":
    main()
