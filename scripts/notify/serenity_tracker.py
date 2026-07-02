"""Serenity (@aleabitoreddit) post tracker -- detect new ticker calls, push Telegram alerts.

DATA SOURCE ($0): the public archive repo yan-labs/serenity-aleabitoreddit refreshes a full tweet
archive (data/aleabitoreddit_tweets.csv: id,url,time,text,likes,views; ~6k tweets since 2025-07).
The X API costs $200+/mo and nitter mirrors are unreliable -- the archive is the budget-honest
source, at the cost of update lag (tracker alerts on whatever cadence the archive refreshes).

Modes:
  --analyze : offline anatomy -- ticker mention counts, first/last seen, direction keywords
  (default) : incremental watch -- fetch archive, diff vs local state (data/_serenity_seen.txt),
              extract $TICKER + direction words from NEW tweets, push Telegram summary

HONEST FRAME (docs/16): his numbers are self-reported/unaudited/leveraged; this tracker gives you
SPEED (see calls early) and a paper-trail (dated calls -> your own forward-return audit), not a
guarantee. Never mirror position sizes of an anonymous account.

Run: uv run python scripts/notify/serenity_tracker.py --analyze
"""

from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

import pandas as pd

RAW = "https://raw.githubusercontent.com/yan-labs/serenity-aleabitoreddit/{branch}/data/aleabitoreddit_tweets.csv"
STATE = Path("data/_serenity_seen.txt")
TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
LONG_WORDS = ("long", "bought", "buy", "adding", "entry", "calls", "accumulat", "position")
EXIT_WORDS = ("sold", "sell", "trim", "exit", "closed", "puts", "short", "stop", "take profit", "tp")
NOISE = {"A", "I", "AI", "US", "IT", "CEO", "GPU", "EPS", "ETF", "IPO", "USD", "PT", "YTD", "ATH", "Q", "K", "M", "B"}


def fetch_archive() -> pd.DataFrame:
    import requests
    for branch in ("main", "master"):
        r = requests.get(RAW.format(branch=branch), timeout=60)
        if r.ok:
            df = pd.read_csv(io.StringIO(r.text))
            tcol = "createdAtISO" if "createdAtISO" in df.columns else "time"
            df["time"] = pd.to_datetime(df[tcol], errors="coerce", utc=True)
            return df.sort_values("time")
    raise RuntimeError("archive fetch failed")


def extract(text: str) -> tuple[list[str], str]:
    ticks = [t for t in TICKER_RE.findall(str(text)) if t not in NOISE]
    low = str(text).lower()
    d_long = any(w in low for w in LONG_WORDS)
    d_exit = any(w in low for w in EXIT_WORDS)
    direction = "long" if d_long and not d_exit else ("exit/short" if d_exit and not d_long else
                                                      ("mixed" if d_long and d_exit else "mention"))
    return ticks, direction


def send_telegram(text: str) -> bool:
    import requests
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("[dry-run]\n" + text)
        return False
    return requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                         json={"chat_id": chat, "text": text[:4000]}, timeout=30).ok


def analyze(df: pd.DataFrame) -> None:
    rows = []
    for _, rw in df.iterrows():
        ticks, direction = extract(rw["text"])
        for t in ticks:
            rows.append((t, rw["time"], direction))
    tk = pd.DataFrame(rows, columns=["ticker", "time", "dir"])
    agg = tk.groupby("ticker").agg(n=("time", "size"), first=("time", "min"), last=("time", "max"),
                                   longs=("dir", lambda s: int((s == "long").sum())),
                                   exits=("dir", lambda s: int((s == "exit/short").sum())))
    agg = agg.sort_values("n", ascending=False)
    print(f"archive: {len(df)} tweets {df['time'].min().date()} -> {df['time'].max().date()}")
    print(f"distinct tickers mentioned: {len(agg)}")
    print(agg.head(30).to_string())


def watch() -> int:
    df = fetch_archive()
    seen = set(STATE.read_text().split()) if STATE.exists() else set()
    new = df[~df["id"].astype(str).isin(seen)]
    if seen and len(new):
        lines = [f"Serenity tracker -- {len(new)} new post(s)"]
        for _, rw in new.tail(20).iterrows():
            ticks, direction = extract(rw["text"])
            if ticks:
                lines.append(f"[{str(rw['time'])[:16]}] ({direction}) {' '.join('$'+t for t in ticks)}\n"
                             f"  {str(rw['text'])[:160]}")
        if len(lines) > 1:
            send_telegram("\n".join(lines))
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(" ".join(df["id"].astype(str)))
    print(f"state: {len(df)} ids ({len(new) if seen else 0} new since last run)")
    return 0


if __name__ == "__main__":
    if "--analyze" in sys.argv:
        analyze(fetch_archive())
        sys.exit(0)
    sys.exit(watch())
