"""Always-available statistical forecaster. Used as Kronos fallback and as a control.

Strategy: drift = mean of last `lookback` log-returns; vol = std of same.
Forecast for horizon h: close_T * exp(drift * h). Vol scales with sqrt(h).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class NaiveDriftForecaster:
    name = "naive_drift"
    version = "0.1.0"

    def forecast(
        self,
        ohlcv: pd.DataFrame,
        lookback: int = 60,
        horizon: int = 5,
    ) -> pd.DataFrame:
        if ohlcv.empty:
            return pd.DataFrame()

        rows = []
        for symbol, sub in ohlcv.sort_values(["symbol", "ts"]).groupby("symbol"):
            sub = sub.tail(lookback + 1)
            if len(sub) < 5:
                continue
            closes = sub["close"].to_numpy(dtype=float)
            log_ret = np.diff(np.log(closes))
            drift = float(np.mean(log_ret))
            vol = float(np.std(log_ret, ddof=1)) if len(log_ret) > 1 else 0.0
            ts = pd.to_datetime(sub["ts"]).reset_index(drop=True)
            asof = ts.iloc[-1]
            last_close = closes[-1]

            # Estimate calendar spacing from observed bars; default 1 day.
            diffs = ts.diff().dropna()
            step = diffs.median() if len(diffs) > 0 else pd.Timedelta(days=1)

            for h in range(1, horizon + 1):
                pred_close = float(last_close * np.exp(drift * h))
                rows.append(
                    {
                        "symbol": symbol,
                        "asof": asof,
                        "horizon": h,
                        "target_ts": asof + step * h,
                        "pred_close": pred_close,
                        "pred_return": float(pred_close / last_close - 1.0),
                        "pred_vol": vol * np.sqrt(h),
                        "model_name": self.name,
                        "model_version": self.version,
                    }
                )
        return pd.DataFrame(rows)
