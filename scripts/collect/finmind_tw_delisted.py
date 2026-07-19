"""TWSE delisted-companies patch for the Taiwan panel (TR-39 b1 gate).

TR-39's four signal candidates are survivorship-conditional: the FinMind universe
lists CURRENTLY-listed stocks only. This patch closes the gap:
  1. official delisted list from TWSE OpenAPI (suspendListingCsvAndHtml, 2001-2026;
     72 four-digit common stocks delisted 2015+),
  2. FinMind per-stock history for each (verified: delisted IDs are served -- 3474
     ends exactly at its 2016-11-29 delisting),
  3. TRUNCATION AT THE OFFICIAL DELISTING DATE stored in the manifest -- some codes
     get re-used/bridged (2311 shows post-delist rows), so the TR must cut each
     patched series at DelistingDate. The manifest (data/finmind_tw/delisted.csv)
     carries {stock_id, name, delist_date} for exactly that.

Output: same layout as the main collector (data/finmind_tw/{price,per}/{id}.parquet)
so TR-39b's loader picks the names up automatically; manifest drives truncation.

Run: uv run python scripts/collect/finmind_tw_delisted.py   (~15-20 min with token)
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

UA = {"User-Agent": "trading-analysis research (romarinhsieh@gmail.com)"}
API = "https://api.finmindtrade.com/api/v4/data"
OUT = Path("data/finmind_tw")
WINDOW_START = "2015-01-01"
START_DATE = "2014-01-01"


def _token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env")
    except Exception:
        pass
    import os
    return os.environ.get("FINMIND_TOKEN", "").strip()


def twse_delisted() -> pd.DataFrame:
    url = "https://openapi.twse.com.tw/v1/company/suspendListingCsvAndHtml"
    r = json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={**UA, "accept": "application/json"}),
        timeout=60).read().decode())
    d = pd.DataFrame(r)

    def roc(s: str) -> str:
        y, m, dd = s.split("/")
        return f"{int(y) + 1911:04d}-{m}-{dd}"

    d["delist_date"] = d["DelistingDate"].map(roc)
    d = d.rename(columns={"Code": "stock_id", "Company": "name"})
    d = d[(d["delist_date"] >= WINDOW_START)
          & d["stock_id"].str.fullmatch(r"\d{4}")
          & ~d["stock_id"].str.startswith("00")]
    return d[["stock_id", "name", "delist_date"]].sort_values("delist_date")


def fm(dataset: str, sid: str, pace: float, token: str) -> list:
    q = {"dataset": dataset, "data_id": sid, "start_date": START_DATE}
    if token:
        q["token"] = token
    time.sleep(pace)
    r = json.loads(urllib.request.urlopen(
        urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers=UA),
        timeout=120).read().decode())
    if r.get("status") != 200:
        raise RuntimeError(f"{dataset} {sid}: {str(r.get('msg'))[:120]}")
    return r.get("data", [])


def main() -> None:
    token = _token()
    pace = 6.5 if token else 12.5
    man = twse_delisted()
    OUT.mkdir(parents=True, exist_ok=True)
    man.to_csv(OUT / "delisted.csv", index=False)
    print(f"[manifest] {len(man)} delisted 4-digit commons since {WINDOW_START} "
          f"({man['delist_date'].min()}..{man['delist_date'].max()}) -> delisted.csv")
    got, empty = 0, 0
    for _, row in man.iterrows():
        sid = row["stock_id"]
        dest_p = OUT / "price" / f"{sid}.parquet"
        if not dest_p.exists():
            rows = fm("TaiwanStockPrice", sid, pace, token)
            if rows:
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(rows).to_parquet(dest_p)
                got += 1
            else:
                empty += 1
                continue
        dest_q = OUT / "per" / f"{sid}.parquet"
        if not dest_q.exists():
            rows = fm("TaiwanStockPER", sid, pace, token)
            if rows:
                dest_q.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(rows).to_parquet(dest_q)
    print(f"[done] +{got} delisted price histories, {empty} empty at FinMind "
          f"(coverage gap recorded); manifest drives delist-date truncation in TR-39b.")


if __name__ == "__main__":
    main()
