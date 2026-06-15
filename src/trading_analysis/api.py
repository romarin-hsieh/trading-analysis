"""Public API. UI and CLI must only import from this module.

Internals (data/, models/, strategy/, backtest/, execution/) are implementation
details. Treat anything outside this module as private and subject to change.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from trading_analysis.backtest.engine import BacktestResult, run_backtest
from trading_analysis.backtest.report import write_markdown_report
from trading_analysis.config import AppConfig, UniverseConfig, load_config
from trading_analysis.data.connectors.yahoo import YahooConnector
from trading_analysis.data.store import DuckStore
from trading_analysis.models.kronos import KronosForecaster
from trading_analysis.models.naive import NaiveDriftForecaster
from trading_analysis.observability.logging import get_logger
from trading_analysis.strategy.rules.kronos_trend import KronosTrendRule
from trading_analysis.strategy.rules.minervini_trend import MinerviniTrendRule
from trading_analysis.strategy.rules.sma_crossover import SMACrossoverRule

log = get_logger(__name__)

_RULES = {
    "kronos_trend": KronosTrendRule,
    "minervini_trend": MinerviniTrendRule,
    "sma_crossover": SMACrossoverRule,
}


# ---------- universe / discovery ----------


def list_available_strategies() -> list[str]:
    return list(_RULES.keys())


def list_universe_symbols(cfg: AppConfig | str | Path | None = None) -> list[str]:
    cfg = _resolve_config(cfg)
    return list(cfg.universe.symbols)


# ---------- ingestion ----------


def ingest_universe(cfg: AppConfig | str | Path | None = None) -> dict[str, int]:
    """Pull bars for all universe symbols from the configured source into DuckStore.

    Returns a per-symbol row count.
    """
    cfg = _resolve_config(cfg)
    store = DuckStore(cfg.data.cache_dir)
    connector = _build_connector(cfg.data.source)

    end = cfg.data.end or date.today()
    df = connector.fetch_ohlcv(
        symbols=cfg.universe.symbols,
        start=cfg.data.start,
        end=end,
        bar=cfg.data.bar,
    )
    if df.empty:
        log.warning("ingest returned no rows")
        return {}

    store.upsert_ohlcv(df)
    counts = (
        df.groupby("symbol")
        .size()
        .astype(int)
        .to_dict()
    )
    log.info(f"ingest done: {len(counts)} symbols, {sum(counts.values())} rows")
    return counts


# ---------- forecasting ----------


def forecast_symbol(
    symbol: str,
    cfg: AppConfig | str | Path | None = None,
    horizon: int | None = None,
) -> pd.DataFrame:
    cfg = _resolve_config(cfg)
    store = DuckStore(cfg.data.cache_dir)
    ohlcv = store.load_ohlcv([symbol], bar=cfg.data.bar)
    if ohlcv.empty:
        raise ValueError(f"no bars for {symbol}; run ingest first")
    forecaster = _build_forecaster(cfg)
    return forecaster.forecast(
        ohlcv,
        lookback=cfg.model.lookback,
        horizon=horizon if horizon is not None else cfg.model.horizon,
    )


def generate_forecasts_for_universe(cfg: AppConfig) -> pd.DataFrame:
    """For each symbol, generate rolling forecasts at every bar we have history for.

    For MVP, we run the forecaster once over the full window per symbol (the
    forecaster itself handles internal windowing). Each row's `asof` indicates
    the bar the prediction is keyed off.
    """
    store = DuckStore(cfg.data.cache_dir)
    forecaster = _build_forecaster(cfg)
    all_forecasts = []
    for symbol in cfg.universe.symbols:
        ohlcv = store.load_ohlcv([symbol], bar=cfg.data.bar)
        if ohlcv.empty:
            continue
        # Rolling: emit a horizon-1 prediction for every bar where we have enough lookback.
        rolling = _rolling_h1_forecasts(
            ohlcv=ohlcv, forecaster=forecaster, lookback=cfg.model.lookback
        )
        if not rolling.empty:
            all_forecasts.append(rolling)
    return pd.concat(all_forecasts, ignore_index=True) if all_forecasts else pd.DataFrame()


def _rolling_h1_forecasts(
    ohlcv: pd.DataFrame, forecaster, lookback: int
) -> pd.DataFrame:
    """Cheap MVP rolling: compute a 1-step-ahead drift forecast at each bar.

    Heavy models (Kronos) call `forecaster.forecast(...)` per bar; for MVP we
    use the NaiveDrift formula directly to keep this fast — Kronos remains
    callable on demand via `forecast_symbol(...)`.
    """
    import numpy as np

    closes = ohlcv.sort_values("ts")["close"].to_numpy(dtype=float)
    ts = pd.to_datetime(ohlcv.sort_values("ts")["ts"]).reset_index(drop=True)
    symbols = ohlcv["symbol"].iloc[0]

    out = []
    for i in range(lookback, len(closes)):
        window = closes[i - lookback : i + 1]
        log_ret = np.diff(np.log(window))
        drift = float(np.mean(log_ret))
        pred_close = float(window[-1] * np.exp(drift))
        pred_return = float(pred_close / window[-1] - 1.0)
        out.append(
            {
                "symbol": symbols,
                "asof": ts.iloc[i],
                "horizon": 1,
                "target_ts": ts.iloc[i],
                "pred_close": pred_close,
                "pred_return": pred_return,
                "pred_vol": None,
                "model_name": forecaster.name,
                "model_version": forecaster.version,
            }
        )
    return pd.DataFrame(out)


# ---------- backtest ----------


def backtest_strategy(
    cfg: AppConfig | str | Path | None = None,
    rule: str | None = None,
    write_report: bool = True,
) -> BacktestResult:
    cfg = _resolve_config(cfg)
    store = DuckStore(cfg.data.cache_dir)
    chosen_rule = rule or cfg.strategy.rule
    if chosen_rule not in _RULES:
        raise ValueError(f"unknown rule: {chosen_rule}. options: {list(_RULES)}")

    ohlcv = store.load_ohlcv(
        cfg.universe.symbols, bar=cfg.data.bar, start=cfg.data.start, end=cfg.data.end
    )
    if ohlcv.empty:
        raise ValueError("no OHLCV data; run ingest first")

    # Pick params: only honor config.strategy.params when the rule matches the
    # configured rule. Otherwise use rule defaults to avoid TypeError.
    if chosen_rule == cfg.strategy.rule:
        params = dict(cfg.strategy.params)
    elif chosen_rule == cfg.strategy.fallback_rule:
        params = dict(cfg.strategy.fallback_params)
    else:
        params = {}

    if chosen_rule == "kronos_trend":
        forecasts = generate_forecasts_for_universe(cfg)
        if forecasts.empty:
            log.warning("no forecasts; falling back to %s", cfg.strategy.fallback_rule)
            chosen_rule = cfg.strategy.fallback_rule or "sma_crossover"
            params = dict(cfg.strategy.fallback_params)
            forecasts = pd.DataFrame()
    else:
        forecasts = pd.DataFrame()

    rule_obj = _RULES[chosen_rule](**params)
    if chosen_rule == "kronos_trend":
        direction = rule_obj.to_pivot(ohlcv, forecasts=forecasts)
    else:
        direction = rule_obj.to_pivot(ohlcv)

    price_field = getattr(cfg.backtest, "price_field", "adj_close")
    close_pivot = store.load_close_pivot(
        cfg.universe.symbols, bar=cfg.data.bar, start=cfg.data.start, end=cfg.data.end,
        column=price_field,
    )

    benchmark_close = None
    if cfg.backtest.benchmark:
        b = store.load_ohlcv(
            [cfg.backtest.benchmark],
            bar=cfg.data.bar,
            start=cfg.data.start,
            end=cfg.data.end,
        )
        if not b.empty:
            col = price_field if price_field in b.columns else "close"
            benchmark_close = b.set_index("ts")[col]

    # Never trade the benchmark itself if it happens to sit in the universe.
    if cfg.backtest.benchmark and cfg.backtest.benchmark in direction.columns:
        direction = direction.copy()
        direction[cfg.backtest.benchmark] = 0

    # Market-regime gate (CAN SLIM "M"): zero out new longs while the market is risk-off.
    if cfg.strategy.regime_gate and benchmark_close is not None and not benchmark_close.empty:
        from trading_analysis.regime.sma_gate import SMARegimeGate

        gate = SMARegimeGate(window=cfg.strategy.regime_window).mask(benchmark_close)
        # float→ffill→shift→bool avoids the object-downcast FutureWarning on a bool reindex
        gate = gate.reindex(direction.index).astype("float").ffill().shift(1).fillna(0.0) > 0
        direction = direction.mul(gate.astype(int), axis=0)
        log.info(f"regime gate ({cfg.backtest.benchmark}): {int(gate.sum())}/{len(gate)} bars risk-on")

    result = run_backtest(close_pivot, direction, cfg.backtest, benchmark_close=benchmark_close)

    if write_report:
        write_markdown_report(
            result,
            output_dir=cfg.backtest.output_dir,
            name=f"{chosen_rule}_{cfg.universe.name}",
            config_summary={
                "rule": chosen_rule,
                "universe": cfg.universe.name,
                "n_symbols": len(cfg.universe.symbols),
                "start": cfg.data.start.isoformat(),
                "end": (cfg.data.end or date.today()).isoformat(),
                "fees_bps": cfg.backtest.fees_bps,
                "slippage_bps": cfg.backtest.slippage_bps,
            },
        )
    return result


# ---------- helpers ----------


def _resolve_config(cfg: AppConfig | str | Path | None) -> AppConfig:
    if isinstance(cfg, AppConfig):
        return cfg
    return load_config(cfg)


def _build_connector(source: str):
    if source == "yahoo":
        return YahooConnector()
    raise ValueError(f"unsupported data source: {source}")


def _build_forecaster(cfg: AppConfig):
    if cfg.model.use_kronos:
        return KronosForecaster(
            size=cfg.model.kronos_size,
            device=cfg.model.device,
            cache_dir=Path(cfg.data.cache_dir) / "kronos_cache",
        )
    return NaiveDriftForecaster()


# ---------- exports ----------

__all__ = [
    "AppConfig",
    "BacktestResult",
    "UniverseConfig",
    "backtest_strategy",
    "forecast_symbol",
    "generate_forecasts_for_universe",
    "ingest_universe",
    "list_available_strategies",
    "list_universe_symbols",
]
