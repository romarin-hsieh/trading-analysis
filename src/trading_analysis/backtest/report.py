"""Markdown / HTML report generation for backtests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from trading_analysis.backtest.engine import BacktestResult


def metrics_markdown(metrics: dict[str, float]) -> str:
    rows = ["| Metric | Value |", "|---|---|"]
    for k, v in metrics.items():
        if isinstance(v, float):
            rows.append(f"| {k} | {v:.4f} |")
        else:
            rows.append(f"| {k} | {v} |")
    return "\n".join(rows)


def write_markdown_report(
    result: BacktestResult,
    output_dir: Path,
    name: str,
    config_summary: dict | None = None,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = output_dir / f"{name}_{stamp}.md"
    csv_path = output_dir / f"{name}_{stamp}_equity.csv"

    result.equity.rename("equity").to_csv(csv_path, header=True)

    chunks = [
        f"# Backtest report — {name}",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Metrics",
        metrics_markdown(result.metrics),
        "",
        "## Summary",
        f"- Bars: {len(result.equity)}",
        f"- Start equity: {float(result.equity.iloc[0]):,.2f}",
        f"- End equity: {float(result.equity.iloc[-1]):,.2f}",
        f"- Trades: {len(result.trades)}",
    ]
    if config_summary:
        chunks += [
            "",
            "## Config",
            "```yaml",
            *[f"{k}: {v}" for k, v in config_summary.items()],
            "```",
        ]
    chunks += [
        "",
        f"Equity curve CSV: `{csv_path.name}`",
    ]
    md_path.write_text("\n".join(chunks), encoding="utf-8")
    return md_path


def equity_dataframe(result: BacktestResult) -> pd.DataFrame:
    """Convenience: combine equity + benchmark for plotting."""
    df = pd.DataFrame({"equity": result.equity})
    if result.benchmark_equity is not None:
        df["benchmark"] = result.benchmark_equity
    return df
