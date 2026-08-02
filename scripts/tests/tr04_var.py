# ruff: noqa: E402
"""TR-04 Value-at-Risk: measurement quality + VaR-targeting overlay.

Part A (measurement): walk-forward 1-day 95%/99% VaR for QQQ and the EW-47
portfolio using three estimators fitted on a lagged 252d window (historical
percentile, parametric normal, Cornish-Fisher). Coverage backtested with the
Kupiec (1995) proportion-of-failures LR test.

Part B (overlay): scale QQQ daily so the lagged historical VaR99 forecast of
the position is <= 2% of equity (leverage cap 1.0), net 5 bps/leg on turnover;
compared against QQQ buy&hold, VOO buy&hold, a 12% vol-target, a constant-
weight control and a time-shuffled-weight control (F6).

Refs: RiskMetrics Technical Document (J.P. Morgan, 1996); Kupiec (1995),
"Techniques for Verifying the Accuracy of Risk Measurement Models"; ibaris/VaR.

Run from repo root: uv run python scripts/tests/tr04_var.py
"""

from __future__ import annotations

from loguru import logger

logger.remove()

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "scripts")
import sector_strategies as ss

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
from trading_analysis.data.store import DuckStore

WINDOW = 252
LEVELS = {"95": 0.05, "99": 0.01}
ETF_COST = 5e-4  # 5 bps per leg on turnover (F2)
VAR_BUDGET = 0.02  # overlay: forecast 99% VaR <= 2% of equity
VOL_TARGET = 0.12  # comparison overlay: 12% annualized vol target
SPLIT = "2020-01-01"  # F7 sub-period split
IMG = "docs/tests/img"


# ---------------------------------------------------------------- Part A ----
def var_forecasts(r: pd.Series) -> dict[str, pd.DataFrame]:
    """Walk-forward VaR forecasts for day t from window [t-252, t-1] (F1: lagged)."""
    mu = r.rolling(WINDOW).mean().shift(1)
    sd = r.rolling(WINDOW).std(ddof=1).shift(1)
    sk = r.rolling(WINDOW).skew().shift(1)
    ku = r.rolling(WINDOW).kurt().shift(1)  # excess kurtosis
    out = {}
    for name, a in LEVELS.items():
        z = stats.norm.ppf(a)
        zcf = (z + (z**2 - 1) * sk / 6 + (z**3 - 3 * z) * ku / 24
               - (2 * z**3 - 5 * z) * sk**2 / 36)
        out[name] = pd.DataFrame({
            "hist": r.rolling(WINDOW).quantile(a).shift(1),
            "normal": mu + sd * z,
            "cf": mu + sd * zcf,
        }).dropna()
    return out


def kupiec_pof(n_viol: int, n_obs: int, p: float) -> tuple[float, float]:
    """Kupiec POF LR statistic and p-value (chi2, df=1)."""
    pi = n_viol / n_obs

    def ll(q: float) -> float:
        out = (n_obs - n_viol) * np.log(1 - q)
        if n_viol > 0:
            out += n_viol * np.log(q)
        return out

    if pi >= 1.0:
        return np.inf, 0.0
    lr = -2.0 * (ll(p) - ll(pi))
    return float(lr), float(1 - stats.chi2.cdf(lr, df=1))


