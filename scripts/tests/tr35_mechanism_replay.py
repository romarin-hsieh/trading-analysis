"""TR-35 -- flagship MECHANISM 50-year replay (docs/25 attack #2, plan item A1).

The flagship's drawdown deliverable has only ever lived inside one macro arc
(2015-2026: ZIRP -> hikes -> AI bull). Its 58% bond weight + tech beta is a
correlated death in a 1970s-style inflation regime, and 2022 already previewed the
failure mode. TR-25's bootstrap resamples the SAME window -- it cannot manufacture
unseen regimes. This TR replays the MECHANISM (risk-parity across trend-gated
equity momentum / dual-momentum defensive / levered trend / gold / bonds) through
1975-2026 with free long-history sleeve ANALOGS.

SLEEVE ANALOGS (monthly clock; mechanism proxies, not the actual book):
  eq_mom    top-7 of KF49 industries by 12-1 momentum, EW, gated by market>10m SMA
            (else T-bill)                     ~ momentum_trend_direction k=10 regime=True
  defensive GEM dual momentum: market if 12m excess>0 else 10y bond
                                              ~ strat_dual_momentum("def")
  lev_trend 2x market minus financing (RF+60bps) when market>10m SMA else T-bill
                                              ~ TQQQ-on-QQQ-trend (2x conservative proxy)
  gold      London fix monthly (datahub/Bundesbank 1833-2026)          ~ GLD
  bonds     10y constant-maturity total return from GS10 yields (par-bond repricing)
                                              ~ IEF
  allocator inverse-vol on trailing 12m vol, monthly rebalance, decisions shift(1)
            (TR-22 DGU: RP/IV/EW near-interchangeable -> IV is a faithful family rep)
  window    PRIMARY 1975-01..2026 (US gold ownership legal 1975; float era);
            1970-1974 reported 4-sleeve descriptive (gold sleeve is fictional pre-1975).

F0 DECLARATION (pre-committed)
  claim      : the mechanism's risk-shaping (combo MDD substantially below market MDD)
             survives regimes it has never seen -- ESPECIALLY bond-equity
             positive-correlation eras -- or it is a child of the 2015-2026 regime.
  CAL (all must pass, else STOP):
    CAL-1 bond proxy vs IEF monthly (2003+): corr >= 0.85
    CAL-2 datahub gold vs GLD monthly (2005+): corr >= 0.85
    CAL-3 analog combo vs REAL flagship monthly (2015-08+): corr >= 0.60 AND the
          analog's MDD-ratio-vs-market within [0.37, 0.77] (real flagship: 0.57)
  C1  per-decade delivery: MDD_combo/MDD_mkt per decade; count decades <= 0.8.
  C2  (decisive) named bond-equity positive-correlation windows:
        W1 1976-01..1981-12 (rate-spiral stagflation)
        W2 1994-01..1994-12 (bond massacre)
        W3 2022-01..2022-12
      plus pooled endogenous regime: months with rolling-36m stock-bond corr > 0.
      VERDICT RULE: MECHANISM-ROBUST iff MDD ratio <= 0.8 in >=2 of 3 named windows
      AND pooled positive-corr MDD ratio <= 0.9; REGIME-CHILD iff ratio >= 1.0 in
      >=2 named windows; else MIXED (named-window table = verdict of record).
  C3  1975-1981 sleeve contribution decomposition (which leg carries stagflation --
      prediction pre-stated: gold, not bonds).
  C4  1970-1974 four-sleeve descriptive.
  anti-HARKing: single pre-registered analog set; no analog search; trials +1 family.
  honest scope: monthly clock understates daily MDD (CAL-3 quantifies); 2x proxy for
  3x TQQQ; KF49 industries proxy a 47-tech-stock sleeve; nominal returns.

Run: uv run python scripts/tests/tr35_mechanism_replay.py   (~1 min)
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

from tr20_ff5_attribution import load_ff5_umd_monthly  # noqa: E402
from tr32_industry_momentum import load_kf49_monthly  # noqa: E402

UA = {"User-Agent": "trading-analysis research (romarinhsieh@gmail.com)"}
START, END = "1975-01", "2026-05"
FIN_SPREAD = 0.006          # levered sleeve financing spread over RF (annual)
IV_LOOKBACK = 12


def fetch_csv(url: str) -> pd.DataFrame:
    req = urllib.request.Request(url, headers=UA)
    return pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=60).read().decode()))


def load_gold_monthly() -> pd.Series:
    cache = Path("data/gold_monthly.parquet")
    if cache.exists():
        s = pd.read_parquet(cache)["price"]
        s.index = pd.PeriodIndex(s.index, freq="M")
        return s
    d = fetch_csv("https://datahub.io/core/gold-prices/r/monthly.csv")
    s = pd.Series(d["Price"].to_numpy(), index=pd.PeriodIndex(d["Date"], freq="M"), name="price")
    s.to_frame().assign(price=s.to_numpy()).set_index(s.index.astype(str))  # noqa: expression for clarity
    pd.DataFrame({"price": s.to_numpy()}, index=s.index.astype(str)).to_parquet(cache)
    return s


def load_gs10_monthly() -> pd.Series:
    """END-of-month 10y CMT yield from DAILY DGS10 (not the GS10 monthly AVERAGE --
    averaged series vs EOM instruments is a Working-1960 alignment error; the first
    run's CAL-1 corr 0.74 was exactly that artifact)."""
    cache = Path("data/dgs10_eom.parquet")
    if cache.exists():
        s = pd.read_parquet(cache)["y"]
        s.index = pd.PeriodIndex(s.index, freq="M")
        return s
    d = fetch_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10")
    d.columns = ["date", "y"]
    d["y"] = pd.to_numeric(d["y"], errors="coerce")
    d["date"] = pd.to_datetime(d["date"])
    s = d.dropna().set_index("date")["y"].div(100.0)
    s = s.groupby(s.index.to_period("M")).last().rename("y")
    pd.DataFrame({"y": s.to_numpy()}, index=s.index.astype(str)).to_parquet(cache)
    return s


def bond_tr_from_yields(y: pd.Series) -> pd.Series:
    """Monthly total return of a 10y constant-maturity par bond (semiannual coupons):
    hold last month's par bond one month, reprice at the new yield, add accrual."""
    y0, y1 = y.shift(1), y
    n = 20                                   # semiannual periods
    a = (1 - (1 + y1 / 2) ** (-n)) / (y1 / 2)
    price_new = (y0 / 2) * a + (1 + y1 / 2) ** (-n)
    return (price_new - 1 + y0 / 12).dropna()


def mdd(nav: pd.Series) -> float:
    return float((nav / nav.cummax() - 1).min())


def window_ratio(combo_r: pd.Series, mkt_r: pd.Series, a: str, b: str) -> tuple[float, float, float]:
    c = combo_r.loc[a:b]
    m = mkt_r.loc[a:b]
    dc, dm = mdd((1 + c).cumprod()), mdd((1 + m).cumprod())
    return dc, dm, (dc / dm if dm < 0 else np.nan)


def main():
    # ---- data legs ----
    ff = load_ff5_umd_monthly(start="1965-01-01")
    mkt = (ff["Mkt-RF"] + ff["RF"]).rename("mkt")
    rf = ff["RF"]
    kf = load_kf49_monthly()
    kf.index = kf.index.to_period("M")
    gold_px = load_gold_monthly()
    gold = gold_px.pct_change().rename("gold")
    y10 = load_gs10_monthly()
    bond = bond_tr_from_yields(y10).rename("bonds")

    print("=" * 100)
    print("TR-35  FLAGSHIP MECHANISM 50-YEAR REPLAY -- monthly analogs, 1975-2026")
    print("=" * 100)

    # ---- CAL-1/2: proxy fidelity vs the real instruments in our store ----
    sys.path.insert(0, "src")
    from trading_analysis.data.store import DuckStore
    from trading_analysis.factors.attribution import compound_to_monthly
    store = DuckStore("./data")

    def store_monthly(sym, how="eom"):
        px = store.load_close_pivot([sym], column="adj_close").iloc[:, 0].dropna()
        if how == "avg":                     # like-for-like vs month-AVERAGE series
            m = px.groupby(px.index.to_period("M")).mean().pct_change().dropna()
            return m
        r = px.pct_change().dropna()
        m = compound_to_monthly(r)
        m.index = pd.PeriodIndex(m.index, freq="M")
        return m

    ief = store_monthly("IEF")                       # EOM vs our EOM bond proxy
    gld_avg = store_monthly("GLD", how="avg")        # month-avg vs datahub month-avg gold
    c1 = pd.concat([bond, ief.rename("ief")], axis=1).dropna().loc["2003-01":]
    corr1 = float(c1.corr().iloc[0, 1])
    c2 = pd.concat([gold, gld_avg.rename("gld")], axis=1).dropna().loc["2005-01":]
    corr2 = float(c2.corr().iloc[0, 1])
    cal1, cal2 = corr1 >= 0.85, corr2 >= 0.85
    print(f"CAL-1 bond proxy (EOM DGS10) vs IEF EOM (2003+): corr {corr1:+.3f} (>=0.85) -> "
          f"{'PASS' if cal1 else 'FAIL'}")
    print(f"CAL-2 gold (month-avg) vs GLD month-avg (2005+): corr {corr2:+.3f} (>=0.85) -> "
          f"{'PASS' if cal2 else 'FAIL'}  [gold leg stays month-averaged; Working smoothing "
          f"understates its vol -- honesty note]")
    if not (cal1 and cal2):
        print("VERDICT: INVALID-TEST -- proxy legs unfaithful; stop.")
        return

    # ---- build sleeves (decisions from t-1 data, applied in month t) ----
    idx = mkt.index.intersection(kf.index).intersection(gold.index).intersection(bond.index)
    mkt_, rf_, kf_, gold_, bond_ = (x.reindex(idx) for x in (mkt, rf, kf, gold, bond))
    level = (1 + mkt_).cumprod()
    trend_on = (level > level.rolling(10).mean()).shift(1).fillna(False)

    mom = (kf_.shift(2) / kf_.shift(12) - 1)
    eq_rows = {}
    for t in idx:
        s = mom.loc[t].dropna()
        if len(s) < 30 or not trend_on.loc[t]:
            eq_rows[t] = rf_.loc[t]
            continue
        top = s.nlargest(7).index
        eq_rows[t] = float(kf_.loc[t, top].mean())
    eq_mom = pd.Series(eq_rows).rename("eq_mom")

    mkt12 = (1 + mkt_).rolling(12).apply(np.prod, raw=True) - 1
    rf12 = (1 + rf_).rolling(12).apply(np.prod, raw=True) - 1
    gem_pick_mkt = (mkt12 - rf12).shift(1) > 0
    defensive = pd.Series(np.where(gem_pick_mkt.reindex(idx).fillna(False), mkt_, bond_),
                          index=idx).rename("defensive")

    lev = pd.Series(np.where(trend_on, 2 * mkt_ - (rf_ + FIN_SPREAD / 12), rf_),
                    index=idx).rename("lev_trend")

    sleeves = pd.concat([eq_mom, defensive, lev, gold_.rename("gold"),
                         bond_.rename("bonds")], axis=1).dropna()
    vol = sleeves.rolling(IV_LOOKBACK).std()
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).shift(1)
    combo = (w * sleeves).sum(axis=1).where(w.notna().all(axis=1)).dropna()
    combo = combo.loc[START:END]
    mktw = mkt_.reindex(combo.index)
    ew = sleeves.mean(axis=1).reindex(combo.index)

    # ---- CAL-3: analog vs the REAL flagship on the overlap ----
    import validate_recommendation as vr
    rp_daily, _e, _s = vr.build_combo()
    real_m = compound_to_monthly(rp_daily)
    real_m.index = pd.PeriodIndex(real_m.index, freq="M")
    ov = pd.concat([combo.rename("analog"), real_m.rename("real")], axis=1).dropna()
    corr3 = float(ov.corr().iloc[0, 1])
    dr_real = mdd((1 + ov["real"]).cumprod()) / mdd((1 + mktw.reindex(ov.index)).cumprod())
    dr_analog = mdd((1 + ov["analog"]).cumprod()) / mdd((1 + mktw.reindex(ov.index)).cumprod())
    cal3 = (corr3 >= 0.60) and (0.37 <= dr_analog <= 0.77)
    print(f"CAL-3 analog vs real flagship ({ov.index[0]}..{ov.index[-1]}): corr {corr3:+.2f} "
          f"(>=0.60); MDD-ratio analog {dr_analog:.2f} vs real {dr_real:.2f} (band 0.37-0.77) "
          f"-> {'PASS' if cal3 else 'FAIL'}")
    if not cal3:
        print("VERDICT: INVALID-TEST -- the analog does not reproduce the mechanism's shape.")
        return

    # ---- headline ----
    yrs = len(combo) / 12
    cagr = (1 + combo).prod() ** (1 / yrs) - 1
    m_cagr = (1 + mktw).prod() ** (1 / yrs) - 1
    print("-" * 100)
    print(f"1975-2026: combo CAGR {cagr:+.1%} MDD {mdd((1+combo).cumprod()):+.1%} | "
          f"market CAGR {m_cagr:+.1%} MDD {mdd((1+mktw).cumprod()):+.1%} | "
          f"EW-5 MDD {mdd((1+ew).cumprod()):+.1%}")

    # ---- C1 per-decade ----
    print("C1 per-decade MDD ratio (combo/market):")
    dec_ok = 0
    decades = [("1975", "1984"), ("1985", "1994"), ("1995", "2004"), ("2005", "2014"), ("2015", "2026")]
    for a, b in decades:
        dc, dm, r = window_ratio(combo, mktw, a, b)
        ok = r <= 0.8
        dec_ok += ok
        print(f"  {a}-{b}: combo {dc:+.1%} vs mkt {dm:+.1%} -> ratio {r:.2f} {'OK' if ok else '--'}")
    print(f"  decades with ratio<=0.8: {dec_ok}/5")

    # ---- C2 named positive-correlation windows ----
    print("C2 bond-equity positive-correlation windows (THE question):")
    named = [("W1 stagflation", "1976-01", "1981-12"), ("W2 bond massacre", "1994-01", "1994-12"),
             ("W3 2022", "2022-01", "2022-12")]
    passes, fails = 0, 0
    for lab, a, b in named:
        dc, dm, r = window_ratio(combo, mktw, a, b)
        passes += r <= 0.8
        fails += r >= 1.0
        print(f"  {lab} ({a}..{b}): combo {dc:+.1%} vs mkt {dm:+.1%} -> ratio {r:.2f}")
    sb = pd.concat([mktw.rename("m"), bond.reindex(combo.index).rename("b")], axis=1)
    poscorr = (sb["m"].rolling(36).corr(sb["b"]) > 0)
    pos_idx = poscorr[poscorr].index
    cpos, mpos = combo.reindex(pos_idx), mktw.reindex(pos_idx)
    dpos_c, dpos_m = mdd((1 + cpos).cumprod()), mdd((1 + mpos).cumprod())
    rpos = dpos_c / dpos_m
    print(f"  pooled corr>0 regime ({len(pos_idx)} months, {len(pos_idx)/len(combo):.0%} of sample): "
          f"combo {dpos_c:+.1%} vs mkt {dpos_m:+.1%} -> ratio {rpos:.2f}")
    if passes >= 2 and rpos <= 0.9:
        verdict = "MECHANISM-ROBUST -- the risk-shaping survives bond-equity positive-correlation regimes."
    elif fails >= 2:
        verdict = "REGIME-CHILD -- the deliverable does not survive outside the 2015-2026 regime."
    else:
        verdict = "MIXED -- named-window table is the verdict of record."

    # ---- C3 stagflation decomposition ----
    print("C3 1975-1981 sleeve contributions (pre-stated prediction: gold, not bonds):")
    contrib = (w.reindex(combo.index) * sleeves.reindex(combo.index)).loc["1975":"1981"]
    for kcol in sleeves.columns:
        ann = contrib[kcol].mean() * 12
        print(f"  {kcol:9s}: {ann:+.2%}/yr contribution")
    for kcol in ("gold", "bonds"):
        r75 = (1 + sleeves[kcol].loc["1975":"1981"]).prod() ** (1 / 7) - 1
        print(f"  {kcol} sleeve standalone CAGR 1975-81: {r75:+.1%}")

    # ---- C4 1970-1974 four-sleeve descriptive ----
    s4 = sleeves.drop(columns="gold")
    vol4 = s4.rolling(IV_LOOKBACK).std()
    w4 = (1 / vol4).div((1 / vol4).sum(axis=1), axis=0).shift(1)
    c4r = (w4 * s4).sum(axis=1).where(w4.notna().all(axis=1)).dropna().loc["1970-01":"1974-12"]
    m4 = mkt_.reindex(c4r.index)
    if len(c4r) > 12:
        print(f"C4 1970-1974 (4-sleeve, no gold): combo MDD {mdd((1+c4r).cumprod()):+.1%} vs "
              f"mkt {mdd((1+m4).cumprod()):+.1%}")

    print("-" * 100)
    print(f"VERDICT: {verdict}")
    print("=" * 100)

    # ---- chart ----
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), height_ratios=[2.2, 1],
                             sharex=True)
    ax = axes[0]
    t = combo.index.to_timestamp()
    ax.plot(t, (1 + combo).cumprod(), lw=1.3, color="#1565c0", label="mechanism analog combo")
    ax.plot(t, (1 + mktw).cumprod(), lw=1.1, color="#757575", label="US market TR")
    for lab, a, b in named:
        ax.axvspan(pd.Period(a, "M").to_timestamp(), pd.Period(b, "M").to_timestamp("M"),
                   color="#c62828", alpha=0.12)
    ax.set_yscale("log")
    ax.legend(fontsize=9)
    ax.set_title("TR-35: flagship mechanism replay 1975-2026 (red bands = bond-equity "
                 "positive-correlation windows)", fontsize=11)
    ax = axes[1]
    ddc = (1 + combo).cumprod()
    ddm = (1 + mktw).cumprod()
    ax.fill_between(t, (ddc / ddc.cummax() - 1) * 100, 0, color="#1565c0", alpha=0.5,
                    label="combo drawdown")
    ax.plot(t, (ddm / ddm.cummax() - 1) * 100, color="#757575", lw=0.9, label="market drawdown")
    ax.legend(fontsize=8)
    ax.set_ylabel("drawdown (%)")
    for a in axes:
        a.grid(alpha=0.3)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr35_mechanism_replay.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
