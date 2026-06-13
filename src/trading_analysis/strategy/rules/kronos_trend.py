"""Kronos-driven trend rule.

Logic per bar:
  - Look at the smoothed predicted return at the configured horizon.
  - Long if pred_return >= +threshold; flat otherwise (no shorts in MVP).
  - Strength scales linearly between threshold and 5×threshold.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from trading_analysis.models.ensembles import smooth_forecast_returns
from trading_analysis.strategy.signal import Direction, Signal


class KronosTrendRule:
    name = "kronos_trend"

    def __init__(self, forecast_threshold: float = 0.005, smoothing: int = 3):
        self.forecast_threshold = forecast_threshold
        self.smoothing = smoothing

    def generate(
        self,
        ohlcv: pd.DataFrame,
        forecasts: pd.DataFrame | None = None,
        params: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[Signal]:
        if forecasts is None or forecasts.empty:
            return []

        smoothed = smooth_forecast_returns(forecasts, smoothing=self.smoothing)
        # Take 1-step-ahead smoothed return as the trade signal.
        h1 = smoothed[smoothed["horizon"] == 1].copy()
        h1["asof"] = pd.to_datetime(h1["asof"])

        out: list[Signal] = []
        for _, row in h1.iterrows():
            pr = float(row["pred_return_smoothed"])
            if pr >= self.forecast_threshold:
                direction = Direction.LONG
            else:
                direction = Direction.FLAT
            strength = min(max(pr / (5 * self.forecast_threshold), 0.0), 1.0)
            out.append(
                Signal(
                    symbol=row["symbol"],
                    ts=_to_dt(row["asof"]),
                    direction=direction,
                    strength=float(strength),
                    note=f"pred_ret={pr:+.4f}",
                )
            )
        return out

    def to_pivot(
        self,
        ohlcv: pd.DataFrame,
        forecasts: pd.DataFrame,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Build a pivot aligned to the OHLCV calendar.

        For each (symbol, ts), the signal at ts uses the forecast made at ts (asof=ts).
        """
        signals = self.generate(ohlcv, forecasts=forecasts, params=params)
        from trading_analysis.strategy.signal import signals_to_pivot

        symbols = sorted(ohlcv["symbol"].unique().tolist())
        sig_pivot = signals_to_pivot(signals, symbols)
        # Re-align to OHLCV ts so vectorbt sees a per-bar signal (forward fill missing days).
        ohlcv_ts = pd.DatetimeIndex(sorted(ohlcv["ts"].unique()))
        sig_pivot = sig_pivot.reindex(ohlcv_ts).ffill().fillna(0).astype(int)
        return sig_pivot


def _to_dt(x) -> datetime:
    return pd.Timestamp(x).to_pydatetime()
