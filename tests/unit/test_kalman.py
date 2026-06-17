import numpy as np
import pandas as pd

from trading_analysis.models.kalman import dynamic_regression, local_linear_trend


def test_local_linear_trend_smooths_and_recovers_slope():
    rng = np.random.default_rng(0)
    n, slope = 300, 0.05
    truth = np.arange(n) * slope
    y = truth + rng.normal(0, 1.0, n)
    lvl, slp = local_linear_trend(y, q_level=1e-2, q_slope=1e-4, r=1.0)
    # filtered level is closer to the latent truth than the raw noisy series
    assert np.nanmean((lvl[50:] - truth[50:]) ** 2) < np.nanmean((y[50:] - truth[50:]) ** 2)
    # the recovered slope converges to the true slope after burn-in
    assert abs(np.nanmean(slp[150:]) - slope) < 0.03


def test_dynamic_regression_recovers_static_beta():
    rng = np.random.default_rng(1)
    n = 400
    x = rng.normal(0, 1, n)
    y = 2.0 * x + rng.normal(0, 0.5, n)
    b = dynamic_regression(y, pd.DataFrame({"x": x}), q=1e-3, r=0.25)
    assert abs(b["x"].iloc[-50:].mean() - 2.0) < 0.2


def test_dynamic_regression_tracks_changing_beta():
    rng = np.random.default_rng(2)
    n = 600
    x = rng.normal(0, 1, n)
    beta_true = np.where(np.arange(n) < 300, 1.0, 3.0)
    y = beta_true * x + rng.normal(0, 0.3, n)
    b = dynamic_regression(y, pd.DataFrame({"x": x}), q=2e-2, r=0.1)["x"].to_numpy()
    assert abs(b[270] - 1.0) < 0.5      # tracked the first regime
    assert abs(b[-1] - 3.0) < 0.6       # adapted to the second
