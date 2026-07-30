import numpy as np
import pandas as pd

from trading_analysis.backtest.costs import (
    amihud_illiquidity,
    expected_cost_drag_bps,
    implementation_shortfall,
    kyle_lambda,
    size_dependent_cost_bps,
)


def test_amihud_higher_when_volume_lower():
    n = 60
    r = np.random.default_rng(0).normal(0, 0.01, n)
    a_high = amihud_illiquidity(r, pd.Series(np.full(n, 1e8))).iloc[-1]
    a_low = amihud_illiquidity(r, pd.Series(np.full(n, 1e6))).iloc[-1]
    assert a_low > a_high > 0


def test_kyle_lambda_proxy_monotone():
    assert kyle_lambda(0.02, 1e6) > kyle_lambda(0.02, 1e8)  # less volume -> more impact


def test_size_cost_monotone_and_spread_floor():
    small = float(size_dependent_cost_bps(1e4, 1e8))   # tiny participation
    big = float(size_dependent_cost_bps(1e7, 1e8))     # 10% of ADV
    assert big > small
    assert abs(float(size_dependent_cost_bps(1.0, 1e8)) - 2.5) < 0.05  # ~half-spread as trade->0
    # sqrt-law: 4x the trade is 2x the impact component (above the spread floor)
    c1 = float(size_dependent_cost_bps(1e6, 1e8, half_spread_bps=0.0))
    c4 = float(size_dependent_cost_bps(4e6, 1e8, half_spread_bps=0.0))
    assert abs(c4 / c1 - 2.0) < 1e-6


def test_implementation_shortfall_sign():
    assert implementation_shortfall(100.0, 101.0, side=1) > 0   # bought above arrival = cost
    assert implementation_shortfall(100.0, 99.0, side=1) < 0    # bought cheaper = gain
    assert implementation_shortfall(100.0, 99.0, side=-1) > 0   # sold below arrival = cost


def test_expected_cost_drag_scales_with_turnover():
    d1 = expected_cost_drag_bps(50, 1e6, 1e8)
    d2 = expected_cost_drag_bps(100, 1e6, 1e8)
    assert d2 > d1 > 0
    assert abs(d2 / d1 - 2.0) < 1e-9


# ---- engine wiring (docs/27 engineering debt: size-dependent slippage panel) ----

def _toy_backtest(dollar_volume=None):
    from trading_analysis.backtest.engine import run_backtest
    from trading_analysis.config import BacktestConfig

    idx = pd.bdate_range("2022-01-03", periods=120)
    rng = np.random.default_rng(7)
    close = pd.DataFrame(
        100 * np.exp(np.cumsum(rng.normal(0, 0.01, (120, 2)), axis=0)),
        index=idx, columns=["LIQ", "THIN"],
    )
    # alternate 10-day holds to force turnover
    direction = pd.DataFrame(0, index=idx, columns=close.columns)
    on = (np.arange(120) // 10) % 2 == 0
    direction.loc[on, :] = 1
    cfg = BacktestConfig(benchmark=None)
    return run_backtest(close, direction, cfg, dollar_volume=dollar_volume)


def test_engine_size_dependent_costs_bite_and_report():
    idx = pd.bdate_range("2022-01-03", periods=120)
    dv = pd.DataFrame({"LIQ": 1e9, "THIN": 1e4}, index=idx)  # THIN: trade 10k = 100% ADV
    flat = _toy_backtest(dollar_volume=None)
    sized = _toy_backtest(dollar_volume=dv)
    assert "cost_model_median_bps" in sized.metrics
    assert sized.metrics["cost_model_median_bps"] >= 5.0          # flat floor respected
    assert sized.metrics["cost_model_p90_bps"] > 6.0              # THIN cells above floor
    assert sized.equity.iloc[-1] < flat.equity.iloc[-1]           # impact costs bite


def test_engine_missing_adv_falls_back_to_flat():
    idx = pd.bdate_range("2022-01-03", periods=120)
    dv_nan = pd.DataFrame(np.nan, index=idx, columns=["LIQ", "THIN"])
    flat = _toy_backtest(dollar_volume=None)
    fallback = _toy_backtest(dollar_volume=dv_nan)
    assert abs(fallback.equity.iloc[-1] / flat.equity.iloc[-1] - 1) < 1e-9
