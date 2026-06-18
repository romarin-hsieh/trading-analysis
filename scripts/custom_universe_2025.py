"""Apply the recommended momentum 'rulebook' to a USER-SUPPLIED universe and estimate 2025.

The user gave ~140 tickers and asked: if we operate the strategy's rules on THESE names, what would
2025 have made? We run the exact momentum_trend_direction engine (top-K by 6m-skip-1m momentum among
uptrend names, daily 50-SMA stop, SPY-200SMA regime gate) on the supplied universe for 2025.

  >>> THE CENTRAL HONESTY PROBLEM <<<
This watchlist is a hand-picked list of names that are hot AS OF 2026 (ASTS, RKLB, OKLO, IONQ, CRCL,
PLTR, HIMS, ...). Backtesting a momentum strategy on a universe curated in hindsight to contain the
biggest movers is TEXTBOOK selection / look-ahead bias. To expose it we also report the equal-weight
buy&hold of the WHOLE universe in 2025 — if that is already huge, the 'profit' is the universe being
pre-selected winners, NOT the strategy. We also flag names that were 2025 IPOs (no momentum history,
so the strategy could not have ranked them early-year). The strategy number here is an UPPER-BIASED
illustration, not a forward estimate.

Run: uv run python scripts/custom_universe_2025.py
"""

from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.connectors.yahoo import YahooConnector  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

Y0, Y1 = "2025-01-01", "2025-12-31"
UNIVERSE = [
    "ASTS", "RIVN", "PL", "ONDS", "RDW", "AVAV", "MDB", "ORCL", "TSM", "RKLB", "CRM", "NVDA", "AVGO",
    "AMZN", "GOOG", "META", "NFLX", "LEU", "SMR", "CRWV", "IONQ", "PLTR", "HIMS", "TSLA", "VST", "KTOS",
    "MELI", "SOFI", "RBRK", "EOSE", "CEG", "TMDX", "GRAB", "RBLX", "IREN", "OKLO", "PATH", "INTR", "SE",
    "KSPI", "LUNR", "HOOD", "APP", "CHYM", "NU", "COIN", "CRCL", "IBKR", "CCJ", "UUUU", "VRT", "ETN",
    "MSFT", "ADBE", "FIG", "PANW", "CRWD", "DDOG", "DUOL", "ZETA", "AXON", "ALAB", "LRCX", "BWXT", "UMAC",
    "MP", "RR", "ABBV", "ACHR", "AMD", "AXP", "BA", "BAC", "BE", "BRK-B", "CAT", "CIFR", "CLSK", "COST",
    "CSCO", "CVX", "DGRO", "DIA", "DIVO", "FTNT", "GEV", "GLD", "GLW", "GS", "HD", "HON", "HUT", "IBM",
    "INTU", "IWM", "JEPI", "JEPQ", "JNJ", "JOBY", "JPM", "KO", "MA", "MAIN", "MCD", "MMM", "MRK", "MU",
    "NET", "O", "PG", "PM", "POWL", "QBTS", "QQQ", "RGTI", "RTX", "SCHD", "SLV", "SMCI", "SNDK", "SPY",
    "TRV", "UNG", "UNH", "USO", "V", "VIG", "VNQ", "VTV", "VUG", "VYM", "WDC", "WFC", "WMT", "WULF",
    "XOM", "ZS",
]


def ingest(store: DuckStore) -> list[str]:
    conn = YahooConnector()
    have = set(store.list_symbols())
    need = [t for t in UNIVERSE if t not in have or
            (store.load_close_pivot([t], column="adj_close").index.max() < pd.Timestamp("2025-12-30"))]
    if need:
        print(f"ingesting/refreshing {len(need)} tickers ...")
        for i in range(0, len(need), 30):
            chunk = need[i:i + 30]
            try:
                df = conn.fetch_ohlcv(chunk, start=_dt.date(2023, 1, 1), end=_dt.date(2026, 6, 19), bar="1d")
                if not df.empty:
                    store.upsert_ohlcv(df)
            except Exception:
                for t in chunk:                       # individual fallback for bad-batch tickers
                    try:
                        df = conn.fetch_ohlcv([t], start=_dt.date(2023, 1, 1), end=_dt.date(2026, 6, 19), bar="1d")
                        if not df.empty:
                            store.upsert_ohlcv(df)
                    except Exception:
                        pass
    px = store.load_close_pivot(UNIVERSE, column="adj_close")
    return [t for t in UNIVERSE if t in px.columns]


