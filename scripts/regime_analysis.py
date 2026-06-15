"""5-year bull/bear regime analysis — does the rule's entry/exit timing do what we expect?

Expectation for a Minervini trend screen + 200-SMA regime gate:
  - BULL (SPY > 200SMA): participate — high exposure, capture most of the basket's upside.
  - BEAR (SPY < 200SMA): stand aside — low exposure, avoid most of the downside.
  - Turning points: de-risk quickly when a bear starts; ramp back when a bull resumes.

We test those expectations on 2020-2024 (COVID crash, 2021 bull, 2022 bear, 2023-24 bull),
with the full 2015-2024 history loaded for SMA/RS warmup.

Run: uv run python scripts/regime_analysis.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from trading_analysis.backtest.metrics import sharpe
from trading_analysis.config import load_config
from trading_analysis.data.store import DuckStore

logger.remove()

CFG = "configs/study.yaml"
W0, W1 = pd.Timestamp("2020-01-01"), pd.Timestamp("2024-12-31")
BEARS = {  # well-known SPY drawdown episodes for turning-point timing
    "COVID-2020": ("2020-02-19", "2020-03-23"),
    "Bear-2022": ("2022-01-03", "2022-10-12"),
}


def _seg_stats(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 2:
        return {"n": len(r), "ann_ret": np.nan, "vol": np.nan, "sharpe": np.nan}
    return {
        "n": len(r),
        "ann_ret": float((1 + r).prod() ** (252 / len(r)) - 1),
        "vol": float(r.std(ddof=1) * np.sqrt(252)),
        "sharpe": sharpe(r),
    }


def main():
    from trading_analysis.api import backtest_strategy

    base = load_config(CFG)
    res = backtest_strategy(base, write_report=False)
    ret = res.returns
    direction = res.weights                       # 0/1 [ts x symbol] (post-cap holding state)
    pf = res.raw

    # realized gross exposure = 1 - cash/value (group level)
    try:
        cash = pf.cash()
        value = pf.value()
        if isinstance(cash, pd.DataFrame):
            cash = cash.sum(axis=1)
        if isinstance(value, pd.DataFrame):
            value = value.sum(axis=1)
        exposure = (1.0 - cash / value).reindex(ret.index)
    except Exception:
        exposure = (direction > 0).sum(axis=1).reindex(ret.index) * base.backtest.target_percent
        exposure = exposure.clip(upper=1.0)

    store = DuckStore(base.data.cache_dir)
    spy = store.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    syms = [s for s in base.universe.symbols if s != "SPY"]
    basket = store.load_close_pivot(syms, column="adj_close").ffill().pct_change().mean(axis=1)
    spy_ret = spy.pct_change()

    # regime label: SPY vs its 200-SMA, lagged one bar (same gate the strategy uses)
    sma200 = spy.rolling(200).mean()
    bull = (spy > sma200).shift(1).reindex(ret.index).fillna(False)

    # restrict everything to the 5-year window
    win = (ret.index >= W0) & (ret.index <= W1)
    ret5, bull5, exp5 = ret[win], bull[win], exposure[win]
    basket5 = basket.reindex(ret.index)[win]
    spy5 = spy_ret.reindex(ret.index)[win]

    print("\n" + "=" * 70)
    print("5-YEAR REGIME ANALYSIS  —  Minervini+gate  /  2020-2024")
    print("=" * 70)
    n = len(ret5)
    print(f"bars: {n}  | bull (SPY>200SMA): {int(bull5.sum())} ({bull5.mean():.0%})  "
          f"| bear: {int((~bull5).sum())} ({(~bull5).mean():.0%})")
    print(f"avg realized gross exposure   : bull {exp5[bull5].mean():.0%}   bear {exp5[~bull5].mean():.0%}")
    print("-" * 70)
    print(f"{'segment':10s} {'n':>5s} {'strat_ann':>10s} {'strat_shp':>10s} {'basket_ann':>11s} {'SPY_ann':>9s}")
    for name, m in [("BULL", bull5), ("BEAR", ~bull5), ("ALL-5y", pd.Series(True, index=ret5.index))]:
        s = _seg_stats(ret5[m])
        b = _seg_stats(basket5[m])
        sp = _seg_stats(spy5[m])
        print(f"{name:10s} {s['n']:5d} {s['ann_ret']:+9.1%} {s['sharpe']:+10.2f} "
              f"{b['ann_ret']:+10.1%} {sp['ann_ret']:+8.1%}")
    # capture ratios
    up = basket5[bull5].sum()
    dn = basket5[~bull5].sum()
    s_up = ret5[bull5].sum()
    s_dn = ret5[~bull5].sum()
    print("-" * 70)
    print("CAPTURE (sum of daily log-ish returns, strategy / basket)")
    print(f"  upside capture (bull)  : {s_up/up:6.0%}   (want HIGH — participate in rallies)")
    print(f"  downside capture (bear): {(s_dn/dn) if dn!=0 else float('nan'):6.0%}   (want LOW/positive — avoid losses)")
    print(f"  strat return in bear   : {s_dn:+.1%}   basket in bear: {dn:+.1%}")

    # ---- holding-run analysis from the DIRECTION pivot (engine-independent) ----
    # from_orders rebalances daily, so pf.trades are rebalance lots, not positions. Derive each
    # name's continuous LONG run (entry->exit of the screen state) directly from the held mask.
    held = direction > 0
    px = store.load_close_pivot(base.universe.symbols, start=base.data.start, end=base.data.end,
                                column="adj_close").ffill().reindex(index=held.index, columns=held.columns)
    bull_on_day = bull.reindex(held.index).fillna(False)
    runs = []
    idxv = held.index
    for c in held.columns:
        col = held[c].to_numpy()
        i = 0
        while i < len(col):
            if col[i]:
                j = i
                while j < len(col) and col[j]:
                    j += 1
                t0 = idxv[i]
                if W0 <= t0 <= W1:
                    p0, p1 = px[c].iloc[i], px[c].iloc[j - 1]
                    r = (p1 / p0 - 1.0) if (p0 and p0 > 0) else np.nan
                    rg = "bull" if bool(bull_on_day.iloc[i]) else "bear"
                    runs.append((j - i, r, rg))
                i = j
            else:
                i += 1
    rdf = pd.DataFrame(runs, columns=["bars", "ret", "regime"]).dropna()
    print("-" * 70)
    print("HOLDING-RUN EFFECTIVENESS (continuous LONG runs entered 2020-2024, by entry regime)")
    print(f"{'regime':8s} {'n':>6s} {'win%':>6s} {'avg_ret':>9s} {'med_hold':>9s}")
    for rg in ["bull", "bear"]:
        g = rdf[rdf["regime"] == rg]
        if len(g) == 0:
            continue
        print(f"{rg:8s} {len(g):6d} {(g['ret']>0).mean():6.0%} {g['ret'].mean():+9.2%} {g['bars'].median():7.0f}b")
    print(f"  all runs: n={len(rdf)}, median hold {rdf['bars'].median():.0f} bars, "
          f"{(rdf['bars']<=5).mean():.0%} last <=5 bars  <-- churn / no hysteresis")

    # ---- turning-point timing ----
    print("-" * 70)
    print("TURNING-POINT TIMING (how fast did exposure fall once each bear began?)")
    for name, (b0, b1) in BEARS.items():
        b0, b1 = pd.Timestamp(b0), pd.Timestamp(b1)
        pre = exposure[(exposure.index >= b0 - pd.Timedelta(days=10)) & (exposure.index < b0)]
        seg = exposure[(exposure.index >= b0) & (exposure.index <= b1)]
        spy_dd = spy[(spy.index >= b0) & (spy.index <= b1)]
        dd = float(spy_dd.iloc[-1] / spy_dd.iloc[0] - 1.0) if len(spy_dd) else np.nan
        half = next((i for i, v in enumerate(seg.values) if v <= 0.5 * (pre.mean() if len(pre) else 1)), None)
        print(f"  {name:12s} SPY {dd:+.0%} over {len(seg):3d}d | "
              f"exposure {pre.mean() if len(pre) else float('nan'):.0%}->{seg.iloc[-1] if len(seg) else float('nan'):.0%}, "
              f"halved after {half if half is not None else '>end'} bars")
    print("=" * 70)


if __name__ == "__main__":
    main()
