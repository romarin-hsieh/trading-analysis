"""Triple-barrier labeling (de Prado, Advances in Financial ML, Ch.3).

Each event (entry time) gets three barriers: an upper (profit-take) and lower
(stop-loss) horizontal barrier scaled by a per-event volatility `target`, plus a
vertical (time) barrier `num_bars` later. The label is decided by which barrier is
touched FIRST:
  +1  upper touched first        (or vertical hit with positive return)
  -1  lower touched first        (or vertical hit with negative return)
   0  (meta-labeling only) when a `side` is supplied and the realized return <= 0

This is the leakage-aware alternative to fixed-horizon labels: the label's end time
`t1` is the actual barrier-touch time, which `labeling.cv.PurgedKFold` then uses to
purge overlapping train/test samples.

Reimplemented from the published algorithm (snippets 3.2/3.3/3.5/3.7); not copied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.labeling.volatility import ewma_vol


def vertical_barriers(close: pd.Series, t_events, num_bars: int) -> pd.Series:
    """Vertical (time) barrier = `num_bars` bars after each event (NaT if it runs off the end)."""
    t_events = pd.DatetimeIndex(t_events)
    locs = close.index.searchsorted(t_events)
    end = locs + num_bars
    t1 = pd.Series(pd.NaT, index=t_events, dtype="datetime64[ns]")
    valid = end < close.shape[0]
    if valid.any():
        t1.iloc[np.where(valid)[0]] = close.index[end[valid]]
    return t1


def _first_touch(close: pd.Series, events: pd.DataFrame, pt_sl) -> pd.DataFrame:
    """First time the path crosses the profit-take / stop-loss barriers, per event."""
    out = events[["t1"]].copy()
    pt = pt_sl[0] * events["trgt"] if pt_sl[0] > 0 else pd.Series(np.inf, index=events.index)
    sl = -pt_sl[1] * events["trgt"] if pt_sl[1] > 0 else pd.Series(-np.inf, index=events.index)

    for loc, t1 in events["t1"].fillna(close.index[-1]).items():
        path = close.loc[loc:t1]
        rets = (path / close.loc[loc] - 1.0) * events.at[loc, "side"]
        out.at[loc, "sl"] = rets[rets < sl[loc]].index.min()  # NaT if never breached
        out.at[loc, "pt"] = rets[rets > pt[loc]].index.min()
    return out


def triple_barrier_events(
    close: pd.Series,
    t_events,
    pt_sl,
    target: pd.Series,
    min_ret: float = 0.0,
    num_bars: int | None = None,
    side: pd.Series | None = None,
) -> pd.DataFrame:
    """Assemble events with their first-touch end time `t1`.

    pt_sl = [pt_mult, sl_mult]; barriers = +/-mult x target. `num_bars` adds a vertical
    barrier. `side` (optional, +1/-1) switches to meta-labeling (single barrier width).
    """
    trgt = target.reindex(pd.DatetimeIndex(t_events)).dropna()
    trgt = trgt[trgt > min_ret]

    vb = vertical_barriers(close, trgt.index, num_bars) if num_bars else pd.Series(
        pd.NaT, index=trgt.index, dtype="datetime64[ns]"
    )

    if side is None:
        side_ = pd.Series(1.0, index=trgt.index)
        pt_sl_ = [pt_sl[0], pt_sl[0]]
    else:
        side_ = side.reindex(trgt.index)
        pt_sl_ = [pt_sl[0], pt_sl[1]]

    events = pd.concat({"t1": vb, "trgt": trgt, "side": side_}, axis=1).dropna(subset=["trgt"])
    touches = _first_touch(close, events, pt_sl_)
    events["t1"] = touches[["t1", "sl", "pt"]].min(axis=1)  # earliest of vertical/SL/PT (skips NaT)
    if side is None:
        events = events.drop(columns=["side"])
    return events


def get_bins(events: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
    """Realized return over [event, t1] and the {-1,0,+1} label."""
    events_ = events.dropna(subset=["t1"])
    end = pd.DatetimeIndex(events_["t1"].values)
    px_end = close.reindex(end).values
    px_start = close.reindex(events_.index).values
    out = pd.DataFrame(index=events_.index)
    out["ret"] = px_end / px_start - 1.0
    if "side" in events_:
        out["ret"] = out["ret"] * events_["side"].values
    out["bin"] = np.sign(out["ret"])
    if "side" in events_:
        out.loc[out["ret"] <= 0, "bin"] = 0  # meta-labeling: don't act on a losing side
    out["t1"] = events_["t1"].values
    return out


def triple_barrier_labels(
    close: pd.Series,
    t_events=None,
    pt: float = 2.0,
    sl: float = 2.0,
    target: pd.Series | None = None,
    num_bars: int = 20,
    min_ret: float = 0.0,
) -> pd.DataFrame:
    """Convenience: symmetric-barrier events + bins in one call.

    `t_events` defaults to every bar with a defined volatility target.
    Returns columns: ret, bin, t1 (indexed by event time).
    """
    if target is None:
        target = ewma_vol(close)
    if t_events is None:
        t_events = target.dropna().index
    events = triple_barrier_events(
        close, t_events, [pt, sl], target, min_ret=min_ret, num_bars=num_bars
    )
    return get_bins(events, close)
