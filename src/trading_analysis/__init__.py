"""trading-analysis: modular stock trading strategy software."""

from trading_analysis.api import (
    backtest_strategy,
    forecast_symbol,
    ingest_universe,
    list_available_strategies,
    list_universe_symbols,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "backtest_strategy",
    "forecast_symbol",
    "ingest_universe",
    "list_available_strategies",
    "list_universe_symbols",
]
