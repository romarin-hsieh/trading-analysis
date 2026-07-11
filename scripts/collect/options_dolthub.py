"""DoltHub options connector (docs/24 action #3, keyless half).

post-no-preference/options is a git-versioned Dolt SQL database of US option EOD
chains (2019-02 .. present, ~2000+ symbols): bid/ask/IV/greeks per contract.
No account, no key -- the public web SQL API serves read queries with per-query
timeouts, so this connector pulls SLICES (one symbol-date at a time) and caches
them locally. For bulk work, clone with the dolt CLI instead (tens of GB).

Schema notes (verified in docs/refs/data-sources.md): NO open interest, NO volume;
vendor greeks/IV should be recomputed from quotes for rigor (that recomputation is
exactly the TR-09 exercise).

Usage:
  uv run python scripts/collect/options_dolthub.py SPY 2020-03-16      # one slice
  uv run python scripts/collect/options_dolthub.py SPY 2020-03-16 --peek  # no save
Library:
  from options_dolthub import chain, expirations
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

import pandas as pd

API = "https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master"
UA = {"User-Agent": "trading-analysis-research (options slice reader)"}
CACHE = os.path.join("data", "options_dolthub")


def _q(sql: str) -> pd.DataFrame:
    url = API + "?q=" + urllib.parse.quote(sql)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        payload = json.loads(r.read())
    if payload.get("query_execution_status") not in ("Success", "RowLimit"):
        raise RuntimeError(f"DoltHub query failed: {payload.get('query_execution_message')}")
    return pd.DataFrame(payload.get("rows", []))


def chain(symbol: str, date: str, use_cache: bool = True) -> pd.DataFrame:
    """Full option chain for one symbol on one quote date (EOD)."""
    fp = os.path.join(CACHE, symbol.upper(), f"{date}.parquet")
    if use_cache and os.path.exists(fp):
        return pd.read_parquet(fp)
    df = _q(f"SELECT * FROM option_chain WHERE act_symbol = '{symbol.upper()}' "
            f"AND date = '{date}'")
    if df.empty:
        return df
    for c in ("bid", "ask", "strike", "vol", "delta", "gamma", "theta", "vega", "rho"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if use_cache:
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        df.to_parquet(fp)
    return df


def expirations(symbol: str, date: str) -> list[str]:
    df = _q(f"SELECT DISTINCT expiration FROM option_chain "
            f"WHERE act_symbol = '{symbol.upper()}' AND date = '{date}' ORDER BY expiration")
    return df["expiration"].tolist() if not df.empty else []


def dates_near(symbol: str, around: str, days: int = 7) -> list[str]:
    df = _q(f"SELECT DISTINCT date FROM option_chain WHERE act_symbol = '{symbol.upper()}' "
            f"AND date BETWEEN DATE_SUB('{around}', INTERVAL {days} DAY) "
            f"AND DATE_ADD('{around}', INTERVAL {days} DAY) ORDER BY date")
    return df["date"].tolist() if not df.empty else []


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    peek = "--peek" in sys.argv
    sym, date = (args + ["SPY", "2020-03-16"])[:2]
    print(f"[dolthub] {sym} {date}")
    df = chain(sym, date, use_cache=not peek)
    if df.empty:
        near = dates_near(sym, date)
        print(f"no rows for that date; nearby dates: {near}")
        return 1
    exps = sorted(df["expiration"].unique())
    print(f"rows: {len(df):,} | expirations: {len(exps)} ({exps[0]}..{exps[-1]}) | "
          f"columns: {list(df.columns)}")
    mid = df[(df["call_put"] == "Call")].nlargest(3, "vol")[
        ["expiration", "strike", "bid", "ask", "vol", "delta"]]
    print("top-IV calls sample:")
    print(mid.to_string(index=False))
    if not peek:
        print(f"[cache] data/options_dolthub/{sym.upper()}/{date}.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
