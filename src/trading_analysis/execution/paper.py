"""In-process paper-trading broker. No external dependencies."""

from __future__ import annotations

from trading_analysis.execution.base import Account, Order, Position, Side


class PaperBroker:
    name = "paper"

    def __init__(self, initial_cash: float = 100_000.0, fees_bps: float = 5.0):
        self._account = Account(cash=initial_cash)
        self.fees_bps = fees_bps
        self._orders: list[Order] = []

    def submit(self, order: Order, fill_price: float) -> None:
        cost = fill_price * order.qty
        fee = abs(cost) * self.fees_bps / 10_000.0
        if order.side == Side.BUY:
            if self._account.cash < cost + fee:
                raise ValueError(
                    f"insufficient cash: have {self._account.cash:.2f}, "
                    f"need {cost + fee:.2f} for {order.symbol}"
                )
            self._account.cash -= cost + fee
            pos = self._account.positions.setdefault(order.symbol, Position(symbol=order.symbol))
            new_qty = pos.qty + order.qty
            pos.avg_price = (
                (pos.avg_price * pos.qty + fill_price * order.qty) / new_qty
                if new_qty > 0
                else 0.0
            )
            pos.qty = new_qty
        elif order.side == Side.SELL:
            pos = self._account.positions.setdefault(order.symbol, Position(symbol=order.symbol))
            if pos.qty < order.qty:
                raise ValueError(
                    f"oversell {order.symbol}: have {pos.qty}, sell {order.qty}"
                )
            pos.qty -= order.qty
            self._account.cash += cost - fee
            if pos.qty == 0:
                pos.avg_price = 0.0
        self._orders.append(order)

    def account(self) -> Account:
        return self._account

    def history(self) -> list[Order]:
        return list(self._orders)

    def equity(self, last_prices: dict[str, float]) -> float:
        total = self._account.cash
        for sym, pos in self._account.positions.items():
            total += pos.qty * last_prices.get(sym, pos.avg_price)
        return total
