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

import warnings

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
        # NOTE: int() truncates the embargo to 0 for small n / small pct (de Prado does the same).
        embargo = int(n * self.pct_embargo)
        starts = self.t1.index                                  # per-sample label start (event time)
        ends = pd.DatetimeIndex(self.t1.values)                 # per-sample label end (t1 = touch time)
        folds = [(fold[0], fold[-1] + 1) for fold in np.array_split(indices, self.n_splits)]

        for lo, hi in folds:
            test_indices = indices[lo:hi]
            test_t0 = self.t1.index[lo]                          # first test event time
            test_t1_max = self.t1.iloc[lo:hi].max()              # latest test label-END *time*
            # (1) exact interval-overlap purge: drop any train label whose [start, t1]
            #     intersects the test label span [test_t0, test_t1_max]. Compared as
            #     timestamps directly — no axis mixing (the prior searchsorted-of-a-t1-value
            #     conflated label-end *time* with event *position* and could under-purge).
            overlap = (starts <= test_t1_max) & (ends >= test_t0)
            # (2) embargo: also drop the `embargo` samples whose EVENT positions immediately
            #     follow the test labels' resolution (serial-correlation guard), anchored on
            #     position via searchsorted of the *end time* into the event index.
            emb_start = int(self.t1.index.searchsorted(test_t1_max, side="right"))
            emb_mask = np.zeros(n, dtype=bool)
            emb_mask[emb_start : emb_start + embargo] = True
            train_mask = ~(np.asarray(overlap) | emb_mask)
            train_mask[lo:hi] = False                           # never put test rows in train
            train_indices = indices[train_mask]
            if train_indices.size == 0:
                warnings.warn(
                    f"PurgedKFold: fold [{lo}:{hi}] purged all train samples "
                    f"(n={n}, n_splits={self.n_splits}, embargo={embargo}); "
                    "reduce n_splits, embargo, or label horizon.",
                    stacklevel=2,
                )
            yield train_indices, test_indices
