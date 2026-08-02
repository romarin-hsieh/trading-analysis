"""Build the Serenity mention/event tables from the tweet archive (reproducible).

Inputs : yan-labs/serenity-aleabitoreddit archive (fetched live, same source as the tracker)
Outputs: data/_serenity_mentions.parquet  one row per (tweet, ticker); dir is the TWEET-level
                                          label from serenity_tracker.extract(), inherited by
                                          every ticker in the tweet (known limitation -- the
                                          fix is per-tweet LLM classification, docs/16 SS5)
         data/_serenity_events.parquet    per ticker: n, first_mention, first_long, n_long

Consumers: scripts/serenity_calls_backtest.py, scripts/verify_serenity_clustering.py.

Run: uv run python scripts/serenity_build_events.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent / "notify"))
from serenity_tracker import extract, fetch_archive

DATA = Path("./data")


def build_mentions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, rw in df.iterrows():
        ticks, direction = extract(rw["text"])
        for t in dict.fromkeys(ticks):  # dedup repeated tickers within one tweet
            rows.append((t, rw["time"], direction, str(rw["id"])))
    return pd.DataFrame(rows, columns=["ticker", "time", "dir", "tweet_id"])


def build_events(mentions: pd.DataFrame) -> pd.DataFrame:
    ev = mentions.groupby("ticker").agg(n=("time", "size"), first_mention=("time", "min"))
    longs = mentions[mentions["dir"] == "long"].groupby("ticker").agg(
        first_long=("time", "min"), n_long=("time", "size"))
    return ev.join(longs).sort_index()  # n_long float64 (NaN where no long)


def main() -> None:
    df = fetch_archive()
    mentions = build_mentions(df)
    events = build_events(mentions)
    mentions.to_parquet(DATA / "_serenity_mentions.parquet", index=False)
    events.to_parquet(DATA / "_serenity_events.parquet")
    print(f"archive: {len(df)} tweets {df['time'].min().date()} -> {df['time'].max().date()}")
    print(f"mentions: {len(mentions)} rows, {mentions['ticker'].nunique()} tickers")
    print("dir counts:\n" + mentions["dir"].value_counts().to_string())
    print(f"events: {len(events)} tickers, {int(events['first_long'].notna().sum())} with first_long")


if __name__ == "__main__":
    main()
