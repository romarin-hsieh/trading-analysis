"""Adversarial verification of the Serenity event study (clustering + extraction lens).

(1) Recompute t-stats with calendar-month clustering (CRVE) and a month-block
    bootstrap -- overlapping event windows in the same AI-bull regime violate the
    independence behind plain-SE t-stats.
(2) Sample random tweets classified 'long' and print their text for hand-judging
    the keyword classifier's misclassification rate; quantify weak-keyword triggers.
    Trigger display uses the LIVE classifier regexes (word-boundary + negation
    guards), so what you see is what labeled the tweet.
(3) Tail dependence: mean vs median gap, and the effect of dropping the top-5
    abnormal events per horizon.

This audit caught two real classifier bugs (both fixed in serenity_tracker.py):
'tp' substring-matching 'http' (16.8% of tweets could never be labeled long), and
negation/non-directional phrases ('never long', 'no positions', 'long-term')
labeled long.

Run: uv run python scripts/verify_serenity_clustering.py
"""

from loguru import logger

logger.remove()

import json  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

sys.path.append(str(Path(__file__).parent / "notify"))
from serenity_tracker import EXIT_RE, LONG_RE, NEG_LONG_RE, NONDIR_LONG_RE  # noqa: E402

DATA = Path("./data")
HORIZONS = [5, 21, 63]
STRONG_LONG = ("bought", "buy", "adding", "accumulat")


def sanitize(text: str, width: int = 220) -> str:
    """ASCII-only, single-line, truncated (cp950-safe console)."""
    t = str(text).replace("\n", " | ").replace("\r", "")
    t = t.encode("ascii", "replace").decode("ascii")
    return t[:width] + ("..." if len(t) > width else "")


def entry_position(tweet_utc: pd.Timestamp, market_dates: pd.DatetimeIndex) -> int:
    et_date = pd.Timestamp(tweet_utc.tz_convert("America/New_York").date())
    return int(market_dates.searchsorted(et_date, side="right"))


def event_returns(events: pd.Series, px: pd.DataFrame,
                  market_dates: pd.DatetimeIndex, qqq: np.ndarray) -> pd.DataFrame:
    rows = []
    for ticker, ts in events.items():
        if ticker not in px.columns:
            continue
        p = px[ticker].to_numpy()
        pos = entry_position(ts, market_dates)
        for h in HORIZONS:
            ex = pos + h
            if pos >= len(market_dates) or ex >= len(market_dates):
                continue
            if np.isnan(p[pos]) or np.isnan(p[ex]):
                continue
            raw = p[ex] / p[pos] - 1.0
            bench = qqq[ex] / qqq[pos] - 1.0
            rows.append({"ticker": ticker, "tweet_utc": ts,
                         "entry_date": market_dates[pos], "horizon": h,
                         "raw": raw, "abnormal": raw - bench})
    return pd.DataFrame(rows)


def clustered_t(ab: np.ndarray, clusters: np.ndarray) -> tuple[float, float, int]:
    """CR1 cluster-robust t for the mean. Returns (t, se, n_clusters)."""
    n = len(ab)
    if n == 0:
        return np.nan, np.nan, 0
    mean = ab.mean()
    e = ab - mean
    sums = pd.Series(e).groupby(pd.Series(clusters)).sum()
    g = len(sums)
    if g <= 1:
        return np.nan, np.nan, g
    var = (g / (g - 1)) * float((sums**2).sum()) / n**2
    se = np.sqrt(var)
    return mean / se if se > 0 else np.nan, se, g


