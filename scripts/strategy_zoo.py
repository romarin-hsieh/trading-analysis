"""STRATEGY ZOO -- batch-validate 60+ strategy variants in one harness (goal: 100+ catalogued).

Families (all leak-free: every signal .shift(1) before position; net 5bps/leg on QQQ, 10bps on
cross-sectional stocks): SMA/EMA crosses, Vegas tunnel (EMA144/169+EMA12), Donchian, Bollinger
(mean-rev + breakout), RSI (Connors RSI2 + RSI14), MACD, ROC/ts-momentum, 52w-high proximity,
Keltner, chandelier trail, golden-cross+volume, volume-surge breakout, OBV, IBS, calendar (TOM,
weekday), VIX regime rules, vol-target overlay, and cross-sectional momentum/52wh/low-vol/volume
on the 47-name tech/AI/space universe.

MULTIPLE-TESTING HONESTY: with N~65 variants over ~11y, the expected MAX Sharpe under the null
(no skill) is ~sqrt(2 ln N)/sqrt(T) ~ 0.9. Any zoo winner below that is indistinguishable from
selection luck; treat the table as a SCREEN, not proof. Ensemble evaluation happens in
scripts/ensemble_mix.py with a train/holdout split.

Run: uv run python scripts/strategy_zoo.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import horizon_slots as hs  # noqa: E402  (xsect_momentum reuse)
import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

COST_ETF = 0.0005
START = "2015-01-01"


# ---------------------------------------------------------------- indicator helpers
def rsi(px: pd.Series, n: int) -> pd.Series:
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(h, l, c, n=14):  # noqa: E741
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def state_rule(enter: pd.Series, exit_: pd.Series) -> pd.Series:
    """Stateful long/flat: go long on `enter`, flat on `exit_`, hold in between."""
    sig = pd.Series(np.nan, index=enter.index)
    sig[enter] = 1.0
    sig[exit_] = 0.0
    return sig.ffill().fillna(0.0)


def run_rule(pos: pd.Series, r: pd.Series, cost=COST_ETF) -> pd.Series:
    pos = pos.reindex(r.index).fillna(0.0).shift(1).fillna(0.0)
    turn = pos.diff().abs().fillna(0.0)
    return pos * r - turn * cost


def stats_row(name, ret, bench_sharpe=None):
    ret = ret.loc[START:].dropna()
    eq = (1 + ret).cumprod()
    active_days = float((ret != 0).mean())
    return {"name": name, "CAGR": cagr(eq), "Sharpe": sharpe(ret), "MDD": max_drawdown(eq),
            "exposure": active_days}


def main():
    store = DuckStore("./data")
    oh = store.load_ohlcv(["QQQ"]).set_index("ts").sort_index().loc["2014-06-01":]
    h, l, c, v = oh["high"], oh["low"], oh["close"], oh["volume"]  # noqa: E741
    adj = oh["adj_close"]
    r = adj.pct_change().fillna(0.0)
    vix = store.load_close_pivot(["^VIX"], column="close").iloc[:, 0].reindex(c.index).ffill()

    Z: dict[str, pd.Series] = {}   # name -> position series (0..1)

    # 1-2) SMA / EMA crosses -----------------------------------------------------
    grid = [(5, 20), (10, 50), (10, 100), (20, 50), (20, 100), (20, 200), (50, 100), (50, 200)]
    for f, s_ in grid:
        Z[f"SMA_cross_{f}_{s_}"] = (c.rolling(f).mean() > c.rolling(s_).mean()).astype(float)
        Z[f"EMA_cross_{f}_{s_}"] = (c.ewm(span=f, adjust=False).mean() > c.ewm(span=s_, adjust=False).mean()).astype(float)
    for n in (20, 50, 200):
        Z[f"close_above_SMA{n}"] = (c > c.rolling(n).mean()).astype(float)

    # 3) Vegas tunnel --------------------------------------------------------------
    e12 = c.ewm(span=12, adjust=False).mean()
    e144 = c.ewm(span=144, adjust=False).mean()
    e169 = c.ewm(span=169, adjust=False).mean()
    tunnel_hi = pd.concat([e144, e169], axis=1).max(axis=1)
    Z["Vegas_strict"] = ((c > tunnel_hi) & (e12 > tunnel_hi)).astype(float)
    Z["Vegas_loose"] = (c > tunnel_hi).astype(float)

    # 4) Donchian ------------------------------------------------------------------
    for hi_n, lo_n in ((20, 10), (55, 20), (10, 5)):
        ent = c > c.rolling(hi_n).max().shift(1)
        ex = c < c.rolling(lo_n).min().shift(1)
        Z[f"Donchian_{hi_n}_{lo_n}"] = state_rule(ent, ex)

    # 5) Bollinger -----------------------------------------------------------------
    for n, k in ((20, 2.0), (20, 1.0)):
        mid = c.rolling(n).mean()
        sd = c.rolling(n).std()
        Z[f"Boll_meanrev_{n}_{k:g}"] = state_rule(c < mid - k * sd, c > mid)
        Z[f"Boll_breakout_{n}_{k:g}"] = state_rule(c > mid + k * sd, c < mid)

    # 6) RSI -----------------------------------------------------------------------
    r2, r14 = rsi(c, 2), rsi(c, 14)
    Z["ConnorsRSI2_under200SMA"] = state_rule((r2 < 5) & (c > c.rolling(200).mean()), r2 > 70)
    Z["RSI14_30_70"] = state_rule(r14 < 30, r14 > 70)
    Z["RSI14_40_60"] = state_rule(r14 < 40, r14 > 60)

    # 7) MACD ----------------------------------------------------------------------
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    sig9 = macd.ewm(span=9, adjust=False).mean()
    Z["MACD_signal_cross"] = (macd > sig9).astype(float)
    Z["MACD_zero_cross"] = (macd > 0).astype(float)

    # 8) ROC ts-momentum -----------------------------------------------------------
    for n in (21, 63, 126, 252):
        Z[f"TSmom_{n}d"] = (c > c.shift(n)).astype(float)

    # 9) 52w-high proximity ---------------------------------------------------------
    hi52 = c.rolling(252).max()
    Z["near52wHigh_5pct"] = (c > 0.95 * hi52).astype(float)
    Z["near52wHigh_10pct"] = (c > 0.90 * hi52).astype(float)

    # 10) Keltner breakout ------------------------------------------------------------
    a20 = atr(h, l, c, 20)
    kmid = c.ewm(span=20, adjust=False).mean()
    Z["Keltner_breakout"] = state_rule(c > kmid + 2 * a20, c < kmid)

    # 11) Chandelier trail (SuperTrend-like) ------------------------------------------
    a14 = atr(h, l, c, 14)
    Z["Chandelier_22_3ATR"] = (c > (c.rolling(22).max() - 3 * a14).shift(1)).astype(float)

    # 12-14) volume family -------------------------------------------------------------
    v20, v100 = v.rolling(20).mean(), v.rolling(100).mean()
    Z["GoldenCross_volConfirm"] = ((c.rolling(50).mean() > c.rolling(200).mean()) & (v20 > v100)).astype(float)
    surge = (c > c.rolling(20).max().shift(1)) & (v > 2 * v20)
    Z["VolSurge_breakout_hold21"] = surge.rolling(21).max().fillna(0.0)
    obv = (np.sign(c.diff()).fillna(0.0) * v).cumsum()
    Z["OBV_above_SMA50"] = (obv > obv.rolling(50).mean()).astype(float)
    Z["MAcross_AND_OBV"] = (Z["SMA_cross_20_100"].astype(bool) & Z["OBV_above_SMA50"].astype(bool)).astype(float)

    # 15) IBS mean-reversion -------------------------------------------------------------
    ibs = (c - l) / (h - l).replace(0, np.nan)
    Z["IBS_02_08"] = state_rule(ibs < 0.2, ibs > 0.8)

    # 16) calendar ------------------------------------------------------------------------
    ym = c.index.to_period("M")
    pos_in_m = pd.Series(np.arange(len(c)), index=c.index).groupby(ym).cumcount()
    cnt = pd.Series(1, index=c.index).groupby(ym).transform("size")
    Z["TurnOfMonth"] = ((pos_in_m <= 2) | (cnt - 1 - pos_in_m == 0)).astype(float)
    Z["Skip_Mondays"] = pd.Series((c.index.dayofweek != 0).astype(float), index=c.index)

    # 17) VIX rules --------------------------------------------------------------------------
    Z["VIX_riskoff_25"] = (vix <= 25).astype(float)
    vix_pct = vix.rolling(252).rank(pct=True)
    Z["VIX_spike_meanrev"] = (vix_pct > 0.85).astype(float)          # long equity AFTER panic
    Z["VIX_calm_only"] = (vix_pct < 0.5).astype(float)

    # 18) vol-target overlay --------------------------------------------------------------------
    rv = r.rolling(20).std() * np.sqrt(252)
    Z["VolTarget_12pct"] = (0.12 / rv).clip(upper=1.0).fillna(0.0)

    # ---------------- evaluate all time-series rules on QQQ -------------------------------
    rows = []
    for name, pos in Z.items():
        ret = run_rule(pos, r)
        rows.append(stats_row(name, ret))

    # ---------------- cross-sectional block (47-name universe, 10bps) ----------------------
    px47 = ss._px(sorted({x for vv in ss.SECTORS.values() for x in vv}))
    for k, hold, lb, skip, nm in ((5, 63, 252, 21, "XS_mom12-1_top5_qtr"),
                                  (10, 21, 126, 21, "XS_mom6-1_top10_mth"),
                                  (10, 21, 252, 21, "XS_mom12-1_top10_mth"),
                                  (5, 21, 126, 21, "XS_mom6-1_top5_mth")):
        ret, _ = hs.xsect_momentum(px47, k=k, hold=hold, lb=lb, skip=skip)
        rows.append(stats_row(nm, ret))
    r47 = px47.pct_change(fill_method=None)
    f_52 = (px47 / px47.rolling(252).max()).shift(1)
    f_lv = (-r47.rolling(63).std()).shift(1)
    f_vol = (px47.notna() * (px47 * 0).add(
        (r47.abs().rolling(21).mean() / r47.abs().rolling(100).mean()), fill_value=0)).shift(1)
    for fac, nm in ((f_52, "XS_52wHigh_top10"), (f_lv, "XS_lowvol_top10"), (f_vol, "XS_volSurprise_top10")):
        held = pd.DataFrame(0.0, index=px47.index, columns=px47.columns)
        grid_b = np.zeros(len(px47), dtype=bool)
        grid_b[::21] = True
        rowv = pd.Series(0.0, index=px47.columns)
        for i, t in enumerate(px47.index):
            if grid_b[i]:
                m = fac.loc[t].dropna()
                rowv = pd.Series(0.0, index=px47.columns)
                if len(m) >= 10:
                    rowv[m.nlargest(10).index] = 1.0
            held.loc[t] = rowv
        w = held / 10
        turn = w.diff().abs().sum(axis=1).fillna(0.0)
        ret = (w.shift(1) * r47).sum(axis=1) - turn * 0.0010
        rows.append(stats_row(nm, ret))

    bench = stats_row("QQQ_buy&hold", r)
    n_var = len(rows)
    t_years = (c.index[-1] - pd.Timestamp(START)).days / 365.25
    emax = float(np.sqrt(2 * np.log(n_var)) / np.sqrt(t_years))

    df = pd.DataFrame(rows).sort_values("Sharpe", ascending=False).reset_index(drop=True)
    print("=" * 100)
    print(f"STRATEGY ZOO -- {n_var} variants batch-validated on QQQ / 47-name tech universe, {START}..{c.index[-1].date()}")
    print(f"benchmark QQQ buy&hold: CAGR {bench['CAGR']:+.1%}  Sharpe {bench['Sharpe']:+.2f}  MDD {bench['MDD']:+.1%}")
    print(f"MULTIPLE-TESTING BAR: E[max Sharpe | no skill, N={n_var}, T={t_years:.0f}y] ~= {emax:.2f}")
    print("=" * 100)
    print(f"{'#':>3s} {'variant':34s} {'CAGR':>7s} {'Sharpe':>7s} {'MDD':>7s} {'expo':>6s}")
    for i, rw in df.iterrows():
        flag = " <== beats B&H Sharpe" if rw["Sharpe"] > bench["Sharpe"] else ""
        print(f"{i+1:>3d} {rw['name']:34s} {rw['CAGR']:+7.1%} {rw['Sharpe']:+7.2f} {rw['MDD']:+7.1%} {rw['exposure']:6.0%}{flag}")
    n_beat = int((df["Sharpe"] > bench["Sharpe"]).sum())
    n_above_null = int((df["Sharpe"] > emax).sum())
    print("-" * 100)
    print(f"beat QQQ B&H Sharpe ({bench['Sharpe']:+.2f}): {n_beat}/{n_var}")
    print(f"above the N-trials null bar ({emax:.2f}): {n_above_null}/{n_var}")
    print("VERDICT: treat as a SCREEN. Single-rule winners under the null bar are selection luck;")
    print("mixing/ensembles are evaluated with a train/holdout split in scripts/ensemble_mix.py.")
    print("=" * 100)

    # persist position matrix for the ensemble step
    posmat = pd.DataFrame({k_: v_.reindex(c.index).fillna(0.0) for k_, v_ in Z.items()})
    posmat.to_parquet("data/_zoo_positions.parquet")
    r.to_frame("qqq_ret").to_parquet("data/_zoo_qqq_ret.parquet")
    print(f"saved {posmat.shape[1]} TS position series -> data/_zoo_positions.parquet (for ensemble_mix)")


if __name__ == "__main__":
    main()
