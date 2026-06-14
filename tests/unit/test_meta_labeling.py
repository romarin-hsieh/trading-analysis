import numpy as np
import pandas as pd

from trading_analysis.features.build import FEATURE_COLUMNS, build_features
from trading_analysis.ml.meta_labeling import (
    build_meta_dataset,
    evaluate_meta,
    walk_forward_meta_prob,
)


def _ohlcv(symbol, n=320, seed=0):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
    ts = pd.date_range("2022-06-01", periods=n, freq="B")
    return pd.DataFrame(
        {"symbol": symbol, "ts": ts, "open": close, "high": close * 1.02, "low": close * 0.98,
         "close": close, "volume": 1e6, "adj_close": close, "bar": "1d"}
    )


def test_build_meta_dataset_structure():
    df = pd.concat([_ohlcv("AAA", seed=1), _ohlcv("BBB", seed=2)], ignore_index=True)
    panel = build_features(df)
    # primary rule: "long" every 8th bar after warm-up, per symbol
    close_wide = df.pivot_table(index="ts", columns="symbol", values="close").sort_index()
    direction = pd.DataFrame(0, index=close_wide.index, columns=close_wide.columns)
    direction.iloc[210::8] = 1
    ds = build_meta_dataset(df, direction, panel, pt=1.0, sl=1.0, num_bars=15)
    assert list(ds.columns) == ["symbol", "t_event", "t1", "y", "ret", *FEATURE_COLUMNS]
    assert ds["y"].isin([0, 1]).all()
    assert (pd.DatetimeIndex(ds["t1"]) >= pd.DatetimeIndex(ds["t_event"])).all()
    assert ds["t_event"].is_monotonic_increasing       # pooled + sorted by event time
    assert len(ds) > 0


def _learnable_dataset(n=400, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-04", periods=n, freq="B")  # unique, sorted
    f_signal = rng.normal(0, 1, n)
    y = (f_signal + rng.normal(0, 0.5, n) > 0).astype(int)    # signal predicts the label
    f_noise = rng.normal(0, 1, n)
    return pd.DataFrame(
        {"t_event": dates, "t1": dates + pd.Timedelta(days=3), "y": y,
         "f_signal": f_signal, "f_noise": f_noise}
    )


def test_walk_forward_meta_prob_learns_and_lifts():
    ds = _learnable_dataset()
    prob = walk_forward_meta_prob(ds, feature_cols=["f_signal", "f_noise"], n_splits=5)
    assert len(prob) == len(ds)
    assert prob.notna().mean() > 0.9          # every fold trains (both classes present)
    ev = evaluate_meta(ds, prob, threshold=0.5)
    assert ev["auc"] > 0.6                     # the model learned the signal out-of-sample
    assert ev["meta_hit_rate"] > ev["rule_hit_rate"]   # filtering improves the win rate
    assert ev["lift"] > 0


def test_walk_forward_meta_prob_random_no_edge():
    rng = np.random.default_rng(7)
    n = 400
    dates = pd.date_range("2021-01-04", periods=n, freq="B")
    ds = pd.DataFrame(
        {"t_event": dates, "t1": dates + pd.Timedelta(days=3),
         "y": rng.integers(0, 2, n), "f_a": rng.normal(0, 1, n), "f_b": rng.normal(0, 1, n)}
    )
    prob = walk_forward_meta_prob(ds, feature_cols=["f_a", "f_b"], n_splits=5)
    ev = evaluate_meta(ds, prob, threshold=0.5)
    assert 0.3 < ev["auc"] < 0.7               # no real edge -> AUC near 0.5
    assert set(ev) >= {"n_events", "rule_hit_rate", "meta_hit_rate", "lift", "auc"}
