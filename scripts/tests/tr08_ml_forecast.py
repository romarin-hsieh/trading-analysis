"""TR-08: ML hybrid return forecasting (LightGBM, yearly walk-forward refit).

refs: manuhup/LSTM-XGBoost-Hybrid; Gu-Kelly-Xiu (2020) "Empirical Asset Pricing
via Machine Learning" (RFS). HONEST SUBSTITUTION: LightGBM stands in for the
XGBoost half (same gradient-boosted-tree model class); the LSTM half is omitted
(no torch installed). Stated explicitly in the TR doc.

Design (Fabric spec docs/17):
  F1 leak-free: features lagged 1 bar; yearly refit trains only on data up to
     Dec 31 of Y-1 with a 21-day purge gap (last 21 train dates dropped because
     their 21d-forward labels bleed into the test year).
  F2 net cost: 10 bps/leg on single stocks, charged on turnover.
  F3 benchmarks: EW-47 buy&hold (same universe), QQQ B&H, plus the dumb
     competitor: plain 6-1 momentum top-10 (same portfolio mechanics + costs).
  F6 control: identical pipeline with SHUFFLED training labels.

Run: uv run python scripts/tests/tr08_ml_forecast.py
"""

from loguru import logger

logger.remove()

# ruff: noqa: E402
import sys

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "src")

import sector_strategies as ss

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
from trading_analysis.data.store import DuckStore

FEATURES = [
    "ret5", "ret21", "ret63", "ret126",
    "vol21", "vol63", "rsi14",
    "dist_sma50", "dist_sma200", "volz21", "hi52w",
]  # fmt: skip
LABEL_H = 21
PURGE = 21
COST_LEG = 0.0010  # 10 bps per leg, single stocks
K = 10
OOS_YEARS = list(range(2018, 2027))
LGB_PARAMS = dict(
    objective="regression",
    n_estimators=300,
    learning_rate=0.05,
    num_leaves=31,
    min_child_samples=200,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=4,
    verbose=-1,
    importance_type="gain",
)


