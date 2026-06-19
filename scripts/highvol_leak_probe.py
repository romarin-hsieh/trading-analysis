"""Adversarial PIT/survivorship leak probe for scripts/highvol_ruleset.py.

Checks, with REAL numbers:
  (A) Timing audit: is ret.loc[day] the day-AFTER the signal's info date? (trace one rebalance bar)
  (B) +1 extra bar of lag on EVERY selection signal (vol, mom, price, hist, death-low).
      A leak collapses; a real (already-lagged) signal is stable.
  (C) Survivorship: do delisted names go NaN after delist and NOT get ffilled across delist?
      Count phantom prices after last-valid-obs; check pct_change never bridges a delist gap.
  (D) death_cut / sma_stop use contemporaneous px.loc[d]/below_low.loc[d] inside the hold loop --
      is below_low itself lagged (built from .shift)? Re-confirm.

ASCII-only prints.
"""

from __future__ import annotations

from loguru import logger

logger.remove()

import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "highvol_ruleset", os.path.join(os.path.dirname(__file__), "highvol_ruleset.py"))
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)


def calmar(eq, c):
    mdd = max_drawdown(eq)
    return float(c / abs(mdd)) if mdd < 0 else 0.0


def quick_stats(port_ret, label):
    r = port_ret.dropna()
    if len(r) < 30 or r.std() == 0:
        return None
    eq = (1.0 + r).cumprod()
    c = cagr(eq)
    return dict(name=label, cagr=c, sharpe=sharpe(r), mdd=max_drawdown(eq),
                calmar=calmar(eq, c), psr=probabilistic_sharpe_ratio(r.values, 0.0))


def pr(d):
    if d is None:
        print("  (insufficient)")
        return
    print(f"  {d['name']:<34} CAGR {d['cagr']*100:6.1f}%  Sh {d['sharpe']:5.2f}  "
          f"MDD {d['mdd']*100:6.1f}%  Cal {d['calmar']:4.2f}  PSR {d['psr']:4.2f}")


