"""TR-13 -- v1.2-B10 delisting terminal returns (Shumway 1997) applied to the survivorship test.

F0 DECLARATION: mechanism = delisting-bias correction (Shumway JF 1997: omitted performance-
related delisting returns average ~-30% NYSE/AMEX, ~-55% Nasdaq). Classification: data-layer /
verification. Native habitat: CRSP-style panels with delist codes. Seat tested: our survivorship-
aware 610-name union (which lacks delist REASONS -- we classify from price behavior). Mis-
application risk: MEDIUM (no delist codes; mergers must not get -30%). Pre-committed claim:
(a) most of our 9 in-window delistings are MERGERS (no crash) so direct injection changes little;
(b) the real bias sits in the 151 unrecovered names; a synthetic Shumway bound will widen the
measured +126bps survivorship inflation materially.

Policies compared on the union EW monthly buy&hold (survivorship_test Test 1):
  P0 baseline        exit at last observed price (the old optimistic convention)
  P1 shumway_all     inject -30% terminal return on every in-window delist
  P2 merger_aware    inject -30% ONLY where the final 20 bars already crashed >20% (bankruptcy-like)
  P3 synthetic bound add 151 synthetic "purged" names tracking union-EW with staggered -30% delists

Run: uv run python scripts/tests/tr13_delisting.py
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import survivorship_test as sv  # noqa: E402

from trading_analysis.backtest.metrics import cagr, sharpe  # noqa: E402

SHUMWAY = -0.30
CUTOFF = pd.Timestamp("2024-12-15")


def main():
    with open("configs/universe_survivorship.json") as fh:
        uni = json.load(fh)
    cur, surv = uni["current"], uni["recovered_survivors"]
    union = sorted(set(cur) | set(surv))
    px_cur = sv._load_pivot(cur)
    px_uni = sv._load_pivot(union)

    # ---- classify the in-window delistings from price behaviour --------------------
    surv_only = sorted(set(surv) - set(cur))
    last = px_uni[surv_only].apply(lambda c: c.last_valid_index())
    delisted = [t for t in surv_only if pd.notna(last[t]) and last[t] < CUTOFF]
    print("=" * 100)
    print("TR-13  DELISTING TERMINAL RETURNS (Shumway 1997) -- survivorship test restated")
    print("=" * 100)
    print(f"in-window delistings among the {len(surv_only)} recovered survivors: {len(delisted)}")
    crashers = []
    for t in delisted:
        s = px_uni[t].dropna()
        tail20 = float(s.iloc[-1] / s.iloc[-21] - 1) if len(s) > 21 else np.nan
        kind = "CRASH-like" if (np.isfinite(tail20) and tail20 < -0.20) else "merger-like"
        if kind == "CRASH-like":
            crashers.append(t)
        print(f"  {t:6s} last={last[t].date()!s}  final-20-bar={tail20:+7.1%}  -> {kind}")

    def inject(px, names, ret=SHUMWAY):
        """Append one synthetic bar with `ret` on the day after each name's last price."""
        out = px.copy()
        for t in names:
            s = out[t].dropna()
            if s.empty:
                continue
            li = out.index.get_loc(s.index[-1])
            if li + 1 < len(out.index):
                out.iloc[li + 1, out.columns.get_loc(t)] = s.iloc[-1] * (1 + ret)
        return out

    # ---- policies -------------------------------------------------------------------
    bh_cur = sv.ew_buyhold(px_cur)
    rows = []

    def add(name, px):
        r = sv.ew_buyhold(px)
        eq = (1 + r).cumprod()
        rows.append((name, cagr(eq), sharpe(r)))

    add("P0 union baseline (exit at last px)", px_uni)
    add("P1 union + Shumway -30% ALL delists", inject(px_uni, delisted))
    add("P2 union + -30% CRASH-like only", inject(px_uni, crashers))

    # P3: synthetic bound for the 151 unrecovered (purged) names
    removed_total = uni["removed_set_total"]
    n_missing = removed_total - len(surv)
    ew_ret = px_uni.pct_change(fill_method=None).mean(axis=1).fillna(0.0)
    ew_path = (1 + ew_ret).cumprod()
    idx = px_uni.index
    synth = {}
    # staggered delist dates: evenly spaced through the window (deterministic, no RNG)
    for k in range(n_missing):
        di = int(len(idx) * (k + 1) / (n_missing + 1))
        s = ew_path.copy()
        s.iloc[di] = s.iloc[di - 1] * (1 + SHUMWAY)   # terminal crash bar
        s.iloc[di + 1:] = np.nan                       # then gone
        synth[f"_SYN{k:03d}"] = s
    px_p3 = pd.concat([px_uni, pd.DataFrame(synth, index=idx)], axis=1)
    add(f"P3 + {n_missing} synthetic purged names", px_p3)

    c_cagr = cagr((1 + bh_cur).cumprod())
    print("-" * 100)
    print(f"{'policy':42s} {'CAGR':>8s} {'Sharpe':>7s} {'inflation vs cur':>17s}")
    print(f"{'CUR (current-only 501)':42s} {c_cagr:>+8.2%} {sharpe(bh_cur):>+7.2f} {'--':>17s}")
    for name, cg, sh in rows:
        print(f"{name:42s} {cg:>+8.2%} {sh:>+7.2f} {c_cagr - cg:>+16.2%}")
    print("-" * 100)
    print("READ: inflation-vs-cur is the survivorship bias estimate under each policy. P0 was the old")
    print("lower bound (+126bps). P1/P2 test the 9 knowable delistings; P3 is the SYNTHETIC upper-ish")
    print("bound assuming every purged name died Shumway-style mid-window (labeled synthetic -- the")
    print("truth lies between P2 and P3). F4: EW book of 501-761 names x ~2,510 days > 1.2M name-days.")
    print("=" * 100)


if __name__ == "__main__":
    main()
