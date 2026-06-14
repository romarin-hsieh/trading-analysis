"""vectorbt-based backtest engine.

Inputs:
    - close: wide DataFrame [ts x symbol] of close prices
    - direction_pivot: same shape, values in {-1, 0, +1}
    - config: BacktestConfig (fees, slippage, cash, freq)

Output: BacktestResult with portfolio object, equity curve, and key metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from trading_analysis.config import BacktestConfig
from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)


@dataclass
class BacktestResult:
    equity: pd.Series                 # portfolio value over time
    returns: pd.Series                # daily returns
    metrics: dict[str, float]
    trades: pd.DataFrame
    weights: pd.DataFrame             # realized target weights
    benchmark_equity: pd.Series | None = None
    raw: Any = field(default=None, repr=False)  # vectorbt portfolio object

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics,
            "n_trades": len(self.trades),
            "equity_start": float(self.equity.iloc[0]) if len(self.equity) else None,
            "equity_end": float(self.equity.iloc[-1]) if len(self.equity) else None,
        }


def _direction_to_entries_exits(
    direction: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Translate -1/0/+1 holdings into vectorbt-style entries/exits (long-only MVP).

    Long signal becomes an entry the first bar it appears, exit when it returns to 0/-1.
    Shorts ignored at MVP; treat as flat.
    """
    long = (direction > 0).astype(int)
    prev = long.shift(1, fill_value=0)
    entries = (long == 1) & (prev == 0)
    exits = (long == 0) & (prev == 1)
    return entries, exits


def run_backtest(
    close: pd.DataFrame,
    direction: pd.DataFrame,
    cfg: BacktestConfig,
    benchmark_close: pd.Series | None = None,
) -> BacktestResult:
    import vectorbt as vbt

    if close.empty:
        raise ValueError("close prices frame is empty")
    if direction.empty:
        raise ValueError("direction pivot is empty")

    # Align frames on common ts x symbol grid.
    common_ts = close.index.intersection(direction.index)
    common_syms = close.columns.intersection(direction.columns)
    if len(common_ts) == 0 or len(common_syms) == 0:
        raise ValueError("no overlap between price frame and direction pivot")
    close_ = close.loc[common_ts, common_syms].astype(float).ffill()
    direction_ = direction.loc[common_ts, common_syms].fillna(0).astype(int)

    entries, exits = _direction_to_entries_exits(direction_)
    fees = cfg.fees_bps / 10_000.0
    slippage = cfg.slippage_bps / 10_000.0

    log.info(
        f"backtest: {close_.shape[0]} bars x {close_.shape[1]} symbols, "
        f"{int(entries.sum().sum())} entries, freq={cfg.freq}"
    )

    # Per-name fixed-fraction sizing — equal share count split across initial cash.
    size = cfg.cash / max(close_.shape[1], 1) / close_.iloc[0].replace(0, np.nan)
    size_value = float(np.nan_to_num(size.median(), nan=0.0))
    size_value = max(size_value, 1.0)

    pf = vbt.Portfolio.from_signals(
        close=close_,
        entries=entries,
        exits=exits,
        size=size_value,
        size_type="amount",
        init_cash=cfg.cash,
        fees=fees,
        slippage=slippage,
        freq=cfg.freq,
        cash_sharing=True,
        group_by=True,
    )

    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.sum(axis=1)
    equity.name = "equity"
    returns = equity.pct_change().fillna(0.0)
    returns.name = "ret"

    benchmark_equity = None
    if benchmark_close is not None and not benchmark_close.empty:
        b = benchmark_close.reindex(equity.index).ffill()
        if not b.empty and b.iloc[0] > 0:
            benchmark_equity = (b / b.iloc[0]) * cfg.cash
            benchmark_equity.name = "benchmark_equity"

    metrics = compute_metrics(equity, returns, benchmark_equity)
    trades = pf.trades.records_readable if hasattr(pf.trades, "records_readable") else pd.DataFrame()

    return BacktestResult(
        equity=equity,
        returns=returns,
        metrics=metrics,
        trades=trades,
        weights=direction_.astype(float),
        benchmark_equity=benchmark_equity,
        raw=pf,
    )


def compute_metrics(
    equity: pd.Series,
    returns: pd.Series,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, float]:
    from trading_analysis.backtest.metrics import (
        cagr,
        hit_rate,
        information_ratio,
        max_drawdown,
        sharpe,
    )

    out = {
        "cagr": cagr(equity),
        "sharpe": sharpe(returns),
        "max_drawdown": max_drawdown(equity),
        "hit_rate": hit_rate(returns),
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0) if len(equity) else 0.0,
    }
    if benchmark_equity is not None and len(benchmark_equity) > 0:
        bench_returns = benchmark_equity.pct_change().fillna(0.0)
        out["information_ratio"] = information_ratio(returns, bench_returns)
        out["benchmark_total_return"] = float(
            benchmark_equity.iloc[-1] / benchmark_equity.iloc[0] - 1.0
        )
    return out
