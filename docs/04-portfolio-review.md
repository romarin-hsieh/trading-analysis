# portfolio/ 對抗式審查（O5）

> ultracode workflow（2026-06-15）：程式碼審查 + 對照 Ledoit-Wolf/DeMiguel-Garlappi-Uppal/Markowitz/Michaud/Kelly。已套用 C1/C2/R1/R2 修正。

# Verdict: `portfolio/` construction module

Both reviews converge cleanly and corroborate each other on the central failure mode. The module is mathematically competent — shrinkage is mandated, SLSQP constraints hold to machine precision, Kelly is fractioned and capped — but it ships a **leakable API** and an **unenforced 1/N discipline** that its own docstrings claim to uphold. **Not trustworthy as-is for any backtest.** The optimizers are sound primitives; the *contract around them* is the liability.

## (1) ISSUES BY SEVERITY

**CRITICAL — leakage / point-in-time**

- **C1. `allocate()` has no temporal contract.** `allocate.py:23-50` consumes *all* rows of `returns` for both `r.mean()` (`:48`) and `shrunk_covariance(r)` (`:42`); the docstring ("single entry point that feeds vectorbt sizing") invites a one-shot `allocate(all_history)` call — textbook look-ahead, with the μ leak the most damaging (optimizer front-runs realized winners). Zero non-test callers today, so the contract can be fixed before misuse is baked in. **Fix:** add a `rebalance(returns, schedule, lookback)` helper that slices `returns.iloc[i-lookback:i]` (strictly `< t`, returns pre-lagged) so callers physically cannot pass full history; have `allocate` raise if `len(returns) > max_window` unless `allow_full_sample=True`.

**Correctness**

- **C2. `max_sharpe` ingests the raw sample mean** (`allocate.py:48` `r.mean()`, fed to `allocators.py:61-64`). Σ is shrunk but μ is not — tangency weights are dominated by μ noise (Michaud's error-maximizer; his Fig-C: estimated Sharpe 0.29 → actual 0.08). Both reviews flag this independently. **Fix:** require `expected_returns` (don't silently default to `r.mean()`), or shrink μ via James-Stein toward the grand mean before it reaches `max_sharpe`.
- **C3. Wrong Ledoit-Wolf target vs. the cited paper.** `covariance.py:29` uses sklearn `LedoitWolf()` = scaled-**identity** target (LW 2004b), which shrinks all correlations toward **zero**. The cited "Honey, I Shrunk…" (LW 2004) uses the **constant-correlation** target — materially better for correlated US large-caps, which is exactly this module's universe. **Fix:** add a `constant_correlation` method (sample variances on diagonal; off-diagonals = avg sample corr × √(vᵢvⱼ); analytic intensity per the paper's Appendix B) and default equities to it; keep sklearn LW/OAS as alternatives.
- **C4. `risk_parity` post-normalization breaks exact ERC.** `allocators.py:58` returns `res.x / res.x.sum()`; the log-barrier optimum is not scale-invariant, so the normalized vector is no longer the exact ERC point. Close in practice (`rc.std()/rc.mean() < 0.1` passes) but the docstring's "equal risk contributions" is overstated. **Fix:** solve with the budget constraint directly, or soften the claim to "approximately equal."

**Robustness**

- **R1. Zero-variance column captures the portfolio.** Confirmed empirically: a constant column survives because LW shrinks its variance to ~1e-6, so `min_variance` puts **98.7%** and `risk_parity` **89.8%** into the degenerate "riskless" asset — silent and catastrophic. **Fix:** in `shrunk_covariance`, detect raw sample variance ≈0 and drop/raise *before* shrinkage masks it.
- **R2. `res.success` ignored in all three optimizers** (`allocators.py:37, 58, 79`). On non-convergence SLSQP returns the last iterate silently. Robust today (200-seed probe feasible), but a latent silent-failure mode. **Fix:** `if not res.success: raise RuntimeError(res.message)`; assert `|sum−1|<tol`, clip tiny negatives.
- **R3. Blunt `dropna()` silently shrinks T** (`covariance.py:23`, `allocate.py:37`). One scattered NaN drops the whole row (1 NaN → 49/50 rows); with staggered listings this can collapse T below N — re-introducing the ill-conditioning shrinkage exists to fix. **Fix:** report dropped-row count; require an aligned gap-free window with an error naming the offending column.
- **R4. T<N only conditioned-away, not gated.** LW runs at T<N (PSD but effective rank T). **Fix:** warn when `T < k·N`.

