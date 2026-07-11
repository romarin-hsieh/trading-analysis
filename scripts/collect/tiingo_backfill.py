"""Tiingo delisted-stock rotation backfill (docs/24 action #7) -- closes the last
survivorship hole in the GP verdict (TR-27's still-open half).

Target universe = every ticker that was EVER an S&P 500 member (1996-2026, from the
PIT membership panel) but is NOT currently in the OHLCV store -- i.e. the removed /
delisted / merged names whose absence biases every cross-sectional factor UP.
593 names as of 2026-07-11, incl. the retro-OTC bankrupt cohort (AAMRQ, EKDKQ,
DPHIQ, ...) that docs/24 flagged as the specific 2008-era hole.

Rate discipline (free tier): 50 req/hr is the binding limit; 500 unique symbols/month;
1000 req/day. One symbol = one full-history request. So each RUN fetches a batch of
<= BATCH symbols (default 45, safely under 50/hr regardless of pacing), records state,
and the NEXT batch must wait ~1 hour. Resumable: state file tracks done / no_data /
failed so re-runs continue and never re-spend quota on a symbol already resolved.

Keys: TIINGO_API_KEY in .env (never echoed).
Run:  uv run python scripts/collect/tiingo_backfill.py            # one batch (<=45)
      uv run python scripts/collect/tiingo_backfill.py --batch 20 # smaller batch
      uv run python scripts/collect/tiingo_backfill.py --status   # show progress only
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
from loguru import logger

logger.remove()
from sp500_constituents import load_membership  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

load_dotenv(dotenv_path=".env")
KEY = os.environ.get("TIINGO_API_KEY", "")
STATE = os.path.join("data", "_tiingo_backfill_state.json")
UA = {"User-Agent": "trading-analysis research"}
PACE = 2.0            # seconds between requests within a batch (<50/hr regardless)
BATCH_DEFAULT = 45


def targets() -> list[str]:
    store = DuckStore("./data")
    have = set(store.list_symbols("1d"))
    mem = load_membership()
    ever = set().union(*mem["tickers"])
    return sorted(ever - have)


def load_state() -> dict:
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"done": [], "no_data": [], "failed": []}


def save_state(s: dict) -> None:
    os.makedirs("data", exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), indent=0)


def fetch_prices(ticker: str) -> pd.DataFrame:
    # URL-encode class-share tickers like AFS.A
    t = urllib.parse.quote(ticker, safe="")
    url = (f"https://api.tiingo.com/tiingo/daily/{t}/prices"
           f"?startDate=1990-01-01&format=json&token={KEY}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.loads(r.read())
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    out = pd.DataFrame({
        "symbol": ticker,
        "ts": pd.to_datetime(df["date"]).dt.tz_localize(None),
        "open": df["open"], "high": df["high"], "low": df["low"],
        "close": df["close"], "volume": df["volume"].fillna(0).astype("int64"),
        "adj_close": df["adjClose"], "bar": "1d",
    })
    return out


def main() -> int:
    import urllib.parse  # noqa: F401 (used in fetch_prices)
    if not KEY:
        print("TIINGO_API_KEY not set in .env -- aborting."); return 1
    batch = BATCH_DEFAULT
    if "--batch" in sys.argv:
        batch = int(sys.argv[sys.argv.index("--batch") + 1])

    tgt = targets()
    st = load_state()
    resolved = set(st["done"]) | set(st["no_data"])
    todo = [t for t in tgt if t not in resolved]
    print(f"backfill universe: {len(tgt)} delisted names | "
          f"done {len(st['done'])} | no-data {len(st['no_data'])} | "
          f"failed {len(st['failed'])} | remaining {len(todo)}")
    if "--status" in sys.argv:
        return 0
    if not todo:
        print("nothing remaining -- backfill complete."); return 0

    store = DuckStore("./data")
    this_batch = todo[:batch]
    print(f"fetching {len(this_batch)} this run (<=50/hr): {this_batch[:8]}...")
    ok = nod = fail = 0
    for i, t in enumerate(this_batch):
        try:
            df = fetch_prices(t)
            if df.empty:
                st["no_data"].append(t); nod += 1
            else:
                store.upsert_ohlcv(df)
                st["done"].append(t); ok += 1
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"  [{i+1}/{len(this_batch)}] {t}: {len(df)} bars "
                          f"{df['ts'].min().date()}..{df['ts'].max().date()}")
            if t in st["failed"]:
                st["failed"].remove(t)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  429 at {t} -- hourly cap hit; saving and stopping.")
                break
            st["failed"].append(t); fail += 1
        except Exception as e:
            st["failed"].append(t); fail += 1
            print(f"  {t}: {str(e)[:60]}")
        save_state(st)
        time.sleep(PACE)

    print(f"batch done: +{ok} priced, {nod} no-data, {fail} failed. "
          f"total done {len(st['done'])}/{len(tgt)}. Re-run in ~1h for the next batch.")
    return 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
