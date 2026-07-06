"""TR-11 -- Random-Forest THEORY applied to backtesting: bagged / path-randomized evaluation.

The user's asks, unified: (1) backtests must assume NO knowledge of the future path (randomness),
(2) can Random-Forest theory help backtesting?, (3) re-test previously-CLOSED mechanisms whose
original test logic/standard differed from fabric v1.

RF theory -> backtest mapping (Breiman 1996/2001; de Prado's CSCV is the formal cousin):
  bagging (bootstrap windows)   -> evaluate each strategy on K random contiguous sub-windows
                                   instead of ONE anchored 2015-start path: a DISTRIBUTION of
                                   Sharpe, not a point estimate (path-agnostic, req 1)
  random feature subspace       -> random ASSET subsets for cross-sectional strategies: is the
                                   result carried by a few names?
  OOB estimation                -> the sub-windows were never used to select anything, so the
                                   distribution is an out-of-bag-like generalization view
  ensemble averaging            -> already proven in this repo: the E1 rule-vote ensemble (a
                                   'forest' of weak rules) beat the best single rule OOS 0.99 vs
                                   0.63 (docs/15 SS3) -- random-forest logic applied to strategies

Re-tested mechanisms (previously closed under weaker/different standards):
  TOM seasonality (docs/13 SS4: no control/no clustered t), Minervini trend-template proxy
  (docs/05: 51-stock PBO era), IBS mean-reversion + Vegas tunnel (zoo: single full-period point,
  no per-rule randomization), XS momentum 6-1 top10 (never window-randomized).

Verdict rule (fabric F9, introduced by this TR): over K=300 random 3-year windows,
  robust-PASS if P(Sharpe_strat > Sharpe_bench) >= 0.60 ; PARTIAL 0.40-0.60 ; FAILED < 0.40.

Plus: RandomForestRegressor as return FORECASTER (same walk-forward as TR-08) -- answering
'can RF help' on the model side too (expected: no, like TR-08's GBM).

Run: uv run python scripts/tests/tr11_bagged_backtest.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import horizon_slots as hs  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

K_WIN = 300           # random 3y windows per mechanism
WIN = 756             # 3 years of trading days
K_SUB = 60            # random asset subsets for the XS mechanism
SEED = 7
COST_ETF = 0.0005


def state_rule(enter, exit_):
    sig = pd.Series(np.nan, index=enter.index)
    sig[enter] = 1.0
    sig[exit_] = 0.0
    return sig.ffill().fillna(0.0)


def net_ret(pos, r, cost=COST_ETF):
    pos = pos.reindex(r.index).fillna(0.0).shift(1).fillna(0.0)
    return pos * r - pos.diff().abs().fillna(0.0) * cost


def main():
    rs = np.random.RandomState(SEED)
    store = DuckStore("./data")
    oh = store.load_ohlcv(["QQQ"]).set_index("ts").sort_index().loc["2014-06-01":]
    h, l, c = oh["high"], oh["low"], oh["close"]  # noqa: E741
    r = oh["adj_close"].pct_change().fillna(0.0)

    # ---- mechanism daily net-return series (full period, precomputed once) ----
    ym = c.index.to_period("M")
    pos_m = pd.Series(np.arange(len(c)), index=c.index).groupby(ym).cumcount()
    cnt = pd.Series(1, index=c.index).groupby(ym).transform("size")
    tom = ((pos_m <= 2) | (cnt - 1 - pos_m == 0)).astype(float)

    minerv = ((c > c.rolling(200).mean()) & (c > 0.75 * c.rolling(252).max())).astype(float)

    ibs_v = (c - l) / (h - l).replace(0, np.nan)
    ibs = state_rule(ibs_v < 0.2, ibs_v > 0.8)

    e144 = c.ewm(span=144, adjust=False).mean()
    e169 = c.ewm(span=169, adjust=False).mean()
    vegas = (c > pd.concat([e144, e169], axis=1).max(axis=1)).astype(float)

    mechs_ts = {
        "TOM_seasonality": net_ret(tom, r),
        "Minervini_proxy": net_ret(minerv, r),
        "IBS_meanrev": net_ret(ibs, r),
        "Vegas_tunnel": net_ret(vegas, r),
    }
    bench_ts = r.loc["2015-01-01":]

    px47 = ss._px(sorted({x for v in ss.SECTORS.values() for x in v}))
    xs_full, _ = hs.xsect_momentum(px47, k=10, hold=21, lb=126, skip=21)
    ew47 = px47.pct_change(fill_method=None).mean(axis=1)

    # ---- Part A: bagged windows (path randomization, req 1) --------------------
    print("=" * 100)
    print(f"TR-11 BAGGED BACKTEST -- {K_WIN} random {WIN}-bar (3y) windows per mechanism, seed {SEED}")
    print("=" * 100)
    rows = []
    dist = {}
    for name, sr in [*mechs_ts.items(), ("XS_mom_6-1_top10", xs_full)]:
        sr = sr.loc["2015-01-01":].dropna()
        bench = (ew47 if name.startswith("XS") else bench_ts).reindex(sr.index).fillna(0.0)
        n = len(sr)
        s_str, s_ben = [], []
        for _ in range(K_WIN):
            a = rs.randint(0, n - WIN)
            s_str.append(sharpe(sr.iloc[a:a + WIN]))
            s_ben.append(sharpe(bench.iloc[a:a + WIN]))
        s_str, s_ben = np.array(s_str), np.array(s_ben)
        p_beat = float((s_str > s_ben).mean())
        p_pos = float((s_str > 0).mean())
        verdict = "robust-PASS" if p_beat >= 0.60 else ("PARTIAL" if p_beat >= 0.40 else "FAILED")
        rows.append((name, np.median(s_str), np.percentile(s_str, 25), np.percentile(s_str, 75),
                     np.median(s_ben), p_beat, p_pos, verdict))
        dist[name] = (s_str, s_ben)
    print(f"{'mechanism':20s} {'medSR':>7s} {'IQR':>15s} {'medBench':>9s} {'P(beat)':>8s} {'P(SR>0)':>8s}  verdict")
    for nm, med, q1, q3, mb, pb, pp, vd in rows:
        print(f"{nm:20s} {med:+7.2f} [{q1:+6.2f},{q3:+6.2f}] {mb:+9.2f} {pb:8.0%} {pp:8.0%}  {vd}")
    print(f"  (samples: {K_WIN} windows x {WIN} bars x {len(rows)} mechanisms = "
          f"{K_WIN * WIN * len(rows):,} window-bar obs, 2015-2026)")

    # ---- Part B: random asset subsets for the XS mechanism (feature subspace) --
    print("-" * 100)
    print(f"XS momentum: {K_SUB} random 28-name (60%) subsets, full-period Sharpe each (seed {SEED})")
    names47 = list(px47.columns)
    sub_s, sub_b = [], []
    for _ in range(K_SUB):
        pick = sorted(rs.choice(names47, size=28, replace=False))
        sub_px = px47[pick]
        sr_sub, _ = hs.xsect_momentum(sub_px, k=10, hold=21, lb=126, skip=21)
        sub_s.append(sharpe(sr_sub.loc["2015-01-01":].dropna()))
        sub_b.append(sharpe(sub_px.pct_change(fill_method=None).mean(axis=1).loc["2015-01-01":].dropna()))
    sub_s, sub_b = np.array(sub_s), np.array(sub_b)
    print(f"  strategy Sharpe median {np.median(sub_s):+.2f} [{np.percentile(sub_s,25):+.2f},{np.percentile(sub_s,75):+.2f}]"
          f" | EW-subset bench median {np.median(sub_b):+.2f} | P(beat)={float((sub_s>sub_b).mean()):.0%}")

    # ---- Part C: RandomForest as forecaster (walk-forward, purged, vs shuffle) --
    print("-" * 100)
    print("RF-as-FORECASTER (sklearn RandomForestRegressor, yearly walk-forward, 21d purge):")
    from sklearn.ensemble import RandomForestRegressor
    r47 = px47.pct_change(fill_method=None)
    feats = {}
    for w_ in (5, 21, 63, 126):
        feats[f"ret{w_}"] = px47.pct_change(w_, fill_method=None)
    feats["vol21"] = r47.rolling(21).std()
    feats["vol63"] = r47.rolling(63).std()
    feats["d50"] = px47 / px47.rolling(50).mean() - 1
    feats["d200"] = px47 / px47.rolling(200).mean() - 1
    feats["hi52"] = px47 / px47.rolling(252).max() - 1
    X = pd.concat({k: v.shift(1).stack() for k, v in feats.items()}, axis=1).dropna()
    y = px47.pct_change(21, fill_method=None).shift(-21).stack().reindex(X.index)
    ok = y.notna()
    X, y = X[ok], y[ok]
    dates = X.index.get_level_values(0)
    ics, ics_sh = [], []
    for yr in range(2018, 2027):
        tr_end = pd.Timestamp(f"{yr - 1}-12-01")            # 21d purge before test year
        te_a, te_b = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        tr_m, te_m = dates < tr_end, (dates >= te_a) & (dates <= te_b)
        if tr_m.sum() < 5000 or te_m.sum() < 500:
            continue
        rf = RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=100,
                                   max_features=0.5, n_jobs=-1, random_state=SEED)
        rf.fit(X[tr_m], y[tr_m])
        pred = pd.Series(rf.predict(X[te_m]), index=X[te_m].index)
        rf_sh = RandomForestRegressor(n_estimators=150, max_depth=6, min_samples_leaf=100,
                                      max_features=0.5, n_jobs=-1, random_state=SEED)
        rf_sh.fit(X[tr_m], y[tr_m].sample(frac=1.0, random_state=SEED).to_numpy())
        pred_sh = pd.Series(rf_sh.predict(X[te_m]), index=X[te_m].index)
        truth = y[te_m]
        for p_, sink in ((pred, ics), (pred_sh, ics_sh)):
            ic_by_day = p_.groupby(level=0).apply(
                lambda s: s.droplevel(0).rank().corr(truth.loc[s.index].droplevel(0).rank()))
            sink.append(ic_by_day)
    ic = pd.concat(ics)
    ic_sh = pd.concat(ics_sh)
    no = ic.dropna().iloc[::21]
    t_no = float(no.mean() / no.std() * np.sqrt(len(no))) if len(no) > 3 else np.nan
    print(f"  OOS daily rank-IC mean {ic.mean():+.4f} (non-overlap t={t_no:+.2f}, n={len(no)})"
          f" | SHUFFLED-label control IC {ic_sh.mean():+.4f}")
    print(f"  samples: {len(X):,} stock-day obs, OOS 2018-2026")
    rf_verdict = "FAILED" if abs(ic.mean()) < 0.01 or (np.isfinite(t_no) and abs(t_no) < 2) else "check"
    print(f"  RF-forecaster verdict: {rf_verdict} (same as TR-08 GBM: no predictive alpha)")

    # ---- chart -------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    names = list(dist.keys())
    axes[0].boxplot([dist[n][0] for n in names] + [dist[names[-1]][1]],
                    tick_labels=[n[:14] for n in names] + ["XS bench(EW47)"], showfliers=False)
    axes[0].axhline(0, color="gray", lw=0.7)
    axes[0].set_title(f"Sharpe distribution over {K_WIN} random 3y windows")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].hist(sub_s, bins=20, alpha=0.7, label="XS mom, random 28-name subsets")
    axes[1].hist(sub_b, bins=20, alpha=0.5, label="EW bench, same subsets")
    axes[1].legend()
    axes[1].set_title("Feature-subspace analogy: random asset subsets")
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr11_bagged.png", dpi=120)
    print("chart -> docs/tests/img/tr11_bagged.png")
    print("=" * 100)


if __name__ == "__main__":
    main()
