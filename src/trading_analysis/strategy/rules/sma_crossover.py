"""SMA crossover — classic baseline. Long when fast SMA crosses above slow SMA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from trading_analysis.models.ta_indicators import sma
from trading_analysis.strategy.signal import Direction, Signal


class SMACrossoverRule:
    name = "sma_crossover"

    def __init__(self, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast SMA window must be < slow SMA window")
        self.fast = fast
        self.slow = slow

    def generate(
        self,
        ohlcv: pd.DataFrame,
        forecasts: pd.DataFrame | None = None,  # noqa: ARG002
        params: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[Signal]:
        signals: list[Signal] = []
        for symbol, sub in ohlcv.sort_values(["symbol", "ts"]).groupby("symbol"):
            sub = sub.sort_values("ts").reset_index(drop=True)
            close = sub["close"]
            fast_sma = sma(close, self.fast)
            slow_sma = sma(close, self.slow)
            for i in range(len(sub)):
                if pd.isna(fast_sma.iloc[i]) or pd.isna(slow_sma.iloc[i]):
                    continue
                direction = (
                    Direction.LONG if fast_sma.iloc[i] > slow_sma.iloc[i] else Direction.FLAT
                )
                strength = float(
                    abs(fast_sma.iloc[i] - slow_sma.iloc[i]) / max(slow_sma.iloc[i], 1e-9)
                )
                signals.append(
                    Signal(
                        symbol=symbol,
                        ts=_to_dt(sub["ts"].iloc[i]),
                        direction=direction,
                        strength=min(strength * 50, 1.0),
                        note=f"sma{self.fast}/{self.slow}",
                    )
                )
        return signals

    def to_pivot(
        self, ohlcv: pd.DataFrame, params: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Vector form for backtests: returns pivot of -1/0/1 by ts × symbol."""
        from trading_analysis.strategy.signal import signals_to_pivot

        signals = self.generate(ohlcv, params=params)
        symbols = sorted(ohlcv["symbol"].unique().tolist())
        return signals_to_pivot(signals, symbols)


def _to_dt(x) -> datetime:
    return pd.Timestamp(x).to_pydatetime()
