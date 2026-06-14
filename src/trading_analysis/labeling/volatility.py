"""Volatility estimate used to scale triple-barrier widths (de Prado AFML §3.1)."""

from __future__ import annotations

import pandas as pd


def ewma_vol(close: pd.Series, span: int = 100) -> pd.Series:
    """EWMA of daily returns' stdev — the per-event target used to size barriers.

    For daily bars this is equivalent to de Prado's `getDailyVol`. Returns a Series
    aligned to `close` (NaN until enough history).
    """
    return close.pct_change().ewm(span=span).std()
