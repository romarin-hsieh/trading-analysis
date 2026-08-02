"""SEC Insider Transactions Data Sets -> slim quarterly transaction parquets (docs/28 p2).

Source (schema probed live before this file was written): official SEC structured
data sets, one ZIP per quarter 2006q1..present at
  https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{yyyy}q{n}_form345.zip
(~14MB each, TSV tables). We keep three joins per quarter:
  NONDERIV_TRANS  (open-market codes P/S, shares, price, TRANS_DATE)
  SUBMISSION      (FILING_DATE  <- the PIT clock; ISSUERCIK/SYMBOL; DOCUMENT_TYPE)
  REPORTINGOWNER  (RPTOWNERCIK, RPTOWNER_RELATIONSHIP; multiple owners per filing
                   legitimately multiply rows -- (owner, transaction) is the unit)
A filing in quarter Q can report transactions from YEARS earlier (observed in the
2024q1 probe: a 2022 TRANS_DATE) -- any signal must key on FILING_DATE.

Raw ZIPs are deleted after successful extraction (re-downloadable, static archives);
the slim parquets in data/sec_form4/trans/ are the working store (~1MB/quarter).

Run: uv run python scripts/collect/sec_form4.py   (~10-25 min for 81 quarters)
"""

from __future__ import annotations

import io
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = ("https://www.sec.gov/files/structureddata/data/"
       "insider-transactions-data-sets/{q}_form345.zip")
UA = {"User-Agent": "trading-analysis research romarinhsieh@gmail.com"}
OUT = Path("data/sec_form4/trans")

KEEP_CODES = {"P", "S"}


def quarters():
    from datetime import date
    y, q = 2006, 1
    today = date.today()
    last_y, last_q = today.year, (today.month - 1) // 3 + 1
    while (y, q) <= (last_y, last_q):
        yield f"{y}q{q}"
        y, q = (y, q + 1) if q < 4 else (y + 1, 1)


def slim(zbytes: bytes) -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    sub = pd.read_csv(z.open("SUBMISSION.tsv"), sep="\t", low_memory=False,
                      usecols=["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE",
                               "ISSUERCIK", "ISSUERTRADINGSYMBOL"])
    own = pd.read_csv(z.open("REPORTINGOWNER.tsv"), sep="\t", low_memory=False,
                      usecols=["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNER_RELATIONSHIP"])
    tr = pd.read_csv(z.open("NONDERIV_TRANS.tsv"), sep="\t", low_memory=False,
                     usecols=["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE",
                              "TRANS_SHARES", "TRANS_PRICEPERSHARE",
                              "TRANS_ACQUIRED_DISP_CD"])
    tr = tr[tr["TRANS_CODE"].isin(KEEP_CODES)]
    df = tr.merge(sub, on="ACCESSION_NUMBER", how="left") \
           .merge(own, on="ACCESSION_NUMBER", how="left")
    df["FILING_DATE"] = pd.to_datetime(df["FILING_DATE"], format="%d-%b-%Y", errors="coerce")
    df["TRANS_DATE"] = pd.to_datetime(df["TRANS_DATE"], format="%d-%b-%Y", errors="coerce")
    df = df.rename(columns={
        "ACCESSION_NUMBER": "acc", "TRANS_CODE": "code", "TRANS_SHARES": "shares",
        "TRANS_PRICEPERSHARE": "price", "TRANS_ACQUIRED_DISP_CD": "ad",
        "FILING_DATE": "filing_date", "TRANS_DATE": "trans_date",
        "DOCUMENT_TYPE": "doc_type", "ISSUERCIK": "issuer_cik",
        "ISSUERTRADINGSYMBOL": "symbol", "RPTOWNERCIK": "owner_cik",
        "RPTOWNER_RELATIONSHIP": "relationship"})
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done = n = 0
    for q in quarters():
        pq = OUT / f"{q}.parquet"
        if pq.exists():
            done += 1
            continue
        try:
            time.sleep(0.4)
            data = urllib.request.urlopen(
                urllib.request.Request(URL.format(q=q), headers=UA), timeout=300).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"[404] {q} not yet published -- stopping at the frontier")
                break
            raise
        df = slim(data)
        df.to_parquet(pq)
        n += 1
        print(f"[{q}] {len(df):,} P/S rows -> {pq.name}")
    print(f"[done] +{n} quarters this run | {done} already present")


def load_all() -> pd.DataFrame:
    """All quarters concatenated (consumed by TR-46)."""
    files = sorted(OUT.glob("*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


if __name__ == "__main__":
    main()
