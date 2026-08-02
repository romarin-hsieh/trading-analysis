"""ThetaData EOD option-chain connector (docs/24 action #3) -- free tier, local terminal.

IMPORTANT (verified 2026-07-12 on the running free tier): the FREE bundle serves EOD
quotes/OHLC for stocks and options (2023-06+), but NOT open interest and NOT intraday
OHLC -- both now return 471 "Invalid permissions". So this connector pulls the EOD
option chain (per-contract OHLC + end-of-day NBBO bid/ask) for VRP / IV-skew / TR-09
BSM validation. GEX/open-interest is NOT available here -- that stays on the self-built
yfinance snapshot (the only free OI source).

Prereq: Theta Terminal running locally (scripts/collect/theta_launch.ps1); this talks
to http://127.0.0.1:25510. Uses the efficient bulk_hist endpoint (one whole expiration
per request). Snapshots cache to gitignored data/ (re-downloadable market data).

Run:  uv run python scripts/collect/thetadata_eod.py SPY 20240703        # one exp EOD
      uv run python scripts/collect/thetadata_eod.py SPY --date 20240703 # all exps that day (heavier)
Library: from thetadata_eod import bulk_eod, expirations
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

import pandas as pd

BASE = "http://127.0.0.1:25510"
OUT = os.path.join("data", "thetadata_eod")
# EOD tick columns (bulk_hist/option/eod format), verified 2026-07-12
COLS = ["ms_of_day", "ms_of_day2", "open", "high", "low", "close", "volume", "count",
        "bid_size", "bid_exchange", "bid", "bid_condition",
        "ask_size", "ask_exchange", "ask", "ask_condition", "date"]


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(BASE + path, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()[:120].decode("utf-8", "replace")
        raise RuntimeError(f"ThetaData {e.code}: {body}") from None
    except urllib.error.URLError:
        raise RuntimeError("Theta Terminal not reachable on :25510 -- run theta_launch.ps1") from None


def expirations(root: str) -> list[int]:
    return _get(f"/v2/list/expirations?root={root}")["response"]


def bulk_eod(root: str, exp: int, start: int, end: int) -> pd.DataFrame:
    """EOD chain for one expiration over [start, end] (yyyymmdd ints)."""
    d = _get(f"/v2/bulk_hist/option/eod?root={root}&exp={exp}"
             f"&start_date={start}&end_date={end}")
    rows = []
    for el in d.get("response", []):
        c = el["contract"]
        for tk in el["ticks"]:
            rec = dict(zip(COLS, tk))
            rec.update(root=c["root"], expiration=c["expiration"],
                       strike=c["strike"] / 1000.0, right=c["right"])
            rows.append(rec)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    return df[["date", "root", "expiration", "strike", "right",
               "open", "high", "low", "close", "volume", "bid", "ask", "mid"]]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = (args + ["SPY"])[0]
    if "--date" in sys.argv:
        day = int(sys.argv[sys.argv.index("--date") + 1])
        exps = [e for e in expirations(root) if e >= day]   # exps still open on that day
        frames = []
        for exp in exps:
            try:
                frames.append(bulk_eod(root, exp, day, day))
            except RuntimeError as e:
                print(f"  {exp}: {e}")
        df = pd.concat([f for f in frames if not f.empty], ignore_index=True) if frames else pd.DataFrame()
        tag = f"{root}_{day}_allexp"
    else:
        exp = int((args + ["SPY", "20240703"])[1])
        df = bulk_eod(root, exp, exp, exp)
        tag = f"{root}_{exp}"
    if df.empty:
        print("no data returned (check date >= 2023-06 and terminal login)."); return 1
    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, f"{tag}.parquet")
    df.to_parquet(fp, index=False)
    print(f"[thetadata] {len(df):,} contract-rows -> {fp} "
          f"({df['strike'].min():.0f}-{df['strike'].max():.0f} strikes, "
          f"mid {df['mid'].gt(0).sum()} priced)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
