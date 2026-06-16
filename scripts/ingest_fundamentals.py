"""Ingest SEC EDGAR fundamentals for a universe into the DuckStore (point-in-time by filed date).

Batched with per-batch upsert so partial progress is checkpointed. SEC fair-access: <=10 req/s.

Run: uv run python scripts/ingest_fundamentals.py [configs/universe_sp500.yaml]
"""

from __future__ import annotations

import sys

import yaml
from loguru import logger

from trading_analysis.data.connectors.edgar import EdgarConnector
from trading_analysis.data.store import DuckStore

logger.remove()
logger.add(sys.stderr, level="WARNING")


def main(universe_yaml: str = "configs/universe_sp500.yaml", batch: int = 50):
    with open(universe_yaml, encoding="utf-8") as f:
        syms = [s for s in yaml.safe_load(f)["symbols"] if s != "SPY"]
    conn = EdgarConnector()
    store = DuckStore("./data")
    total = 0
    for i in range(0, len(syms), batch):
        chunk = syms[i : i + batch]
        df = conn.fetch_fundamentals(chunk)
        store.upsert_fundamentals(df)
        total += len(df)
        print(f"  {min(i + batch, len(syms))}/{len(syms)} symbols, {total:,} facts so far", flush=True)
    print(f"DONE: {total:,} fundamental facts ingested for {len(syms)} symbols")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/universe_sp500.yaml")
