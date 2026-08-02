"""TR-42 -- L2 bond-equity correlation brake (docs/27 risk-engine v2, first challenger).

TR-35 found the flagship's one structural exposure: equity-led crashes are cut to
0.07-0.16x the market's drawdown, but RATE-LED windows (1976-81 stagflation, 1994) get
ZERO added protection -- the 58% bond leg stops diversifying exactly when it is needed,
and gold (not bonds) carried stagflation. This is the first risk-engine v2 challenger:
detect the regime where the diversification assumption is broken, and act on it.

THE TRAP THIS MUST NOT FALL INTO: seven timing claims have died in this repo, every one
of them beaten by a DUMB CONSTANT exposure (Cederburg control). A correlation brake is
NOT a return forecast -- it is a statement that the risk model's inputs have changed --
but it can still be beaten by a constant, and if it is, it is the eighth failure. The
decisive check is therefore not "does the brake help" but "does it beat a constant
de-lever at the same average exposure, plus a random-brake placebo".

F0 DECLARATION (pre-committed)
  claim  : braking on a positive stock-bond correlation regime improves delivery
         (drawdown/Calmar) over the incumbent AND beats the constant-exposure control
         at matched average exposure.
  seats  : (1) LIVE = flagship 2015-2026 (build_combo, daily); (2) ANALOG = TR-35's
         50-year monthly mechanism replay 1975-2026, which is where rate-led regimes
         actually exist. The ANALOG seat carries the verdict; the live seat is a
         consistency check (it contains only 2022).
  signal : rolling 36m correlation of equity and bond sleeve returns, LAGGED one period.
         Regime "broken" when corr > 0. Pre-registered variants:
           A  de-lever the whole book to 70% while broken
           B  move the bond sleeve's weight to gold while broken
         No threshold search, no parameter tuning: 36m/0.0/70% fixed here.
  CAL    : incumbent reproduces TR-35's headline on the analog seat (52y MDD within
         +-3pp of -14.6%) and build_combo's live Sharpe within +-0.15. Fail -> STOP.
  C1     : brake A/B vs incumbent, full analog sample: MDD, Calmar, CAGR.
  C2 (decisive): vs CONSTANT exposure at the SAME average exposure as the brake, and vs
         a RANDOM brake (same number of braked months, shuffled) 1000x -> the brake must
         beat the constant on Calmar AND land above the random p95.
  C3     : the rate-led windows that motivated this (1976-81, 1994, 2022) -- does the
         brake actually protect where the incumbent had nothing?
  C4     : live seat consistency (2015-2026) + alpha-t must not degrade below 2.0.
  VERDICT: beats constant AND random p95 on the analog seat -> ADOPT-CANDIDATE (then the
         live seat and alpha-t decide); loses to constant -> EIGHTH TIMING FAILURE
         (recorded, the iron law extends to risk-input timing).
  anti-HARKing : two pre-registered variants only, thresholds fixed above before running;
         trials +1 family (risk-engine challengers).

Run: uv run python scripts/tests/tr42_correlation_brake.py   (~3 min)
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
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

CORR_WIN = 36
BRAKE_LEVEL = 0.70
N_PLACEBO = 1000
SEED = 0


def mdd(nav: pd.Series) -> float:
    return float((nav / nav.cummax() - 1).min())


def stats(r: pd.Series, per: int) -> dict:
    nav = (1 + r).cumprod()
    yrs = len(r) / per
    cagr = float(nav.iloc[-1] ** (1 / yrs) - 1)
    d = mdd(nav)
    return {"cagr": cagr, "mdd": d, "calmar": cagr / abs(d) if d < 0 else np.nan}


def build_analog():
    """TR-35's monthly analog sleeves + inverse-vol allocator, rebuilt here so the brake
    can act on the weights rather than only on the finished return stream."""
    import tr35_mechanism_replay as t35

    from tr20_ff5_attribution import load_ff5_umd_monthly
    from tr32_industry_momentum import load_kf49_monthly

    ff = load_ff5_umd_monthly(start="1965-01-01")
    mkt = (ff["Mkt-RF"] + ff["RF"]).rename("mkt")
    rf = ff["RF"]
    kf = load_kf49_monthly()
    kf.index = kf.index.to_period("M")
    gold = t35.load_gold_monthly().pct_change().rename("gold")
    bond = t35.bond_tr_from_yields(t35.load_gs10_monthly()).rename("bonds")

    idx = mkt.index.intersection(kf.index).intersection(gold.index).intersection(bond.index)
    mkt_, rf_, kf_, gold_, bond_ = (x.reindex(idx) for x in (mkt, rf, kf, gold, bond))
    level = (1 + mkt_).cumprod()
    trend_on = (level > level.rolling(10).mean()).shift(1).fillna(False)
    mom = kf_.shift(2) / kf_.shift(12) - 1
    eq_rows = {}
    for t in idx:
        s = mom.loc[t].dropna()
        eq_rows[t] = rf_.loc[t] if (len(s) < 30 or not trend_on.loc[t]) else \
            float(kf_.loc[t, s.nlargest(7).index].mean())
    eq = pd.Series(eq_rows).rename("eq_mom")
    mkt12 = (1 + mkt_).rolling(12).apply(np.prod, raw=True) - 1
    rf12 = (1 + rf_).rolling(12).apply(np.prod, raw=True) - 1
    gem = ((mkt12 - rf12).shift(1) > 0).reindex(idx).fillna(False)
    defensive = pd.Series(np.where(gem, mkt_, bond_), index=idx).rename("defensive")
    lev = pd.Series(np.where(trend_on, 2 * mkt_ - (rf_ + 0.006 / 12), rf_),
                    index=idx).rename("lev_trend")
    sleeves = pd.concat([eq, defensive, lev, gold_, bond_], axis=1).dropna()
    vol = sleeves.rolling(12).std()
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).shift(1)
    return sleeves, w, mkt_


def apply_brake(sleeves, w, broken, variant: str) -> pd.Series:
    w2 = w.copy()
    if variant == "B":                    # move bond weight to gold while broken
        b = w2.loc[broken, "bonds"]
        w2.loc[broken, "gold"] = w2.loc[broken, "gold"] + b
        w2.loc[broken, "bonds"] = 0.0
        scale = pd.Series(1.0, index=w2.index)
    else:                                  # A: de-lever the book
        scale = pd.Series(1.0, index=w2.index)
        scale[broken] = BRAKE_LEVEL
    r = (w2 * sleeves).sum(axis=1) * scale
    return r.where(w2.notna().all(axis=1)).dropna()


def main():
    rng = np.random.default_rng(SEED)
    sleeves, w, mkt = build_analog()
    sl = sleeves.loc["1975-01":]
    w = w.loc["1975-01":]
    incumbent = (w * sl).sum(axis=1).where(w.notna().all(axis=1)).dropna()
    idx = incumbent.index

    print("=" * 100)
    print("TR-42  L2 股債相關 regime 煞車(風險引擎 v2 第一位挑戰者)")
    print("=" * 100)

    st_inc = stats(incumbent, 12)
    cal = abs(st_inc["mdd"] - (-0.146)) <= 0.03
    print(f"CAL(類比座位重現 TR-35):MDD {st_inc['mdd']:+.1%} vs −14.6%(±3pp)、"
          f"CAGR {st_inc['cagr']:+.1%} -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: INVALID-TEST -- analog engine drift vs TR-35.")
        return

    # regime signal: rolling corr of equity-ish vs bonds, lagged
    eq_stream = sl["eq_mom"]
    corr = eq_stream.rolling(CORR_WIN).corr(sl["bonds"]).shift(1)
    broken = (corr > 0).reindex(idx).fillna(False)
    share = float(broken.mean())
    print(f"regime 訊號:{CORR_WIN} 月滾動股債相關 > 0 的月份佔 {share:.0%}"
          f"(落後一期,無前視)")

    res = {"現役(無煞車)": incumbent}
    for variant, lab in (("A", "煞車A 破裂時降到 70%"), ("B", "煞車B 破裂時債換金")):
        res[lab] = apply_brake(sl, w, broken, variant)

    print("-" * 100)
    print("C1 全樣本 1975-2026:")
    for lab, r in res.items():
        s = stats(r, 12)
        print(f"  {lab:<20}: CAGR {s['cagr']:+.1%}  MDD {s['mdd']:+.1%}  Calmar {s['calmar']:.2f}")

    # ---- C2 decisive: constant control at matched average exposure + random placebo ----
    print("-" * 100)
    print("C2 決定性對照(Cederburg 靜態控制 + 隨機煞車安慰劑):")
    avg_exp = 1 - (1 - BRAKE_LEVEL) * share
    const = incumbent * avg_exp
    s_const = stats(const, 12)
    print(f"  恆定 {avg_exp:.0%} 曝險(與煞車A 同平均曝險): CAGR {s_const['cagr']:+.1%}  "
          f"MDD {s_const['mdd']:+.1%}  Calmar {s_const['calmar']:.2f}")
    n_broken = int(broken.sum())
    plc = []
    for _ in range(N_PLACEBO):
        pos = rng.choice(len(idx), n_broken, replace=False)
        b = pd.Series(False, index=idx)
        b.iloc[pos] = True
        plc.append(stats(apply_brake(sl, w, b, "A"), 12)["calmar"])
    p95 = float(np.percentile(plc, 95))
    cal_a = stats(res["煞車A 破裂時降到 70%"], 12)["calmar"]
    cal_b = stats(res["煞車B 破裂時債換金"], 12)["calmar"]
    pct_a = float(np.mean(np.array(plc) < cal_a))
    beats_const = cal_a > s_const["calmar"]
    beats_plc = cal_a > p95
    print(f"  隨機煞車安慰劑 Calmar p95 = {p95:.2f};煞車A = {cal_a:.2f}"
          f"(第 {pct_a:.0%} 百分位)")
    print(f"  → 勝靜態控制:{beats_const} | 勝隨機 p95:{beats_plc}")

    # ---- C3 rate-led windows ----
    print("-" * 100)
    print("C3 利率主導窗(TR-35 指出現役毫無保護之處):")
    mkt_r = mkt.reindex(idx)
    for lab, a, b in (("停滯性通膨 1976-81", "1976-01", "1981-12"),
                      ("債券大屠殺 1994", "1994-01", "1994-12"),
                      ("2022", "2022-01", "2022-12")):
        dm = mdd((1 + mkt_r.loc[a:b]).cumprod())
        cells = []
        for name, r in res.items():
            d = mdd((1 + r.loc[a:b]).cumprod())
            cells.append(f"{name.split()[0]} {d:+.1%}(比 {d/dm:.2f})")
        print(f"  {lab:<18} 市場 {dm:+.1%} | " + " | ".join(cells))

    # ---- C4 live seat ----
    print("-" * 100)
    import validate_recommendation as vr
    from trading_analysis.factors.attribution import compound_to_monthly, load_ff_factors_monthly
    rp, _e, live_sleeves = vr.build_combo()
    lm = compound_to_monthly(rp)
    lm.index = pd.PeriodIndex(lm.index, freq="M")
    ls_m = live_sleeves.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    ls_m.index = pd.PeriodIndex(ls_m.index, freq="M")
    corr_l = ls_m["equity_mom"].rolling(CORR_WIN).corr(ls_m["bonds"]).shift(1)
    broken_l = (corr_l > 0).reindex(lm.index).fillna(False)
    live_brake = lm * np.where(broken_l, BRAKE_LEVEL, 1.0)
    ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)

    def alpha_t(x):
        df = pd.concat([x.rename("r"), ff], axis=1).dropna()
        y = df["r"] - df["RF"]
        X = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "UMD"]])
        return float(sm.OLS(y, X).fit().tvalues["const"])

    s_live, s_live_b = stats(lm, 12), stats(live_brake, 12)
    t_live, t_brake = alpha_t(lm), alpha_t(live_brake)
    print(f"C4 實際座位 2015-2026(僅含 2022,一致性檢查):破裂月份佔 {broken_l.mean():.0%}")
    print(f"  現役 : CAGR {s_live['cagr']:+.1%} MDD {s_live['mdd']:+.1%} alpha-t {t_live:+.2f}")
    print(f"  煞車A: CAGR {s_live_b['cagr']:+.1%} MDD {s_live_b['mdd']:+.1%} alpha-t {t_brake:+.2f}")

    if beats_const and beats_plc:
        v = ("ADOPT-CANDIDATE -- 煞車在類比座位上同時勝過靜態控制與隨機安慰劑;"
             "進入實際座位與 alpha-t 的最終檢查。")
    elif not beats_const:
        v = (f"EIGHTH TIMING FAILURE -- 煞車 Calmar {cal_a:.2f} 輸給同平均曝險的恆定部位 "
             f"{s_const['calmar']:.2f}:擇時鐵律延伸到「風險輸入型擇時」,不只報酬擇時。")
    else:
        v = (f"REJECTED -- 勝靜態但未過隨機安慰劑 p95({cal_a:.2f} vs {p95:.2f}):"
             f"訊號沒有比隨機挑同樣多的月份更好。")
    print("-" * 100)
    print(f"VERDICT: {v}")
    print(f"(煞車B 債換金 Calmar {cal_b:.2f} 供對照)")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))
    ax = axes[0]
    for lab, r in res.items():
        nav = (1 + r).cumprod()
        ax.plot(nav.index.to_timestamp(), nav.values, lw=1.3,
                label=f"{lab}(Calmar {stats(r,12)['calmar']:.2f})")
    navc = (1 + const).cumprod()
    ax.plot(navc.index.to_timestamp(), navc.values, lw=1.1, ls="--", color="#616161",
            label=f"恆定 {avg_exp:.0%} 控制(Calmar {s_const['calmar']:.2f})")
    ax.set_yscale("log")
    ax.legend(fontsize=8.5)
    ax.set_title("類比座位 1975-2026(對數)", fontsize=10.5)
    ax = axes[1]
    ax.hist(plc, bins=50, color="#90a4ae", alpha=0.85, label="隨機煞車安慰劑")
    ax.axvline(p95, color="#c62828", ls="--", lw=2, label=f"隨機 p95 {p95:.2f}")
    ax.axvline(cal_a, color="#1565c0", lw=2.5, label=f"煞車A {cal_a:.2f}")
    ax.axvline(s_const["calmar"], color="#2e7d32", lw=2, ls=":",
               label=f"恆定控制 {s_const['calmar']:.2f}")
    ax.set_xlabel("Calmar")
    ax.set_title("C2:煞車有贏過「隨便踩」和「一直輕踩」嗎?", fontsize=10.5)
    ax.legend(fontsize=8.5)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-42:股債相關 regime 煞車 —— 風險引擎 v2 第一位挑戰者", fontsize=12.5)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr42_correlation_brake.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
