"""EDGAR fundamentals backfill for the DELISTED S&P cohort (B1's second data leg).

The Tiingo rotation restores dead names' PRICES; the GP survivorship verdict
(TR-51) also needs their FUNDAMENTALS. Blocker: EdgarConnector resolves CIKs via
the official company_tickers.json, which mostly lists CURRENT registrants -- dead
names miss. Fix: a two-source CIK map --
  1) official company_tickers.json (works for some recently-dead names);
  2) fallback: our SEC Form-4 slim parquets (SUBMISSION issuer_cik x symbol,
     2006q1+, covers every filer's ticker as-used-at-the-time). Ticker REUSE is
     real (the TR-39b ghost lesson): when several CIKs share a symbol we keep the
     one whose Form-4 filing span overlaps the name's S&P membership window.
Scope note (honest): names dead before ~2006 with no entry in either source stay
uncovered -- reported, not silently dropped.

Output: rows upserted into the DuckStore fundamentals partition (same schema as
the live universe). State: data/_edgar_backfill_state.json. Resumable; re-run
after each Tiingo batch to pick up newly-priced names.
Run: uv run python scripts/collect/edgar_backfill.py   (~0.2s/name, minutes)
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
from loguru import logger

logger.remove()
from sp500_constituents import load_membership  # noqa: E402

from trading_analysis.data.connectors.edgar import EdgarConnector  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

STATE = Path("data/_edgar_backfill_state.json")
TIINGO_STATE = Path("data/_tiingo_backfill_state.json")


def member_windows() -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    mem = load_membership()
    first: dict[str, pd.Timestamp] = {}
    last: dict[str, pd.Timestamp] = {}
    for dt, row in mem["tickers"].items():
        for s in row:
            if s not in first:
                first[s] = dt
            last[s] = dt
    return {s: (first[s], last[s]) for s in first}


def form4_cik_map() -> pd.DataFrame:
    files = sorted(glob.glob("data/sec_form4/trans/*.parquet"))
    frames = []
    for f in files:
        d = pd.read_parquet(f, columns=["symbol", "issuer_cik", "filing_date"])
        frames.append(d.dropna(subset=["symbol"]))
    a = pd.concat(frames, ignore_index=True)
    a["symbol"] = a["symbol"].astype(str).str.upper().str.strip()
    g = a.groupby(["symbol", "issuer_cik"])["filing_date"].agg(["min", "max", "count"])
    return g.reset_index()


def resolve_ciks(targets: list[str]) -> tuple[dict[str, str], list[str]]:
    conn = EdgarConnector()
    official = conn.ticker_cik_map()
    f4 = form4_cik_map()
    win = member_windows()
    out: dict[str, str] = {}
    unresolved: list[str] = []
    for sym in targets:
        u = sym.upper()
        if u in official:
            out[sym] = official[u]
            continue
        cands = f4[f4["symbol"] == u.replace(".", "-")] if "." in u else f4[f4["symbol"] == u]
        if len(cands) == 0:
            unresolved.append(sym)
            continue
        if len(cands) > 1 and sym in win:
            lo, hi = win[sym]
            ok = cands[(cands["min"] <= hi + pd.Timedelta(days=365))
                       & (cands["max"] >= lo - pd.Timedelta(days=365))]
            cands = ok if len(ok) else cands
        cik = int(cands.sort_values("count").iloc[-1]["issuer_cik"])
        out[sym] = f"{cik:010d}"
    return out, unresolved


def main() -> None:
    store = DuckStore("./data")
    tiingo = json.loads(TIINGO_STATE.read_text())
    priced = list(tiingo["done"])
    st = json.loads(STATE.read_text()) if STATE.exists() else {
        "done": [], "no_cik": [], "no_facts": []}
    todo = [s for s in priced
            if s not in set(st["done"]) | set(st["no_cik"]) | set(st["no_facts"])]
    print(f"[edgar-backfill] priced {len(priced)} | done {len(st['done'])} "
          f"| no-cik {len(st['no_cik'])} | no-facts {len(st['no_facts'])} | todo {len(todo)}")
    if not todo:
        print("[edgar-backfill] nothing to do")
        return

    ciks, unresolved = resolve_ciks(todo)
    print(f"[cik] resolved {len(ciks)} (official+Form4) | unresolved {len(unresolved)}")
    st["no_cik"].extend(unresolved)

    conn = EdgarConnector()
    conn.ticker_cik_map = lambda: {s.upper(): c for s, c in ciks.items()}  # inject map
    n_rows = 0
    for i, sym in enumerate(sorted(ciks)):
        df = conn.fetch_fundamentals([sym])
        if df.empty:
            st["no_facts"].append(sym)
        else:
            store.upsert_fundamentals(df)
            st["done"].append(sym)
            n_rows += len(df)
        if (i + 1) % 50 == 0:
            STATE.write_text(json.dumps(st, indent=0))
            print(f"[edgar-backfill] {i+1}/{len(ciks)} ...")
    STATE.write_text(json.dumps(st, indent=0))
    print(f"[done] +{len(st['done'])} with facts ({n_rows:,} rows this run) | "
          f"no-cik {len(st['no_cik'])} | no-facts {len(st['no_facts'])}")


if __name__ == "__main__":
    main()
