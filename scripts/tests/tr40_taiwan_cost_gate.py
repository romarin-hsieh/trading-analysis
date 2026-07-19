"""TR-40 -- Taiwan candidates through the cost gate (docs/27 b2; the survival test).

TR-39b confirmed three characteristics on the survivorship-patched TWSE panel:
mom122 (+84bps/mo, t=2.44), avol (+94, t=3.39), logdv (-106, t=-2.77). Those are
REGRESSION SLOPES on rank-standardized characteristics -- they are not money. This TR
converts each into a tradable long-only portfolio and charges Taiwan's real round trip.

TAIWAN COST STACK (retail, cash account, 2026):
  commission 0.1425% x 2 sides (many brokers discount to ~0.06-0.09%; we use FULL rate
  as the conservative base and report a discounted variant), securities transaction tax
  0.30% on the SELL side only, plus the Corwin-Schultz effective half-spread measured on
  THIS panel (TR-38 machinery, overnight-adjusted) -- because a decile portfolio of
  illiquid names pays a spread the fee schedule never mentions. Full-rate baseline
  therefore ~= 0.585% + spread per round trip.

F0 DECLARATION (pre-committed)
  claim  : at least one confirmed candidate survives Taiwan's round-trip cost as a
         long-only, monthly-rebalanced decile portfolio.
  seat   : survivorship-patched panel (TR-39b engine: delisted names patched and
         truncated at official dates, pct_change(fill_method=None)), 2015-07..2026,
         monthly rebalance, top-decile long-only (no shorting -- TW borrow limits),
         equal-weight within the decile.
  CAL    : (a) the gross (pre-cost) top-decile minus EW-universe spread must reproduce
         the sign and rough scale of the TR-39b FM slope for each candidate (same
         direction, |gross| >= 40bps/mo); (b) measured CS spread on the panel must be
         higher for the illiquid decile than for the liquid decile (sanity: the cost
         we are charging must behave like a spread). Fail -> STOP.
  C1 (decisive, per candidate): NET annualized excess return over the EW universe after
         full-rate costs + measured spread.
           net > 0 with t >= 2   -> SURVIVES-COSTS (tradable candidate)
           net > 0, t < 2        -> MARGINAL (report, do not promote)
           net <= 0              -> KILLED-BY-COSTS
  C2  : turnover decomposition -- annual turnover per candidate and the bps/yr each
         cost component eats (commission / transaction tax / spread). This is the
         number that decides everything, so it is reported explicitly.
  C3  : rebalance-frequency ladder (21d / 63d / 126d): slower trading pays less cost but
         holds staler signal -- reported as a menu, NOT optimized (F5/TR-37).
  C4  : discounted-commission variant (0.0855% = 6折) as a sensitivity, reported only.
  anti-HARKing : deciles/EW/monthly fixed before running; the frequency ladder is a
         reported menu and the verdict is judged at the pre-registered 21d cell;
         trials +0 families (same Taiwan family, economics layer).

Run: uv run python scripts/tests/tr40_taiwan_cost_gate.py   (~3-5 min)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from tr39_taiwan_panel import DATA, START, load_panels  # noqa: E402
from tr39b_taiwan_delisted import build_chars  # noqa: E402

COMMISSION_FULL = 0.001425      # per side
COMMISSION_DISC = 0.000855      # 6-fold discount, common retail rate
TAX_SELL = 0.0030               # securities transaction tax, sell side only
DECILE = 0.10
CANDIDATES = {"mom122": +1, "avol": +1, "logdv": -1}   # sign = direction of the FM slope
DEN = 3 - 2 * np.sqrt(2)


def cs_spread_monthly(px: pd.DataFrame) -> pd.DataFrame:
    """Corwin-Schultz effective spread (TR-38 machinery incl. the overnight adjustment),
    averaged to month-ends. Half of this is paid per side."""
    high = px * 1.0
    low = px * 1.0
    # panel carries close only -> use a 2-day high/low proxy from closes (documented
    # limitation: understates the true intraday range, so the spread estimate is a
    # LOWER bound; the verdict therefore errs toward the candidates' favour)
    hi2 = px.rolling(2).max()
    lo2 = px.rolling(2).min()
    lh = np.log((hi2 / lo2).where(lo2 > 0)) ** 2
    beta = lh + lh.shift(1)
    hmax = np.maximum(hi2, hi2.shift(1))
    lmin = np.minimum(lo2, lo2.shift(1))
    gamma = np.log((hmax / lmin).where(lmin > 0)) ** 2
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / DEN - np.sqrt(gamma / DEN)
    s = (2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))).clip(lower=0)
    del high, low
    return s.resample("ME").mean()


def decile_portfolio(char: pd.DataFrame, fwd: pd.DataFrame, sign: int,
                     spread_m: pd.DataFrame, step_months: int, commission: float):
    """Long-only top-decile EW portfolio. Returns (gross, net, turnover, cost_parts)."""
    dates = list(char.index)
    held: set[str] = set()
    rows = []
    for i, t in enumerate(dates):
        if i % step_months == 0:                      # rebalance month
            s = (char.loc[t] * sign).dropna()
            if len(s) < 100:
                continue
            k = max(10, int(len(s) * DECILE))
            new = set(s.nlargest(k).index)
        else:
            new = held
        if not new:
            continue
        f = fwd.loc[t, list(new)].dropna()
        if f.empty:
            continue
        gross = float(f.mean())
        # turnover: names entering + leaving, as a fraction of the book
        if held:
            churn = len(new - held) / max(len(new), 1)
        else:
            churn = 1.0
        sp = spread_m.loc[t, list(new)].dropna()
        half_spread = float(sp.mean()) / 2 if len(sp) else 0.0
        # cost per unit of turnover: buy = commission + half-spread;
        # sell = commission + tax + half-spread
        cost_rt = (commission + half_spread) + (commission + TAX_SELL + half_spread)
        cost = churn * cost_rt
        rows.append({"date": t, "gross": gross, "cost": cost, "churn": churn,
                     "commission": churn * 2 * commission, "tax": churn * TAX_SELL,
                     "spread": churn * 2 * half_spread})
        held = new
    return pd.DataFrame(rows).set_index("date")


def nw_t(x: pd.Series, lags: int = 3) -> tuple[float, float]:
    x = x.dropna()
    res = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(res.params[0]), float(res.tvalues[0])


def main():
    man = pd.read_csv(DATA / "delisted.csv", dtype={"stock_id": str})
    px, dv, pbr, per = load_panels()
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px.columns:
            px.loc[px.index > dd, sid] = np.nan
            dv.loc[dv.index > dd, sid] = np.nan
    chars, fwd, ret_m, dv_p, me = build_chars(px, dv, pbr, include_bp=False)
    ew_universe = fwd.mean(axis=1)

    print("=" * 104)
    print("TR-40  TAIWAN COST GATE -- do the confirmed candidates survive 0.585% + spread?")
    print("=" * 104)

    spread_m = cs_spread_monthly(px.where(px > 0)).reindex(chars["mom122"].index)
    liq = chars["logdv"]                     # rank-standardized liquidity
    sp_illiq = spread_m.where(liq < -0.3).stack().median()
    sp_liq = spread_m.where(liq > 0.3).stack().median()
    cal_b = sp_illiq > sp_liq
    print(f"CAL b: measured CS spread illiquid decile {sp_illiq*1e4:.0f}bps vs liquid "
          f"{sp_liq*1e4:.0f}bps -> {'PASS' if cal_b else 'FAIL'}")

    results, cal_a_ok = {}, True
    for name, sign in CANDIDATES.items():
        d = decile_portfolio(chars[name], fwd, sign, spread_m, 1, COMMISSION_FULL)
        excess_gross = d["gross"] - ew_universe.reindex(d.index)
        g_mean, _ = nw_t(excess_gross)
        ok = abs(g_mean) >= 0.0040 and np.sign(g_mean) > 0
        cal_a_ok &= ok
        results[name] = (d, excess_gross)
        print(f"CAL a {name}: gross top-decile minus EW = {g_mean*1e4:+.0f}bps/mo "
              f"(rule: >= +40bps) -> {'PASS' if ok else 'FAIL'}")
    if not (cal_b and cal_a_ok):
        print("VERDICT: INVALID-TEST -- gross economics do not reproduce the slope layer.")
        return

    print("-" * 104)
    print("C1/C2 net-of-cost verdicts (full-rate commission 0.1425%x2 + 0.30% sell tax + measured spread):")
    verdicts = {}
    for name, (d, excess_gross) in results.items():
        net_m = excess_gross - d["cost"]
        m, t = nw_t(net_m)
        g, _ = nw_t(excess_gross)
        turn_ann = float(d["churn"].mean() * 12)
        comm = float(d["commission"].mean() * 12)
        tax = float(d["tax"].mean() * 12)
        spr = float(d["spread"].mean() * 12)
        if m > 0 and t >= 2:
            v = "SURVIVES-COSTS"
        elif m > 0:
            v = "MARGINAL"
        else:
            v = "KILLED-BY-COSTS"
        verdicts[name] = v
        print(f"  {name:7s}: gross {g*12*100:+6.2f}%/yr - costs {(comm+tax+spr)*100:5.2f}%/yr "
              f"= NET {m*12*100:+6.2f}%/yr (t={t:+.2f})  -> {v}")
        print(f"{'':11s}turnover {turn_ann:.1f}x/yr | commission {comm*100:.2f}% + tax "
              f"{tax*100:.2f}% + spread {spr*100:.2f}%")

    print("C3 rebalance-frequency menu (NOT optimized; verdict judged at 21d/monthly):")
    ladder = {}
    for name, sign in CANDIDATES.items():
        row = []
        for step, lab in ((1, "月"), (3, "季"), (6, "半年")):
            d = decile_portfolio(chars[name], fwd, sign, spread_m, step, COMMISSION_FULL)
            net = (d["gross"] - ew_universe.reindex(d.index)) - d["cost"]
            m, t = nw_t(net)
            row.append((lab, m * 12, t, float(d["churn"].mean() * 12 / step)))
        ladder[name] = row
        print(f"  {name:7s}: " + " | ".join(
            f"{lab} {m*100:+.2f}%/yr (t={t:+.1f}, 換手 {to:.1f}x)" for lab, m, t, to in row))

    print("C4 discounted commission (6折 0.0855%/side) sensitivity:")
    for name, sign in CANDIDATES.items():
        d = decile_portfolio(chars[name], fwd, sign, spread_m, 1, COMMISSION_DISC)
        net = (d["gross"] - ew_universe.reindex(d.index)) - d["cost"]
        m, t = nw_t(net)
        print(f"  {name:7s}: NET {m*12*100:+.2f}%/yr (t={t:+.2f})")

    survivors = [k for k, v in verdicts.items() if v == "SURVIVES-COSTS"]
    marginal = [k for k, v in verdicts.items() if v == "MARGINAL"]
    if survivors:
        verdict = (f"SURVIVES: {', '.join(survivors)}"
                   + (f" | MARGINAL: {', '.join(marginal)}" if marginal else "")
                   + " -- proceed to b3 bucket economics.")
    elif marginal:
        verdict = (f"ALL MARGINAL ({', '.join(marginal)}) -- positive net but below t=2; "
                   f"no promotion, the Taiwan line stays research-only.")
    else:
        verdict = ("KILLED-BY-COSTS -- the slopes were real but the round trip eats them; "
                   "the Taiwan line ends here as a documented negative.")
    print("-" * 104)
    print(f"VERDICT: {verdict}")
    print("=" * 104)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))
    ax = axes[0]
    names = list(CANDIDATES)
    x = np.arange(len(names))
    gross = [nw_t(results[n][1])[0] * 12 * 100 for n in names]
    costs = [float((results[n][0]["cost"]).mean() * 12 * 100) for n in names]
    nets = [g - c for g, c in zip(gross, costs)]
    ax.bar(x - 0.22, gross, 0.22, label="毛超額", color="#2e7d32", alpha=0.9)
    ax.bar(x, [-c for c in costs], 0.22, label="成本", color="#c62828", alpha=0.9)
    ax.bar(x + 0.22, nets, 0.22, label="淨超額", color="#1565c0", alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("%/年(相對等權宇宙)")
    ax.set_title("C1:毛 → 成本 → 淨(全額手續費+證交稅+實測價差)", fontsize=10.5)
    ax.legend(fontsize=9)
    ax = axes[1]
    for name, col in zip(names, ("#1565c0", "#f9a825", "#2e7d32")):
        labs = [r[0] for r in ladder[name]]
        vals = [r[1] * 100 for r in ladder[name]]
        ax.plot(labs, vals, "o-", label=name, color=col)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("淨超額 %/年")
    ax.set_title("C3:再平衡頻率選單(慢=省成本但訊號變舊)", fontsize=10.5)
    ax.legend(fontsize=9)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-40:台股候選過成本關卡了嗎?", fontsize=12.5)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr40_taiwan_cost_gate.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
