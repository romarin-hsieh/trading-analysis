# ruff: noqa: E402
"""TR-02: Markov regime-switching (Hamilton 1989) volatility-regime gate, walk-forward.

Design (per docs/17 fabric spec):
  - QQQ daily returns 2015-2026 + SPY replication (~5780 bars total).
  - Walk-forward leak-free: refit MONTHLY on expanding window (min 750 bars),
    2-regime MarkovRegression with switching_variance=True on log returns (pct).
  - Signal = FILTERED probability of the low-variance regime (never smoothed).
    Variant A ("monthly"): P_low at the LAST in-sample bar, held for the next month.
    Variant B ("daily"): Hamilton filter run daily with the frozen params from the
    last monthly refit (filtered prob at bar t only uses data <= t -> leak-free).
  - Position: long QQQ/SPY when P(low-vol) > 0.5, else cash at 0%. shift(1) applied.
  - Costs: 5 bps per leg on turnover (ETF).
  - Competitors: buy & hold, SMA200 rule (close > SMA200, shift(1), same costs).
  - Control: 200 random permutations of the daily position series (shuffled regimes).
"""

from loguru import logger

logger.remove()

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from trading_analysis.backtest.metrics import max_drawdown, sharpe
from trading_analysis.data.store import DuckStore

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = ROOT / "docs" / "tests" / "img"
IMG_DIR.mkdir(parents=True, exist_ok=True)

MIN_TRAIN = 750
COST = 0.0005  # 5 bps per leg (ETF)
THRESH = 0.5
N_SHUFFLE = 200
SEED = 42
TRADING_DAYS = 252


def ann_return(returns: pd.Series) -> float:
    if len(returns) < 2:
        return 0.0
    eq = float((1.0 + returns).prod())
    years = len(returns) / TRADING_DAYS
    return eq ** (1.0 / years) - 1.0 if eq > 0 else -1.0


def month_end_positions(idx: pd.DatetimeIndex) -> list[int]:
    ser = pd.Series(np.arange(len(idx)), index=idx)
    return ser.groupby([idx.year, idx.month]).last().tolist()


def walk_forward_markov(r_log: pd.Series) -> tuple[pd.Series, pd.Series, dict]:
    """Return (p_low_daily, p_low_monthly, fit_info). Signals are 'known at close of bar t'."""
    y = r_log.to_numpy()
    n = len(y)
    me = month_end_positions(r_log.index)
    p_daily = np.full(n, np.nan)
    p_monthly = np.full(n, np.nan)
    prev_params = None
    n_fit, n_fail = 0, 0
    sig_low, sig_high = [], []
    for k, i in enumerate(me):
        if i + 1 < MIN_TRAIN:
            continue
        j = me[k + 1] if k + 1 < len(me) else n - 1
        if j <= i:
            continue
        try:
            mod = MarkovRegression(y[: i + 1], k_regimes=2, trend="c", switching_variance=True)
            res = mod.fit(start_params=prev_params, disp=False)
            params = res.params
            prev_params = params
            names = mod.param_names
            s0 = float(params[names.index("sigma2[0]")])
            s1 = float(params[names.index("sigma2[1]")])
            low = 0 if s0 < s1 else 1
            sig_low.append(min(s0, s1))
            sig_high.append(max(s0, s1))
            fp = res.filtered_marginal_probabilities  # (i+1, 2) ndarray
            p_month = float(fp[i, low])
            # signal held constant for bars t in [i, j-1] -> trades returns t+1 in (i, j]
            p_monthly[i:j] = p_month
            # daily: freeze params, run Hamilton filter over extended data.
            # filtered prob at bar t uses only data <= t -> no leak.
            mod_ext = MarkovRegression(y[: j + 1], k_regimes=2, trend="c", switching_variance=True)
            res_ext = mod_ext.filter(params)
            p_daily[i:j] = res_ext.filtered_marginal_probabilities[i:j, low]
            n_fit += 1
        except Exception:
            n_fail += 1
            if i >= 1 and not np.isnan(p_monthly[i - 1]):
                p_monthly[i:j] = p_monthly[i - 1]
            if i >= 1 and not np.isnan(p_daily[i - 1]):
                p_daily[i:j] = p_daily[i - 1]
    info = {
        "n_fit": n_fit,
        "n_fail": n_fail,
        "med_sigma_low": float(np.median(sig_low)) if sig_low else np.nan,
        "med_sigma_high": float(np.median(sig_high)) if sig_high else np.nan,
    }
    return (
        pd.Series(p_daily, index=r_log.index),
        pd.Series(p_monthly, index=r_log.index),
        info,
    )


