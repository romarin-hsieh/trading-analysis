"""Minervini Trend Template (Stage-2) screen + cross-sectional RS Rating.

Per symbol, per bar → LONG when ALL criteria hold (FLAT otherwise):
  1. close > 150-day SMA and close > 200-day SMA
  2. 150-day SMA > 200-day SMA
  3. 200-day SMA trending up (> its value `rising_lookback` bars ago, ~1 month)
  4. 50-day SMA > 150-day SMA > 200-day SMA   (the "(4)" chain; with #2 + close>50SMA)
  5. close > 50-day SMA
  6. close >= (1 + above_low_pct) * 52-week low   (>= 30% above the 52w low)
  7. close >= (1 - within_high_pct) * 52-week high (within 25% of the 52w high)
  8. RS Rating >= min_rs

RS Rating: weighted trailing return (most-recent quarter double-weighted), then
cross-sectional percentile-ranked across the universe at each bar (→ 1..100). This
mirrors the open-source IBD-style approximation (no proprietary IBD feed); it is
relative to peers in the loaded universe, not to a benchmark index.

Signals are LAGGED one bar (`shift(1)`): the screen decided from bar t's close is
acted on bar t+1, so a backtest can never trade on the close it used to decide
(scorecard #1 — no look-ahead).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def rs_rating(close_wide: pd.DataFrame, quarter: int = 63) -> pd.DataFrame:
    """Cross-sectional RS Rating (1..100) per bar over a wide [ts x symbol] close frame.

    Weighted trailing return over four ~quarter (63-bar) windows, most recent
    double-weighted, then percentile-ranked across symbols at each date.
    """
    c = close_wide
    perf = (
        0.4 * (c / c.shift(quarter) - 1.0)
        + 0.2 * (c.shift(quarter) / c.shift(2 * quarter) - 1.0)
        + 0.2 * (c.shift(2 * quarter) / c.shift(3 * quarter) - 1.0)
        + 0.2 * (c.shift(3 * quarter) / c.shift(4 * quarter) - 1.0)
    )
    return perf.rank(axis=1, pct=True) * 100.0


class MinerviniTrendRule:
    name = "minervini_trend"

    def __init__(
        self,
        min_rs: float = 70.0,
        within_high_pct: float = 0.25,
        above_low_pct: float = 0.30,
        rising_lookback: int = 21,
        quarter: int = 63,
    ):
        self.min_rs = min_rs
        self.within_high_pct = within_high_pct
        self.above_low_pct = above_low_pct
        self.rising_lookback = rising_lookback
        self.quarter = quarter

    def to_pivot(
        self, ohlcv: pd.DataFrame, params: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Return a [ts x symbol] pivot of 0/1 (LONG) signals, lagged one bar."""
        if ohlcv.empty:
            return pd.DataFrame()
        # Prefer total-return (dividend+split-adjusted) prices when available, so SMAs /
        # 52w-high-low / RS are computed on the same series the P&L compounds. yfinance's
        # raw "close" is split-adjusted but NOT dividend-adjusted.
        price_col = "adj_close" if "adj_close" in ohlcv.columns else "close"
        close = (
            ohlcv.pivot_table(index="ts", columns="symbol", values=price_col, aggfunc="last")
            .sort_index()
        )

        sma50 = close.rolling(50, min_periods=50).mean()
        sma150 = close.rolling(150, min_periods=150).mean()
        sma200 = close.rolling(200, min_periods=200).mean()
        sma200_rising = sma200 > sma200.shift(self.rising_lookback)
        high_52w = close.rolling(252, min_periods=200).max()
        low_52w = close.rolling(252, min_periods=200).min()
        rs = rs_rating(close, quarter=self.quarter)

        passes = (
            (close > sma150)
            & (close > sma200)
            & (sma150 > sma200)
            & sma200_rising
            & (sma50 > sma150)
            & (close > sma50)
            & (close >= (1.0 + self.above_low_pct) * low_52w)
            & (close >= (1.0 - self.within_high_pct) * high_52w)
            & (rs >= self.min_rs)
        )
        direction = passes.fillna(False).astype(int)
        # Lag one bar: act on t+1 on a decision made from close[t]. No look-ahead.
        return direction.shift(1).fillna(0).astype(int).sort_index()
