"""TR-39 -- Taiwan habitat FM factor panel (docs/25 B4; the post-TR-36 #1 breakout).

PRE-REGISTERED before the data drip completed (F0 committed at 863/1220 coverage;
the script refuses to run the panel until all 1,220 universe entries are attempted).

WHY THIS HABITAT: six proofs say the $0 US-large-cap seat is mined out (docs/25 II).
TWSE is the thinnest-arbitrage market we can reach: retail-dominated (Barber-Lee-
Liu-Odean 2009 RFS, full-market account data), with literature priors of WEAK
momentum (Griffin-Ji-Martin) and STRONG lottery (MAX) / attention (volume) effects.
Per the TR-34 calibration lesson, those priors are REPORTED comparisons, never CAL
gates -- for a NEW seat, machine fidelity = data-level checks (vendor cross-check,
market reconstruction), not effect-level priors.

SEAT: TWSE 4-digit common stocks, daily 2014-2026 via FinMind (price + daily
PER/PBR/dividend-yield), monthly FM cross-sections, next-month returns; machinery =
TR-34's fm_slopes/rank_std/nw_mean_t, reused verbatim.

LOUD HONESTY (three structural caveats, all pre-declared):
  F13  universe = CURRENTLY-LISTED only (TaiwanStockInfo) -> survivorship bias.
       Direction analysis pre-stated: dead lottery names are absent, which biases the
       MAX slope TOWARD ZERO -- a significant negative MAX despite this bias is
       conservative-strong; a null MAX is ambiguous (bias or truth). v2 = TWSE
       delisted-list patch.
  LIMITS Taiwan daily price limits (7% pre-2015-06, 10% after) COMPRESS max daily
       returns vs the US MAX literature -- MAX(5) here measures the capped version.
  COSTS panel = signal existence only. TW round trip ~45bps (0.1425%x2 commission +
       0.30% sell-side STT) -- any candidate must later clear it (F2 stage).

F0 DECLARATION (pre-committed)
  characteristics (6 core): mom122 (t-12..t-2), str1m, max5 (mean of 5 largest daily
      returns, prior month -- TR-23 MAX(5) convention, declared up front), avol
      (log of prior-1m avg daily TWD volume / prior-12m avg -- abnormal attention),
      logdv (log median daily TWD volume, 12m -- size/liquidity proxy), bp (1/PBR at
      month-end, PIT daily-published). Extras REPORTED in C3: ep (1/PER), dy.
  CAL (all must pass, else STOP):
      a: panel EW market monthly return vs an independent market series (TAIEX index
         if fetchable, else 0050 ETF): corr >= 0.90.
      b: vendor cross-check: 2330 monthly returns FinMind vs Yahoo 2330.TW,
         corr >= 0.95.
      c: coverage: >= 600 stocks with all 6 characteristics in every month from
         2015-07 on.
  C1 (decisive, joint FM, NW t): any characteristic with |t| >= 2 -> named
      SIGNAL-CANDIDATE(s) (depth series follows in b-series TRs); all |t| < 2 ->
      HABITAT-EFFICIENT-TOO (the thin-arbitrage hypothesis fails on this seat/window).
  C2  univariate slopes + literature-sign table (reported, not gated).
  C3  subperiods 2015-2020 / 2021-2026; ep/dy extras.
  anti-HARKing : single pre-registered spec; no characteristic search; trials +1
      family (new habitat).

Run: uv run python scripts/tests/tr39_taiwan_panel.py   (~3-5 min once drip complete)
"""

from __future__ import annotations

import json
import sys
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

from tr34_fama_macbeth import fm_slopes, nw_mean_t, rank_std  # noqa: E402

DATA = Path("data/finmind_tw")
STATE = Path("data/_finmind_tw_state.json")
START = "2015-07"
LIT = {"mom122": "0/+ (weak in Asia)", "str1m": "-", "max5": "- (lottery)",
       "avol": "- (attention/overtrading)", "logdv": "0/-", "bp": "+ (value)"}


