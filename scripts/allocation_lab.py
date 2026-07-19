"""Allocation Lab -- the honest version of a FIRE allocation dashboard.

Concept is public (allocations x Monte Carlo x percentile fans); implementation is
ours and fixes the three failure modes our TRs documented in normal-distribution
retirement calculators:
  1. NORMAL TAILS (TR-05: realized worst day = -11.8 sigma under GBM) -> E1 uses
     stationary BLOCK bootstrap of REAL joint monthly returns (mean block 24m keeps
     vol clustering and multi-year bears).
  2. SYNTHETIC LEVERAGE DRAG (mu - sigma^2/2 approximations) -> E1 uses the REAL
     NAV of 00631L (daily reset, fees, financing all live inside the price);
     E2 builds a DAILY-RESET 2x from FF daily market minus financing.
  3. SINGLE-REGIME ARC (TR-25/35: bootstrap cannot invent unseen regimes) -> E2
     replays every allocation through 1975-2026 US analogs with REAL CPI deflation:
     the stagflation badge (1975-1981 real drawdown) and 2022 badge are reported
     next to every allocation.
ANTI-OPTIMIZER BY DESIGN (F5/TR-22/TR-37): this lab presents a MENU, never a "best
cell". Rankings between adjacent allocations sit inside assumption error; only big
contrasts are meaningful. No grid search, no utility argmax.

Instruments (TW investor, TWD terms): 0050, 00631L (2x), 00679B (US 20y bond),
00635U (gold). E1 joint window 2017-02.. (bounded by 00679B). DCA: 1 real unit per
month x 360 months, monthly rebalance to target weights, 10bps round trip on
turnover, 2%/yr inflation to real terms (E1); E2 uses actual US CPI.

Outputs: exports/dashboard/allocation_lab.json + docs/img/allocation_lab.png.
Run: uv run python scripts/allocation_lab.py   (~2 min)
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

ETF_DIR = Path("data/finmind_tw/etf")
N_PATHS = 3000
MONTHS = 360
BLOCK_MEAN = 24
INFL = 0.02
COST_RT = 0.0010
SEED = 0
FIN_SPREAD = 0.006

# (name, w0050, w2x, wBond, wGold)
PRESETS = [
    ("經典 FIRE 80/20", 0.80, 0.00, 0.20, 0.00),
    ("股債 90/10", 0.90, 0.00, 0.10, 0.00),
    ("全市場 100/0", 1.00, 0.00, 0.00, 0.00),
    ("生命週期 50正2/50債", 0.00, 0.50, 0.50, 0.00),
    ("防禦槓桿 40正2/60債", 0.00, 0.40, 0.60, 0.00),
    ("三分 33/33/34", 0.33, 0.33, 0.34, 0.00),
    ("穩健小槓桿 65/5/30", 0.65, 0.05, 0.30, 0.00),
    ("積極小槓桿 70/5/25", 0.70, 0.05, 0.25, 0.00),
    ("保守防禦 40/0/60", 0.40, 0.00, 0.60, 0.00),
    ("小槓桿+金 55/5/25/15", 0.55, 0.05, 0.25, 0.15),
    ("防禦+金 35/0/45/20", 0.35, 0.00, 0.45, 0.20),
]


def tw_monthly() -> pd.DataFrame:
    """DIVIDEND-ADJUSTED monthly returns (Yahoo auto_adjust, data/finmind_tw/etf_adj).

    T1 catch from run 1: FinMind TaiwanStockPrice is UNadjusted -- 0050's ~2.5%/yr
    distributions (measured raw-vs-adj CAGR gap +2.49%/yr) were stripped while the
    accumulating 00631L kept its full return, rigging every comparison toward the
    leveraged ETF (the lifecycle mix 'dominated' with P10 3.1x). Total-return prices
    are mandatory for cross-asset allocation work; the same caveat is now on file for
    the TR-39 panel's price-only returns (rank-level second-order, level-relevant)."""
    cols = {}
    for sid in ("0050", "00631L", "00679B", "00635U"):
        d = pd.read_parquet(ETF_DIR.parent / "etf_adj" / f"{sid}.parquet")["close"]
        d.index = pd.to_datetime(d.index)
        cols[sid] = d.where(d > 0).resample("ME").last()
    px = pd.DataFrame(cols)
    r = px.pct_change(fill_method=None).dropna()
    return r


def fred_series(series: str, cache: str) -> pd.Series:
    p = Path(cache)
    if p.exists():
        s = pd.read_parquet(p)["v"]
        s.index = pd.PeriodIndex(s.index, freq="M")
        return s
    req = urllib.request.Request(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}",
        headers={"User-Agent": "trading-analysis research (romarinhsieh@gmail.com)"})
    d = pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=60).read().decode()))
    d.columns = ["date", "v"]
    d["v"] = pd.to_numeric(d["v"], errors="coerce")
    s = d.dropna().set_index(pd.to_datetime(d.dropna()["date"]))["v"]
    s = s.groupby(s.index.to_period("M")).last().rename("v")
    pd.DataFrame({"v": s.to_numpy()}, index=s.index.astype(str)).to_parquet(p)
    return s


