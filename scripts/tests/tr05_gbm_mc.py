"""TR-05: Monte Carlo under GBM (Black-Scholes-Merton dynamics) as a RISK model for tech equity.

Question: does standard GBM Monte Carlo describe the actual risk of QQQ?
Design (leak-free, F1): calibrate mu/sigma on QQQ 2015-2019 daily log returns ONLY;
simulate 20,000 GBM paths with length = realized 2020-2026 bar count; compare the
simulated distribution against REALIZED 2020-2026 (terminal return percentile, MDD
distribution, per-path skew/kurtosis, worst-day probability). Controls/alternatives:
  - IID bootstrap of 2015-2019 real returns (fat marginals, no clustering) = F6 control
  - stationary block bootstrap (mean block 21d) of 2015-2019 returns = honest alternative
No trading strategy is formed -> turnover 0, costs n/a (F2 reported as such).
"""
# ruff: noqa: E402

from loguru import logger

logger.remove()

import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe
from trading_analysis.data.store import DuckStore

RNG = np.random.default_rng(42)
N_PATHS = 20_000
MEAN_BLOCK = 21
IMG_DIR = Path("docs/tests/img")
IMG_DIR.mkdir(parents=True, exist_ok=True)


def path_stats(logret: np.ndarray) -> dict:
    """Per-path summary stats for a (n_paths, n_steps) matrix of daily log returns."""
    equity = np.exp(np.cumsum(logret, axis=1))
    terminal = equity[:, -1] - 1.0
    running_max = np.maximum.accumulate(equity, axis=1)
    mdd = (equity / running_max - 1.0).min(axis=1)
    simple = np.exp(logret) - 1.0
    worst_day = simple.min(axis=1)
    skew = stats.skew(logret, axis=1)
    exkurt = stats.kurtosis(logret, axis=1)  # excess (Fisher)
    mu_d = logret.mean(axis=1)
    sd_d = logret.std(axis=1, ddof=1)
    path_sharpe = np.sqrt(252.0) * simple.mean(axis=1) / simple.std(axis=1, ddof=1)
    n_years = logret.shape[1] / 252.0
    ann_ret = (1.0 + terminal) ** (1.0 / n_years) - 1.0
    eq_pct = np.percentile(equity, [5, 25, 50, 75, 95], axis=0)
    return {
        "terminal": terminal,
        "ann_ret": ann_ret,
        "mdd": mdd,
        "worst_day": worst_day,
        "skew": skew,
        "exkurt": exkurt,
        "mu_d": mu_d,
        "sd_d": sd_d,
        "sharpe": path_sharpe,
        "eq_pct": eq_pct,
    }


def summarize(name: str, st: dict, realized: dict) -> dict:
    """Print and return the comparison summary of one simulator vs realized 2020-2026."""
    term_pctile = float((st["terminal"] < realized["terminal"]).mean() * 100)
    p_mdd30 = float((st["mdd"] <= -0.30).mean())
    p_mdd_real = float((st["mdd"] <= realized["mdd"]).mean())
    p_any_crash_day = float((st["worst_day"] <= realized["worst_day"]).mean())
    out = {
        "name": name,
        "med_ann": float(np.median(st["ann_ret"])),
        "med_sharpe": float(np.median(st["sharpe"])),
        "med_mdd": float(np.median(st["mdd"])),
        "mdd_p5": float(np.percentile(st["mdd"], 5)),
        "term_pctile": term_pctile,
        "p_mdd30": p_mdd30,
        "p_mdd_real": p_mdd_real,
        "p_any_crash_day": p_any_crash_day,
        "kurt_med": float(np.median(st["exkurt"])),
        "kurt_p99": float(np.percentile(st["exkurt"], 99)),
        "skew_med": float(np.median(st["skew"])),
        "worst_day_med": float(np.median(st["worst_day"])),
        "worst_day_min": float(st["worst_day"].min()),
    }
    print(f"--- {name} ({N_PATHS} paths) ---")
    print(f"  median ann return        : {out['med_ann'] * 100:8.2f} %")
    print(f"  median path Sharpe       : {out['med_sharpe']:8.2f}")
    print(f"  median path MDD          : {out['med_mdd'] * 100:8.2f} %")
    print(f"  MDD 5th pctile (bad tail): {out['mdd_p5'] * 100:8.2f} %")
    print(f"  P(MDD <= -30%)           : {out['p_mdd30'] * 100:8.3f} %")
    print(f"  P(MDD <= realized {realized['mdd'] * 100:.1f}%): {out['p_mdd_real'] * 100:8.3f} %")
    print(f"  realized terminal pctile : {out['term_pctile']:8.2f} (pct of paths below reality)")
    print(f"  P(any day <= realized worst {realized['worst_day'] * 100:.1f}%): {out['p_any_crash_day'] * 100:8.4f} %")
    print(f"  per-path excess kurtosis : median {out['kurt_med']:.2f} | p99 {out['kurt_p99']:.2f}")
    print(f"  per-path skew (median)   : {out['skew_med']:.3f}")
    print(f"  worst simulated day      : median {out['worst_day_med'] * 100:.2f} % | min {out['worst_day_min'] * 100:.2f} %")
    return out


