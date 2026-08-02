"""8-K event-stream collector (docs/24 action #8, EDGAR half) -- $0, no key.

Phase 1: pull EDGAR daily form indexes, keep 8-K/8-K/A rows for our S&P universe
(CIK-mapped via the official company_tickers.json), append to a yearly CSV.
Filing DATE is index-level; second-precision acceptance timestamps and item codes
live in each filing header and are deferred to phase 2 (fetch-on-demand for event
studies). Backfillable: daily indexes exist for decades -- run with --backfill DAYS.

Storage: collected/events8k/{yyyy}.csv.gz  (~500 members x ~8 filings/yr = tiny)
Run:     uv run python scripts/collect/events_8k.py            # last 7 days
         uv run python scripts/collect/events_8k.py --backfill 90
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

import pandas as pd

UA = {"User-Agent": "trading-analysis research romarinhsieh@gmail.com"}
IDX = "https://www.sec.gov/Archives/edgar/daily-index/{y}/QTR{q}/form.{ymd}.idx"
TICKERS_JSON = "https://www.sec.gov/files/company_tickers.json"
OUT = os.path.join("collected", "events8k")
UNIVERSE_YAML = os.path.join("configs", "universe_sp500.yaml")


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def universe_ciks() -> dict[int, str]:
    syms = {ln.strip()[2:].strip() for ln in open(UNIVERSE_YAML, encoding="utf-8")
            if ln.strip().startswith("- ")}
    m = json.loads(_fetch(TICKERS_JSON))
    return {int(v["cik_str"]): v["ticker"] for v in m.values() if v["ticker"] in syms}


def parse_form_idx(raw: bytes) -> pd.DataFrame:
    """Fixed-ish width form.idx: Form Type / Company Name / CIK / Date Filed / File Name."""
    lines = raw.decode("latin-1").splitlines()
    start = next(i for i, l in enumerate(lines) if set(l.strip()) == {"-"}) + 1
    rows = []
    for l in lines[start:]:
        if not l.strip():
            continue
        parts = l.split()
        if len(parts) < 5:
            continue
        form = parts[0]
        fname = parts[-1]
        filed = parts[-2]
        cik = parts[-3]
        company = " ".join(parts[1:-3])
        rows.append((form, company, cik, filed, fname))
    return pd.DataFrame(rows, columns=["form", "company", "cik", "filed", "path"])


def collect_day(d: date, cikmap: dict[int, str]) -> pd.DataFrame:
    q = (d.month - 1) // 3 + 1
    url = IDX.format(y=d.year, q=q, ymd=d.strftime("%Y%m%d"))
    try:
        df = parse_form_idx(_fetch(url))
    except Exception:
        return pd.DataFrame()          # weekend/holiday -> no index
    df = df[df["form"].isin(["8-K", "8-K/A"])].copy()
    df["cik"] = pd.to_numeric(df["cik"], errors="coerce").astype("Int64")
    df = df[df["cik"].isin(cikmap)].copy()
    df["ticker"] = df["cik"].map(cikmap)
    df["accession"] = df["path"].str.rsplit("/", n=1).str[-1].str.replace(".txt", "", regex=False)
    return df[["filed", "ticker", "cik", "form", "accession", "path"]]


def append_rows(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    os.makedirs(OUT, exist_ok=True)
    n_new = 0
    for y, g in df.groupby(df["filed"].str[:4]):
        fp = os.path.join(OUT, f"{y}.csv.gz")
        if os.path.exists(fp):
            old = pd.read_csv(fp, dtype=str)
            merged = pd.concat([old, g.astype(str)]).drop_duplicates(subset=["accession"])
            n_new += len(merged) - len(old)
        else:
            merged = g.astype(str).drop_duplicates(subset=["accession"])
            n_new += len(merged)
        buf = io.StringIO()
        merged.sort_values(["filed", "ticker"]).to_csv(buf, index=False)
        with gzip.open(fp, "wt", encoding="utf-8") as fh:
            fh.write(buf.getvalue())
    return n_new


def main() -> int:
    days = 7
    if "--backfill" in sys.argv:
        days = int(sys.argv[sys.argv.index("--backfill") + 1])
    cikmap = universe_ciks()
    print(f"[8k] universe CIKs mapped: {len(cikmap)}")
    frames = []
    today = date.today()
    for i in range(days):
        d = today - timedelta(days=i)
        df = collect_day(d, cikmap)
        if len(df):
            frames.append(df)
            print(f"  {d}: {len(df)} filings")
    allf = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    n = append_rows(allf)
    print(f"[8k] appended {n} new rows -> {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
