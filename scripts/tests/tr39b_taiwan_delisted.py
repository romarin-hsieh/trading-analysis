"""TR-39b -- Taiwan panel, survivorship-patched (the b1 gate for TR-39's candidates).

PRE-REGISTERED while the delisted drip is still running. TR-39 found four joint
|t|>=2 candidates (mom122, max5, avol, logdv) on a CURRENTLY-LISTED universe, with
the bias direction flipped to INFLATING (dead lottery/momentum losers absent). This
TR re-runs the exact panel with the official TWSE delisted cohort patched in.

PATCH: 72 four-digit commons delisted 2015+ (TWSE OpenAPI suspendListing list),
FinMind per-stock histories, EACH SERIES TRUNCATED AT ITS OFFICIAL DELISTING DATE
(codes get re-used/bridged -- 2311 shows post-delist rows; the manifest
data/finmind_tw/delisted.csv drives the cut).

KEY PRE-REGISTERED DESIGN CALL (made BEFORE seeing patched data): valuation data
(PER/PBR) for delisted names is structurally sparser at FinMind. Requiring all SIX
characteristics would silently drop exactly the names the patch adds -- survivorship
through the back door. Therefore:
  PRIMARY  = FIVE-characteristic panel (mom122, str1m, max5, avol, logdv -- all
             price/volume-derived, available for every name). bp was not a candidate
             anyway (t=1.87).
  SECONDARY= six-characteristic panel (reported; known re-exclusion caveat).
The unpatched baseline is re-run under the SAME 5-char spec so the delta compares
like with like.

F0 DECLARATION (pre-committed)
  CAL : a) DV-weighted panel market vs TAIEX corr >= 0.90 (TR-39 v2 instrument);
        b) 2330 FinMind-vs-Yahoo corr >= 0.95;
        c) joint 5-char coverage >= 600/mo;
        d) >= 50 of the manifest names enter the 5-char panel in >= 1 evaluation
           month (the patch actually bites). Fail any -> STOP.
  C1  : per-candidate verdict on the PATCHED 5-char panel:
          |t| >= 2  -> CONFIRMED-CANDIDATE (proceeds to b2 cost gate)
          |t| <  2  -> SURVIVORSHIP-ARTIFACT (retired)
        bp is NOT promotable regardless of its patched t (not pre-registered; a
        crossing would need fresh-sample confirmation).
  C2  : delta table -- unpatched vs patched slope/t under the identical 5-char spec;
        delisted-cohort diagnostics (entry-month characteristic ranks: were the dead
        names high-MAX/high-avol as hypothesized?).
  C3  : secondary 6-char panel, reported.
  anti-HARKing : verdict rules and the primary-spec switch fixed before the patched
        data existed; trials +0 (same family, corrected universe).

Run: uv run python scripts/tests/tr39b_taiwan_delisted.py   (after the patch drip)
"""

from __future__ import annotations

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
from tr39_taiwan_panel import DATA, START, load_panels  # noqa: E402

CANDIDATES = ("mom122", "max5", "avol", "logdv")
FIVE = ("mom122", "str1m", "max5", "avol", "logdv")


def build_chars(px, dv, pbr, include_bp: bool):
    px = px.where(px > 0)
    zero_share = (px.pct_change() == 0).mean()
    px = px.loc[:, zero_share[zero_share < 0.4].index]
    dv = dv[px.columns].where(dv[px.columns] > 0)
    me_full = px.resample("ME").last()
    ret_full = me_full.pct_change().replace([np.inf, -np.inf], np.nan)
    me = me_full.loc[START:]
    ret_m = ret_full.loc[START:]
    fwd = ret_full.shift(-1).loc[START:]
    daily_ret = px.pct_change()
    chars = {
        "mom122": (me_full.shift(2) / me_full.shift(12) - 1).loc[START:],
        "str1m": ret_m,
        "max5": daily_ret.rolling(21).apply(lambda x: np.sort(x)[-5:].mean(), raw=True)
        .resample("ME").last().loc[START:].reindex(me.index),
        "avol": np.log((dv.rolling(21).mean() / dv.rolling(252).mean()).where(lambda x: x > 0))
        .resample("ME").last().loc[START:].reindex(me.index),
        "logdv": np.log(dv.rolling(252).median().where(lambda x: x > 0))
        .resample("ME").last().loc[START:].reindex(me.index),
    }
    if include_bp:
        pbr = pbr[px.columns]
        chars["bp"] = (1.0 / pbr.where(pbr > 0)).resample("ME").last().loc[START:].reindex(me.index)
    return {k: rank_std(v) for k, v in chars.items()}, fwd, ret_m, dv, me


