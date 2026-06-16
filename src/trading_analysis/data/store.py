"""DuckDB-backed local store. Holds OHLCV bars and forecasts in parquet partitions.

Partition layout:
    {cache_dir}/ohlcv/symbol=AAPL/bar=1d/data.parquet
    {cache_dir}/forecasts/symbol=AAPL/model=kronos-mini/data.parquet
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from trading_analysis.data.schema import CANONICAL_COLUMNS, OHLCVFrame
from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)


class DuckStore:
    """Thin facade around DuckDB + parquet partitions.

    Designed for a single-process MVP. For multi-process safety later, swap
    parquet writes for an actual DuckDB file with a serialized writer.
    """

    def __init__(self, cache_dir: Path | str):
        self.cache_dir = Path(cache_dir)
        self.ohlcv_dir = self.cache_dir / "ohlcv"
        self.forecasts_dir = self.cache_dir / "forecasts"
        self.fundamentals_dir = self.cache_dir / "fundamentals"
        for d in (self.ohlcv_dir, self.forecasts_dir, self.fundamentals_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(":memory:")

    # ---------- OHLCV ----------

    def _ohlcv_path(self, symbol: str, bar: str) -> Path:
        return self.ohlcv_dir / f"symbol={symbol.upper()}" / f"bar={bar}" / "data.parquet"

    def upsert_ohlcv(self, df: pd.DataFrame) -> int:
        """Insert/replace bars. Idempotent on (symbol, ts, bar).

        Returns the number of rows after upsert (per symbol+bar partition).
        """
        if df.empty:
            return 0
        df = OHLCVFrame.validate_frame(df.copy())
        df["ts"] = pd.to_datetime(df["ts"], utc=False)
        total = 0
        for (symbol, bar), part in df.groupby(["symbol", "bar"], sort=False):
            path = self._ohlcv_path(symbol, bar)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = pd.read_parquet(path)
                merged = pd.concat([existing, part], ignore_index=True)
                merged = merged.drop_duplicates(subset=["symbol", "ts", "bar"], keep="last")
                merged = merged.sort_values("ts").reset_index(drop=True)
            else:
                merged = part.sort_values("ts").reset_index(drop=True)
            merged[CANONICAL_COLUMNS].to_parquet(path, index=False)
            total += len(merged)
            log.debug(f"upserted {symbol} {bar}: {len(part)} new -> {len(merged)} total")
        return total

    def load_ohlcv(
        self,
        symbols: list[str],
        bar: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> pd.DataFrame:
        """Load bars for the given symbols. Missing symbols are skipped silently."""
        frames = []
        for s in symbols:
            path = self._ohlcv_path(s, bar)
            if path.exists():
                frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame(columns=CANONICAL_COLUMNS)
        df = pd.concat(frames, ignore_index=True)
        df["ts"] = pd.to_datetime(df["ts"])
        if start is not None:
            df = df[df["ts"] >= pd.Timestamp(start)]
        if end is not None:
            df = df[df["ts"] <= pd.Timestamp(end)]
        return df.sort_values(["symbol", "ts"]).reset_index(drop=True)

    def load_close_pivot(
        self,
        symbols: list[str],
        bar: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
        column: str = "close",
    ) -> pd.DataFrame:
        """Return wide-form DataFrame: index=ts, columns=symbol, values=column."""
        long = self.load_ohlcv(symbols, bar=bar, start=start, end=end)
        if long.empty:
            return pd.DataFrame()
        wide = long.pivot_table(index="ts", columns="symbol", values=column, aggfunc="last")
        return wide.sort_index()

    def list_symbols(self, bar: str = "1d") -> list[str]:
        out: list[str] = []
        if not self.ohlcv_dir.exists():
            return out
        for symdir in self.ohlcv_dir.iterdir():
            if (
                symdir.is_dir()
                and symdir.name.startswith("symbol=")
                and (symdir / f"bar={bar}" / "data.parquet").exists()
            ):
                out.append(symdir.name.removeprefix("symbol="))
        return sorted(out)

    def latest_ts(self, symbol: str, bar: str = "1d") -> datetime | None:
        path = self._ohlcv_path(symbol, bar)
        if not path.exists():
            return None
        df = pd.read_parquet(path, columns=["ts"])
        if df.empty:
            return None
        return pd.to_datetime(df["ts"]).max().to_pydatetime()

    # ---------- Forecasts ----------

    def _forecast_path(self, symbol: str, model: str) -> Path:
        return self.forecasts_dir / f"symbol={symbol.upper()}" / f"model={model}" / "data.parquet"

    def upsert_forecasts(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        required = {"symbol", "asof", "horizon", "target_ts", "pred_close", "model_name"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"forecast frame missing: {missing}")
        df = df.copy()
        df["asof"] = pd.to_datetime(df["asof"])
        df["target_ts"] = pd.to_datetime(df["target_ts"])
        total = 0
        for (symbol, model), part in df.groupby(["symbol", "model_name"], sort=False):
            path = self._forecast_path(symbol, model)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = pd.read_parquet(path)
                merged = pd.concat([existing, part], ignore_index=True)
                merged = merged.drop_duplicates(
                    subset=["symbol", "asof", "horizon", "model_name"], keep="last"
                )
            else:
                merged = part
            merged.to_parquet(path, index=False)
            total += len(merged)
        return total

    def load_forecasts(
        self,
        symbols: list[str],
        model: str | None = None,
    ) -> pd.DataFrame:
        frames = []
        for s in symbols:
            sdir = self.forecasts_dir / f"symbol={s.upper()}"
            if not sdir.exists():
                continue
            for mdir in sdir.iterdir():
                if not mdir.is_dir() or not mdir.name.startswith("model="):
                    continue
                m = mdir.name.removeprefix("model=")
                if model is not None and m != model:
                    continue
                path = mdir / "data.parquet"
                if path.exists():
                    frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    # ---------- Fundamentals (alt-data, point-in-time by `as_of` = SEC filed date) ----------

    def _fundamentals_path(self, symbol: str) -> Path:
        return self.fundamentals_dir / f"symbol={symbol.upper()}" / "data.parquet"

    def upsert_fundamentals(self, df: pd.DataFrame) -> int:
        """Insert/replace fundamental facts. Idempotent on (symbol, tag, period_end, form, as_of)."""
        if df.empty:
            return 0
        total = 0
        for symbol, part in df.groupby("symbol", sort=False):
            path = self._fundamentals_path(symbol)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                merged = pd.concat([pd.read_parquet(path), part], ignore_index=True)
                merged = merged.drop_duplicates(
                    subset=["symbol", "tag", "period_end", "form", "as_of"], keep="last")
            else:
                merged = part
            merged.to_parquet(path, index=False)
            total += len(merged)
        return total

    def load_fundamentals(self, symbols: list[str]) -> pd.DataFrame:
        frames = [pd.read_parquet(self._fundamentals_path(s)) for s in symbols
                  if self._fundamentals_path(s).exists()]
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        df["as_of"] = pd.to_datetime(df["as_of"])
        df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")
        return df

    # ---------- Insider transactions (alt-data, point-in-time by `as_of` = SEC filing date) ----------

    def _insider_path(self, symbol: str) -> Path:
        return (self.cache_dir / "insider" / f"symbol={symbol.upper()}" / "data.parquet")

    def upsert_insider(self, df: pd.DataFrame) -> int:
        """Insert/replace aggregated insider rows. Idempotent on (symbol, as_of)."""
        if df.empty:
            return 0
        total = 0
        for symbol, part in df.groupby("symbol", sort=False):
            path = self._insider_path(symbol)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                merged = pd.concat([pd.read_parquet(path), part], ignore_index=True)
                merged = merged.drop_duplicates(subset=["symbol", "as_of"], keep="last")
            else:
                merged = part
            merged.to_parquet(path, index=False)
            total += len(merged)
        return total

    def load_insider(self, symbols: list[str]) -> pd.DataFrame:
        frames = [pd.read_parquet(self._insider_path(s)) for s in symbols
                  if self._insider_path(s).exists()]
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        df["as_of"] = pd.to_datetime(df["as_of"])
        return df

    # ---------- DuckDB ad-hoc query ----------

    def query(self, sql: str) -> pd.DataFrame:
        """Run a DuckDB SQL query against on-disk parquet files.

        The store registers the current ohlcv parquet glob as `ohlcv` view.
        """
        glob = (self.ohlcv_dir / "*" / "*" / "data.parquet").as_posix()
        self._con.execute(f"CREATE OR REPLACE VIEW ohlcv AS SELECT * FROM '{glob}'")
        return self._con.execute(sql).fetchdf()

    def close(self) -> None:
        self._con.close()
