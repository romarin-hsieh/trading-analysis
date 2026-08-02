"""TR-07 Hierarchical Risk Parity (Lopez de Prado 2016) vs the repo's log-barrier risk parity.

HRP from scipy directly: corr -> distance sqrt(0.5*(1-rho)) -> single-linkage tree ->
quasi-diagonalization -> recursive bisection with inverse-variance splits.

Two arenas, monthly walk-forward (252d lookback, weights lagged, 10 bps/leg on turnover):
  A) the repo's 5 sleeves (validate_recommendation.build_combo): HRP vs log-barrier
     risk_parity (trading_analysis.portfolio.rebalance) vs equal-weight, + QQQ.
  B) the 47-name sector universe: HRP vs EW vs inverse-vol, + same-universe B&H + QQQ.

Controls: permuted-HRP (weights shuffled across assets at each rebalance, 20 seeds) --
destroys the cluster structure while keeping the weight distribution (F6).

Run: uv run python scripts/tests/tr07_hrp.py
"""

from __future__ import annotations

import sys

from loguru import logger

logger.remove()

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy.cluster.hierarchy as sch  # noqa: E402
from scipy.spatial.distance import squareform  # noqa: E402

sys.path.insert(0, "scripts")
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.backtest.metrics import max_drawdown, sharpe  # noqa: E402
from trading_analysis.portfolio import rebalance  # noqa: E402

LOOKBACK, STEP, TD = 252, 21, 252
COST_BPS = 10.0  # per leg on turnover (assignment spec; conservative for the ETF sleeves)
IMG = "docs/tests/img"


# ---------------------------------------------------------------- HRP (LdP 2016, ch.16 AFML)
def quasi_diag(link: np.ndarray) -> list[int]:
    """Leaf order of the linkage tree (quasi-diagonalization)."""
    link = link.astype(int)
    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]
    while sort_ix.max() >= num_items:
        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
        df0 = sort_ix[sort_ix >= num_items]
        i, j = df0.index, df0.to_numpy() - num_items
        sort_ix[i] = link[j, 0]
        sort_ix = pd.concat([sort_ix, pd.Series(link[j, 1], index=i + 1)]).sort_index()
        sort_ix.index = range(sort_ix.shape[0])
    return sort_ix.tolist()


def cluster_var(cov: pd.DataFrame, items: list) -> float:
    """Variance of the inverse-variance portfolio within a cluster."""
    sub = cov.loc[items, items].to_numpy()
    ivp = 1.0 / np.diag(sub)
    ivp /= ivp.sum()
    return float(ivp @ sub @ ivp)


def rec_bipart(cov: pd.DataFrame, sort_ix: list) -> pd.Series:
    """Recursive bisection: split top-down, allocate 1 - v0/(v0+v1) to the lower-var half."""
    w = pd.Series(1.0, index=sort_ix)
    clusters = [sort_ix]
    while clusters:
        clusters = [
            c[j:k] for c in clusters for j, k in ((0, len(c) // 2), (len(c) // 2, len(c))) if len(c) > 1
        ]
        for i in range(0, len(clusters), 2):
            c0, c1 = clusters[i], clusters[i + 1]
            v0, v1 = cluster_var(cov, c0), cluster_var(cov, c1)
            alpha = 1.0 - v0 / (v0 + v1)
            w[c0] *= alpha
            w[c1] *= 1.0 - alpha
    return w


def hrp_weights(win: pd.DataFrame) -> pd.Series:
    cov, corr = win.cov(), win.corr()
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr.to_numpy()), 0.0, None))
    link = sch.linkage(squareform(dist, checks=False), method="single")
    order = [corr.index[i] for i in quasi_diag(link)]
    return rec_bipart(cov, order).reindex(win.columns)


# ---------------------------------------------------------------- walk-forward harness
def walk_forward(rets: pd.DataFrame, weight_fn, lookback: int = LOOKBACK, step: int = STEP) -> pd.DataFrame:
    """Weights at date t fitted on the trailing `lookback` rows strictly BEFORE t (F1)."""
    idx = rets.index
    rows = {}
    for i in range(lookback, len(idx), step):
        win = rets.iloc[i - lookback : i].dropna(axis=1, how="any")
        win = win.loc[:, win.std() > 1e-12]
        if win.shape[0] < lookback // 2 or win.shape[1] < 2:
            continue
        try:
            rows[idx[i]] = weight_fn(win)
        except (RuntimeError, ValueError):
            continue
    return pd.DataFrame(rows).T.reindex(columns=rets.columns).fillna(0.0)


