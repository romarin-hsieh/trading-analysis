"""SEC EDGAR fundamentals connector — free, no API key (just a polite User-Agent).

Pulls standardized XBRL company facts (Revenues, NetIncome, GrossProfit, Assets, Equity, ...)
from https://data.sec.gov. The KEY discipline for fundamental alt-data is point-in-time:
every fact carries a `filed` date (when the 10-K/10-Q became public). We keep `filed` as the
`as_of` date and NEVER use the fiscal period-end — otherwise a factor would "know" a quarter's
earnings weeks before they were disclosed (the classic fundamental look-ahead bug).

SEC fair-access rules: <=10 requests/sec and a descriptive User-Agent with contact email.
"""

from __future__ import annotations

import json
import time
import urllib.request

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)

# tags that enable the classic fundamental factors (quality / value / profitability / accruals)
DEFAULT_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "NetIncomeLoss",
    "GrossProfit",
    "Assets",
    "AssetsCurrent",
    "Liabilities",
    "StockholdersEquity",
    "OperatingIncomeLoss",
    "CashAndCashEquivalentsAtCarryingValue",
)
FUNDAMENTAL_COLUMNS = ["symbol", "cik", "tag", "unit", "period_end", "fy", "fp", "form", "as_of", "val"]


class EdgarConnector:
    name = "edgar"

    def __init__(self, user_agent: str = "trading-analysis research romarinhsieh@gmail.com",
                 min_interval: float = 0.15):
        self.user_agent = user_agent
        self.min_interval = min_interval  # >= 0.1s keeps us under 10 req/s

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent,
                                                   "Accept-Encoding": "gzip, deflate"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                import gzip
                raw = gzip.decompress(raw)
            return json.loads(raw)

    def ticker_cik_map(self) -> dict[str, str]:
        """ticker (upper) -> zero-padded 10-digit CIK, from the official SEC mapping."""
        data = self._get_json("https://www.sec.gov/files/company_tickers.json")
        out: dict[str, str] = {}
        for row in data.values():
            out[str(row["ticker"]).upper()] = f"{int(row['cik_str']):010d}"
        return out

    def fetch_fundamentals(self, symbols: list[str], tags=DEFAULT_TAGS) -> pd.DataFrame:
        """Long-form fundamentals for `symbols`. One row per (symbol, tag, period, filing), with
        `as_of` = SEC `filed` date (point-in-time). 10-K/10-Q forms only."""
        cik_map = self.ticker_cik_map()
        tagset = set(tags)
        rows: list[dict] = []
        for sym in symbols:
            cik = cik_map.get(sym.upper())
            if cik is None:
                log.warning(f"edgar: no CIK for {sym}")
                continue
            try:
                facts = self._get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
            except Exception as e:
                log.warning(f"edgar: companyfacts failed for {sym}: {repr(e)[:80]}")
                time.sleep(self.min_interval)
                continue
            usgaap = facts.get("facts", {}).get("us-gaap", {})
            for tag in tagset & set(usgaap):
                for unit, entries in usgaap[tag].get("units", {}).items():
                    for e in entries:
                        if e.get("form") not in ("10-K", "10-Q") or "filed" not in e:
                            continue
                        rows.append({"symbol": sym.upper(), "cik": cik, "tag": tag, "unit": unit,
                                     "period_end": e.get("end"), "fy": e.get("fy"), "fp": e.get("fp"),
                                     "form": e.get("form"), "as_of": e["filed"], "val": e.get("val")})
            time.sleep(self.min_interval)
        df = pd.DataFrame(rows, columns=FUNDAMENTAL_COLUMNS)
        if not df.empty:
            df["as_of"] = pd.to_datetime(df["as_of"])
            df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")
            df = df.dropna(subset=["val", "as_of"]).drop_duplicates(
                subset=["symbol", "tag", "period_end", "form", "as_of"])
        log.info(f"edgar: {len(df)} fundamental facts for {df['symbol'].nunique() if len(df) else 0} symbols")
        return df


def point_in_time(fund: pd.DataFrame, tag: str, dates: pd.DatetimeIndex,
                  symbols: list[str]) -> pd.DataFrame:
    """Wide [date x symbol] of the most-recently-FILED value of `tag` as of each date — strictly
    point-in-time (uses only facts with as_of <= date). The core no-look-ahead alignment."""
    sub = fund[fund["tag"] == tag]
    out = pd.DataFrame(index=dates, columns=symbols, dtype=float)
    for sym in symbols:
        s = sub[sub["symbol"] == sym.upper()]
        if s.empty:
            continue
        # A filing re-discloses prior periods as comparatives (same as_of, many period_end). For
        # each filing date keep the LATEST period disclosed, then forward-fill onto price dates
        # (uses only facts with as_of <= date — strictly no future leakage).
        s = s.sort_values(["as_of", "period_end"])
        ser = s.groupby("as_of").tail(1).set_index("as_of")["val"].astype(float)
        ser = ser[~ser.index.duplicated(keep="last")].sort_index()
        out[sym] = ser.reindex(dates, method="ffill")
    return out
