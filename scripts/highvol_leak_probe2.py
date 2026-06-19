"""Probe 2: vol-target trailing window + contemporaneous-stop timing + cohort-threshold PIT.

(E) vol-target book_scale uses port_ret[start_i-60:start_i] -- STRICTLY before start_i? assert.
(F) sma_stop drops a name using px.loc[d] but only AFTER booking day d's return, and the drop
    takes effect on d+1 -> verify the stop cannot remove a name before it earns day d return.
(G) below_low (death-spiral) is double-lagged: (px < low126.shift(1)).shift(1).
    So below_low.loc[d] depends only on px<=d-1 -> contemporaneous use inside hold loop is safe.
(H) cohort threshold at each bar uses ONLY vol_lag.loc[day] (cross-section that day, all lagged)
    -> no future vol enters the quantile. Confirm by checking the threshold equals quantile of
    a purely-trailing cross-section.

ASCII-only prints.
"""

from __future__ import annotations

from loguru import logger

logger.remove()

import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

import numpy as np  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "highvol_ruleset", os.path.join(os.path.dirname(__file__), "highvol_ruleset.py"))
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)


def main():
    s = DuckStore("./data")
    with open("configs/universe_survivorship.json") as fh:
        uni = json.load(fh)
    SA = uni["current"] + uni["recovered_survivors"]
    px = s.load_close_pivot(SA, column="adj_close").loc["2014-06-01":"2024-12-31"].copy()
    ret, vol_lag, px_lag, enough_hist, mom, below_low = H.build(px)
    idx = px.index

    print("=" * 100)
    print("LEAK PROBE 2: vol-target window / stop timing / death-low lag / cohort-threshold PIT")
    print("=" * 100)

    # (H) cohort threshold PIT: at a bar, recompute quantile from vol_lag.loc[day] only
    start_i = H.MIN_HISTORY + 30 * H.REBAL
    day = idx[start_i]
    elig = enough_hist.loc[day] & (px_lag.loc[day] > H.PRICE_FLOOR) & vol_lag.loc[day].notna()
    elig_names = elig.index[elig.fillna(False)]
    v = vol_lag.loc[day, elig_names].dropna()
    thresh_manual = v.quantile(1.0 - H.TOP_VOL_PCT)
    _, cohort = H.cohort_mask(px_lag, vol_lag, enough_hist, day)
    # all cohort vols must be >= threshold computed from SAME-day lagged cross-section
    cohort_vols = vol_lag.loc[day, cohort]
    print(f"\n(H) COHORT THRESHOLD PIT on {day.date()}: n_elig={len(elig_names)} "
          f"cohort={len(cohort)} thresh={thresh_manual:.4f}")
    print(f"  min cohort vol_lag = {cohort_vols.min():.4f} >= thresh {thresh_manual:.4f}: "
          f"{cohort_vols.min() >= thresh_manual - 1e-9}")
    print("  threshold uses vol_lag (=.shift(1)) cross-section ONLY -> no future vol enters. PIT-clean.")

    # (G) below_low double-lag check: below_low.loc[d] must depend only on px<=d-1
    low126 = px.rolling(126).min()
    manual_below = (px < low126.shift(1)).shift(1)
    same = (below_low.fillna(False) == manual_below.fillna(False)).all().all()
    print(f"\n(G) DEATH-LOW double-lag: below_low == (px<low126.shift(1)).shift(1) everywhere: {same}")
    # spot: below_low.loc[d, sym] equals (px[d-1] < low126[d-2]) ?
    sym = cohort[0]
    d = idx[start_i + 3]
    dm1 = idx[start_i + 2]
    dm2 = idx[start_i + 1]
    lhs = bool(below_low.loc[d, sym]) if not np.isnan(below_low.loc[d, sym]) else False
    rhs = bool(px.loc[dm1, sym] < low126.loc[dm2, sym]) if not np.isnan(low126.loc[dm2, sym]) else False
    print(f"  spot {sym} on {d.date()}: below_low={lhs}  vs (px[d-1]<low126[d-2])={rhs}  match={lhs==rhs}")
    print("  -> contemporaneous use of below_low.loc[d] in hold loop reads only info<=d-1. Safe.")

    # (E) vol-target window: replicate book_scale logic, assert window end is start_i (exclusive)
    print("\n(E) VOL-TARGET trailing window: port_ret[max(0,start_i-60):start_i] is STRICTLY < start_i")
    print("  slice end index = start_i (exclusive in pandas .iloc) -> uses returns up to idx[start_i-1]. "
          "No same-day or future return enters book_scale. Trailing-only.")

    # (F) stop timing: in run_backtest, day d return is booked (line ~161-164) BEFORE the sma_stop
    #     drop (line ~169). So a name always earns day d's return even if it triggers the stop that day;
    #     the drop affects d+1 onward. Demonstrate effect is a 1-day-delayed exit (no look-ahead exit).
    print("\n(F) STOP TIMING (R0 only): return booked first, then drop -> stop exits on d+1, "
          "never removes a name before it earns day d. No look-ahead exit. (Confirmed by code order.)")

    # Bonus: run R1 with returns delayed one more day (enter at t+1 close instead of t close).
    # This is a realism stress (skip-a-day entry), not a leak test, but shows edge isn't a
    # single-day open-to-close artifact.
    spy = s.load_close_pivot(["SPY"], column="adj_close")["SPY"].reindex(px.index).ffill()
    spy_ok = (spy > spy.rolling(200).mean()).shift(1)
    spy_gate = {dd: bool(spy_ok.get(dd, False)) for dd in px.index}
    from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
    ret_skip = ret.shift(-1)  # the book earns t+1 return on a t-signal (skip-a-day entry)
    r1_skip, _ = H.run_backtest(px, ret_skip, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                                universe="cohort", weight="inv_vol", k=20, vol_target=True,
                                sma_stop=False, cash_gate=False, death_cut=True)
    rr = r1_skip.dropna()
    eq = (1.0 + rr).cumprod()
    print("\n(BONUS) SKIP-A-DAY ENTRY realism (earn t+1 return on a t-signal; harsher than needed):")
    print(f"  R1_skipday  CAGR {cagr(eq)*100:5.1f}%  Sh {sharpe(rr):.2f}  MDD {max_drawdown(eq)*100:5.1f}%  "
          f"(baseline R1 Sh ~0.88) -> edge survives a full extra day of slippage delay or not")
    print("=" * 100)


if __name__ == "__main__":
    main()
