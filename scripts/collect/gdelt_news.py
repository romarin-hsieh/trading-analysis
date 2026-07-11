"""GDELT news tone/volume collector (docs/24 action #8, sentiment half) -- $0, no key.

IRON RULE (docs/24): GDELT is accessed ONLY via the free DOC 2.0 API -- NEVER BigQuery
(pay-per-TB, uncapped).

Weekly snapshot of daily news tone + article volume for (a) market-level themes and
(b) a compact company watchlist (company NAMES, since GDELT is full-text news, not
ticker-tagged). This is collect-forward seed data for the docs/11 opinion_event design;
tone-model caveats (uncalibrated, English-weighted) are documented, not hidden.

Storage: collected/gdelt/{YYYY-MM-DD}.csv.gz  (one row per query x day, ~few KB/week)
Run:     uv run python scripts/collect/gdelt_news.py           # last 7 days
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

import pandas as pd

API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "trading-analysis research (weekly tone snapshot)"}
OUT = os.path.join("collected", "gdelt")

MARKET_QUERIES = {
    "market": '"stock market"',
    "fed": '"Federal Reserve"',
    "inflation": '"inflation"',
    "recession": '"recession"',
}
COMPANY_QUERIES = {
    "AAPL": '"Apple Inc"', "MSFT": '"Microsoft"', "NVDA": '"Nvidia"',
    "GOOGL": '"Google" OR "Alphabet Inc"', "AMZN": '"Amazon.com" OR "Amazon"',
    "META": '"Meta Platforms"', "TSLA": '"Tesla"', "AVGO": '"Broadcom"',
    "JPM": '"JPMorgan"', "XOM": '"Exxon"', "UNH": '"UnitedHealth"',
    "LLY": '"Eli Lilly"', "V": '"Visa Inc"', "WMT": '"Walmart"',
    "BRK": '"Berkshire Hathaway"', "AMD": '"AMD" OR "Advanced Micro Devices"',
}


def timeline(query: str, mode: str, days: int) -> pd.DataFrame:
    """One DOC-API timeline call with a single 30s-backoff retry on 429.
    Observed rate behavior (2026-07-12, residential IP): a burst of ~20 paired
    requests at 1s pacing triggers sustained 429s for a while afterwards --
    pace >= 6s between queries AND between the tone/vol pair."""
    params = {"query": query + " sourcelang:eng", "mode": mode,
              "timespan": f"{days}d", "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        time.sleep(30.0)
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8", errors="replace"))
    tl = payload.get("timeline", [])
    if not tl:
        return pd.DataFrame()
    rows = [{"date": pt["date"][:8], "value": pt["value"]} for pt in tl[0].get("data", [])]
    df = pd.DataFrame(rows)
    # API returns intraday (15-min) points; aggregate to daily BEFORE any merge
    agg = "sum" if mode == "timelinevolraw" else "mean"
    return df.groupby("date", as_index=False)["value"].agg(agg)


def main() -> int:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    frames = []
    queries = {**{f"mkt:{k}": v for k, v in MARKET_QUERIES.items()},
               **{f"co:{k}": v for k, v in COMPANY_QUERIES.items()}}
    for name, q in queries.items():
        try:
            tone = timeline(q, "timelinetone", days)
            time.sleep(6.0)
            vol = timeline(q, "timelinevolraw", days)
            if tone.empty:
                print(f"  [warn] {name}: empty tone")
                continue
            m = tone.rename(columns={"value": "tone"})
            if not vol.empty:
                m = m.merge(vol.rename(columns={"value": "volume"}), on="date", how="left")
            m.insert(0, "query", name)
            frames.append(m)
            print(f"  {name}: {len(m)} days, mean tone {m['tone'].mean():+.2f}")
        except Exception as e:
            print(f"  [warn] {name}: {str(e)[:80]}")
        time.sleep(6.0)          # GDELT rate limit: 1s pacing draws 429s; 6s is clean
    if not frames:
        print("nothing collected -- not an error")
        return 0
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "asof", date.today().isoformat())
    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, f"{date.today().isoformat()}.csv.gz")
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    with gzip.open(fp, "wt", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    print(f"[gdelt] {len(out)} rows ({out['query'].nunique()} queries) -> {fp} "
          f"({os.path.getsize(fp) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
