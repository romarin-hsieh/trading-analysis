"""TR-03: Statistical factor model (log-return PCA, Connor-Korajczyk style) for min-var
portfolio construction on the 47-name sector universe.

Walk-forward monthly: at each month-end, fit on trailing 252d of LOG returns strictly up to
that close (F1), build Sigma = B F B' + D (k=5 PCs), long-only min-var (clip negatives,
renormalize, 10 percent cap), hold one month. Compared vs equal-weight, sample-cov min-var,
Ledoit-Wolf min-var, plus a label-permutation placebo (F6) and QQQ buy-and-hold (F3).
Universe is dynamic: a name enters once it has a complete trailing 252d window (CRWD 2019,
SNOW/PLTR 2020 IPOs; the other 44 names span the full 2015-2026 panel).
Costs: 10 bps per leg on turnover (single stocks, F2).
"""

from loguru import logger

logger.remove()

import sys  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.covariance import LedoitWolf  # noqa: E402

sys.path.insert(0, "scripts")
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

LOOKBACK = 252
K = 5
CAP = 0.10
COST_PER_LEG = 0.0010  # 10 bps, single stocks
SEED = 42


def pca_factor_cov(x: np.ndarray, k: int = K) -> np.ndarray:
    """Sigma = B F B' + D from top-k eigenvectors of the sample covariance."""
    s = np.cov(x, rowvar=False, ddof=1)
    evals, evecs = np.linalg.eigh(s)
    idx = np.argsort(evals)[::-1][:k]
    lam, v = evals[idx], evecs[:, idx]
    common = (v * lam) @ v.T
    d = np.maximum(np.diag(s) - np.diag(common), 1e-8)
    return common + np.diag(d)


def var_explained(x: np.ndarray, k: int = K) -> tuple[float, float]:
    """(share of variance in top-k PCs, share in PC1) of the sample covariance."""
    evals = np.linalg.eigvalsh(np.cov(x, rowvar=False, ddof=1))
    evals = np.sort(evals)[::-1]
    tot = evals.sum()
    return float(evals[:k].sum() / tot), float(evals[0] / tot)


def long_only_minvar(sigma: np.ndarray, cap: float = CAP) -> np.ndarray:
    """Unconstrained min-var -> clip negatives -> renormalize -> iterative 10pct cap."""
    n = sigma.shape[0]
    ones = np.ones(n)
    try:
        w = np.linalg.solve(sigma, ones)
    except np.linalg.LinAlgError:
        w = np.linalg.solve(sigma + 1e-6 * np.eye(n), ones)
    w = np.clip(w, 0.0, None)
    if w.sum() <= 0:
        w = ones.copy()
    w = w / w.sum()
    for _ in range(100):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        free = ~over
        if w[free].sum() <= 0:
            w[free] += excess / free.sum()
        else:
            w[free] += excess * w[free] / w[free].sum()
    return w


def run_backtest(simple_ret: pd.DataFrame, log_ret: pd.DataFrame, method: str,
                 rng: np.random.Generator | None = None) -> tuple[pd.Series, float, list]:
    """Daily net return series, annualized two-sided turnover, per-rebalance diagnostics.

    Dynamic universe: at each rebalance only names with a complete (NaN-free) trailing
    252d log-return window are eligible. Weights are pandas Series keyed by ticker so
    turnover across membership changes is exact.
    """
    dates = simple_ret.index
    month_ends = simple_ret.groupby(dates.to_period("M")).tail(1).index
    rebals = [d for d in month_ends if dates.get_loc(d) >= LOOKBACK and d < dates[-1]]
    port, port_dates = [], []
    w_prev = pd.Series(dtype=float)
    turn_sum, diags = 0.0, []
    for ri, d in enumerate(rebals):
        i = dates.get_loc(d)
        window = log_ret.iloc[i - LOOKBACK + 1: i + 1]  # ends AT rebalance close (F1)
        valid = window.columns[window.notna().all(axis=0)]
        win = window[valid].to_numpy()
        n = len(valid)
        if method == "ew":
            wv = np.full(n, 1.0 / n)
        else:
            if method == "sample":
                sigma = np.cov(win, rowvar=False, ddof=1)
            elif method == "lw":
                sigma = LedoitWolf().fit(win).covariance_
            elif method in ("pca", "pca_placebo"):
                sigma = pca_factor_cov(win, K)
                diags.append(var_explained(win, K))
            wv = long_only_minvar(sigma)
            if method == "pca_placebo":
                wv = wv[rng.permutation(n)]  # same concentration, random labels (F6)
        w = pd.Series(wv, index=valid)
        union = w.index.union(w_prev.index)
        turn = float((w.reindex(union, fill_value=0.0)
                      - w_prev.reindex(union, fill_value=0.0)).abs().sum())
        turn_sum += turn
        cost = turn * COST_PER_LEG
        j_end = dates.get_loc(rebals[ri + 1]) if ri + 1 < len(rebals) else len(dates) - 1
        for j in range(i + 1, j_end + 1):
            r = simple_ret.iloc[j].reindex(w.index).fillna(0.0)
            pr = float((w * r).sum()) - (cost if j == i + 1 else 0.0)
            port.append(pr)
            port_dates.append(dates[j])
            w = w * (1.0 + r)
            w = w / w.sum()
        w_prev = w
    ret = pd.Series(port, index=pd.DatetimeIndex(port_dates), name=method)
    years = (ret.index[-1] - ret.index[0]).days / 365.25
    return ret, turn_sum / years, diags


