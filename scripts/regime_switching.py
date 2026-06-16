"""Does regime-conditional factor switching (from the applicability map) actually beat
unconditional momentum and the simple 200-SMA gate?

The applicability map (docs/09) said momentum's IC survives FDR only in {bull, low-vol, normal}.
Here we BUILD that as a rule and test it honestly against simpler baselines, with a sub-period
split and the rigor gate. All regime labels are lagged/leak-free (regime.conditional_attribution).

Honesty note: the {bull, low-vol, normal} rule was INFORMED by the in-sample map, so the full
window is partly in-sample; the 2016-19 vs 2020-24 split + PSR-vs-1/N are the real evidence.

Run: uv run python scripts/regime_switching.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
from sector_strategies import _px, _spy  # noqa: E402

from trading_analysis.backtest.deflated_sharpe import probabilistic_sharpe_ratio  # noqa: E402
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.backtest.spa import spa_pvalue  # noqa: E402
from trading_analysis.config import load_config  # noqa: E402
from trading_analysis.regime.conditional_attribution import (  # noqa: E402
    drawdown_regime,
    trend_regime,
    vol_regime,
)

COST = 0.0010
SPLITS = {"2016-2019": ("2016-01-01", "2019-12-31"), "2020-2024": ("2020-01-01", "2024-12-31")}


def momentum_topk(px, k=10, lb=126, skip=21, hold=21):
    lp = np.log(px)
    mom = (lp.shift(skip) - lp.shift(lb)).shift(1)
    rebal = pd.Series(False, index=px.index)
    rebal.iloc[::hold] = True
    topk = mom.rank(axis=1, ascending=False, method="first") <= k
    return topk.where(rebal).ffill().fillna(False)


def perf(held, ret):
    """Equal-weight among held names (fully invested when >=1 held, else cash), net of turnover."""
    w = held.astype(float).div(held.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return (w.shift(1) * ret).sum(axis=1).fillna(0.0) - turn * COST


def stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = max_drawdown(eq)
    c = cagr(eq)
    return {"CAGR": c, "Sharpe": sharpe(r), "MDD": mdd, "Calmar": c / abs(mdd) if mdd else np.nan}


def main():
    cfg = load_config("configs/study.yaml")
    stocks = [s for s in cfg.universe.symbols if s != "SPY"]
    px = _px([*stocks, "IEF"]).ffill()
    spy = _spy().reindex(px.index).ffill()
    ret = px.pct_change()
    stock_px = px[stocks]

    topk = momentum_topk(stock_px).reindex(columns=px.columns, fill_value=False)
    bull = (trend_regime(spy) == "bull").reindex(px.index).fillna(False)
    good = ((trend_regime(spy) == "bull")
            & (vol_regime(spy) != "high_vol")
            & (drawdown_regime(spy) == "normal")).reindex(px.index).fillna(False)

    def gate(mask, to_bonds=False):
        held = topk.copy()
        held[stocks] = topk[stocks].mul(mask.astype(int), axis=0).astype(bool)
        if to_bonds:
            held["IEF"] = ~mask
        return held

    variants = {
        "A unconditional momentum": topk,
        "B 200SMA-gated (bull)": gate(bull),
        "C applicability-cond (->cash)": gate(good),
        "D applicability-cond (->bonds)": gate(good, to_bonds=True),
    }
    # 1/N buy&hold benchmark (always invested, equal-weight stocks)
    ones = pd.DataFrame(True, index=px.index, columns=stocks).reindex(columns=px.columns, fill_value=False)
    bench = perf(ones, ret)

    print("=" * 84)
    print("REGIME-CONDITIONAL FACTOR SWITCHING — us_study, net of 10bps turnover")
    print("=" * 84)
    print(f"{'variant':32s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'Calmar':>7s} {'16-19 Sh':>9s} {'20-24 Sh':>9s}")
    rets = {}
    for name, held in variants.items():
        r = perf(held, ret)
        rets[name] = r
        s = stats(r)
        sh = {}
        for sp, (a, b) in SPLITS.items():
            m = (r.index >= a) & (r.index <= b)
            sh[sp] = sharpe(r[m]) if m.sum() > 60 else np.nan
        print(f"{name:32s} {s['CAGR']:+7.1%} {s['Sharpe']:+7.2f} {s['MDD']:+7.1%} {s['Calmar']:7.2f} "
              f"{sh['2016-2019']:+9.2f} {sh['2020-2024']:+9.2f}")
    bs = stats(bench)
    print(f"{'(1/N buy&hold benchmark)':32s} {bs['CAGR']:+7.1%} {bs['Sharpe']:+7.2f} {bs['MDD']:+7.1%} {bs['Calmar']:7.2f}")

    # rigor gate on the best-Calmar variant
    best = max(rets, key=lambda k: stats(rets[k])["Calmar"])
    r = rets[best].loc[rets[best].index >= "2016-01-01"]
    bench_pp = float(bench.loc[r.index].mean() / bench.loc[r.index].std())
    print("-" * 84)
    print(f"RIGOR GATE on best-Calmar variant: {best}")
    print(f"  PSR P(Sharpe>0)        : {probabilistic_sharpe_ratio(r.to_numpy(), 0.0):.3f}")
    print(f"  PSR P(Sharpe>1/N)      : {probabilistic_sharpe_ratio(r.to_numpy(), bench_pp):.3f}  (the bar that matters)")
    d = (r - bench.loc[r.index]).to_numpy().reshape(-1, 1)
    print(f"  SPA P(no edge vs 1/N)  : {spa_pvalue(d):.3f}  (HIGH => no edge over buy&hold)")
    print("=" * 84)
    print("  VERDICT: compare C/D Calmar to B (simple gate) and to A (unconditional). If C/D ~ B,")
    print("  the fancy multi-regime conditioning adds little over the plain 200SMA gate (honest).")
    print("=" * 84)


if __name__ == "__main__":
    main()
