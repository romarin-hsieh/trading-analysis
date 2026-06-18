"""How many times does the recommended combo actually TRADE in 2025? (out-of-sample activity audit)

The user's practical question: looking at 2025 data, how many "出手" (moves/trades) does the
recommended 5-sleeve combo make? This ingests 2025 (now fully available) and counts the REAL
trade activity per sleeve over the 2025 calendar year — entries, exits, regime flips, rebalances —
so the operational burden is a measured number, not a guess.

Note: 2025 is fully OUT OF SAMPLE (all research was on 2015-2024). Trade COUNT/cadence is structural
(monthly rebalance + daily stop-exits) and reliable; 2025 P&L is not the point here and is not claimed.

Run: uv run python scripts/trades_2025.py
"""

from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import sector_strategies as ss  # noqa: E402

from trading_analysis.data.connectors.yahoo import YahooConnector  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

Y0, Y1 = "2025-01-01", "2025-12-31"
UNIV = sorted(set(s for v in ss.SECTORS.values() for s in v) | {"TQQQ", "QQQ", "GLD", "IEF", "TLT", "SPY", "BIL"})


def ingest_2025(store: DuckStore) -> str:
    """Fetch through today for the combo universe so 2025 (and any 2026) bars are present."""
    latest = store.load_close_pivot(["SPY"], column="adj_close")
    have_to = latest.index.max() if len(latest) else None
    if have_to is not None and have_to >= pd.Timestamp("2025-12-31"):
        return f"already have through {have_to.date()}"
    conn = YahooConnector()
    df = conn.fetch_ohlcv(UNIV, start=_dt.date(2024, 6, 1), end=_dt.date(2026, 6, 19), bar="1d")
    store.upsert_ohlcv(df)
    new = store.load_close_pivot(["SPY"], column="adj_close")
    return f"ingested -> now through {new.index.max().date()}"


def in25(s: pd.Series | pd.DataFrame):
    return s.loc[(s.index >= Y0) & (s.index <= Y1)]


def main():
    store = DuckStore("./data")
    print(ingest_2025(store))
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    px = ss._px(allsyms)
    spy = ss._spy().reindex(px.index).ffill()

    print("=" * 86)
    print(f"COMBO TRADE ACTIVITY in 2025 (out-of-sample) — data through {px.index.max().date()}")
    print("=" * 86)

    # ---- Sleeve 1: equity momentum (top-10, monthly entries, daily stop-exits, regime-gated) ----
    held = ss.momentum_trend_direction(px, spy, k=10, hold=21, regime=True)
    h25 = in25(held)
    delta = held.diff().fillna(0.0)
    buys, sells = (delta == 1), (delta == -1)
    nb, nsl = int(in25(buys).sum().sum()), int(in25(sells).sum().sum())
    rebal_grid = pd.Series(False, index=px.index)
    rebal_grid.iloc[::21] = True
    n_rebal_25 = int(in25(rebal_grid).sum())
    avg_pos = float(h25.sum(axis=1).mean())
    names = sorted(set(h25.columns[(in25(buys) | in25(sells)).any(axis=0)]))
    print("SLEEVE 1 — equity momentum (top-10 RS, regime-gated):")
    print(f"  monthly rebalance dates in 2025 : {n_rebal_25}")
    print(f"  buys (entries) : {nb}    sells (exits) : {nsl}    TOTAL fills : {nb + nsl}")
    print(f"  avg names held : {avg_pos:.1f} / 10     distinct names traded : {len(names)}")

    # ---- Sleeve 2: defensive dual-momentum (top-4, monthly rotation bonds/gold) ----
    dsyms = list(dict.fromkeys([*allsyms, "IEF", "TLT", "GLD"]))
    pxd = ss._px(dsyms)
    lp = np.log(pxd)
    mom12 = (lp.shift(1) - lp.shift(252))
    defv = ["IEF", "TLT", "GLD"]
    spy_off = ~((spy > spy.rolling(200, min_periods=150).mean()).shift(1).reindex(pxd.index).ffill().fillna(False))
    reb = pd.Series(False, index=pxd.index)
    reb.iloc[::21] = True
    sel_prev, switches, k = set(), 0, 4
    switch_dates = []
    for t in pxd.index[reb.to_numpy()]:
        row = mom12.loc[t]
        drow = row[defv].dropna().sort_values(ascending=False)
        if bool(spy_off.loc[t]):
            win = [s for s in drow.index if drow[s] > 0][:k]
        else:
            rk = row[[s for s in allsyms if s in pxd.columns]].dropna().sort_values(ascending=False)
            bar = float(drow.max()) if len(drow) else 0.0
            win = [s for s in rk.index[:k] if rk[s] > 0 and rk[s] > bar]
            if len(win) < k and len(drow):
                win += [s for s in drow.index if drow[s] > 0][: k - len(win)]
        cur = set(win)
        if Y0 <= str(t.date()) <= Y1 and cur != sel_prev:
            switches += 1
            switch_dates.append(str(t.date()))
        sel_prev = cur
    print("SLEEVE 2 — defensive dual-momentum (top-4, monthly):")
    print(f"  monthly rotation decisions in 2025 : {n_rebal_25}    roster CHANGES : {switches}")

    # ---- Sleeve 3: leveraged trend (TQQQ on while QQQ>200SMA) ----
    qqq = ss._px(["QQQ"]).iloc[:, 0]
    on = (qqq > qqq.rolling(200, min_periods=150).mean()).shift(1).reindex(qqq.index).ffill().fillna(False)
    flips = on.ne(on.shift()).fillna(False)
    nflip = int(in25(flips).sum())
    state_end = "ON (in TQQQ)" if bool(in25(on).iloc[-1]) else "OFF (in cash)"
    print("SLEEVE 3 — leveraged trend (TQQQ gated by QQQ 200-SMA):")
    print(f"  on/off flips in 2025 : {nflip}    year-end state : {state_end}")

    # ---- Sleeves 4&5: gold / bonds — buy-and-hold, only monthly risk-parity reweights ----
    print("SLEEVE 4&5 — gold (GLD) / bonds (IEF): held continuously; only the ~monthly")
    print(f"  risk-parity reweight touches them. risk-parity rebalances in 2025 : {n_rebal_25}")

    # ---- headline ----
    print("-" * 86)
    total_fills = nb + nsl + switches + nflip
    print("OUT-OF-SAMPLE 2025 ACTIVITY SUMMARY:")
    print(f"  decision cadence              : MONTHLY ~{n_rebal_25} rebalance dates (not daily/intraday)")
    print(f"  equity-momentum fills         : {nb + nsl}  ({nb} buys + {nsl} sells across {len(names)} names)")
    print(f"  defensive roster changes      : {switches}")
    print(f"  leveraged-trend regime flips  : {nflip}")
    print(f"  ==> total discrete trades 2025: ~{total_fills}  (plus ~{n_rebal_25} monthly weight tweaks)")
    print("  i.e. a LOW-TOUCH monthly book: rebalance once a month, ~a handful of fills each time,")
    print("  exits can fire intramonth on a 50-SMA break or a market-regime flip. Not day-trading.")
    print("=" * 86)


if __name__ == "__main__":
    main()
