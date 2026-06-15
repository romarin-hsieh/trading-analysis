"""Round-3 backtest rigor harness — point the O1/O3 apparatus at our OWN strategy.

Runs the Minervini screen across a parameter grid, then asks the questions a single
backtest cannot answer:
  - PBO (CSCV): is the best config a selection artifact?
  - Deflated Sharpe: does the best Sharpe survive the number of configs we tried?
  - Fair benchmarks: does timing/selection beat equal-weight buy-&-hold of the SAME names
    (not just cap-weighted SPY)?
  - Factor attribution: is there alpha, or is it market/size/value/momentum beta?

Run: uv run python scripts/backtest_study.py
"""

from __future__ import annotations

import itertools

import pandas as pd
from loguru import logger

from trading_analysis.backtest.deflated_sharpe import (
    deflated_sharpe_ratio,
    min_track_record_length,
    probabilistic_sharpe_ratio,
)
from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
from trading_analysis.backtest.pbo import probability_of_backtest_overfitting
from trading_analysis.config import load_config
from trading_analysis.data.store import DuckStore

logger.remove()  # quiet the per-run INFO lines

CFG_PATH = "configs/study.yaml"


def _grid():
    rs = [60.0, 70.0, 80.0]
    within_high = [0.25, 0.35]
    rising = [21, 42]
    for r, w, rl in itertools.product(rs, within_high, rising):
        yield {"min_rs": r, "within_high_pct": w, "rising_lookback": rl}


def run_grid():
    from trading_analysis.api import backtest_strategy

    base = load_config(CFG_PATH)
    rows, cols = {}, []
    for params in _grid():
        cfg = base.model_copy(deep=True)
        cfg.strategy.params = params
        res = backtest_strategy(cfg, write_report=False)
        lbl = f"rs{int(params['min_rs'])}_wh{int(params['within_high_pct']*100)}_rl{params['rising_lookback']}"
        rows[lbl] = res.returns
        cols.append({"label": lbl, **params,
                     "sharpe": sharpe(res.returns), "cagr": cagr(res.equity),
                     "maxdd": max_drawdown(res.equity),
                     "total_ret": float(res.equity.iloc[-1] / res.equity.iloc[0] - 1.0)})
    mat = pd.DataFrame(rows).dropna()
    return mat, pd.DataFrame(cols), base


def benchmarks(base):
    store = DuckStore(base.data.cache_dir)
    syms = [s for s in base.universe.symbols if s != base.backtest.benchmark]
    px = store.load_close_pivot(syms, start=base.data.start, end=base.data.end,
                                column="adj_close").ffill()
    ew_ret = px.pct_change().mean(axis=1).fillna(0.0)            # equal-weight, always invested
    spy = store.load_close_pivot([base.backtest.benchmark], start=base.data.start,
                                 end=base.data.end, column="adj_close").ffill().iloc[:, 0]
    spy_ret = spy.pct_change().fillna(0.0)
    return ew_ret, spy_ret


def attribution(strat_ret):
    try:
        from trading_analysis.factors.attribution import factor_alpha, load_ff_factors
        ff = load_ff_factors(start="2015-01-01")
        fac_cols = [c for c in ["Mkt-RF", "SMB", "HML", "UMD"] if c in ff.columns]
        out = factor_alpha(strat_ret, ff[fac_cols], rf=ff["RF"])
        return out
    except Exception as e:  # network / data issues — don't fail the whole study
        return {"error": str(e)[:160]}


def main():
    mat, summary, base = run_grid()
    ew_ret, spy_ret = benchmarks(base)

    best = summary.sort_values("sharpe", ascending=False).iloc[0]
    best_ret = mat[best["label"]]

    # per-period (daily) Sharpe across configs -> trial dispersion for the DSR bar
    pp_sr = mat.apply(lambda c: c.mean() / c.std(ddof=1))
    n_trials = mat.shape[1]
    dsr = deflated_sharpe_ratio(best_ret.to_numpy(), n_trials=n_trials,
                                trials_sharpe_std=float(pp_sr.std(ddof=1)))
    psr = probabilistic_sharpe_ratio(best_ret.to_numpy(), sr_benchmark=0.0)
    # The bar that matters is the INVESTABLE alternative, not 0: P(strategy Sharpe > 1/N Sharpe).
    ew_pp_sr = float(ew_ret.mean() / ew_ret.std(ddof=1))
    psr_vs_bench = probabilistic_sharpe_ratio(best_ret.to_numpy(), sr_benchmark=ew_pp_sr)
    pbo = probability_of_backtest_overfitting(mat.to_numpy(), n_splits=16)
    mtrl = min_track_record_length(best_ret.to_numpy())

    common = mat.index.intersection(spy_ret.index)
    attr = attribution(best_ret.reindex(common).fillna(0.0))

    print("\n" + "=" * 64)
    print("ROUND-3 RIGOR REPORT  —  Minervini / us_study / 2015-2024")
    print("=" * 64)
    print(f"grid configs tried (N_trials)     : {n_trials}")
    print(f"best config                       : {best['label']}")
    print(f"  annualized Sharpe (in-sample)   : {best['sharpe']:+.3f}")
    print(f"  CAGR / total / maxDD            : {best['cagr']:+.2%} / {best['total_ret']:+.1%} / {best['maxdd']:.1%}")
    print(f"  config Sharpe spread (min..max) : {summary['sharpe'].min():+.3f} .. {summary['sharpe'].max():+.3f}")
    print("-" * 64)
    print("MULTIPLE-TESTING GATE (O1)")
    print(f"  PSR  P(true Sharpe>0)           : {psr:.3f}      (>0.95 good)")
    print(f"  PSR  P(Sharpe > 1/N benchmark)  : {psr_vs_bench:.3f}      (THE bar that matters)")
    print(f"  DSR  survives {n_trials:2d} trials       : {dsr:.3f}      (>0.95 survives)")
    print(f"  PBO  P(best is overfit)         : {pbo['pbo']:.3f}      (<0.5 good)  [{pbo['n_combinations']} splits]")
    print(f"  min track record length (bars)  : {mtrl:,.0f}      (have {len(best_ret):,})")
    print("-" * 64)
    print("FAIR BENCHMARKS (same window, same 51 names)")
    bh_sharpe_ew = sharpe(ew_ret)
    bh_sharpe_spy = sharpe(spy_ret)
    print(f"  strategy ann. Sharpe            : {best['sharpe']:+.3f}")
    print(f"  equal-weight buy&hold Sharpe    : {bh_sharpe_ew:+.3f}")
    print(f"  SPY buy&hold Sharpe             : {bh_sharpe_spy:+.3f}")
    print(f"  EW buy&hold total return        : {(1+ew_ret).prod()-1:+.1%}")
    print(f"  SPY buy&hold total return       : {(1+spy_ret).prod()-1:+.1%}")
    print("-" * 64)
    print("FACTOR ATTRIBUTION (O3 — Carhart 4-factor, HAC errors)")
    if "error" in attr:
        print(f"  unavailable: {attr['error']}")
    else:
        print(f"  annualized alpha                : {attr['alpha']*252:+.2%}  (t={attr['alpha_tstat']:+.2f}, p={attr['alpha_pvalue']:.3f})")
        print("  betas                           : " +
              ", ".join(f"{k}={v:+.2f}" for k, v in attr["betas"].items()))
        print(f"  R^2                             : {attr['r2']:.2f}")
    print("=" * 64)


if __name__ == "__main__":
    main()
