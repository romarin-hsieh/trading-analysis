"""TR-16 -- IBS mean-reversion: the full fabric v1.2 treatment for the only robust-PASS TS rule.

F0 DECLARATION (pre-committed BEFORE running):
- Mechanism: Internal Bar Strength IBS=(C-L)/(H-L); long when IBS<0.2, flat when IBS>0.8
  (Connors-era index mean-reversion; refs: Pagonidis "The IBS Effect", QuantifiedStrategies).
- Classification: alpha-generation (timing overlay). NATIVE HABITAT: US index ETFs, DAILY bars,
  mean-reversion era 1990s-2010s. Seat tested = native habitat (QQQ + SPY/DIA/IWM replications).
  Mis-application risk: LOW. Re-open condition if FAILED: none (this IS its home turf).
- Falsifiable claims & verdict rule (pre-committed):
  C1 FILL-TIME is the make-or-break: the zoo convention enters AT the signal close (t close ->
     t+1 close). Under the honest B1 standard (fill at NEXT close, t+1 -> t+2) the edge SHRINKS;
     PASSED requires the NEXT-CLOSE variant to still beat (a) QQQ B&H on excess-over-rf Sharpe,
     (b) the constant-exposure static control (Cederburg), (c) the random-entry control's 95th
     percentile. Anything less = PARTIAL (same-close-only artifact) or FAILED.
  C2 LONG HISTORY (1999-2026, incl. 2000-02 and 2008 bears) must show same-sign sub-era gaps.
  C3 Threshold grid (0.2/0.8 base; 0.1/0.9, 0.25/0.75, 0.3/0.7 pre-declared) -> family N=4 into
     the trial registry; report all, judge the BASE (a priori from zoo, not tuned here).
- F12 exemption: stateful daily rule, no rebalance grid -> no phase test (recorded).

Run: uv run python scripts/tests/tr16_ibs.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from trading_analysis.data.store import DuckStore  # noqa: E402

COST = 0.0005
SEED = 11
ERAS = {"1999-2007": ("1999-03-10", "2007-12-31"), "2008-2014": ("2008-01-01", "2014-12-31"),
        "2015-2020": ("2015-01-01", "2020-12-31"), "2021-2026": ("2021-01-01", "2026-07-06")}


def ex_sharpe(x):
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 60 and x.std() > 0 else np.nan


def state_rule(enter, exit_):
    sig = pd.Series(np.nan, index=enter.index)
    sig[enter] = 1.0
    sig[exit_] = 0.0
    return sig.ffill().fillna(0.0)


def run(sig, r, rf, lag, cost_mult=1.0):
    """Position from sig lagged `lag` bars; flat fraction earns rf; returns EXCESS-over-rf series."""
    p = sig.shift(lag).fillna(0.0)
    gross = p * r + (1 - p) * rf - p.diff().abs().fillna(0.0) * COST * cost_mult
    return gross - rf, p


def main():
    rs = np.random.RandomState(SEED)
    store = DuckStore("./data")
    irx = store.load_ohlcv(["^IRX"]).set_index("ts")["close"].sort_index()
    rf_full = ((1 + irx / 100) ** (1 / 252) - 1).rename("rf")

    def load(tkr):
        oh = store.load_ohlcv([tkr]).set_index("ts").sort_index()
        r = oh["adj_close"].pct_change().fillna(0.0)
        ibs = ((oh["close"] - oh["low"]) / (oh["high"] - oh["low"]).replace(0, np.nan))
        rf = rf_full.reindex(oh.index).ffill().fillna(0.0)
        return r, ibs, rf

    # ================= Panel A/B: conventions x tickers, full history ==============
    print("=" * 108)
    print("TR-16  IBS MEAN-REVERSION -- full fabric treatment (excess-over-rf Sharpe everywhere)")
    print("=" * 108)
    print(f"{'ticker':7s} {'span':>20s} {'expo':>5s} | {'B&H exSR':>8s} | {'sameclose exSR':>14s} "
          f"{'NEXTclose exSR':>14s} {'next 2xcost':>11s}")
    results = {}
    for tkr in ("QQQ", "SPY", "DIA", "IWM"):
        r, ibs, rf = load(tkr)
        sig = state_rule(ibs < 0.2, ibs > 0.8)
        bh = ex_sharpe(r - rf)
        s1, _p1 = run(sig, r, rf, lag=1)             # zoo convention: enter AT signal close
        s2, p2 = run(sig, r, rf, lag=2)             # B1 standard: fill at NEXT close
        s2c, _ = run(sig, r, rf, lag=2, cost_mult=2.0)
        results[tkr] = dict(r=r, rf=rf, sig=sig, bh=bh, s1=s1, s2=s2, expo=float(p2.mean()))
        print(f"{tkr:7s} {str(r.index.min().date())+'..'+str(r.index.max().date()):>20s} "
              f"{float(p2.mean()):5.0%} | {bh:+8.2f} | {ex_sharpe(s1):+14.2f} {ex_sharpe(s2):+14.2f} "
              f"{ex_sharpe(s2c):+11.2f}")

    # ================= Panel C: controls on QQQ (next-close convention) ============
    q = results["QQQ"]
    r, rf, sig = q["r"], q["rf"], q["sig"]
    s2 = q["s2"]
    expo = q["expo"]
    # static constant-exposure control (Cederburg)
    static = expo * r + (1 - expo) * rf
    st_ex = ex_sharpe(static - rf)
    # random-entry control: shuffle the POSITION BLOCKS (preserve exposure + holding structure)
    pos2 = sig.shift(2).fillna(0.0).to_numpy()
    # identify holding blocks
    blocks, cur = [], 0
    for v in pos2:
        if v == 1:
            cur += 1
        elif cur:
            blocks.append(cur)
            cur = 0
    if cur:
        blocks.append(cur)
    n = len(pos2)
    rand_ex = []
    rr, rfv = r.to_numpy(), rf.to_numpy()
    for _ in range(200):
        p = np.zeros(n)
        order = rs.permutation(len(blocks))
        starts = np.sort(rs.choice(n - 1, size=len(blocks), replace=False))
        for st, bi in zip(starts, order, strict=False):
            p[st:st + blocks[bi]] = 1.0
        ret = p * rr + (1 - p) * rfv - np.abs(np.diff(p, prepend=0.0)) * COST
        ex = ret - rfv
        rand_ex.append(float(np.mean(ex) / np.std(ex) * np.sqrt(252)))
    rand_ex = np.array(rand_ex)
    p95 = float(np.percentile(rand_ex, 95))
    print("-" * 108)
    print(f"CONTROLS (QQQ, NEXT-close, {ERAS['1999-2007'][0]}..2026): IBS exSR {ex_sharpe(s2):+.2f}")
    print(f"  static {expo:.0%}-exposure control exSR : {st_ex:+.2f}")
    print(f"  random-entry control (200 draws)     : mean {rand_ex.mean():+.2f}  p95 {p95:+.2f}  "
          f"-> IBS at {(rand_ex < ex_sharpe(s2)).mean():.0%} pctile")

    # ================= Panel D: sub-eras (F7 v2 long-history) ======================
    print("-" * 108)
    print(f"{'era':12s} {'B&H exSR':>9s} {'IBS(next) exSR':>14s} {'gap':>7s}   (QQQ)")
    era_gaps = []
    for era, (a, b) in ERAS.items():
        bh_e = ex_sharpe((r - rf).loc[a:b])
        ibs_e = ex_sharpe(s2.loc[a:b])
        era_gaps.append(ibs_e - bh_e)
        print(f"{era:12s} {bh_e:>+9.2f} {ibs_e:>+14.2f} {ibs_e - bh_e:>+7.2f}")

    # ================= Panel E: pre-declared threshold grid (family N=4) ===========
    print("-" * 108)
    print("THRESHOLD GRID (pre-declared; family N=4 -> trial registry):")
    for lo, hi in ((0.2, 0.8), (0.1, 0.9), (0.25, 0.75), (0.3, 0.7)):
        rq, ib, rfq = load("QQQ")
        sg = state_rule(ib < lo, ib > hi)
        ex2, pp = run(sg, rq, rfq, lag=2)
        print(f"  enter<{lo:.2f}/exit>{hi:.2f}: exSR {ex_sharpe(ex2):+.2f}  expo {float(pp.mean()):.0%}")

    # ================= Panel F: F9 window randomization on full history ============
    win, K = 756, 300
    ex_np = s2.to_numpy()
    bh_np = (r - rf).to_numpy()
    beat = []
    for _ in range(K):
        a = rs.randint(0, len(ex_np) - win)
        se = ex_np[a:a + win]
        sb = bh_np[a:a + win]
        beat.append(float(np.mean(se) / np.std(se)) > float(np.mean(sb) / np.std(sb)))
    print("-" * 108)
    print(f"F9: P(IBS next-close beats B&H) over {K} random 3y windows (1999-2026): {np.mean(beat):.0%}")

    # ================= verdict (per pre-committed rule) =============================
    ibs_ex = ex_sharpe(s2)
    c_bh = ibs_ex > q["bh"]
    c_st = ibs_ex > st_ex
    c_rand = ibs_ex > p95
    c_eras = all(g > 0 for g in era_gaps)
    print("=" * 108)
    print(f"PRE-COMMITTED CHECKS (NEXT-close): beats B&H: {c_bh} | beats static control: {c_st} | "
          f"beats random p95: {c_rand} | all-era positive gap: {c_eras}")
    verdict = "PASSED" if (c_bh and c_st and c_rand) else ("PARTIAL" if c_bh or c_st else "FAILED")
    print(f"VERDICT: {verdict}")
    print("=" * 108)

    # chart
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    eq1 = (1 + q["s1"] + q["rf"]).cumprod()
    eq2 = (1 + s2 + rf).cumprod()
    eqb = (1 + r).cumprod()
    ax[0].semilogy(eqb.index, eqb, label="QQQ B&H", lw=1)
    ax[0].semilogy(eq1.index, eq1, label="IBS same-close (zoo conv.)", lw=1)
    ax[0].semilogy(eq2.index, eq2, label="IBS NEXT-close (B1 honest)", lw=1)
    ax[0].legend()
    ax[0].set_title("IBS on QQQ 1999-2026: fill-time convention decides")
    ax[1].hist(rand_ex, bins=25, alpha=0.7, label="random-entry control (200)")
    ax[1].axvline(ex_sharpe(s2), color="r", lw=2, label=f"IBS next-close {ex_sharpe(s2):+.2f}")
    ax[1].axvline(st_ex, color="g", ls="--", lw=1.5, label=f"static control {st_ex:+.2f}")
    ax[1].legend()
    ax[1].set_title("Controls (excess Sharpe)")
    fig.tight_layout()
    fig.savefig("docs/tests/img/tr16_ibs.png", dpi=120)
    print("chart -> docs/tests/img/tr16_ibs.png")


if __name__ == "__main__":
    main()
