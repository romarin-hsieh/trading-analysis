"""Combine forecast distributions and TA signals into a single decision input."""

from __future__ import annotations

import pandas as pd


def smooth_forecast_returns(forecasts: pd.DataFrame, smoothing: int = 3) -> pd.DataFrame:
    """For each (symbol, asof) take a smoothed average of pred_return up to `smoothing` horizons."""
    if forecasts.empty:
        return forecasts.assign(pred_return_smoothed=[])
    df = forecasts.copy()
    df["pred_return_smoothed"] = (
        df.sort_values(["symbol", "asof", "horizon"])
        .groupby(["symbol", "asof"])["pred_return"]
        .transform(lambda s: s.rolling(window=smoothing, min_periods=1).mean())
    )
    return df


def latest_horizon(forecasts: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Filter to the row whose horizon == `horizon` for each (symbol, asof)."""
    if forecasts.empty:
        return forecasts
    return forecasts[forecasts["horizon"] == horizon].copy()
