"""Event-study backtest of Serenity (@aleabitoreddit) stock calls.

Primary event: first tweet classified 'long' per ticker.
Secondary event: first mention per ticker.
Entry: close of first trading day STRICTLY AFTER the tweet's US/Eastern calendar
date (no intraday lookahead). Forward +5/+21/+63 trading-day returns, abnormal
vs QQQ over the identical window. Decisive control: random-timing placebo on the
same tickers (K=20 draws each, seed 42) with a ticker-bootstrap percentile.

Caveats printed inline: archive span 2025-07-02..2026-07-02 is a raging AI bull
market; direction labels come from noisy keyword matching.
"""

from loguru import logger

logger.remove()

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

DATA = Path("./data")
HORIZONS = [5, 21, 63]
K_PLACEBO = 20
N_BOOT = 1000
SEED = 42
SPAN_START = pd.Timestamp("2025-07-02")
SPAN_END = pd.Timestamp("2026-07-02")


def entry_position(tweet_utc: pd.Timestamp, market_dates: pd.DatetimeIndex) -> int:
    """Index of first trading day strictly after the tweet's ET calendar date."""
    et_date = pd.Timestamp(tweet_utc.tz_convert("America/New_York").date())
    return int(market_dates.searchsorted(et_date, side="right"))


def event_returns(
    events: pd.Series,
    px: pd.DataFrame,
    market_dates: pd.DatetimeIndex,
    qqq: np.ndarray,
) -> tuple[pd.DataFrame, dict[int, int]]:
    """Per-event forward raw/abnormal returns for each horizon.

    Returns (frame, n_no_entry_price) where frame has one row per
    (ticker, horizon) with a full window and valid prices at both ends.
    """
    rows = []
    no_entry = dict.fromkeys(HORIZONS, 0)
    for ticker, ts in events.items():
        if ticker not in px.columns:
            continue
        p = px[ticker].to_numpy()
        pos = entry_position(ts, market_dates)
        for h in HORIZONS:
            ex = pos + h
            if pos >= len(market_dates) or ex >= len(market_dates):
                continue  # window truncated by end of data
            if np.isnan(p[pos]) or np.isnan(p[ex]):
                no_entry[h] += 1  # no usable price at entry or exit (IPO/delist/halt)
                continue
            raw = p[ex] / p[pos] - 1.0
            bench = qqq[ex] / qqq[pos] - 1.0
            rows.append(
                {
                    "ticker": ticker,
                    "tweet_utc": ts,
                    "entry_date": market_dates[pos],
                    "horizon": h,
                    "raw": raw,
                    "abnormal": raw - bench,
                }
            )
    return pd.DataFrame(rows), no_entry


