"""Feature importance for pruning (MDI). Apply within CV folds (de Prado AFML Ch.8).

Mean-Decrease-Impurity from a RandomForest, with per-tree std so you can see how
concentrated the importance is. MDI is in-sample and biased toward high-cardinality
features; pair with out-of-sample MDA when it matters. Like stationarity selection,
this is a modeling-time tool, not part of the causal feature build.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def mdi_importance(
    X: pd.DataFrame,
    y,
    n_estimators: int = 200,
    random_state: int = 0,
    max_features: str | float = "sqrt",
    **kwargs,
) -> pd.DataFrame:
    """Return a DataFrame [mdi_mean, mdi_std] indexed by feature, sorted descending."""
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        max_features=max_features,
        **kwargs,
    )
    clf.fit(X, y)
    per_tree = np.array([t.feature_importances_ for t in clf.estimators_])
    out = pd.DataFrame(
        {"mdi_mean": clf.feature_importances_, "mdi_std": per_tree.std(axis=0)},
        index=X.columns,
    )
    return out.sort_values("mdi_mean", ascending=False)
