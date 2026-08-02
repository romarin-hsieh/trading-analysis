"""Daily options-chain snapshot collector (SPY/QQQ) -- the time-sensitive data dimension.

Why: TR-09 (Black-Scholes) and every options mechanism (GEX/dealer-gamma, VRP, IV-skew
predictors) are N/A for us because there is NO free point-in-time options history -- you
cannot download the past, only record the present. Every day not collected is lost forever.
This script snapshots the front ~6 expirations of SPY and QQQ chains from yfinance (free,
delayed -- fine for daily research) into small gzipped CSVs committed to the repo.

Grossman-Stiglitz framing: this is us PAYING an information cost (in time) to open the
options dimension. After ~6-12 months of snapshots, first candidate tests: dealer net-GEX
as a volatility/pinning regime signal (vs the Nagel controls), VRP (implied - realized).

Storage: collected/options/{SYMBOL}/{YYYY-MM-DD}.csv.gz  (~50-150 KB/day total)
Run:     uv run python scripts/collect/options_snapshot.py   (or standalone: pip install yfinance)
"""

from __future__ import annotations

import datetime as dt
import gzip
import io
import os
import sys

import pandas as pd

SYMBOLS = ("SPY", "QQQ")
N_EXPIRIES = 6
OUT_ROOT = os.path.join("collected", "options")


def snapshot_symbol(sym: str, today: str) -> str | None:
    import yfinance as yf

    tk = yf.Ticker(sym)
    expiries = list(tk.options or [])[:N_EXPIRIES]
    if not expiries:
        print(f"[{sym}] no expiries returned; skip")
        return None
    spot = None
    try:
        spot = float(tk.fast_info["last_price"])
    except Exception:
        h = tk.history(period="1d")
        if len(h):
            spot = float(h["Close"].iloc[-1])
    frames = []
    cols = ["contractSymbol", "strike", "lastPrice", "bid", "ask", "volume",
            "openInterest", "impliedVolatility", "inTheMoney"]
    for exp in expiries:
        try:
            ch = tk.option_chain(exp)
        except Exception as e:
            print(f"[{sym}] {exp}: {str(e)[:80]}")
            continue
        for side, df in (("C", ch.calls), ("P", ch.puts)):
            if df is None or df.empty:
                continue
            d = df[[c for c in cols if c in df.columns]].copy()
            d.insert(0, "type", side)
            d.insert(0, "expiry", exp)
            frames.append(d)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "spot", spot)
    out.insert(0, "asof", today)
    ddir = os.path.join(OUT_ROOT, sym)
    os.makedirs(ddir, exist_ok=True)
    path = os.path.join(ddir, f"{today}.csv.gz")
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    print(f"[{sym}] {len(out)} contracts x {len(expiries)} expiries -> {path} "
          f"({os.path.getsize(path)//1024} KB)")
    return path


def main() -> int:
    today = dt.date.today().isoformat()
    wrote = [p for s in SYMBOLS if (p := snapshot_symbol(s, today))]
    if not wrote:
        print("nothing collected (holiday / API down) -- not an error")
    return 0


if __name__ == "__main__":
    sys.exit(main())
