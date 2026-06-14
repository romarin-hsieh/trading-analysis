import numpy as np
import pandas as pd

from trading_analysis.factors.attribution import factor_alpha


def _factors(n=300, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-03", periods=n, freq="B")
    return pd.DataFrame(
        {
            "Mkt-RF": rng.normal(0.0003, 0.01, n),
            "SMB": rng.normal(0.0, 0.006, n),
            "HML": rng.normal(0.0, 0.006, n),
            "UMD": rng.normal(0.0, 0.007, n),
        },
        index=idx,
    )


def test_pure_factor_exposure_has_no_alpha():
    f = _factors(seed=1)
    rng = np.random.default_rng(2)
    strat = 1.2 * f["Mkt-RF"] + 0.5 * f["HML"] + rng.normal(0, 0.002, len(f))  # zero true alpha
    res = factor_alpha(strat, f)
    assert abs(res["betas"]["Mkt-RF"] - 1.2) < 0.12
    assert abs(res["betas"]["HML"] - 0.5) < 0.15
    assert abs(res["alpha"]) < 5e-4
    assert abs(res["alpha_tstat"]) < 2.5            # alpha not significant — it's all beta
    assert res["n"] == len(f)


def test_genuine_alpha_is_significant():
    f = _factors(seed=3)
    rng = np.random.default_rng(4)
    strat = 0.002 + 1.0 * f["Mkt-RF"] + rng.normal(0, 0.002, len(f))  # +20bps/day real alpha
    res = factor_alpha(strat, f)
    assert res["alpha"] > 0.0015
    assert res["alpha_tstat"] > 3.0                 # clearly significant skill beyond beta
    assert abs(res["betas"]["Mkt-RF"] - 1.0) < 0.12


def test_alpha_handles_misaligned_index():
    f = _factors(seed=5)
    strat = (0.5 * f["Mkt-RF"] + np.random.default_rng(6).normal(0, 0.003, len(f))).iloc[20:]
    res = factor_alpha(strat, f)  # shorter series than factors -> inner-join on dates
    assert res["n"] == len(f) - 20
    assert "Mkt-RF" in res["betas"]
