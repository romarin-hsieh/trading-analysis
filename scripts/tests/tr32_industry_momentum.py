"""TR-32 -- Moskowitz-Grinblatt (1999) industry momentum on the KF49 native-adjacent seat.

Reopen basis: docs/22 queue, information cost already paid -- KF industry portfolios
ingested for TR-21b; FF5+UMD monthly loader in hand (TR-20/24/25). M-G (JF 1999,
"Do Industries Explain Momentum?") claim: buying the past-6-month strongest industries
and shorting the weakest earns ~+0.43%/mo, is STRONGEST WITHOUT skipping the most
recent month (their fingerprint vs stock momentum), and absorbs most of individual-
stock momentum. Our cross-sectional ledger so far: broad stock momentum dead
(docs/09, ICIR~0), XS top-K momentum = beta (TR-11); M-G is the literature's
"momentum's true home is the industry layer" counterclaim.

MACHINE FIDELITY (T1) -- M-G construction transcribed before coding:
  - rank industries on cumulative J=6-month return INCLUDING the most recent month
    (no skip -- M-G emphasize industry momentum is strongest unskipped);
  - hold K=6 months, overlapping Jegadeesh-Titman portfolios (strategy return at t
    = average over the 6 cohorts formed at t-1..t-6);
  - long top 15% / short bottom 15%, equal-weight across selected industries,
    value-weighted within (KF portfolios are VW) -> 49 industries: top-7/bottom-7
    (M-G native: top-3/bottom-3 of their 20 self-built industries);
  - seat differences declared: KF49 classification (not M-G's 20), 1970-01 start
    (KF49 coverage; M-G 1963-07), monthly VW returns from Ken French library.

F0 DECLARATION (pre-committed)
  claim         : industry momentum 6/6 L-S is significantly positive, with the
                no-skip > skip fingerprint, and survives FF5+UMD spanning.
  seat          : KF49 VW industry portfolios, monthly, 1970-01..latest; L-S signal-
                level verdict (industry baskets were not directly tradable pre-1998;
                costs reported descriptively at 10bps one-way on turnover).
  PRE-COMMITTED CHECKS
    CAL  : overlap window 1970-01..1995-07 (M-G in-sample tail): 6/6 L-S mean monthly
           return in [0.15%, 0.85%] (anchor +0.43%) AND t >= 1.5. Fail -> STOP
           (NO-REPLICATION on this seat).
    C1   : full-sample 1970-2026 mean and Newey-West t (6 lags, overlapping K).
    C2   : post-publication decay (1999-08..): mean, NW t; McLean-Pontiff framing.
    C3   : spanning: L-S regressed on FF5+UMD, full sample AND post-publication;
           report alpha and alpha-t (HAC).
    C4   : fingerprint diagnostic: no-skip vs skip-1-month ranking -- M-G's signature
           is no-skip >= skip; report both (diagnostic, not a verdict input).
  VERDICT RULE (pre-committed):
    CAL fail                          -> NO-REPLICATION (this seat)
    CAL pass & C2 t < 1.0             -> REPLICATED-BUT-DEAD (post-publication decay)
    CAL pass & C2 t >= 2 & C3 post-pub alpha-t < 2 -> REPLICATED-BUT-SPANNED (UMD in
                                         industry clothes)
    CAL pass & C2 t >= 2 & C3 post-pub alpha-t >= 2 -> ALIVE (cross-sectional survivor)
    (1 <= C2 t < 2: report as MARGINAL-DECAY, verdict = REPLICATED-BUT-DEAD class with
     the t stated -- decay is the story either way.)
  anti-HARKing : single pre-registered configuration (J=6/K=6/15%); skip variant is a
               fidelity fingerprint, not a candidate; trials +1 family.

Run: uv run python scripts/tests/tr32_industry_momentum.py   (~1 min)
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
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
from tr20_ff5_attribution import load_ff5_umd_monthly  # noqa: E402

START = "1970-01"
PUB = "1999-08"            # M-G published JF August 1999
J, K = 6, 6
FRAC = 0.15                # top/bottom 15% -> 7 of 49
COST_1W = 0.0010           # 10bps one-way, descriptive only
CACHE = Path("data/kf49_monthly.parquet")


def load_kf49_monthly() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    url = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
           "49_Industry_Portfolios_CSV.zip")
    raw = urllib.request.urlopen(url, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
    lines = text.splitlines()
    hdr = next(i for i, ln in enumerate(lines)
               if ln.count(",") >= 48 and not ln.strip()[:6].isdigit())
    cols = [c.strip() for c in lines[hdr].split(",")][1:]
    data = []
    for ln in lines[hdr + 1:]:
        tok = ln.strip().split(",")[0].strip()
        if len(tok) == 6 and tok.isdigit():
            data.append(ln)
        elif data:
            break                                   # end of first (VW monthly) table
    df = pd.read_csv(io.StringIO("\n".join(data)), header=None)
    df.columns = ["date", *cols]
    df.index = pd.PeriodIndex(df["date"].astype(str), freq="M").to_timestamp("M")
    df = df.drop(columns="date").astype(float) / 100.0
    df = df.where(df > -0.99)                       # -99.99 = missing
    df.to_parquet(CACHE)
    return df


def ls_stream(r: pd.DataFrame, skip: int = 0) -> tuple[pd.Series, pd.Series]:
    """J/K overlapping industry momentum L-S returns and monthly turnover."""
    n_pick = max(1, round(r.shape[1] * FRAC))
    # formation signal at month t: cumulative return over t-J-skip+1 .. t-skip
    cum = (1 + r).rolling(J).apply(np.prod, raw=True) - 1
    sig = cum.shift(skip)
    longs, shorts = {}, {}
    for t in sig.index:
        s = sig.loc[t].dropna()
        if len(s) < 30:                              # need most industries present
            continue
        ranked = s.sort_values()
        longs[t] = list(ranked.index[-n_pick:])
        shorts[t] = list(ranked.index[:n_pick])
    ls, tos = {}, {}
    dates = r.index
    prev_w = None
    for i, t in enumerate(dates):
        # cohorts formed at t-1..t-K (signal known at end of formation month)
        cohorts = [dates[i - k] for k in range(1, K + 1) if i - k >= 0]
        cohorts = [d for d in cohorts if d in longs]
        if len(cohorts) < K:
            continue
        w = pd.Series(0.0, index=r.columns)
        for d in cohorts:
            w[longs[d]] += 1.0 / (K * len(longs[d]))
            w[shorts[d]] -= 1.0 / (K * len(shorts[d]))
        ret = (w * r.loc[t]).sum()
        if not np.isfinite(ret):
            ret = (w * r.loc[t].fillna(0.0)).sum()
        ls[t] = ret
        if prev_w is not None:
            tos[t] = (w - prev_w).abs().sum() / 2
        prev_w = w
    return pd.Series(ls), pd.Series(tos)


def nw_t(x: pd.Series, lags: int = 6) -> tuple[float, float]:
    x = x.dropna()
    res = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC",
                                                    cov_kwds={"maxlags": lags})
    return float(res.params[0]), float(res.tvalues[0])


def spanning(ls: pd.Series, ff: pd.DataFrame) -> tuple[float, float]:
    y = ls.copy()
    y.index = y.index.to_period("M")
    df = pd.concat([y.rename("ls"), ff], axis=1).dropna()
    X = sm.add_constant(df.drop(columns="ls"))
    res = sm.OLS(df["ls"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    return float(res.params["const"]), float(res.tvalues["const"])


def main():
    r = load_kf49_monthly().loc[START:]
    print("=" * 100)
    print(f"TR-32  MOSKOWITZ-GRINBLATT INDUSTRY MOMENTUM -- KF49 VW monthly, "
          f"{r.index[0]:%Y-%m}..{r.index[-1]:%Y-%m}, J={J}/K={K}, top/bottom {FRAC:.0%}")
    print("=" * 100)

    ls, to = ls_stream(r, skip=0)
    ls_skip, _ = ls_stream(r, skip=1)

    # CAL: M-G in-sample overlap
    cal_w = ls.loc[:"1995-07"]
    m_cal, t_cal = nw_t(cal_w)
    cal = (0.0015 <= m_cal <= 0.0085) and (t_cal >= 1.5)
    print(f"CAL 1970-01..1995-07: mean {m_cal*100:+.3f}%/mo (anchor +0.43%, band "
          f"[0.15%,0.85%]), NW t={t_cal:+.2f} (rule >=1.5) -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: NO-REPLICATION -- M-G industry momentum does not reproduce on this seat.")
        return

    # C1 full sample
    m_full, t_full = nw_t(ls)
    print(f"C1 full 1970-2026: mean {m_full*100:+.3f}%/mo, NW t={t_full:+.2f} | "
          f"avg monthly turnover {to.mean():.0%} -> net at 10bps 1-way: "
          f"{(m_full - 2*COST_1W*to.mean())*100:+.3f}%/mo (descriptive)")

    # C2 post-publication
    post = ls.loc[PUB:]
    m_post, t_post = nw_t(post)
    decay = 1 - m_post / m_cal if m_cal != 0 else np.nan
    print(f"C2 post-publication {PUB}..2026: mean {m_post*100:+.3f}%/mo, NW t={t_post:+.2f} "
          f"| decay vs in-sample {decay:+.0%} (McLean-Pontiff avg -58%)")

    # C3 spanning
    ff = load_ff5_umd_monthly(start="1970-01-01")
    ff = ff.drop(columns=[c for c in ("RF",) if c in ff.columns])
    a_full, at_full = spanning(ls, ff)
    a_post, at_post = spanning(post, ff)
    print(f"C3 spanning FF5+UMD: full alpha {a_full*100:+.3f}%/mo (t={at_full:+.2f}); "
          f"post-pub alpha {a_post*100:+.3f}%/mo (t={at_post:+.2f})")

    # C4 fingerprint
    m_ns, _ = nw_t(ls.loc[:"1995-07"])
    m_sk, _ = nw_t(ls_skip.loc[:"1995-07"])
    print(f"C4 fingerprint (in-sample): no-skip {m_ns*100:+.3f}% vs skip-1m {m_sk*100:+.3f}% "
          f"-> {'matches M-G (no-skip >= skip)' if m_ns >= m_sk else 'does NOT match M-G'}")

    if t_post >= 2 and at_post >= 2:
        v = "ALIVE -- industry momentum survives publication and FF5+UMD spanning on this seat."
    elif t_post >= 2:
        v = ("REPLICATED-BUT-SPANNED -- alive post-publication but absorbed by FF5+UMD: "
             "UMD in industry clothes.")
    else:
        v = (f"REPLICATED-BUT-DEAD -- in-sample replication passes, post-publication "
             f"t={t_post:+.2f} (<2): the McLean-Pontiff decay ate it.")
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    cum = (1 + ls).cumprod()
    ax.plot(cum.index, cum.values, color="#1565c0", lw=1.2, label="6/6 industry momentum L-S")
    ax.axvline(pd.Timestamp("1995-07-31"), color="#757575", ls=":", lw=1)
    ax.axvline(pd.Timestamp("1999-08-31"), color="#c62828", ls="--", lw=1.2,
               label="M-G published (1999-08)")
    ax.set_yscale("log")
    ax.set_title("cumulative L-S (log scale): before vs after publication", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    win = [("in-sample\n1970-1995", m_cal, t_cal), ("full\n1970-2026", m_full, t_full),
           ("post-pub\n1999-2026", m_post, t_post)]
    xs = [w[0] for w in win]
    ax.bar(xs, [w[1] * 100 for w in win],
           color=["#2e7d32" if w[2] >= 2 else "#f9a825" if w[2] >= 1 else "#c62828" for w in win],
           alpha=0.9)
    for i, w in enumerate(win):
        ax.text(i, w[1] * 100 + 0.01, f"t={w[2]:+.2f}", ha="center", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(0.43, color="#757575", ls=":", lw=1, label="M-G anchor +0.43%")
    ax.set_ylabel("mean L-S return (%/mo)")
    ax.set_title(f"window comparison | post-pub FF5+UMD alpha-t {at_post:+.2f}", fontsize=10)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-32: Moskowitz-Grinblatt industry momentum (KF49, J=6/K=6, no skip)",
                 fontsize=12)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr32_industry_momentum.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
