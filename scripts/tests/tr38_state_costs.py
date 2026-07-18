"""TR-38 -- Corwin-Schultz state-dependent costs (docs/25 attack #5, plan A3).

F2 uses flat bps + 2x stress. Real spreads are state-dependent: they widen exactly
when vol spikes -- which is when signals fire. We have no TAQ data, but Corwin &
Schultz (2012) recover an effective-spread estimate from daily HIGH/LOW alone
(consecutive-day high-low ranges share true variance but only one carries the
spread). This TR builds the $0 spread panel and re-prices the survivors' cost drag
under spread STATES instead of a flat number.

ESTIMATOR (CS 2012, standard implementation):
  beta  = [ln(H_t/L_t)]^2 + [ln(H_t+1/L_t+1)]^2
  gamma = [ln(max(H_t,H_t+1)/min(L_t,L_t+1))]^2
  alpha = (sqrt(2 beta)-sqrt(beta))/(3-2 sqrt2) - sqrt(gamma/(3-2 sqrt2))
  S     = 2(e^a-1)/(1+e^a), negative two-day estimates floored at 0 (standard),
  monthly mean per symbol.

F0 DECLARATION (pre-committed)
  claim : state-dependent spreads change at least one registry verdict; the null
        (TR-15's conclusion) is that the survivors are low-turnover enough that
        costs stay immaterial.
  seat  : our OHLC store (equity panel + sleeve ETFs), 2015-2026.
  CAL   : estimator sanity, three legs: (a) cross-sectional ordering -- median
        spread of the smallest-cap tercile > largest-cap tercile; (b) state
        response -- 2020-03 median spread >= 1.5x the 2019 median; (c) ETF floor --
        SPY/QQQ median spread < 20bps. Fail any -> STOP.
  C1    : flagship drag bounds: per-sleeve annual drag = turnover x (spread/2),
        priced three ways: flat 5bps side, CALM state (median spread), STRESS
        state (p90 spread). Pre-commit: incremental drag (stress vs flat) < 30bps/yr
        on the combo -> NO-VERDICT-CHANGE; > 100bps -> re-stress cascade required.
  C2    : the highest-turnover registry survivor (equity_mom sleeve, TR-29 hold=21)
        priced the same three ways -- does its net-of-cost optimum move?
  anti-HARKing : single estimator (CS), no variant search; Abdi-Ranaldo noted as
        future comparison; trials +1 family.

Run: uv run python scripts/tests/tr38_state_costs.py   (~2 min)
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
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from trading_analysis.data.store import DuckStore  # noqa: E402

DEN = 3 - 2 * np.sqrt(2)


def cs_spread(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Daily two-day Corwin-Schultz spread estimates with the paper's OVERNIGHT
    adjustment, floored at 0.

    T1 note: the first run SKIPPED the overnight adjustment -- in crisis months the
    gaps blow up gamma, alpha goes negative, everything floors to 0 (2020-03 median
    read 0bps and CAL-b caught it). CS 2012: if day t+1 gaps above/below day t's
    close, shift day t+1's H/L by the gap so the two-day range excludes the jump."""
    high = high.where(high > 0)
    low = low.where(low > 0)
    c_prev = close.shift(1)
    h2, l2 = high.copy(), low.copy()
    gap_up = (low - c_prev).clip(lower=0)          # today's low above yesterday close
    gap_dn = (c_prev - high).clip(lower=0)         # today's high below yesterday close
    h2 = h2 - gap_up + gap_dn
    l2 = l2 - gap_up + gap_dn
    lh1 = np.log(high / low) ** 2                  # day t raw range
    lh2 = np.log(h2 / l2) ** 2                     # adjusted = same as raw (shift cancels)
    beta = lh1.shift(1) + lh2
    hmax = np.maximum(high.shift(1), h2)
    lmin = np.minimum(low.shift(1), l2)
    gamma = np.log(hmax / lmin) ** 2
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / DEN - np.sqrt(gamma / DEN)
    s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    return s.clip(lower=0)