def run_panel(chars, fwd):
    sl = fm_slopes(chars, fwd, min_n=300)
    return {k: nw_mean_t(sl[k]) for k in sl.columns}, sl


def main():
    man = pd.read_csv(DATA / "delisted.csv", dtype={"stock_id": str})
    print("=" * 100)
    print(f"TR-39b  TAIWAN PANEL, SURVIVORSHIP-PATCHED -- {len(man)} delisted names, "
          f"truncated at official delisting dates")
    print("=" * 100)

    px, dv, pbr, per = load_panels()
    # truncate every manifest name at its official delisting date
    present = [s for s in man["stock_id"] if s in px.columns]
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px.columns:
            px.loc[px.index > dd, sid] = np.nan
            dv.loc[dv.index > dd, sid] = np.nan
            if sid in pbr.columns:
                pbr.loc[pbr.index > dd, sid] = np.nan
    print(f"patched: {len(present)}/{len(man)} manifest names present in the loaded panel")

    # ---- PRIMARY: 5-char patched panel ----
    chars_p, fwd_p, ret_p, dv_p, me_p = build_chars(px, dv, pbr, include_bp=False)

    # CAL a: DV-weighted market vs TAIEX (same instrument as TR-39 v2)
    import json as _json
    import os
    import urllib.parse
    import urllib.request
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
    q = {"dataset": "TaiwanStockPrice", "data_id": "TAIEX", "start_date": "2014-01-01"}
    tok = os.environ.get("FINMIND_TOKEN", "").strip()
    if tok:
        q["token"] = tok
    r = _json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://api.finmindtrade.com/api/v4/data?" + urllib.parse.urlencode(q),
        headers={"User-Agent": "trading-analysis research"}), timeout=60).read().decode())
    d = pd.DataFrame(r["data"])
    taiex = pd.Series(d["close"].to_numpy(), index=pd.to_datetime(d["date"])) \
        .resample("ME").last().pct_change()
    dvw = dv_p.rolling(252).median().resample("ME").last().loc[START:] \
        .reindex(columns=ret_p.columns).shift(1)
    w = dvw.where(ret_p.notna())
    mkt = (w * ret_p).sum(axis=1) / w.sum(axis=1)
    both = pd.concat([mkt.rename("m"), taiex.rename("t")], axis=1).dropna().loc[START:]
    cal_a = float(both.corr().iloc[0, 1])

    import yfinance as yf
    y2330 = yf.download("2330.TW", start="2014-06-01", auto_adjust=False, progress=False)["Close"]
    y2330 = y2330.iloc[:, 0] if isinstance(y2330, pd.DataFrame) else y2330
    ym = y2330.resample("ME").last().pct_change()
    fmm = me_p["2330"].pct_change()
    bothb = pd.concat([fmm.rename("f"), ym.rename("y")], axis=1).dropna()
    cal_b = float(bothb.corr().iloc[0, 1])

    cov = pd.DataFrame({k: v.notna().sum(axis=1) for k, v in chars_p.items()}).min(axis=1)
    cov = cov.loc[START:cov.index[-2]]
    joint_ok = pd.concat([v.notna() for v in chars_p.values()]).groupby(level=0).min()
    dead_in = [s for s in present if s in chars_p["mom122"].columns
               and pd.DataFrame({k: chars_p[k][s] for k in chars_p}).dropna().shape[0] >= 1]
    ok_a, ok_b, ok_c, ok_d = cal_a >= 0.90, cal_b >= 0.95, bool((cov >= 600).all()), len(dead_in) >= 50
    print(f"CAL a: DVW market vs TAIEX corr {cal_a:+.3f} (>=0.90) -> {'PASS' if ok_a else 'FAIL'}")
    print(f"CAL b: 2330 cross-vendor corr {cal_b:+.3f} (>=0.95) -> {'PASS' if ok_b else 'FAIL'}")
    print(f"CAL c: min 5-char coverage {int(cov.min())}/mo (>=600) -> {'PASS' if ok_c else 'FAIL'}")
    print(f"CAL d: {len(dead_in)}/{len(man)} delisted names enter the panel (>=50) -> "
          f"{'PASS' if ok_d else 'FAIL'}")
    if not (ok_a and ok_b and ok_c and ok_d):
        print("VERDICT: INVALID-TEST -- patch fidelity failed.")
        return

    stats_p, sl_p = run_panel(chars_p, fwd_p)

    # ---- unpatched baseline under the IDENTICAL 5-char spec ----
    px0, dv0, pbr0, _ = load_panels()
    drop = [s for s in present if s in px0.columns]
    px0 = px0.drop(columns=drop)
    dv0 = dv0.drop(columns=drop)
    pbr0 = pbr0.drop(columns=[c for c in drop if c in pbr0.columns])
    chars_0, fwd_0, *_ = build_chars(px0, dv0, pbr0, include_bp=False)
    stats_0, _ = run_panel(chars_0, fwd_0)

    print("-" * 100)
    print("C1/C2 per-candidate verdicts (PRIMARY 5-char panel):")
    confirmed, artifacts = [], []
    for k in FIVE:
        m0, t0 = stats_0[k]
        m1, t1 = stats_p[k]
        if k in CANDIDATES:
            status = "CONFIRMED-CANDIDATE" if abs(t1) >= 2 else "SURVIVORSHIP-ARTIFACT"
            (confirmed if abs(t1) >= 2 else artifacts).append(k)
        else:
            status = "(not a candidate)"
        print(f"  {k:7s}: unpatched {m0*1e4:+7.1f} (t={t0:+.2f}) -> patched "
              f"{m1*1e4:+7.1f} (t={t1:+.2f})   {status}")

    # delisted-cohort diagnostics: where did the dead names sit at entry?
    print("C2 delisted-cohort entry ranks (0=lowest, 1=highest; hypothesis: high max5/avol):")
    for k in FIVE:
        ranks = []
        for s in dead_in:
            col = chars_p[k][s].dropna()
            if len(col):
                ranks.append(float(col.mean() + 0.5))
        if ranks:
            print(f"  {k:7s}: mean rank {np.mean(ranks):.2f} (n={len(ranks)})")

    # ---- C3 secondary 6-char ----
    px6, dv6, pbr6, _ = load_panels()
    for _, row in man.iterrows():
        sid, dd = row["stock_id"], pd.Timestamp(row["delist_date"])
        if sid in px6.columns:
            px6.loc[px6.index > dd, sid] = np.nan
            dv6.loc[dv6.index > dd, sid] = np.nan
            if sid in pbr6.columns:
                pbr6.loc[pbr6.index > dd, sid] = np.nan
    chars_6, fwd_6, *_ = build_chars(px6, dv6, pbr6, include_bp=True)
    stats_6, _ = run_panel(chars_6, fwd_6)
    print("C3 secondary 6-char panel (bp re-exclusion caveat):")
    for k in ("mom122", "max5", "avol", "logdv", "bp"):
        m, t = stats_6[k]
        print(f"  {k:7s}: {m*1e4:+7.1f} bps/mo (t={t:+.2f})")

    print("-" * 100)
    if confirmed and not artifacts:
        v = f"ALL FOUR CONFIRMED -- {', '.join(confirmed)} survive the survivorship patch; b2 cost gate is next."
    elif confirmed:
        v = (f"SPLIT -- confirmed: {', '.join(confirmed)}; artifacts: {', '.join(artifacts)}. "
             f"Confirmed set proceeds to b2.")
    else:
        v = "ALL ARTIFACTS -- the Taiwan light was survivorship glare; candidates retired."
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ks = list(FIVE)
    x = np.arange(len(ks))
    t0s = [stats_0[k][1] for k in ks]
    t1s = [stats_p[k][1] for k in ks]
    ax.bar(x - 0.2, t0s, 0.4, label="unpatched (listed-only)", color="#90a4ae", alpha=0.9)
    ax.bar(x + 0.2, t1s, 0.4, label="patched (+delisted, truncated)", color="#1565c0", alpha=0.9)
    ax.axhline(2, color="#c62828", ls="--", lw=1)
    ax.axhline(-2, color="#c62828", ls="--", lw=1)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(ks)
    ax.set_ylabel("joint FM NW t")
    ax.set_title("TR-39b: do the Taiwan candidates survive the survivorship patch?", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    outp = Path("docs/tests/img/tr39b_taiwan_delisted.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
