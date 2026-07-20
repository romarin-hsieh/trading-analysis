"""TWSE chip data (docs/27-28 b7/p1): institutional flows + margin balances.

Two per-stock datasets, both verified against live API responses BEFORE this file
was written (machine fidelity; probe 2026-07-20):
  TaiwanStockInstitutionalInvestorsBuySell  -- daily buy/sell in SHARES, five investor
    types (Foreign_Investor, Foreign_Dealer_Self, Investment_Trust, Dealer_self,
    Dealer_Hedging). Per-stock history starts 2012-05 (docs claim 2005+ but that is
    not what the API returns) -- fully covers the 2014+ Taiwan panel window.
  TaiwanStockMarginPurchaseShortSale -- daily margin/short balances in LOTS (張,
    1 lot = 1,000 shares) plus MarginPurchaseLimit, so margin utilization =
    TodayBalance / Limit needs no shares-outstanding data. Verified identity
    today = yesterday + buy - sell - cash_repayment (TR-45 CAL-b).
Plus one market-level aggregate for the CAL-a anchor:
  TaiwanStockTotalInstitutionalInvestors -- market-wide buy/sell in NT$ VALUE
    (note the unit mismatch vs per-stock shares; TR-45 bridges via shares x close).

Output: data/finmind_tw/chips_flow/{id}.parquet, chips_margin/{id}.parquet,
        chips_total_instit.parquet
Run: uv run python scripts/collect/finmind_tw_chips.py [batch]
     (~4.5-5h for the full 1,293-name universe with token: 2 requests/stock @6.5s)
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
STATE = Path("data/_finmind_tw_chips_state.json")
START = "2012-01-01"
BATCH_DEFAULT = 1400


def _token() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env")
    except Exception:
        pass
    import os
    return os.environ.get("FINMIND_TOKEN", "").strip()


def fetch(dataset: str, pace: float, token: str, **params):
    q = {"dataset": dataset, "start_date": START, **params}
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
    st = json.loads(STATE.read_text()) if STATE.exists() else {
        "done": [], "flow_none": [], "mgn_none": []}

    # market-level aggregate first (single request, CAL-a anchor)
    agg_path = OUT / "chips_total_instit.parquet"
    if not agg_path.exists():
        rows = fetch("TaiwanStockTotalInstitutionalInvestors", pace, token)
        if isinstance(rows, list) and rows:
            pd.DataFrame(rows).to_parquet(agg_path)
            print(f"[agg] TaiwanStockTotalInstitutionalInvestors {len(rows)} rows")
        else:
            print(f"[agg] fetch failed ({rows}) -- retry next run")

    todo = [s for s in syms if s not in set(st["done"])]
    print(f"[chips] universe {len(syms)} | done {len(st['done'])} | todo {len(todo)} "
          f"| this run {min(batch, len(todo))}")
    n = 0
    for sid in todo[:batch]:
        flow = fetch("TaiwanStockInstitutionalInvestorsBuySell", pace, token, data_id=sid)
        if flow == "rate":
            print(f"[rate] stopped at {sid} (flow)")
            break
        mgn = fetch("TaiwanStockMarginPurchaseShortSale", pace, token, data_id=sid)
        if mgn == "rate":
            print(f"[rate] stopped at {sid} (margin; flow re-fetched next run)")
            break
        if flow:
            (OUT / "chips_flow").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(flow).to_parquet(OUT / "chips_flow" / f"{sid}.parquet")
        else:
            st["flow_none"].append(sid)
        if mgn:
            (OUT / "chips_margin").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(mgn).to_parquet(OUT / "chips_margin" / f"{sid}.parquet")
        else:
            st["mgn_none"].append(sid)
        st["done"].append(sid)
        n += 1
        if len(st["done"]) % 25 == 0:
            STATE.write_text(json.dumps(st, indent=1))
            print(f"[chips] {len(st['done'])}/{len(syms)} "
                  f"(flow-none {len(st['flow_none'])}, mgn-none {len(st['mgn_none'])})")
    STATE.write_text(json.dumps(st, indent=1))
    print(f"[done] +{n} | total {len(st['done'])}/{len(syms)} "
          f"| no-flow {len(st['flow_none'])} | no-margin {len(st['mgn_none'])}")


# ---------- panel builders (consumed by TR-45) ----------

def flow_panels(dates: pd.DatetimeIndex, cols):
    """Daily NET buy panels in SHARES: foreign (Foreign_Investor+Foreign_Dealer_Self)
    and investment trust. 0 on alive days with no row is applied by the CALLER (TR-45
    masks by price availability); here missing stays NaN."""
    d = OUT / "chips_flow"
    fnet = pd.DataFrame(index=dates, columns=list(cols), dtype=float)
    itnet = pd.DataFrame(index=dates, columns=list(cols), dtype=float)
    if not d.exists():
        return fnet, itnet
    for f in d.glob("*.parquet"):
        sid = f.stem
        if sid not in fnet.columns:
            continue
        t = pd.read_parquet(f)
        t["net"] = t["buy"] - t["sell"]
        t["date"] = pd.to_datetime(t["date"])
        p = t.pivot_table(index="date", columns="name", values="net", aggfunc="sum")
        for_cols = [c for c in ("Foreign_Investor", "Foreign_Dealer_Self") if c in p.columns]
        if for_cols:
            fnet[sid] = p[for_cols].sum(axis=1).reindex(dates)
        if "Investment_Trust" in p.columns:
            itnet[sid] = p["Investment_Trust"].reindex(dates)
    return fnet, itnet


def margin_panels(dates: pd.DatetimeIndex, cols):
    """Daily margin panels in LOTS: balance, limit, and the identity residual
    today - (yesterday + buy - sell - cash_repayment) for CAL-b."""
    d = OUT / "chips_margin"
    bal = pd.DataFrame(index=dates, columns=list(cols), dtype=float)
    lim = pd.DataFrame(index=dates, columns=list(cols), dtype=float)
    resid_ok = resid_n = 0
    if not d.exists():
        return bal, lim, resid_ok, resid_n
    for f in d.glob("*.parquet"):
        sid = f.stem
        if sid not in bal.columns:
            continue
        t = pd.read_parquet(f)
        t["date"] = pd.to_datetime(t["date"])
        t = t.set_index("date").sort_index()
        t = t[~t.index.duplicated(keep="last")]
        bal[sid] = t["MarginPurchaseTodayBalance"].reindex(dates)
        lim[sid] = t["MarginPurchaseLimit"].reindex(dates)
        r = (t["MarginPurchaseTodayBalance"]
             - (t["MarginPurchaseYesterdayBalance"] + t["MarginPurchaseBuy"]
                - t["MarginPurchaseSell"] - t["MarginPurchaseCashRepayment"]))
        resid_ok += int((r.abs() <= 5).sum())
        resid_n += int(r.notna().sum())
    return bal, lim, resid_ok, resid_n


def total_instit_monthly() -> pd.DataFrame:
    """Published market-wide monthly NET buy VALUE (NT$) by investor type (CAL-a)."""
    t = pd.read_parquet(OUT / "chips_total_instit.parquet")
    t["date"] = pd.to_datetime(t["date"])
    t["net"] = t["buy"] - t["sell"]
    return (t.pivot_table(index="date", columns="name", values="net", aggfunc="sum")
            .resample("ME").sum())


if __name__ == "__main__":
    main()