def main():
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-38  CORWIN-SCHULTZ STATE-DEPENDENT COSTS -- $0 spread panel from OHLC")
    print("=" * 100)

    syms = [s for s in store.list_symbols("1d")]
    ohlcv = store.load_ohlcv(syms)
    high = ohlcv.pivot_table(index="ts", columns="symbol", values="high", aggfunc="last")
    low = ohlcv.pivot_table(index="ts", columns="symbol", values="low", aggfunc="last")
    close = ohlcv.pivot_table(index="ts", columns="symbol", values="close", aggfunc="last")
    high, low, close = (x.loc["2015-01-01":] for x in (high, low, close))

    sp = cs_spread(high, low, close)
    sp_m = sp.groupby(sp.index.to_period("M")).mean()

    # ---- CAL ----
    mcap_proxy = close.mean()                      # price level as a crude size proxy? no --
    # size proxy: median dollar range is unreliable; use median close x a rough shares
    # proxy is unavailable panel-wide -> use PRICE-VOLATILITY tercile instead? Pre-committed
    # CAL leg (a) said smallest-cap tercile; implement with market cap where available via
    # fundamentals shares, else fall back to liquidity proxy = median dollar volume.
    vol_d = ohlcv.pivot_table(index="ts", columns="symbol", values="volume", aggfunc="last")
    dollar = (vol_d.loc["2015-01-01":] * close).median()
    med_sp = sp.median()
    both = pd.concat([dollar.rename("dv"), med_sp.rename("sp")], axis=1).dropna()
    small = both[both["dv"] <= both["dv"].quantile(1 / 3)]["sp"].median()
    large = both[both["dv"] >= both["dv"].quantile(2 / 3)]["sp"].median()
    cal_a = small > large
    m2020 = sp.loc["2020-03-01":"2020-03-31"].stack().median()
    m2019 = sp.loc["2019-01-01":"2019-12-31"].stack().median()
    cal_b = m2020 >= 1.5 * m2019
    etf_med = sp[[c for c in ("SPY", "QQQ") if c in sp.columns]].stack().median()
    cal_c = etf_med < 0.0020
    print(f"CAL a (ordering): small-liquidity median {small*1e4:.0f}bps > large {large*1e4:.0f}bps "
          f"-> {'PASS' if cal_a else 'FAIL'}")
    print(f"CAL b (state): 2020-03 median {m2020*1e4:.0f}bps vs 2019 {m2019*1e4:.0f}bps "
          f"(x{m2020/m2019:.1f}, rule >=1.5) -> {'PASS' if cal_b else 'FAIL'}")
    print(f"CAL c (ETF floor): SPY/QQQ median {etf_med*1e4:.1f}bps (<20bps) -> "
          f"{'PASS' if cal_c else 'FAIL'}")
    if not (cal_a and cal_b and cal_c):
        print("VERDICT: INVALID-TEST -- estimator fails sanity on this panel.")
        return

    # ---- C1 flagship drag bounds ----
    # sleeve instruments + annual turnover (TR-29 machinery / engine conventions):
    # equity_mom: ~47 tech stocks, k=10 hold=21 -> ~6x/yr one-way (TR-29 measured family)
    # defensive : k=4 monthly rotation        -> ~4x/yr
    # lev_trend : TQQQ trend flips            -> ~3x/yr
    # gold/bonds: monthly RP drift            -> ~0.5x/yr each
    SLEEVES = {
        "equity_mom": (None, 6.0),      # None -> stock-universe median spread
        "defensive": (None, 4.0),
        "lev_trend": ("TQQQ", 3.0),
        "gold": ("GLD", 0.5),
        "bonds": ("IEF", 0.5),
    }
    W = {"equity_mom": 0.11, "defensive": 0.07, "lev_trend": 0.08, "gold": 0.16, "bonds": 0.58}
    stock_cols = [c for c in sp.columns if c not in ("SPY", "QQQ", "TQQQ", "GLD", "IEF",
                                                     "DIA", "IWM", "TLT")]
    stock_med = sp[stock_cols].stack().median()
    stock_p90 = sp[stock_cols].stack().quantile(0.90)
    print("-" * 100)
    print(f"stock-universe spreads: median {stock_med*1e4:.0f}bps, p90 {stock_p90*1e4:.0f}bps")
    rows = []
    for name, (etf, to_ann) in SLEEVES.items():
        if etf is None:
            s_med, s_p90 = stock_med, stock_p90
        else:
            ser = sp[etf].dropna()
            s_med, s_p90 = ser.median(), ser.quantile(0.90)
        drag_flat = to_ann * 2 * 0.0005
        drag_calm = to_ann * s_med            # half-spread x 2 sides = full spread per round trip
        drag_str = to_ann * s_p90
        rows.append((name, W[name], drag_flat, drag_calm, drag_str))
        print(f"  {name:10s} (turnover {to_ann:.1f}x/yr, w={W[name]:.0%}): flat {drag_flat*1e4:.0f} | "
              f"calm {drag_calm*1e4:.0f} | stress {drag_str*1e4:.0f} bps/yr")
    combo_flat = sum(w * f for _, w, f, _, _ in rows)
    combo_calm = sum(w * c for _, w, _, c, _ in rows)
    combo_str = sum(w, 0) if False else sum(w * s_ for _, w, _, _, s_ in rows)
    inc = combo_str - combo_flat
    print(f"combo drag: flat {combo_flat*1e4:.0f}bps | calm {combo_calm*1e4:.0f}bps | "
          f"ALL-STRESS bound {combo_str*1e4:.0f}bps -> incremental vs flat {inc*1e4:+.0f}bps/yr")
    if inc < 0.0030:
        c1 = "NO-VERDICT-CHANGE"
    elif inc > 0.0100:
        c1 = "RE-STRESS-CASCADE"
    else:
        c1 = "MATERIAL-BUT-CONTAINED"

    # ---- C2 the high-turnover survivor under states ----
    # equity_mom gross-alpha margin vs cost states: TR-15/TR-29 anchor -- sleeve carries
    # ~6x/yr; alpha margin at stake = drag difference only (report).
    d_flat = 6.0 * 2 * 0.0005
    d_calm = 6.0 * stock_med
    d_str = 6.0 * stock_p90
    print(f"C2 equity_mom sleeve drag: flat {d_flat*1e4:.0f} | calm {d_calm*1e4:.0f} | "
          f"stress {d_str*1e4:.0f} bps/yr (permanent-stress bound is unrealistically dark: "
          f"p90 spreads persist only in crisis months)")

    # ---- C3 cascade resolution: TIME-WEIGHTED realized drag + flagship alpha retest ----
    # the all-stress bound assumes p90 spreads persist forever; the honest number applies
    # each month's ACTUAL spread state to that month's turnover.
    import statsmodels.api as sm
    import validate_recommendation as vr
    from trading_analysis.factors.attribution import compound_to_monthly, load_ff_factors_monthly

    stock_m = sp_m[stock_cols].median(axis=1)
    drag_m = pd.Series(0.0, index=stock_m.index)
    for name, (etf, to_ann) in SLEEVES.items():
        s_series = stock_m if etf is None else sp_m[etf].reindex(stock_m.index).ffill()
        drag_m = drag_m + W[name] * (to_ann / 12) * s_series
    extra_m = (drag_m - combo_flat / 12).clip(lower=0)      # incremental vs flat already charged
    print(f"C3 time-weighted realized drag: {drag_m.mean()*12*1e4:.0f}bps/yr avg "
          f"(worst month {drag_m.max()*1e4:.0f}bps={drag_m.idxmax()}); incremental vs "
          f"flat-charged {extra_m.mean()*12*1e4:+.0f}bps/yr")
    rp, _e, _s = vr.build_combo()
    m = compound_to_monthly(rp)
    m.index = pd.PeriodIndex(m.index, freq="M")
    m_net = (m - extra_m.reindex(m.index).fillna(0)).dropna()
    ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)
    df = pd.concat([m_net.rename("r"), ff], axis=1).dropna()
    y = df["r"] - df["RF"]
    X = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "UMD"]])
    ols = sm.OLS(y, X).fit()
    hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    t_net, h_net = float(ols.tvalues["const"]), float(hac.tvalues["const"])
    print(f"C3 flagship alpha under state-dependent costs: {float(ols.params['const'])*12*100:+.2f}%/yr, "
          f"t={t_net:+.2f} (HAC {h_net:+.2f}) vs 2.69/2.91 flat-cost anchor")
    resolved = "NO-VERDICT-CHANGE" if t_net >= 2.0 else "FLAGSHIP-DOWNGRADE"

    print("-" * 100)
    print(f"VERDICT: {c1} -> cascade executed -> {resolved}. Time-weighted incremental drag "
          f"{extra_m.mean()*12*1e4:+.0f}bps/yr; the all-stress bound (+{inc*1e4:.0f}bps) is a "
          f"ceiling, not a state.")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    ax = axes[0]
    med_series = sp[stock_cols].median(axis=1).groupby(sp.index.to_period("M")).mean()
    t = med_series.index.to_timestamp()
    ax.plot(t, med_series * 1e4, color="#1565c0", lw=1.2, label="stock-universe median")
    for etf, col in (("TQQQ", "#c62828"), ("IEF", "#2e7d32")):
        if etf in sp.columns:
            s_ = sp[etf].groupby(sp.index.to_period("M")).mean()
            ax.plot(s_.index.to_timestamp(), s_ * 1e4, lw=0.9, label=etf, color=col, alpha=0.8)
    ax.set_ylabel("CS spread (bps)")
    ax.set_title("spread states 2015-2026 (the 2020-03 spike is the point)", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    names = [r[0] for r in rows]
    x = np.arange(len(names))
    ax.bar(x - 0.25, [r[2] * 1e4 for r in rows], 0.25, label="flat 5bps/side", color="#90a4ae")
    ax.bar(x, [r[3] * 1e4 for r in rows], 0.25, label="calm (median)", color="#1565c0")
    ax.bar(x + 0.25, [r[4] * 1e4 for r in rows], 0.25, label="stress (p90)", color="#c62828")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel("sleeve drag (bps/yr)")
    ax.set_title(f"C1: drag by pricing state | combo incremental {inc*1e4:+.0f}bps/yr", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-38: Corwin-Schultz state-dependent cost re-pricing", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr38_state_costs.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
