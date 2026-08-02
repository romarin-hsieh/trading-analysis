"""FinMind Taiwan collector -- per-stock daily OHLCV + PER/PBR/dividend-yield drip.

Feeds docs/25 B4 (Taiwan habitat factor panel, TR-39): the #1 breakout direction
after TR-36 demoted VRP. Free per-stock mode returns the FULL 2014->today history in
ONE call per dataset (verified: 2330 = 3,058 price rows + 3,061 PER rows), so the
whole 1,220-stock TWSE common-stock universe costs ~2,440 calls total.

Rate limits: ~300 req/hr without a token, ~600 req/hr with a FREE registered token
(set FINMIND_TOKEN in .env; https://finmindtrade.com -> register -> token). The
all-stocks-per-date snapshot mode is a PAID tier (sponsor) -- recorded as an info
cost; we do not use it.

HONESTY (loud, for TR-39's F0): TaiwanStockInfo lists CURRENTLY-listed stocks only
-> the universe is survivorship-biased (delisted names absent). Bias direction:
inflates average returns; second-order but real for cross-sectional slopes (lottery
losers delist more). v2 patch planned: TWSE delisted-company list scrape. Until
then every TR on this panel carries an F13 caveat.

State: data/_finmind_tw_state.json {done, failed}. Output (gitignored):
data/finmind_tw/price/{id}.parquet, data/finmind_tw/per/{id}.parquet,
data/finmind_tw/universe.csv.

Run: uv run python scripts/collect/finmind_tw.py [batch_stocks]   (default 140)
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://api.finmindtrade.com/api/v4/data"
UA = {"User-Agent": "trading-analysis research (romarinhsieh@gmail.com)"}
START_DATE = "2014-01-01"
STATE = Path("data/_finmind_tw_state.json")
OUT = Path("data/finmind_tw")
BATCH_DEFAULT = 140


def _token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env")
    except Exception:
        pass
    import os
    return os.environ.get("FINMIND_TOKEN", "").strip()


def fm(dataset: str, pace: float, token: str, **kw) -> dict:
    q = {"dataset": dataset, **kw}
    if token:
        q["token"] = token
    url = f"{API}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers=UA)
    time.sleep(pace)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return {"status": e.code, "msg": body}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"done": [], "failed": {}}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, indent=1))


def universe(pace: float, token: str) -> pd.DataFrame:
    cache = OUT / "universe.csv"
    if cache.exists():
        return pd.read_csv(cache, dtype={"stock_id": str})
    r = fm("TaiwanStockInfo", pace, token)
    if r.get("status") != 200:
        raise RuntimeError(f"TaiwanStockInfo failed: {r.get('msg')}")
    d = pd.DataFrame(r["data"])
    tw = d[(d["type"] == "twse")
           & d["stock_id"].str.fullmatch(r"\d{4}")
           & ~d["stock_id"].str.startswith("00")].drop_duplicates("stock_id")
    OUT.mkdir(parents=True, exist_ok=True)
    tw.to_csv(cache, index=False)
    print(f"[universe] {len(tw)} twse common stocks cached "
          f"(HONESTY: currently-listed only -- survivorship-biased until v2 patch)")
    return tw


def pull_one(sid: str, pace: float, token: str) -> str:
    """Fetch price + PER for one stock. Returns 'ok' | 'no_data' | 'rate' | 'fail'."""
    for dataset, sub in (("TaiwanStockPrice", "price"), ("TaiwanStockPER", "per")):
        dest = OUT / sub / f"{sid}.parquet"
        if dest.exists():
            continue
        r = fm(dataset, pace, token, data_id=sid, start_date=START_DATE)
        if r.get("status") != 200:
            msg = str(r.get("msg", ""))
            if "upper limit" in msg or "level" in msg.lower() or r.get("status") in (402, 429):
                return "rate"
            return "fail"
        rows = r.get("data", [])
        if not rows:
            if sub == "price":                    # no price at all -> dead entry
                return "no_data"
            continue                              # PER can be legitimately absent
        dest.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(dest)
    return "ok"


def main() -> None:
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else BATCH_DEFAULT
    token = _token()
    pace = 6.5 if token else 12.5                 # ~550/hr with token, ~285/hr without
    print(f"[finmind_tw] token={'yes' if token else 'NO (register free at finmindtrade.com '
          f'-> FINMIND_TOKEN in .env doubles the rate)'} | pace {pace}s/call | batch {batch} stocks")
    uni = universe(pace, token)
    st = load_state()
    todo = [s for s in uni["stock_id"] if s not in st["done"]]
    print(f"[state] done {len(st['done'])}/{len(uni)} | this batch: {min(batch, len(todo))}")
    n_ok = 0
    for sid in todo[:batch]:
        res = pull_one(sid, pace, token)
        if res == "rate":
            print(f"[rate] limit reached at {sid}; stopping cleanly (resume next run)")
            break
        if res in ("ok", "no_data"):
            st["done"].append(sid)
            n_ok += res == "ok"
        else:
            st["failed"][sid] = st["failed"].get(sid, 0) + 1
        if len(st["done"]) % 20 == 0:
            save_state(st)
    save_state(st)
    print(f"[done] +{n_ok} stocks this run | total {len(st['done'])}/{len(uni)} "
          f"| failed {len(st['failed'])}")
    print("TR-39 (Taiwan FM panel) fires when coverage is complete.")


if __name__ == "__main__":
    main()
