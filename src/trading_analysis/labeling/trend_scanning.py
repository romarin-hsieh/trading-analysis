"""Trend-scanning labels (de Prado AFML §17 / Snippet 17.4).

For each event, scan forward windows of length `min_sample..look_forward`, fit a
linear trend (OLS price ~ time), and pick the window whose slope is most
statistically significant (max |t-value|). The label is the sign of that t-value;
the t-value itself doubles as a sample weight, and the window end is the label end
time `t1` (feed it to PurgedKFold like triple-barrier `t1`).

Reimplemented from the published algorithm; not copied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _tval_slope(y: np.ndarray) -> float:
    """t-statistic of the slope coefficient from OLS of y on [1, t]."""
    n = len(y)
    if n < 3:
        return 0.0
    x = np.column_stack([np.ones(n), np.arange(n, dtype=float)])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    dof = n - 2
    s2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.inv(x.T @ x)
    se_slope = float(np.sqrt(s2 * xtx_inv[1, 1]))
    if se_slope == 0.0:
        return 0.0
    return float(beta[1] / se_slope)


def trend_scanning_labels(
    close: pd.Series,
    t_events=None,
    look_forward: int = 20,
    min_sample: int = 5,
) -> pd.DataFrame:
    """Return columns: t1, t_value, bin (indexed by event time)."""
    idx = close.index if t_events is None else pd.DatetimeIndex(t_events)
    vals = close.to_numpy(dtype=float)
    n = len(close)
    rows = []
    for t in idx:
        loc = close.index.get_loc(t)
        best_t1 = None
        best_tv = 0.0
        for length in range(min_sample, look_forward + 1):
            if loc + length > n:
                break
            tv = _tval_slope(vals[loc : loc + length])
            if abs(tv) > abs(best_tv):
                best_tv = tv
                best_t1 = close.index[loc + length - 1]
        if best_t1 is not None:
            rows.append((t, best_t1, best_tv, float(np.sign(best_tv))))
    out = pd.DataFrame(rows, columns=["t_event", "t1", "t_value", "bin"])
    return out.set_index("t_event")