def evaluate(w_frame: pd.DataFrame, rets: pd.DataFrame, start=None) -> dict:
    """Apply lagged ffilled weights; charge COST_BPS on one-way turnover sum|dw|."""
    wd = w_frame.reindex(rets.index).ffill().shift(1).fillna(0.0)
    turn = wd.diff().abs().sum(axis=1).fillna(0.0)
    net = (wd * rets).sum(axis=1) - turn * COST_BPS / 1e4
    s = w_frame.index[0] if start is None else start
    net, turn = net.loc[s:], turn.loc[s:]
    return _stats(net, float(turn.sum() / (len(net) / TD)))


def _stats(net: pd.Series, ann_turn: float) -> dict:
    eq = (1.0 + net).cumprod()
    years = len(net) / TD
    return {
        "ret": net, "eq": eq, "ann": float(eq.iloc[-1] ** (1 / years) - 1),
        "sharpe": sharpe(net), "mdd": max_drawdown(eq),
        "vol": float(net.std(ddof=1) * np.sqrt(TD)), "turn": ann_turn,
        "sh_a": sharpe(net.loc[:"2019-12-31"]), "sh_b": sharpe(net.loc["2020-01-01":]),
    }


def bench_stats(ret: pd.Series, index: pd.DatetimeIndex) -> dict:
    return _stats(ret.reindex(index).fillna(0.0), 0.0)


def prow(label: str, d: dict) -> None:
    print(f"  {label:<26s} ann {d['ann']:+7.2%}  sharpe {d['sharpe']:5.2f}  mdd {d['mdd']:+7.2%}  "
          f"vol {d['vol']:6.2%}  turn {d['turn']:5.2f}x/yr  sh15-19 {d['sh_a']:5.2f}  sh20-26 {d['sh_b']:5.2f}")