def e1_bootstrap(r: pd.DataFrame, w: np.ndarray, rng: np.random.Generator):
    """DCA block-bootstrap: returns (real multiples of contributions, path MDDs)."""
    R = r.to_numpy()
    T = len(R)
    p_geo = 1.0 / BLOCK_MEAN
    idx = np.zeros((N_PATHS, MONTHS), dtype=int)
    pos = rng.integers(0, T, size=N_PATHS)
    for t in range(MONTHS):
        idx[:, t] = pos
        new = rng.random(N_PATHS) < p_geo
        pos = np.where(new, rng.integers(0, T, size=N_PATHS), (pos + 1) % T)
    Rp = R[idx]                                     # paths x months x assets
    r_port = Rp @ w
    grow = (1 + Rp) * w                             # asset values after month
    tot = 1 + r_port
    with np.errstate(invalid="ignore", divide="ignore"):
        drift = np.abs(grow / tot[..., None] - w).sum(axis=2) / 2
    r_net = r_port - drift * COST_RT
    infl_m = (1 + INFL) ** (1 / 12) - 1
    r_real = (1 + r_net) / (1 + infl_m) - 1
    wealth = np.zeros(N_PATHS)
    for t in range(MONTHS):
        wealth = (wealth + 1.0) * (1 + r_real[:, t])
    mult = wealth / MONTHS
    nav = np.cumprod(1 + r_real, axis=1)
    runmax = np.maximum.accumulate(nav, axis=1)
    mdd = (nav / runmax - 1).min(axis=1)
    return mult, mdd


def e2_analogs() -> pd.DataFrame:
    """US 50y analog monthly REAL returns: market, daily-reset 2x, 10y bond, gold."""
    from trading_analysis.factors.attribution import load_ff_factors
    from tr35_mechanism_replay import bond_tr_from_yields, load_gold_monthly, load_gs10_monthly

    ffd = load_ff_factors(start="1972-01-01", momentum=False)
    mkt_d = ffd["Mkt-RF"] + ffd["RF"]
    rf_d = ffd["RF"]
    lev_d = 2 * mkt_d - rf_d - FIN_SPREAD / 252
    mkt_m = (1 + mkt_d).groupby(mkt_d.index.to_period("M")).prod() - 1
    lev_m = (1 + lev_d).groupby(lev_d.index.to_period("M")).prod() - 1
    bond_m = bond_tr_from_yields(load_gs10_monthly())
    gold_m = load_gold_monthly().pct_change()
    cpi = fred_series("CPIAUCSL", "data/cpi_us.parquet")
    infl_m = cpi.pct_change()
    out = pd.concat([mkt_m.rename("mkt"), lev_m.rename("lev2"), bond_m.rename("bond"),
                     gold_m.rename("gold"), infl_m.rename("cpi")], axis=1).dropna()
    out = out.loc["1975-01":]
    for c in ("mkt", "lev2", "bond", "gold"):
        out[c] = (1 + out[c]) / (1 + out["cpi"]) - 1
    return out.drop(columns="cpi")


def e2_replay(a: pd.DataFrame, w: np.ndarray) -> dict:
    r = a.to_numpy() @ w
    r = pd.Series(r, index=a.index)
    nav = (1 + r).cumprod()

    def mdd(x):
        return float((x / x.cummax() - 1).min())

    yrs = len(r) / 12
    return {
        "real_cagr": float(nav.iloc[-1] ** (1 / yrs) - 1),
        "real_mdd": mdd(nav),
        "stagflation_75_81_mdd": mdd(nav.loc["1975-01":"1981-12"]),
        "y2022_mdd": mdd(nav.loc["2022-01":"2022-12"]),
    }


