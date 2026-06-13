"""Connector protocol — every market-data source implements this."""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class Connector(Protocol):
    """A connector pulls OHLCV bars and returns them in the canonical schema."""

    name: str

    def fetch_ohlcv(
        self,
        symbols: list[str],
        start: date,
        end: date | None = None,
        bar: str = "1d",
    ) -> pd.DataFrame:
        """Return a DataFrame with the canonical OHLCV columns.

        Required columns: symbol, ts, open, high, low, close, volume, adj_close, bar.
        """
        ...
