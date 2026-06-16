"""SEC insider-transactions (Form 4) connector — free, no API key.

Uses SEC's bulk quarterly Form 3/4/5 data sets (one ZIP per quarter, ~14MB), far cheaper than
scraping individual filings. The informative signal is OPEN-MARKET activity: purchases
(TRANS_CODE 'P') vs sales ('S') — grants/option-exercises/gifts are excluded (Lakonishok-Lee 2001).

Point-in-time: `as_of` = the SEC FILING_DATE (Form 4 must be filed within ~2 business days of the
trade, so the disclosure lag is small but real — we condition on the filing date, never the trade
date, to avoid look-ahead). Aggregated to one row per (symbol, as_of): buy/sell value & shares.
"""

from __future__ import annotations

import io
import time
import urllib.request
import zipfile

import numpy as np
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)

BASE = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets"
INSIDER_COLUMNS = ["symbol", "as_of", "buy_value", "sell_value", "buy_shares", "sell_shares",
                   "n_buy", "n_sell"]


class InsiderConnector:
    name = "insider"

    def __init__(self, user_agent: str = "trading-analysis research romarinhsieh@gmail.com",
                 min_interval: float = 0.3):
        self.user_agent = user_agent
        self.min_interval = min_interval

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _zip(self, year: int, q: int) -> zipfile.ZipFile:
        url = f"{BASE}/{year}q{q}_form345.zip"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=90) as r:
            return zipfile.ZipFile(io.BytesIO(r.read()))

    def fetch_quarter(self, year: int, q: int, symbols: set[str] | None = None) -> pd.DataFrame:
        """Open-market P/S insider transactions for one quarter, aggregated per (symbol, as_of)."""
        z = self._zip(year, q)
        sub = pd.read_csv(z.open("SUBMISSION.tsv"), sep="\t", dtype=str,
                          usecols=["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERTRADINGSYMBOL"])
        sub = sub[sub["DOCUMENT_TYPE"] == "4"].copy()
        sub["symbol"] = sub["ISSUERTRADINGSYMBOL"].astype(str).str.upper().str.strip()
        if symbols is not None:
            sub = sub[sub["symbol"].isin(symbols)]
        if sub.empty:
            return pd.DataFrame(columns=INSIDER_COLUMNS)
        tr = pd.read_csv(z.open("NONDERIV_TRANS.tsv"), sep="\t", dtype=str,
                         usecols=["ACCESSION_NUMBER", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE"])
        tr = tr[tr["TRANS_CODE"].isin(["P", "S"])]
        m = tr.merge(sub[["ACCESSION_NUMBER", "FILING_DATE", "symbol"]], on="ACCESSION_NUMBER")
        if m.empty:
            return pd.DataFrame(columns=INSIDER_COLUMNS)
        m["shares"] = pd.to_numeric(m["TRANS_SHARES"], errors="coerce")
        m["value"] = m["shares"] * pd.to_numeric(m["TRANS_PRICEPERSHARE"], errors="coerce")
        m["as_of"] = pd.to_datetime(m["FILING_DATE"].str.title(), format="%d-%b-%Y", errors="coerce")
        m = m.dropna(subset=["as_of", "shares"])
        m["buy"] = m["TRANS_CODE"] == "P"
        g = m.groupby(["symbol", "as_of"]).apply(lambda d: pd.Series({
            "buy_value": d.loc[d["buy"], "value"].sum(),
            "sell_value": d.loc[~d["buy"], "value"].sum(),
            "buy_shares": d.loc[d["buy"], "shares"].sum(),
            "sell_shares": d.loc[~d["buy"], "shares"].sum(),
            "n_buy": int(d["buy"].sum()),
            "n_sell": int((~d["buy"]).sum()),
        }), include_groups=False).reset_index()
        return g[INSIDER_COLUMNS]

    def fetch_range(self, start_year: int, end_year: int, symbols: set[str] | None = None) -> pd.DataFrame:
        frames = []
        for year in range(start_year, end_year + 1):
            for q in (1, 2, 3, 4):
                try:
                    g = self.fetch_quarter(year, q, symbols)
                    if not g.empty:
                        frames.append(g)
                    log.info(f"insider {year}q{q}: {0 if g.empty else len(g)} (symbol,date) rows")
                except Exception as e:  # a missing/late quarter shouldn't kill the run
                    log.warning(f"insider {year}q{q} failed: {repr(e)[:80]}")
                time.sleep(self.min_interval)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=INSIDER_COLUMNS)


def net_purchase_ratio(insider: pd.DataFrame, dates: pd.DatetimeIndex, symbols: list[str],
                       window: int = 126) -> pd.DataFrame:
    """Point-in-time insider net-purchase ratio over a trailing `window` (calendar-ish) of FILINGS:
    (buy_value - sell_value) / (buy_value + sell_value), using only filings with as_of <= date.
    Returns [date x symbol]; NaN where there is no insider activity in the window."""
    out = pd.DataFrame(index=dates, columns=symbols, dtype=float)
    for sym in symbols:
        s = insider[insider["symbol"] == sym.upper()]
        if s.empty:
            continue
        # snap each filing to the first trading day STRICTLY AFTER as_of (act next day -> leak-free)
        pos = np.clip(dates.searchsorted(s["as_of"].to_numpy(), side="right"), 0, len(dates) - 1)
        agg = pd.DataFrame({"d": dates[pos], "bv": s["buy_value"].to_numpy(), "sv": s["sell_value"].to_numpy()})
        bv = agg.groupby("d")["bv"].sum().reindex(dates, fill_value=0.0)
        sv = agg.groupby("d")["sv"].sum().reindex(dates, fill_value=0.0)
        bvr = bv.rolling(window, min_periods=1).sum()
        svr = sv.rolling(window, min_periods=1).sum()
        denom = bvr + svr
        out[sym] = ((bvr - svr) / denom).where(denom > 0)
    return out
