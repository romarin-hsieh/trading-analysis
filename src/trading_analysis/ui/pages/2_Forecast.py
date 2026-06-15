"""Streamlit page — single-symbol forecast."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from trading_analysis import api
from trading_analysis.config import load_config
from trading_analysis.data.store import DuckStore

st.set_page_config(page_title="Forecast", layout="wide")
st.title("Forecast — single symbol")

config_path = st.sidebar.text_input("Config path", value="configs/mvp.yaml")
try:
    cfg = load_config(config_path)
except Exception as e:
    st.error(f"Failed to load config: {e}")
    st.stop()

universe_symbols = cfg.universe.symbols

store = DuckStore(cfg.data.cache_dir)
available = set(store.list_symbols(bar=cfg.data.bar))
options = [s for s in universe_symbols if s in available] or universe_symbols
if not available:
    st.warning("No data ingested yet — run `trading-analysis ingest` first.")

symbol = st.sidebar.selectbox("Symbol", options, index=0 if options else None)
horizon = st.sidebar.slider("Horizon (bars ahead)", 1, 30, value=cfg.model.horizon)
run = st.sidebar.button("Generate forecast", type="primary")

if run and symbol:
    with st.spinner(f"Forecasting {symbol}..."):
        try:
            forecasts = api.forecast_symbol(symbol, cfg=cfg, horizon=horizon)
        except Exception as e:
            st.error(str(e))
            st.stop()

    history = store.load_ohlcv([symbol], bar=cfg.data.bar)
    history["ts"] = pd.to_datetime(history["ts"])
    last_n = history.tail(120).set_index("ts")["close"]
    last_n.name = "close"

    st.subheader(f"Forecast for {symbol}")
    st.dataframe(forecasts, use_container_width=True)

    chart_df = pd.DataFrame({"close (history)": last_n})
    f = forecasts.copy()
    f["target_ts"] = pd.to_datetime(f["target_ts"])
    pred = f.set_index("target_ts")["pred_close"]
    pred.name = "pred_close"
    chart_df = chart_df.join(pred, how="outer").sort_index()
    st.line_chart(chart_df)
elif not run:
    st.info("Choose a symbol on the left, then click **Generate forecast**.")
