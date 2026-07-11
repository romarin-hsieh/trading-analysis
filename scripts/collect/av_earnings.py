"""Alpha Vantage EARNINGS backfill (docs/24 action #5) -- consensus-based SUE for PEAD.

The EARNINGS endpoint returns, per quarter: fiscalDateEnding, reportedDate (the PIT
known date), reportedEPS, estimatedEPS (analyst CONSENSUS at report time), surprise,
surprisePercentage, reportTime. This is the piece our EDGAR-only SUE lacked -- a
consensus expectation to measure the surprise against, which is what sharpens PEAD.

Free tier = 25 requests/day. One symbol = one full-history request, so each run does a
batch <= 24 and records resumable state; ~500 names span ~3 weeks of daily drips.
Historical + re-downloadable, so it lands in gitignored data/ like Tiingo/EDGAR (NOT
committed) -- market-data discipline; only the state file (ticker names) is tracked.

Keys: ALPHA_VANTAGE_API_KEY in .env (never echoed).
Run:  uv run python scripts/collect/av_earnings.py            # one daily batch (<=24)
      uv run python scripts/collect/av_earnings.py --batch 10
      uv run python scripts/collect/av_earnings.py --status
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sys
import time
import urllib.request

import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
OUT = os.path.join("data", "av_earnings")
STATE = os.path.join("data", "_av_earnings_state.json")
UNIVERSE_YAML = os.path.join("configs", "universe_sp500.yaml")
UA = {"User-Agent": "trading-analysis research"}
PACE = 2.0
BATCH_DEFAULT = 24                 # keep 1 of the 25/day in reserve


def universe() -> list[str]:
    return [ln.strip()[2:].strip() for ln in open(UNIVERSE_YAML, encoding="utf-8")
            if ln.strip().startswith("- ")]


def load_state() -> dict:
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"done": [], "no_data": [], "failed": []}


def save_state(s: dict) -> None:
    os.makedirs("data", exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), indent=0)


def fetch(symbol: str) -> tuple[pd.DataFrame | None, str]:
    """Returns (quarterly earnings frame, status). status in {ok, no_data, rate}."""
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={KEY}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        d = json.loads(r.read())
    # AV signals throttling with a Note/Information field and HTTP 200
    if any(kk in d for kk in ("Note", "Information")):
        return None, "rate"
    qe = d.get("quarterlyEarnings")
    if not qe:
        return None, "no_data"
    df = pd.DataFrame(qe)
    df.insert(0, "symbol", symbol)
    for c in ("reportedEPS", "estimatedEPS", "surprise", "surprisePercentage"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, "ok"


def main() -> int:
    if not KEY:
        print("ALPHA_VANTAGE_API_KEY not set in .env -- aborting."); return 1
    batch = BATCH_DEFAULT
    if "--batch" in sys.argv:
        batch = int(sys.argv[sys.argv.index("--batch") + 1])

    uni = universe()
    st = load_state()
    resolved = set(st["done"]) | set(st["no_data"])
    todo = [t for t in uni if t not in resolved]
    print(f"universe {len(uni)} | done {len(st['done'])} | no-data {len(st['no_data'])} | "
          f"failed {len(st['failed'])} | remaining {len(todo)}")
    if "--status" in sys.argv:
        return 0
    if not todo:
        print("nothing remaining -- earnings backfill complete."); return 0

    os.makedirs(OUT, exist_ok=True)
    this_batch = todo[:batch]
    print(f"fetching {len(this_batch)} this run (<=25/day): {this_batch[:8]}...")
    ok = nod = fail = 0
    for i, t in enumerate(this_batch):
        try:
            df, status = fetch(t)
            if status == "rate":
                print(f"  daily 25-request cap hit at {t} -- saving and stopping.")
                break
            if status == "no_data":
                st["no_data"].append(t); nod += 1
            else:
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                with gzip.open(os.path.join(OUT, f"{t}.csv.gz"), "wt", encoding="utf-8") as fh:
                    fh.write(buf.getvalue())
                st["done"].append(t); ok += 1
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"  [{i+1}/{len(this_batch)}] {t}: {len(df)} quarters "
                          f"{df['reportedDate'].min()}..{df['reportedDate'].max()}")
            if t in st["failed"]:
                st["failed"].remove(t)
        except Exception as e:
            st["failed"].append(t); fail += 1
            print(f"  {t}: {str(e)[:60]}")
        save_state(st)
        time.sleep(PACE)

    print(f"batch done: +{ok} earnings, {nod} no-data, {fail} failed. "
          f"total done {len(st['done'])}/{len(uni)}. Re-run tomorrow for the next batch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
