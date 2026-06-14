import numpy as np
import pandas as pd

from trading_analysis.factors.validation import (
    cross_sectional_ic,
    forward_returns,
    ic_summary,
    quantile_spread,
    validate_factor,
)
from trading_analysis.features.build import build_features


def test_forward_returns():
    dates = pd.date_range("2024-01-01", periods=5, freq="B")
    close = pd.DataFrame({"A": [100.0, 110.0, 121.0, 133.1, 146.41]}, index=dates)
    fr = forward_returns(close, 1)
    assert abs(fr["A"].iloc[0] - 0.10) < 1e-9
    assert pd.isna(fr["A"].iloc[-1])  # no future bar


def test_cross_sectional_ic_perfect_and_inverse():
    dates = pd.date_range("2024-01-01", periods=12, freq="B")
    syms = [f"S{i}" for i in range(8)]
    rng = np.random.default_rng(0)
    fwd = pd.DataFrame(rng.normal(size=(12, 8)), index=dates, columns=syms)
    assert cross_sectional_ic(fwd, fwd, min_names=5).mean() > 0.99       # factor == target
    assert cross_sectional_ic(-fwd, fwd, min_names=5).mean() < -0.99     # inverted


def test_ic_summary_fields_and_zero_vol():
    s = ic_summary(pd.Series([0.1, 0.2, -0.05, 0.15, 0.0]))
    assert s["n"] == 5
    assert set(s) >= {"mean_ic", "ic_std", "icir", "t_stat", "hit_rate", "n"}
    flat = ic_summary(pd.Series([0.1, 0.1, 0.1]))      # zero std -> ICIR NaN, no crash
    assert np.isnan(flat["icir"])


def test_quantile_spread_monotone_for_informative_factor():
    dates = pd.date_range("2024-01-01", periods=40, freq="B")
    syms = [f"S{i}" for i in range(10)]
    rng = np.random.default_rng(1)
    factor = pd.DataFrame(rng.normal(size=(40, 10)), index=dates, columns=syms)
    fwd = 0.05 * factor + pd.DataFrame(rng.normal(0, 0.01, size=(40, 10)), index=dates, columns=syms)
    qs = quantile_spread(factor, fwd, q=5)
    assert qs["mean_fwd_ret"].iloc[-1] > qs["mean_fwd_ret"].iloc[0]  # top quantile beats bottom


def _ohlcv(symbol, n, seed):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n)))
    ts = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame(
        {"symbol": symbol, "ts": ts, "open": close, "high": close * 1.01, "low": close * 0.99,
         "close": close, "volume": 1e6, "adj_close": close, "bar": "1d"}
    )


def test_validate_factor_end_to_end_structure():
    df = pd.concat([_ohlcv(f"S{i}", 300, seed=i) for i in range(8)], ignore_index=True)
    panel = build_features(df)
    close_wide = df.pivot_table(index="ts", columns="symbol", values="close").sort_index()
    res = validate_factor(panel, close_wide, "ret_20d", horizons=(1, 5), q=4)
    assert res["factor"] == "ret_20d"
    assert set(res["ic"]) == {1, 5}
    assert "mean_ic" in res["ic"][1]
    assert res["ic"][5]["n"] > 0
    assert list(res["quantiles"].columns) == ["mean_fwd_ret"]