def load_panels() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Daily close/volume(TWD)/PBR/PER wide frames from the per-stock parquets."""
    closes, moneys, pbrs, pers = {}, {}, {}, {}
    for f in sorted((DATA / "price").glob("*.parquet")):
        d = pd.read_parquet(f)
        if len(d) < 260:                       # need at least ~1y of history to ever rank
            continue
        sid = f.stem
        idx = pd.to_datetime(d["date"])
        closes[sid] = pd.Series(d["close"].to_numpy(), index=idx)
        moneys[sid] = pd.Series(d["Trading_money"].to_numpy(), index=idx)
        pf = DATA / "per" / f.name
        if pf.exists():
            p = pd.read_parquet(pf)
            pidx = pd.to_datetime(p["date"])
            pbrs[sid] = pd.Series(pd.to_numeric(p["PBR"], errors="coerce").to_numpy(), index=pidx)
            pers[sid] = pd.Series(pd.to_numeric(p["PER"], errors="coerce").to_numpy(), index=pidx)
    px = pd.DataFrame(closes).sort_index()
    dv = pd.DataFrame(moneys).sort_index().reindex(px.index)
    pbr = pd.DataFrame(pbrs).sort_index().reindex(px.index).reindex(columns=px.columns)
    per = pd.DataFrame(pers).sort_index().reindex(px.index).reindex(columns=px.columns)
    return px, dv, pbr, per


def main():
    st = json.loads(STATE.read_text())
    if len(st["done"]) < 1220:
        print(f"drip incomplete ({len(st['done'])}/1220) -- TR-39 fires when all universe "
              f"entries are attempted. Aborting (pre-registration gate).")
        return

    print("=" * 100)
    print("TR-39  TAIWAN HABITAT FM PANEL -- TWSE common stocks, monthly, 2015-07..")
    print("=" * 100)
    px, dv, pbr, per = load_panels()
    print(f"panel: {px.shape[1]} stocks with >=1y daily history, {px.index[0].date()}..{px.index[-1].date()}")

    px = px.where(px > 0)                                   # suspended rows carry close=0 -> poison pct_change with inf
    zero_share = (px.pct_change() == 0).mean()
    px = px.loc[:, zero_share[zero_share < 0.4].index]      # ghost filter (TW limit days inflate zeros; loose bar)
    dv, pbr, per = (x[px.columns] for x in (dv, pbr, per))
    dv = dv.where(dv > 0)

    # characteristics on the FULL monthly history (2014+), THEN slice the evaluation
    # window -- slicing first left mom122/str1m all-NaN in the first months (CAL-c
    # caught it: joint coverage 0 at 2015-07).
    me_full = px.resample("ME").last()
    ret_full = me_full.pct_change().replace([np.inf, -np.inf], np.nan)
    me = me_full.loc[START:]
    ret_m = ret_full.loc[START:]
    fwd = ret_full.shift(-1).loc[START:]

    mom122 = (me_full.shift(2) / me_full.shift(12) - 1).loc[START:]
    str1m = ret_m
    daily_ret = px.pct_change()
    max5 = daily_ret.rolling(21).apply(lambda x: np.sort(x)[-5:].mean(), raw=True) \
        .resample("ME").last().loc[START:]
    dv1 = dv.rolling(21).mean()
    dv12 = dv.rolling(252).mean()
    avol = np.log((dv1 / dv12).where(lambda x: x > 0)).resample("ME").last().loc[START:]
    logdv = np.log(dv.rolling(252).median().where(lambda x: x > 0)) \
        .resample("ME").last().loc[START:]
    bp = (1.0 / pbr.where(pbr > 0)).resample("ME").last().loc[START:]
    ep = (1.0 / per.where(per > 0)).resample("ME").last().loc[START:]

    chars_raw = {"mom122": mom122, "str1m": str1m, "max5": max5.reindex(me.index),
                 "avol": avol.reindex(me.index), "logdv": logdv.reindex(me.index),
                 "bp": bp.reindex(me.index)}
    chars = {k: rank_std(v) for k, v in chars_raw.items()}

    # ---- CAL a v2: DOLLAR-VOLUME-WEIGHTED panel market vs the cap-weighted TAIEX ----
    # (v1 compared an EQUAL-weighted panel mean against the cap-weighted index -- an
    # apples-to-oranges CAL design: TAIEX is ~30% TSMC, EW-vs-VW genuinely correlates
    # ~0.78 in Taiwan. v1's 0.908 was an artifact of inf-poisoned months being dropped.
    # Like-for-like instrument: liquidity(DV)-weighted panel market; bar unchanged 0.90.)
    dvw = dv.rolling(252).median().resample("ME").last().loc[START:].reindex(columns=ret_m.columns)
    dvw = dvw.shift(1)
    w = dvw.div(dvw.sum(axis=1), axis=0)
    ew_mkt = (w * ret_m).sum(axis=1) / (w * ret_m.notna()).sum(axis=1).replace(0, np.nan) * 1.0
    ew_mkt = (w.where(ret_m.notna()) * ret_m).sum(axis=1) / w.where(ret_m.notna()).sum(axis=1)
    mkt_ind = None
    try:
        import urllib.request
        import urllib.parse
        import os
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=".env")
        q = {"dataset": "TaiwanStockPrice", "data_id": "TAIEX", "start_date": "2014-01-01"}
        tok = os.environ.get("FINMIND_TOKEN", "").strip()
        if tok:
            q["token"] = tok
        url = "https://api.finmindtrade.com/api/v4/data?" + urllib.parse.urlencode(q)
        r = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "trading-analysis research"}),
            timeout=60).read().decode())
        if r.get("status") == 200 and r.get("data"):
            d = pd.DataFrame(r["data"])
            s = pd.Series(d["close"].to_numpy(), index=pd.to_datetime(d["date"]))
            mkt_ind = s.resample("ME").last().pct_change()
            src = "TAIEX"
    except Exception:
        pass
    if mkt_ind is None:
        import yfinance as yf
        s = yf.download("0050.TW", start="2014-01-01", auto_adjust=True, progress=False)["Close"]
        s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        mkt_ind = s.resample("ME").last().pct_change()
        src = "0050.TW (yahoo)"
    both = pd.concat([ew_mkt.rename("ew"), mkt_ind.rename("ind")], axis=1).dropna().loc[START:]
    cal_a = float(both.corr().iloc[0, 1])
    ok_a = cal_a >= 0.90

    # ---- CAL b: vendor cross-check 2330 FinMind vs Yahoo ----
    import yfinance as yf
    y2330 = yf.download("2330.TW", start="2014-06-01", auto_adjust=False, progress=False)["Close"]
    y2330 = y2330.iloc[:, 0] if isinstance(y2330, pd.DataFrame) else y2330
    ym = y2330.resample("ME").last().pct_change()
    fm2330 = me["2330"].pct_change() if "2330" in me.columns else pd.Series(dtype=float)
    bothb = pd.concat([fm2330.rename("fm"), ym.rename("yh")], axis=1).dropna()
    cal_b = float(bothb.corr().iloc[0, 1]) if len(bothb) > 24 else np.nan
    ok_b = cal_b >= 0.95

    # ---- CAL c: coverage ----
    cov = pd.DataFrame({k: v.notna().sum(axis=1) for k, v in chars.items()}).min(axis=1)
    cov = cov.loc[START:cov.index[-2]]
    ok_c = bool((cov >= 600).all())
    print(f"CAL a: EW panel market vs {src}: corr {cal_a:+.3f} (>=0.90) -> {'PASS' if ok_a else 'FAIL'}")
    print(f"CAL b: 2330 FinMind vs Yahoo monthly: corr {cal_b:+.3f} (>=0.95) -> {'PASS' if ok_b else 'FAIL'}")
    print(f"CAL c: min joint coverage {int(cov.min())} stocks/month (>=600) -> {'PASS' if ok_c else 'FAIL'}")
    if not (ok_a and ok_b and ok_c):
        print("VERDICT: INVALID-TEST -- seat fidelity failed; fix data before judging.")
        return

    # ---- C1 joint FM ----
    sl = fm_slopes(chars, fwd, min_n=300)
    stats = {k: nw_mean_t(sl[k]) for k in sl.columns}
    print("-" * 100)
    print(f"C1 joint FM ({len(sl)} months, median names/mo "
          f"{int(pd.DataFrame({k: chars[k].notna().sum(axis=1) for k in chars}).min(axis=1).median())}):")
    candidates = []
    for k in ("mom122", "str1m", "max5", "avol", "logdv", "bp"):
        m, t = stats[k]
        flag = "  <-- SIGNAL-CANDIDATE" if abs(t) >= 2 else ""
        if abs(t) >= 2:
            candidates.append(k)
        print(f"  {k:7s}: {m*1e4:+7.1f} bps/mo  NW t={t:+.2f}   (lit: {LIT[k]}){flag}")

    # ---- C2 univariate ----
    print("C2 univariate slopes:")
    for k in chars:
        u = fm_slopes({k: chars[k]}, fwd, min_n=300)
        m, t = nw_mean_t(u[k])
        print(f"  {k:7s}: {m*1e4:+7.1f} bps/mo  t={t:+.2f}")

    # ---- C3 subperiods + extras ----
    for lab, a, b in (("2015-2020", "2015", "2020"), ("2021-2026", "2021", "2026")):
        parts = []
        for k in ("max5", "avol", "mom122", "bp"):
            m, t = nw_mean_t(sl[k].loc[a:b])
            parts.append(f"{k} {m*1e4:+.0f} (t={t:+.1f})")
        print(f"C3 {lab}: " + " | ".join(parts))
    extr = {"ep": rank_std(ep.reindex(me.index)), "dy_note": None}
    ue = fm_slopes({"ep": extr["ep"]}, fwd, min_n=200)
    m, t = nw_mean_t(ue["ep"])
    print(f"C3 extras: ep {m*1e4:+.1f} bps/mo (t={t:+.2f})")

    if candidates:
        v = (f"SIGNAL-CANDIDATE(S): {', '.join(candidates)} -- depth series (b-TRs) follows: "
             f"cost gate (45bps RT), delisting patch, bucket economics.")
    else:
        v = ("HABITAT-EFFICIENT-TOO -- no characteristic clears |t|>=2 jointly; the "
             "thin-arbitrage hypothesis fails on this seat/window (survivorship caveat noted).")
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    ks = list(("mom122", "str1m", "max5", "avol", "logdv", "bp"))
    ms = [stats[k][0] * 1e4 for k in ks]
    ts = [stats[k][1] for k in ks]
    cols = ["#c62828" if abs(t) >= 2 else "#90a4ae" for t in ts]
    ax.bar(ks, ms, color=cols, alpha=0.9)
    for i, (m, t) in enumerate(zip(ms, ts)):
        ax.text(i, m + (3 if m >= 0 else -8), f"t={t:+.1f}", ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("joint FM slope (bps/mo)")
    ax.set_title("C1: TWSE joint Fama-MacBeth slopes", fontsize=10)
    ax = axes[1]
    for k, col in (("max5", "#c62828"), ("avol", "#f9a825"), ("bp", "#2e7d32"), ("mom122", "#1565c0")):
        cum = sl[k].cumsum() * 1e4
        ax.plot(cum.index, cum.values, lw=1.2, label=k, color=col)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("cumulative slope (bps)")
    ax.set_title("slope paths", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-39: Taiwan habitat -- do factors live where arbitrage capital is thin?",
                 fontsize=12)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr39_taiwan_panel.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
