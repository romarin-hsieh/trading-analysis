import numpy as np

from trading_analysis.backtest.deflated_sharpe import (
    deflated_sharpe_ratio,
    expected_max_sharpe,
    min_track_record_length,
    probabilistic_sharpe_ratio,
)
from trading_analysis.backtest.pbo import probability_of_backtest_overfitting
from trading_analysis.backtest.spa import reality_check_pvalue, spa_pvalue


def _rets(n, mu, sd=1.0, seed=0):
    return np.random.default_rng(seed).normal(mu, sd, n)


# ---------- deflated / probabilistic Sharpe ----------


def test_psr_increases_with_track_length():
    r = _rets(600, 0.1, seed=0)
    assert probabilistic_sharpe_ratio(r) > probabilistic_sharpe_ratio(r[:60])


def test_expected_max_sharpe_rises_with_trials():
    assert expected_max_sharpe(200, 0.5) > expected_max_sharpe(10, 0.5) > 0.0


def test_dsr_decreases_with_more_trials():
    r = _rets(500, 0.08, seed=1)
    d_few = deflated_sharpe_ratio(r, n_trials=10, trials_sharpe_std=0.1)
    d_many = deflated_sharpe_ratio(r, n_trials=1000, trials_sharpe_std=0.1)
    assert d_few > d_many  # a higher trial count raises the bar -> lower deflated confidence


def test_min_track_record_length_finite_positive():
    n = min_track_record_length(_rets(500, 0.06, seed=2), sr_benchmark=0.0, prob=0.95)
    assert np.isfinite(n) and n > 0


# ---------- PBO ----------


def test_pbo_noise_near_half_on_average():
    # The CSCV combinations are highly correlated, so a single matrix is noisy; average a
    # few. Pure noise -> the IS-winner is an artifact -> PBO near 0.5.
    pbos = [
        probability_of_backtest_overfitting(
            np.random.default_rng(s).normal(0, 1, (240, 10)), n_splits=8
        )["pbo"]
        for s in range(5)
    ]
    assert np.mean(pbos) > 0.35


def test_pbo_genuine_skill_is_low():
    rng = np.random.default_rng(1)
    m = rng.normal(0, 1, (240, 12))
    m[:, 0] += 0.5  # one config has a consistent edge every period
    res = probability_of_backtest_overfitting(m, n_splits=10)
    assert res["n_combinations"] == 252
    assert res["pbo"] < 0.2


# ---------- SPA / Reality Check ----------


def test_spa_rc_no_skill_high_pvalue():
    d = np.random.default_rng(0).normal(0, 1, (200, 10))
    assert reality_check_pvalue(d, n_boot=400) > 0.1
    assert spa_pvalue(d, n_boot=400) > 0.1


def test_spa_rc_skill_low_pvalue():
    rng = np.random.default_rng(1)
    d = rng.normal(0, 1, (200, 10))
    d[:, 0] += 0.4  # model 0 genuinely beats the benchmark
    assert reality_check_pvalue(d, n_boot=400) < 0.1
    assert spa_pvalue(d, n_boot=400) < 0.1
