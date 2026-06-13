from datetime import datetime

import pandas as pd

from trading_analysis.data.store import DuckStore


def _bar(symbol: str, ts: datetime, close: float = 100.0) -> dict:
    return {
        "symbol": symbol,
        "ts": ts,
        "open": close - 0.5,
        "high": close + 0.5,
        "low": close - 1.0,
        "close": close,
        "volume": 1_000_000,
        "adj_close": close,
        "bar": "1d",
    }


def test_upsert_is_idempotent(tmp_path):
    store = DuckStore(tmp_path)
    df = pd.DataFrame(
        [
            _bar("AAPL", datetime(2024, 1, 2), 180.0),
            _bar("AAPL", datetime(2024, 1, 3), 181.0),
            _bar("MSFT", datetime(2024, 1, 2), 380.0),
        ]
    )
    store.upsert_ohlcv(df)
    store.upsert_ohlcv(df)  # second time should not duplicate
    out = store.load_ohlcv(["AAPL", "MSFT"])
    assert len(out) == 3
    assert set(out["symbol"]) == {"AAPL", "MSFT"}


def test_load_close_pivot(tmp_path):
    store = DuckStore(tmp_path)
    df = pd.DataFrame(
        [
            _bar("AAPL", datetime(2024, 1, 2), 180.0),
            _bar("AAPL", datetime(2024, 1, 3), 181.0),
            _bar("MSFT", datetime(2024, 1, 2), 380.0),
            _bar("MSFT", datetime(2024, 1, 3), 381.0),
        ]
    )
    store.upsert_ohlcv(df)
    pivot = store.load_close_pivot(["AAPL", "MSFT"])
    assert pivot.shape == (2, 2)
    assert set(pivot.columns) == {"AAPL", "MSFT"}
    assert pivot.loc[pd.Timestamp("2024-01-03"), "MSFT"] == 381.0


def test_latest_ts_and_list(tmp_path):
    store = DuckStore(tmp_path)
    df = pd.DataFrame(
        [
            _bar("AAPL", datetime(2024, 1, 2), 180.0),
            _bar("AAPL", datetime(2024, 1, 3), 181.0),
        ]
    )
    store.upsert_ohlcv(df)
    assert store.latest_ts("AAPL") == datetime(2024, 1, 3)
    assert store.list_symbols() == ["AAPL"]
