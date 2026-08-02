"""Export trading-analysis research outputs as investment-dashboard sibling JSONs.

Integration contract (docs/architecture-integration.md, AUGMENT decision 2026-06-14):
- dashboard_status.json has NO Zod validation -> NEW SIBLING FILES are zero-risk,
  backward-compatible. We never touch existing files/fields/meta.version.
- Every exported score carries its registry verdict label ("honesty" block) so the
  dashboard can never over-claim what the research supports: these are INFORMATION
  layers, not alpha claims (TR-33 NO-STACK; docs/09 momentum dead; docs/05/07
  Minervini alpha decayed).

Outputs (exports/dashboard/):
  quant_scores.json      -- per-ticker: GP quality percentile (members-only, the one
                            surviving cross-sectional signal, with the TR-34 WATCH),
                            Minervini trend-template pass (structure info), RS rating
                            percentile (info only). Universe = dashboard config/stocks
                            intersect our store.
  flagship_combo.json    -- the one borderline-alpha book: current risk-parity sleeve
                            weights, monthly-clock stats (Carhart alpha t, Sharpe,
                            MDD), last 250 equity/drawdown points.
  research_registry.json -- the verdict map as data (groups/classes/counts, zh+en),
                            for a research panel; links to docs/tests/TR-*.md.

Wiring (user step, additive): copy or fetch these into investment-dashboard's
public/data/ (or point the dashboard at this repo's raw GitHub URL). No existing
dashboard file changes.

Run: uv run python scripts/export_dashboard.py   (~2-3 min; needs local store)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/collect")
sys.path.insert(0, "scripts/tests")

OUT = Path("exports/dashboard")
DASH_STOCKS = Path("C:/Users/Romarin/Documents/Software Projects/investment-dashboard/config/stocks.json")
SCHEMA_VERSION = "1.0.0"

HONESTY = {
    "gp_quality_pct": ("only surviving cross-sectional signal (registry docs/10, TR-26/27); "
                       "WATCH: FM panel prices it 2015-2020 (t=+2.67), flat since 2021 (TR-34); "
                       "information, not a bookable sleeve (TR-33 NO-STACK)"),
    "trend_template_pass": ("Minervini stage-2 structure check; registry PARTIAL: structure real, "
                            "alpha decayed (docs/05/07); use as structure info"),
    "rs_rating_pct": ("relative-strength percentile vs our universe; information only: broad "
                      "momentum ICIR~0 here (docs/09), XS top-K momentum = beta (TR-11)"),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[export] {path}  ({path.stat().st_size/1024:.0f} KB)")


def export_quant_scores(store) -> None:
    from sp500_constituents import load_membership
    from tr27_gp_membership_size import member_mask

    from trading_analysis.factors.fundamentals import build_all
    from trading_analysis.strategy.rules.minervini_trend import rs_rating

    dash = json.loads(DASH_STOCKS.read_text(encoding="utf-8"))
    dash_syms = [s["symbol"] for s in dash["stocks"] if s.get("enabled", True)]
    have = set(store.list_symbols("1d"))

    # scores are computed on OUR full stock panel (so percentiles are meaningful),
    # then reported for the dashboard universe
    syms = [s for s in store.list_symbols("1d")
            if s not in ("SPY", "QQQ", "IEF", "TLT", "GLD", "TQQQ", "DIA", "IWM")]
    px_raw = store.load_close_pivot(syms, column="adj_close")
    # honest as_of: the last date where >=90% of the ALIVE panel has a FRESH price.
    # Scoring a cross-section on a mixed-currency row (28/865 fresh after a partial
    # refresh) would rank fresh prices against stale ones. "Alive" = traded within the
    # last 30 bars -- Tiingo-backfilled delisted names end at their delist dates and
    # must not drag the freshness denominator into the past.
    alive = px_raw.columns[px_raw.tail(30).notna().any()]
    frac = px_raw[alive].notna().mean(axis=1)
    t_star = frac[frac >= 0.90].index[-1]
    px = px_raw.loc[:t_star].ffill()
    as_of = str(t_star.date())

    fund = store.load_fundamentals(syms)
    fsyms = [s for s in syms if s in set(fund["symbol"])]
    gp = build_all(fund, px[fsyms], fsyms)["gross_profitability"]
    mem = load_membership()
    mm = member_mask(px.index, fsyms, mem)
    gp_last = gp.where(mm).iloc[-1]
    gp_pct = gp_last.rank(pct=True) * 100

    # Minervini stage-2 structure state at t_star (unlagged display state; the rule's
    # own legs, close-basis, cf. MinerviniTrendRule.to_pivot which lags for backtests)
    c = px
    sma50 = c.rolling(50, min_periods=50).mean().iloc[-1]
    sma150 = c.rolling(150, min_periods=150).mean().iloc[-1]
    sma200 = c.rolling(200, min_periods=200).mean()
    sma200_rising = (sma200.iloc[-1] > sma200.iloc[-22]) if len(sma200) > 22 else pd.Series(False, index=c.columns)
    sma200 = sma200.iloc[-1]
    hi52 = c.rolling(252, min_periods=200).max().iloc[-1]
    lo52 = c.rolling(252, min_periods=200).min().iloc[-1]
    rs_full = rs_rating(c)
    rs_last = rs_full.iloc[-1]
    last = c.iloc[-1]
    tt_last = ((last > sma150) & (last > sma200) & (sma150 > sma200) & sma200_rising
               & (sma50 > sma150) & (last > sma50)
               & (last >= 1.30 * lo52) & (last >= 0.75 * hi52)
               & (rs_last >= 70.0)).fillna(False)

    data = {}
    for s in dash_syms:
        if s not in have:
            data[s] = {"covered": False}
            continue
        row = {"covered": True, "as_of": as_of}
        row["gp_quality_pct"] = (round(float(gp_pct[s]), 1)
                                 if s in gp_pct.index and np.isfinite(gp_pct[s]) else None)
        row["gp_member"] = bool(mm.iloc[-1].get(s, False)) if s in mm.columns else False
        row["trend_template_pass"] = (bool(tt_last.get(s, 0)) if s in tt_last.index else None)
        row["rs_rating_pct"] = (round(float(rs_last[s]), 1)
                                if s in rs_last.index and np.isfinite(rs_last[s]) else None)
        data[s] = row

    covered = sum(1 for v in data.values() if v.get("covered"))
    _dump(OUT / "quant_scores.json", {
        "meta": {"source": "trading-analysis", "schema_version": SCHEMA_VERSION,
                 "generated_at": _now(), "as_of": as_of,
                 "universe": {"dashboard": len(dash_syms), "covered": covered},
                 "honesty": HONESTY,
                 "registry": "https://github.com/romarin-hsieh/trading-analysis/blob/main/docs/18-strategy-registry.md"},
        "data": data,
    })


def export_flagship_combo() -> None:
    import statsmodels.api as sm
    import validate_recommendation as vr

    from trading_analysis.backtest.metrics import max_drawdown
    from trading_analysis.factors.attribution import compound_to_monthly, load_ff_factors_monthly
    from trading_analysis.portfolio import rebalance

    rp, _ew, sleeves = vr.build_combo()
    W = rebalance(sleeves, lookback=126, step=21, method="risk_parity")
    weights = {k: round(float(v), 4) for k, v in W.iloc[-1].items()}

    ff = load_ff_factors_monthly(start="2015-01-01", momentum=True)
    m = compound_to_monthly(rp)
    df = pd.concat([m.rename("r"), ff], axis=1).dropna()
    y = df["r"] - df["RF"]
    X = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "UMD"]])
    t_ols = float(sm.OLS(y, X).fit().tvalues["const"])
    t_hac = float(sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3}).tvalues["const"])

    nav = (1 + rp).cumprod()
    dd = nav / nav.cummax() - 1
    tail = nav.iloc[-250:]
    curve = [[str(d.date()), round(float(v / tail.iloc[0]), 4)] for d, v in tail.items()]

    _dump(OUT / "flagship_combo.json", {
        "meta": {"source": "trading-analysis", "schema_version": SCHEMA_VERSION,
                 "generated_at": _now(),
                 "verdict": ("the campaign's only borderline alpha: monthly Carhart t=2.6-2.7 "
                             "(OLS), below the HLZ 3.0 bar (TR-18); plateau-robust (TR-25); "
                             "deliverable is risk-shaping (half of VOO drawdown), not return-max"),
                 "docs": ["docs/08", "docs/tests/TR-18", "docs/tests/TR-25", "docs/tests/TR-33"]},
        "window": {"start": str(rp.index[0].date()), "end": str(rp.index[-1].date())},
        "weights": weights,
        "stats": {
            "sharpe_daily_ann": round(float(rp.mean() / rp.std() * np.sqrt(252)), 2),
            "mdd": round(float(max_drawdown(nav)), 4),
            "current_drawdown": round(float(dd.iloc[-1]), 4),
            "carhart_alpha_t_monthly_ols": round(t_ols, 2),
            "carhart_alpha_t_monthly_hac": round(t_hac, 2),
            "hlz_pass": bool(t_ols >= 3.0),
            "monthly_obs": int(len(y)),
        },
        "equity_curve_250d": curve,
    })


def export_research_registry() -> None:
    import readme_figs as rf

    groups = []
    for zh, en, items in rf.GROUPS:
        groups.append({
            "group_zh": zh, "group_en": en,
            "tests": [{"code": c, "name_zh": nzh, "name_en": nen, "cls": cls,
                       "doc": f"docs/tests/{c.replace('TR-', 'TR-')}*.md"}
                      for c, nzh, nen, cls in items],
        })
    counts = {k: sum(1 for g in rf.GROUPS for *_, c in g[2] if c == k) for k in rf.COLORS}
    _dump(OUT / "research_registry.json", {
        "meta": {"source": "trading-analysis", "schema_version": SCHEMA_VERSION,
                 "generated_at": _now(),
                 "legend": rf.LEGEND,
                 "repo": "https://github.com/romarin-hsieh/trading-analysis"},
        "counts": counts,
        "groups": groups,
    })


def main() -> None:
    from trading_analysis.data.store import DuckStore

    store = DuckStore("./data")
    print("=" * 90)
    print("EXPORT dashboard sibling JSONs (additive; no existing dashboard file is touched)")
    print("=" * 90)
    export_quant_scores(store)
    export_flagship_combo()
    export_research_registry()
    print("wiring: copy exports/dashboard/*.json into investment-dashboard/public/data/ "
          "(or fetch the raw GitHub URLs); existing dashboard files unchanged.")


if __name__ == "__main__":
    main()
