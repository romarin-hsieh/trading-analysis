import numpy as np
import pandas as pd
import pytest

from trading_analysis.labeling.cv import PurgedKFold
from trading_analysis.labeling.trend_scanning import trend_scanning_labels
from trading_analysis.labeling.triple_barrier import (
    get_bins,
    triple_barrier_events,
    triple_barrier_labels,
    vertical_barriers,
)
from trading_analysis.labeling.volatility import ewma_vol


def _close(vals) -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=len(vals), freq="B")
    return pd.Series(np.asarray(vals, dtype=float), index=idx)


# ---------- volatility ----------


def test_ewma_vol_positive_and_aligned():
    c = _close(100 * (1.001 ** np.arange(120)) + np.random.default_rng(0).normal(0, 0.5, 120))
    v = ewma_vol(c, span=50)
    assert v.index.equals(c.index)
    assert v.dropna().gt(0).all()


# ---------- triple barrier ----------


def test_triple_barrier_profit_take():
    c = _close([100, 100.5, 101, 102, 103])  # rises >2% well before the vertical
    target = pd.Series(0.02, index=c.index)
    bins = get_bins(triple_barrier_events(c, [c.index[0]], [1, 1], target, num_bars=4), c)
    assert bins["bin"].iloc[0] == 1.0
    assert bins["ret"].iloc[0] > 0


def test_triple_barrier_stop_loss():
    c = _close([100, 99.5, 99, 98, 97])
    target = pd.Series(0.02, index=c.index)
    bins = get_bins(triple_barrier_events(c, [c.index[0]], [1, 1], target, num_bars=4), c)
    assert bins["bin"].iloc[0] == -1.0
    assert bins["ret"].iloc[0] < 0


def test_triple_barrier_vertical_when_barriers_far():
    c = _close([100, 100.1, 100.0, 100.1, 100.05])  # never reaches ±5%
    target = pd.Series(0.05, index=c.index)
    ev = triple_barrier_events(c, [c.index[0]], [1, 1], target, num_bars=4)
    assert ev["t1"].iloc[0] == c.index[4]  # the vertical barrier decided it


def test_triple_barrier_t1_is_a_touch_time_not_horizon():
    # Return path: bar1 +1% (no touch), bar2 +3% (> +2% PT). First touch = bar 2,
    # NOT the vertical barrier (bar 4) — the leakage-prevention property PurgedKFold needs.
    c = _close([100, 101, 103, 104, 105])
    target = pd.Series(0.02, index=c.index)
    ev = triple_barrier_events(c, [c.index[0]], [1, 1], target, num_bars=4)
    assert ev["t1"].iloc[0] == c.index[2]


def test_triple_barrier_labels_convenience_runs():
    rng = np.random.default_rng(1)
    c = _close(100 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, 260))))
    out = triple_barrier_labels(c, pt=2, sl=2, num_bars=10)
    assert set(out.columns) == {"ret", "bin", "t1"}
    assert out["bin"].isin([-1.0, 0.0, 1.0]).all()
    assert (pd.DatetimeIndex(out["t1"]) >= out.index).all()  # t1 never before the event


# ---------- trend scanning ----------


def test_trend_scanning_uptrend_positive_label():
    c = _close(100 * (1.01 ** np.arange(40)))  # clean uptrend
    out = trend_scanning_labels(c, t_events=[c.index[0]], look_forward=20, min_sample=5)
    assert out["bin"].iloc[0] == 1.0
    assert out["t1"].iloc[0] > c.index[0]


def test_trend_scanning_downtrend_negative_label():
    c = _close(100 * (0.99 ** np.arange(40)))
    out = trend_scanning_labels(c, t_events=[c.index[0]], look_forward=20, min_sample=5)
    assert out["bin"].iloc[0] == -1.0


# ---------- purged k-fold ----------


def test_purged_kfold_no_train_test_overlap():
    n = 24
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    X = pd.DataFrame({"f": range(n)}, index=idx)
    # each label spans 3 bars forward
    ends = np.minimum(np.arange(n) + 3, n - 1)
    t1 = pd.Series(idx[ends], index=idx)

    cv = PurgedKFold(n_splits=4, t1=t1, pct_embargo=0.05)
    n_folds = 0
    for train, test in cv.split(X):
        n_folds += 1
        test_start, test_end = idx[test[0]], idx[test[-1]]
        for ti in train:
            lbl_start, lbl_end = idx[ti], t1.iloc[ti]
            overlaps = (lbl_start <= test_end) and (lbl_end >= test_start)
            assert not overlaps, f"train label {ti} overlaps test [{test_start}, {test_end}]"
    assert n_folds == 4
    assert cv.get_n_splits() == 4


def test_purged_kfold_rejects_mismatched_index():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    X = pd.DataFrame({"f": range(10)}, index=idx)
    t1 = pd.Series(idx, index=idx[::-1])  # wrong index
    with pytest.raises(ValueError):
        list(PurgedKFold(n_splits=3, t1=t1).split(X))


# ---------- adversarial-review fixes ----------


def test_vertical_barriers_reject_off_grid_event():
    c = _close([100, 101, 102, 103, 104])
    with pytest.raises(ValueError):
        vertical_barriers(c, [pd.Timestamp("2099-01-01")], 2)


def test_triple_barrier_honors_asymmetric_stop():
    # pt=3 (+6% PT, never hit), sl=1 (-2% SL, hit at bar 1). The old symmetric-forcing
    # bug would have used sl=3 (-6%) and missed it -> vertical -> bin 0.
    c = _close([100, 97.5, 98, 99, 100])
    target = pd.Series(0.02, index=c.index)
    bins = get_bins(triple_barrier_events(c, [c.index[0]], [3, 1], target, num_bars=4), c)
    assert bins["bin"].iloc[0] == -1.0


def test_purged_kfold_embargo_shrinks_train():
    n = 24
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    X = pd.DataFrame({"f": range(n)}, index=idx)
    t1 = pd.Series(idx[np.minimum(np.arange(n) + 3, n - 1)], index=idx)
    train0 = sum(len(tr) for tr, _ in PurgedKFold(4, t1, 0.0).split(X))
    train1 = sum(len(tr) for tr, _ in PurgedKFold(4, t1, 0.20).split(X))
    assert train1 < train0  # embargo removes additional train samples
