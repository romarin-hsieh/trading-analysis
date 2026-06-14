"""Causal feature panel from OHLCV — the X for factor/ML work.

POINT-IN-TIME GUARANTEE: every feature at bar t is computed only from data at or
before t (rolling/lagged, never centered or full-sample-fit). Therefore, for a single
symbol, `build_features(ohlcv)[ts <= T]` equals `build_features(ohlcv[ts <= T])`
column-for-column — the executable form of rigor-scorecard #1 (no look-ahead). Feature
SELECTION (stationarity / importance) is intentionally NOT here; it is data-dependent
and must run within CV folds.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.features.timeseries import (
    rolling_half_life,
    rolling_hurst,
    rolling_variance_ratio,
)
from trading_analysis.models.ta_indicators import atr, macd, realized_vol, rsi, sma

# The feature columns produced by build_features (excluding the symbol/ts keys).
FEATURE_COLUMNS = [
    "ret_1d", "ret_5d", "ret_20d", "roc_10",
    "px_to_sma20", "px_to_sma50", "px_to_sma200", "sma20_slope",
    "rsi_14", "macd_hist", "atr_pct", "rvol_20",
    "dist_high_252", "dist_low_252", "vol_ratio_20",
    "hurst_100", "half_life_60", "vratio_q2_40",
]


def _one_symbol(sub: pd.DataFrame) -> pd.DataFrame:
    close, high, low, volume = sub["close"], sub["high"], sub["low"], sub["volume"]
    f = pd.DataFrame(index=sub.index)

    f["ret_1d"] = np.log(close / close.shift(1))
    f["ret_5d"] = np.log(close / close.shift(5))
    f["ret_20d"] = np.log(close / close.shift(20))
    f["roc_10"] = close / close.shift(10) - 1.0

    s20, s50, s200 = sma(close, 20), sma(close, 50), sma(close, 200)
    f["px_to_sma20"] = close / s20 - 1.0
    f["px_to_sma50"] = close / s50 - 1.0
    f["px_to_sma200"] = close / s200 - 1.0
    f["sma20_slope"] = s20 / s20.shift(20) - 1.0

    f["rsi_14"] = rsi(close, 14)
    f["macd_hist"] = macd(close)["macd_hist"]
    f["atr_pct"] = atr(high, low, close, 14) / close
    f["rvol_20"] = realized_vol(close, 20)

    high_252 = close.rolling(252, min_periods=60).max()
    low_252 = close.rolling(252, min_periods=60).min()
    f["dist_high_252"] = close / high_252 - 1.0
    f["dist_low_252"] = close / low_252 - 1.0
    f["vol_ratio_20"] = volume / sma(volume, 20)

    f["hurst_100"] = rolling_hurst(close, 100)
    f["half_life_60"] = rolling_half_life(close, 60)
    f["vratio_q2_40"] = rolling_variance_ratio(close, 40, q=2)
    return f[FEATURE_COLUMNS]


def build_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Long-form causal feature panel: columns [symbol, ts, *FEATURE_COLUMNS].

    Computed per symbol on the canonical OHLCV schema. NaNs during warm-up are expected.
    """
    if ohlcv.empty:
        return pd.DataFrame(columns=["symbol", "ts", *FEATURE_COLUMNS])
    frames = []
    for symbol, sub in ohlcv.sort_values(["symbol", "ts"]).groupby("symbol", sort=True):
        sub = sub.sort_values("ts").reset_index(drop=True)
        f = _one_symbol(sub)
        f.insert(0, "ts", pd.to_datetime(sub["ts"]).to_numpy())
        f.insert(0, "symbol", symbol)
        frames.append(f)
    return pd.concat(frames, ignore_index=True)
