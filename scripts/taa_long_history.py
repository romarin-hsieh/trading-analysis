"""TAA over a MULTI-DECADE history — the decisive test of the docs/11 "extend history" claim.

scripts/taa_dual_momentum.py found Antonacci/Faber TAA underperforming 60/40 and SPY on
2015-24, and the commit claimed that is a *window artifact*: 2015-24 is one long US-equity
bull decade — the single worst environment for defensive/trend TAA — so the 10y window
structurally buries it. That is a falsifiable claim. Here we falsify-or-confirm it.

Same two strategies, same rules, but on a universe with a genuine multi-cycle record built
from dividend-adjusted Vanguard mutual-fund proxies that exist back to the mid-1990s, so the
window now CONTAINS the dot-com bust (2000-02) and the GFC (2007-09) — the bear markets a
defensive TAA is supposed to earn its keep in.

  RISKY     VFINX(US) VGTSX(intl) VEIEX(EM) VGSIX(REIT)
  DEFENSIVE VUSTX(long-tsy) VBMFX(total-bond) VFITX(interm-tsy)
  CASH      VFISX(short-tsy ~ T-bills)

If TAA's full-cycle Sharpe >> its 2015-24 Sharpe AND it protects capital in 2000-02 / 2008,
the claim is CONFIRMED: the strategy was never dead, the test window was. If it still loses
to 60/40 over the full cycle, the claim is REFUTED and the data-ceiling is deeper than window.

Run: uv run python scripts/taa_long_history.py
"""

from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.connectors.yahoo import YahooConnector  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

RISKY = ["VFINX", "VGTSX", "VEIEX", "VGSIX"]
DEFENSIVE = ["VUSTX", "VBMFX", "VFITX"]
CASH = "VFISX"
US = "VFINX"  # long-history buy&hold benchmark (S&P 500 total return)
COST = 0.0010
START = "1995-01-01"

# named historical episodes — the whole point is to see TAA behave across regimes
EPISODES = {
    "dot-com bust 00-02": ("2000-03-01", "2002-12-31"),
    "recovery   03-07": ("2003-01-01", "2007-09-30"),
    "GFC        07-09": ("2007-10-01", "2009-03-31"),
    "QE bull    09-19": ("2009-04-01", "2019-12-31"),
    "tested win 15-24": ("2015-01-01", "2024-12-31"),
    "covid+22   20-24": ("2020-01-01", "2024-12-31"),
}


def ingest_if_missing(s: DuckStore) -> None:
    have = set(s.list_symbols())
    need = [t for t in RISKY + DEFENSIVE + [CASH] if t not in have]
    if not need:
        return
    logger.remove()
    print(f"ingesting long-history proxies: {need}")
    conn = YahooConnector()
    df = conn.fetch_ohlcv(need, start=_dt.date(1995, 1, 1), end=_dt.date(2025, 1, 1), bar="1d")
    s.upsert_ohlcv(df)


def stats(r):
    r = r.dropna()
    if len(r) < 60:
        return {"CAGR": np.nan, "Sharpe": np.nan, "MDD": np.nan, "Calmar": np.nan}
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def weighted_ret(w, ret):
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return (w.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * COST


def episode_total(r, a, b):
    seg = r[(r.index >= a) & (r.index <= b)].dropna()
    if len(seg) < 20:
        return np.nan
    return (1 + seg).prod() - 1


def main():
    s = DuckStore("./data")
    ingest_if_missing(s)
    syms = RISKY + DEFENSIVE + [CASH]
    px = s.load_close_pivot(syms, column="adj_close").ffill()
    px = px.dropna(how="all")
    # restrict to dates where all RISKY exist (EM/REIT/intl funds start ~1996)
    first_all = px[RISKY].dropna().index.min()
    px = px.loc[px.index >= first_all]
    ret = px.pct_change()
    mom12 = px / px.shift(252) - 1
    reb = pd.Series(False, index=px.index)
    reb.iloc[::21] = True

    print("=" * 100)
    print(f"MULTI-DECADE TAA — Antonacci + Faber, {px.index.min().date()}..{px.index.max().date()}, net 10bps")
    print(f"universe risk={RISKY} def={DEFENSIVE} cash={CASH}")
    print("=" * 100)

    # Antonacci dual momentum, K=2 (only 4 risk assets)
    K = 2
    sel = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    for t in px.index[reb.to_numpy()]:
        m = mom12.loc[t]
        cm = m[CASH] if np.isfinite(m[CASH]) else 0.0
        winners = [a for a in RISKY if np.isfinite(m[a]) and m[a] > cm and m[a] > 0]
        winners = sorted(winners, key=lambda a: m[a], reverse=True)[:K]
        if len(winners) < K:
            dwin = sorted([d for d in DEFENSIVE if np.isfinite(m[d]) and m[d] > 0],
                          key=lambda a: m[a], reverse=True)
            winners += dwin[: K - len(winners)]
        if winners:
            sel.loc[t, winners] = 1.0
    held = sel.where(pd.Series(reb.to_numpy(), index=px.index), np.nan).ffill().fillna(0.0)
    anto = weighted_ret(held.div(held.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0), ret)

    # Faber GTAA: each risk asset 1/N while above its 10mo (200d) SMA, else cash
    sma = px.rolling(200, min_periods=150).mean()
    above = (px[RISKY] > sma[RISKY]).shift(1, fill_value=False).reindex(px.index, fill_value=False)
    fw = above.astype(float) / len(RISKY)
    fw = fw.where(pd.Series(reb.to_numpy(), index=px.index), np.nan).ffill().fillna(0.0)
    fw = fw.reindex(columns=px.columns, fill_value=0.0)
    faber = weighted_ret(fw, ret)

    # 60/40 (US equity / total bond) + US buy&hold
    w6040 = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    w6040[US] = 0.6
    w6040["VBMFX"] = 0.4
    bench = weighted_ret(w6040.where(pd.Series(reb.to_numpy(), index=px.index)).ffill().fillna(0.0), ret)
    usbh = ret[US]

    streams = {"Antonacci dual-mom": anto, "Faber GTAA": faber,
               "60/40 (US/bond)": bench, "US buy&hold": usbh}

    print(f"{'strategy':20s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'Calmar':>7s}")
    full = {}
    for name, r in streams.items():
        st = stats(r.iloc[252:])
        full[name] = st
        print(f"{name:20s} {st['CAGR']:+7.1%} {st['Sharpe']:+7.2f} {st['MDD']:+7.1%} {st['Calmar']:7.2f}")

    # the decisive table: total return through each historical episode (does TAA protect?)
    print("-" * 100)
    print("TOTAL RETURN through each episode (the capital-protection test):")
    hdr = "  ".join(f"{k.split()[0]:>10s}" for k in EPISODES)
    print(f"{'strategy':20s} {hdr}")
    for name, r in streams.items():
        cells = "  ".join(f"{episode_total(r, a, b):>+10.1%}" if np.isfinite(episode_total(r, a, b))
                           else f"{'n/a':>10s}" for a, b in EPISODES.values())
        print(f"{name:20s} {cells}")

    print("-" * 100)
    sh_full = full["Faber GTAA"]["Sharpe"]
    # compare to the short-window result recorded in the prior commit (Faber 0.74)
    print(f"VERDICT: Faber full-cycle Sharpe {sh_full:+.2f} vs 2015-24-only 0.74 (prior commit).")
    print("If full-cycle >> 0.74 AND TAA is green where buy&hold is deep red in 00-02/07-09,")
    print("the 'extend history' claim is CONFIRMED: TAA was buried by the window, not dead.")
    print("=" * 100)


if __name__ == "__main__":
    main()
