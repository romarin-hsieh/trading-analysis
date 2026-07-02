"""Telegram exit-discipline monitor -- daily multi-dimensional exit votes for your holdings.

Computes the 5 exit votes from scripts/multi_exit.py for each configured holding and pushes a
Telegram message after the US close. Calibration from the backtest (2015-2026): the vote stack is
an ADVISORY confirmation filter, not an auto-trade signal -- on QQQ buy&hold beat every mechanical
stop; on 3x-leverage the bias(V3)/position(V2) dimensions cut MDD -82%->-58/-44% at real CAGR cost.
Read >=3/5 votes as "regime deteriorating, review the position", >=4/5 as "strong exit signal".

Setup (once):
  1. Telegram: talk to @BotFather -> /newbot -> copy the token. Then message your bot once and get
     your chat id from https://api.telegram.org/bot<TOKEN>/getUpdates
  2. env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PORTFOLIO (e.g. "QQQ,NVDA,TQQQ,PLTR")
  3. Run manually:  uv run python scripts/notify/exit_monitor.py
     or via GitHub Actions cron: .github/workflows/monitor.yml (add the two secrets in repo settings)

Standalone by design (yfinance direct) so the Actions runner needs no DuckDB store.
"""

from __future__ import annotations

import contextlib
import os
import sys

import numpy as np
import pandas as pd


def _fetch(tickers: list[str], days: int = 600) -> pd.DataFrame:
    import yfinance as yf
    raw = yf.download(tickers=[*tickers, "SPY", "^VIX"], period=f"{days}d", interval="1d",
                      auto_adjust=True, progress=False, group_by="ticker", threads=True)
    out = {}
    for t in [*tickers, "SPY", "^VIX"]:
        with contextlib.suppress(Exception):
            out[t] = raw[t]["Close"].dropna()
    return pd.DataFrame(out).ffill()


def _rsi(px: pd.Series, n: int = 14) -> pd.Series:
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def votes_today(c: pd.Series, vix: pd.Series) -> dict:
    sma50 = c.rolling(50).mean()
    bias = float((c.iloc[-1] - sma50.iloc[-1]) / sma50.iloc[-1])
    r14 = float(_rsi(c).iloc[-1])
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    hist = macd - macd.ewm(span=9, adjust=False).mean()
    dd = float(c.iloc[-1] / c.rolling(252, min_periods=20).max().iloc[-1] - 1.0)
    vix_pct = float(vix.rolling(252).rank(pct=True).iloc[-1])
    v = {
        "V1 VIX panic": vix_pct > 0.80,
        "V2 pos loss>10%": dd < -0.10,
        "V3 bias<-5%": bias < -0.05,
        "V4 RSI<45": r14 < 45,
        "V5 MACD down": bool(hist.iloc[-1] < 0 and hist.diff().iloc[-1] < 0),
    }
    return {"votes": v, "n": sum(v.values()), "bias": bias, "rsi": r14, "dd": dd, "vix_pct": vix_pct}


def send_telegram(text: str) -> bool:
    import requests
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("[dry-run] TELEGRAM_BOT_TOKEN/CHAT_ID not set; message below:\n" + text)
        return False
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": text, "parse_mode": "HTML"}, timeout=30)
    return r.ok


def main() -> int:
    tickers = [t.strip().upper() for t in os.environ.get("PORTFOLIO", "QQQ,TQQQ").split(",") if t.strip()]
    px = _fetch(tickers)
    if "^VIX" not in px.columns or "SPY" not in px.columns:
        print("fetch failed")
        return 1
    vix, spy = px["^VIX"], px["SPY"]
    regime_on = bool(spy.iloc[-1] > spy.rolling(200).mean().iloc[-1])

    lines = [f"<b>Exit discipline -- {px.index[-1].date()}</b>",
             f"SPY vs 200SMA: {'ABOVE (risk-on)' if regime_on else 'BELOW (risk-off)'} | "
             f"VIX {vix.iloc[-1]:.1f} (1y pct {vix.rolling(252).rank(pct=True).iloc[-1]:.0%})", ""]
    alerts = 0
    for t in tickers:
        if t not in px.columns:
            lines.append(f"{t}: no data")
            continue
        s = votes_today(px[t].dropna(), vix)
        mark = "OK" if s["n"] <= 1 else ("WATCH" if s["n"] == 2 else ("REVIEW" if s["n"] == 3 else "EXIT?"))
        alerts += int(s["n"] >= 3)
        fired = ", ".join(k for k, on in s["votes"].items() if on) or "-"
        lines.append(f"<b>{t}</b> [{mark}] votes {s['n']}/5 | bias {s['bias']:+.1%} | "
                     f"RSI {s['rsi']:.0f} | dd {s['dd']:+.1%}\n   fired: {fired}")
    lines.append("")
    lines.append("calibration: >=3/5 review, >=4/5 strong exit. Advisory only (backtest: mechanical"
                 " stops underperform B&H on QQQ; they matter on leverage).")
    send_telegram("\n".join(lines))
    print(f"done: {len(tickers)} tickers, {alerts} alert(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
