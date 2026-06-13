from datetime import datetime

import pytest

from trading_analysis.execution.base import Order, Side
from trading_analysis.execution.paper import PaperBroker


def test_paper_broker_buy_then_sell_pnl():
    pb = PaperBroker(initial_cash=100_000, fees_bps=0)
    pb.submit(
        Order(symbol="AAPL", side=Side.BUY, qty=10, ts=datetime(2024, 1, 2)),
        fill_price=180.0,
    )
    assert pb.account().cash == pytest.approx(100_000 - 1800)
    pb.submit(
        Order(symbol="AAPL", side=Side.SELL, qty=10, ts=datetime(2024, 1, 5)),
        fill_price=200.0,
    )
    assert pb.account().cash == pytest.approx(100_000 + 200)
    assert pb.account().positions["AAPL"].qty == 0


def test_paper_broker_oversell_raises():
    pb = PaperBroker(initial_cash=100_000)
    with pytest.raises(ValueError, match="oversell"):
        pb.submit(
            Order(symbol="AAPL", side=Side.SELL, qty=1, ts=datetime(2024, 1, 2)),
            fill_price=180.0,
        )


def test_paper_broker_underfunded_buy_raises():
    pb = PaperBroker(initial_cash=100)
    with pytest.raises(ValueError, match="insufficient cash"):
        pb.submit(
            Order(symbol="AAPL", side=Side.BUY, qty=10, ts=datetime(2024, 1, 2)),
            fill_price=180.0,
        )
