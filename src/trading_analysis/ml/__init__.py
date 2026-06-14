"""ML layer. Meta-labeling: filter/size a primary rule's signals with a leakage-safe
LightGBM model (triple-barrier labels + features + PurgedKFold walk-forward)."""

from trading_analysis.ml.meta_labeling import (
    META_DEFAULT_PARAMS,
    build_meta_dataset,
    evaluate_meta,
    walk_forward_meta_prob,
)

__all__ = [
    "META_DEFAULT_PARAMS",
    "build_meta_dataset",
    "evaluate_meta",
    "walk_forward_meta_prob",
]
