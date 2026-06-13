"""Streamlit page — list past backtest reports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from trading_analysis.config import load_config

st.set_page_config(page_title="Reports", layout="wide")
st.title("Past backtest reports")

config_path = st.sidebar.text_input("Config path", value="configs/mvp.yaml")
try:
    cfg = load_config(config_path)
except Exception as e:
    st.error(f"Failed to load config: {e}")
    st.stop()

report_dir = Path(cfg.backtest.output_dir)
if not report_dir.exists():
    st.info(f"No reports yet at `{report_dir}`. Run a backtest first.")
    st.stop()

mds = sorted(report_dir.glob("*.md"), reverse=True)
csvs = sorted(report_dir.glob("*_equity.csv"), reverse=True)

if not mds:
    st.info(f"No `.md` reports found in `{report_dir}`.")
    st.stop()

choice = st.sidebar.selectbox("Report", [m.name for m in mds])
selected = next(m for m in mds if m.name == choice)

st.markdown(selected.read_text(encoding="utf-8"))

# Try to find matching equity CSV.
stem = selected.stem
matching_csv = next((c for c in csvs if c.stem.startswith(stem)), None)
if matching_csv is not None:
    eq = pd.read_csv(matching_csv, index_col=0, parse_dates=[0])
    st.subheader("Equity curve")
    st.line_chart(eq)
