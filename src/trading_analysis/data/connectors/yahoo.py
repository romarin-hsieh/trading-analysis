"""Yahoo Finance connector via yfinance. Free, daily bars, no key required.

Note on rate limits: yfinance scrapes Yahoo and is occasionally throttled. We batch
download up to 50 symbols per call and back off on failure.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)


class YahooConnector:
    name = "yahoo"

    _BAR_MAP = {"1d": "1d", "1wk": "1wk", "1mo": "1mo"}

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _download(
        self, symbols: list[str], start: date, end: date | None, interval: str
    ) -> pd.DataFrame:
        import yfinance as yf

        return yf.download(
            tickers=symbols,
            start=start.isoformat(),
            end=end.isoformat() if end else None,
            interval=interval,
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
        )

    def fetch_ohlcv(
        self,
        symbols: list[str],
        start: date,
        end: date | None = None,
        bar: str = "1d",
    ) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame()
        interval = self._BAR_MAP.get(bar)
        if interval is None:
            raise ValueError(f"Unsupported bar: {bar}")

        all_frames: list[pd.DataFrame] = []
        for i in range(0, len(symbols), self.batch_size):
            chunk = symbols[i : i + self.batch_size]
            log.info(f"yahoo: fetching {len(chunk)} symbols [{chunk[0]}..{chunk[-1]}]")
            raw = self._download(chunk, start, end, interval)
            all_frames.append(self._normalize(raw, chunk, bar))

        df = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
        return df

    @staticmethod
    def _normalize(raw: pd.DataFrame, symbols: list[str], bar: str) -> pd.DataFrame:
        """Yahoo returns either a single-level index (1 ticker) or a 2-level
        column index (multi-ticker). Normalize to long form.
        """
        if raw is None or raw.empty:
            return pd.DataFrame()

        rows: list[pd.DataFrame] = []
        if isinstance(raw.columns, pd.MultiIndex):
            # group_by="ticker" => columns are (ticker, field)
            tickers = sorted({c[0] for c in raw.columns})
            for t in tickers:
                if t not in raw.columns.get_level_values(0):
                    continue
                sub = raw[t].copy()
                sub = sub.rename(
                    columns={
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Adj Close": "adj_close",
                        "Volume": "volume",
                    }
                )
                sub["symbol"] = t
                sub.index.name = "ts"
                sub = sub.reset_index()
                rows.append(sub)
        else:
            sub = raw.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )
            sub["symbol"] = symbols[0]
            sub.index.name = "ts"
            sub = sub.reset_index()
            rows.append(sub)

        df = pd.concat(rows, ignore_index=True)
        df["bar"] = bar
        df = df.dropna(subset=["open", "close"])
        # Ensure adj_close exists
        if "adj_close" not in df.columns:
            df["adj_close"] = df["close"]
        df["adj_close"] = df["adj_close"].fillna(df["close"])
        keep = ["symbol", "ts", "open", "high", "low", "close", "volume", "adj_close", "bar"]
        return df[keep]
