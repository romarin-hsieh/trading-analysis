from datetime import datetime

import pandas as pd
import pytest

from trading_analysis.data.schema import OHLCVBar, OHLCVFrame


def test_ohlcv_bar_validates_and_uppercases():
    bar = OHLCVBar(
        symbol="aapl",
        ts=datetime(2024, 1, 5),
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1_000_000,
    )
    assert bar.symbol == "AAPL"
    assert bar.adj_close is None


def test_validate_frame_detects_negative_volume():
    df = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "ts": [datetime(2024, 1, 5)],
            "open": [100.0],
            "high": [105.0],
            "low": [99.0],
            "close": [104.0],
            "volume": [-5.0],
            "adj_close": [104.0],
            "bar": ["1d"],
        }
    )
    with pytest.raises(ValueError, match="Negative volume"):
        OHLCVFrame.validate_frame(df)


def test_validate_frame_detects_high_inconsistency():
    df = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "ts": [datetime(2024, 1, 5)],
            "open": [100.0],
            "high": [99.0],   # wrong: high < open
            "low": [98.0],
            "close": [99.5],
            "volume": [1.0],
            "adj_close": [99.5],
            "bar": ["1d"],
        }
    )
    with pytest.raises(ValueError, match="high"):
        OHLCVFrame.validate_frame(df)