def build_panel(adj: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    ret1 = adj.pct_change(fill_method=None)
    delta = adj.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    feats = {
        "ret5": adj.pct_change(5, fill_method=None),
        "ret21": adj.pct_change(21, fill_method=None),
        "ret63": adj.pct_change(63, fill_method=None),
        "ret126": adj.pct_change(126, fill_method=None),
        "vol21": ret1.rolling(21).std(),
        "vol63": ret1.rolling(63).std(),
        "rsi14": 100.0 * up / (up + dn),
        "dist_sma50": adj / adj.rolling(50).mean() - 1.0,
        "dist_sma200": adj / adj.rolling(200).mean() - 1.0,
        "volz21": (volume - volume.rolling(21).mean()) / volume.rolling(21).std(),
        "hi52w": adj / adj.rolling(252).max() - 1.0,
    }
    frames = [feats[f].shift(1).stack().rename(f) for f in FEATURES]  # lag 1 bar (F1)
    label = (adj.shift(-LABEL_H) / adj - 1.0).stack().rename("label")
    panel = pd.concat([*frames, label], axis=1)
    return panel.dropna(subset=FEATURES)


def daily_rank_ic(pred: pd.Series, label: pd.Series, min_names: int = 20) -> pd.Series:
    df = pd.concat([pred.rename("p"), label.rename("y")], axis=1).dropna()
    ics = {}
    for d, g in df.groupby(level=0):
        if len(g) >= min_names:
            ics[d] = g["p"].rank().corr(g["y"].rank())
    return pd.Series(ics).sort_index()


def ic_stats(ic: pd.Series) -> tuple[float, float, int]:
    """mean daily IC + t-stat on the non-overlapping (every 21st day) subsample."""
    sub = ic.iloc[::LABEL_H]
    t = sub.mean() / (sub.std(ddof=1) / np.sqrt(len(sub)))
    return float(ic.mean()), float(t), len(sub)


def run_portfolio(
    score_w: pd.DataFrame, rets: pd.DataFrame, k: int = K, cost_leg: float = COST_LEG
) -> tuple[pd.Series, float]:
    """Monthly top-k EW; signal at month-end close, executed at next close (F1);
    intramonth weights drift with returns; cost on |dw| at execution (F2)."""
    dates = score_w.index
    months = pd.Series(dates.to_period("M"), index=dates)
    rebal_dates = sorted({dates[0], *(g.index[-1] for _, g in months.groupby(months))})
    pos = {d: i for i, d in enumerate(dates)}
    exec_targets: dict[pd.Timestamp, pd.Series] = {}
    for d in rebal_dates:
        i = pos[d]
        if i + 1 >= len(dates):
            continue
        row = score_w.loc[d].dropna()
        if len(row) < k:
            continue
        tgt = pd.Series(0.0, index=score_w.columns)
        tgt[row.nlargest(k).index] = 1.0 / k
        exec_targets[dates[i + 1]] = tgt
    w = pd.Series(0.0, index=score_w.columns)
    out, total_dw = [], 0.0
    for d in dates:
        r = rets.loc[d].reindex(score_w.columns).fillna(0.0)
        gross = float((w * r).sum())
        if w.sum() > 0:
            w = w * (1.0 + r) / (1.0 + gross)
        cost = 0.0
        if d in exec_targets:
            dw = float((exec_targets[d] - w).abs().sum())
            cost = cost_leg * dw
            total_dw += dw
            w = exec_targets[d].copy()
        out.append(gross - cost)
    net = pd.Series(out, index=dates)
    ann_turnover = (total_dw / 2.0) / (len(dates) / 252.0)
    return net, ann_turnover


def perf(ret: pd.Series) -> tuple[float, float, float]:
    eq = (1.0 + ret).cumprod()
    return cagr(eq), sharpe(ret), max_drawdown(eq)


def sub_perf(ret: pd.Series) -> str:
    a = ret.loc[:"2019-12-31"]
    b = ret.loc["2020-01-01":]
    return (
        f"2018-2019 ann={cagr((1 + a).cumprod()):+.1%} shp={sharpe(a):+.2f} | "
        f"2020-2026 ann={cagr((1 + b).cumprod()):+.1%} shp={sharpe(b):+.2f}"
    )


def main() -> None:
    tickers = sorted({t for names in ss.SECTORS.values() for t in names})
    print(f"universe: {len(tickers)} names")
    store = DuckStore("./data")
    adj = store.load_close_pivot(tickers, column="adj_close")
    long = store.load_ohlcv(tickers)
    volume = long.pivot_table(index="ts", columns="symbol", values="volume", aggfunc="last")
    volume = volume.reindex(index=adj.index, columns=adj.columns)
    bench = store.load_close_pivot(["QQQ", "VOO"], column="adj_close")
    print(f"prices: {adj.index[0].date()} .. {adj.index[-1].date()}  ({len(adj)} bars)")

    panel = build_panel(adj, volume)
    dates_level = panel.index.get_level_values(0)

    preds, preds_shuf = [], []
    imp_sum = pd.Series(0.0, index=FEATURES)
    print("\nwalk-forward yearly refit (purge gap = 21 train days):")
    for y in OOS_YEARS:
        tr = panel[dates_level < pd.Timestamp(f"{y}-01-01")].dropna(subset=["label"])
        tr_dates = tr.index.get_level_values(0).unique().sort_values()
        tr = tr[tr.index.get_level_values(0).isin(tr_dates[:-PURGE])]
        te = panel[
            (dates_level >= pd.Timestamp(f"{y}-01-01"))
            & (dates_level <= pd.Timestamp(f"{y}-12-31"))
        ]
        if te.empty:
            continue
        model = lgb.LGBMRegressor(**LGB_PARAMS)
        model.fit(tr[FEATURES], tr["label"])
        preds.append(pd.Series(model.predict(te[FEATURES]), index=te.index))
        imp = pd.Series(model.feature_importances_, index=FEATURES)
        imp_sum += imp / imp.sum()
        rng = np.random.default_rng(1000 + y)
        m2 = lgb.LGBMRegressor(**LGB_PARAMS)
        m2.fit(tr[FEATURES], tr["label"].to_numpy()[rng.permutation(len(tr))])
        preds_shuf.append(pd.Series(m2.predict(te[FEATURES]), index=te.index))
        print(f"  {y}: train={len(tr):>7,} rows (thru {tr_dates[:-PURGE][-1].date()}), test={len(te):>6,} rows")

    pred = pd.concat(preds).sort_index()
    pred_sh = pd.concat(preds_shuf).sort_index()
    label = panel["label"]

    n_days = pred.index.get_level_values(0).nunique()
    xs = pred.groupby(level=0).size()
    print(f"\nOOS panel: {len(pred):,} name-days over {n_days} days "
          f"({pred.index.get_level_values(0).min().date()} .. "
          f"{pred.index.get_level_values(0).max().date()})")
    print(f"cross-section size: min={xs.min()} median={int(xs.median())} max={xs.max()}")

    # ---- rank IC ----
    ic = daily_rank_ic(pred, label)
    ic_sh = daily_rank_ic(pred_sh, label)
    m, t, n_no = ic_stats(ic)
    m_sh, t_sh, _ = ic_stats(ic_sh)
    lbl = label.reindex(pred.index)
    mask = lbl.notna()
    r2_oos = 1.0 - ((lbl[mask] - pred[mask]) ** 2).sum() / (lbl[mask] ** 2).sum()
    print(f"\nOOS daily rank-IC: mean={m:+.4f}  t(non-overlap, n={n_no})={t:+.2f}  "
          f"%pos={float((ic > 0).mean()):.1%}")
    print(f"SHUFFLED control : mean={m_sh:+.4f}  t={t_sh:+.2f}")
    print(f"OOS R2 (vs zero forecast, GKX-style): {r2_oos:+.4f}")
    print("\nIC by year:")
    for y, g in ic.groupby(ic.index.year):
        print(f"  {y}: mean={g.mean():+.4f}  %pos={float((g > 0).mean()):.0%}")

    # ---- portfolios ----
    pred_w = pred.unstack()
    pred_sh_w = pred_sh.unstack()
    oos_dates = pred_w.index
    rets = adj.pct_change(fill_method=None).loc[oos_dates]
    mom = (adj.shift(1 + LABEL_H) / adj.shift(1 + 126) - 1.0).loc[oos_dates]  # 6-1, lagged 1

    ml_ret, ml_to = run_portfolio(pred_w, rets)
    mom_ret, mom_to = run_portfolio(mom, rets)
    sh_ret, sh_to = run_portfolio(pred_sh_w, rets)
    ew_ret = rets.mean(axis=1)
    qqq_ret = bench["QQQ"].pct_change(fill_method=None).reindex(oos_dates).fillna(0.0)
    voo_ret = bench["VOO"].pct_change(fill_method=None).reindex(oos_dates).fillna(0.0)

    rows = [
        ("ML LightGBM top-10 (net 10bps)", ml_ret, ml_to),
        ("Momentum 6-1 top-10 (net 10bps)", mom_ret, mom_to),
        ("SHUFFLED-label control (net)", sh_ret, sh_to),
        ("EW-47 buy&hold (no cost)", ew_ret, 0.0),
        ("QQQ buy&hold", qqq_ret, 0.0),
        ("VOO buy&hold", voo_ret, 0.0),
    ]
    print(f"\nportfolio results {oos_dates[0].date()} .. {oos_dates[-1].date()} "
          f"({len(oos_dates)} days):")
    print(f"{'strategy':<34} {'annret':>8} {'sharpe':>7} {'mdd':>8} {'turnover':>9}")
    for name, r, to in rows:
        a, s, d = perf(r)
        print(f"{name:<34} {a:>+8.1%} {s:>7.2f} {d:>8.1%} {to:>8.1f}x")

    print("\nsub-periods (F7):")
    for name, r, _ in rows[:5]:
        print(f"  {name:<34} {sub_perf(r)}")

    print("\nfeature importance (mean normalized gain across 9 refits):")
    for f, v in (imp_sum / len(OOS_YEARS)).sort_values(ascending=False).items():
        print(f"  {f:<12} {v:.3f}")

    # ---- charts ----
    eq = {name: (1 + r).cumprod() for name, r, _ in rows}
    fig, ax = plt.subplots(figsize=(10, 5))
    styles = {
        "ML LightGBM top-10 (net 10bps)": ("tab:blue", 1.8),
        "Momentum 6-1 top-10 (net 10bps)": ("tab:orange", 1.3),
        "SHUFFLED-label control (net)": ("tab:red", 1.0),
        "EW-47 buy&hold (no cost)": ("tab:green", 1.3),
        "QQQ buy&hold": ("gray", 1.0),
        "VOO buy&hold": ("lightgray", 1.0),
    }
    for name, e in eq.items():
        c, lw = styles[name]
        ax.plot(e.index, e.values, label=name, color=c, lw=lw)
    ax.set_yscale("log")
    ax.set_title("TR-08 ML hybrid forecast: OOS 2018-2026, monthly top-10, net costs")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr08_equity.png", dpi=120)

    fig2, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].plot(ic.index, ic.rolling(126).mean(), color="tab:blue", label="ML")
    axes[0].plot(ic_sh.index, ic_sh.rolling(126).mean(), color="tab:red", label="shuffled")
    axes[0].axhline(0, color="k", lw=0.8)
    axes[0].set_title("rolling 126d mean rank-IC")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)
    axes[1].hist(ic.values, bins=50, color="tab:blue", alpha=0.7)
    axes[1].axvline(ic.mean(), color="k", ls="--", label=f"mean={ic.mean():+.3f}")
    axes[1].set_title("daily rank-IC distribution")
    axes[1].legend(fontsize=8)
    imp_avg = (imp_sum / len(OOS_YEARS)).sort_values()
    axes[2].barh(imp_avg.index, imp_avg.values, color="tab:blue")
    axes[2].set_title("LightGBM gain importance (mean)")
    fig2.tight_layout()
    fig2.savefig("docs/tests/img/tr08_ic_diag.png", dpi=120)
    print("\nsaved: docs/tests/img/tr08_equity.png, docs/tests/img/tr08_ic_diag.png")


if __name__ == "__main__":
    main()