def seg(s):
    return s.loc[(s.index >= Y0) & (s.index <= Y1)].dropna()


def stat(r):
    r = seg(r)
    if len(r) < 20:
        return None
    eq = (1 + r).cumprod()
    return float(eq.iloc[-1] - 1), sharpe(r), r.std() * np.sqrt(252), max_drawdown(eq)


def main():
    store = DuckStore("./data")
    avail = ingest(store)
    px = ss._px(avail)
    spy = ss._spy().reindex(px.index).ffill()
    missing = [t for t in UNIVERSE if t not in avail]

    # eligibility: had >=150 trading days of history by 2025-01-01 (else too-new to rank early 2025)
    cutoff = px.loc[px.index < pd.Timestamp(Y0)]
    hist = cutoff.notna().sum()
    new_2025 = sorted([t for t in avail if hist.get(t, 0) < 150])

    print("=" * 96)
    print(f"USER UNIVERSE -- momentum rulebook applied, 2025 (data through {px.index.max().date()})")
    print(f"  supplied {len(UNIVERSE)} tickers | data found {len(avail)} | missing {len(missing)}")
    print(f"  2025-IPO / <150d history (strategy could NOT rank these early-year): {len(new_2025)}")
    if missing:
        print(f"  no data: {', '.join(missing)}")
    if new_2025:
        print(f"  too-new: {', '.join(new_2025)}")
    print("=" * 96)

    # equal-weight buy&hold of the WHOLE universe = the 'how hot was this hand-picked list' benchmark
    ew = px.pct_change(fill_method=None).mean(axis=1)
    voo = store.load_close_pivot(["VOO"], column="adj_close").reindex(px.index).ffill().iloc[:, 0].pct_change().fillna(0.0)

    rows = []
    for k in (10, 5):
        held = ss.momentum_trend_direction(px, spy, k=k, hold=21, regime=True)
        res = ss.run_engine(px, held, spy, k)
        rows.append((f"momentum rulebook k={k}", res.returns, held))
    rows.append(("equal-wt buy&hold (UNIVERSE)", ew, None))
    rows.append(("VOO (S&P 500)", voo, None))

    print(f"{'strategy':30s} {'2025 ret':>9s} {'Sharpe':>8s} {'vol':>7s} {'MDD':>8s}  {'$10k->':>10s}")
    print("-" * 96)
    for name, r, _ in rows:
        st = stat(r)
        if st:
            tot, sh, vol, mdd = st
            print(f"{name:30s} {tot:+9.1%} {sh:+8.2f} {vol:7.1%} {mdd:+8.1%}  ${10000*(1+tot):>9,.0f}")

    # which names did the k=10 rulebook actually hold during 2025
    held10 = rows[0][2]
    h25 = seg(held10)
    names = sorted(h25.columns[(h25 > 0).any(axis=0)])
    print("-" * 96)
    print(f"names the k=10 rulebook actually held in 2025 ({len(names)}): {', '.join(names)}")

    print("=" * 96)
    print("HONEST READ: the gap between 'momentum rulebook' and 'equal-wt buy&hold (UNIVERSE)' is the only")
    print("part attributable to the STRATEGY. The universe itself is hand-picked 2026-hot names, so most of")
    print("any profit is SELECTION BIAS (you knew which names to list because they already ran), not the rules.")
    print("This is an upper-biased illustration on a hindsight universe -- NOT a forward/ deployable estimate.")
    print("=" * 96)


if __name__ == "__main__":
    main()
