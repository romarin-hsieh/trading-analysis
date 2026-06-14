"""Meta-labeling (de Prado AFML Ch.3): a LightGBM model that decides whether to ACT on a
primary rule's signal — and how big — but never the direction.

The primary rule (e.g. minervini_trend) supplies the SIDE (long/flat). For each rule-fire
we form a triple-barrier meta-label (1 if the long would have hit its profit barrier before
its stop/time barrier, else 0), attach the causal feature panel, and learn P(profit).
Out-of-sample probabilities come from a PurgedKFold walk-forward (no leakage); predict_proba
is then a FILTER (act if p > threshold) and a SIZER (size ~ p).

Cheap by design: LightGBM on daily-bar tabular data trains in seconds on CPU and infers at
$0. Validate with PurgedKFold + Deflated Sharpe (rigor scorecard #5).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.features.build import FEATURE_COLUMNS, build_features
from trading_analysis.labeling.cv import PurgedKFold
from trading_analysis.labeling.triple_barrier import get_bins, triple_barrier_events
from trading_analysis.labeling.volatility import ewma_vol

META_DEFAULT_PARAMS = {
    "n_estimators": 200,
    "num_leaves": 15,
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_child_samples": 10,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 0,
    "n_jobs": 1,
    "verbosity": -1,
}


def build_meta_dataset(
    ohlcv: pd.DataFrame,
    direction_pivot: pd.DataFrame,
    feature_panel: pd.DataFrame | None = None,
    pt: float = 1.0,
    sl: float = 1.0,
    num_bars: int = 20,
    vol_span: int = 50,
) -> pd.DataFrame:
    """Pool per-symbol meta-labeled events into one dataset sorted by event time.

    direction_pivot: [ts x symbol], 1 where the primary rule is long (the side).
    Returns long-form [symbol, t_event, t1, y, ret, *FEATURE_COLUMNS], sorted by t_event.
    """
    if feature_panel is None:
        feature_panel = build_features(ohlcv)
    rows = []
    for symbol, sub in ohlcv.sort_values(["symbol", "ts"]).groupby("symbol"):
        if symbol not in direction_pivot.columns:
            continue
        sub = sub.sort_values("ts")
        close = pd.Series(sub["close"].to_numpy(), index=pd.DatetimeIndex(sub["ts"]))
        side_col = direction_pivot[symbol].reindex(close.index).fillna(0)
        t_events = close.index[side_col.to_numpy() > 0]
        if len(t_events) == 0:
            continue
        target = ewma_vol(close, span=vol_span)
        side = pd.Series(1.0, index=t_events)
        events = triple_barrier_events(close, t_events, [pt, sl], target, num_bars=num_bars, side=side)
        bins = get_bins(events, close)  # columns: ret, bin in {0,1}, t1
        if bins.empty:
            continue
        feats = feature_panel[feature_panel["symbol"] == symbol].set_index("ts")[FEATURE_COLUMNS]
        feats.index = pd.DatetimeIndex(feats.index)
        joined = bins.join(feats, how="inner").dropna(subset=[*FEATURE_COLUMNS, "bin", "t1"])
        if joined.empty:
            continue
        out = joined[["t1", "bin", "ret", *FEATURE_COLUMNS]].rename(columns={"bin": "y"})
        out.insert(0, "t_event", out.index)
        out.insert(0, "symbol", symbol)
        rows.append(out.reset_index(drop=True))
    if not rows:
        return pd.DataFrame(columns=["symbol", "t_event", "t1", "y", "ret", *FEATURE_COLUMNS])
    dataset = pd.concat(rows, ignore_index=True)
    dataset["y"] = dataset["y"].astype(int)
    return dataset.sort_values("t_event").reset_index(drop=True)


def walk_forward_meta_prob(
    dataset: pd.DataFrame,
    feature_cols: list[str] | None = None,
    n_splits: int = 5,
    pct_embargo: float = 0.02,
    params: dict | None = None,
) -> pd.Series:
    """Out-of-sample P(profit) per event via PurgedKFold walk-forward LightGBM.

    Returns a Series (positional, aligned to `dataset` after sort) with the OOS prob from
    the fold where each row was in the test set (NaN if its fold could not train).
    """
    from lightgbm import LGBMClassifier

    if feature_cols is None:
        feature_cols = FEATURE_COLUMNS
    params = {**META_DEFAULT_PARAMS, **(params or {})}
    ds = dataset.sort_values("t_event").reset_index(drop=True)
    idx = pd.DatetimeIndex(ds["t_event"].to_numpy())
    X = ds[feature_cols].set_axis(idx)
    y = ds["y"].to_numpy()
    t1 = pd.Series(pd.DatetimeIndex(ds["t1"].to_numpy()), index=idx)

    oos = np.full(len(ds), np.nan)
    for train_idx, test_idx in PurgedKFold(n_splits=n_splits, t1=t1, pct_embargo=pct_embargo).split(X):
        if len(train_idx) == 0 or len(np.unique(y[train_idx])) < 2:
            continue  # cannot fit without both classes present in train
        model = LGBMClassifier(**params)
        model.fit(X.iloc[train_idx], y[train_idx])
        oos[test_idx] = model.predict_proba(X.iloc[test_idx])[:, 1]
    return pd.Series(oos, index=ds.index, name="meta_prob")


def evaluate_meta(dataset: pd.DataFrame, oos_prob: pd.Series, threshold: float = 0.5) -> dict:
    """Rule-alone vs rule-filtered-by-meta-model, out-of-sample."""
    y = dataset["y"].to_numpy()
    prob = oos_prob.to_numpy()
    valid = ~np.isnan(prob)
    y_v, prob_v = y[valid], prob[valid]
    take = prob_v > threshold
    rule_hit = float(np.mean(y_v)) if len(y_v) else np.nan
    meta_hit = float(np.mean(y_v[take])) if take.any() else np.nan
    auc = np.nan
    if len(np.unique(y_v)) == 2:
        from sklearn.metrics import roc_auc_score

        auc = float(roc_auc_score(y_v, prob_v))
    lift = (meta_hit - rule_hit) if (meta_hit == meta_hit and rule_hit == rule_hit) else np.nan
    return {
        "n_events": len(y_v),
        "rule_hit_rate": rule_hit,
        "meta_hit_rate": meta_hit,
        "meta_coverage": float(np.mean(take)) if len(take) else np.nan,
        "lift": lift,
        "auc": auc,
        "threshold": threshold,
    }
