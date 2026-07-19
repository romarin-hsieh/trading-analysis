"""TWSE ex-dividend events -> total-return adjustment factors (docs/27 b6).

TR-39/40/41 all ran on RAW closes. Taiwan's cash yields are large (0050 measured at
+2.49%/yr in the allocation lab) and, critically for TR-41, they are NOT uniform across
the liquidity ladder -- small illiquid names in Taiwan are often high-yield. Every
price-only conclusion therefore carries an unknown level error, and the direction is
not obvious a priori.

FinMind's TaiwanStockDividendResult gives, per ex-date, the official before/after
reference prices. The adjustment factor for one event is after/before; the cumulative
back-adjustment for a date t is the product of all factors AFTER t. Total-return price
= raw_close / cum_factor(t)  (equivalently: multiply historical prices by the factors
that have not yet happened -- standard back-adjustment).

Output: data/finmind_tw/divresult/{id}.parquet + a built adjustment panel consumed by
the TR-39b engine.
Run: uv run python scripts/collect/finmind_tw_dividends.py [batch]   (~2h for 1,220 with token)
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
OUT = Path("data/finmind_tw")
STATE = Path("data/_finmind_tw_div_state.json")
BATCH_DEFAULT = 400


def _token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env")
    except Exception:
        pass
    import os
    return os.environ.get("FINMIND_TOKEN", "").strip()


def fetch(sid: str, pace: float, token: str):
    q = {"dataset": "TaiwanStockDividendResult", "data_id": sid, "start_date": "2013-01-01"}
    if token:
        q["token"] = token
    time.sleep(pace)
    try:
        r = json.loads(urllib.request.urlopen(
            urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers=UA),
            timeout=120).read().decode())
    except urllib.error.HTTPError as e:
        return None if e.code in (400, 404) else "rate"
    if r.get("status") != 200:
        msg = str(r.get("msg", "")).lower()
        return "rate" if ("limit" in msg or "level" in msg) else None
    return r.get("data", [])


def main() -> None:
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else BATCH_DEFAULT
    token = _token()
    pace = 6.5 if token else 12.5
    uni = pd.read_csv(OUT / "universe.csv", dtype={"stock_id": str})["stock_id"].tolist()
    man = pd.read_csv(OUT / "delisted.csv", dtype={"stock_id": str})["stock_id"].tolist()
    syms = sorted(set(uni) | set(man))
    st = json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "none": []}
    todo = [s for s in syms if s not in set(st["done"]) | set(st["none"])]
    print(f"[div] universe {len(syms)} | done {len(st['done'])} | no-events {len(st['none'])} "
          f"| todo {len(todo)} | this run {min(batch, len(todo))}")
    n = 0
    for sid in todo[:batch]:
        rows = fetch(sid, pace, token)
        if rows == "rate":
            print(f"[rate] stopped at {sid}")
            break
        if rows:
            (OUT / "divresult").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_parquet(OUT / "divresult" / f"{sid}.parquet")
            st["done"].append(sid)
            n += 1
        else:
            st["none"].append(sid)
        if (len(st["done"]) + len(st["none"])) % 50 == 0:
            STATE.write_text(json.dumps(st, indent=1))
    STATE.write_text(json.dumps(st, indent=1))
    print(f"[done] +{n} with events | total {len(st['done'])} with / {len(st['none'])} without")


def adjustment_panel(dates: pd.DatetimeIndex, cols) -> pd.DataFrame:
    """Cumulative back-adjustment divisor: raw_close / factor = total-return price.

    factor(t) = product of (after/before) for every ex-event STRICTLY AFTER t, so the
    most recent price is unchanged and history is scaled down -- the standard
    back-adjusted convention (matches Yahoo's auto_adjust)."""
    import numpy as np
    d = Path("data/finmind_tw/divresult")
    out = pd.DataFrame(1.0, index=dates, columns=list(cols))
    if not d.exists():
        return out
    for f in d.glob("*.parquet"):
        sid = f.stem
        if sid not in out.columns:
            continue
        ev = pd.read_parquet(f)
        ev = ev[(ev["before_price"] > 0) & (ev["after_price"] > 0)]
        if ev.empty:
            continue
        ex = pd.to_datetime(ev["date"])
        ratio = (ev["after_price"] / ev["before_price"]).to_numpy()
        ratio = np.clip(ratio, 0.5, 1.0)          # guard against bad rows (splits/errors)
        s = pd.Series(ratio, index=ex).sort_index()
        s = s[~s.index.duplicated(keep="last")]
        # cumulative product of factors strictly after each date
        rev = s.iloc[::-1].cumprod().iloc[::-1]
        aligned = rev.reindex(dates.union(rev.index)).bfill().reindex(dates).fillna(1.0)
        out[sid] = aligned.to_numpy()
    return out


if __name__ == "__main__":
    main()
