"""Market-regime gate — operationalizes the CAN SLIM / Minervini "M" pillar.

Only allow new long entries when the market (a benchmark index, e.g. SPY) is in a
confirmed uptrend: price above a rising long-term SMA. This is the simplest,
most defensible market-direction filter (Mebane Faber / Minervini "trade with the
market"); an HMM/MarkovRegression probabilistic overlay can be layered on later.
"""

from __future__ import annotations

import pandas as pd

from trading_analysis.models.ta_indicators import sma


class SMARegimeGate:
    name = "sma_gate"

    def __init__(self, window: int = 200, rising_lookback: int = 21):
        self.window = window
        self.rising_lookback = rising_lookback

    def mask(self, benchmark_close: pd.Series) -> pd.Series:
        """Boolean Series (index=ts): True where the market is risk-on
        (close > SMA(window) AND the SMA is rising over `rising_lookback` bars)."""
        if benchmark_close is None or len(benchmark_close) == 0:
            return pd.Series(dtype=bool)
        s = pd.Series(benchmark_close).sort_index()
        ma = sma(s, self.window)
        rising = ma > ma.shift(self.rising_lookback)
        return ((s > ma) & rising).fillna(False)
