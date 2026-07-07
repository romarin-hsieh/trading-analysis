"""TR-02 addendum -- v1.2-A4 / F6 v2: the risk-matched STATIC control for the Markov gate.

Cederburg-O'Doherty-Wang-Yan (JFE 2020): volatility-managed portfolios do not systematically
beat their unmanaged (static-exposure) counterparts. TR-02 credited the Markov gate with
"MDD halved" while running ~59% average exposure -- this addendum runs the control TR-02
lacked: a CONSTANT 59%-QQQ / 41%-BIL book (no regime model at all), plus a vol-matched static.

Comparison is under the v1.2-B3 honest convention (flat fraction earns BIL, Sharpe on excess-
over-BIL) for ALL rows, so the Markov row is recomputed here the same way (its TR-02 headline
+11.19%/0.84/-18.92% was computed pre-B3 with cash-earns-0; documented, both shown).

Verdict rule (pre-committed): the Markov gate only keeps its PARTIAL "risk value" if it beats
the static control on MDD at comparable Sharpe, or on Sharpe at comparable MDD. If static
matches it, the regime model adds nothing over a constant dial (Cederburg's tempered read).

Run: uv run python scripts/tests/tr02b_static_control.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

from trading_analysis.backtest.metrics import cagr, max_drawdown  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

COST = 0.0005


def ex_sharpe(r, bil):
    x = (r - bil).dropna()
    return float(x.mean() / x.std() * np.sqrt(252))


def main():
    store = DuckStore("./data")
    qqq = store.load_close_pivot(["QQQ"], column="adj_close").iloc[:, 0].pct_change()
    bil = (store.load_close_pivot(["BIL"], column="adj_close").iloc[:, 0]
           .reindex(qqq.index).ffill().pct_change().fillna(0.0))

    # reproduce the Markov walk-forward exposure series via the TR-02 script's own machinery
    import tr02_markov_regime as tr02
    # preferred: the TR-02 script's exposed helper; else rebuild the minimal faithful pipeline
    sig = tr02.walk_forward_signal("QQQ") if hasattr(tr02, "walk_forward_signal") else None
    if sig is None:
        # minimal faithful re-implementation of TR-02's monthly walk-forward filtered signal
        from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
        r = qqq.dropna().loc["2015-01-01":]
        month = pd.Series(r.index.to_period("M"), index=r.index)
        sig = pd.Series(np.nan, index=r.index)
        state = 0.0
        prev = None
        for t in r.index:
            m = month.loc[t]
            if m != prev:
                hist = r.loc[:t].iloc[:-1]
                if len(hist) >= 750:
                    try:
                        mod = MarkovRegression(hist.to_numpy() * 100, k_regimes=2,
                                               trend="c", switching_variance=True)
                        res = mod.fit(disp=False)
                        fp = res.filtered_marginal_probabilities[:, :]
                        # low-vol regime = the one with smaller sigma2
                        low = int(np.argmin([res.params[-2], res.params[-1]]))
                        state = float(fp[-1, low] > 0.5)
                    except Exception:
                        pass
                prev = m
            sig.loc[t] = state
        sig = sig.fillna(0.0)

    sig = sig.reindex(qqq.index).fillna(0.0)
    oos = sig.loc["2017-12-29":].index
    q, b, s_ = qqq.loc[oos].fillna(0.0), bil.loc[oos], sig.loc[oos]

    expo = float(s_.mean())
    p = s_.shift(1).fillna(0.0)
    markov = p * q + (1 - p) * b - p.diff().abs().fillna(0.0) * COST
    static = expo * q + (1 - expo) * b                     # constant dial, ~zero turnover
    # vol-matched static: scale to Markov's realized vol
    scale = float((markov - b).std() / (q - b).std())
    static_vm = scale * q + (1 - scale) * b
    bh = q

    print("=" * 96)
    print("TR-02b  RISK-MATCHED STATIC CONTROL (Cederburg / F6 v2) -- all rows under B3 convention")
    print(f"OOS {oos[0].date()}..{oos[-1].date()} | Markov avg exposure = {expo:.0%} | vol-match scale = {scale:.2f}")
    print("=" * 96)
    print(f"{'book':34s} {'CAGR':>8s} {'exSharpe':>9s} {'MDD':>8s} {'exits/yr':>9s}")
    yrs = len(q) / 252
    for name, r_ in (("QQQ buy&hold", bh), (f"Markov gate (expo {expo:.0%})", markov),
                     (f"STATIC {expo:.0%} QQQ / rest BIL", static),
                     (f"static vol-matched ({scale:.2f}x)", static_vm)):
        eq = (1 + r_).cumprod()
        nex = float(p.diff().clip(lower=0).sum() / yrs) if "Markov" in name else 0.0
        print(f"{name:34s} {cagr(eq):>+8.2%} {ex_sharpe(r_, b):>+9.2f} {max_drawdown(eq):>+8.1%} {nex:>9.1f}")
    print("-" * 96)
    m_eq, s_eq = (1 + markov).cumprod(), (1 + static).cumprod()
    dm, ds = max_drawdown(m_eq), max_drawdown(s_eq)
    sm, ss = ex_sharpe(markov, b), ex_sharpe(static, b)
    beats = (dm > ds + 0.01 and sm >= ss - 0.05) or (sm > ss + 0.1 and dm >= ds - 0.01)
    print(f"VERDICT: Markov {'BEATS' if beats else 'DOES NOT BEAT'} the static control "
          f"(MDD {dm:+.1%} vs {ds:+.1%}; exSharpe {sm:+.2f} vs {ss:+.2f}).")
    print("If not beaten: the regime model's 'MDD halving' is reproducible with a constant dial --")
    print("Cederburg's tempered read; TR-02's PARTIAL narrows to 'vol identification only'.")
    print("=" * 96)


if __name__ == "__main__":
    main()
