"""TR-04b (appendix to TR-04) -- Student-t nu MLE fit + t-VaR vs normal-VaR gap.

Closes the docs/20 queue item: TR-04 already showed normal VaR fails Kupiec (2.9% violations
at nominal 1%); this appendix QUANTIFIES the fat tail by fitting Student-t degrees of freedom
nu by MLE on daily returns, and reports how far apart the 99% VaRs sit. Expectation
(pre-committed, from the user's citation): nu in [3, 5]; sizeable VaR gap at 99%+.

POST-RUN AUDIT NOTE (pre-commitment above NOT edited):
  (1) UNCONDITIONAL nu came in at 2.55-3.04 -- 2/3 of series BELOW the pre-committed [3,5]
      band. Not a fit bug: the unconditional distribution mixes volatility clustering, which
      depresses nu. The CONDITIONAL nu (EWMA-0.94-standardized residuals) is 4.7-6.6 -- that
      is the quantity comparable to the cited [3,5]. Both are now reported.
  (2) The 99.9% gap column is PARAMETRIC EXTRAPOLATION, not empirical: QQQ-1999's t-VaR99.9
      (12.97%) was breached 0 times in-sample vs 6.9 expected (over-conservative); the
      EMPIRICAL 0.1% quantile gap vs normal is ~+59%, not +150%. Direction stands (normal
      breaches ~7x nominal at 99.9%) but the precise +107-150% figures are model artifacts.
  (3) "Explains TR-04's Kupiec failure" was OVERSTATED: static fat tails imply only a
      1.6-1.8% violation rate for a static normal VaR99; the remaining gap to TR-04's 2.9%
      comes from volatility clustering + rolling-window lag. Wording corrected below.

Run: uv run python scripts/tests/tr04b_student_t.py
"""

from __future__ import annotations

import numpy as np
from loguru import logger
from scipy import stats

logger.remove()

from trading_analysis.data.store import DuckStore  # noqa: E402


def main():
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-04b  STUDENT-T FIT (MLE) + 99% VaR GAP vs NORMAL (99.9% = extrapolation, see note)")
    print("=" * 100)
    print(f"{'series':16s} {'n':>6s} {'nu_unc':>7s} {'nu_cond':>8s} {'VaR99 t':>9s} {'VaR99 N':>9s} "
          f"{'emp q1%':>9s} {'gap99':>7s} {'gap99.9*':>9s}")
    for sym, start in (("QQQ", "1999-03-10"), ("QQQ", "2015-01-01"), ("SPY", "2015-01-01")):
        px = store.load_close_pivot([sym], column="adj_close").iloc[:, 0].loc[start:]
        rr = px.pct_change().dropna()
        r = rr.to_numpy()
        nu, loc, scale = stats.t.fit(r)
        # conditional nu: EWMA(0.94)-standardized residuals (the quantity comparable to cited [3,5])
        ew = rr.ewm(alpha=0.06).std().shift(1)
        z = (rr / ew).dropna().to_numpy()
        nu_c, _, _ = stats.t.fit(z[np.isfinite(z)])
        var_t99 = -(loc + scale * stats.t.ppf(0.01, nu))
        var_n99 = -(r.mean() + r.std() * stats.norm.ppf(0.01))
        emp99 = -np.quantile(r, 0.01)
        var_t999 = -(loc + scale * stats.t.ppf(0.001, nu))
        var_n999 = -(r.mean() + r.std() * stats.norm.ppf(0.001))
        print(f"{sym + ' ' + start[:4] + '-':16s} {len(r):>6d} {nu:>7.2f} {nu_c:>8.2f} "
              f"{var_t99:>9.2%} {var_n99:>9.2%} {emp99:>9.2%} {var_t99/var_n99-1:>+7.0%} "
              f"{var_t999/var_n999-1:>+9.0%}")
    print("-" * 100)
    print("READ (audit-corrected): UNCONDITIONAL nu = 2.5-3.0 (below the cited [3,5] -- vol clustering")
    print("depresses it); CONDITIONAL nu (EWMA-standardized) = 4.7-6.6 matches the citation. At 99%")
    print("the t-VaR is well-calibrated vs the empirical 1% quantile and the normal underprices by")
    print("~20-25%. *gap99.9 is parametric extrapolation (in-sample t-VaR99.9 breached 0x vs 6.9")
    print("expected on QQQ-1999; empirical 0.1% gap ~+59%) -- direction real (normal breaches ~7x")
    print("nominal), magnitude model-dependent. This quantifies the STATIC-fat-tail component of")
    print("TR-04's Kupiec failure (~1.6-1.8% implied violations); the rest of the 2.9% comes from")
    print("volatility clustering + rolling-window lag. Conventions stand: historical/CF/t-VaR, never normal.")
    print("=" * 100)


if __name__ == "__main__":
    main()
