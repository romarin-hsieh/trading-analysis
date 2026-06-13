"""Canonical pydantic schemas for OHLCV bars and related data."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import pandas as pd
from pydantic import BaseModel, Field, field_validator


class OHLCVBar(BaseModel):
    """One row of price data for one symbol at one timestamp."""

    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(ge=0.0)
    adj_close: float | None = None
    bar: str = "1d"  # 1d, 1wk, 1mo

    @field_validator("symbol")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("high")
    @classmethod
    def _high_consistent(cls, v: float, info) -> float:
        # Yahoo data sometimes has rounding inconsistencies; allow small slack.
        # Strict check is done at frame level in `OHLCVFrame.validate_frame`.
        return v


CANONICAL_COLUMNS = ["symbol", "ts", "open", "high", "low", "close", "volume", "adj_close", "bar"]


class OHLCVFrame:
    """Helper for converting a pandas DataFrame in canonical OHLCV form."""

    @staticmethod
    def to_frame(bars: list[OHLCVBar]) -> pd.DataFrame:
        if not bars:
            return pd.DataFrame(columns=CANONICAL_COLUMNS)
        df = pd.DataFrame([b.model_dump() for b in bars])
        return df[CANONICAL_COLUMNS]

    @staticmethod
    def from_frame(df: pd.DataFrame) -> list[OHLCVBar]:
        return [OHLCVBar.model_validate(row) for row in df.to_dict(orient="records")]

    @staticmethod
    def validate_frame(df: pd.DataFrame) -> pd.DataFrame:
        """Lightweight frame-level checks. Returns the frame on success, raises otherwise."""
        missing = set(CANONICAL_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"OHLCV frame missing columns: {missing}")
        if df["volume"].lt(0).any():
            raise ValueError("Negative volume detected")
        # Allow 0.01 tolerance for floating-point rounding in adjusted/raw mismatch.
        bad = df[(df["high"] + 1e-2 < df[["open", "close", "low"]].max(axis=1))]
        if len(bad) > 0:
            raise ValueError(f"{len(bad)} rows with high < max(open,close,low)")
        return df


class ForecastRow(BaseModel):
    symbol: str
    asof: datetime           # the bar time the forecast was made from
    horizon: int             # bars ahead
    target_ts: datetime      # the bar time being forecasted
    pred_close: float        # point prediction of close
    pred_return: float       # implied return vs last close
    pred_vol: float | None = None
    model_name: str
    model_version: str
