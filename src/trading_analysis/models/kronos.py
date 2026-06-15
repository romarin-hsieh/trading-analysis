"""Kronos foundation model wrapper.

Behavior:
- If the `kronos` Python package or `model.Kronos` is importable, use it.
- Otherwise, fall back to NaiveDriftForecaster so MVP still produces forecasts.

Expected layout when Kronos is installed (from https://github.com/shiyu-coder/Kronos):
    from model import Kronos, KronosTokenizer, KronosPredictor

The wrapper caches forecasts to {cache_dir}/forecasts/<key>.parquet to avoid
re-running expensive inference during repeated backtests.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from trading_analysis.models.naive import NaiveDriftForecaster
from trading_analysis.observability.logging import get_logger

log = get_logger(__name__)


_HF_MODELS = {
    "mini": ("NeoQuasar/Kronos-mini", "NeoQuasar/Kronos-Tokenizer-base"),
    "small": ("NeoQuasar/Kronos-small", "NeoQuasar/Kronos-Tokenizer-base"),
    "base": ("NeoQuasar/Kronos-base", "NeoQuasar/Kronos-Tokenizer-base"),
}


def _try_import_kronos():
    """Return (Kronos, KronosTokenizer, KronosPredictor) or None."""
    try:
        from model import Kronos, KronosPredictor, KronosTokenizer  # type: ignore
        return Kronos, KronosTokenizer, KronosPredictor
    except Exception:
        try:
            from kronos import Kronos, KronosPredictor, KronosTokenizer  # type: ignore
            return Kronos, KronosTokenizer, KronosPredictor
        except Exception:
            return None


class KronosForecaster:
    """Wrapper around Kronos with caching and naive fallback."""

    name = "kronos"
    version = "0.1.0"

    def __init__(
        self,
        size: str = "mini",
        device: str = "cpu",
        cache_dir: Path | str | None = None,
        sample_count: int = 1,
        temperature: float = 1.0,
        top_p: float = 0.9,
    ):
        if size not in _HF_MODELS:
            raise ValueError(f"Unknown kronos size: {size}. Options: {list(_HF_MODELS)}")
        self.size = size
        self.device = device
        self.sample_count = sample_count
        self.temperature = temperature
        self.top_p = top_p
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/kronos_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.version = f"0.1.0-{size}"

        kronos = _try_import_kronos()
        self._predictor = None
        if kronos is None:
            log.warning(
                "kronos package not importable — using NaiveDriftForecaster fallback. "
                "Install kronos from https://github.com/shiyu-coder/Kronos to enable."
            )
            self._fallback = NaiveDriftForecaster()
        else:
            Kronos, KronosTokenizer, KronosPredictor = kronos
            model_id, tok_id = _HF_MODELS[size]
            try:
                log.info(f"Loading Kronos: {model_id} (device={device})")
                tokenizer = KronosTokenizer.from_pretrained(tok_id)
                model = Kronos.from_pretrained(model_id)
                self._predictor = KronosPredictor(
                    model, tokenizer, device=device, max_context=512
                )
                self._fallback = None
            except Exception as e:
                log.warning(f"Failed to load Kronos ({e}); using NaiveDriftForecaster fallback.")
                self._fallback = NaiveDriftForecaster()

    # ---------- public API ----------

    def forecast(
        self,
        ohlcv: pd.DataFrame,
        lookback: int = 256,
        horizon: int = 5,
    ) -> pd.DataFrame:
        if self._predictor is None:
            return self._fallback.forecast(ohlcv, lookback=lookback, horizon=horizon)

        rows = []
        for symbol, sub in ohlcv.sort_values(["symbol", "ts"]).groupby("symbol"):
            sub = sub.tail(lookback)
            if len(sub) < max(32, horizon + 1):
                continue
            cache_key = self._cache_key(symbol, sub, horizon)
            cached = self._read_cache(cache_key)
            if cached is not None:
                rows.append(cached)
                continue
            try:
                forecast_df = self._run_kronos(symbol, sub, horizon)
            except Exception as e:
                log.warning(f"kronos inference failed for {symbol}: {e}; falling back")
                forecast_df = self._naive_for_symbol(symbol, sub, horizon)
            self._write_cache(cache_key, forecast_df)
            rows.append(forecast_df)

        return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

    # ---------- internals ----------

    def _run_kronos(self, symbol: str, sub: pd.DataFrame, horizon: int) -> pd.DataFrame:
        x_df = sub[["open", "high", "low", "close", "volume"]].astype(float).reset_index(drop=True)
        x_ts = pd.to_datetime(sub["ts"]).reset_index(drop=True)
        # Future timestamps: extend with same calendar spacing
        last_ts = x_ts.iloc[-1]
        diffs = x_ts.diff().dropna()
        step = diffs.median() if len(diffs) > 0 else pd.Timedelta(days=1)
        y_ts = pd.Series([last_ts + step * (i + 1) for i in range(horizon)])

        pred_df = self._predictor.predict(  # type: ignore[union-attr]
            df=x_df,
            x_timestamp=x_ts,
            y_timestamp=y_ts,
            pred_len=horizon,
            T=self.temperature,
            top_p=self.top_p,
            sample_count=self.sample_count,
        )

        # Kronos returns columns including 'close'; some versions also return 'volume' etc.
        last_close = float(x_df["close"].iloc[-1])
        out = []
        for h, (_, row) in enumerate(pred_df.iterrows(), start=1):
            pred_close = float(row.get("close", row.get("Close", last_close)))
            out.append(
                {
                    "symbol": symbol,
                    "asof": last_ts,
                    "horizon": h,
                    "target_ts": y_ts.iloc[h - 1],
                    "pred_close": pred_close,
                    "pred_return": pred_close / last_close - 1.0,
                    "pred_vol": None,
                    "model_name": f"kronos-{self.size}",
                    "model_version": self.version,
                }
            )
        return pd.DataFrame(out)

    def _naive_for_symbol(self, symbol: str, sub: pd.DataFrame, horizon: int) -> pd.DataFrame:
        f = NaiveDriftForecaster().forecast(sub, lookback=len(sub), horizon=horizon)
        f["symbol"] = symbol
        f["model_name"] = f"kronos-{self.size}-fallback"
        return f

    def _cache_key(self, symbol: str, sub: pd.DataFrame, horizon: int) -> str:
        last_ts = pd.to_datetime(sub["ts"]).iloc[-1].isoformat()
        n = len(sub)
        h = hashlib.sha1(f"{symbol}|{last_ts}|{n}|{horizon}|{self.size}".encode()).hexdigest()[:16]
        return f"{symbol}_{h}"

    def _read_cache(self, key: str) -> pd.DataFrame | None:
        path = self.cache_dir / f"{key}.parquet"
        if path.exists():
            return pd.read_parquet(path)
        return None

    def _write_cache(self, key: str, df: pd.DataFrame) -> None:
        if df is None or df.empty:
            return
        path = self.cache_dir / f"{key}.parquet"
        df.to_parquet(path, index=False)


# Numpy is imported only to keep type hints local; remove if mypy complains.
__all__ = ["KronosForecaster"]
_ = np  # silence unused-import lint
