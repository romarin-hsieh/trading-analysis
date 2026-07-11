"""S&P 500 point-in-time constituents ingest (fja05680/sp500) -- docs/24 action #7 (free half).

Why: F11 (universe legitimacy) needs point-in-time index membership; using today's
constituents for historical backtests is survivorship bias. fja05680/sp500 publishes
'S&P 500 Historical Components & Changes' as a CSV time series (1996-present, MIT,
maintained; built on Clenow's dataset + Wikipedia changes). $0, no key.

This script (a) downloads the CSV to data/ (gitignored -- re-downloadable, never
committed), (b) exposes `membership_on(date)` for backtests, and (c) self-tests the
panel against externally verified 2008-09 events.

DATA CAVEATS (verified 2026-07-11):
  * Tickers are RETROACTIVE post-delisting symbols, not tickers-of-record:
    Lehman = LEHMQ (not LEH), Fannie = FNMA (not FNM), Freddie = FMCC (not FRE),
    old GM = MTLQQ (not GM). Joining to price sources keyed on contemporaneous
    tickers (e.g. Tiingo) needs a symbol-translation step -- do NOT join naively.
  * Removal timing verified correct: FNMA/FMCC out Sep-2008, WB (Wachovia) out
    Dec-2008, MTLQQ out Jun-2009. AIG was NEVER removed from the S&P 500 (a common
    misconception -- it left the Dow, not the S&P 500).
  * Early years thinner (panel starts 1996 with ~487 upstream caveat).

Run:  uv run python scripts/collect/sp500_constituents.py          (download + verify)
Use:  from sp500_constituents import load_membership, membership_on
"""

from __future__ import annotations

import io
import os
import sys
import urllib.parse
import urllib.request

import pandas as pd

RAW_URL = ("https://raw.githubusercontent.com/fja05680/sp500/master/"
           "S%26P%20500%20Historical%20Components%20%26%20Changes(04-16-2025).csv")
# the filename carries a date stamp upstream; fall back to listing the repo if it moved
API_URL = "https://api.github.com/repos/fja05680/sp500/contents/"
LOCAL = os.path.join("data", "sp500_constituents.csv")


def _download() -> str:
    req = urllib.request.Request(API_URL, headers={"User-Agent": "trading-analysis-research"})
    with urllib.request.urlopen(req, timeout=30) as r:
        listing = pd.read_json(io.BytesIO(r.read()))
    import re
    names = [n for n in listing["name"]
             if n.startswith("S&P 500 Historical Components") and n.endswith(".csv")]
    if not names:
        raise RuntimeError("constituents CSV not found in fja05680/sp500 listing")

    def stamp(n):                # prefer "(Updated)", then latest date-stamped file
        if "(Updated)" in n:
            return ("9999", "99", "99")
        m = re.search(r"\((\d{2})-(\d{2})-(\d{4})\)", n)
        return (m.group(3), m.group(1), m.group(2)) if m else ("0000", "00", "00")

    name = max(names, key=stamp)
    url = "https://raw.githubusercontent.com/fja05680/sp500/master/" + urllib.parse.quote(name)
    req = urllib.request.Request(url, headers={"User-Agent": "trading-analysis-research"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    os.makedirs("data", exist_ok=True)
    with open(LOCAL, "wb") as fh:
        fh.write(data)
    print(f"[download] {name} -> {LOCAL} ({len(data) // 1024} KB)")
    return LOCAL


def load_membership(path: str = LOCAL) -> pd.DataFrame:
    """date-indexed DataFrame with a `tickers` column = frozenset of members that day."""
    if not os.path.exists(path):
        _download()
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["tickers"] = df["tickers"].map(lambda s: frozenset(t.strip() for t in s.split(",")))
    return df.set_index("date").sort_index()


def membership_on(date, mem: pd.DataFrame | None = None) -> frozenset:
    """PIT membership as of `date` (last snapshot at or before the date)."""
    mem = load_membership() if mem is None else mem
    idx = mem.index.searchsorted(pd.Timestamp(date), side="right") - 1
    if idx < 0:
        raise ValueError(f"{date} precedes the panel start {mem.index[0].date()}")
    return mem["tickers"].iloc[idx]


def main() -> int:
    mem = load_membership()
    print(f"panel: {mem.index[0].date()} .. {mem.index[-1].date()}, {len(mem)} snapshots")

    checks = []

    def check(name, cond, detail):
        checks.append((name, bool(cond), detail))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}: {detail}")

    m_sep08 = membership_on("2008-09-05", mem)
    m_jan09 = membership_on("2009-01-15", mem)
    m_jul09 = membership_on("2009-07-15", mem)
    m_last = mem["tickers"].iloc[-1]
    check("LEHMQ (Lehman) in 2008-09-05", "LEHMQ" in m_sep08, "retroactive OTC symbol")
    check("LEHMQ out by 2009-01", "LEHMQ" not in m_jan09, "dropped Sep 2008")
    check("FNMA+FMCC in 2008-09-05", {"FNMA", "FMCC"} <= m_sep08, "GSEs pre-removal")
    check("FNMA+FMCC out by 2009-01", not ({"FNMA", "FMCC"} & m_jan09), "removed Sep 2008")
    check("WB (Wachovia) in 2008-09-05", "WB" in m_sep08, "removed Dec 2008")
    check("WB out by 2009-01-15", "WB" not in m_jan09, "Wells Fargo merger")
    check("MTLQQ (old GM) in 2009-01", "MTLQQ" in m_jan09, "retroactive OTC symbol")
    check("MTLQQ out by 2009-07", "MTLQQ" not in m_jul09, "removed Jun 2009")
    check("AIG in 2008-09 AND today", "AIG" in m_sep08 and "AIG" in m_last,
          "AIG never left the S&P 500 (left the Dow, not the index)")
    check("membership size ~500 (2008)", 490 <= len(m_sep08) <= 510, f"n={len(m_sep08)}")
    check("membership size ~500 (latest)", 495 <= len(m_last) <= 510, f"n={len(m_last)}")
    check("AAPL in latest", "AAPL" in m_last, "sanity")
    n_fail = sum(1 for _, ok, _ in checks if not ok)
    print(f"{'ALL CHECKS PASSED' if n_fail == 0 else f'{n_fail} CHECKS FAILED'} "
          f"({len(checks) - n_fail}/{len(checks)})")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