def stats_row(name: str, ret: pd.Series, ann_turn: float | None) -> dict:
    eq = (1.0 + ret).cumprod()
    return {
        "name": name,
        "ann_ret": cagr(eq),
        "ann_vol": float(ret.std() * np.sqrt(252)),
        "sharpe": sharpe(ret),
        "mdd": max_drawdown(eq),
        "turn": ann_turn,
    }


def sub_stats(ret: pd.Series) -> tuple[float, float, float, float]:
    a, b = ret[ret.index < "2020-01-01"], ret[ret.index >= "2020-01-01"]
    return (float(a.std() * np.sqrt(252)), sharpe(a), float(b.std() * np.sqrt(252)), sharpe(b))


def main() -> None:
    store = DuckStore("./data")
    tickers = sorted({t for v in ss.SECTORS.values() for t in v})
    px = store.load_close_pivot(tickers, column="adj_close").ffill()
    qqq = store.load_close_pivot(["QQQ"], column="adj_close").ffill().iloc[:, 0]
    print(f"universe: {px.shape[1]} names, {px.shape[0]} days, {px.index[0].date()}"
          f" -> {px.index[-1].date()}")
    simple_ret = px.pct_change(fill_method=None).iloc[1:]
    log_ret = np.log(px).diff().iloc[1:]
    n_obs = int(simple_ret.notna().sum().sum())
    print(f"samples: {simple_ret.shape[1]} names x {simple_ret.shape[0]} days panel,"
          f" {n_obs} non-NaN bar-asset obs (F4)")

    rng = np.random.default_rng(SEED)
    runs = {}
    for m in ["ew", "sample", "lw", "pca", "pca_placebo"]:
        runs[m] = run_backtest(simple_ret, log_ret, m, rng=rng)
    bt_index = runs["ew"][0].index
    print(f"backtest span: {bt_index[0].date()} -> {bt_index[-1].date()}"
          f" ({len(bt_index)} days)")
    qqq_ret = qqq.pct_change().reindex(bt_index).dropna()
    diags = runs["pca"][2]
    ve5 = float(np.mean([d[0] for d in diags]))
    ve1 = float(np.mean([d[1] for d in diags]))
    print(f"rebalances: {len(diags)}; avg var explained top-5 PCs = {ve5:.1%},"
          f" PC1 alone = {ve1:.1%}")

    labels = {"ew": "Equal-weight (monthly)", "sample": "Sample-cov min-var",
              "lw": "Ledoit-Wolf min-var", "pca": "PCA factor-model min-var (k=5)",
              "pca_placebo": "Placebo: permuted PCA weights"}
    rows = [stats_row(labels[m], runs[m][0], runs[m][1]) for m in labels]
    rows.append(stats_row("QQQ buy-and-hold", qqq_ret, None))

    hdr = f"{'strategy':34s} {'annret':>7s} {'annvol':>7s} {'sharpe':>7s} {'mdd':>7s} {'turn':>7s}"
    print("\n" + hdr)
    print("-" * len(hdr))
    for r in rows:
        t = f"{r['turn']:7.2f}" if r["turn"] is not None else "    n/a"
        print(f"{r['name']:34s} {r['ann_ret']:7.2%} {r['ann_vol']:7.2%}"
              f" {r['sharpe']:7.2f} {r['mdd']:7.2%} {t}")

    print("\nsub-periods (F7): 2016-2019 vs 2020-2026  [annvol / sharpe]")
    for m in ["ew", "sample", "lw", "pca"]:
        v1, s1, v2, s2 = sub_stats(runs[m][0])
        print(f"  {labels[m]:34s} {v1:6.2%} / {s1:5.2f}   vs   {v2:6.2%} / {s2:5.2f}")
    v1, s1, v2, s2 = sub_stats(qqq_ret)
    print(f"  {'QQQ buy-and-hold':34s} {v1:6.2%} / {s1:5.2f}   vs   {v2:6.2%} / {s2:5.2f}")

    # charts
    fig, ax = plt.subplots(figsize=(10, 5))
    for m in ["ew", "sample", "lw", "pca"]:
        eq = (1.0 + runs[m][0]).cumprod()
        ax.plot(eq.index, eq.values, label=labels[m], lw=1.2)
    eq_q = (1.0 + qqq_ret).cumprod()
    ax.plot(eq_q.index, eq_q.values, label="QQQ B&H", color="black", ls="--", lw=1.0)
    ax.set_yscale("log")
    ax.set_title("TR-03 long-only min-var: PCA factor cov vs sample vs LW vs EW (net 10bps)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr03_equity.png", dpi=120)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for m in ["ew", "sample", "lw", "pca"]:
        rv = runs[m][0].rolling(63).std() * np.sqrt(252)
        axes[0].plot(rv.index, rv.values, label=labels[m], lw=1.0)
    axes[0].set_title("rolling 63d realized vol (ann.)")
    axes[0].legend(fontsize=7)
    axes[0].grid(alpha=0.3)
    ve5_series = [d[0] for d in diags]
    ve1_series = [d[1] for d in diags]
    x = range(len(ve5_series))
    axes[1].plot(x, ve5_series, label="top-5 PCs", lw=1.2)
    axes[1].plot(x, ve1_series, label="PC1", lw=1.2)
    axes[1].set_title(f"variance explained per fit (avg 5PC={ve5:.0%}, PC1={ve1:.0%})")
    axes[1].set_xlabel(f"rebalance # (n={len(ve5_series)} months)")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr03_diag.png", dpi=120)
    print("\nsaved docs/tests/img/tr03_equity.png, docs/tests/img/tr03_diag.png")


if __name__ == "__main__":
    main()
