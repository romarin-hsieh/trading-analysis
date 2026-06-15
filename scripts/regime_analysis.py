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
    direction = res.weights                       # 0/1 [ts x symbol]
    trades = res.trades.copy()
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

    # ---- entry/exit effectiveness, tagged by entry regime ----
    trades["Entry Timestamp"] = pd.to_datetime(trades["Entry Timestamp"])
    trades["Exit Timestamp"] = pd.to_datetime(trades["Exit Timestamp"])
    t5 = trades[(trades["Entry Timestamp"] >= W0) & (trades["Entry Timestamp"] <= W1)].copy()
    bull_on_day = bull.reindex(ret.index).fillna(False)
    t5["entry_regime"] = t5["Entry Timestamp"].map(
        lambda d: "bull" if bool(bull_on_day.get(d, False)) else "bear")
    t5["dur"] = (t5["Exit Timestamp"] - t5["Entry Timestamp"]).dt.days
    t5["tiny"] = t5["Size"] * t5["Avg Entry Price"] < 1000.0   # < $1k = cash-starved scrap fill
    print("-" * 70)
    print("ENTRY/EXIT EFFECTIVENESS (trades entered 2020-2024, tagged by entry regime)")
    print(f"{'regime':8s} {'n':>5s} {'win%':>6s} {'avg_ret':>8s} {'med_dur':>8s} {'tiny%':>6s}")
    for rg in ["bull", "bear"]:
        g = t5[t5["entry_regime"] == rg]
        if len(g) == 0:
            continue
        print(f"{rg:8s} {len(g):5d} {(g['Return']>0).mean():6.0%} {g['Return'].mean():+8.2%} "
              f"{g['dur'].median():7.0f}d {g['tiny'].mean():6.0%}")
    print(f"  cash-starved scrap fills (<$1k): {t5['tiny'].mean():.0%} of all entries  "
          f"[{int(t5['tiny'].sum())}/{len(t5)}]  <-- sizing/cash-contention artifact")

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