def month_block_bootstrap(ab: np.ndarray, clusters: np.ndarray,
                          n_boot: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    """Resample calendar months (blocks) with replacement; return
    (boot mean of means, frac of boot means <= 0, boot se)."""
    rs = np.random.RandomState(seed)
    ser = pd.Series(ab)
    groups = {m: ser[clusters == m].to_numpy() for m in np.unique(clusters)}
    keys = list(groups)
    g = len(keys)
    if g == 0:
        return np.nan, np.nan, np.nan
    means = np.empty(n_boot)
    for b in range(n_boot):
        pick = rs.randint(0, g, size=g)
        vals = np.concatenate([groups[keys[i]] for i in pick])
        means[b] = vals.mean()
    return means.mean(), float((means <= 0).mean()), means.std(ddof=1)


def triggers(text: str) -> tuple[list[str], list[str]]:
    """Surface keyword matches under the LIVE classifier's preprocessing."""
    low = re.sub(r"https?://\S+", " ", str(text).lower())
    low = NONDIR_LONG_RE.sub(" ", NEG_LONG_RE.sub(" ", low))
    return sorted(set(LONG_RE.findall(low))), sorted(set(EXIT_RE.findall(low)))


def main() -> None:
    events = pd.read_parquet(DATA / "_serenity_events.parquet")
    mentions = pd.read_parquet(DATA / "_serenity_mentions.parquet")
    covered = json.loads((DATA / "_serenity_covered.json").read_text())

    store = DuckStore("./data")
    px = store.load_close_pivot(sorted(set(covered) | {"QQQ"}), column="adj_close")
    market_dates = px.index[px["QQQ"].notna()]
    px = px.loc[market_dates]
    qqq = px["QQQ"].to_numpy()

    ev_cov = events[events.index.isin(covered)]
    first_long = ev_cov["first_long"].dropna().sort_index()
    fl_df = event_returns(first_long, px, market_dates, qqq)

    print("=" * 78)
    print("VERIFIER: month-clustered stats, tail dependence, extraction quality")
    print("=" * 78)

    # ---------- (1) calendar-month clustering ----------
    print("\n[1] CALENDAR-TIME CLUSTERING (entry month as cluster)")
    fl_df["month"] = fl_df["entry_date"].dt.strftime("%Y-%m")
    for h in HORIZONS:
        sub = fl_df[fl_df["horizon"] == h]
        ab = sub["abnormal"].to_numpy()
        n = len(ab)
        plain_t = ab.mean() / (ab.std(ddof=1) / np.sqrt(n))
        ct, cse, g = clustered_t(ab, sub["month"].to_numpy())
        _bmean, pneg, bse = month_block_bootstrap(ab, sub["month"].to_numpy())
        mcounts = sub["month"].value_counts()
        print(f"  H={h:>2}: n={n:>3} months={g:>2} (max month share "
              f"{mcounts.max() / n:.0%}) mean abn={ab.mean():>7.2%}")
        print(f"        plain t={plain_t:>5.2f}  month-clustered t={ct:>5.2f} "
              f"(CR1 se={cse:.4f})")
        print(f"        month-block bootstrap: se={bse:.4f}  "
              f"P(mean<=0)={pneg:.3f}  (2000 reps, seed 7)")
    print("  entry-month distribution (H=63 sample):")
    d63 = fl_df[fl_df["horizon"] == 63]["month"].value_counts().sort_index()
    for m, c in d63.items():
        print(f"    {m}: {c}")

    # ---------- (3) tail dependence ----------
    print("\n[3] TAIL DEPENDENCE: mean vs median, drop-top-5 abnormal")
    for h in HORIZONS:
        sub = fl_df[fl_df["horizon"] == h].sort_values("abnormal")
        ab = sub["abnormal"].to_numpy()
        n = len(ab)
        top5 = sub.tail(5)
        rest = ab[:-5]
        t_rest = rest.mean() / (rest.std(ddof=1) / np.sqrt(len(rest)))
        ct_rest, _, _ = clustered_t(rest, sub["month"].to_numpy()[:-5])
        top5_share = top5["abnormal"].sum() / ab.sum() if ab.sum() != 0 else np.nan
        print(f"  H={h:>2}: mean={ab.mean():>7.2%} median={np.median(ab):>7.2%} "
              f"| top-5 events = {top5_share:.0%} of total abnormal sum")
        print("        top5: " + ", ".join(
            f"{r['ticker']} {r['abnormal']:+.0%}" for _, r in top5.iloc[::-1].iterrows()))
        print(f"        drop top 5 -> mean={rest.mean():>7.2%} "
              f"plain t={t_rest:>5.2f} clustered t={ct_rest:>5.2f} "
              f"hit={float((rest > 0).mean()):.1%} (n={len(rest)})")

    # ---------- (2) extraction quality ----------
    print("\n[2] EXTRACTION QUALITY of 'long' labels")
    longs = mentions[mentions["dir"] == "long"]
    print(f"  'long' mentions: {len(longs)} rows, "
          f"{longs['tweet_id'].nunique()} distinct tweets")

    from serenity_tracker import fetch_archive
    arch = fetch_archive()
    arch["id"] = arch["id"].astype(str)
    arch = arch.set_index("id")
    print(f"  archive fetched: {len(arch)} tweets")

    txt = arch["text"].astype(str)
    frac_http = float(txt.str.contains("http", case=False).mean())
    print(f"  tweets containing 'http' (URL): {frac_http:.1%}")
    print("  NOTE: an earlier classifier substring-matched 'tp' inside 'http' (any")
    print("  tweet with a URL could never be labeled 'long') -- FIXED via word-")
    print("  boundary regexes + URL stripping; negation guards added later.")

    # which keywords actually trigger the 'long' label? (surface forms)
    long_tweets = longs.drop_duplicates("tweet_id").merge(
        arch[["text"]], left_on="tweet_id", right_index=True, how="left")
    n_missing = int(long_tweets["text"].isna().sum())
    trig_counts: dict[str, int] = {}
    weak_only = 0
    for _, r in long_tweets.dropna(subset=["text"]).iterrows():
        lt, _ = triggers(r["text"])
        for w in lt:
            trig_counts[w] = trig_counts.get(w, 0) + 1
        if lt and not any(w.startswith(s) for s in STRONG_LONG for w in lt):
            weak_only += 1
    n_ok = len(long_tweets) - n_missing
    print(f"  'long' tweets matched to archive text: {n_ok} (missing {n_missing})")
    print("  trigger keyword counts (a tweet can hit several):")
    for w, c in sorted(trig_counts.items(), key=lambda kv: -kv[1]):
        print(f"    {w:<12}: {c:>5} ({c / n_ok:.0%})")
    print(f"  triggered ONLY by weak words (long/entry/calls/position, "
          f"no bought/buy/adding/accumulat): {weak_only} ({weak_only / n_ok:.0%})")

    multi = longs.groupby("tweet_id")["ticker"].nunique()
    frac_multi3 = float((multi >= 3).mean())
    print(f"  'long' rows inherit the tweet-level label for EVERY ticker in the "
          f"tweet; {frac_multi3:.0%} of long tweets carry >=3 tickers")

    # random sample of 15 'long' mentions for hand judging
    print("\n  --- RANDOM SAMPLE: 15 mentions labeled 'long' (seed 123) ---")
    samp = longs.sample(min(15, len(longs)), random_state=123).sort_values("time")
    for _, r in samp.iterrows():
        text = arch["text"].get(str(r["tweet_id"]), "<not in archive>")
        lt, et = triggers(text)
        print(f"  [{str(r['time'])[:16]}] ${r['ticker']} "
              f"(long-trigs={lt} exit-trigs={et})")
        print(f"    {sanitize(text)}")

    # the decision-relevant sample: first_long tweets actually used as events
    print("\n  --- SAMPLE: 12 of the first_long EVENT tweets used in the study "
          "(seed 99) ---")
    fl_used = fl_df.drop_duplicates("ticker")[["ticker", "tweet_utc"]]
    key = mentions[mentions["dir"] == "long"].merge(
        fl_used, left_on=["ticker", "time"], right_on=["ticker", "tweet_utc"])
    samp2 = key.sample(min(12, len(key)), random_state=99).sort_values("time")
    for _, r in samp2.iterrows():
        text = arch["text"].get(str(r["tweet_id"]), "<not in archive>")
        lt, et = triggers(text)
        print(f"  [{str(r['time'])[:16]}] ${r['ticker']} "
              f"(long-trigs={lt} exit-trigs={et})")
        print(f"    {sanitize(text)}")


if __name__ == "__main__":
    main()
