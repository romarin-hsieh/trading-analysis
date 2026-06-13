"""Streamlit dashboard. Acts as a thin shell over `trading_analysis.api`.

Run:
    uv run streamlit run src/trading_analysis/ui/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from trading_analysis import api
from trading_analysis.config import load_config
from trading_analysis.observability.logging import setup_logging

setup_logging(level="INFO", log_dir=Path("./logs"))

st.set_page_config(page_title="trading-analysis", layout="wide")

st.title("trading-analysis")
st.caption(
    "Modular stock trading strategy software — MVP (US equities, daily/weekly bars, "
    "Kronos forecasting + rule-based strategies)."
)

config_path = st.sidebar.text_input("Config path", value="configs/mvp.yaml")

try:
    cfg = load_config(config_path)
except Exception as e:
    st.error(f"Failed to load config: {e}")
    st.stop()

st.sidebar.success(f"Universe: **{cfg.universe.name}** ({len(cfg.universe.symbols)} symbols)")
st.sidebar.write(f"Bar: `{cfg.data.bar}`")
st.sidebar.write(f"Date range: `{cfg.data.start} → {cfg.data.end or 'today'}`")

st.markdown(
    """
### What's here

- **Backtest** — run a strategy over the full universe, see equity curve and metrics.
- **Forecast** — generate a Kronos (or fallback) forecast for a single symbol.
- **Reports** — past backtest reports written to disk.

Use the sidebar to navigate.
"""
)

st.markdown("---")
st.markdown(
    f"**Available strategies:** {', '.join(api.list_available_strategies())}"
)