def net_strategy(ret: pd.Series, pos_signal: pd.Series, cost: float = COST) -> pd.Series:
    """pos_signal known at close of t -> applied to return t+1; cost per leg on turnover."""
    pos_applied = pos_signal.shift(1).fillna(0.0)
    turnover = pos_applied.diff().abs().fillna(0.0)
    return pos_applied * ret - cost * turnover


def stats_row(name: str, ret: pd.Series) -> dict:
    eq = (1.0 + ret).cumprod()
    return {
        "name": name,
        "ann": ann_return(ret),
        "sharpe": sharpe(ret),
        "mdd": max_drawdown(eq),
    }


def main() -> None:
    store = DuckStore(ROOT / "data")
    px = store.load_close_pivot(["QQQ", "SPY"], column="adj_close").dropna()
    px = px.loc["2015-01-01":]
    print(f"data: {px.index[0].date()} -> {px.index[-1].date()}, bars={len(px)}")

    results = {}
    summary_rows = []
    rng = np.random.default_rng(SEED)

    for sym in ["QQQ", "SPY"]:
        close = px[sym]
        ret = close.pct_change().dropna()
        r_log = np.log(close / close.shift(1)).dropna() * 100.0

        p_daily, p_monthly, info = walk_forward_markov(r_log)
        print(
            f"[{sym}] refits={info['n_fit']} fails={info['n_fail']} "
            f"med sigma2 low/high={info['med_sigma_low']:.3f}/{info['med_sigma_high']:.3f} "
            f"(daily pct-ret variance)"
        )

        oos = p_monthly.dropna().index
        oos_ret = ret.loc[oos]
        n_oos = len(oos_ret)
        print(f"[{sym}] OOS window: {oos[0].date()} -> {oos[-1].date()}, bars={n_oos}")

        pos_m = (p_monthly.loc[oos] > THRESH).astype(float)
        pos_d = (p_daily.loc[oos] > THRESH).astype(float)
        sma200 = close.rolling(200).mean()
        pos_sma = (close > sma200).astype(float).loc[oos]

        strat_m = net_strategy(oos_ret, pos_m)
        strat_d = net_strategy(oos_ret, pos_d)
        strat_sma = net_strategy(oos_ret, pos_sma)
        bh = oos_ret.copy()

        years = n_oos / TRADING_DAYS
        to_m = float(pos_m.shift(1).fillna(0.0).diff().abs().sum()) / years
        to_d = float(pos_d.shift(1).fillna(0.0).diff().abs().sum()) / years
        to_sma = float(pos_sma.shift(1).fillna(0.0).diff().abs().sum()) / years

        # regime identification quality: predictive (label at t, realized ret at t+1)
        lab = pos_d.shift(1).dropna()
        r_next = oos_ret.loc[lab.index]
        vol_low = float(r_next[lab == 1].std() * np.sqrt(TRADING_DAYS))
        vol_high = float(r_next[lab == 0].std() * np.sqrt(TRADING_DAYS))
        share_low = float((lab == 1).mean())
        print(
            f"[{sym}] regime quality (predictive): ann vol low={vol_low:.1%} "
            f"high={vol_high:.1%} ratio={vol_high / vol_low:.2f} share_low={share_low:.1%}"
        )

        # shuffled-regime control on the daily position series
        null_sharpes = []
        pos_vals = pos_d.to_numpy()
        for _ in range(N_SHUFFLE):
            perm = pd.Series(rng.permutation(pos_vals), index=pos_d.index)
            null_sharpes.append(sharpe(net_strategy(oos_ret, perm)))
        null_sharpes = np.array(null_sharpes)
        null_mean = float(null_sharpes.mean())
        null_p95 = float(np.percentile(null_sharpes, 95))
        pct_m = float((null_sharpes < sharpe(strat_m)).mean())
        pct_d = float((null_sharpes < sharpe(strat_d)).mean())
        print(
            f"[{sym}] shuffle control ({N_SHUFFLE}x): null Sharpe mean={null_mean:.2f} "
            f"p95={null_p95:.2f} | monthly pct={pct_m:.0%} daily pct={pct_d:.0%}"
        )

        rows = [
            stats_row(f"{sym} B&H", bh),
            stats_row(f"{sym} SMA200", strat_sma),
            stats_row(f"{sym} Markov monthly", strat_m),
            stats_row(f"{sym} Markov daily", strat_d),
        ]
        turnovers = {"B&H": 0.0, "SMA200": to_sma, "Markov monthly": to_m, "Markov daily": to_d}
        for row in rows:
            key = row["name"].replace(f"{sym} ", "")
            row["turnover"] = turnovers[key]
            summary_rows.append(row)
            print(
                f"  {row['name']:<20s} ann={row['ann']:+7.2%} sharpe={row['sharpe']:5.2f} "
                f"mdd={row['mdd']:7.2%} turnover={row['turnover']:.1f} legs/yr"
            )

        # sub-periods (F7)
        for label, lo, hi in [("2018-2019", None, "2019-12-31"), ("2020-2026", "2020-01-01", None)]:
            sl = slice(lo, hi)
            for nm, sr in [("B&H", bh), ("SMA200", strat_sma), ("Mkv-m", strat_m), ("Mkv-d", strat_d)]:
                sub = sr.loc[sl]
                if len(sub) > 20:
                    print(
                        f"  [{sym} {label}] {nm:<7s} ann={ann_return(sub):+7.2%} "
                        f"sharpe={sharpe(sub):5.2f}"
                    )

        results[sym] = {
            "ret": oos_ret,
            "bh": bh,
            "sma": strat_sma,
            "m": strat_m,
            "d": strat_d,
            "p_daily": p_daily.loc[oos],
            "vol_low": vol_low,
            "vol_high": vol_high,
            "share_low": share_low,
            "null_sharpes": null_sharpes,
        }

    total_oos = sum(len(results[s]["ret"]) for s in results)
    print(f"total OOS samples (bars x assets): {total_oos}")

    # ---- charts ----
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    for ax, sym in zip(axes, ["QQQ", "SPY"], strict=True):
        rr = results[sym]
        for nm, sr, c in [
            ("B&H", rr["bh"], "black"),
            ("SMA200", rr["sma"], "tab:orange"),
            ("Markov monthly", rr["m"], "tab:blue"),
            ("Markov daily", rr["d"], "tab:green"),
        ]:
            ax.plot((1 + sr).cumprod(), label=nm, color=c, lw=1.2)
        ax.set_yscale("log")
        ax.set_title(f"TR-02 {sym}: walk-forward Markov vol-regime gate vs B&H vs SMA200 (net 5bps/leg)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr02_equity.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    rr = results["QQQ"]
    axes[0].plot(rr["p_daily"], lw=0.6, color="tab:blue")
    axes[0].axhline(THRESH, color="red", ls="--", lw=0.8)
    axes[0].set_title("QQQ filtered P(low-vol), daily walk-forward")
    axes[0].grid(alpha=0.3)
    labels = ["QQQ low", "QQQ high", "SPY low", "SPY high"]
    vols = [
        results["QQQ"]["vol_low"],
        results["QQQ"]["vol_high"],
        results["SPY"]["vol_low"],
        results["SPY"]["vol_high"],
    ]
    colors = ["tab:green", "tab:red", "tab:green", "tab:red"]
    axes[1].bar(labels, [v * 100 for v in vols], color=colors)
    axes[1].set_title("Ann vol (%) next-day by predicted regime")
    axes[1].grid(alpha=0.3, axis="y")
    axes[2].hist(rr["null_sharpes"], bins=30, color="grey", alpha=0.7)
    axes[2].axvline(sharpe(rr["m"]), color="tab:blue", lw=1.5, label="Markov monthly")
    axes[2].axvline(sharpe(rr["d"]), color="tab:green", lw=1.5, label="Markov daily")
    axes[2].axvline(sharpe(rr["bh"]), color="black", lw=1.5, label="B&H")
    axes[2].set_title(f"QQQ shuffled-regime null ({N_SHUFFLE}x), net Sharpe")
    axes[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr02_diagnostics.png", dpi=120)
    plt.close(fig)
    print("charts saved: docs/tests/img/tr02_equity.png, tr02_diagnostics.png")


if __name__ == "__main__":
    main()
