"""Signal: a rule's per-bar, per-symbol opinion."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum

import pandas as pd
from pydantic import BaseModel


class Direction(IntEnum):
    SHORT = -1
    FLAT = 0
    LONG = 1


class Signal(BaseModel):
    symbol: str
    ts: datetime
    direction: Direction = Direction.FLAT
    strength: float = 0.0       # 0..1; 0 = no conviction, 1 = max
    note: str | None = None

    model_config = {"use_enum_values": True}


def signals_to_long_frame(signals: list[Signal]) -> pd.DataFrame:
    if not signals:
        return pd.DataFrame(columns=["symbol", "ts", "direction", "strength"])
    return pd.DataFrame([s.model_dump() for s in signals])


def signals_to_pivot(signals: list[Signal], symbols: list[str]) -> pd.DataFrame:
    """Wide form: index=ts, columns=symbol, values=direction (-1/0/1)."""
    df = signals_to_long_frame(signals)
    if df.empty:
        return pd.DataFrame(columns=symbols)
    pivot = df.pivot_table(index="ts", columns="symbol", values="direction", aggfunc="last")
    return pivot.reindex(columns=symbols).fillna(0).astype(int).sort_index()