def stats_table(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for h in HORIZONS:
        sub = df[df["horizon"] == h]
        n = len(sub)
        if n == 0:
            continue
        ab = sub["abnormal"].to_numpy()
        se = ab.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
        out.append(
            {
                "H": h,
                "n": n,
                "mean_raw": sub["raw"].mean(),
                "med_raw": sub["raw"].median(),
                "mean_abn": ab.mean(),
                "med_abn": np.median(ab),
                "hit_abn": (ab > 0).mean(),
                "t_abn": ab.mean() / se if se and se > 0 else np.nan,
            }
        )
    return pd.DataFrame(out)


def print_stats(label: str, tab: pd.DataFrame) -> None:
    print(f"\n--- {label} ---")
    print(f"{'H':>4} {'n':>5} {'meanRaw':>9} {'medRaw':>9} {'meanAbn':>9} "
          f"{'medAbn':>9} {'hit%':>6} {'t':>7}")
    for _, r in tab.iterrows():
        print(
            f"{int(r['H']):>4} {int(r['n']):>5} {r['mean_raw']:>8.2%} "
            f"{r['med_raw']:>8.2%} {r['mean_abn']:>8.2%} {r['med_abn']:>8.2%} "
            f"{r['hit_abn']:>6.1%} {r['t_abn']:>7.2f}"
        )


def main() -> None:
    events = pd.read_parquet(DATA / "_serenity_events.parquet")
    covered = json.loads((DATA / "_serenity_covered.json").read_text())

    store = DuckStore("./data")
    px = store.load_close_pivot(sorted(set(covered) | {"QQQ"}), column="adj_close")
    market_dates = px.index[px["QQQ"].notna()]
    px = px.loc[market_dates]  # restrict to QQQ trading days; NO ffill anywhere
    qqq = px["QQQ"].to_numpy()

    ev_cov = events[events.index.isin(covered)]
    first_long = ev_cov["first_long"].dropna().sort_index()
    first_mention = ev_cov["first_mention"].dropna().sort_index()

    print("=" * 76)
    print("SERENITY CALLS EVENT-STUDY BACKTEST (entry: next-day close after ET date)")
    print("Archive span 2025-07-02..2026-07-02 -- a raging AI bull market.")
    print("Direction labels are keyword-matched (noisy). Abnormal = ticker - QQQ.")
    print("=" * 76)

    print("\n[COVERAGE]")
    print(f"tickers in events file          : {len(events)}")
    print(f"tickers with usable prices      : {len(ev_cov)} (covered list: {len(covered)})")
    print(f"  with a first_long event       : {len(first_long)}")
    print(f"  with a first_mention event    : {len(first_mention)}")

    fl_df, fl_noentry = event_returns(first_long, px, market_dates, qqq)
    fm_df, _fm_noentry = event_returns(first_mention, px, market_dates, qqq)

    for h in HORIZONS:
        n_full = int((fl_df["horizon"] == h).sum())
        trunc = len(first_long) - n_full - fl_noentry[h]
        print(
            f"  first_long H={h:>2}: full-window n={n_full:>3} | "
            f"truncated-by-data-end={trunc:>3} | no-price-at-entry/exit={fl_noentry[h]}"
        )

    tab_long = stats_table(fl_df)
    print_stats("PRIMARY: first_long events (t-stat: plain SE; windows overlap in "
                "calendar time, so clustering is NOT corrected -- t is optimistic)",
                tab_long)

    tab_mention = stats_table(fm_df)
    print_stats("SECONDARY: first_mention events (same caveats)", tab_mention)

    # ---------------- PLACEBO: random timing on the SAME tickers ----------------
    rs = np.random.RandomState(SEED)
    span_mask = (market_dates >= SPAN_START) & (market_dates <= SPAN_END)
    span_pos = np.flatnonzero(span_mask)

    print("\n--- PLACEBO (decisive control): K=20 random entry dates per event "
          "ticker, seed 42 ---")
    print("Separates HIS TIMING from HIS UNIVERSE drifting up in this bull tape.")
    placebo_summary = {}
    for h in HORIZONS:
        ev_h = fl_df[fl_df["horizon"] == h]
        tickers_h = sorted(ev_h["ticker"].unique())
        draws = {}
        for t in tickers_h:
            p = px[t].to_numpy()
            elig = [
                pos for pos in span_pos
                if pos + h < len(market_dates)
                and not np.isnan(p[pos]) and not np.isnan(p[pos + h])
            ]
            if not elig:
                continue
            picks = rs.choice(elig, size=K_PLACEBO, replace=True)
            raw = p[picks + h] / p[picks] - 1.0
            bench = qqq[picks + h] / qqq[picks] - 1.0
            draws[t] = raw - bench
        mat = np.array([draws[t] for t in sorted(draws)])  # (n_tickers, K)
        placebo_mean = mat.mean()
        real_mean = ev_h["abnormal"].mean()

        n_tick = mat.shape[0]
        boot_means = np.empty(N_BOOT)
        for b in range(N_BOOT):
            rows = rs.randint(0, n_tick, size=n_tick)
            cols = rs.randint(0, K_PLACEBO, size=n_tick)
            boot_means[b] = mat[rows, cols].mean()
        pct = (boot_means < real_mean).mean() * 100.0
        placebo_summary[h] = (placebo_mean, pct, real_mean, n_tick)
        print(
            f"  H={h:>2}: real mean abn={real_mean:>8.2%} | placebo mean abn="
            f"{placebo_mean:>8.2%} | timing edge={real_mean - placebo_mean:>8.2%} | "
            f"real is at pctile {pct:5.1f} of {N_BOOT} bootstrap placebo means "
            f"({n_tick} tickers)"
        )

    # ---------------- Sub-period split (first_long, +21d abnormal) ----------------
    print("\n--- SUB-PERIOD: first_long events, +21d abnormal ---")
    sub21 = fl_df[fl_df["horizon"] == 21].copy()
    et_dates = sub21["tweet_utc"].dt.tz_convert("America/New_York")
    sub21["period"] = np.where(et_dates < pd.Timestamp("2026-01-01",
                                                       tz="America/New_York"),
                               "2025H2", "2026H1")
    for per, grp in sub21.groupby("period"):
        ab = grp["abnormal"]
        print(f"  {per}: n={len(grp):>3} | mean abn={ab.mean():>8.2%} | "
              f"median abn={ab.median():>8.2%} | hit={float((ab > 0).mean()):.1%}")

    # ---------------- Top/bottom 10 by +63d abnormal ----------------
    sub63 = fl_df[fl_df["horizon"] == 63].sort_values("abnormal")
    print("\n--- BOTTOM 10 first_long events by +63d abnormal ---")
    for _, r in sub63.head(10).iterrows():
        print(f"  {r['ticker']:<6} entry {r['entry_date'].date()}  "
              f"raw {r['raw']:>8.2%}  abn {r['abnormal']:>8.2%}")
    print("--- TOP 10 first_long events by +63d abnormal ---")
    for _, r in sub63.tail(10).iloc[::-1].iterrows():
        print(f"  {r['ticker']:<6} entry {r['entry_date'].date()}  "
              f"raw {r['raw']:>8.2%}  abn {r['abnormal']:>8.2%}")

    print("\n[NOTE] One event per ticker, but event windows overlap heavily in")
    print("calendar time (most calls cluster in the same AI-bull regime), so the")
    print("plain-SE t-stats overstate independence. The placebo percentile is the")
    print("more honest test of TIMING skill vs universe drift.")


if __name__ == "__main__":
    main()