def coverage_table(returns: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for asset, r in returns.items():
        fc = var_forecasts(r)
        for lvl, a in LEVELS.items():
            df = fc[lvl]
            rr = r.reindex(df.index)
            for est in ["hist", "normal", "cf"]:
                viol = rr < df[est]
                n, x = len(viol), int(viol.sum())
                lr, pv = kupiec_pof(x, n, a)
                pre = viol[viol.index < SPLIT]
                post = viol[viol.index >= SPLIT]
                rows.append({
                    "asset": asset, "level": lvl, "est": est, "n_obs": n,
                    "viol": x, "rate": x / n, "nominal": a, "LR": lr, "p": pv,
                    "kupiec": "PASS" if pv > 0.05 else "FAIL",
                    "rate_pre": float(pre.mean()), "rate_post": float(post.mean()),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Part B ----
def overlay_path(w: pd.Series, r: pd.Series, cost: float = ETF_COST) -> dict:
    w = w.clip(0.0, 1.0)
    turn = w.diff().abs()
    turn.iloc[0] = abs(w.iloc[0])  # initial entry leg
    net = w * r - turn * cost
    eq = (1 + net).cumprod()
    years = len(net) / 252
    pre, post = net[net.index < SPLIT], net[net.index >= SPLIT]
    return {
        "ret": net, "eq": eq, "cagr": cagr(eq), "sharpe": sharpe(net),
        "mdd": max_drawdown(eq), "vol": float(net.std(ddof=1) * np.sqrt(252)),
        "turnover": float(turn.sum() / years), "avg_w": float(w.mean()),
        "cagr_pre": cagr((1 + pre).cumprod()), "sharpe_pre": sharpe(pre),
        "cagr_post": cagr((1 + post).cumprod()), "sharpe_post": sharpe(post),
        "w": w,
    }


def main() -> None:
    store = DuckStore("./data")
    all47 = sorted({t for v in ss.SECTORS.values() for t in v})
    qqq = store.load_close_pivot(["QQQ"], column="adj_close").ffill().iloc[:, 0]
    voo = store.load_close_pivot(["VOO"], column="adj_close").ffill().iloc[:, 0]
    px47 = store.load_close_pivot(all47, column="adj_close").ffill()
    r_qqq = qqq.pct_change().dropna()
    r_voo = voo.pct_change().dropna()
    r_ew = px47.pct_change().mean(axis=1).dropna()
    print(f"data: QQQ {qqq.index[0].date()}..{qqq.index[-1].date()} ({len(r_qqq)} rets), "
          f"EW-47 {len(r_ew)} rets, {px47.shape[1]} tickers")

    # ---- Part A: coverage
    cov = coverage_table({"QQQ": r_qqq, "EW47": r_ew})
    print("\n=== Part A: Kupiec POF coverage (252d walk-forward, lagged) ===")
    print(f"{'asset':6}{'lvl':5}{'est':8}{'n':>6}{'viol':>6}{'rate%':>8}{'nom%':>6}"
          f"{'LR':>8}{'p':>8}  {'kupiec':7}{'pre%':>7}{'post%':>7}")
    for _, q in cov.iterrows():
        print(f"{q['asset']:6}{q['level']:5}{q['est']:8}{q['n_obs']:>6}{q['viol']:>6}"
              f"{q['rate'] * 100:>8.2f}{q['nominal'] * 100:>6.1f}{q['LR']:>8.2f}"
              f"{q['p']:>8.4f}  {q['kupiec']:7}{q['rate_pre'] * 100:>7.2f}"
              f"{q['rate_post'] * 100:>7.2f}")
    n_fc = int(cov[cov["level"] == "99"]["n_obs"].sum())  # per estimator-asset days
    total_fc = int(cov["n_obs"].sum())
    print(f"\nsamples: {n_fc} forecast-days at 99% level (2 assets x 3 estimators); "
          f"both levels total {total_fc}")

    # ---- Part B: overlay on QQQ
    fc_q = var_forecasts(r_qqq)
    var99 = fc_q["99"]["hist"]
    var99_cf = fc_q["99"]["cf"]
    vol20 = (r_qqq.rolling(20).std(ddof=1) * np.sqrt(252)).shift(1)
    idx = var99.index.intersection(vol20.dropna().index)
    r = r_qqq.reindex(idx)

    w_var = (VAR_BUDGET / var99.abs()).reindex(idx)
    w_var_cf = (VAR_BUDGET / var99_cf.abs()).reindex(idx)
    w_vol = (VOL_TARGET / vol20).reindex(idx)
    rng = np.random.default_rng(42)
    w_shuf = pd.Series(rng.permutation(w_var.clip(0, 1).values), index=idx)

    paths = {
        "QQQ B&H": overlay_path(pd.Series(1.0, index=idx), r),
        # VOO history in store ends 2026-06-18: flat-line the last 9 days (ret=0)
        "VOO B&H": overlay_path(pd.Series(1.0, index=idx), r_voo.reindex(idx).fillna(0.0)),
        "VaR99-target 2% (hist)": overlay_path(w_var, r),
        "VaR99-target 2% (CF)": overlay_path(w_var_cf, r),
        "vol-target 12%": overlay_path(w_vol, r),
        "const-w control": overlay_path(pd.Series(float(w_var.clip(0, 1).mean()),
                                                  index=idx), r),
        "shuffled-w control": overlay_path(w_shuf, r),
    }
    print(f"\n=== Part B: QQQ overlays {idx[0].date()}..{idx[-1].date()} "
          f"({len(idx)} days, net {ETF_COST * 1e4:.0f}bps/leg) ===")
    print(f"{'strategy':24}{'CAGR%':>8}{'Sharpe':>8}{'MDD%':>8}{'vol%':>7}"
          f"{'turn/yr':>8}{'avgW':>6}{'pre-CAGR%':>10}{'post-CAGR%':>11}")
    for name, m in paths.items():
        print(f"{name:24}{m['cagr'] * 100:>8.2f}{m['sharpe']:>8.2f}{m['mdd'] * 100:>8.2f}"
              f"{m['vol'] * 100:>7.1f}{m['turnover']:>8.2f}{m['avg_w']:>6.2f}"
              f"{m['cagr_pre'] * 100:>10.2f}{m['cagr_post'] * 100:>11.2f}")

    # realized 99% VaR of the overlay vs budget (did the overlay do its job?)
    real_var = float(np.percentile(paths["VaR99-target 2% (hist)"]["ret"], 1))
    real_var_bh = float(np.percentile(paths["QQQ B&H"]["ret"], 1))
    print(f"\nrealized 1% quantile of daily returns: overlay {real_var * 100:.2f}% "
          f"(budget -2.00%), QQQ B&H {real_var_bh * 100:.2f}%")

    # ---- charts
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for ax, lvl in zip(axes, ["95", "99"], strict=False):
        sub = cov[cov["level"] == lvl]
        labels = [f"{e}\n{a}" for a in ["QQQ", "EW47"] for e in ["hist", "normal", "cf"]]
        vals = [sub[(sub["asset"] == a) & (sub["est"] == e)]["rate"].iloc[0] * 100
                for a in ["QQQ", "EW47"] for e in ["hist", "normal", "cf"]]
        colors = ["tab:blue"] * 3 + ["tab:orange"] * 3
        ax.bar(range(6), vals, color=colors)
        ax.axhline(LEVELS[lvl] * 100, color="k", ls="--", lw=1,
                   label=f"nominal {LEVELS[lvl] * 100:.0f}%")
        ax.set_xticks(range(6), labels, fontsize=8)
        ax.set_title(f"VaR{lvl} violation rate (Kupiec)")
        ax.set_ylabel("violation rate %")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr04_coverage.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(r_qqq.reindex(fc_q["99"].index) * 100, lw=0.3, color="gray", alpha=0.6,
            label="QQQ daily ret")
    for est, c in [("hist", "tab:blue"), ("normal", "tab:red"), ("cf", "tab:green")]:
        ax.plot(fc_q["99"][est] * 100, lw=0.9, color=c, label=f"VaR99 {est}")
    ax.set_title("QQQ daily returns vs walk-forward VaR99 forecasts")
    ax.set_ylabel("%")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr04_var99_lines.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for name, c in [("QQQ B&H", "k"), ("VaR99-target 2% (hist)", "tab:blue"),
                    ("vol-target 12%", "tab:green"), ("const-w control", "tab:gray"),
                    ("shuffled-w control", "tab:red")]:
        axes[0].plot(paths[name]["eq"], lw=1, color=c, label=name)
    axes[0].set_yscale("log")
    axes[0].set_title("QQQ overlays, net 5bps/leg (log)")
    axes[0].legend(fontsize=7)
    axes[1].plot(w_var.clip(0, 1).rolling(21).mean(), lw=0.9, color="tab:blue",
                 label="w VaR99-target (21d ma)")
    axes[1].plot(w_vol.clip(0, 1).rolling(21).mean(), lw=0.9, color="tab:green",
                 label="w vol-target (21d ma)")
    axes[1].set_title("overlay weights")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{IMG}/tr04_overlay.png", dpi=120)
    plt.close(fig)
    print(f"\ncharts saved to {IMG}/tr04_*.png")


if __name__ == "__main__":
    main()
