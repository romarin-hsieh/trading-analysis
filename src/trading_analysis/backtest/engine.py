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


def run_backtest(
    close: pd.DataFrame,
    direction: pd.DataFrame,
    cfg: BacktestConfig,
    benchmark_close: pd.Series | None = None,
    dollar_volume: pd.DataFrame | None = None,
    book_dollars: float | None = None,
) -> BacktestResult:
    """When `dollar_volume` (wide, same grid as close) is given, per-cell slippage is
    the size-dependent model from backtest.costs (half-spread + sqrt-impact on the
    approximate participation target_percent*book / 21d ADV) instead of the flat
    cfg.slippage_bps. Trade size uses a STATIC book approximation (book_dollars,
    default cfg.cash) — vectorbt's slippage input cannot see order-time equity, so
    this is a conservative fixed-book impact, not a compounding one (documented
    limitation; the flat floor still applies wherever ADV is missing)."""
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

    fees = cfg.fees_bps / 10_000.0
    slippage = cfg.slippage_bps / 10_000.0
    cost_stats: dict[str, float] = {}
    if dollar_volume is not None:
        from trading_analysis.backtest.costs import size_dependent_cost_bps

        dv = dollar_volume.reindex(index=common_ts, columns=common_syms).astype(float)
        adv = dv.rolling(21, min_periods=10).mean().shift(1)      # causal 21d ADV
        trade = (book_dollars if book_dollars is not None else cfg.cash) \
            * getattr(cfg, "target_percent", 0.10)
        bps = size_dependent_cost_bps(trade, adv.to_numpy())
        panel = pd.DataFrame(bps, index=common_ts, columns=common_syms)
        # flat cfg.slippage_bps stays as the FLOOR and the missing-ADV fallback;
        # cap at 500bps so a dead name cannot inject infs into the simulation
        panel = panel.clip(lower=cfg.slippage_bps, upper=500.0) \
            .fillna(float(cfg.slippage_bps))
        slippage = (panel / 10_000.0).to_numpy()
        traded_cells = panel.to_numpy()[direction_.to_numpy() > 0]
        if traded_cells.size:
            cost_stats = {
                "cost_model_median_bps": float(pd.Series(traded_cells).median()),
                "cost_model_p90_bps": float(pd.Series(traded_cells).quantile(0.90)),
            }
        log.info(
            f"size-dependent costs ON: trade≈${trade:,.0f}, held-cell slippage "
            f"median {cost_stats.get('cost_model_median_bps', float('nan')):.1f}bps / "
            f"p90 {cost_stats.get('cost_model_p90_bps', float('nan')):.1f}bps"
        )

    # Equal-weight TARGET-PERCENT sizing via from_orders: each currently-signaled long targets
    # `target_percent` of CURRENT equity (equity-scaled — not a fixed dollar tied to init_cash,
    # which would de-gross as equity compounds). With an upstream top-N cap the per-bar targets
    # sum to <= 1.0, so under cash_sharing every target is met exactly and the result is
    # ORDER-INDEPENDENT (no alphabetical column-order rationing). call_seq="auto" runs sells
    # before buys within a bar so freed cash funds new entries.
    target_pct = getattr(cfg, "target_percent", 0.10)
    target_weights = (direction_ > 0).astype(float) * target_pct
    n_long_bars = int((direction_ > 0).any(axis=1).sum())
    log.info(
        f"backtest: {close_.shape[0]} bars x {close_.shape[1]} symbols, "
        f"{n_long_bars} bars with >=1 long, freq={cfg.freq}"
    )

    pf = vbt.Portfolio.from_orders(
        close=close_,
        size=target_weights,
        size_type="targetpercent",
        init_cash=cfg.cash,
        fees=fees,
        slippage=slippage,
        freq=cfg.freq,
        cash_sharing=True,
        group_by=True,
        call_seq="auto",
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
    metrics.update(cost_stats)
    trades = pf.trades.records_readable if hasattr(pf.trades, "records_readable") else pd.DataFrame()
    # per-TRADE win rate (distinct from daily_hit_rate, which is a per-day equity-return stat)
    if len(trades) and "Return" in trades.columns:
        metrics["trade_win_rate"] = float((trades["Return"] > 0).mean())
        metrics["n_trades"] = len(trades)

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
        "daily_hit_rate": hit_rate(returns),  # per-DAY win rate (NOT per-trade — see trade_win_rate)
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0) if len(equity) else 0.0,
    }
    if benchmark_equity is not None and len(benchmark_equity) > 0:
        bench_returns = benchmark_equity.pct_change().fillna(0.0)
        out["information_ratio"] = information_ratio(returns, bench_returns)
        out["benchmark_total_return"] = float(
            benchmark_equity.iloc[-1] / benchmark_equity.iloc[0] - 1.0
        )
    return out
