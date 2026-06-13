"""Performance metrics — keep these dependency-free."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def cagr(equity: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    if equity is None or len(equity) < 2:
        return 0.0
    start, end = float(equity.iloc[0]), float(equity.iloc[-1])
    if start <= 0:
        return 0.0
    years = len(equity) / periods_per_year
    if years <= 0:
        return 0.0
    return float((end / start) ** (1 / years) - 1)


def sharpe(returns: pd.Series, periods_per_year: int = TRADING_DAYS, rf: float = 0.0) -> float:
    if returns is None or returns.std() == 0 or len(returns) < 2:
        return 0.0
    excess = returns - rf / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / excess.std(ddof=1))


def max_drawdown(equity: pd.Series) -> float:
    if equity is None or len(equity) == 0:
        return 0.0
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def hit_rate(returns: pd.Series) -> float:
    if returns is None or len(returns) == 0:
        return 0.0
    nonzero = returns[returns != 0]
    if nonzero.empty:
        return 0.0
    return float((nonzero > 0).mean())


def information_ratio(
    returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = TRADING_DAYS
) -> float:
    diff = (returns - benchmark_returns).dropna()
    if diff.empty or diff.std() == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * diff.mean() / diff.std(ddof=1))
