"""Typer-based CLI entrypoints."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from trading_analysis import api
from trading_analysis.observability.logging import setup_logging

app = typer.Typer(
    name="trading-analysis",
    help="Modular stock trading strategy software (MVP).",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def _setup(verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging")):
    setup_logging(level="DEBUG" if verbose else "INFO", log_dir=Path("./logs"))


@app.command()
def ingest(
    config: Path = typer.Option(
        Path("configs/mvp.yaml"), "--config", "-c", help="Path to MVP config yaml"
    ),
):
    """Pull OHLCV bars for the configured universe."""
    counts = api.ingest_universe(config)
    table = Table(title="Ingested rows per symbol")
    table.add_column("Symbol", style="cyan")
    table.add_column("Rows", justify="right", style="magenta")
    for sym, n in sorted(counts.items()):
        table.add_row(sym, str(n))
    console.print(table)
    console.print(f"[green]Total rows:[/green] {sum(counts.values())}")


@app.command()
def forecast(
    symbol: str = typer.Argument(..., help="Ticker symbol, e.g. AAPL"),
    config: Path = typer.Option(Path("configs/mvp.yaml"), "--config", "-c"),
    horizon: int = typer.Option(5, "--horizon", "-h"),
):
    """Run Kronos (or fallback) forecast for one symbol and print it."""
    df = api.forecast_symbol(symbol, cfg=config, horizon=horizon)
    if df.empty:
        console.print(f"[yellow]No forecast for {symbol}[/yellow]")
        raise typer.Exit(code=1)
    table = Table(title=f"Forecast — {symbol}")
    for col in ["horizon", "target_ts", "pred_close", "pred_return", "model_name"]:
        table.add_column(col)
    for _, row in df.iterrows():
        table.add_row(
            str(row["horizon"]),
            str(row["target_ts"]),
            f"{row['pred_close']:.2f}",
            f"{row['pred_return']:+.4%}",
            str(row["model_name"]),
        )
    console.print(table)


@app.command()
def backtest(
    config: Path = typer.Option(Path("configs/mvp.yaml"), "--config", "-c"),
    rule: str | None = typer.Option(None, "--rule", "-r", help="Override strategy rule"),
):
    """Run a backtest end-to-end and print metrics."""
    result = api.backtest_strategy(cfg=config, rule=rule, write_report=True)
    table = Table(title="Backtest metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    for k, v in result.metrics.items():
        if isinstance(v, float):
            if "drawdown" in k or "return" in k or "rate" in k or "cagr" in k:
                table.add_row(k, f"{v:+.4%}")
            else:
                table.add_row(k, f"{v:.4f}")
        else:
            table.add_row(k, str(v))
    console.print(table)
    console.print(
        f"[green]Equity:[/green] {float(result.equity.iloc[0]):,.2f} -> "
        f"{float(result.equity.iloc[-1]):,.2f}  "
        f"([cyan]{len(result.equity)}[/cyan] bars, [cyan]{len(result.trades)}[/cyan] trades)"
    )


@app.command(name="list-strategies")
def list_strategies():
    """Show available strategy rules."""
    for s in api.list_available_strategies():
        console.print(f"  - {s}")


@app.command(name="list-universe")
def list_universe(
    config: Path = typer.Option(Path("configs/mvp.yaml"), "--config", "-c"),
):
    """Show symbols in the configured universe."""
    symbols = api.list_universe_symbols(config)
    console.print(f"[cyan]{len(symbols)}[/cyan] symbols:")
    for chunk_start in range(0, len(symbols), 8):
        console.print("  " + "  ".join(symbols[chunk_start : chunk_start + 8]))


if __name__ == "__main__":
    app()
