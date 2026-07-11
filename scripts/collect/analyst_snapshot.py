"""Weekly analyst-estimate snapshot collector (S&P 500 universe) -- docs/24 action #4.

Why: analyst estimate REVISIONS are docs/11's top-ranked alt-data factor, but revision
HISTORY cannot be downloaded free at any price under our budget (IBES/Zacks are
institutional-priced). Like options chains, you cannot buy the past -- only record the
present. Every week not collected is lost forever ("collect-forward"). After 12-18
months of snapshots we can compute point-in-time estimate-revision factors (up/down
counts, eps_trend deltas, target-price momentum) with zero look-ahead by construction.

Grossman-Stiglitz framing: paying an information cost (calendar time) to open the
analyst-expectations dimension at $0.

Collected per symbol (all from yfinance / Yahoo quoteSummary, delayed -- fine for weekly):
  eps_trend          current/7d/30d/60d/90d-ago EPS consensus per period (0q,+1q,0y,+1y)
  eps_revisions      analyst up/down revision counts (last 7/30 days) per period
  earnings_estimate  consensus EPS avg/low/high + #analysts + growth per period
  revenue_estimate   consensus revenue per period
  price_targets      analyst target price current/mean/median/low/high
  recommendations    strongBuy/buy/hold/sell/strongSell counts by month

Storage: collected/analyst/{table}/{YYYY-MM-DD}.csv.gz  (long format, ~200-400 KB/week total)
Run:     uv run python scripts/collect/analyst_snapshot.py            (full universe, ~15-25 min)
         uv run python scripts/collect/analyst_snapshot.py AAPL MSFT  (subset, for testing)
"""

from __future__ import annotations

import datetime as dt
import gzip
import io
import os
import sys
import time

import pandas as pd

UNIVERSE_YAML = os.path.join("configs", "universe_sp500.yaml")
OUT_ROOT = os.path.join("collected", "analyst")
SLEEP = 0.15          # be polite; ~3 quoteSummary-family calls per symbol
MAX_FAIL_STREAK = 25  # if Yahoo blocks us wholesale, stop early instead of hammering


def load_universe() -> list[str]:
    syms = []
    with open(UNIVERSE_YAML, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("- "):
                syms.append(line[2:].strip())
    return syms


def _frame(df: pd.DataFrame | None, sym: str, index_name: str) -> pd.DataFrame | None:
    if df is None or getattr(df, "empty", True):
        return None
    if index_name in df.columns:          # table already carries the key (e.g. recommendations)
        d = df.reset_index(drop=True)
    else:
        d = df.reset_index()
        if d.columns[0] in ("index", 0):
            d = d.rename(columns={d.columns[0]: index_name})
    d.insert(0, "symbol", sym)
    return d


def snapshot_symbol(sym: str) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    tk = yf.Ticker(sym)
    out: dict[str, pd.DataFrame] = {}
    # earningsTrend family (yfinance caches the underlying payload per Ticker)
    for table, attr, idx in (
        ("eps_trend", "eps_trend", "period"),
        ("eps_revisions", "eps_revisions", "period"),
        ("earnings_estimate", "earnings_estimate", "period"),
        ("revenue_estimate", "revenue_estimate", "period"),
    ):
        try:
            d = _frame(getattr(tk, attr), sym, idx)
            if d is not None:
                out[table] = d
        except Exception:
            pass
    try:
        pt = tk.analyst_price_targets  # dict: current/low/high/mean/median
        if pt:
            out["price_targets"] = pd.DataFrame([{"symbol": sym, **pt}])
    except Exception:
        pass
    try:
        d = _frame(tk.recommendations, sym, "period")  # monthly strongBuy..strongSell
        if d is not None:
            out["recommendations"] = d
    except Exception:
        pass
    return out


def main() -> int:
    today = dt.date.today().isoformat()
    syms = sys.argv[1:] or load_universe()
    buckets: dict[str, list[pd.DataFrame]] = {}
    n_ok, fail_streak = 0, 0
    t0 = time.time()
    for i, sym in enumerate(syms):
        try:
            tables = snapshot_symbol(sym)
        except Exception as e:
            print(f"[{sym}] {str(e)[:80]}")
            tables = {}
        if tables:
            n_ok += 1
            fail_streak = 0
            for k, d in tables.items():
                buckets.setdefault(k, []).append(d)
        else:
            fail_streak += 1
            if fail_streak >= MAX_FAIL_STREAK:
                print(f"aborting: {fail_streak} consecutive empty symbols (API block?)")
                break
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(syms)} symbols, {n_ok} ok, {time.time() - t0:.0f}s")
        time.sleep(SLEEP)
    if not buckets:
        print("nothing collected (API down?) -- not an error")
        return 0
    for table, frames in buckets.items():
        out = pd.concat(frames, ignore_index=True)
        out.insert(0, "asof", today)
        ddir = os.path.join(OUT_ROOT, table)
        os.makedirs(ddir, exist_ok=True)
        path = os.path.join(ddir, f"{today}.csv.gz")
        buf = io.StringIO()
        out.to_csv(buf, index=False)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(buf.getvalue())
        print(f"[{table}] {len(out)} rows ({out['symbol'].nunique()} symbols) -> {path} "
              f"({os.path.getsize(path) // 1024} KB)")
    print(f"done: {n_ok}/{len(syms)} symbols in {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
