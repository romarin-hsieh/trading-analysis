from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from trading_analysis.regime.sma_gate import SMARegimeGate
from trading_analysis.strategy.rules.minervini_trend import MinerviniTrendRule, rs_rating


def _ohlcv(symbol: str, closes, start=datetime(2023, 1, 2)) -> pd.DataFrame:
    n = len(closes)
    ts = [start + timedelta(days=i) for i in range(n)]
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame(
        {
            "symbol": symbol,
            "ts": ts,
            "open": closes,
            "high": closes * 1.01,
            "low": closes * 0.99,
            "close": closes,
            "volume": 1_000_000.0,
            "adj_close": closes,
            "bar": "1d",
        }
    )


def _universe(n: int = 300) -> pd.DataFrame:
    i = np.arange(n)
    up = 100 * (1.004 ** i)        # strong, persistent uptrend
    down = 200 * (0.998 ** i)      # persistent downtrend
    flat = 150 + 5 * np.sin(i / 20.0)
    mild = 120 * (1.0015 ** i)     # mild uptrend
    return pd.concat(
        [_ohlcv("UP", up), _ohlcv("DOWN", down), _ohlcv("FLAT", flat), _ohlcv("MILD", mild)],
        ignore_index=True,
    )


def test_rs_rating_is_cross_sectional_percentile():
    df = _universe()
    close = df.pivot_table(index="ts", columns="symbol", values="close").sort_index()
    rs = rs_rating(close)
    last = rs.iloc[-1].dropna()
    assert last["UP"] == last.max()      # strongest trend ranks top
    assert last["DOWN"] == last.min()    # weakest ranks bottom
    assert last.between(0.0, 100.0).all()


def test_minervini_longs_uptrend_not_downtrend_and_is_lagged():
    df = _universe()
    piv = MinerviniTrendRule(min_rs=70).to_pivot(df)
    assert set(np.unique(piv.values)).issubset({0, 1})   # binary long/flat
    assert piv["UP"].sum() > 0                            # uptrend triggers longs
    assert piv["DOWN"].sum() == 0                         # downtrend never does
    assert piv.iloc[0].sum() == 0                         # lagged: first bar has no signal


def test_regime_gate_risk_on_off():
    n = 260
    i = np.arange(n)
    up = pd.Series(100 * (1.003 ** i))
    down = pd.Series(300 * (0.997 ** i))
    assert bool(SMARegimeGate(window=200).mask(up).iloc[-1]) is True
    assert bool(SMARegimeGate(window=200).mask(down).iloc[-1]) is False
    assert SMARegimeGate(window=200).mask(pd.Series(dtype=float)).empty
