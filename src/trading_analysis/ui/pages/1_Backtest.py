"""Streamlit page — run a backtest."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from trading_analysis import api
from trading_analysis.backtest.report import equity_dataframe
from trading_analysis.config import load_config

st.set_page_config(page_title="Backtest", layout="wide")
st.title("Backtest")

config_path = st.sidebar.text_input("Config path", value="configs/mvp.yaml")
try:
    cfg = load_config(config_path)
except Exception as e:
    st.error(f"Failed to load config: {e}")
    st.stop()

rules = api.list_available_strategies()
default_idx = rules.index(cfg.strategy.rule) if cfg.strategy.rule in rules else 0
rule = st.sidebar.selectbox("Strategy rule", rules, index=default_idx)
write_report = st.sidebar.checkbox("Write markdown report", value=True)

run = st.sidebar.button("Run backtest", type="primary")

if run:
    with st.spinner(f"Running backtest [{rule}] on {len(cfg.universe.symbols)} symbols..."):
        try:
            result = api.backtest_strategy(cfg=cfg, rule=rule, write_report=write_report)
        except Exception as e:
            st.error(str(e))
            st.stop()

    metrics_df = pd.DataFrame(result.metrics.items(), columns=["metric", "value"])
    st.subheader("Metrics")
    st.dataframe(metrics_df, use_container_width=True)

    st.subheader("Equity curve")
    eq = equity_dataframe(result)
    st.line_chart(eq)

    st.subheader("Trades")
    if result.trades is not None and len(result.trades) > 0:
        st.dataframe(result.trades.head(200), use_container_width=True)
        st.caption(f"Showing first 200 of {len(result.trades)} trades.")
    else:
        st.info("No trades produced by this strategy on this period.")
else:
    st.info("Configure on the left, then click **Run backtest**.")
