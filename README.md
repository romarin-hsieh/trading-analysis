# trading-analysis

Modular stock trading strategy software. Layered architecture: data → models → strategy → backtest → execution → UI. MVP focuses on US equities, daily/weekly bars, with Kronos foundation-model forecasting and rule-based strategies. LLM multi-agent layer arrives in V1.

## Quickstart

```bash
# Install
uv sync --extra kronos --extra dev

# Configure
cp .env.example .env

# Ingest market data
uv run trading-analysis ingest --config configs/mvp.yaml

# Run a backtest
uv run trading-analysis backtest --config configs/mvp.yaml

# Launch dashboard
uv run streamlit run src/trading_analysis/ui/streamlit_app.py
```

## Architecture

UI (Streamlit) → CLI (Typer) → `trading_analysis.api` (public) → core library (data / models / strategy / backtest / execution).

UI may **only** call `trading_analysis.api`. Internals are private.

## Status

MVP — Kronos prediction + rule-based strategies + vectorbt backtest. No LLM agents yet.

## License

Apache-2.0. See [LICENSE](LICENSE).

**Reference resources** (design inspiration only — no code copied):
- [Kronos](https://github.com/shiyu-coder/Kronos) (foundation model, integrated as dependency)
- [TradingAgents](https://github.com/TauricResearch/TradingAgents)
- [ai-hedge-fund](https://github.com/QuantJosh/ai-hedge-fund)
- [system-design-primer](https://github.com/donnemartin/system-design-primer)
- FinceptTerminal — design reference only; **no code copied** (AGPL-3.0).
