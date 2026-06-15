from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from trading_analysis.models.naive import NaiveDriftForecaster
from trading_analysis.models.ta_indicators import atr, ema, rsi, sma


def _make_ohlcv(n: int = 80, drift: float = 0.001, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    log_ret = rng.normal(loc=drift, scale=0.01, size=n)
    closes = 100 * np.exp(np.cumsum(log_ret))
    ts = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    return pd.DataFrame(
        {
            "symbol": ["TEST"] * n,
            "ts": ts,
            "open": closes - 0.1,
            "high": closes + 0.2,
            "low": closes - 0.3,
            "close": closes,
            "volume": [1_000_000] * n,
            "adj_close": closes,
            "bar": ["1d"] * n,
        }
    )


def test_naive_forecaster_shape_and_horizon():
    f = NaiveDriftForecaster()
    out = f.forecast(_make_ohlcv(), lookback=60, horizon=5)
    assert len(out) == 5
    assert set(out.columns) >= {
        "symbol",
        "asof",
        "horizon",
        "pred_close",
        "pred_return",
        "model_name",
    }
    assert sorted(out["horizon"].tolist()) == [1, 2, 3, 4, 5]
    # Drift was positive — pred_close should be increasing in horizon.
    assert out.sort_values("horizon")["pred_close"].is_monotonic_increasing


def test_sma_ema_rsi_atr_no_lookahead():
    df = _make_ohlcv(n=100)
    s = sma(df["close"], 20)
    e = ema(df["close"], 20)
    r = rsi(df["close"], 14)
    a = atr(df["high"], df["low"], df["close"], 14)
    # SMA/EMA enforce min_periods=window: first window-1 values are NaN.
    assert s.iloc[:19].isna().all()
    assert e.iloc[:19].isna().all()
    # RSI / ATR (EWM-based) require at least one prior observation; index 0 is NaN.
    assert pd.isna(r.iloc[0])
    assert pd.isna(a.iloc[0])
    # Last value must be finite for all four — sanity that they actually computed.
    for series in (s, e, r, a):
        assert not pd.isna(series.iloc[-1])