def main():
    rng = np.random.default_rng(SEED)
    r_tw = tw_monthly()
    print("=" * 110)
    print(f"ALLOCATION LAB -- E1: TW real data {r_tw.index[0]:%Y-%m}..{r_tw.index[-1]:%Y-%m} "
          f"({len(r_tw)}m joint, block bootstrap {N_PATHS} paths x {MONTHS}m DCA) | "
          f"E2: US analogs 1975-2026 real replay")
    print("=" * 110)
    analogs = e2_analogs()
    rows = []
    for name, a, b, c, d in PRESETS:
        w = np.array([a, b, c, d])
        mult, mdd1 = e1_bootstrap(r_tw, w, rng)
        e2 = e2_replay(analogs, w)
        rows.append({
            "name": name, "w": [a, b, c, d],
            "P10": float(np.percentile(mult, 10)),
            "P50": float(np.percentile(mult, 50)),
            "P90": float(np.percentile(mult, 90)),
            "mdd_P50": float(np.percentile(mdd1, 50)),
            "mdd_P10": float(np.percentile(mdd1, 10)),
            **e2,
        })
        print(f"{name:22s} | 實質倍數 P10 {rows[-1]['P10']:5.2f}x P50 {rows[-1]['P50']:5.2f}x "
              f"P90 {rows[-1]['P90']:6.2f}x | 路徑MDD P50 {rows[-1]['mdd_P50']:+.0%} "
              f"P10 {rows[-1]['mdd_P10']:+.0%} | 50y實質CAGR {e2['real_cagr']:+.1%} "
              f"MDD {e2['real_mdd']:+.0%} | 停滯通膨MDD {e2['stagflation_75_81_mdd']:+.0%} "
              f"2022 {e2['y2022_mdd']:+.0%}")

    out = {
        "meta": {
            "source": "trading-analysis allocation lab",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "engines": {
                "E1": f"TW real ETF NAVs (0050/00631L/00679B/00635U) {r_tw.index[0]}..{r_tw.index[-1]}, "
                      f"stationary block bootstrap (mean {BLOCK_MEAN}m), {N_PATHS} paths x {MONTHS}m DCA, "
                      f"10bps RT rebalance cost, 2%/yr real terms",
                "E2": "US analogs 1975-2026 (FF market, DAILY-RESET 2x minus financing, 10y CMT TR, "
                      "gold), REAL terms via actual CPI -- regime badges per allocation",
            },
            "honesty": [
                "E1 ABSOLUTE multiples inherit the 2017-26 golden arc (0050 adj CAGR ~15%/yr in-window): read RELATIVE gaps and drawdown shapes, never levels as forecasts; E2's 50y real CAGRs (5-9%) are the sober anchor",
                "E1 single-arc caveat: bootstrap cannot invent unseen regimes -> read E2 badges",
                "dividend-adjusted (total-return) prices mandatory: run 1 used raw closes and the stripped ~2.5%/yr 0050 distributions rigged every comparison toward the accumulating 2x ETF",
                "real 00631L NAV carries true daily-reset drag/fees (no mu-sigma^2/2 approximation)",
                "menu not optimizer: rankings between adjacent allocations sit inside assumption error (TR-37)",
                "no shorting/margin; long-only wealth floor is structural",
            ],
        },
        "allocations": rows,
    }
    Path("exports/dashboard").mkdir(parents=True, exist_ok=True)
    Path("exports/dashboard/allocation_lab.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[export] exports/dashboard/allocation_lab.json")

    # chart
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 9))
    names = [r["name"] for r in rows]
    x = np.arange(len(rows))
    ax = axes[0]
    ax.bar(x - 0.25, [r["P10"] for r in rows], 0.25, color="#c62828", alpha=0.9, label="P10 悲觀")
    ax.bar(x, [r["P50"] for r in rows], 0.25, color="#1565c0", alpha=0.9, label="P50 中位")
    ax.bar(x + 0.25, [r["P90"] for r in rows], 0.25, color="#2e7d32", alpha=0.9, label="P90 樂觀")
    ax.axhline(1.0, color="black", lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.set_ylabel("30 年 DCA 實質購買力(投入倍數,log)")
    ax.set_title("E1|台股真實資料區塊拔靴(厚尾;真實正2耗損)— 3,000 路徑", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=18, ha="right")
    ax.legend(fontsize=9)
    ax = axes[1]
    ax.bar(x - 0.2, [r["stagflation_75_81_mdd"] * 100 for r in rows], 0.4,
           color="#f9a825", alpha=0.9, label="1975-81 停滯性通膨實質MDD")
    ax.bar(x + 0.2, [r["y2022_mdd"] * 100 for r in rows], 0.4,
           color="#90a4ae", alpha=0.9, label="2022 實質MDD")
    ax.set_ylabel("實質回撤 (%)")
    ax.set_title("E2|50 年美國類比 regime 徽章(真實 CPI;拔靴造不出的 regime 在這裡)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=18, ha="right")
    ax.legend(fontsize=9)
    for a_ in axes:
        a_.grid(alpha=0.3, axis="y")
    fig.suptitle("配置實驗室(誠實版):選單不選格 — 區塊拔靴 × regime 回放", fontsize=13)
    fig.text(0.5, 0.005,
             "⚠ E1 絕對倍數繼承 2017–26 台股黃金弧(0050 還原 CAGR 該窗 ~15%/yr)——只讀「配置之間的相對差」與回撤形狀,勿當預測;"
             "E2 的 50 年實質 CAGR(5–9%)才是清醒的長期錨。本表是選單,不是最佳化器。",
             ha="center", fontsize=8.5, color="#c62828")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    outp = Path("docs/img/allocation_lab.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