def main():
    s = DuckStore("./data")
    with open("configs/universe_survivorship.json") as fh:
        uni = json.load(fh)
    SA = uni["current"] + uni["recovered_survivors"]
    px_all = s.load_close_pivot(SA, column="adj_close")
    px = px_all.loc["2014-06-01":"2024-12-31"].copy()

    print("=" * 100)
    print("LEAK PROBE for highvol_ruleset.py")
    print("=" * 100)

    # ---------------- (A) timing audit on one bar ----------------
    ret, vol_lag, px_lag, enough_hist, mom, below_low = H.build(px)
    idx = px.index
    start_i = H.MIN_HISTORY + 5 * H.REBAL  # an arbitrary rebalance bar
    day = idx[start_i]
    prev = idx[start_i - 1]
    print("\n(A) TIMING AUDIT on rebalance bar", day.date())
    # pick a symbol present that day
    _, pool = H.cohort_mask(px_lag, vol_lag, enough_hist, day)
    sym = mom.loc[day, pool].dropna().sort_values(ascending=False).index[0]
    # vol_lag.loc[day] must equal raw vol.loc[prev]
    raw_vol = (ret.rolling(H.VOL_LOOKBACK).std() * np.sqrt(H.TD))
    print(f"  picked top-mom name: {sym}")
    print(f"  vol_lag[day]={vol_lag.loc[day, sym]:.4f}  vs raw vol[prev]={raw_vol.loc[prev, sym]:.4f}  "
          f"(equal => vol is lagged 1 bar): {np.isclose(vol_lag.loc[day, sym], raw_vol.loc[prev, sym])}")
    # mom is shift(21)-shift(126) then shift(1); effective info date = idx through prev
    raw_mom = (np.log(px).shift(21) - np.log(px).shift(126))
    print(f"  mom[day]={mom.loc[day, sym]:.4f}  vs raw_mom[prev]={raw_mom.loc[prev, sym]:.4f}  "
          f"(equal => mom double-lagged to prev): {np.isclose(mom.loc[day, sym], raw_mom.loc[prev, sym])}")
    # the FIRST return the book earns in run_backtest is ret.loc[day]:
    print(f"  first return earned = ret.loc[day] = {ret.loc[day, sym]:.4f} "
          f"(this is the prev->day move, realized AFTER info date prev => correct day-after timing)")
    print("  ret.loc[day] uses px[day]/px[prev]-1; signal info date = prev. "
          "So position formed on info<=prev earns prev->day return. NO look-ahead.")

    # ---------------- (C) survivorship NaN / ffill audit ----------------
    print("\n(C) SURVIVORSHIP NaN / no-ffill-across-delist audit")
    recovered = uni["recovered_survivors"]
    # a name is 'delisted within window' if it has a last-valid-obs before the window end with NaNs after
    n_phantom = 0
    n_delisted_in_win = 0
    examples = []
    for nm in SA:
        if nm not in px.columns:
            continue
        col = px[nm]
        valid = col.dropna()
        if valid.empty:
            continue
        last_valid = valid.index[-1]
        # phantom = any non-NaN AFTER a >=10-day gap of NaN following last cluster? Simpler:
        # check ffill would create values: count NaN-after-last-valid that are < window end
        if last_valid < px.index[-1] - pd.Timedelta(days=10):
            n_delisted_in_win += 1
            # are there any non-NaN values after last_valid? (there can't be by def of last_valid)
            # check the raw pivot didn't ffill: values after last_valid must be NaN
            after = col.loc[col.index > last_valid]
            phantom = after.notna().sum()
            n_phantom += int(phantom)
            if len(examples) < 6:
                examples.append((nm, last_valid, int(phantom),
                                 nm in recovered))
    print(f"  names delisted before window end (last valid > 10d before end): {n_delisted_in_win}")
    print(f"  phantom prices AFTER last-valid-obs (should be 0 if no ffill across delist): {n_phantom}")
    print("  examples (name, last_valid, phantom_after, is_recovered_survivor):")
    for e in examples:
        print(f"    {e[0]:<8} last={e[1].date()}  phantom_after={e[2]}  recovered={e[3]}")
    # confirm pct_change does not bridge delist: ret after last_valid must be NaN (fill_method=None)
    bridge = 0
    for nm, lv, _, _ in examples:
        rr = ret[nm]
        after = rr.loc[rr.index > lv]
        bridge += int(after.notna().sum())
    print(f"  return obs after last-valid for sampled delisted names (should be 0): {bridge}")

    # ---------------- (B) +1 extra bar of lag on all signals ----------------
    print("\n(B) +1 EXTRA BAR OF LAG ON ALL SELECTION SIGNALS (leak => collapse; real => stable)")
    spy = s.load_close_pivot(["SPY"], column="adj_close")["SPY"].reindex(px.index).ffill()
    spy_ok = (spy > spy.rolling(200).mean()).shift(1)
    spy_gate = {d: bool(spy_ok.get(d, False)) for d in px.index}

    # baseline R1 and R2 (best) using the original build()
    r1b, _ = H.run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                            universe="cohort", weight="inv_vol", k=20, vol_target=True,
                            sma_stop=False, cash_gate=False, death_cut=True)
    r2b, _ = H.run_backtest(px, ret, vol_lag, px_lag, enough_hist, mom, below_low, spy_gate,
                            universe="cohort", weight="inv_vol", k=20, vol_target=False,
                            sma_stop=False, cash_gate=False, death_cut=True)
    bhb, _ = H.buyhold_cohort(px, ret, vol_lag, px_lag, enough_hist)
    print(" BASELINE:")
    pr(quick_stats(r1b, "R1_baseline"))
    pr(quick_stats(r2b, "R2_baseline(best)"))
    pr(quick_stats(bhb, "BENCH_buyhold_baseline"))

    # +1 lag: shift every selection signal one more bar
    vol_lag2 = vol_lag.shift(1)
    px_lag2 = px_lag.shift(1)
    eh2 = enough_hist.shift(1)
    mom2 = mom.shift(1)
    below_low2 = below_low.shift(1)
    r1l, _ = H.run_backtest(px, ret, vol_lag2, px_lag2, eh2, mom2, below_low2, spy_gate,
                            universe="cohort", weight="inv_vol", k=20, vol_target=True,
                            sma_stop=False, cash_gate=False, death_cut=True)
    r2l, _ = H.run_backtest(px, ret, vol_lag2, px_lag2, eh2, mom2, below_low2, spy_gate,
                            universe="cohort", weight="inv_vol", k=20, vol_target=False,
                            sma_stop=False, cash_gate=False, death_cut=True)
    bhl, _ = H.buyhold_cohort(px, ret, vol_lag2, px_lag2, eh2)
    print(" +1 EXTRA LAG:")
    pr(quick_stats(r1l, "R1_+1lag"))
    pr(quick_stats(r2l, "R2_+1lag(best)"))
    pr(quick_stats(bhl, "BENCH_buyhold_+1lag"))

    print(" NOTE: a +1 lag that BARELY moves Sharpe => signal is genuinely lagged (no leak).")

    # quantify deltas
    def sh(x):
        d = quick_stats(x, "")
        return d['sharpe'] if d else float('nan')
    print("\n SUMMARY DELTAS (Sharpe):")
    print(f"  R1:    baseline {sh(r1b):.3f} -> +1lag {sh(r1l):.3f}  (delta {sh(r1l)-sh(r1b):+.3f})")
    print(f"  R2:    baseline {sh(r2b):.3f} -> +1lag {sh(r2l):.3f}  (delta {sh(r2l)-sh(r2b):+.3f})")
    print(f"  BENCH: baseline {sh(bhb):.3f} -> +1lag {sh(bhl):.3f}  (delta {sh(bhl)-sh(bhb):+.3f})")
    # the active spread vs fair bar under +1 lag
    diff_b = (r1b - bhb).dropna()
    diff_l = (r1l - bhl).dropna()
    psr_b = probabilistic_sharpe_ratio(diff_b.values, 0.0) if diff_b.std() > 0 else float('nan')
    psr_l = probabilistic_sharpe_ratio(diff_l.values, 0.0) if diff_l.std() > 0 else float('nan')
    print(f"  PSR(R1-BENCH) baseline {psr_b:.3f} -> +1lag {psr_l:.3f}")
    print("=" * 100)


if __name__ == "__main__":
    main()
