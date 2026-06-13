"""Forecaster protocol — anything that turns OHLCV history into forward-looking predictions."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class Forecaster(Protocol):
    """Maps a long-form OHLCV frame to a forecast frame.

    Forecast frame columns (per ForecastRow):
        symbol, asof, horizon, target_ts, pred_close, pred_return, pred_vol,
        model_name, model_version
    """

    name: str
    version: str

    def forecast(
        self,
        ohlcv: pd.DataFrame,
        lookback: int,
        horizon: int,
    ) -> pd.DataFrame:
        ...
