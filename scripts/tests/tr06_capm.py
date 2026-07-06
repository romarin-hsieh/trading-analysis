"""TR-06 CAPM / market model (Sharpe 1964) -- two tests.

A) PRICING: does beta price returns in the 47-name universe? Rolling 252d beta vs SPY
   (strictly lagged), monthly beta-tercile sorts (net 10bps/leg on turnover), and a
   Fama-MacBeth cross-sectional regression of next-month returns on lagged beta.
   CAPM predicts slope = market excess return (~0.5-1%/mo). Also the low-beta anomaly
   (Frazzini-Pedersen betting-against-beta) check: Sharpe(low tercile) vs Sharpe(high).
B) ATTRIBUTION: CAPM (single-factor) alpha/beta of the repo's 5-sleeve risk-parity combo
   vs SPY (rf = BIL), Newey-West HAC t -- compared with the documented Carhart-4 alpha
   (docs/08: +6.08%/yr, t=2.64).

Fabric spec: docs/17-fabric-acceptance.md. Run: uv run python scripts/tests/tr06_capm.py
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402
from trading_analysis.factors.attribution import factor_alpha  # noqa: E402

COST_STOCK = 0.0010  # 10 bps per leg, single stocks (F2)
MIN_XS = 30  # min cross-section size for a Fama-MacBeth month
IMG = "docs/tests/img"


def ann_ret_m(r: pd.Series) -> float:
    r = r.dropna()
    return float((1.0 + r).prod() ** (12.0 / len(r)) - 1.0) if len(r) else 0.0


def load_all():
    syms = sorted({x for v in ss.SECTORS.values() for x in v})
    store = DuckStore("./data")
    px = store.load_close_pivot([*syms, "SPY", "QQQ", "BIL"], column="adj_close").ffill()
    return syms, px


def rolling_betas(px: pd.DataFrame, syms: list[str]) -> pd.DataFrame:
    ret = px[syms].pct_change()
    mkt = px["SPY"].pct_change()
    cov = ret.rolling(252, min_periods=252).cov(mkt)
    var = mkt.rolling(252, min_periods=252).var()
    return cov.div(var, axis=0)


def fama_macbeth(b_lag: pd.DataFrame, r_m: pd.DataFrame):
    """Monthly cross-sectional OLS r_{i,t} = g0_t + g1_t*beta_{i,t-1}. Returns slope series."""
    g0, g1, months, nobs = [], [], [], 0
    for t in r_m.index:
        if t not in b_lag.index:
            continue
        x, y = b_lag.loc[t], r_m.loc[t]
        m = x.notna() & y.notna()
        if int(m.sum()) < MIN_XS:
            continue
        design = np.column_stack([np.ones(int(m.sum())), x[m].to_numpy()])
        coef, *_ = np.linalg.lstsq(design, y[m].to_numpy(), rcond=None)
        g0.append(coef[0])
        g1.append(coef[1])
        months.append(t)
        nobs += int(m.sum())
    return pd.Series(g0, index=months), pd.Series(g1, index=months), nobs


def fm_t(s: pd.Series) -> float:
    return float(s.mean() / s.std(ddof=1) * np.sqrt(len(s))) if len(s) > 2 else 0.0


def tercile_track(b_lag: pd.DataFrame, r_m: pd.DataFrame):
    """EW beta-tercile portfolios, net 10bps/leg on one-way turnover. Returns net rets, turnover."""
    rets = {0: [], 1: [], 2: []}
    tos = {0: [], 1: [], 2: []}
    prev_w: dict[int, pd.Series] = {}
    months = []
    for t in r_m.index:
        if t not in b_lag.index:
            continue
        x, y = b_lag.loc[t], r_m.loc[t]
        m = x.notna() & y.notna()
        if int(m.sum()) < MIN_XS:
            continue
        tc = pd.qcut(x[m].rank(method="first"), 3, labels=False)
        months.append(t)
        for q in (0, 1, 2):
            mem = tc.index[tc == q]
            w = pd.Series(1.0 / len(mem), index=mem)
            pw = prev_w.get(q, pd.Series(dtype=float))
            to = float((w.subtract(pw, fill_value=0.0)).abs().sum())  # one-way, incl. entry
            gross = float(y[mem].mean())
            rets[q].append(gross - to * COST_STOCK)
            tos[q].append(to)
            prev_w[q] = w
    idx = pd.DatetimeIndex(months)
    net = pd.DataFrame({q: pd.Series(rets[q], index=idx) for q in (0, 1, 2)})
    net.columns = ["low", "mid", "high"]
    to_df = pd.DataFrame({q: pd.Series(tos[q], index=idx) for q in (0, 1, 2)})
    to_df.columns = ["low", "mid", "high"]
    return net, to_df


def stats_row(label: str, r: pd.Series) -> str:
    eq = (1.0 + r.fillna(0)).cumprod()
    return (f"{label:26s} ann={ann_ret_m(r) * 100:7.2f}%  shp={sharpe(r, 12):5.2f}  "
            f"mdd={max_drawdown(eq) * 100:7.2f}%")


def main():
    rng = np.random.default_rng(42)
    syms, px = load_all()
    beta = rolling_betas(px, syms)
    px_m = px.resample("ME").last()
    r_m = px_m[syms].pct_change()
    mkt_m = px_m["SPY"].pct_change()
    qqq_m = px_m["QQQ"].pct_change()
    rf_m = px_m["BIL"].pct_change()
    b_lag = beta.resample("ME").last().shift(1)  # beta known at end of month t-1 (F1)

    print("=" * 78)
    print("TR-06 CAPM / market model (Sharpe 1964)")
    print("=" * 78)

    # ---------------- A) PRICING: Fama-MacBeth ----------------
    g0, g1, nobs = fama_macbeth(b_lag, r_m)
    prem = (mkt_m - rf_m).reindex(g1.index)
    print(f"\n[A1] Fama-MacBeth, {len(g1)} months {g1.index[0]:%Y-%m}..{g1.index[-1]:%Y-%m}, "
          f"total obs={nobs} (stock-months)")
    print(f"  mean slope (gamma1) = {g1.mean() * 100:+.3f}%/mo   t = {fm_t(g1):+.2f}")
    print(f"  mean intercept (g0) = {g0.mean() * 100:+.3f}%/mo   t = {fm_t(g0):+.2f}")
    print(f"  CAPM-predicted slope = realized mkt excess ret = {prem.mean() * 100:+.3f}%/mo")
    for lab, msk in [("2016-2019", g1.index <= "2019-12-31"), ("2020-2026", g1.index >= "2020-01-01")]:
        print(f"  sub {lab}: slope={g1[msk].mean() * 100:+.3f}%/mo t={fm_t(g1[msk]):+.2f} "
              f"(pred {prem[msk].mean() * 100:+.3f}%/mo)")

    # placebo control (F6): cross-sectionally shuffled betas, 200 reps
    reps = 200
    tstats = []
    for _ in range(reps):
        bs = b_lag.copy()
        for t in bs.index:
            v = bs.loc[t].dropna()
            if len(v):
                bs.loc[t, v.index] = rng.permutation(v.to_numpy())
        _, gs, _ = fama_macbeth(bs, r_m)
        tstats.append(fm_t(gs))
    tstats = np.array(tstats)
    frac = float((np.abs(tstats) >= abs(fm_t(g1))).mean())
    print(f"[A2] placebo (shuffled beta x{reps}): mean t={tstats.mean():+.2f}, "
          f"P(|t_placebo|>=|t_obs|)={frac:.2f}")

    # ---------------- A) PRICING: beta terciles ----------------
    net, to_df = tercile_track(b_lag, r_m)
    ew = r_m.reindex(net.index).mean(axis=1)  # same-universe EW (gross) benchmark (F3)
    spread = net["low"] - net["high"]
    print("\n[A3] beta terciles (EW, net 10bps/leg) -- low-beta anomaly check")
    for c in ["low", "mid", "high"]:
        print("  " + stats_row(f"{c}-beta tercile (net)", net[c])
              + f"  ann.turnover={to_df[c].mean() * 12:4.1f}x")
    print("  " + stats_row("low-minus-high (net)", spread))
    print("  " + stats_row("EW universe (gross)", ew))
    print("  " + stats_row("QQQ", qqq_m.reindex(net.index)))
    print("  " + stats_row("SPY", mkt_m.reindex(net.index)))
    for lab, msk in [("2016-2019", net.index <= "2019-12-31"), ("2020-2026", net.index >= "2020-01-01")]:
        print(f"  sub {lab}: shp low={sharpe(net.loc[msk, 'low'], 12):+.2f} "
              f"high={sharpe(net.loc[msk, 'high'], 12):+.2f} "
              f"L-H={sharpe(spread[msk], 12):+.2f}")
    # realized post-formation betas of the terciles
    x = (mkt_m - rf_m).reindex(net.index)
    rbetas = {c: float(np.polyfit(x, net[c] - rf_m.reindex(net.index), 1)[0]) for c in net}
    fbetas = {}
    for t in net.index:
        v = b_lag.loc[t].dropna()
        tc = pd.qcut(v.rank(method="first"), 3, labels=False)
        for q, c in zip((0, 1, 2), ["low", "mid", "high"], strict=True):
            fbetas.setdefault(c, []).append(float(v[tc.index[tc == q]].mean()))
    fb = {c: float(np.mean(v)) for c, v in fbetas.items()}
    print("  formation betas: " + ", ".join(f"{c}={fb[c]:.2f}" for c in ["low", "mid", "high"]))
    print("  realized  betas: " + ", ".join(f"{c}={rbetas[c]:.2f}" for c in ["low", "mid", "high"]))

    # per-stock SML points (time-series mean lagged beta vs mean next-month return)
    common = g1.index
    mb = b_lag.reindex(common).mean()
    mr = r_m.reindex(common).mean()
    ok = mb.notna() & mr.notna()
    sml_slope, sml_int = np.polyfit(mb[ok], mr[ok], 1)
    print(f"\n[A4] SML cross-section ({int(ok.sum())} names): "
          f"slope={sml_slope * 100:+.3f}%/mo per beta, intercept={sml_int * 100:+.3f}%/mo")
    print(f"  CAPM predicts slope={prem.mean() * 100:+.3f}%/mo, intercept=rf={rf_m.reindex(common).mean() * 100:+.3f}%/mo")

    # ---------------- B) ATTRIBUTION: combo CAPM alpha ----------------
    rp, _, _ = vr.build_combo()
    rf_d = px["BIL"].pct_change()
    mkt_d = px["SPY"].pct_change()
    idx = rp.index.intersection(mkt_d.dropna().index).intersection(rf_d.dropna().index)
    res = factor_alpha(rp.reindex(idx),
                       pd.DataFrame({"Mkt-RF": (mkt_d - rf_d).reindex(idx)}),
                       rf=rf_d.reindex(idx))
    eq_rp = (1.0 + rp.reindex(idx)).cumprod()
    print(f"\n[B] 5-sleeve combo vs SPY (CAPM single factor, HAC), n={res['n']} days "
          f"{idx[0]:%Y-%m-%d}..{idx[-1]:%Y-%m-%d}")
    print(f"  CAPM alpha = {res['alpha'] * 252 * 100:+.2f}%/yr  t={res['alpha_tstat']:+.2f} "
          f"(p={res['alpha_pvalue']:.4f})  beta={res['betas']['Mkt-RF']:.2f}  R2={res['r2']:.2f}")
    print(f"  combo: ann={(eq_rp.iloc[-1] ** (252 / len(idx)) - 1) * 100:.2f}% "
          f"shp={sharpe(rp.reindex(idx)):.2f} mdd={max_drawdown(eq_rp) * 100:.2f}%")
    eq_spy = (1.0 + mkt_d.reindex(idx)).cumprod()
    print(f"  SPY  : ann={(eq_spy.iloc[-1] ** (252 / len(idx)) - 1) * 100:.2f}% "
          f"shp={sharpe(mkt_d.reindex(idx)):.2f} mdd={max_drawdown(eq_spy) * 100:.2f}%")
    print("  documented Carhart-4 alpha (docs/08): +6.08%/yr, t=2.64")
    for lab, (a, b) in vr.SPLITS.items():
        sub = rp.reindex(idx).loc[a:b]
        sm_ = (mkt_d - rf_d).reindex(sub.index)
        r2 = factor_alpha(sub, pd.DataFrame({"Mkt-RF": sm_}), rf=rf_d.reindex(sub.index))
        print(f"  sub {lab}: alpha={r2['alpha'] * 252 * 100:+.2f}%/yr t={r2['alpha_tstat']:+.2f} "
              f"beta={r2['betas']['Mkt-RF']:.2f}")

    # ---------------- charts ----------------
    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    ax[0].scatter(mb[ok], mr[ok] * 100, s=18, alpha=0.7, label="47 names")
    xs = np.linspace(float(mb[ok].min()), float(mb[ok].max()), 50)
    ax[0].plot(xs, (sml_int + sml_slope * xs) * 100, "r-",
               label=f"actual SML {sml_slope * 100:+.2f}%/mo/beta")
    rf_bar = float(rf_m.reindex(common).mean())
    ax[0].plot(xs, (rf_bar + prem.mean() * xs) * 100, "g--",
               label=f"CAPM SML {prem.mean() * 100:+.2f}%/mo/beta")
    ax[0].set_xlabel("mean lagged 252d beta vs SPY")
    ax[0].set_ylabel("mean next-month return (%)")
    ax[0].set_title("TR-06 SML: actual vs CAPM-predicted")
    ax[0].legend(fontsize=8)
    for c, col in zip(["low", "mid", "high"], ["tab:blue", "tab:gray", "tab:red"], strict=True):
        ax[1].plot((1 + net[c]).cumprod(), color=col, label=f"{c}-beta (net)")
    ax[1].plot((1 + ew).cumprod(), "k--", lw=1, label="EW universe")
    ax[1].plot((1 + qqq_m.reindex(net.index)).cumprod(), color="tab:green", lw=1, label="QQQ")
    ax[1].set_yscale("log")
    ax[1].set_title("beta terciles, net 10bps/leg")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr06_sml_terciles.png", dpi=120)

    fig2, ax2 = plt.subplots(1, 2, figsize=(11, 5))
    capm_rep = (rf_d + res["betas"]["Mkt-RF"] * (mkt_d - rf_d)).reindex(idx)
    ax2[0].plot(eq_rp, label="5-sleeve combo")
    ax2[0].plot(eq_spy, label="SPY")
    ax2[0].plot((1 + capm_rep).cumprod(), "--", label=f"CAPM replica (beta={res['betas']['Mkt-RF']:.2f})")
    ax2[0].set_yscale("log")
    ax2[0].set_title("combo vs SPY vs CAPM replica")
    ax2[0].legend(fontsize=8)
    rb = rp.reindex(idx).rolling(252).cov(mkt_d.reindex(idx)) / mkt_d.reindex(idx).rolling(252).var()
    ax2[1].plot(rb, color="tab:purple")
    ax2[1].axhline(res["betas"]["Mkt-RF"], color="gray", ls="--")
    ax2[1].set_title("combo rolling 252d beta vs SPY")
    fig2.tight_layout()
    fig2.savefig(f"{IMG}/tr06_attribution.png", dpi=120)
    print(f"\ncharts -> {IMG}/tr06_sml_terciles.png , {IMG}/tr06_attribution.png")


if __name__ == "__main__":
    main()
