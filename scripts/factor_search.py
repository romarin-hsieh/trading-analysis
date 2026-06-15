"""Autonomous factor / holding-period search against a hard fitness function.

Fitness gates (ALL must pass):
  Sharpe(net) > 2.0 ; MDD(@10% vol target) < 10% ; t-stat(net daily mean) > 3.5 ;
  cost ratio = gross_ann_return / ann_cost > 3 ; capacity: NT$10M (~US$310k) single order
  absorbable (<0.1% of median $ADV).

Data scope: daily OHLCV for 51 liquid US large-caps, 2015-2024. No intraday => the 1-hour end
of the holding range is OUT of data scope; we search holding H in {1,5,10,21,63,126,252} bars.
All factors are point-in-time (lagged >=1 bar). Portfolios are dollar-neutral cross-sectional
z-weighted long-short. Costs: one-way 10 bps on turnover (sum|dw|). Sharpe & cost-ratio are
leverage-invariant; vol-targeting only sets MDD.

Run: uv run python scripts/factor_search.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from trading_analysis.config import load_config
from trading_analysis.data.store import DuckStore

logger.remove()

COST_ONEWAY = 0.0010          # 10 bps per unit turnover (fee+slippage), liquid large-caps
VOL_TARGET = 0.10             # annual, for MDD reporting
HOLDS = [1, 5, 10, 21, 63, 126, 252]
NTD_ORDER_USD = 10_000_000 / 32.0   # NT$10M -> ~US$312k


def _load():
    cfg = load_config("configs/study.yaml")
    store = DuckStore(cfg.data.cache_dir)
    syms = [s for s in cfg.universe.symbols if s != "SPY"]
    px = store.load_close_pivot(syms, column="adj_close").ffill()
    oh = store.load_ohlcv(syms)
    vol = oh.pivot_table(index="ts", columns="symbol", values="volume", aggfunc="last").reindex(px.index)
    rawc = oh.pivot_table(index="ts", columns="symbol", values="close", aggfunc="last").reindex(px.index)
    return px, (rawc * vol)


def _factors(px):
    lp = np.log(px)
    ret = px.pct_change()
    return {
        "mom_12_1": lp.shift(21) - lp.shift(252),     # 12m return skipping last month
        "mom_6_1":  lp.shift(21) - lp.shift(126),
        "rev_5":   -(lp.shift(1) - lp.shift(6)),       # 5-day short-term reversal
        "rev_1":   -(lp.shift(1) - lp.shift(2)),       # 1-day reversal
        "lowvol":  -ret.rolling(60).std().shift(1),    # low realized vol
    }


def _zweights(sig):
    z = sig.sub(sig.mean(axis=1), axis=0).div(sig.std(axis=1).replace(0, np.nan), axis=0)
    return z.div(z.abs().sum(axis=1).replace(0, np.nan), axis=0)   # dollar-neutral, gross=1


def _evaluate(weights_target, ret, hold):
    idx = weights_target.index
    rebal = np.zeros(len(idx), dtype=bool)
    rebal[::hold] = True
    w_held = weights_target.where(pd.Series(rebal, index=idx), np.nan).ffill().fillna(0.0)
    gross = (w_held * ret).sum(axis=1).fillna(0.0)
    dw = w_held.diff().abs().sum(axis=1).fillna(0.0)           # turnover per bar (only nonzero at rebal)
    cost = dw * COST_ONEWAY
    net = (gross - cost).dropna()
    net = net.iloc[252:]                                        # drop warmup
    g = gross.reindex(net.index)
    n = len(net)
    if n < 252 or net.std() == 0:
        return None
    ann = np.sqrt(252)
    sh_net = float(ann * net.mean() / net.std(ddof=1))
    sh_gr = float(ann * g.mean() / g.std(ddof=1)) if g.std() else np.nan
    tstat = float(net.mean() / net.std(ddof=1) * np.sqrt(n))
    ann_turn = float(dw.reindex(net.index).mean() * 252)
    ann_cost = float(cost.reindex(net.index).mean() * 252)
    gross_ann = float(g.mean() * 252)
    cost_ratio = float(abs(gross_ann) / ann_cost) if ann_cost > 0 else np.inf
    # MDD at vol target
    scale = VOL_TARGET / (net.std(ddof=1) * ann)
    eq = (1 + net * scale).cumprod()
    mdd = float((eq / eq.cummax() - 1).min())
    return {"sharpe_net": sh_net, "sharpe_gross": sh_gr, "tstat": tstat, "mdd": mdd,
            "ann_turnover": ann_turn, "cost_ratio": cost_ratio, "gross_ann": gross_ann, "n": n}


def _passes(m):
    return (m and m["sharpe_net"] > 2.0 and m["mdd"] > -0.10
            and m["tstat"] > 3.5 and m["cost_ratio"] > 3.0)


def main():
    px, dvol = _load()
    ret = px.pct_change()
    facs = _factors(px)
    med_adv = float(dvol.median(axis=1).median())
    cap_ok = 0.001 * med_adv > NTD_ORDER_USD

    # combined factor: equal-weight z of momentum + low-vol + 5d reversal (diversified)
    def zc(s):
        return s.sub(s.mean(axis=1), axis=0).div(s.std(axis=1).replace(0, np.nan), axis=0)
    facs["COMBO(mom+lowvol+rev5)"] = (zc(facs["mom_12_1"]) + zc(facs["lowvol"]) + zc(facs["rev_5"])) / 3
    # iteration 2: drop the broken sleeves (reversal dead on mega-caps; short-low-vol fatal in a
    # tech bull) and keep ONLY the momentum that worked
    facs["MOM_ONLY(12_1+6_1)"] = (zc(facs["mom_12_1"]) + zc(facs["mom_6_1"])) / 2

    rows = []
    for fname, sig in facs.items():
        w = _zweights(sig)
        for h in HOLDS:
            m = _evaluate(w, ret, h)
            if m:
                rows.append({"factor": fname, "hold": h, **m, "pass": _passes(m)})

    # iteration 3: LONG-ONLY momentum (no short leg — shorting was the killer). Top-10 by 6-1 mom.
    sig = facs["mom_6_1"]
    rank = sig.rank(axis=1, ascending=False)
    longw = (rank <= 10).astype(float)
    longw = longw.div(longw.sum(axis=1).replace(0, np.nan), axis=0)
    for h in HOLDS:
        m = _evaluate(longw, ret, h)
        if m:
            rows.append({"factor": "LONGONLY_mom_top10", "hold": h, **m, "pass": _passes(m)})
            facs.setdefault("LONGONLY_mom_top10", longw)
    df = pd.DataFrame(rows)

    print("\n" + "=" * 92)
    print("AUTONOMOUS FACTOR SEARCH — fitness: Sharpe>2, MDD<10%, t>3.5, cost_ratio>3")
    print(f"universe: 51 US large-caps (median $ADV ${med_adv/1e6:,.0f}M) | "
          f"NT$10M order ${NTD_ORDER_USD/1e3:.0f}k = {NTD_ORDER_USD/med_adv*1e4:.2f} bps of ADV -> "
          f"capacity {'OK' if cap_ok else 'FAIL'}")
    print("=" * 92)
    hdr = f"{'factor':24s} {'H':>4s} {'Sh_net':>7s} {'Sh_grs':>7s} {'t':>6s} {'MDD':>7s} {'turn':>6s} {'cost_x':>7s} {'pass'}"
    print(hdr)
    for fname in facs:
        for _, r in df[df["factor"] == fname].sort_values("hold").iterrows():
            flag = "<== PASS" if r["pass"] else ""
            print(f"{r['factor']:24s} {int(r['hold']):4d} {r['sharpe_net']:+7.2f} {r['sharpe_gross']:+7.2f} "
                  f"{r['tstat']:6.2f} {r['mdd']:+7.1%} {r['ann_turnover']:6.1f} {r['cost_ratio']:7.1f} {flag}")
    # extra rows from iteration 2/3 not in the per-factor loop above
    for fname in ["MOM_ONLY(12_1+6_1)", "LONGONLY_mom_top10"]:
        for _, r in df[df["factor"] == fname].sort_values("hold").iterrows():
            flag = "<== PASS" if r["pass"] else ""
            print(f"{r['factor']:24s} {int(r['hold']):4d} {r['sharpe_net']:+7.2f} {r['sharpe_gross']:+7.2f} "
                  f"{r['tstat']:6.2f} {r['mdd']:+7.1%} {r['ann_turnover']:6.1f} {r['cost_ratio']:7.1f} {flag}")
    print("-" * 92)
    n_pass = int(df["pass"].sum())
    best = df.sort_values("sharpe_net", ascending=False).iloc[0]

    # multiple-testing deflation: I have now tried N configs. Expected MAX Sharpe of N zero-skill
    # trials (Bailey-LdP) — the best must clear THIS bar, not 0.
    from trading_analysis.backtest.deflated_sharpe import expected_max_sharpe
    pp_sr = df["sharpe_net"] / np.sqrt(252)              # per-period Sharpes across configs
    e_max_ann = expected_max_sharpe(len(df), float(pp_sr.std(ddof=1))) * np.sqrt(252)
    print(f"multiple-testing: tried {len(df)} configs; expected MAX Sharpe under null ~ "
          f"{e_max_ann:+.2f} ann.  best observed {best['sharpe_net']:+.2f} "
          f"({'clears' if best['sharpe_net'] > e_max_ann else 'DOES NOT clear'} the deflated bar)")
    print(f"configs passing ALL gates: {n_pass}/{len(df)}")
    print(f"best NET Sharpe: {best['factor']} H={int(best['hold'])} -> "
          f"Sh_net {best['sharpe_net']:+.2f}, t {best['tstat']:.2f}, MDD {best['mdd']:+.1%}, "
          f"cost_x {best['cost_ratio']:.1f}")
    # best that also clears cost+MDD (the realistic frontier)
    feas = df[(df["mdd"] > -0.10) & (df["cost_ratio"] > 3.0)].sort_values("sharpe_net", ascending=False)
    if len(feas):
        b = feas.iloc[0]
        print(f"best cost+MDD-feasible: {b['factor']} H={int(b['hold'])} -> "
              f"Sh_net {b['sharpe_net']:+.2f}, t {b['tstat']:.2f}, MDD {b['mdd']:+.1%}, cost_x {b['cost_ratio']:.1f}")
    print("=" * 92)


if __name__ == "__main__":
    main()
