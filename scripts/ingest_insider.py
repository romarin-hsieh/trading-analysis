"""Ingest SEC insider (Form 4) open-market transactions for the ingested universe, 2015-2024.

Quarterly bulk data sets, aggregated per (symbol, filing_date), upserted per quarter (checkpointed).

Run: uv run python scripts/ingest_insider.py [start_year] [end_year]
"""

from __future__ import annotations

import sys
import time

from loguru import logger

from trading_analysis.data.connectors.insider import InsiderConnector
from trading_analysis.data.store import DuckStore

logger.remove()
logger.add(sys.stderr, level="WARNING")


def main(start: int = 2015, end: int = 2024):
    store = DuckStore("./data")
    syms = set(store.list_symbols("1d"))
    conn = InsiderConnector()
    total = 0
    for year in range(start, end + 1):
        for q in (1, 2, 3, 4):
            try:
                g = conn.fetch_quarter(year, q, symbols=syms)
                store.upsert_insider(g)
                total += len(g)
                print(f"  {year}q{q}: {len(g):,} rows ({total:,} total)", flush=True)
            except Exception as e:
                print(f"  {year}q{q} FAILED: {repr(e)[:80]}", flush=True)
            time.sleep(0.3)
    print(f"DONE: {total:,} insider (symbol,date) rows ingested")


if __name__ == "__main__":
    a = sys.argv
    main(int(a[1]) if len(a) > 1 else 2015, int(a[2]) if len(a) > 2 else 2024)
