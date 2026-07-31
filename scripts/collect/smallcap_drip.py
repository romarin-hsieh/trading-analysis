"""US small/micro-cap panel drip (docs/28 p3) -- universe builder + two collectors.

The anomaly literature's native habitat. $0 PIT-honest universe WITHOUT CRSP/Russell:
the SEC Form-4 issuer universe (our slim parquets, 2006q1+) -- every issuer with
insider filings carries symbol+CIK+activity years, INCLUDING names that later died
(the survivorship honesty is built into the source).

UNIVERSE RULES (pre-registered here; F11 notes below):
  - dominant issuer_cik per symbol (max row count -- ticker-reuse guard is weaker
    than TR-51's membership-window method and is DECLARED as such);
  - >= 8 distinct (owner, filing_date) events over the sample (shell/SPAC floor);
  - last filing year >= 2015 (a 2015-07+ panel cannot use names dead before it);
  - first filing year <= 2024 (some history);
  - symbol: alnum/dash, <= 5 chars;
  - EXCLUDE ever-S&P-500 members (the large-cap seat) and current store symbols;
  - seeded uniform sample of N=1000 (rng seed 42) -> data/smallcap/universe.csv.
HONESTY NOTES: (a) activity-conditioned (issuers with insider filings) -- a mild
liveness/reporting bias, declared; (b) NOT an index reconstruction -- the size band
is applied at PANEL time from collected mcap; (c) OTC/ADR mix possible -- panel-time
filters decide; (d) sampling (not census) is a quota fact: Tiingo 500 uniques/month.

Modes:
  uv run python scripts/collect/smallcap_drip.py build            # universe.csv
  uv run python scripts/collect/smallcap_drip.py edgar            # facts (fast, no quota)
  uv run python scripts/collect/smallcap_drip.py prices [--batch N]  # Tiingo, 45/hr
State: data/_smallcap_edgar_state.json, data/_smallcap_tiingo_state.json
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
from loguru import logger

logger.remove()
from sp500_constituents import load_membership  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

UNI = Path("data/smallcap/universe.csv")
ST_EDGAR = Path("data/_smallcap_edgar_state.json")
ST_TIINGO = Path("data/_smallcap_tiingo_state.json")
N_SAMPLE = 1000


def build() -> None:
    frames = []
    for f in sorted(glob.glob("data/sec_form4/trans/*.parquet")):
        d = pd.read_parquet(f, columns=["symbol", "issuer_cik", "owner_cik", "filing_date"])
        frames.append(d.dropna(subset=["symbol", "filing_date"]))
    a = pd.concat(frames, ignore_index=True)
    a["symbol"] = a["symbol"].astype(str).str.upper().str.strip()
    ok = a["symbol"].str.fullmatch(r"[A-Z0-9]{1,5}(-[A-Z])?")
    a = a[ok]
    ev = a.drop_duplicates(subset=["symbol", "owner_cik", "filing_date"])
    g = ev.groupby("symbol").agg(
        n_events=("filing_date", "size"),
        first_year=("filing_date", lambda s: int(s.dt.year.min())),
        last_year=("filing_date", lambda s: int(s.dt.year.max())),
    )
    cik = (a.groupby(["symbol", "issuer_cik"]).size().reset_index(name="n")
           .sort_values("n").groupby("symbol").tail(1).set_index("symbol")["issuer_cik"])
    g["cik"] = cik
    g = g[(g["n_events"] >= 8) & (g["last_year"] >= 2015) & (g["first_year"] <= 2024)]

    mem = load_membership()
    ever = set().union(*mem["tickers"])
    store_syms = set(DuckStore("./data").list_symbols("1d"))
    g = g[~g.index.isin(ever | store_syms)]

    rng = np.random.default_rng(42)
    pick = rng.choice(g.index.to_numpy(), size=min(N_SAMPLE, len(g)), replace=False)
    out = g.loc[sorted(pick)].reset_index()
    UNI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(UNI, index=False)
    print(f"[build] candidates after filters {len(g):,} -> sampled {len(out)} "
          f"(seed 42) -> {UNI}")


def edgar() -> None:
    from trading_analysis.data.connectors.edgar import EdgarConnector
    uni = pd.read_csv(UNI, dtype={"symbol": str})
    st = json.loads(ST_EDGAR.read_text()) if ST_EDGAR.exists() else {"done": [], "no_facts": []}
    todo = uni[~uni["symbol"].isin(set(st["done"]) | set(st["no_facts"]))]
    print(f"[edgar] universe {len(uni)} | done {len(st['done'])} | todo {len(todo)}")
    conn = EdgarConnector()
    cmap = {r.symbol.upper(): f"{int(r.cik):010d}" for r in todo.itertuples()}
    conn.ticker_cik_map = lambda: cmap
    store = DuckStore("./data")
    for i, sym in enumerate(sorted(cmap)):
        df = conn.fetch_fundamentals([sym])
        if df.empty:
            st["no_facts"].append(sym)
        else:
            store.upsert_fundamentals(df)
            st["done"].append(sym)
        if (i + 1) % 100 == 0:
            ST_EDGAR.write_text(json.dumps(st, indent=0))
            print(f"[edgar] {i+1}/{len(cmap)} ...")
    ST_EDGAR.write_text(json.dumps(st, indent=0))
    print(f"[edgar done] facts {len(st['done'])} | no-facts {len(st['no_facts'])}")


def prices(batch: int) -> None:
    from tiingo_backfill import fetch_prices
    uni = pd.read_csv(UNI, dtype={"symbol": str})["symbol"].tolist()
    st = json.loads(ST_TIINGO.read_text()) if ST_TIINGO.exists() else {
        "done": [], "no_data": [], "failed": []}
    from collections import Counter
    parked = {s for s, n in Counter(st["failed"]).items() if n >= 3}
    todo = [s for s in uni
            if s not in set(st["done"]) | set(st["no_data"]) | parked]
    print(f"[prices] universe {len(uni)} | done {len(st['done'])} "
          f"| no-data {len(st['no_data'])} | parked {len(parked)} | todo {len(todo)}")
    store = DuckStore("./data")
    n = 0
    for sym in todo[:batch]:
        import time
        time.sleep(2.0)
        try:
            df = fetch_prices(sym)
        except Exception as e:
            st["failed"].append(sym)
            print(f"  [fail] {sym}: {repr(e)[:60]}")
            continue
        if df.empty:
            st["no_data"].append(sym)
        else:
            store.upsert_ohlcv(df)
            st["done"].append(sym)
            n += 1
    ST_TIINGO.write_text(json.dumps(st, indent=0))
    print(f"[prices done] +{n} this run | total {len(st['done'])}/{len(uni)} "
          f"| re-run in ~1h (50/hr cap)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        build()
    elif mode == "edgar":
        edgar()
    elif mode == "prices":
        b = int(sys.argv[sys.argv.index("--batch") + 1]) if "--batch" in sys.argv else 45
        prices(b)
    else:
        print("mode must be build|edgar|prices")
