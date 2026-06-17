"""Kalman filter, applied — does an adaptive trend estimate beat the (too-slow) 200-SMA gate?

The session repeatedly found the 200-SMA regime gate too laggy (misses below-SMA recoveries,
docs/05). A Kalman local-linear-trend adapts its lag instead of using a fixed window. We test:
(1) how much FASTER the Kalman trend turns at the 2020/2022 inflections; (2) honestly, whether a
Kalman-slope regime gate beats the 200-SMA gate for timing SPY; (3) a dynamic market beta example.

Run: uv run python scripts/kalman_demo.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.models.kalman import dynamic_regression, local_linear_trend  # noqa: E402


def main():
    s = DuckStore("./data")
    spy = s.load_close_pivot(["SPY"], column="adj_close").ffill().iloc[:, 0]
    logp = np.log(spy)
    _lvl, slp = local_linear_trend(logp.to_numpy(), q_level=5e-5, q_slope=1e-6, r=1e-3)
    k_slope = pd.Series(slp, index=spy.index)
    sma200 = spy.rolling(200, min_periods=150).mean()

    # (1) lag at the big inflections: when does each signal turn risk-OFF then back ON?
    print("=" * 78)
    print("KALMAN TREND vs 200-SMA — adaptive lag")
    print("=" * 78)
    kal_off = (k_slope.shift(1) <= 0)          # Kalman: slope turns negative
    sma_off = (spy < sma200).shift(1)          # SMA: price crosses below
    for lo, hi, label in [("2020-02-01", "2020-08-01", "COVID crash+recovery"),
                          ("2022-01-01", "2023-06-01", "2022 bear+recovery")]:
        win = (spy.index >= lo) & (spy.index <= hi)
        ko = kal_off[win]
        so = sma_off[win]
        k_off_date = ko[ko].index.min()
        s_off_date = so[so].index.min()
        k_on_date = ko[~ko & (ko.index > (k_off_date or ko.index[0]))].index.min()
        s_on_date = so[~so & (so.index > (s_off_date or so.index[0]))].index.min()
        print(f"  {label}:")
        print(f"    risk-OFF  Kalman {str(k_off_date)[:10]}  vs SMA {str(s_off_date)[:10]}")
        print(f"    risk-ON   Kalman {str(k_on_date)[:10]}  vs SMA {str(s_on_date)[:10]}")

    # (2) honest gate test: time SPY with each signal (in SPY when ON, cash when OFF)
    ret = spy.pct_change().fillna(0.0)
    def gated(on):
        return (ret * on.astype(float)).rename("r")
    kal_on = (k_slope > 0).shift(1).fillna(False)
    sma_on = (spy > sma200).shift(1).fillna(False)
    print("-" * 78)
    print("HONEST GATE TEST — time SPY (in when ON, cash when OFF), 2016+:")
    for name, r in [("buy & hold", ret), ("200-SMA gate", gated(sma_on)), ("Kalman-slope gate", gated(kal_on))]:
        r = r[r.index >= "2016-01-01"]
        eq = (1 + r).cumprod()
        print(f"    {name:18s} CAGR {cagr(eq):+.1%}  Sharpe {sharpe(r):+.2f}  MDD {max_drawdown(eq):+.1%}")

    # (3) dynamic market beta of NVDA via Kalman regression (time-varying)
    nvda = s.load_close_pivot(["NVDA"], column="adj_close").ffill().iloc[:, 0].reindex(spy.index)
    df = pd.DataFrame({"nvda": nvda.pct_change(), "mkt": ret}).dropna()
    X = pd.DataFrame({"const": 1.0, "mkt": df["mkt"]})
    beta = dynamic_regression(df["nvda"].to_numpy(), X, q=5e-4, r=4e-4)["mkt"]
    beta.index = df.index
    print("-" * 78)
    print(f"DYNAMIC BETA (NVDA vs SPY, Kalman): min {beta.iloc[252:].min():.2f}  "
          f"max {beta.iloc[252:].max():.2f}  latest {beta.iloc[-1]:.2f}  (static OLS would force one number)")
    print("=" * 78)


if __name__ == "__main__":
    main()
