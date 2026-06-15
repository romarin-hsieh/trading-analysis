"""Broker protocol and order/position dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    symbol: str
    side: Side
    qty: float
    ts: datetime
    price: float | None = None
    note: str | None = None


@dataclass
class Position:
    symbol: str
    qty: float = 0.0
    avg_price: float = 0.0


@dataclass
class Account:
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)


@runtime_checkable
class Broker(Protocol):
    name: str

    def submit(self, order: Order, fill_price: float) -> None: ...
    def account(self) -> Account: ...
    def history(self) -> list[Order]: ...