**Minor**

- **M1.** `max_sharpe`'s `neg_sharpe` returns `0.0` when `vol==0` (`allocators.py:69`) — masks degenerate input as a finite objective; minor since shrinkage prevents it.
- **M2.** Kelly sizing is a **latent primitive** — `configs/mvp.yaml` uses `fixed_fraction`, so `sizing.py` isn't wired end-to-end. Feed it the *same shrunk* μ/σ², not raw moments.
- **M3.** `_SUM_TO_ONE` module-global is fine (stateless).

**Verified-correct** (don't re-touch): LW centers internally; shrunk Σ symmetric/PD/better-conditioned at T≈N; SLSQP constraints tight to 2.2e-16 across 200 seeds; no `max_sharpe` local-minima sensitivity (40 restarts never beat 1/N start); Kelly fractioning+cap is the strongest, most faithful part (Kelly 1956 ruin caveat correctly operationalized).

## (2) THE SINGLE MOST IMPORTANT FIX

**C1 — leak-proof the calling contract before any backtest wiring.** This is the one issue that is (a) cheap now (zero production callers) and (b) ruinous later (every downstream Sharpe becomes fiction once `allocate(all_history)` is called). Both reviewers independently land here. Ship the `rebalance()` walk-forward helper and make full-sample calls raise. Everything else is improvement on top of a sound core; this is the difference between a real backtest and a leaked one. C2's μ-leak is the most damaging *instance* of C1 and should be closed in the same change.

## (3) FOLLOW-UPS (mapped to effort)

| Follow-up | Effort | Note |
|---|---|---|
| `rebalance()` walk-forward helper + raise on full-sample (C1) | **M** | do first; blocks all backtesting |
| Drop/flag zero-variance columns (R1) | **S** | a few lines in `shrunk_covariance` |
| Honor `res.success` + clip/assert (R2) | **S** | guard clause in 3 optimizers |
| Shrink μ (James-Stein) or require `expected_returns` (C2) | **S–M** | closes the worst leak surface |
| `constant_correlation` shrinkage target, default for equities (C3) | **M** | paper-faithfulness; analytic intensity per LW Appendix B |
| `portfolio/evaluate.py` OOS walk-forward + turnover-aware 1/N gate (DGU) | **L** | the discipline the docstrings *assert* but no module implements; route `max_sharpe`/`min_variance` selection through it via `backtest/costs.py` |
| NaN-aware windowing with diagnostics (R3) | **S–M** | |
| Resampled efficiency (Michaud) — bootstrap-averaged weights | **L** | nice-to-have after the gate exists |
| Feed shrunk μ/σ² into Kelly + wire `sizing.py` into config (M2) | **S** | currently latent |

## (4) OVERALL CALL

**Needs fixes — do not wire into a backtest yet.** The numerics are trustworthy; the *API and the enforcement layer are not*. Three small changes plus one medium one make it safe to use: **C1 (temporal contract), R1 (zero-variance drop), R2 (convergence check), C2 (shrink μ / require expected_returns)** — that quartet flips the module from "one careless call from a leaked backtest" to genuinely usable. C3 (constant-correlation target) and the DGU OOS-gate (`evaluate.py`) are the higher-effort items that move it from "usable" to "faithful to the papers it cites." Until the 1/N gate exists, treat `max_sharpe` as experimental and never default to it (the default is already `risk_parity`, which is correct). Bottom line: solid foundation, unsafe contract — fix the contract first.


---

# 附錄 A — 程式碼審查

# Adversarial Review: `portfolio/` construction module

## CRITICAL — Leakage / point-in-time

**C1. `allocate()` has no temporal contract — invites look-ahead.** `allocate.py:23-50` takes a `returns` frame and uses *all* of it (`r.mean()`, `shrunk_covariance(r)`). Nothing in the signature, docstring, or types distinguishes "trailing window known at rebalance t" from "full-sample returns." `allocate.py` docstring even calls it "the single entry point that feeds vectorbt sizing" — so the natural (wrong) call is `allocate(all_history)` once, or worse, `weights = allocate(returns)` then applied across the whole backtest. That is a textbook look-ahead leak: both Σ and μ are estimated on data containing the future. `max_sharpe`'s μ leak is the most damaging (future mean returns → the optimizer trivially front-runs winners). **Fix:** make the windowing explicit and unavoidable. Add a `min_window`/`max_window` and force per-rebalance calls: the only supported pattern is, for each rebalance date `t`, `allocate(returns.loc[:t].iloc[-lookback:])` using strictly `< t` data (returns must already be lagged so row `t` is the return *realized over* `[t-1, t]` and is therefore known at `t`). Provide a `rebalance(returns, schedule, lookback)` helper that loops dates and slices `returns.iloc[i-lookback:i]`, so callers physically cannot pass all history. At minimum, raise if `len(returns) > max_window` unless an `allow_full_sample=True` escape is set. Until that exists this module is one careless call away from a leaked backtest. *(Confirmed: `allocate` is not yet wired into any backtest — `grep` shows zero non-test callers — so this is the moment to fix the contract before misuse is baked in.)*

## Correctness

**C2. `max_sharpe` uses the raw sample mean — estimation-error maximizer.** `allocate.py:48` (`r.mean()`) and `allocators.py:61`. Σ is shrunk (good) but μ is not, and tangency weights are dominated by μ noise (Michaud 1989; Best-Grauer 1991: tiny μ perturbations → wild weight swings). The shrinkage mandate (O5) is half-applied. **Fix:** shrink/denoise μ too — James-Stein toward the grand mean, or expose `expected_returns` as required (don't silently default to `r.mean()`). Document loudly that the default μ is unsuitable for OOS sizing.

**C3. `risk_parity` post-normalization changes the risk-contribution structure it claims to deliver.** `allocators.py:58` returns `res.x / res.x.sum()`. The log-barrier optimum `w*` satisfies `w_i(Σw)_i = const`; but ERC is **not** scale-invariant in this objective — rescaling by `1/sum` shifts the relative balance of the quadratic term vs. the (scale-free) log term, so the *normalized* vector is no longer the exact ERC point. In practice it's close (your test `rc.std()/rc.mean() < 0.1` passes), but "truly equal risk contributions" in the docstring is overstated. **Fix:** solve the ERC problem *with* the budget constraint directly (`sum(w)=1`, `w>0`, objective = variance-of-risk-contributions or the constrained Spinu formulation), or verify-and-iterate the rescaling. State the tolerance ("approximately equal") rather than asserting exactness.

## Robustness

**R1. Zero-/near-zero-variance column captures the portfolio.** Confirmed empirically: a constant column survives because LedoitWolf shrinks its variance to a tiny positive number (≈1e-6), so no exception fires — but `min_variance` then puts **98.7%** and `risk_parity` **89.8%** into the degenerate asset (it looks riskless). `covariance.py` / `allocators.py`. This is silent and economically catastrophic. **Fix:** in `shrunk_covariance`, detect columns with raw sample variance `≈0` and drop or flag them (raise, or warn + exclude), before shrinkage masks them.

**R2. `res.success` is ignored in all three optimizers.** `allocators.py:37, 51-58, 71-79` all `return res.x` regardless of convergence. On non-convergence SLSQP returns the last iterate, which can violate constraints or be garbage, with no signal to the caller. (In my 200-seed T<N probe the constraint slack stayed at 2e-16 and weights were feasible — so it's robust *today* — but you're shipping a silent failure mode.) **Fix:** `if not res.success: raise RuntimeError(res.message)` (or fall back to `equal_weight` with a warning), and assert `abs(res.x.sum()-1) < tol` / clip tiny negatives before returning.

**R3. NaN handling via global `dropna()` is too blunt and silently shrinks T.** `covariance.py:23` and `allocate.py:37` both `dropna()` row-wise. A *single* scattered NaN in any column drops the whole row (confirmed: 1 NaN → 49/50 rows). With staggered listing histories this can collapse T below N (→ ill-conditioning the shrinkage is meant to fix) or to near-empty, all silently. A column that is *entirely* NaN drops every row → `ValueError`, but the message ("need >=2 rows") won't point at the bad column. **Fix:** report dropped-row count, and either pairwise-handle or explicitly require an aligned, gap-free window with a clear error naming the offending column.

**R4. T<N regime is only conditioned-away, not gated.** `covariance.py` happily runs LedoitWolf when `T<N`; the estimate is PSD but the effective rank is `T`, leaving near-zero eigen-directions the optimizers can still exploit. Consider warning when `T < N` (or `T < k·N`).

## Minor

- **M1.** `covariance.py:36` `np.atleast_2d` makes single-asset return a `(1,1)` frame (good), but `sample` for 1 column gives `np.cov(...)` as a 0-d scalar — `atleast_2d` saves it; keep the test for it.
- **M2.** `max_sharpe` `neg_sharpe` returns `0.0` when `vol==0` (`allocators.py:69`) — masks a degenerate input as a finite objective; minor since shrinkage prevents `vol==0` in practice.
- **M3.** `_SUM_TO_ONE` is a module-global lambda shared across calls — fine (stateless), just note it relies on `np.sum(w)`.

## Correct (one line each)

- LedoitWolf **does center** internally (`assume_centered=False`); raw non-zero-mean returns are fine — no manual de-meaning needed. **Verified.**
- Shrunk covariance is symmetric and PD, and better-conditioned than sample at T≈N. **Verified** (matches `test_shrunk_cov_is_pd_and_better_conditioned`).
- SLSQP sum-to-1 + long-only are enforced tightly: max `|sum-1|` = 2.2e-16, no negative weights across 200 ill-conditioned seeds. **Verified.**
- `max_sharpe` did not exhibit local-minima sensitivity here — 40 random restarts never beat the 1/N start across 100 seeds (long-only + shrunk Σ keeps it well-behaved). Still, add restarts as insurance if you relax bounds.
- `equal_weight`, single-asset path, and the Kelly/vol-target clipping (zero-variance→0, cap saturation) all behave as documented.
- Keeping `sample` for comparison-only and mandating shrinkage by default is the right design.

**Top priorities:** C1 (leak-proof the API before any backtest wiring), R1 + R2 (silent degenerate-asset capture and ignored non-convergence), then C2 (shrink μ for `max_sharpe`).

Relevant files: `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\portfolio\allocate.py`, `...\allocators.py`, `...\covariance.py`, `...\sizing.py`.


---

# 附錄 B — 論文對照

# Portfolio Module vs. Source Papers — Faithfulness Audit

**Module:** `src/trading_analysis/portfolio/` (`covariance.py`, `allocators.py`, `sizing.py`, `allocate.py`)
**Verified against:** Ledoit-Wolf (2004), DeMiguel-Garlappi-Uppal (2009), Markowitz (1952), Michaud (1989), Kelly (1956).
*Note: the DGU PDF is image-only (no text layer) and could not be OCR'd in this environment; its findings are assessed from the paper's well-established results, which the module's own docstrings cite correctly.*

## 1. Ledoit-Wolf — "Honey, I Shrunk the Sample Covariance Matrix"

**Faithful?** Partially. We shrink (the paper's central thesis) and we route every optimizer through a shrunk covariance — correct in spirit. But `shrunk_covariance` uses `sklearn.LedoitWolf`, whose target is the **scaled identity** (spherical: equal variances, zero correlations). The *paper's* operational estimator is **shrink-CC: the constant-correlation target** (the page-5 text states they chose it over the single-factor target "because it is easier to implement [and] gives comparable performance"). sklearn's spherical target is from Ledoit-Wolf (2004b, *Ann. Stat.*), a *different* paper.

**Does the difference matter for us?** Yes, materially, for equities. The identity target shrinks all pairwise correlations toward **zero**; equities have a strong, persistently positive common (market) factor, so an equity covariance shrunk toward zero-correlation is biased exactly where min-variance and max-sharpe are most sensitive. The constant-correlation target preserves the average positive correlation — a far better prior for a stock universe. For our use case (correlated US large-caps) this is the single most consequential gap.

**Gap:** Wrong shrinkage target relative to the cited paper.
**Recommendation:** Add a `constant_correlation` method to `shrunk_covariance` (sample variances on the diagonal; off-diagonals set by the average sample correlation × sqrt(var_i·var_j); analytic optimal intensity per the paper's Appendix B) and make it the **default for equities**. Keep sklearn LW/OAS as alternatives.

## 2. DeMiguel-Garlappi-Uppal — "Optimal Versus Naive Diversification" (1/N)

**Faithful?** No — aspirational only. The docstrings repeatedly assert "every optimizer must beat equal_weight OOS net of turnover," but **no code operationalizes it.** There is no rolling/expanding-window OOS harness, no turnover computation, and no gate that rejects an allocator failing to beat 1/N net of cost. `equal_weight` exists as a callable, not as an enforced benchmark. DGU's entire point is that sample-based optimizers lose to 1/N out-of-sample *once estimation error and rebalancing turnover are charged* — so an in-sample-only implementation reproduces precisely the trap the paper warns against.

**Gap:** The discipline is documented but not enforced.
**Recommendation:** Build a `portfolio/evaluate.py` walk-forward harness: estimate weights on a trailing window, hold OOS, roll, accumulate net returns, and compute per-rebalance turnover (Σ|w_t − w_{t−1}|) charged through the existing `backtest/costs.py` model. Report OOS Sharpe and **certainty-equivalent net of turnover vs. 1/N** for each method, with 1/N as a hard gate (and, ideally, the DGU paper's own metrics). Wire `max_sharpe`/`min_variance` selection to that gate rather than to in-sample objective values.

## 3. Michaud — "The Markowitz Optimization Enigma"

**Faithful?** Largely, on the cheapest fixes. Michaud's "error-maximization" diagnosis is addressed by (a) shrinkage and (b) the long-only constraint (w ≥ 0) — and he explicitly notes long-only and informed input adjustment both blunt error-maximization; Jagannathan-Ma echo this. So our defaults are pointed the right way.

**But:** Michaud's *constructive* remedy is **resampled efficiency** — Monte-Carlo resampling of the inputs to average over "statistically equivalent" portfolios — and we have **none of it**. More importantly, `max_sharpe` is still dangerous: it is the textbook estimation-error maximizer because it ingests the **sample mean** `r.mean()` directly (`allocate.py` line 48). Michaud's Figure-C example shows the estimated tangency Sharpe (0.29) collapsing to an actual 0.08 — means are far noisier than covariances, and shrinkage of the *covariance* does nothing to fix a noisy *mean*. Long-only caps the damage but does not remove it.

**Gap:** No resampling; `max_sharpe` consumes raw sample means.
**Recommendation:** Treat `max_sharpe` as opt-in/experimental, gated behind the DGU OOS test, and never default to it. As a concrete first step, shrink the *mean* (James-Stein / Black-Litterman-style grand-mean shrinkage) before it reaches the tangency optimizer; add resampled weights (average over N bootstrap re-draws of returns) as a follow-on.

## 4. Kelly — "A New Interpretation of Information Rate"

**Faithful?** Yes — this is the strongest part. `kelly_leverage` implements f·μ/σ² with a fractional multiplier (half-Kelly default) and a hard cap, which is exactly the prudent operationalization. Kelly's own derivation shows full-Kelly betting maximizes *expected* wealth yet leaves the gambler "broke with probability one" as N→∞ under noise — the variance/ruin caveat that justifies fractioning. Pairing with `vol_target_scale` is sound.

**Caveat:** Kelly assumes **known** μ and σ². In practice μ is estimated with large error, so even half-Kelly on an estimated edge can over-lever; the right fraction shrinks as estimation uncertainty rises. Also note Kelly sizing is **not yet wired into the default pipeline** — `configs/mvp.yaml` uses `fixed_fraction`, so this is a latent primitive.

**Recommendation:** Keep fractional + capped Kelly as the policy, but feed it the *same shrunk* μ and σ² used elsewhere (not raw sample moments), and document that the fraction is an estimation-error haircut, not a risk preference — consider scaling the fraction down with a confidence proxy (e.g., shorter/noisier history → smaller fraction).

---

### Priority order
1. **DGU OOS-net-of-turnover gate** (#2) — currently asserted but absent; it is the discipline that makes everything else safe.
2. **Constant-correlation shrinkage target** (#1) — correct the paper-vs-implementation mismatch for equities.
3. **Shrink means before `max_sharpe` + gate it** (#3) — close the remaining error-maximization hole.
4. **Feed shrunk moments into Kelly** (#4) — already well-designed; minor hardening.

**Key file references:** target mismatch at `covariance.py:29`; raw sample mean into tangency at `allocate.py:48`; missing OOS/turnover harness across the package (`__init__.py:3-4` docstring claims it; no module implements it).