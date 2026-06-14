# 量化研究與優化議程（35 篇論文 × 我們的引擎）

> ultracode workflow（2026-06-15）。讀 `C:/Users/Romarin/Documents/Quant Analysis` 35 篇論文，分 5 主題 + meta-labeling 對抗審查。

# Quant Research + Optimization Deliverable — trading-analysis Engine

Twenty-eight papers across five themes plus an adversarial code review, distilled into what to keep, fix, and build. Cross-references use the form *[Theme:Paper]*.

## 1. VALIDATES — papers that confirm choices already in the engine

| Our choice (module) | Confirmed by | What it confirms |
|---|---|---|
| `minervini_trend` rule + cross-sectional RS | Jegadeesh-Titman 1993; Brock-Lakonishok-LeBaron 1992; Hurst-Ooi-Pedersen 2017 | RS momentum earns ~1%/mo unexplained by risk; MA rules carry information; trend is profitable every decade 1880-2016. |
| 1-bar signal lag | Jegadeesh-Titman 1993 (skip-week); Hurst-Ooi-Pedersen 2017 | Skip-period is standard hygiene against microstructure bias; HOP show signal lag *erodes* returns — our lag is the honest minimum, don't add more. |
| 200-SMA / HMM regime gate | Hurst-Ooi-Pedersen 2017; Campbell-Thompson 2005; Sharpe 1964 | Trend pays in trending regimes; gating to market state is the "TSMOM smile." |
| Cross-sectional rank-IC / ICIR / quantile-spread harness (`factors/validation.py`) | Fama-French 1992/1993; Ross 1976 (APT) | Decile sorts on characteristics with NYSE-style breakpoints are the canonical cross-section test; APT licenses empirically-motivated multi-factor panels. |
| Mean-reversion pack: Hurst / half-life / **variance-ratio** (`features/`) | Lo-MacKinlay 1988 | VR is the canonical leak-free random-walk test; our pack is the right toolset. |
| Triple-barrier + trend-scanning labels (`labeling/`) | de Prado (AFML); Gatev-Goetzmann-Rouwenhorst 2006 | Horizontal barriers = the natural σ-band entry/exit; pairs 2σ/0σ maps onto it directly. |
| **PurgedKFold** strict purge + embargo (`labeling/cv.py`) | de Prado (AFML Ch.7); Bailey-López de Prado (DSR) | Interval-overlap purge + embargo is the correct *leakage* control (verified timestamp-based, no axis mixing). |
| LightGBM meta-labeling, shallow trees (`ml/meta_labeling.py`) | Gu-Kelly-Xiu 2020; de Prado | Trees beat deep nets at finance's low signal-to-noise; shallow/regularized wins; meta-label probability is exactly the input Kelly sizing needs. |
| Causal feature panel — momentum, rvol, ATR, volume | Gu-Kelly-Xiu 2020 | GKX's **top-3 predictor categories** are price-trend, volatility, liquidity — we have the first two. |
| Rigor scorecard: Deflated Sharpe (#5), look-ahead, survivorship, walk-forward | Bailey-López de Prado (DSR); Brown-Goetzmann-Ibbotson-Ross 1992; McLean-Pontiff 2013; White 2000 | DSR targets exactly in-sample inflation; BGIR validate the survivorship line; MP validate walk-forward/decay. |
| Skepticism toward over-engineered estimation | Michaud 1989; DeMiguel-Garlappi-Uppal 2009 | "Estimation-error maximizer"; 1/N is hard to beat — our caution is correct. |

**Net:** Nothing already built is *wrong* by these papers. Two practices are *insufficient* (not incorrect): PurgedKFold protects against leakage but not selection bias *[Validation:DSR/PBO]*, and the cost model (if flat-bps) understates impact *[Execution:all]*. Those are in §2.

## 2. OPTIMIZE NOW — improvements to existing modules, ranked

**O1. Multiple-testing gate into the rigor scorecard — `backtest/` (highest value).** PurgedKFold is leakage control, *not* overfitting control — DSR shows "apply holdout 20 times and false positives are expected." Add three files: `backtest/deflated_sharpe.py` (PSR+DSR, consuming the **real trial count N** = every grid cell × feature subset tried), `backtest/spa.py` (Hansen's SPA — studentized, sample-dependent null; preferred over White's RC because junk strategies dilute RC's power), and `backtest/pbo.py` (CSCV; gate promotion on PBO < 0.5). *How:* log every rule-threshold and LightGBM config to a trial registry, feed N into DSR, surface PBO + IS-vs-OOS degradation slope as scorecard lines. This is the loudest cross-theme message — *[Validation:White/Hansen/STW/DSR/PBO]* and *[Factors:McLean-Pontiff]* both demand it.

**O2. Size-dependent costs into `backtest/` — replace flat-bps (highest value, currently-wrong).** If vectorbt fills at close with a constant haircut, we are the "20%/yr paper portfolio" of Bertsimas-Lo's Perold example (live fund got 2.5%/yr). *How:* `cost = spread/2 + λ·(trade_$/ADV)`, with **Kyle-λ ≈ daily σ / daily $volume** (Amihud proxy) computed from the `features/` panel we already have. Add an **implementation-shortfall line** (arrival price vs. realized fills) as the headline cost metric. *[Execution:Kyle/Bertsimas-Lo]*

**O3. Carhart-4 / FF3 factor benchmark into `factors/` — make alpha the bar, not Sharpe.** A trend system loads hard on UMD and HML; raw Sharpe mis-attributes factor beta as skill (Fama-1970 joint-hypothesis). *How:* build SMB/HML (2×3 size×BE/ME sorts, value-weighted, **NYSE breakpoints**, June rebalance, BE from t-1 — FF1993 recipe) + UMD, add a regression step so every strategy reports **α net of Mkt/SMB/HML/UMD**. This is the single most important benchmark for `minervini_trend`. Dependency: EDGAR book equity → makes EDGAR the first fundamentals deliverable. *[Factors:FF92/FF93/Carhart/Ross/Fama70]*

**O4. McLean-Pontiff decay haircut into the scorecard — `backtest/`.** Known anomalies decay ~35% post-publication. *How:* add a haircut line discounting live alpha of well-known factors (value/momentum/size) by ~35%, plus a **post-publication-date walk-forward window**, and lean into less-arbitraged corners (illiquid/small/high-idio-vol — fits the TW small-cap tilt where MP show decay is weakest). *[Factors:McLean-Pontiff]*

**O5. Ledoit-Wolf shrinkage as a build constraint for `portfolio/` — before any Σ touches code.** Raw sample Σ is an estimation-error maximizer (Michaud). *How:* `sklearn.covariance.LedoitWolf` (constant-correlation target) — one import, CPU-trivial, zero infra cost. Mandate it so risk-parity/min-variance get shrunk inputs from day one. *[Portfolio:Ledoit-Wolf/Michaud]*

**O6. Liquidity feature pack into `features/` — fix the one GKX gap.** GKX rank liquidity their **#2** predictor category; we have volume/rvol but no true liquidity pack. *How:* add dollar volume, bid-ask spread, market cap. Cheap, high-IC, also feeds the Kyle-λ in O2. *[Factors:Gu-Kelly-Xiu]*

**O7. Heteroskedasticity-robust statistics across `rigor`/`features/`.** Returns cluster (ARCH/GARCH), so any i.i.d. bootstrap or homoskedastic VR is mis-specified. *How:* use Lo-MacKinlay's **robust z*(q)** VR (not homoskedastic — it over-rejects), compute VR per-asset with `q∈{2,4,8,16}` and report the sign distribution (VR>1 at index level but <1 for single names — a global VR mislabels structure); use **block/wild bootstrap** under AR(1)/GARCH-M nulls; add an ARCH-LM diagnostic. *[TimeSeries:Lo-MacKinlay/Engle/Bollerslev]*

**O8. Campbell-Thompson constraints on the regime/timing layer.** Unconstrained OLS premium/regime predictors fail OOS. *How:* impose **coefficient-sign restriction + non-negative-equity-premium floor** on any market-timing overlay or HMM regime-probability regression. Cheap, high-value. *[Factors:Campbell-Thompson]*

**Stop doing:** raw CAPM β as an alpha factor (β-return is flat — FF92; β is for risk-neutralization only, *[Factors:Sharpe/FF92]*); judging edge on raw/excess Sharpe alone; unconstrained OLS over wide feature sets (GKX: goes negative OOS); taking the roadmap line "PyPortfolioOpt **MVO**" literally (see O11).

## 3. RESEARCH & MODEL-DESIGN AGENDA — new builds, prioritized

**DO FIRST → R1. GARCH(1,1) vol-targeting — Effort S, very high value.** A single change that connects four modules. *How:* `features/garch_vol` via the `arch` package, point-in-time expanding-window fit only, one-step-ahead σ. Feeds (a) **vol-target position sizing** in `portfolio/` (HOP's core lesson: scale each `minervini_trend` name to constant per-name vol, target ~10% book vol), and (b) `ml/` meta-label sizing. Highest ROI on the board — CPU-cheap, fits <$15/mo. *[TimeSeries:Bollerslev/HOP]*

**R2. Kelly bet-sizing in `ml/` — Effort S, high value.** We already produce the OOS probability `p` and triple-barrier payoff ratio `b` — everything Kelly needs. *How:* **fractional/half-Kelly** off `(p, b)` to convert the binary side into a sized position (full Kelly is too aggressive given estimation error — same Michaud/DGU lesson). Pairs naturally with R1. *[Portfolio:Kelly]*

**R3. Point-in-time / survivorship-free universe — Effort M, high value (do early, expensive to retrofit).** Cross-sectional RS, rank-IC, and every future FF/QMJ port are corrupted by a survivor-only universe (BGIR: survival *manufactures* spurious persistence). *How:* enforce point-in-time universe membership including delisted names in the data layer feeding `features/`/`factors/`; document as a hard precondition. Gates the credibility of everything cross-sectional. *[Validation:BGIR]*

**R4. Pairs-trading / cointegration module — Effort M, high value.** The clean market-neutral complement to the trend engine; exploits the mean-reversion our Hurst/half-life features already detect. *How:* `strategies/pairs_trading` — distance-match selection, 12-mo formation / 6-mo trade, **2σ entry / 0σ exit / time-stop** mapped onto existing triple-barrier `labeling/`; gate trend-vs-revert with the robust VR from O7. Include post-2002 decay check (GGR show crowding). *[TimeSeries:Gatev/Lo-MacKinlay]*

**R5. `execution/` as a tiered cheap model — Effort M, high value.** *How:* **TWAP/equal-slice baseline** (Bertsimas-Lo: provably optimal under simplest assumptions, zero tuning) + **Almgren-Chriss trade half-life τ=1/κ** parameterized off `features/` (ATR→σ, $volume→impact). Surfaces a per-name capacity check for `portfolio/` (position too big if AC half-life > rebalance horizon). Add Obizhaeva-Wang resilience as a **single stress-test knob** (recovery half-life), not an LOB simulator (~7% cost swing → report net-Sharpe across fast/slow band). *[Execution:Bertsimas-Lo/Almgren-Chriss/Obizhaeva-Wang]*

**R6. GKX-style ML asset-pricing evaluation discipline — Effort M, medium-high value.** Not a new model — a new *evaluation contract*. *How:* judge the meta-labeler at the **portfolio level** (GKX stock-level R² is ~0.3%/mo; portfolio R² is 1-1.8%); keep tree depth/leaves small; evaluate bottom-up decile Sharpe. Wire into O1's gate. *[Factors:Gu-Kelly-Xiu]*

**R7. Fundamental momentum + QMJ / FF factors — Effort L, medium value (post-EDGAR).** *How:* after O3's EDGAR book-equity lands, add QMJ (quality) and earnings/fundamental-momentum factors to the APT-style panel. Larger effort, gated on the fundamentals layer; sequence after R1-R5.

**Sequencing:** R1 → R2 (sizing stack, days) → R3 (universe, before scaling factors) → R4/R5 (parallel new modules) → R6 (eval discipline, continuous) → R7 (after EDGAR). Demote naked MVO to an also-ran (R8, low priority): recast `portfolio/` around shrunk-Σ **risk-parity/min-variance + 1/N benchmark + Kelly/vol-target sizing**; max-Sharpe MVO must *earn* its place by beating 1/N net of turnover OOS (DGU). Cover's universal portfolio is an optional assumption-free benchmark only.

## 4. META-LABELING REVIEW VERDICT

I re-ran the review's claims against the actual source. **All line references verified.** Issues by severity:

**C1 — CRITICAL (correctness / silent metric corruption). CONFIRMED.** `walk_forward_meta_prob` re-sorts internally (`meta_labeling.py:103`) and returns the prob Series on the **sorted** `ds.index` (`:116`), but `evaluate_meta` reads `y` from the **caller's** unsorted order (`:121`) and pairs it positionally with `prob`. Every metric (AUC, lift, hit-rate) is then computed on mismatched (y, prob) pairs. It only passes today because `build_meta_dataset` happens to return sorted (`:83`), so no test exercises an unsorted caller. This is leakage-grade: plausible-but-wrong numbers, not a crash. **Fix:** return the prob aligned to the *input* index (assign back onto the original index, don't `reset_index`), or return the sorted dataset alongside the probs and have `evaluate_meta` consume that exact object. Minimum guard: assert `dataset["t_event"].is_monotonic_increasing` at the top of both functions. **This is the top priority — fix before any further use.**

**C2 — MEDIUM (correctness; public-API leak surface). CONFIRMED.** When `feature_panel` is passed pre-built (`:41`, `:70`), there is no check that its `ts` grid is a subset of `close.index` or that it came from the causal `build_features`. The default path is safe (verified `build_features` is genuinely causal — rolling/shift/`min_periods`, no centering or full-sample fit), but the API lets a caller inject a future-inclusive panel undetected. **Fix:** when `feature_panel` is supplied, assert per-symbol `ts ⊆ close.index` and document that it must come from `build_features`.

**W1 — MINOR (unstated contract).** OOS-prob coverage <100% near series ends is correct and leak-free (rows in one-class/empty-train folds stay NaN, dropped by `evaluate_meta`'s `valid` mask). **Fix:** document that sub-100% coverage is expected.

**W2 — MINOR (silent no-op).** `subsample=0.8` (`:30`) has **no effect** without `subsample_freq>0` in LightGBM — row bagging is never applied. **Fix:** set `subsample_freq=1` if bagging is intended, else drop `subsample` to avoid implying randomness that isn't happening. (`random_state=0`, `n_jobs=1`, `verbosity=-1` are correctly set for determinism.)

**E1 — MINOR (metric framing).** `lift = meta_hit − rule_hit` (`:133`) compares the filtered subset's win-rate to the *full* OOS base rate — de Prado's intended framing, but not edge over a random filter at the same coverage. **Fix:** also report precision-at-coverage so a high-threshold cherry-pick can't masquerade as lift.

**Investigated and CONFIRMED CORRECT (no action):** pooled duplicate-`t_event` purge across symbols (timestamp comparison at `cv.py:54` purges by time regardless of array position — sidesteps the searchsorted-conflates-time-with-position bug the comment flags); `X.index.equals(t1.index)` on non-unique datetime index (positional, duplicates fine); embargo `searchsorted(side="right")` on the sorted non-unique index; AUC/lift computed on OOS rows only (no selection bias); one-class fold guard (`:111`); `triple_barrier_events` first-touch `t1`; `get_bins` {0,1} meta-target; long-only side encoding; causal EWMA vol target.

**Overall call: NEEDS FIXES before trusting reported metrics — but the leakage/CV core is sound.** The leak-free machinery (PurgedKFold, triple-barrier, causal features, OOS-prob construction) is correct and well-built. The blocker is **C1**, a presentation/alignment bug in the evaluation layer that silently invalidates every reported metric the moment a caller doesn't pre-sort. Fix C1 (must) and C2 (should); W1/W2/E1 are polish. Post-C1, the meta-labeler is trustworthy — and note the §2/§1 caveat that even a correct PurgedKFold is *leakage* protection, not *selection-bias* protection, so the O1 DSR/PBO/SPA gate is still required above this layer before any strategy is promoted.

---

Verified source files: `src\trading_analysis\ml\meta_labeling.py`, `src\trading_analysis\labeling\cv.py` (both confirm the review's line-level claims); existing modules confirmed present: `src\trading_analysis\factors\validation.py`, `src\trading_analysis\backtest\engine.py`, `src\trading_analysis\execution\base.py`. Files to add per §2/§3: `backtest\deflated_sharpe.py`, `backtest\spa.py`, `backtest\pbo.py`, `features\garch_vol.py`, `strategies\pairs_trading\`, plus a trial-registry hook in `ml/` and a point-in-time universe contract in the data layer.


---

# 附錄 A — 因子與可預測性

# Academic Asset-Pricing Theme → trading-analysis Engine

Read from source PDFs (first pages + key tables) unless noted. Carhart and Ross are image-only scans with no text layer (no `pdftoppm`/OCR available in this env), so those two are covered from established knowledge and flagged.

## Per-paper findings

**Fama-French 1992, "The Cross-Section of Expected Stock Returns."** Core: Two variables — size (ME) and book-to-market (BE/ME) — absorb the cross-section of average returns over 1963-1990; market β is *flat* (no relation to return) once you control for size. Validates: our cross-sectional rank-IC harness and the *idea* of cross-sectional characteristic sorts — FF use NYSE breakpoints and sort into deciles, exactly our quantile-spread design. Challenges: nothing we built, but it warns that β alone is not a return predictor — don't let CAPM β leak in as an "alpha" factor. Improvement: add **size and value (BE/ME)** as first-class factors in `factors/`, built with **NYSE breakpoints** (not all-stock breakpoints — FF show that all-exchange breakpoints make portfolios all-small after NASDAQ enters). This needs EDGAR book equity → a concrete dependency for the planned fundamentals layer.

**Fama-French 1993, "Common risk factors."** Core: A 3-factor model (Mkt, SMB, HML) plus two bond factors; mimicking portfolios for size/value capture *common variation* and drive intercepts (alphas) to ~0. Validates: our IC-validation harness needs a *benchmark to risk-adjust against* — FF3 is that benchmark. Challenges: our `rigor scorecard` and meta-label OOS probabilities currently judge the rule's edge in raw/excess-return terms; FF3 says the right bar is **alpha net of Mkt/SMB/HML**, because momentum strategies load heavily on these. Improvement: build the **SMB/HML construction** (6 portfolios from 2×3 size × BE/ME sorts, value-weighted, rebalanced each June, BE from year t-1) and add an **FF3 (then FF3+momentum) regression step** in `backtest/`/rigor so every strategy reports α, not just Sharpe. The paper's exact recipe is in the extract — port it directly.

**Jegadeesh-Titman 1993, "Returns to Buying Winners and Selling Losers."** Core: 3-12 month relative-strength (momentum) earns ~1% /month; the best 12-month-formation/3-month-hold strategy yields **1.31%/month** (1.49% with a 1-week skip), *not* explained by systematic risk; ~half reverses over the following 24 months. Validates strongly: our `minervini_trend` rule, our momentum/RS features, the cross-sectional RS ranking, and **the 1-bar lag** — JT explicitly add a 1-week skip to dodge bid-ask/microstructure bias; our 1-bar-lag is the same hygiene. Improvement: implement the **skip-period convention explicitly** (formation return computed to t-2, not t-1, i.e. a skip-month gap) as a tunable in `features/`, and add a **momentum-reversal guardrail** — JT's 24-month decay means holding periods should be bounded; encode an exit/holding-horizon cap in the rule/meta-label sizing.

**Carhart 1997, "On Persistence in Mutual Fund Performance"** (image-only scan — from knowledge). Core: Adds a momentum factor (UMD/WML) to FF3 → the **4-factor model**; fund "persistence" is mostly the momentum factor plus expenses, not skill. Validates: our entire momentum thesis deserves to be benchmarked against a *priced momentum factor*, not treated as free alpha. Challenges: if `minervini_trend`'s edge is just UMD loading, our rigor scorecard would currently mis-attribute it to the rule. Improvement: add **UMD** as the 4th factor in the `factors/` regression panel; report `minervini_trend` alpha net of **Carhart-4**. This is the single most important benchmark for a trend/momentum system.

**Sharpe 1964, CAPM.** Core: In equilibrium, expected return is linear in market β alone (security market line); β is the only priced risk. Validates: the *concept* of a market factor and regime-gating to the market (our 200-SMA/HMM gate is a crude market-state version). Challenges/flag: FF1992 empirically *killed* the β-return relation — so do **not** add raw β as an alpha factor in `factors/`; β belongs only as a *risk control / neutralization* term, and as the denominator in risk-adjustment. Improvement: use β purely for **risk-neutralization** in `portfolio/` (beta-neutral or beta-targeted positioning), not as a return signal.

**Ross 1976, APT** (image-only scan — from knowledge). Core: Returns are driven by a *small set of common factors*; expected return is linear in factor loadings, with no-arbitrage pinning the prices — multi-factor, theory-agnostic about *which* factors. Validates: our whole multi-factor `factors/` direction and the IC/quantile-spread machinery — APT is the license to use empirically-motivated factors (momentum, value, quality) without a CAPM derivation. Improvement: structure `factors/` as an **APT-style multi-factor panel** with explicit factor-loading regressions (betas to Mkt/SMB/HML/UMD/QMJ), enabling factor-risk decomposition of any strategy's returns.

**Gu-Kelly-Xiu 2020, "Empirical Asset Pricing via ML."** Core: Trees and neural nets roughly **double** the long-short Sharpe of linear models (NN value-weighted decile spread Sharpe **1.35** vs OLS **0.61**); naive OLS on 900+ predictors goes *negative* OOS; the top predictors across all methods are **price trends (momentum/reversal), liquidity, and volatility**. Validates a lot: (a) our choice of **LightGBM** (trees > deep nets at finance's low signal-to-noise — GKX find shallow trees ~6 leaves win); (b) our feature panel — momentum, rvol, ATR, volume are *exactly* GKX's top-3 categories; (c) the necessity of regularization/dimension-reduction (our PurgedKFold + MDI/ADF selection). Challenges: nothing built, but it implies our raw stock-level R² will be tiny (GKX: ~0.3-0.4%/month) — **judge models at the portfolio level**, where GKX get R² 1-1.8%. Improvement: add **liquidity features** (dollar volume, bid-ask spread, market value) to `features/` — currently we have volume/rvol but not a true liquidity pack; GKX rank these #2. Also: keep tree depth/leaves **small** (regularize hard), and evaluate via **bottom-up portfolio R²/Sharpe**, not stock-level R².

**McLean-Pontiff 2013, "Does Academic Research Destroy Predictability?"** Core: Across 82 published anomalies, returns decay **~10% out-of-sample** (statistical bias, insignificant) and **~35% post-publication** (arbitrage). Validates: our entire `rigor scorecard` (Deflated Sharpe, walk-forward) and PurgedKFold — these target exactly the in-sample inflation MP measure. Challenges/flag: a published-anomaly factor backtest will **overstate live alpha by ~35-50%** — our scorecard should *haircut* it. Improvement: add an explicit **"publication/anomaly-decay haircut" line to the rigor scorecard** — discount expected live alpha of any well-known factor (value, momentum, size) by ~35%, and **prefer less-arbitraged niches** (MP: decay is *smaller* for high-idiosyncratic-risk, illiquid, small stocks — relevant to the TW/small-cap tilt). This also argues for a **post-publication start-date** in walk-forward: test the factor on data *after* its paper to see real decay.

**Campbell-Thompson 2005, "Predicting the Equity Premium OOS."** Core: Equity-premium predictors beat the historical-mean forecast OOS *only* after imposing **sign restrictions** (coefficient sign + non-negative equity premium); OOS R² is tiny (<0.5%/month) but economically meaningful. Validates: our regime gate (don't go long when the model is "perverse"). Challenges: a free OLS time-series predictor (e.g. for the 200-SMA/HMM regime probability) will likely **fail OOS** unless constrained. Improvement: in any equity-premium/regime timing model, **impose economic sign constraints and a non-negative-premium floor** (Campbell-Thompson's two restrictions) — a cheap, high-value rule for the regime layer and any market-timing overlay.

**Fama 1970, "Efficient Capital Markets."** Core: The weak/semi-strong/strong-form taxonomy; prices "fully reflect" information, so any predictability test is a *joint test* of efficiency + the assumed return model. Validates: the humility baked into our rigor scorecard. Flag: the **joint-hypothesis problem** means our IC/alpha results are only as good as the benchmark model — reinforcing the FF3/Carhart-4 risk-adjustment point above.

## Theme takeaways (highest-value actions)

1. **Build the FF3 → Carhart-4 (→ QMJ) factor panel in `factors/` and make it the benchmark, not an afterthought.** Every strategy — especially `minervini_trend` — must report **alpha net of Mkt/SMB/HML/UMD**, because a trend system loads hard on UMD/HML. Use **NYSE breakpoints, 2×3 sorts, value-weighted, June rebalance, BE from t-1** (FF1993 recipe, in the extract). This requires EDGAR book equity — make it the first fundamentals deliverable.

2. **Add a McLean-Pontiff decay haircut to the rigor scorecard and prefer less-arbitraged corners.** Discount known-anomaly live alpha by ~35%; add a post-publication-date walk-forward window; lean into illiquid/small/high-idio-vol names where MP show decay is weakest (fits a TW small-cap tilt).

3. **Lean into what GKX validated, fix the one gap.** Keep LightGBM with **shallow, heavily-regularized trees**; evaluate at the **portfolio level** (stock-level R² is ~0.3%); and **add a liquidity feature pack** (dollar volume, bid-ask spread, market cap) — GKX rank liquidity the #2 predictor category and we're missing it. For any market-timing/regime model, apply **Campbell-Thompson sign + non-negative-premium constraints**.

**Things to stop / not do:** Do **not** add raw CAPM β as an alpha factor (FF1992 show β-return is flat) — β is for risk-neutralization only. Do **not** judge the rule's edge in raw or excess-return Sharpe alone (Fama-1970 joint-hypothesis + Carhart) — risk-adjust against the factor model. Do **not** run unconstrained OLS time-series predictors for regime/premium timing (Campbell-Thompson) or unconstrained OLS over a wide feature set (GKX: goes negative OOS).

Source extracts saved at `C:\Users\Romarin\AppData\Local\Temp\qextract\` (ff1992.txt, ff1993.txt, jt1993.txt, gkx.txt, mclean.txt, campbell.txt, sharpe.txt, fama1970.txt). Carhart and Ross PDFs are image-only scans with no extractable text in this environment.


---

# 附錄 B — 驗證與資料窺探

# Data-Snooping, Overfitting & Survivorship — What This Theme Means for trading-analysis

This theme is the statistical-rigor backbone for everything we backtest. All six papers attack one enemy: **performance inflation from searching over many strategies/rules/funds and reporting only the winner.** They directly govern our `backtest/` module and the 10-point `rigor scorecard`, and they impose constraints on `factors/`, `ml/`, and `labeling/`.

## Paper-by-paper

**White, *A Reality Check for Data Snooping* (2000).** Core result: a bootstrap test (the "Reality Check") for the null that *the best model found in a specification search has no predictive superiority over a benchmark*, delivering an asymptotically valid p-value that accounts for the **full universe of L models searched**, not just the winner (Example 2.2 is literally a trading-strategy long/short signal vs. buy-and-hold). Validates our scorecard's "walk-forward / multiple-testing" intent but **challenges our practice**: we currently have *no* familywise p-value for the rule-selection step. When we pick `minervini_trend`'s 8 thresholds (or sweep RS cutoffs / ATR multiples), the single-strategy Sharpe is optimistic. Improvement: add a `backtest/reality_check.py` implementing White's stationary-bootstrap max-statistic over the L parameterizations we actually tried.

**Hansen, *A Test for Superior Predictive Ability (SPA)* (2005).** Core result: a strictly better version of White's RC — it **studentizes** the loss differentials and uses a **sample-dependent null** that down-weights "poor and irrelevant" alternatives; the RC's power can be **driven to zero** simply by padding the candidate set with junk strategies. Challenges a naive RC port: if we throw all our gridded rules into one Reality Check, the bad ones dilute the test. Improvement: implement **Hansen's SPA (the consistent p-value), not plain RC** — studentize by each strategy's own bootstrap std. This is the single best multiple-testing test for our `backtest/` selection gate.

**Sullivan-Timmermann-White, *Data-Snooping, Technical Trading Rules* (1999).** Core result: applying the RC to **~7,846 trading-rule parameterizations** on 100 years of DJIA, the best rule *survives* snooping adjustment in-sample (1897–1986), but **out-of-sample (1987–1996) the best rule's p-value is ≈0.12 — no significant economic value**, and on S&P futures (with real costs) nothing beats the benchmark. This is the most direct mirror of our system: `minervini_trend` is a technical rule selected from a family. Validates our 1-bar-lag and regime-gating discipline but **flags a real risk**: a trend rule that looks great in-sample can be snooping-driven. Improvement: treat the *entire grid* of Minervini/RS/ATR variants we test as the universe and report the SPA-adjusted p-value of the *chosen* config, plus a hard **post-2010 OOS holdout** the optimizer never sees.

**Bailey & López de Prado, *The Deflated Sharpe Ratio* (2014).** Core result: DSR corrects an observed Sharpe for (a) **number of trials**, (b) **non-normal returns** (skew/kurtosis via the Probabilistic Sharpe Ratio), and (c) track-record length — "a backtest where the researcher has not controlled for the extent of the search is worthless." Crucially it shows the **holdout/k-fold method does *not* prevent overfitting** ("apply holdout 20 times and false positives are *expected*"). This both validates and challenges us: our PurgedKFold is correct for *leakage* but is **not** a defense against *selection* across many strategy configs. **We are currently doing something the paper says is insufficient** — relying on OOS PurgedKFold probs as if they certify the strategy. Improvement: add `backtest/deflated_sharpe.py` computing PSR + DSR, and require the scorecard's "Deflated Sharpe" point to consume the **actual trial count N** (every grid cell, every feature-set tried), not a hand-wave.

**Bailey-Borwein-López de Prado, *Probability of Backtest Overfitting* (PBO/CSCV).** Core result: Combinatorially-Symmetric Cross-Validation estimates the **probability that the IS-best strategy underperforms the OOS median**. In a "full overfit" null (N strategies all true-Sharpe 0), **PBO ≈ 1**; degrees of freedom behave like regression (overfit risk rises with N, falls with T). Provides the *diagnostic* DSR can't: it tells us whether our *selection procedure itself* is fragile. Improvement: add `backtest/pbo.py` (CSCV) and surface PBO and the **IS-vs-OOS performance-degradation slope** as a scorecard line item; gate any strategy promotion on PBO < 0.5.

**Brown-Goetzmann-Ibbotson-Ross, *Survivorship Bias* (1992).** Core result: truncating a sample by survival makes the **volatility–return relationship masquerade as performance persistence** — survivorship alone can manufacture "hot hands" out of pure noise, strong enough to explain published predictability. Directly validates the scorecard's survivorship-bias point and our point-in-time discipline. **Flags a concrete risk for `features/` and `factors/`**: cross-sectional RS rank and any universe we build from *currently-listed* tickers is survivor-biased; delisted/dead names must be in-universe at each date. Improvement: enforce **point-in-time universe membership** (include delisted equities) in the data layer feeding RS ranking, IC validation, and any future EDGAR/fundamentals join — and document it as a hard precondition in `factors/`.

## THEME TAKEAWAY — the 3 highest-value moves

1. **Build a multiple-testing gate in `backtest/` and wire it into the scorecard.** Implement **Hansen's SPA** (preferred over White's RC) over the *full grid* of strategy configs we try, plus **DSR/PSR** and **PBO (CSCV)**. The scorecard's "Deflated Sharpe" point must take the real trial count N as input. This is the theme's loudest message: **un-deflated, un-snooping-adjusted Sharpes from a parameter search are worthless.**

2. **Stop treating PurgedKFold OOS probs as overfitting protection.** Per DSR/PBO, purging fixes *leakage*, not *selection bias*. We need a layer above CV: log every trial across `ml/` (LightGBM hyperparams, feature subsets) and `backtest/` (rule thresholds), feed N into DSR, and report PBO. Add a **frozen, never-optimized post-2010 holdout** that the meta-labeler and rule grid never touch.

3. **Make the universe point-in-time / survivorship-free before scaling `factors/`.** Cross-sectional RS, rank-IC validation, and QMJ/Fama-French ports are all corrupted by a survivor-only universe (BGIR: survival *creates* spurious persistence). This is cheap to get right now and very expensive to retrofit — it gates the credibility of every cross-sectional factor we add.

Files to add: `backtest/reality_check.py` (or `spa.py`), `backtest/deflated_sharpe.py`, `backtest/pbo.py`; a trial-registry hook in `ml/` and the rule grid; a point-in-time universe contract in the data layer feeding `features/` and `factors/`.


---

# 附錄 C — 組合與部位

# Portfolio Construction & Capital Allocation: What This Theme Means for Our Quant Engine

Six papers, read from primary source (DeMiguel-Garlappi-Uppal and Cover via OCR of scanned originals; the rest via text layer). This theme speaks almost entirely to our **planned `portfolio/` module** (PyPortfolioOpt MVO / risk-parity) and to position **sizing in `ml/`** — and it carries one strong warning about what *not* to build.

## Paper-by-paper

**Markowitz, "Portfolio Selection" (1952).** Core: rejects "maximize discounted expected return" because it never implies diversification; replaces it with the expected-return–variance (E-V) rule, where the efficient set trades mean against variance and *covariances* (not just individual variances) drive diversification benefit. Validates: our cross-sectional thinking — Minervini RS is a cross-sectional ranking, and E-V says the *covariance structure* of the selected names, not their individual merit, determines portfolio risk. Challenges: nothing we built, but exposes a gap — we have no covariance-aware sizing; the rule's whole point is that picking good names ≠ a good portfolio. Improvement: `portfolio/` must consume a covariance matrix Σ, not just expected-return scores, so correlated Minervini winners (often same sector/factor) don't concentrate risk.

**Michaud, "The Markowitz Optimization Enigma" (1989).** Core: MV optimization is an **"estimation-error maximizer"** — it overweights assets with overestimated returns / underestimated variance / spurious negative correlation, so **unconstrained MV can be inferior to equal-weighting** out of sample. Validates: our entire rigor scorecard philosophy (look-ahead, out-of-sample). Challenges: any plan to drop raw sample-MVO into `portfolio/`. Improvement: never ship unconstrained MVO; require constraints (box/turnover) and treat resampling/robust MVO as the baseline, not vanilla MVO.

**DeMiguel-Garlappi-Uppal, "Optimal Versus Naive Diversification" (2009).** Core: across **14 models and 7 datasets, none consistently beats naive 1/N** on Sharpe, certainty-equivalent return, or turnover; the estimation window needed for sample-MVO to beat 1/N is ~**3,000 months for 25 assets, ~6,000 for 50**. Validates: Michaud, and our skepticism of over-engineered estimation. Challenges: the assumption that a fancy `portfolio/` optimizer adds value — empirically it usually doesn't at our asset counts. Improvement: **make 1/N the mandatory benchmark in `backtest/`**; any optimizer must beat equal-weight *net of turnover* on PurgedKFold-style OOS before it's allowed to size live positions. This is a new scorecard line.

**Ledoit-Wolf, "Honey, I Shrunk the Sample Covariance Matrix" (2004).** Core: the sample Σ is "estimated with a lot of error" when N approaches/exceeds T; shrink it toward a structured target (here the **constant-correlation** model) with an analytically optimal intensity δ*. Result: shrinkage gives the **highest information ratio and lowest realized volatility in all tested scenarios**. Validates: directly answers Michaud/DGU — it's the cheap, CPU-friendly fix for the input that breaks MVO. Challenges: nothing; complements. Improvement: if `portfolio/` does *any* Σ-based optimization (MVO, min-variance, risk-parity), the covariance estimator must be **Ledoit-Wolf shrinkage** (constant-correlation or LW2020 nonlinear), never raw sample Σ. `sklearn.covariance.LedoitWolf` is one import — zero infra cost.

**Kelly, "A New Interpretation of Information Rate" (1956).** Core: betting to **maximize G = E[log(wealth)]** (fraction = edge/odds for a binary bet) makes capital grow at the maximal exponential rate and, in a non-terminating game, **dominates any other strategy with probability one**; betting full-bankroll maximizes expected wealth but goes broke a.s. Validates: our `ml/` meta-labeling design — LightGBM already produces the OOS probability p that Kelly needs to *size* (not just gate) the bet. Challenges: any plan to size positions by a fixed fraction or by raw signal strength. Improvement: add **Kelly (and fractional/half-Kelly) sizing** to `ml/` driven by meta-label probability and the triple-barrier payoff ratio b — this is exactly de Prado's "bet sizing from predicted probabilities."

**Cover, "Universal Portfolios" (1991).** Core: a performance-weighted average over *all* constant-rebalanced portfolios is "universal" — with **no statistical assumptions about the market** (it explicitly allows 1929/1987 crashes), it achieves the same asymptotic growth rate as the best constant-rebalanced portfolio chosen in hindsight, with (1/n)·ln(S*ₙ/Sₙ)→0. Validates: the regret/robustness mindset behind our walk-forward discipline. Challenges: nothing we built, but it's an alternative to optimization entirely. Improvement: a low-priority, no-estimation **online-allocation baseline** for `portfolio/` — useful precisely because it needs no Σ and no μ; treat as a research benchmark, not a core dependency.

## Theme takeaway — the 2-3 highest-value moves

1. **Do NOT build a naked MVO optimizer; gate `portfolio/` behind a 1/N hurdle.** Michaud + DeMiguel-Garlappi-Uppal are unambiguous: at our likely asset counts (dozens of Minervini names), sample-MVO is an estimation-error maximizer that loses to equal-weight OOS. Add an **equal-weight benchmark as a hard scorecard line**: an optimizer ships only if it beats 1/N net of turnover under walk-forward. Start with **risk-parity / min-variance**, not max-Sharpe MVO (avoids the noisy μ estimate entirely — the input DGU shows is hopeless).

2. **Whenever you touch a covariance matrix, use Ledoit-Wolf shrinkage — never raw sample Σ.** This is the single cheap fix (one `sklearn` import, CPU-trivial) that makes any Σ-based step in `portfolio/` defensible. Flag this as a build constraint up front so risk-parity/min-variance get shrunk inputs from day one.

3. **Wire Kelly bet-sizing into `ml/` off the meta-label probability.** We already produce OOS PurgedKFold probabilities and triple-barrier payoff ratios — that's everything Kelly needs. Use **fractional/half-Kelly** (full Kelly is too aggressive given estimation error — the same DGU/Michaud lesson applied to sizing) to convert the rule's binary side into a sized position. This is higher-leverage and cheaper than a full MVO stack.

**One flag on current practice:** nothing we've already built is *wrong* by these papers — but our roadmap line "PyPortfolioOpt MVO" is a trap if taken literally. Recast `portfolio/` around **shrunk-covariance risk-parity/min-variance + a 1/N benchmark + Kelly sizing**, and demote max-Sharpe MVO to an also-ran that must earn its place. Cover's universal portfolio is an optional assumption-free benchmark, not a core build.

*Note: two papers (DeMiguel-Garlappi-Uppal, Cover) are scanned image PDFs with no text layer; I extracted them via Windows OCR (WinRT PdfDocument render + Windows.Media.Ocr) — numbers like the 3,000/6,000-month estimation windows are corroborated from the OCR'd abstract.*


---

# 附錄 D — 執行與微結構

# Optimal Execution Theme — What It Means for Our Quant Engine

This theme is the academic foundation of **transaction-cost-aware trading**. It maps directly onto our *planned* `execution/` module and forces changes to `backtest/` and the `rigor scorecard`. None of it touches our signal/alpha logic — it governs how a signal becomes fills.

## Kyle (1985) — "Continuous Auctions and Insider Trading"
**Core result.** A linear equilibrium where price impact is governed by a single constant, **Kyle's lambda (λ)**: the price moves λ per unit of net order flow, so **market depth = 1/λ**, with λ ∝ √(noise-trading variance / private-information variance). Half of private information is impounded into price each auction; prices follow Brownian motion and impact is *permanent and linear*.

**Validates / challenges us.** Validates the *premise* that trading moves price and that impact scales with order size relative to liquidity (volume). It challenges any backtest that fills at the close/VWAP with only a flat bps cost — Kyle says impact is structural, proportional to order/ADV, not a fixed haircut. Our `rigor scorecard` "costs/slippage" line currently has no λ-style size-dependent term.

**Concrete improvement.** Add a **Kyle-λ permanent-impact estimator** to `execution/`: λ ≈ (daily σ) / (daily $volume), i.e. an Amihud-illiquidity proxy per name. Feed this into `backtest/` so cost scales with `trade_$ / ADV`, not a constant.

## Bertsimas–Lo (1998) — "Optimal Control of Execution Costs"
**Core result.** Best execution = the dynamic program (Bellman) that minimizes *expected* cost of trading a block over N periods. With an arithmetic random walk + linear permanent impact, the optimum is the **naive equal-slice (TWAP) strategy**; informative state (private info, serial correlation) adds a linear "shifting" correction on top of equal slices. They cite Perold's *implementation shortfall* — a Value Line paper portfolio beat the market ~20%/yr but the live fund only 2.5%/yr, the gap being execution cost.

**Validates / challenges us.** This is the rigorous justification for child-order slicing and for using **implementation shortfall as our execution benchmark** — directly relevant to closing the paper-vs-live gap our `rigor scorecard` is meant to police. It challenges nothing we built, but exposes a gap: we have no execution cost model at all yet, so our backtested Sharpe is the "20%/yr paper portfolio."

**Concrete improvement.** Adopt **TWAP/equal-slice as the default execution baseline** in `execution/` (it is provably optimal under the simplest realistic assumptions — cheap, no tuning), and add an **implementation-shortfall accounting line** to `backtest/` (arrival price vs. realized fills) as the headline cost metric.

## Almgren–Chriss (2000) — "Optimal Execution of Portfolio Transactions"
**Core result.** Adds **risk** to Bertsimas–Lo: minimize cost *variance* plus expected cost, producing an **efficient frontier** of liquidation trajectories and a closed-form **trade half-life** τ = 1/κ, where κ² ≈ (risk-aversion × σ²)/(temporary-impact param). τ is independent of the imposed deadline T — it's the *intrinsic* time-scale set by volatility, liquidity, and risk aversion. More volatile/illiquid ⇒ trade faster; this is impossible in a risk-neutral (Bertsimas–Lo) model.

**Validates / challenges us.** Strongly validates our existing instinct toward **regime/volatility-aware behavior** — Almgren–Chriss say the *speed* of trading should be a function of σ and liquidity, exactly the variables our `features/` panel already computes (ATR, rvol, dollar-volume). It gives us a principled "L-VaR / liquidation-cost" number to add to risk reporting.

**Concrete improvement.** Implement the **Almgren–Chriss trajectory + trade half-life** in `execution/`, parameterized off our existing `features/` (ATR→σ, dollar-volume→impact). Surface τ as a **per-name "max sensible position / time-to-exit" liquidity check** in `portfolio/` — a position whose AC half-life exceeds your rebalance horizon is too big.

## Obizhaeva–Wang (2013) — "Optimal Trading Strategy and Supply/Demand Dynamics"
**Core result.** The optimum depends **not on static depth/spread but on resilience** — the *speed the limit-order book refills* after a trade. Optimal shape: a **large initial trade, a stream of small trades, then a final block** — not equal slices. Cost savings vs. TWAP grow with book recovery time: **0.33% (0.9-min recovery half-life) → 1.88% (5.4 min) → 7.41% (27 min)** for an order 20× depth.

**Validates / challenges us.** **Challenges the TWAP-is-optimal conclusion** of Bertsimas–Lo / Almgren–Chriss: equal-slicing is only optimal under static impact; with realistic finite resilience it leaves up to ~7% on the table. For our context this is a caution, not a build order — modeling resilience needs intraday LOB data we don't have under the <$15/mo constraint.

**Concrete improvement.** Don't build an LOB simulator. Instead encode resilience as a **single "recovery half-life" sensitivity parameter** in the `execution/` cost model and the `rigor scorecard` — i.e., stress-test net Sharpe under fast vs. slow book recovery so a strategy that only survives on optimistic intraday liquidity is flagged.

---

## THEME TAKEAWAY — the 2–3 highest-value moves

1. **Stop reporting frictionless Sharpe; adopt implementation-shortfall accounting (highest value).** All four papers, anchored by Bertsimas–Lo's Perold example (20%/yr → 2.5%/yr), say the paper-vs-live gap *is* execution cost. **Flag as currently-wrong:** if `backtest/` (vectorbt) fills at close with a flat bps cost and the `rigor scorecard` treats "costs/slippage" as a constant, we are overstating returns in exactly the way these papers warn against. Replace the flat haircut with a **size-dependent cost = spread/2 + λ·(trade_$/ADV)**, λ from Kyle/Amihud.

2. **Build `execution/` as a tiered, cheap model — TWAP baseline + Almgren–Chriss half-life — not an LOB simulator.** Bertsimas–Lo make equal-slice the provably-optimal, zero-tuning default; Almgren–Chriss add the volatility/liquidity-scaled **trade half-life τ = 1/κ** computed from `features/` we already have. This is CPU-cheap, point-in-time-clean, and gives `portfolio/` a hard **liquidity/capacity constraint** (position too big if AC half-life > rebalance horizon) — important once MVO/risk-parity sizing comes online and can pick large illiquid weights.

3. **Treat resilience (Obizhaeva–Wang) as a stress-test knob, not a module.** Their ~7% cost swing across recovery half-lives means our headline net-Sharpe should be reported across a fast/slow-resilience band. Add one resilience-sensitivity row to the `rigor scorecard` so capacity claims aren't hostage to optimistic liquidity assumptions.

**One scope caution:** this theme governs `execution/`, `backtest/`, `portfolio/` capacity, and the scorecard — it says **nothing** about `labeling/`, `features/`, `factors/`, or `ml/` alpha generation, and none of these papers challenge our de Prado / IC-validation / meta-labeling stack. The single thing they say we may currently be doing *wrong* is **frictionless or flat-cost backtesting**; everything else is additive.

Source PDFs (all in `C:\Users\Romarin\Documents\Quant Analysis`): `Continuous Auctions and Insider Trading ... Kyle ... 1985.pdf`; `Optimal control of execution costs ... Bertsimas; Lo ... 1998.pdf`; `Almgren & Chriss (2000) — Optimal Execution of Portfolio Transactions.pdf`; `Optimal trading strategy and supply_demand dynamics ... Obizhaeva; Wang ... 2013.pdf`.


---

# 附錄 E — 時序/均值回歸/波動

# Theme: Time-Series Econometrics & Statistical-Arbitrage Foundations — Implications for trading-analysis

*Six papers. Four read directly from text (Lo-MacKinlay, Gatev et al., Bollerslev, Hurst-Ooi-Pedersen); two are scanned image-only PDFs with no extractable text (Engle 1982, Brock-Lakonishok-LeBaron 1992) — summarized from established knowledge and flagged as such.*

## Lo-MacKinlay (1988) — "Stock Prices Do Not Follow Random Walks" (Variance Ratio)
**Core result.** The variance-ratio test rejects the random walk for weekly returns 1962-1985. Equal-weighted CRSP index VR rises monotonically above 1 (1.30 at q=2 to ~2.0 at q=16); weekly first-order autocorrelation is **+30%** for the index — *positive* serial correlation (momentum) at the index level, driven by small caps, while *individual* stocks show negative autocorrelation. Not explained by infrequent trading or time-varying volatility.
**Validates / challenges us.** Validates our `features/` mean-reversion pack (Hurst, half-life, **variance-ratio**) as the canonical leak-free way to test for trending vs. mean-reverting structure. Crucially it *qualifies* it: VR>1 at the portfolio level but VR<1 for single names means a VR feature is regime/cross-sectionally dependent — a single global VR mislabels the structure.
**Concrete improvement.** Make the VR feature explicitly Lo-MacKinlay heteroskedasticity-robust (the z\*(q) statistic), compute it per-asset *and* report its sign distribution; expose `q` (2/4/8/16) as a feature-config parameter rather than one fixed horizon. Use the *robust* z\*(q), not the homoskedastic one — the homoskedastic version over-rejects.

## Brock-Lakonishok-LeBaron (1992) — Simple Technical Trading Rules *(scanned PDF, from knowledge)*
**Core result.** On the DJIA 1897-1986, simple moving-average (VMA) and trading-range-breakout (TRB) rules have predictive power: buy signals generate ~12% annualized returns vs. sell signals that are *negative*, and buy-day return variance is lower than sell-day variance — inconsistent with a constant-risk random walk. Returns conditioned on signals differ significantly via bootstrap (AR(1)/GARCH-M nulls).
**Validates / challenges us.** Directly validates the *premise* of `minervini_trend` (MA-relationship rules carry information) and our bootstrap/`rigor scorecard` instinct. **But it is the canonical data-snooping cautionary tale** — Sullivan-Timmermann-White later showed BLB's specific rules don't survive a full-universe data-snooping correction. This is the single most important flag for us.
**Concrete improvement / flag.** Any rule we tune (MA windows, RS thresholds, the 8 Minervini criteria) must be scored against a **data-snooping-adjusted** null — add White's Reality Check / Hansen's SPA to the `rigor scorecard` alongside Deflated Sharpe. BLB's bootstrap nulls (AR(1), GARCH-M) are exactly the right benchmark models to simulate against when bootstrapping `backtest/` signal returns.

## Gatev-Goetzmann-Rouwenhorst (2006) — Pairs Trading
**Core result.** Distance-based pairs trading (match on minimum sum-of-squared-deviations of normalized prices, open at **2σ** divergence, close on convergence) earns **~11% annualized excess return** on self-financing top-pairs portfolios, 1962-2002, exceeding conservative transaction costs and *distinct* from simple reversal/contrarian profits; profits load on an unidentified common latent factor.
**Validates / challenges us.** This is a *new module*, not yet built. It's the cleanest cross-sectional complement to our trend engine — market-neutral, exploits the mean-reversion structure our Hurst/half-life features already detect. The 2σ-entry/convergence-exit is a textbook triple-barrier setup.
**Concrete improvement.** Add a `strategies/pairs_trading` module: distance-metric pair selection on a 12-month formation window, 6-month trading window, **2σ entry / 0σ exit / time-stop** mapped onto our existing `labeling/` triple-barrier (the σ-bands *are* the horizontal barriers). Critically — they note profits decayed post-2002 (capacity/crowding); our `rigor scorecard` must include an out-of-sample/post-publication decay check.

## Engle (1982) — ARCH *(scanned PDF, from knowledge)*
**Core result.** Introduced Autoregressive Conditional Heteroskedasticity: conditional variance modeled as a function of past squared errors, with an LM test for ARCH effects, applied to UK inflation uncertainty (Nobel 2003). Volatility clusters and is forecastable even when returns are not.
**Validates / challenges us.** Our `features/` ATR/rvol are crude realized-vol proxies; ARCH says conditional variance is *predictable*, which matters for two of our modules. **Flag:** any bootstrap or significance test in `rigor`/`backtest` that assumes homoskedastic i.i.d. returns is mis-specified — return volatility clusters, so block/wild bootstraps are required.
**Concrete improvement.** Add an ARCH-LM test as a diagnostic in the `rigor scorecard` (confirms heteroskedasticity → forces robust standard errors and the heteroskedasticity-consistent Lo-MacKinlay VR statistic above).

## Bollerslev (1986) — GARCH
**Core result.** Generalizes ARCH by letting current conditional variance depend on past conditional variances (GARCH(1,1)), giving a parsimonious long-memory volatility model — the workhorse of modern vol forecasting.
**Validates / challenges us.** Gives us the principled vol estimate that `portfolio/` (PLANNED risk-parity / MVO) and position-sizing need — a GARCH conditional σ is far better than trailing-window std for forward risk. Feeds directly into `ml/` meta-labeling: position size should scale by *forecast* volatility.
**Concrete improvement.** Add a lightweight `features/garch_vol` (GARCH(1,1) one-step-ahead σ via `arch` package, point-in-time/expanding-window fit only) as (a) the vol target for risk-parity sizing in `portfolio/`, and (b) a conditioning feature for `ml/` meta-label sizing. This is CPU-cheap and fits the <$15/mo constraint.

## Hurst-Ooi-Pedersen (2017) — A Century of Trend-Following
**Core result.** A volatility-scaled time-series-momentum strategy (equal-weight 1/3/12-month signals, **10% annualized vol target**, 67 markets) is profitable in **every decade from 1880-2016** — the first ~100 years being pure out-of-sample. It earns its best returns in **bear markets / equity drawdowns** (the "TSMOM smile") and works best in low-correlation regimes; performance survives 2-and-20 fees and transaction costs but deteriorates with signal lagging (esp. short horizons).
**Validates / challenges us.** Strongly validates trend-following as a genuine, non-data-mined premium and validates our 200-SMA/HMM **regime gate** (trend pays in trending regimes). Two design lessons for us: (1) **volatility-target position sizing** — they size every position to equal vol and scale the book to 10% — which our engine does not yet do; (2) signal lag *materially* erodes returns, validating our 1-bar lag as honest but warning us not to add more.
**Concrete improvement.** Add **vol-target sizing** to `portfolio/`: scale each `minervini_trend` position to a constant per-name vol (use the GARCH σ above) and target a book-level vol — this is the highest-leverage portfolio change available. Add a "crisis-alpha" panel to `backtest/` reporting conditioned on equity-bear periods.

---

## Theme Takeaways — highest-value actions

1. **Add data-snooping-robust significance to the `rigor scorecard` (do this first).** BLB is the field's canonical example of rules that look great and then fail White's Reality Check / Hansen's SPA. We currently have Deflated Sharpe; **add White Reality Check + Hansen SPA** as siblings. Every tuned threshold in `minervini_trend` and any future pairs/momentum rule must clear this bar. *Flag: bootstrapping returns under an i.i.d. null is wrong — Engle/Bollerslev say returns are heteroskedastic, so use block/wild bootstrap and GARCH/AR(1) nulls (BLB's own choice).*

2. **Make volatility a first-class, forecasted quantity — then size by it.** Replace trailing-std risk with a CPU-cheap **GARCH(1,1) conditional σ** (`arch` library, point-in-time fit) feeding (a) **vol-target position sizing** in `portfolio/` (the core lesson of Hurst-Ooi-Pedersen's 10%-vol book) and (b) `ml/` meta-label sizing. This single change connects four modules and is the highest-ROI improvement.

3. **Build the pairs-trading module as the market-neutral complement.** Gatev et al.'s distance-match + 2σ-entry/convergence-exit maps cleanly onto our existing triple-barrier `labeling/` and Hurst/half-life `features/`. Use Lo-MacKinlay's **heteroskedasticity-robust variance ratio** (per-asset, multiple q, with sign distribution) as the gating feature to decide trend-vs-revert — and bake post-publication **return-decay checks** into `rigor` for both pairs and trend (both papers show alpha decays after publication/crowding).

*Source files (all in `C:\Users\Romarin\Documents\Quant Analysis`): Lo-MacKinlay, Gatev-Goetzmann-Rouwenhorst, Bollerslev, and Hurst-Ooi-Pedersen PDFs were text-extractable and read directly. The **Engle 1982 (ARCH)** and **Brock-Lakonishok-LeBaron 1992** PDFs are scanned image-only (zero extractable text, no OCR tooling installed) — their summaries draw on established knowledge of these seminal papers and should be spot-verified if exact figures are needed.*


---

# 附錄 F — meta-labeling 對抗審查

# Adversarial Review: `ml/meta_labeling.py` (LEAKAGE / correctness)

Scope: `meta_labeling.py` with `labeling/cv.py`, `labeling/triple_barrier.py`, `features/build.py`, `tests/unit/test_meta_labeling.py`. I loaded the modules directly and ran the duplicate-timestamp, fold-boundary, embargo-`searchsorted`, and sort-alignment cases to verify each claim.

## CRITICAL / correctness

**C1 — `y`/`prob` misalignment when caller passes an unsorted dataset (correctness, silent metric corruption).** `meta_labeling.py:103` `walk_forward_meta_prob` internally re-sorts (`ds = dataset.sort_values("t_event").reset_index(drop=True)`) and returns a Series in **sorted positional order**. But `evaluate_meta` (`:121`) reads `y = dataset["y"].to_numpy()` from the **caller's** order and pairs it positionally with `prob`. I confirmed: caller `y=[1,0,1]` vs internal sorted `[0,1,1]` — every metric (AUC, lift, hit-rate) is then computed on mismatched (y, prob) pairs. It only "works" today because `build_meta_dataset` happens to return sorted (`:83`), so the tests never exercise an unsorted caller. This is a leakage-grade landmine: it produces plausible-but-wrong numbers, not a crash. Fix: have `walk_forward_meta_prob` return the prob aligned to the **input** index (don't reset; assign back into a Series on the original index), or return the sorted dataset alongside the probs and make `evaluate_meta` consume that exact object. Minimum: assert `dataset["t_event"].is_monotonic_increasing` at the top of both functions.

**C2 — features are NOT re-validated as point-in-time at the event bar inside `build_meta_dataset`; trust is fully delegated.** `meta_labeling.py:70-72` pulls `feature_panel[symbol].set_index("ts")[FEATURE_COLUMNS]` and `bins.join(feats, how="inner")` on the **event timestamp**. That correctly selects the feature row *at* the event bar (no future), and `build_features` is genuinely causal (rolling/shift/`min_periods`, no centering or full-sample fit — verified in `build.py`). So the value at the event bar is point-in-time. The gap: the feature panel can be passed in pre-built (`feature_panel` arg, `:41`), and there is no check that its `ts` grid matches `close.index` or that it wasn't built on a different (future-inclusive) slice. Severity is correctness-medium because the default path is safe; flagging because the public API lets a caller inject a leaky panel undetected. Fix: when `feature_panel` is supplied, assert its per-symbol `ts` is a subset of `close.index` and document that it must come from `build_features` (causal).

## Leakage (the pooled-duplicate-timestamp question) — investigated, found CORRECT

**Pooling across symbols with duplicate `t_event` does NOT defeat the purge.** I built a pooled dataset with interleaved duplicate timestamps and forced `np.array_split` to cut *inside* a duplicate block. The overlap purge at `cv.py:54` (`overlap = (starts <= test_t1_max) & (ends >= test_t0)`) is a pure **timestamp** comparison, so a train row sharing a test row's timestamp (different symbol) is purged regardless of its array position — I confirmed zero shared `t_event` between train and test across all folds in every constructed case. This is the right design and it sidesteps the classic "searchsorted-of-a-t1-value conflates time with position" bug the comment at `:51-53` calls out. Confirmed correct.

**`X.index.equals(t1.index)` holds with duplicate datetimes.** Verified `True` on a non-unique index; `Index.equals` is positional, so duplicates are fine (`cv.py:36`).

**Embargo `searchsorted` is safe on the sorted, non-unique event index.** `cv.py:58` anchors on `test_t1_max` into `self.t1.index`. The index is sorted after `build_meta_dataset` (C1 caveat aside), so `searchsorted(side="right")` returns correct positions on duplicates (I confirmed `01-03→5`, future→`n` → empty embargo). Correct.

## Walk-forward / determinism

**W1 — one-OOS-prob-per-row only holds if folds are exhaustive AND disjoint; rows in a one-class or empty-train fold get NaN, which is correct, but the contract is unstated (minor).** `meta_labeling.py:110-115`: `np.full(len(ds), np.nan)` then `oos[test_idx] = ...`. PurgedKFold test sets partition all positions, so every row is in exactly one test fold; rows whose fold can't train stay NaN and are dropped by `evaluate_meta`'s `valid = ~np.isnan(prob)` (`:123`). Correct and leak-free. Confirm: fold-skip on `len(np.unique(y[train_idx])) < 2` (`:111`) is the right guard — fitting a one-class model would emit a degenerate constant prob. Fix (minor): document that coverage < 100% is expected near series ends.

**W2 — LightGBM determinism on tiny folds (minor).** `META_DEFAULT_PARAMS` sets `random_state=0`, `n_jobs=1`, `verbosity=-1` (`:24-35`) — good, single-thread + fixed seed is reproducible. But `subsample=0.8`/`colsample_bytree=0.8` with `min_child_samples=10` on a fold that may have <50 events can yield unstable trees, and `subsample` has **no effect without `subsample_freq>0`** in LightGBM (silent no-op — row subsampling is simply never applied). Fix: set `subsample_freq=1` if you actually want bagging, or drop `subsample` to avoid implying randomness that isn't happening.

## `evaluate_meta`

**AUC and lift are computed on OOS probs only — CORRECT, no survivorship/selection bias in the lift calc.** `:123` masks to non-NaN (OOS) rows; AUC uses `roc_auc_score(y_v, prob_v)` over those same OOS rows (`:132`); `rule_hit` is the base rate over **all** valid events and `meta_hit` over `prob_v > threshold` (`:125-127`). The lift is a fair within-OOS comparison; no future label leaks in. One nit (minor): `lift = meta_hit - rule_hit` compares the filtered subset's win-rate to the *full* OOS base rate — that is the intended de Prado framing, but it is **not** a measure of edge over a random filter taking the same fraction; consider also reporting precision-at-coverage so a high-threshold cherry-pick can't masquerade as lift. AUC guard `len(np.unique(y_v)) == 2` (`:129`) correctly avoids `roc_auc_score` raising on single-class OOS.

## Confirmed-correct (one line each)
- `triple_barrier_events` sets `t1` = earliest of vertical/SL/PT via `min(axis=1)` skipping NaT (`triple_barrier.py:85`) — label end-time is the true first touch.
- `get_bins` flips return by `side` and zeros the bin on non-positive return for meta-labeling (`:100-103`) — correct {0,1} meta-target.
- `side = pd.Series(1.0, index=t_events)` (`meta_labeling.py:65`) correctly encodes the rule's long-only side; direction is never learned.
- `direction_pivot[symbol].reindex(close.index).fillna(0)` then `>0` (`:60-61`) — events only on rule-fire bars; the rule's signals are already 1-bar-lagged upstream.
- `vol_span=50` EWMA target is causal (`ewm(...).std()`, `volatility.py:14`).

**Top priority: fix C1** (alignment) — it can silently invalidate every reported metric the moment a caller doesn't pre-sort.