def main() -> None:
    qqq = ss._px(["QQQ"]).iloc[:, 0].pct_change()

    # ================= Arena A: the repo's 5 sleeves =================
    print("=" * 100)
    print("ARENA A -- 5 sleeves (equity_mom/defensive/lev_trend/gold/bonds), monthly WF, "
          f"{LOOKBACK}d lookback, {COST_BPS:.0f}bps")
    _, _, sleeves = vr.build_combo()
    w_hrp_a = walk_forward(sleeves, hrp_weights)
    w_rp_a = rebalance(sleeves, lookback=LOOKBACK, step=STEP, method="risk_parity").fillna(0.0)
    w_rp126 = rebalance(sleeves, lookback=126, step=STEP, method="risk_parity").fillna(0.0)
    w_ew_a = walk_forward(sleeves, lambda w: pd.Series(1.0 / w.shape[1], index=w.columns))
    start_a = max(w_hrp_a.index[0], w_rp_a.index[0], w_rp126.index[0])
    res_a = {
        "HRP": evaluate(w_hrp_a, sleeves, start_a),
        "risk_parity (log-barrier)": evaluate(w_rp_a, sleeves, start_a),
        "risk_parity 126d (repo)": evaluate(w_rp126, sleeves, start_a),
        "equal-weight sleeves": evaluate(w_ew_a, sleeves, start_a),
    }
    idx_a = res_a["HRP"]["ret"].index
    res_a["QQQ buy&hold"] = bench_stats(qqq, idx_a)
    for k, v in res_a.items():
        prow(k, v)
    print(f"  sample: {len(idx_a)} days x 5 sleeves = {len(idx_a) * 5} bar-asset obs, "
          f"{idx_a[0].date()} -> {idx_a[-1].date()}")
    avg_hrp = w_hrp_a.mean().round(3)
    avg_rp = w_rp_a.mean().round(3)
    print("  avg weights HRP :", dict(avg_hrp))
    print("  avg weights RP  :", dict(avg_rp))

    # ================= Arena B: 47-name sector universe =================
    print("=" * 100)
    print(f"ARENA B -- 47-name universe, monthly WF, {LOOKBACK}d lookback, {COST_BPS:.0f}bps")
    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    px = ss._px(allsyms)
    rets_b = px.pct_change()
    w_hrp_b = walk_forward(rets_b, hrp_weights)
    w_ew_b = walk_forward(rets_b, lambda w: pd.Series(1.0 / w.shape[1], index=w.columns))
    w_iv_b = walk_forward(rets_b, lambda w: (lambda s: s / s.sum())(1.0 / w.std()))
    w_mv_b = rebalance(rets_b, lookback=LOOKBACK, step=STEP, method="min_variance").fillna(0.0)
    start_b = w_hrp_b.index[0]
    res_b = {
        "HRP": evaluate(w_hrp_b, rets_b, start_b),
        "equal-weight (monthly)": evaluate(w_ew_b, rets_b, start_b),
        "inverse-vol": evaluate(w_iv_b, rets_b, start_b),
        "min-variance (LW shrunk)": evaluate(w_mv_b, rets_b, start_b),
    }
    idx_b = res_b["HRP"]["ret"].index
    # same-universe buy & hold: names investable at start, bought once, drift (F3)
    have = px.columns[px.loc[start_b].notna()]
    bh_eq = (px.loc[start_b:, have] / px.loc[start_b, have]).mean(axis=1)
    res_b["same-universe B&H"] = bench_stats(bh_eq.pct_change(), idx_b)
    res_b["QQQ buy&hold"] = bench_stats(qqq, idx_b)
    for k, v in res_b.items():
        prow(k, v)
    n_obs_b = int(rets_b.loc[idx_b].notna().sum().sum())
    print(f"  sample: {len(idx_b)} days, {n_obs_b} bar-asset obs, {idx_b[0].date()} -> {idx_b[-1].date()}, "
          f"{w_hrp_b.shape[0]} rebalances, avg {(w_hrp_b > 0).sum(axis=1).mean():.1f} names held")

    # ================= F6 control: permuted HRP (arena B) =================
    rng = np.random.default_rng(7)
    perm_sh, perm_vol, perm_mdd = [], [], []
    for _ in range(20):
        vals = w_hrp_b.to_numpy().copy()
        for r_i in range(vals.shape[0]):
            m = vals[r_i] > 0
            vals[r_i, m] = rng.permutation(vals[r_i, m])
        wp = pd.DataFrame(vals, index=w_hrp_b.index, columns=w_hrp_b.columns)
        d = evaluate(wp, rets_b, start_b)
        perm_sh.append(d["sharpe"])
        perm_vol.append(d["vol"])
        perm_mdd.append(d["mdd"])
    print(f"  CONTROL permuted-HRP (20 seeds): sharpe {np.mean(perm_sh):.2f}+/-{np.std(perm_sh):.2f}  "
          f"vol {np.mean(perm_vol):.2%}+/-{np.std(perm_vol):.2%}  mdd {np.mean(perm_mdd):.2%}")
    print(f"  -> HRP vol {res_b['HRP']['vol']:.2%} vs permuted {np.mean(perm_vol):.2%}: cluster info "
          f"{'reduces' if res_b['HRP']['vol'] < np.mean(perm_vol) else 'does NOT reduce'} risk")

    # ================= charts =================
    win = rets_b.iloc[-LOOKBACK:].dropna(axis=1, how="any")
    corr = win.corr()
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr.to_numpy()), 0.0, None))
    link = sch.linkage(squareform(dist, checks=False), method="single")
    order = [corr.index[i] for i in quasi_diag(link)]
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    sch.dendrogram(link, labels=list(corr.index), ax=ax[0], leaf_font_size=7, color_threshold=0.55)
    ax[0].set_title(f"HRP single-linkage dendrogram, last {LOOKBACK}d window ({win.index[-1].date()})")
    ax[0].set_ylabel("distance sqrt(0.5(1-rho))")
    im = ax[1].imshow(corr.loc[order, order], cmap="RdYlBu_r", vmin=-0.2, vmax=1.0)
    ax[1].set_title("quasi-diagonalized correlation")
    ax[1].set_xticks(range(len(order)), order, rotation=90, fontsize=5)
    ax[1].set_yticks(range(len(order)), order, fontsize=5)
    fig.colorbar(im, ax=ax[1], fraction=0.046)
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr07_dendrogram.png", dpi=120)

    fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=False)
    for k, v in res_a.items():
        ax[0].plot(v["eq"], label=f"{k} (sh {v['sharpe']:.2f})", lw=1.2)
    ax[0].set_yscale("log")
    ax[0].set_title("Arena A: 5 sleeves -- HRP vs log-barrier risk parity vs EW (net 10bps)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    for k, v in res_b.items():
        ax[1].plot(v["eq"], label=f"{k} (sh {v['sharpe']:.2f})", lw=1.2)
    ax[1].set_yscale("log")
    ax[1].set_title("Arena B: 47-name universe -- HRP vs EW vs inverse-vol (net 10bps)")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr07_equity.png", dpi=120)
    print(f"saved {IMG}/tr07_dendrogram.png , {IMG}/tr07_equity.png")

    # F-checklist summary line
    print("F1 lagged WF (strictly-before windows + shift(1)) | F2 10bps/leg on sum|dw| | "
          "F3 same-universe B&H + QQQ | F4 counts above | F5 7 pre-specified variants, no tuning | "
          "F6 permuted control | F7 sub-period cols above")


if __name__ == "__main__":
    main()
