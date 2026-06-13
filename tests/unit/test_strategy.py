from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from trading_analysis.strategy.rules.kronos_trend import KronosTrendRule
from trading_analysis.strategy.rules.sma_crossover import SMACrossoverRule
from trading_analysis.strategy.signal import Direction


def _ohlcv(symbols: list[str], n: int = 80, seed: int = 1) -> pd.DataFrame:
    frames = []
    rng = np.random.default_rng(seed)
    for i, s in enumerate(symbols):
        log_ret = rng.normal(loc=0.001 * (i + 1), scale=0.01, size=n)
        closes = 100 * np.exp(np.cumsum(log_ret))
        ts = [datetime(2024, 1, 1) + timedelta(days=k) for k in range(n)]
        frames.append(
            pd.DataFrame(
                {
                    "symbol": [s] * n,
                    "ts": ts,
                    "open": closes - 0.1,
                    "high": closes + 0.2,
                    "low": closes - 0.3,
                    "close": closes,
                    "volume": 1_000_000,
                    "adj_close": closes,
                    "bar": "1d",
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_sma_crossover_pivot_dimensions():
    df = _ohlcv(["AAA", "BBB"], n=80)
    rule = SMACrossoverRule(fast=10, slow=30)
    pivot = rule.to_pivot(df)
    assert set(pivot.columns) == {"AAA", "BBB"}
    assert pivot.values.min() >= 0
    assert pivot.values.max() <= 1


def test_kronos_trend_uses_forecast_threshold():
    df = _ohlcv(["AAA"], n=60)
    forecasts = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "asof": df["ts"].iloc[i],
                "horizon": 1,
                "target_ts": df["ts"].iloc[i],
                "pred_close": float(df["close"].iloc[i]) * 1.01,
                "pred_return": 0.01,
                "pred_vol": None,
                "model_name": "naive",
                "model_version": "0.1",
            }
            for i in range(40, 60)
        ]
    )
    rule = KronosTrendRule(forecast_threshold=0.005, smoothing=1)
    signals = rule.generate(df, forecasts=forecasts)
    assert all(s.direction == Direction.LONG for s in signals)


def test_kronos_trend_below_threshold_is_flat():
    df = _ohlcv(["AAA"], n=60)
    forecasts = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "asof": df["ts"].iloc[i],
                "horizon": 1,
                "target_ts": df["ts"].iloc[i],
                "pred_close": float(df["close"].iloc[i]) * 1.001,
                "pred_return": 0.001,
                "pred_vol": None,
                "model_name": "naive",
                "model_version": "0.1",
            }
            for i in range(40, 60)
        ]
    )
    rule = KronosTrendRule(forecast_threshold=0.005, smoothing=1)
    signals = rule.generate(df, forecasts=forecasts)
    assert all(s.direction == Direction.FLAT for s in signals)