def stationary_bootstrap_idx(n_src: int, n_steps: int, n_paths: int, mean_block: float) -> np.ndarray:
    """Politis-Romano stationary bootstrap index matrix (n_paths, n_steps), circular."""
    p_new = 1.0 / mean_block
    idx = np.empty((n_paths, n_steps), dtype=np.int64)
    idx[:, 0] = RNG.integers(0, n_src, size=n_paths)
    for t in range(1, n_steps):
        restart = RNG.random(n_paths) < p_new
        cont = (idx[:, t - 1] + 1) % n_src
        idx[:, t] = np.where(restart, RNG.integers(0, n_src, size=n_paths), cont)
    return idx


def main() -> None:
    store = DuckStore("./data")
    px = store.load_close_pivot(["QQQ", "VOO"], column="adj_close").dropna()
    px.index = px.index.tz_localize(None) if px.index.tz is not None else px.index
    qqq = px["QQQ"]
    logret = np.log(qqq / qqq.shift(1)).dropna()

    calib = logret.loc["2015-01-01":"2019-12-31"]
    test = logret.loc["2020-01-01":]
    n_steps = len(test)
    print("=== TR-05 GBM Monte Carlo vs realized QQQ risk ===")
    print(f"calibration: {calib.index[0].date()} .. {calib.index[-1].date()}  n={len(calib)} bars")
    print(f"test       : {test.index[0].date()} .. {test.index[-1].date()}  n={n_steps} bars")

    m, s = float(calib.mean()), float(calib.std(ddof=1))
    mu_ann, sig_ann = m * 252 + 0.5 * s * s * 252, s * np.sqrt(252)
    print(f"calibrated daily log-ret mean={m:.6f} std={s:.6f}")
    print(f"GBM params: mu={mu_ann * 100:.2f}%/yr  sigma={sig_ann * 100:.2f}%/yr")

    # realized 2020-2026 facts
    test_simple = np.exp(test) - 1.0
    eq_real = np.exp(test.cumsum())
    realized = {
        "terminal": float(eq_real.iloc[-1] - 1.0),
        "ann": cagr(eq_real),
        "sharpe": sharpe(test_simple),
        "mdd": max_drawdown(eq_real),
        "worst_day": float(test_simple.min()),
        "skew": float(stats.skew(test.values)),
        "exkurt": float(stats.kurtosis(test.values)),
    }
    worst_day_date = test_simple.idxmin().date()
    print("--- REALIZED QQQ 2020-2026 ---")
    print(f"  terminal return {realized['terminal'] * 100:.1f}% | ann {realized['ann'] * 100:.2f}% | Sharpe {realized['sharpe']:.2f}")
    print(f"  MDD {realized['mdd'] * 100:.1f}% | worst day {realized['worst_day'] * 100:.2f}% on {worst_day_date}")
    print(f"  daily skew {realized['skew']:.2f} | excess kurtosis {realized['exkurt']:.2f}")

    # F7 sub-period: calibration-era moments for contrast
    calib_simple = np.exp(calib) - 1.0
    eq_calib = np.exp(calib.cumsum())
    print("--- SUB-PERIOD (F7): realized 2015-2019 (calibration era) ---")
    print(f"  ann {cagr(eq_calib) * 100:.2f}% | Sharpe {sharpe(calib_simple):.2f} | MDD {max_drawdown(eq_calib) * 100:.1f}%")
    print(f"  worst day {calib_simple.min() * 100:.2f}% | skew {stats.skew(calib.values):.2f} | exkurt {stats.kurtosis(calib.values):.2f}")

    # benchmarks (F3): buy & hold over the SAME evaluation window
    voo = np.log(px["VOO"] / px["VOO"].shift(1)).dropna().loc["2020-01-01":]
    voo_simple = np.exp(voo) - 1.0
    eq_voo = np.exp(voo.cumsum())
    print("--- BENCHMARK (F3): VOO buy&hold 2020-2026 ---")
    print(f"  ann {cagr(eq_voo) * 100:.2f}% | Sharpe {sharpe(voo_simple):.2f} | MDD {max_drawdown(eq_voo) * 100:.1f}%")
    print("  (QQQ buy&hold 2020-2026 IS the realized row above; turnover 0, costs n/a)")

    summaries = []

    # 1) GBM: iid normal daily log returns
    gbm = RNG.normal(m, s, size=(N_PATHS, n_steps))
    st_gbm = path_stats(gbm)
    del gbm
    summaries.append(summarize("GBM (iid normal, BSM)", st_gbm, realized))
    # analytic single-day crash probability under the fitted normal
    z = (np.log1p(realized["worst_day"]) - m) / s
    p_day = float(stats.norm.cdf(z))
    p_path = 1.0 - (1.0 - p_day) ** n_steps
    print(f"  [analytic] P(one day <= {realized['worst_day'] * 100:.1f}%) = {p_day:.3e} ({z:.1f} sigma)")
    print(f"  [analytic] P(at least one such day in {n_steps} bars) = {p_path:.3e}")
    print(f"  [analytic] expected wait for such a day = {1.0 / (p_day * 252):.2e} years")

    src = calib.values
    n_src = len(src)

    # 2) control (F6): iid bootstrap of real 2015-2019 returns (kills clustering, keeps marginals)
    iid_idx = RNG.integers(0, n_src, size=(N_PATHS, n_steps))
    st_iid = path_stats(src[iid_idx])
    del iid_idx
    summaries.append(summarize("IID bootstrap 2015-19 (control)", st_iid, realized))

    # 3) stationary block bootstrap (mean block = 21 days) of real 2015-2019 returns
    blk_idx = stationary_bootstrap_idx(n_src, n_steps, N_PATHS, MEAN_BLOCK)
    st_blk = path_stats(src[blk_idx])
    del blk_idx
    summaries.append(summarize("Stationary block bootstrap b=21", st_blk, realized))
    print(f"  [note] worst day in 2015-19 source = {(np.exp(src.min()) - 1) * 100:.2f}% -> any bootstrap of it")
    print("         cannot produce a single day below that support (structural limit).")

    # charts
    x = np.arange(n_steps)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    ax = axes[0]
    for st, color, lbl in [(st_gbm, "tab:blue", "GBM 5-95%"), (st_blk, "tab:orange", "BlockBoot 5-95%")]:
        ax.fill_between(x, st["eq_pct"][0], st["eq_pct"][4], alpha=0.18, color=color, label=lbl)
        ax.plot(x, st["eq_pct"][2], color=color, lw=1.0, alpha=0.8)
    ax.plot(x, eq_real.values, color="black", lw=1.6, label="Realized QQQ 2020-26")
    ax.set_title("20k-path fan vs realized QQQ")
    ax.set_xlabel("trading days since 2020-01-02")
    ax.set_ylabel("growth of $1")
    ax.legend(fontsize=8)
    ax = axes[1]
    bins = np.linspace(-0.75, 0.0, 76)
    ax.hist(st_gbm["mdd"], bins=bins, alpha=0.55, density=True, label="GBM", color="tab:blue")
    ax.hist(st_blk["mdd"], bins=bins, alpha=0.55, density=True, label="BlockBoot", color="tab:orange")
    ax.axvline(realized["mdd"], color="black", lw=1.6, label=f"Realized {realized['mdd'] * 100:.0f}%")
    ax.set_title("Max drawdown distribution (per path)")
    ax.set_xlabel("MDD")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr05_gbm_fan_mdd.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    ax = axes[0]
    bins = np.linspace(-1.0, 4.0, 101)
    ax.hist(st_gbm["terminal"], bins=bins, alpha=0.55, density=True, label="GBM", color="tab:blue")
    ax.hist(st_blk["terminal"], bins=bins, alpha=0.55, density=True, label="BlockBoot", color="tab:orange")
    ax.axvline(realized["terminal"], color="black", lw=1.6, label=f"Realized {realized['terminal'] * 100:.0f}%")
    ax.set_title("Terminal return distribution")
    ax.set_xlabel("total return over test window")
    ax.legend(fontsize=8)
    ax = axes[1]
    grid = np.linspace(-0.13, 0.13, 261)
    ax.hist(test.values, bins=grid, density=True, alpha=0.5, color="gray", label="Realized daily 2020-26")
    ax.plot(grid, stats.norm.pdf(grid, m, s), color="tab:blue", lw=1.5, label="GBM normal (2015-19 fit)")
    ax.axvline(np.log1p(realized["worst_day"]), color="black", lw=1.2, ls="--", label=f"worst day {realized['worst_day'] * 100:.1f}%")
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 200)
    ax.set_title("Daily log-return density (log scale) - the tail gap")
    ax.set_xlabel("daily log return")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr05_tails_terminal.png", dpi=120)
    plt.close(fig)
    print(f"charts saved: {IMG_DIR}/tr05_gbm_fan_mdd.png , {IMG_DIR}/tr05_tails_terminal.png")

    # compact comparison table
    print("=== SUMMARY TABLE (all vs realized QQQ 2020-2026) ===")
    hdr = f"{'model':32s} {'medAnn%':>8s} {'medShrp':>8s} {'medMDD%':>8s} {'P(MDD<=-30%)':>13s} {'P(MDD<=real)':>13s} {'termPctl':>9s} {'P(crashday)':>12s} {'kurt_med':>9s}"
    print(hdr)
    for o in summaries:
        print(
            f"{o['name']:32s} {o['med_ann'] * 100:8.2f} {o['med_sharpe']:8.2f} {o['med_mdd'] * 100:8.2f} "
            f"{o['p_mdd30'] * 100:12.3f}% {o['p_mdd_real'] * 100:12.3f}% {o['term_pctile']:8.1f}% "
            f"{o['p_any_crash_day'] * 100:11.4f}% {o['kurt_med']:9.2f}"
        )
    print(
        f"{'REALIZED QQQ 2020-2026':32s} {realized['ann'] * 100:8.2f} {realized['sharpe']:8.2f} "
        f"{realized['mdd'] * 100:8.2f} {'--':>13s} {'--':>13s} {'--':>9s} {'--':>12s} {realized['exkurt']:9.2f}"
    )
    print("F-rules: F1 calib strictly pre-2020 | F2 no strategy, turnover 0 | F3 QQQ+VOO B&H rows | "
          f"F4 {N_PATHS} paths x {n_steps} bars, data 2015-2026 | F5 3 simulators, no alpha claim | "
          "F6 iid-bootstrap control | F7 sub-period printed | F8 verdict in report")


if __name__ == "__main__":
    main()
