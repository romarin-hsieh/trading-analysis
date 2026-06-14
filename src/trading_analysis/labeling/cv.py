"""Purged + embargoed K-Fold cross-validation (de Prado AFML Ch.7, Snippet 7.3).

Financial labels span an interval [event_time, t1]. Ordinary K-Fold leaks because a
train label can overlap the test window. PurgedKFold removes (purges) train samples
whose label interval overlaps any test label interval, and additionally embargoes a
fraction of samples immediately after the test window (to kill serial-correlation
leakage across the boundary).

Standalone (no sklearn inheritance) but sklearn-compatible: exposes `split()` and
`get_n_splits()`, so it drops into `cross_val_score`/`GridSearchCV`.
Reimplemented from the published algorithm; not copied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class PurgedKFold:
    def __init__(self, n_splits: int = 5, t1: pd.Series | None = None, pct_embargo: float = 0.0):
        if not isinstance(t1, pd.Series):
            raise ValueError("t1 must be a pd.Series of label end-times indexed by event time")
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        self.n_splits = n_splits
        self.t1 = t1
        self.pct_embargo = pct_embargo

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits

    def split(self, X: pd.DataFrame, y=None, groups=None):
        if not X.index.equals(self.t1.index):
            raise ValueError("X and t1 must share the same index, in the same order")
        n = X.shape[0]
        indices = np.arange(n)
        embargo = int(n * self.pct_embargo)
        starts = self.t1.index                                  # per-sample label start
        ends = pd.DatetimeIndex(self.t1.values)                 # per-sample label end (t1)
        test_ranges = [(fold[0], fold[-1] + 1) for fold in np.array_split(indices, self.n_splits)]

        for lo, hi in test_ranges:
            test_indices = indices[lo:hi]
            test_t0 = self.t1.index[lo]                          # first test event time
            # extend the right edge of the purge window by `embargo` bars past the
            # latest test label-end (kills serial-correlation leakage across the boundary)
            max_t1_idx = self.t1.index.searchsorted(self.t1.iloc[test_indices].max())
            purge_end = self.t1.index[min(max_t1_idx + embargo, n - 1)]
            # purge: drop any train sample whose label interval [start, t1] overlaps
            # the (embargoed) test window [test_t0, purge_end] — touching counts as overlap.
            overlap = (starts <= purge_end) & (ends >= test_t0)
            train_mask = ~np.asarray(overlap)
            train_mask[test_indices] = False
            yield indices[train_mask], test_indices
