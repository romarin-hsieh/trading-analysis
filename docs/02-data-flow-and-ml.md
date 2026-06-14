# 資料流設計 + 便宜 ML 方案（M0 設計專場）

> ultracode workflow（2026-06-15）。輸入：design-brief.md。含對 labeling 模組的對抗式審查。

# Integrated Design Summary: Three-Repo Stock-Analysis System

## 1. Data-Flow Design (cross-ref: Section A)

```
trading-data ──raw parquet + opinion JSONL──▶ trading-analysis ──contract JSON──▶ investment-dashboard
 (ingest/SoR)      R2 + git mirror              (engine / contract SoT)   atomic export      (Vue3 static)
 2×/day fast                                     1×/day after slow ingest                     client read
 1×/day slow         as_of stamped here ───────▶ as_of propagated in rows ─▶ as_of<=D snapshot
```

One direction, no cycles. **Boundary A** (`trading-data` → `trading-analysis`): two physical mirrors of one logical store — `data/latest/` git tree (versioned cold SoR) and identical bytes in R2 (`r2://td-bucket/latest/`, zero-egress hot serving), both partitioned, <1 GB, single-writer. Hot PIT tables (`insider_txns`, `congress_txns`, `superinvestor_holdings`, `events_8k`, `xbrl_eps`, `analyst_ratings`, `tw_chips`) are parquet keyed on a **load-bearing `as_of`** (filing/disclosure instant), plus `opinion_event.jsonl` and a `manifest.json` freshness/integrity index (rows/sha256/`as_of_max` per table). An 18-month raw audit trail lives in git only, not R2. trading-analysis reads R2 parquet through the existing `DuckStore` pattern — `duckdb` httpfs `read_parquet('r2://…')` registered as views, with an `rclone`-backed local cache invalidated by `manifest.json` sha.

**Boundary B** (`trading-analysis` → dashboard): three contract artifacts emitted atomically by `api.export_dashboard_json()` (`*.tmp` → `os.replace`, gated by `DashboardStatus.model_validate()` — invalid never publishes): `dashboard_status.json` (`{meta, updated_at, global_regime, data[]}`, each entry carrying required comet keys `coordinates{x_trend,y_momentum,z_structure}` + `trace[30]` + `sector_trace[30]`, plus additive `scores{}`/`opinions[]`), `opinions.json`, and `creator_scorecards.json`. The dashboard reads-by-key with **no Zod** on the status file, so additive keys are zero-risk.

The spine of the whole design is **PIT `as_of` propagation**: ingest stamps `as_of` at publication (congress uses `disclosure_date`, not `txn_date` — the #1 look-ahead trap); every intermediate table (`labels`, `features`, `factor_scores`, `signals`, `opinion_event`) is keyed `(ticker, as_of, …)`; backtests select `WHERE as_of <= D`; export emits an `as_of <= D` snapshot that re-runs reproducibly — which is exactly what makes the creator scorecards honest. Degradation is graceful: per-source isolation, stale-but-valid last-known-good from git history, partial-contract export with `None` defaults, and the comet math (ported `daily_update.py`) never silently breaks because its required keys don't depend on alt-data.

## 2. Cheap-ML Verdict (cross-ref: Section C)

**The concrete $0-marginal path:** train a **LightGBM meta-labeling classifier** on local CPU (the inner loop — boosting on daily-bar tabular features trains in <1 min; no GPU needed), mirror to **Kaggle** (~30 GPU-hr/wk, 12-hr sessions) only for occasional heavier sweeps or a scheduled monthly retrain. Serialize via `joblib` or export to **ONNX** (`onnxmltools` + `onnxruntime` CPU) and commit `models/meta_labeler_v{N}.onnx` + a `model_card.json` (train window, feature list, CV scores, `as_of`) into the contract repo. **Daily inference runs inside GitHub Actions on CPU at $0** (public-repo runners unmetered; private gets 2,000 free Linux min/mo). Retraining is a separate, occasional job; daily inference reuses the pinned artifact — deterministic and auditable. Recurring infra cost ≈ **$0**, leaving the full <$15/mo budget for data/LLM, not compute. Trees decisively beat deep nets on heterogeneous tabular finance data and yield native importances that feed the MDI/MDA pruning.

**The meta-labeling-on-Minervini plan:** the Minervini/CAN SLIM rule (already +1-bar-lagged, regime-gated by 200-SMA/HMM) supplies the **side** (`+1`); ML never picks direction. Each rule-fire → `t_events` → `triple_barrier_events(side=rule_side, target=ewma_vol, pt_sl, num_bars)` → `get_bins` emits the `{0,1}` meta-label (did the rule make money before a barrier?). LightGBM's `predict_proba` becomes both **filter** (act if p > threshold) and **sizer** (position ∝ p, Kelly-capped). Validation reuses the existing `PurgedKFold(t1=events.t1, embargo)` walk-forward + **Deflated Sharpe** (deflated for trial count), feature selection inside folds. Reported as rule-alone vs rule×meta-label OOS lift. **Do NOT:** rent cloud GPU, use deep learning on daily bars, depend on free-GPU quotas, run an always-on inference server, let ML pick direction, or use random-split CV / full-dataset selection / undeflated Sharpe.

## 3. Refined Next-PR List (cross-ref: Section B)

M0 is **DONE & committed** (SMA regime gate, Minervini trend rule + RS rating, full labeling module, all wired into `api.backtest_strategy` with green tests). The path walks **features → factors → meta-labeling ML → fundamentals → value rules → alt-data**, each gated by the rigor scorecard.

| PR | Scope | Dep | Effort |
|----|-------|-----|--------|
| **PR-1 ⟵ HIGHEST-VALUE NEXT** | `features/` — breadth indicators (`ta`), mean-reversion (Hurst/VR/half-life), ADF stationarity filter, MDI/MDA importance, leak-free `build()` | M0 | M |
| PR-2 | `factors/` — Alphalens IC harness (`validate()` gate), qlib Alpha158 port, quantile portfolios | PR-1 | M |
| PR-3 | **Meta-labeling ML** — LightGBM on Minervini side, `api.backtest_meta_labeled` (the strategic payoff) | PR-1, PR-2 | L |
| PR-4 | EDGAR fundamentals connector — PIT `as_of=filed`, `edgartools` wrapper (parallelizable) | — | M |
| PR-5 | `magic_formula` + `graham` value rules, regime-gated, PIT-filtered | PR-4 | M |
| PR-6 | `opinion/`+`signals/` alt-data — insider cluster-buy, PEAD/SUE, congress (`as_of=disclosure_date`) | PR-4 | L |

**PR-1 is the single highest-value next PR**, not PR-3, even though meta-labeling is the real edge upgrade — because meta-labeling is **blocked on a feature matrix X**. M0 gave labels (y) and CV (folds) but no features; PR-2 and PR-3 both consume `features.build()`. Building PR-3 first would force hand-assembling features inline, re-creating the exact leak risk M0 was built to prevent. The load-bearing acceptance test is `test_features_are_point_in_time_leakproof()`: `build(ohlcv)[:T]` must equal `build(ohlcv[:T])` column-for-column — scorecard #1 made executable, inherited by everything downstream.

## 4. Labeling-Review Verdict (cross-ref: Section D)

**Issues by severity, each with its fix:**

**CRITICAL:**
1. **`cv.py:48` — embargo-anchor leakage (top priority).** `max_t1_idx` maps a label-*end-value* into the event-*index* via `searchsorted`, conflating two axes. Whenever `t1` values ≠ event timestamps (i.e. essentially always for real triple-barrier output, where `t1` is a touch time), the embargo anchor silently moves, **under-purging the right edge → leakage.** *Fix:* anchor embargo on test *position* — `max_test_pos = test_indices[-1]; embargo_end_pos = min(max_test_pos + embargo, n-1); purge_end = self.t1.index[embargo_end_pos]` — plus the existing interval-overlap purge.
2. **`triple_barrier.py:30` — vertical-barrier off-by-one.** `end = locs + num_bars` makes the horizon span `num_bars+1` bars inclusive, so every label's horizon (and every `t1` PurgedKFold purges on) is one bar longer than the name promises — a definitional inconsistency that inflates the purge interval. *Fix:* `end = locs + num_bars - 1` if `num_bars` means "bars held", or document it as an offset and fix the test that currently bakes in the +1.
3. **`triple_barrier.py:29` — off-grid `searchsorted` (side='left').** If an event time isn't exactly on the close grid (intraday/holiday gaps, resampled events, duplicate timestamps), the entry bar and vertical barrier silently shift to the next bar. *Fix:* assert event membership, or use `close.index.get_indexer(t_events)` and raise on `-1`.

**Correctness items confirmed RIGHT (no change needed):** first-touch `NaT` handling (`triple_barrier.py:47-48,82` — min skips NaT correctly); `get_bins` label-based reindex alignment (`:91-93`); PurgedKFold left-edge overlap purge (`cv.py:52`) and the clamp itself (`:49`); trend-scanning t-stat math (`:18-32`) and forward-window bound (`:51`); `ewma_vol` (`volatility.py:14`).

**MINOR / EDGE:**
- `triple_barrier.py:75` — meta-labeling (`side is None`) forces symmetric `pt_sl` and **silently discards caller `sl`**. Honor both or document.
- `cv.py:36` — `int(n*pct_embargo)` truncates embargo to 0 for small n (e.g. `0.01, n=50 → 0`). de Prado does the same; flag it.
- `cv.py:41` — degenerate folds can purge **all** train samples → empty train array → opaque downstream error. Add a `len(train)==0` warning.
- `trend_scanning.py:47` — `get_loc` on duplicate index breaks slicing. Assert unique index.

**Overall call: NOT trustworthy as-is for building ML on top — fix the three CRITICALs first, and they are cheap.** This is decisive. The `cv.py:48` embargo-anchor bug is the dangerous one: it silently leaks at the test-fold right edge, which would make every Deflated-Sharpe and OOS number in the PR-3 meta-labeling validation **optimistically biased and untrustworthy** — defeating the entire reason M0 built PurgedKFold first. PR-1 and PR-2 can proceed in parallel (they don't exercise the embargo path heavily), but **the three CRITICAL fixes are a hard prerequisite gate for PR-3.** All three are small, localized, high-confidence edits with clear fixes already specified, and each should land with a regression test (shuffled-label precision collapse for the embargo leak; an explicit bar-count assertion for the off-by-one; an off-grid membership assertion for the searchsorted). Fix them as a tiny `labeling-hardening` PR before — or as the opening commit of — PR-3.


---

# 附錄 A — 資料流架構

# Three-Repo Data Flow Design

`trading-data` (ingest/store) ──raw parquet+JSONL──▶ `trading-analysis` (engine/contract SoT) ──contract JSON──▶ `investment-dashboard` (Vue3 presentation). One direction, no cycles. This goes a layer below the master plan: exact artifacts, schemas, paths, cadence, and `as_of` propagation.

## 1. Artifacts crossing each boundary

### Boundary A — `trading-data` → `trading-analysis`

Two physical mirrors of one logical store (`data/latest/` git tree = versioned cold SoR; same bytes pushed to R2 `r2://td-bucket/latest/` = zero-egress hot serving). Both partitioned, total <1 GB, single-writer (only Actions commits).

**Hot tables** (`data/latest/`, mirrored to R2):

| Artifact | Format | Key columns (the `as_of` is load-bearing) |
|---|---|---|
| `insider_txns.parquet` | parquet | `ticker, code, shares, price, txn_date, filing_date AS as_of, accession` |
| `congress_txns.parquet` | parquet | `politician, chamber, ticker, txn_type, amount_range, txn_date, disclosure_date AS as_of, source` |
| `superinvestor_holdings.parquet` | parquet | `fund, ticker, shares, shares_delta, period_end, filing_date AS as_of` |
| `events_8k.parquet` | parquet | `ticker, item_code, filing_date AS as_of, accession` |
| `xbrl_eps.parquet` | parquet | `ticker, fiscal_period, eps_diluted, filed AS as_of` |
| `analyst_ratings.parquet` | parquet | `ticker, firm, rating, target, publish_date AS as_of` |
| `tw_chips.parquet` | parquet | `ticker, inst_type, net_shares, trade_date AS as_of` (FinMind 三大法人/融券) |
| `opinion_event.jsonl` | JSON Lines | brief §6 row; `published_at == as_of`; `raw_text_ref` points into `raw/`, never the blob |
| `manifest.json` | JSON | `{table: {rows, sha256, generated_at, as_of_max}}` — the freshness/integrity index |

**Raw audit trail** (`data/raw/`, git only, **not** R2 — rolling 18-month window, monthly prune):
```
raw/ohlcv/us/dt=2026-06-14/*.parquet
raw/edgar/form4/dt=2026-06-14/*.json
raw/congress/dt=2026-06-14/*.json
raw/articles/dt=2026-06-14/*.md          # trafilatura markdown + frontmatter
raw/transcripts/raw/<videoId>.json       # captions or home-box Whisper output
```
US OHLCV is the exception to the EDGAR-style PIT tables: it is bar data keyed by trade `ts`, partitioned `dt=`, and consumed the way the existing `DuckStore` already reads parquet.

### Boundary B — `trading-analysis` → `investment-dashboard`

Three contract artifacts, emitted atomically by `api.export_dashboard_json()` (`*.tmp` → `os.replace`; `DashboardStatus.model_validate()` is the gate — invalid never publishes). Written to the dashboard's data lake path / R2 contract prefix:

| Artifact | Path (dashboard side) | Shape |
|---|---|---|
| `dashboard_status.json` | `public/data/dashboard_status.json` | `{meta, updated_at, global_regime, data[]}`; each entry carries the de-facto-required `coordinates{x_trend,y_momentum,z_structure}`, `trace[30]`, `sector_trace[30]`, `ticker/sector/strategy/signal/reason/commentary/price/change_percent/date`, plus additive `scores{}` + `opinions[]` |
| `opinions.json` | `public/data/opinions.json` | denormalized `OpinionEvent[]` feed for the opinion view |
| `creator_scorecards.json` | `public/data/creator_scorecards.json` | per-`source_name` hit-rate/IR/WLO/Sharpe/MDD over 1/5/20/60d |
| `contract/schema/*.schema.json` | vendored in dashboard repo | JSON Schema (build-time CI gate, not runtime) |

The dashboard reads-by-key with **no Zod** on `dashboard_status.json`, so new keys are zero-risk; `meta.version` is echoed through unchanged and our additive semver lives only in `meta.contract_version`.

## 2. `trading-analysis` ingest + intermediate tables

Ingestion side: `data/store.py:DuckStore` already does `duckdb.connect(":memory:")` + `CREATE VIEW … FROM '<glob>'`. Extend that pattern to read trading-data directly: register R2 parquet as DuckDB views via the httpfs extension (`SELECT * FROM read_parquet('r2://td-bucket/latest/congress_txns.parquet')`), with a **local cache** — `rclone copy` (or first-touch download) into `{cache_dir}/td/latest/` so a daily run hits R2 once. `manifest.json` sha drives cache invalidation: unchanged sha = reuse local copy. `opinion_event.jsonl` loads via DuckDB `read_json_auto`.

Intermediate DuckDB tables (materialized in the run, not crossing a boundary):
- `regime_state(date, regime_state, risk_off_prob, cond_vol)` — M0 output, feeds `global_regime`.
- `labels(ticker, as_of, label, t_value, sample_weight)` — triple-barrier/trend-scan.
- `features(ticker, as_of, <ADF-survivor cols>)`.
- `factor_scores(ticker, as_of, name, value, rank, percentile, universe)` → serialized as `FactorScore`.
- `signals(ticker, as_of, strategy, direction, strength, entry, stop, target, reason)` → `Signal`.
- `opinion_event` (the unified table) + per-`source_name` forward-return joins → scorecards.

## 3. Cadence: incremental vs full recompute

| Stage | Repo | Cadence | Mode |
|---|---|---|---|
| RSS detect + EDGAR + Finnhub + FinMind light | trading-data | `ingest-fast.yml` 2×/day | incremental (seen-set diff, append new `dt=` partitions) |
| congress, Dataroma, XBRL, articles, transcripts | trading-data | `ingest-slow.yml` 1×/day (`23 9 * * *`) | incremental |
| YouTube transcripts + Camoufox | home box residential-IP cron | on detect | incremental; pushed back into `raw/` next Actions run |
| R2 mirror | trading-data | every ingest run | full sync of `data/latest/` (small) |
| LLM Haiku distillation → `opinion_event` | trading-analysis | 1×/day (Batch) | incremental: only new `raw_text_ref` rows; watchlist+schema cache prefix |
| regime/features/factors/signals + export contract | trading-analysis | 1×/day after slow ingest | **incremental** for daily signals (append today's `as_of` row per ticker); **full recompute** only for factor re-validation / walk-forward re-optimization, run weekly or on-demand `workflow_dispatch` |
| Dashboard fetch | investment-dashboard | client read | static, on page load (3-tier cache: memory → CDN → local `/data/` fallback) |

OHLCV in-repo backtests stay incremental via `DuckStore.upsert_ohlcv` (idempotent on `symbol,ts,bar`). Heavy items that are deliberately **never live**: GARCH AIC grid and HMM fits are cached; factor IC validation is on-demand.

## 4. Point-in-time `as_of` propagation end-to-end

The discipline lives **in the stored rows**, not at serialization:

1. **Ingest** stamps `as_of` = publication/disclosure/filing instant. The traps: congress uses `disclosure_date` (sidesteps the 45-day PTR lag — the #1 look-ahead failure); Form 4 / 13F / 8-K use `filing_date`; EDGAR companyfacts visible only on/after `filed`. `txn_date`/`period_end` survive as informational columns only. A `trading-data` CI assertion fails if any PIT-table row has null `as_of`.
2. **Ingest into trading-analysis**: every loaded row keeps `as_of`; intermediate tables (`signals`, `factor_scores`, `labels`, `opinion_event`) are all keyed `(ticker, as_of, …)`.
3. **Backtest at sim_date D** selects `WHERE as_of <= D` on every table — so a backtest at D sees only what was knowable at D. Unit tests reject txn-date `as_of` and run the +1-bar shift test (leaked returns must collapse).
4. **Export**: `export_dashboard_json(as_of=D)` selects `as_of <= D`, making the contract a PIT snapshot. Re-running at D reproduces exactly what was knowable at D — that reproducibility is what makes `creator_scorecards.json` honest.

## 5. Timeline of one daily run

```
09:23 UTC  trading-data ingest-slow.yml cron fires (odd minute, off-hour; workflow_dispatch fallback)
09:23–09:30  FETCH: news/Substack RSS + trafilatura; YouTube detect (queues videoIds);
             EDGAR Form4/8-K/XBRL; congress (stock-watcher + Clerk PTR + xref); Dataroma 13F;
             FinMind TW + Finnhub ratings. Each connector stamps as_of.
09:30–09:35  STORE: lib/store.py writes dt= parquet partitions + opinion_event.jsonl rows;
             dedup vs seen.json; rebuild manifest.json (rows/sha/as_of_max).
09:35  COMMIT git-as-DB (single writer, concurrency group "ingest") + git push.
09:36  PUSH-R2: rclone sync data/latest → r2://td-bucket/latest (zero egress).
~asynchronous  Home box cron pulls queued videoIds → transcript/yt-dlp/Whisper →
             pushes raw/transcripts/ back (lands in next Actions run).
10:00  trading-analysis daily.yml fires.
10:00–10:05  PULL: rclone copy R2 latest → local cache; manifest sha gates re-download.
10:05–10:10  DISTILL: Haiku Batch over new raw_text_ref → opinion_event rows.
10:10–10:25  ANALYZE: regime.classify → features → factors (cached validation) →
             rules (regime-gated) → portfolio weights → forward-return scorecards.
             All keyed (ticker, as_of); export selects as_of <= today.
10:25  EXPORT: api.export_dashboard_json() validates DashboardStatus, atomic-writes
             dashboard_status.json + opinions.json + creator_scorecards.json; commit/push
             to dashboard data prefix (or R2 contract prefix).
on next load  investment-dashboard fetches via resolveDataUrl(); comet + ATR exit render.
```

## 6. Failure / staleness handling — graceful degradation

- **Per-source isolation**: each connector writes independently; one failing (EDGAR 503, FinMind quota) means its partition simply isn't appended this run. `manifest.json.as_of_max` per table exposes the staleness; the commit step is `|| echo "no changes"` so a no-op run is not an error.
- **Stale-but-valid**: trading-analysis reads last-known-good from `data/latest/` (git history is the rollback). A table whose `as_of_max` lags > N days is flagged in `global_regime`/`meta` and that signal's `scores{}` field goes `None` rather than emitting a stale number.
- **Partial contract**: export still runs on whatever tables are fresh; missing optional `scores`/`opinions` default to `None` (additive-safe). The hard-required comet keys (`coordinates/trace/sector_trace`) come from the ported `daily_update.py` math, so the comet never silently breaks even if alt-data is down.
- **R2 outage**: dashboard's 3-tier cache falls back to same-origin `/data/` (Phase-1 fallback tier kept); trading-analysis falls back to the git-tree copy of `data/latest/`.
- **Schedule miss**: Actions cron is best-effort; the 2×/day fast + daily slow cadence tolerates a dropped trigger, and `workflow_dispatch` is the manual catch-up. Periodic commits also prevent the ~60-day idle auto-disable.
- **Contract validation failure**: `model_validate()` aborts the atomic write — the dashboard keeps reading yesterday's valid file rather than a corrupt one.

---

Files grounding this design (all absolute): `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\ingestion-pipeline.md`, `...\docs\architecture-integration.md`, `...\docs\01-implementation-plan.md` (appendices B Data Contract, D Ingestion storage table + as_of rule, E roadmap), `...\docs\design-brief.md`; existing ingest-side code that the trading-analysis reader extends — `...\src\trading_analysis\data\store.py` (`DuckStore` in-memory DuckDB + parquet-glob views, the hook for R2 `read_parquet`) and `...\src\trading_analysis\data\schema.py` (`OHLCVBar`/`ForecastRow` PIT `asof` precedent).


---

# 附錄 B — 開發計畫（refined）

# DEVELOPMENT PLAN (refined) — post-M0

**M0 status: DONE & committed.** `regime/sma_gate.py` (`SMARegimeGate`, rising-SMA mask), `strategy/rules/minervini_trend.py` (Trend Template + cross-sectional `rs_rating`, +1-bar lag), and `labeling/` (`triple_barrier.py`, `trend_scanning.py`, `cv.PurgedKFold`, `volatility.ewma_vol`) all landed, wired into `api.backtest_strategy` (regime gate applied via `gate.shift(1)`), with `tests/unit/test_minervini.py` + `test_labeling.py` green. SPY is in `configs/smoke.yaml`. The M0→M2 spine is proven end-to-end on the smoke universe.

The next 4–6 PRs walk the path **features → factors → meta-labeling ML → fundamentals → value rules → alt-data**, each gated by the rigor scorecard (#1 look-ahead, #2 survivorship, #4 walk-forward, #5 Deflated Sharpe, #6 cost/slippage, #7 OOS, #10 reproducible).

---

## PR-1 — `features/` breadth + ADF + mean-reversion pack *(HIGHEST-VALUE NEXT PR — defined concretely below)*

**Scope (new module `src/trading_analysis/features/`):** `indicators.py` (breadth via the `ta` library — Donchian/Keltner/Ulcer/ADX/Vortex/CCI/Aroon/MFI/CMF/TSI/Williams%R/PPO), `mean_reversion.py` (Hurst, variance-ratio, half-life of mean reversion — pure NumPy), `stationarity.py` (`adf_filter` keeping only stationary series as ML inputs), `importance.py` (MDI per-tree mean±std + MDA permutation + >0.8 correlation pruning), and `build.py` exposing `features.build(ohlcv) -> wide [ts x (symbol,feature)] frame`. Add `ta` to `pyproject.toml`. Reuse `models/ta_indicators.py` for the primitives already present (sma/ema/rsi/atr/macd/bollinger) rather than re-deriving.

**Dependencies:** M0 (`labeling.cv.PurgedKFold` for the IC-stability fold loop; `ewma_vol` for the reversion target).

**Extraction specs / sources:** mean-reversion ← QuantResearch `mean_reversion.py:30-102`; breadth + ADF ← jo-cho `tautil.py` (**add `ta` dep, do not hand-copy** — jo-cho is no-LICENSE, reference only); MDI/MDA ← jo-cho plain-sklearn pattern, rewritten with mean±std + permutation; microstructure (Amihud/Corwin-Schultz) deferred to a stretch commit (needs no new data, OHLCV-derived).

**Verification:** scorecard **#1** — every feature carries `available_at <= bar_ts` (no `.shift(-k)`); a +1-bar shock test on a feature-driven z-score signal must collapse returns. **#2** — features computed on adj-close, never `SELECT DISTINCT ticker`. **pytest** `tests/unit/test_features.py`: `adf_filter` rejects a synthetic random walk and accepts an AR(0.3) series; Hurst≈0.5 on GBM, <0.5 on a mean-reverting OU series; `build()` is leak-free (assert `build(ohlcv[:T])` equals `build(ohlcv)[:T]` column-for-column — the key acceptance test). **vectorbt** — z-score reversion sim on smoke universe; confirm IC sign stable across the M0 purged-CV folds.

**Effort: M.**

---

## PR-2 — `factors/` Alphalens IC harness + qlib Alpha158 port

**Scope (new `src/trading_analysis/factors/`):** `validate.py` (`factors.validate(factor, fwd_returns) -> {ic, ic_decay, quantile_spread, n_tried}` — the **gate every factor passes before any backtest**), `alpha158.py` (clean port of qlib's Alpha158 expression set computed off the PR-1 feature frame), `quantile.py` (rank-sort into quantile portfolios). Defer Fama-French/QMJ + PCA to a follow-up (they need EDGAR fundamentals from PR-4).

**Dependencies:** PR-1 (feature frame), M0 (PurgedKFold for OOS IC). Add `alphalens-reloaded` (MIT) — do not hand-roll IC decay.

**Extraction specs / sources:** Alphalens harness ← QuantResearch `volume_factor_alphalens.ipynb`; Alpha158 ← qlib (already inventoried in extraction-backlog). 

**Verification:** scorecard **#5 (Deflated Sharpe)** — `validate()` records and discloses `N = factors tried`; DSR>0 required before promotion. **#9** — factor selection counts toward N; hold out a period. **pytest** `tests/unit/test_factors.py`: a known leaky factor (uses `fwd_returns` directly) shows a single-bar IC spike that `validate()` flags; a legitimate factor shows graceful IC decay. **vectorbt** — monotone quantile return spread out-of-sample on smoke→top-50.

**Effort: M.**

---

## PR-3 — META-LABELING ML (LightGBM on the Minervini signal) ⟵ *the strategic payoff of M0*

**Scope (new `src/trading_analysis/strategy/meta_label.py` + `api.backtest_meta_labeled(...)`):** Use `MinerviniTrendRule.to_pivot()` as the **primary side** (already +1-bar-lagged), generate triple-barrier meta-labels via `triple_barrier_events(..., side=minervini_long)` + `get_bins` (the `side`-aware {0,1} path already exists), train **LightGBM** on the PR-1 feature frame under `PurgedKFold(t1=events.t1, pct_embargo=0.01)` walk-forward, and emit a size multiplier (predicted P(profit)) that scales the Minervini direction in the existing sizing layer. The meta-model decides **whether to act on**, never **whether to enter** — preserving the rule's interpretability.

**Dependencies:** PR-1 (features = X), PR-2 (only validated features enter X), M0 (`triple_barrier`, `PurgedKFold`, `MinerviniTrendRule`). Add `lightgbm`.

**Extraction specs / sources:** de Prado AFML Ch3 meta-labeling (already implemented in `get_bins` side-path) + Ch7 PurgedKFold (done). No new repo — this **composes existing M0 primitives**, which is exactly why M0 was built first.

**Verification:** scorecard **#1 + #3 + #4 + #7** — train P(profit) only on train fold, embargo ≥ label horizon (assert no train/test `t1` overlap, reusing the M0 invariant); **#5** DSR on the meta-strategy vs the raw Minervini baseline. **pytest** `test_meta_label.py`: shuffling labels collapses OOS precision to base-rate (no leak); meta-filtered equity ≥ raw Minervini equity net of cost on smoke. **vectorbt** — walk-forward `Splitter` loop; meta-labeled Sharpe beats raw rule OOS net of turnover.

**Effort: L.**

---

## PR-4 — Fundamentals connector (SEC EDGAR, point-in-time)

**Scope (new `src/trading_analysis/data/connectors/edgar.py`):** `EdgarConnector.companyfacts(tickers) -> DataFrame` keyed by `(ticker, concept, fiscal_period, filed)`, **`as_of = filed` (the row is visible only on/after `filed`)**, plus a DuckStore upsert + `set_identity(email)`. Wrap `edgartools` XBRL `by_concept(...)` for EBIT/equity/ROE/EPS. No new business logic — just PIT-correct ingestion.

**Dependencies:** independent of PR-1/2/3 (could parallelize), but value is unlocked by PR-5. Add `edgartools`.

**Extraction specs / sources:** extraction-backlog opinion/alt-data row — "edgartools 最強，只缺 DuckDB upsert 包裝 + `set_identity(email)`."

**Verification:** scorecard **#2 + #1** — *the* failure mode for fundamentals. **pytest** `test_edgar_pit.py`: querying `as_of <= D` never returns a row with `filed > D` (reject `period_end`-keyed lookups); a restatement appears as a **second, later-dated row**, never overwriting the original. **Effort: M.**

---

## PR-5 — `magic_formula` + `graham` value rules (regime-gated)

**Scope (new `strategy/rules/magic_formula.py`, `graham.py`):** Greenblatt rank (earnings yield × ROIC) and Graham defensive screen, each implementing `to_pivot()`, registered in `api.py:_RULES`, **AND-gated by the M0 regime + filtered `as_of(filed) <= sim_date`**. Compute ratios via `FinanceToolkit` (MIT) — **never hand-code Graham/Piotroski**.

**Dependencies:** PR-4 (PIT fundamentals). **Verification:** scorecard **#2** (PIT filter), **#6** (≥25 bps cost sweep), **#8** (≥1 cycle incl. 2022). **pytest**: rank reproducible from a fixed companyfacts fixture; mis-dating to `period_end` measurably inflates returns (the canary). **Effort: M.**

---

## PR-6 — `opinion/` + `signals/` alt-data (insider / PEAD / congress)

**Scope (new `signals/insider.py`, `signals/pead.py`, `opinion/congress.py` → unified `opinion_event`):** Form-4 rolling-30d ≥N distinct `Code='P'` cluster-buy (`as_of=filing_date`); time-series SUE `(EPS_q−EPS_{q−4})/σ(ΔEPS~8q)` from EDGAR XBRL (`as_of=8-K Item 2.02 filing_date`); congress PTR **`as_of=disclosure_date` (the 45-day-lag trap)**. Per-`source_name` scoreboard over 1/5/20/60d.

**Dependencies:** PR-4 (EDGAR), the contract `OpinionEvent` model. **Verification:** scorecard **#1+#2+#5** — unit test **rejecting any txn-date `as_of`** for congress; drift must vanish when `as_of` is wrongly set to txn/period_end. **vectorbt** event-driven entries on top-50. **Effort: L.**

---

## The single highest-value next PR — PR-1, defined concretely

**Why PR-1, not PR-3:** the meta-labeling ML (the real edge upgrade) is the goal, but it is **blocked on a feature matrix X**. M0 gave us labels (y) and CV (folds) but **no features**. PR-1 is the smallest unblock-everything step: factors (PR-2) and meta-labeling (PR-3) both consume `features.build()`, and it ships on infrastructure that already exists. Building meta-labeling first would mean hand-assembling features inline — re-creating the leak risk M0 was built to prevent.

**Files:** `src/trading_analysis/features/{__init__,build,indicators,mean_reversion,stationarity,importance}.py`; `pyproject.toml` (+`ta`); `tests/unit/test_features.py`; extend `configs/smoke.yaml` with a `features:` block.

**Acceptance test (the load-bearing one):**
```python
def test_features_are_point_in_time_leakproof():
    full = features.build(ohlcv)                 # smoke universe
    truncated = features.build(ohlcv.iloc[:T])
    pd.testing.assert_frame_equal(
        full.iloc[:T].dropna(how="all"),
        truncated.dropna(how="all"),
    )  # a feature value at bar t must never change when future bars arrive
```
Plus: `adf_filter` rejects a random walk / accepts AR(0.3); Hurst≈0.5 on GBM and <0.5 on OU. This is scorecard **#1** made executable and is the gate the rest of the path inherits.

**Relevant files (absolute):** `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\features\` (new), `...\src\trading_analysis\models\ta_indicators.py` (reuse primitives), `...\src\trading_analysis\labeling\cv.py` (fold loop), `...\src\trading_analysis\api.py` (`_RULES` + future `backtest_meta_labeled`), `...\configs\smoke.yaml`, `...\docs\extraction-backlog.md` (source rows), `...\docs\data-and-backtest-rigor.md` (scorecard #1/#2/#5/#6).


---

# 附錄 C — 便宜 ML 評估

# Cheap ML for the Stock-Analysis System: A $0-Marginal-Cost Plan

**Bottom line up front:** with the de Prado triple-barrier + PurgedKFold foundation already in `src/trading_analysis/labeling/`, the highest-ROI ML you can add is a **gradient-boosting meta-labeling model trained on a free notebook (Kaggle/Colab) and run for inference inside GitHub Actions on CPU at $0**. Deep learning and rented cloud GPU are not justified at this scale and would blow the <$15/mo budget for near-zero accuracy gain on tabular data. Total recurring infra: effectively **$0** (public-repo Actions are unmetered; free notebooks cost nothing), leaving the entire $15 headroom for data/LLM API, not compute.

## 1. WHERE to train cheaply

You almost never need a GPU here — gradient boosting on a few thousand-to-low-million rows trains in seconds-to-minutes on CPU. But for the free options:

| Option | 2026 limits (verify — these drift) | Suitability |
|---|---|---|
| **Local CPU / home box** | Unlimited, your electricity | **Best default.** LightGBM on daily-bar features trains in <1 min. No quota anxiety, reproducible. |
| **Kaggle Kernels** | ~**30 GPU-hr/week** quota (T4 x2 or P100 16GB), **12-hr** session cap, resets weekly | Best free *managed* option: more generous than Colab, persistent datasets, schedulable. Good for batch retrains. |
| **Google Colab free** | Dynamic ~**15–30 GPU-hr/week**, ~12-hr session, throttled by demand/usage history; can be cut off mid-session | Fine for ad-hoc experiments; **unreliable for scheduled jobs** — no guaranteed availability. |
| **Paperspace Gradient (DigitalOcean) free tier** | Still exists as of mid-2026 (free GPU/CPU notebooks, private workspaces, queueing) | Backup only; availability/queues unpredictable. |

**Uncertainty flag:** all free-tier numbers above are *soft, dynamic, and frequently revised*. Colab in particular explicitly varies by load and account history. Do not architect anything that *depends* on a specific free-GPU quota — treat GPU as a bonus, CPU as the contract.

**Recommendation:** train on **local CPU** for the inner loop, mirror to **Kaggle** for any heavier sweep or scheduled weekly retrain. You will essentially never touch the GPU quota for boosting on this data.

## 2. MODEL families for tabular finance

**Gradient boosting wins on tabular, decisively.** LightGBM / XGBoost / sklearn-HGB consistently match or beat deep nets on heterogeneous tabular data, train orders of magnitude faster, run on CPU, and produce native feature importances (which feed straight into your MDI/MDA + >0.8-correlation pruning from the backlog). For your feature set — Hurst/variance-ratio/half-life, indicator breadth, microstructure (Corwin-Schultz, Amihud, VPIN), regime flags — this is exactly the regime where trees dominate.

**Default:** **LightGBM** (fast, low memory, great with many weakly-informative features and missing values; handles your wide breadth-indicator matrix well). XGBoost is a fine sibling; plain sklearn `HistGradientBoostingClassifier` is the zero-extra-dependency fallback.

**When is deep learning worth it?** Almost never *here*. DL earns its keep on raw sequences/tick-level/text/cross-asset transformers with huge data and a GPU budget — none of which fits <$15/mo or your daily-bar tabular features. The Kronos/AI-Trader verdicts in your memory already point the same way. The cheap, high-value pattern is **boosting + meta-labeling**: de Prado's insight is that you don't ask ML to *predict direction* (hard, low signal); you let the **Minervini/CANSLIM rule pick the side**, and ML only answers *"should I take this signal, and how big?"* — a far easier binary problem with naturally balanced-ish labels from `get_bins`' `{0,1}` meta output.

## 3. INFERENCE in the pipeline — $0 on GitHub Actions

Inference is trivially cheap and belongs in CI:

- **Public-repo GitHub-hosted runners are unmetered/free** (no quota). Private repos get 2,000 free Linux min/mo on the Free plan; Linux runner price dropped to **$0.006/min** on 2026-01-01 if you ever exceed it. Keep the data/contract repo **public** (or stay well under 2,000 min) and inference is **$0**.
- Serialize the trained model two ways: **`joblib`** for the native LightGBM (simplest), and optionally export to **ONNX** via `onnxmltools.convert_lightgbm` + run with `onnxruntime` `CPUExecutionProvider`. ONNX gives a tiny, dependency-light, version-stable artifact and fast CPU inference — useful if you want the inference job to *not* pull the full training stack. Tree models are inherently tiny (threshold splits, not tensors), so artifacts are KB–low-MB.
- **Store the artifact in the data/contract repo** (git or a release asset): `models/meta_labeler_v{N}.onnx` + a `model_card.json` (train window, feature list, CV scores, `as_of`). The Actions inference job loads it, scores today's events, and writes predictions into the contract DuckDB/parquet alongside the rule signals. Retraining is a *separate, occasional* job (manual or monthly cron); daily inference just reuses the pinned artifact — deterministic and auditable.

## 4. WALK-FORWARD validation — don't fool yourself

This ties directly to rigor scorecard #5. Reuse your existing `PurgedKFold`:

1. **Purge + embargo:** `triple_barrier` already emits `t1` (true label end); `PurgedKFold` uses it to drop train samples whose label window overlaps the test fold, plus an embargo gap. This is the non-negotiable leakage guard for overlapping labels.
2. **Walk-forward, not random:** evaluate in expanding/rolling time order (the monthly-retrain loop from `Deep-Factor-Models.ipynb` `training()`), never shuffled CV.
3. **Deflated Sharpe Ratio (DSR):** after backtesting the meta-labeled strategy, deflate the Sharpe for the **number of trials** you ran (every hyperparameter combo counts) and for skew/kurtosis. A raw Sharpe from 200 configs is meaningless; DSR tells you whether it survives multiple-testing. Pair with PBO (probability of backtest overfitting) if you sweep heavily.
4. **Feature selection inside the CV fold**, never on the full set — otherwise selection leaks.

## 5. The concrete meta-labeling model (highest-ROI cheap ML)

This is the one ML thing to build. It *augments*, never replaces, the Minervini rule.

- **Side (given, not learned):** the Minervini/CANSLIM rule fires `side = +1` on qualifying setups (trend-template + breakout, gated by your 200-SMA / HMM regime "M").
- **Events:** each rule-fire timestamp → `t_events`. Feed to `triple_barrier_events(..., side=rule_side)` with per-event `target = ewma_vol(close)` and `pt_sl=[pt, sl]`, plus a `num_bars` vertical barrier (e.g. 20 daily bars). `get_bins` returns the **meta label**: `bin ∈ {0,1}` — 1 if the rule's side actually made money before a barrier, 0 if not.
- **Target:** binary `bin` (take the trade vs. skip). The model's `predict_proba` becomes both a **filter** (act only if p > threshold) and a **sizer** (position ∝ p, optionally Kelly-capped).
- **Features (X):** your existing tabular battery — breadth/momentum indicators (ADF-stationary only), Hurst/VR/half-life, microstructure liquidity, regime probability (HMM high-vol), distance-to-barrier vol `target`, and rule-strength fields. Prune with MDI/MDA + >0.8 correlation drop *inside folds*.
- **Model:** LightGBM classifier, `scale_pos_weight` or sample weights from label uniqueness (de Prado's overlap weighting), early-stopping on a purged validation fold.
- **Training cadence:** retrain **monthly** (or quarterly) on the expanding window via Kaggle/local; daily Actions inference uses the pinned artifact.
- **Plug-in:** export → commit `meta_labeler.onnx` to the contract repo → Actions scores today's rule signals → writes `p_meta` into the signal contract. The **vectorbt backtest consumes `p_meta`** as an entry filter + size multiplier, and you report **PurgedKFold OOS + Deflated Sharpe** of (rule alone) vs (rule × meta-label) to prove lift.

## CHEAP-ML RECOMMENDATION

- **Train where:** local CPU for the loop; **Kaggle** (≈30 GPU-hr/wk, 12-hr sessions) for scheduled monthly retrains. GPU is a bonus you won't need.
- **Which model:** **LightGBM meta-labeling classifier** on triple-barrier `{0,1}` labels — boosting + meta-labeling is the cheap high-value pattern.
- **Infer where:** **GitHub Actions CPU**, free on public repo (or under the 2,000-min private quota), via `joblib` or **ONNX/onnxruntime**; artifact lives in the data/contract repo with a model card.
- **Validate how:** **PurgedKFold + embargo + walk-forward + Deflated Sharpe**, feature selection inside folds.
- **Marginal cost:** ~**$0**. Full $15 budget stays free for data/LLM, not compute.

### Do NOT do
- **No rented cloud GPU** (A100/H100 hourly, SageMaker, Vertex, Lambda) — instant budget kill for zero tabular benefit.
- **No deep learning** (LSTM/Transformer/Kronos-style) on daily-bar tabular features — slower, GPU-hungry, and *worse* than trees here.
- **Don't depend on free-GPU quotas** for production — they're dynamic and can vanish mid-session; keep CPU as the contract.
- **No always-on inference server / hosted endpoint** — batch-score in Actions instead.
- **Don't let ML pick direction** — meta-labeling only sizes/filters the rule.
- **No random-split CV, no full-dataset feature selection, no undeflated Sharpe** — that's the overfitting trap rigor #5 exists to catch.

---

**Relevant files:** `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\labeling\triple_barrier.py` (meta-label generator — `triple_barrier_events(side=...)` + `get_bins` already emit the `{0,1}` target), its sibling `labeling\cv.py` (`PurgedKFold`) and `labeling\volatility.py` (`ewma_vol` target), and `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\extraction-backlog.md` (features/MDI-MDA pruning, walk-forward loop, ADF screening this model consumes).

**Sources** (free-tier limits are dynamic — re-verify before relying on quotas):
- [Google Colab Free Tier T4 Guide 2026 (aicreditmart)](https://aicreditmart.com/ai-credits-providers/google-colab-free-tier-t4-gpu-access-guide-2026/)
- [Kaggle vs Colab 2026 (Medium)](https://lalatenduswain.medium.com/kaggle-vs-google-colab-which-cloud-notebook-platform-should-you-choose-in-2026-da053a02fcb7) · [Kaggle Efficient GPU Usage docs](https://www.kaggle.com/docs/efficient-gpu-usage)
- [GitHub Actions pricing change 2026 (GitHub Changelog)](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/) · [GitHub Actions billing docs](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Paperspace/DigitalOcean pricing docs](https://docs.digitalocean.com/products/paperspace/pricing/)
- [ONNX Runtime: deploy traditional ML](https://onnxruntime.ai/docs/tutorials/traditional-ml.html) · [sklearn-onnx LightGBM conversion](https://onnx.ai/sklearn-onnx/auto_tutorial/plot_gexternal_lightgbm.html)


---

# 附錄 D — labeling 對抗式審查

# Adversarial review: AFML labeling module

## 1. `triple_barrier.py`

### CRITICAL (look-ahead) — `vertical_barriers` off-by-one: barrier is one bar too far. `triple_barrier.py:30`
de Prado's snippet 3.4 sets `t1 = close.index[i + numDays]`, but he indexes by *searching for the timestamp `numDays` later*, then takes the bar **at or before** it (`searchsorted(..., side)` then `-1` for the inclusive bar). Here `end = locs + num_bars` and `t1 = close.index[end]` makes the vertical barrier the `(loc+num_bars)`-th bar, i.e. it spans `num_bars+1` bars inclusive (verified: `loc=0, num_bars=4 → t1=bar4 → path length 5`). If you intend "hold N bars," the holding window is N+1 bars. This is a definitional leak: every label's horizon, and therefore every `t1` PurgedKFold purges on, is one bar longer than specified. Whether this is "wrong" depends on intent, but it is **inconsistent with the bar count the API name promises** and silently inflates the purge interval.
Fix: `end = locs + num_bars - 1` if `num_bars` means "number of bars held", or document that `num_bars` is an *offset*, not a count, and align the test (`test_triple_barrier_vertical_when_barriers_far` currently bakes in the +1).

### CRITICAL (silent wrong answer) — `searchsorted` default side + off-grid events. `triple_barrier.py:29`
`close.index.searchsorted(t_events)` uses `side='left'`. If an event time is **not exactly on the close grid** (common with intraday/holiday gaps or resampled events), `searchsorted` returns the insertion point — the *next* bar — so the entry bar in `_first_touch` (`close.loc[loc]`) and the vertical barrier silently shift. Worse, if `t_event` equals a bar exactly but a duplicate timestamp exists, `side='left'` picks the first. de Prado assumes events ⊆ index; you don't enforce it.
Fix: assert membership, or `locs = close.index.get_indexer(t_events)` and raise on `-1`.

### CORRECT — first-touch NaT handling. `triple_barrier.py:47-48, 82`
`rets[rets < sl].index.min()` returns `NaT` when never breached, and `min(axis=1)` over `t1/sl/pt` **skips NaT** (verified). The earliest of the three barriers is correctly selected; a NaT cannot poison the min. The `sl`/`pt` columns also inherit `datetime64[ns]` (seeded from the datetime `t1` column), so no object-dtype min corruption. This part is right.

### CORRECT — `get_bins` reindex alignment. `triple_barrier.py:91-93`
`close.reindex(end)` and `close.reindex(events_.index)` are **label-based** (DatetimeIndex), so prices align by timestamp, not position — correct even after `dropna` reorders nothing. `.values` then strips the index for the arithmetic. Good. Meta-label zeroing (`ret <= 0 → bin 0`) matches snippet 3.7.

### MINOR — meta-labeling barrier asymmetry. `triple_barrier.py:75`
When `side is None` you force `pt_sl_ = [pt_sl[0], pt_sl[0]]`, overriding any caller-supplied `sl`. `triple_barrier_labels` passes `[pt, sl]` but the `sl` is **discarded** in the symmetric branch. So `triple_barrier_labels(c, pt=2, sl=5)` silently uses sl=2. Fix: honor both, or document that symmetric mode ignores `sl`.

## 2. `cv.py` (PurgedKFold)

### CRITICAL (leakage) — `max_t1_idx` maps a label-*value* into the event-*index*. `cv.py:48`
`self.t1.index.searchsorted(self.t1.iloc[test_indices].max())` takes the **max label-END time** (a `t1` *value*) and finds its position **within the event-time index**. These are different axes. When a test label's end time falls *between* two event times or *past the last event* (the normal case — labels end in the future), `searchsorted` returns an insertion index that does **not** correspond to "the bar `embargo` past the last test label." Verified: with irregular spacing, `max t1 = 2024-01-06` (not an event) maps to event position 3 = `2024-01-08`, silently moving the embargo anchor. The embargo length in *bars* is therefore wrong whenever t1 values ≠ event timestamps — i.e. essentially always for real triple-barrier output where `t1` is a touch time, not an entry time. This can **under-purge the right edge and leak**.
Fix: anchor embargo on the **test position**, per de Prado: `max_test_pos = test_indices[-1]; embargo_end_pos = min(max_test_pos + embargo, n-1); purge_end = self.t1.index[embargo_end_pos]` — and purge any train sample with `start` in `[test_t0_pos, embargo_end_pos]` *plus* any whose interval overlaps the test interval.

### CORRECT — left-edge overlap purge. `cv.py:52`
`overlap = (starts <= purge_end) & (ends >= test_t0)` correctly drops train labels that **start before** the test block but **end inside** it (left leakage), matching snippet 7.2's two-sided condition. The interval logic itself is right; only the embargo anchor (above) is broken.

### CORRECT — `min(max_t1_idx+embargo, n-1)` clamp. `cv.py:49`
The clamp prevents out-of-bounds indexing. No off-by-one in the clamp itself (it indexes a valid event). The bug is *what* `max_t1_idx` is, not the clamp.

### MINOR — `embargo = int(n * pct_embargo)` truncates to 0. `cv.py:36`
For small `n` or small `pct_embargo`, embargo silently becomes 0 (no embargo) with no warning. de Prado uses the same `int()`, so acceptable, but flag it: `pct_embargo=0.01, n=50 → 0`.

### EDGE — empty/degenerate folds. `cv.py:41`
`np.array_split` tolerates `n_splits` near `n` (no crash), but a fold can purge **all** train samples, yielding an empty train array — `cross_val_score` will then error opaquely downstream. No guard. Single-bar labels (t1==event) work but produce maximal overlap purging. Consider warning when `len(train)==0`.

## 3. `trend_scanning.py`

### CORRECT — t-stat math. `trend_scanning.py:18-32`
OLS via `lstsq`, `dof=n-2`, `s2 = RSS/dof`, `se = sqrt(s2·(XᵀX)⁻¹₁₁)`, `t = β₁/se`. This is the textbook slope t-statistic and matches snippet 17.4. `n<3` and `se==0` guards are correct.

### CORRECT — no read-beyond-data. `trend_scanning.py:51`
`if loc + length > n: break` correctly bounds the forward window (`vals[loc:loc+length]` max-ends at `n`). `t1 = close.index[loc+length-1]` is the **last in-window bar** — a genuine future bar, intended. As the docstring warns, that future `t1` is exactly what PurgedKFold must consume; no *unintended* leakage as long as callers actually feed `t1` to the CV. Fine.

### MINOR — `get_loc` on duplicate index. `trend_scanning.py:47`
`close.index.get_loc(t)` returns a slice/array on duplicate timestamps, breaking `vals[loc:...]`. Assert a unique index.

## 4. `volatility.py` / `__init__.py`

### CORRECT — `ewma_vol`. `volatility.py:14`
`pct_change().ewm(span).std()` aligned to `close`, NaN warm-up. Matches `getDailyVol` for daily bars. `__init__.py` exports are consistent; no issues.

---

**Top priorities:** (1) `cv.py:48` embargo-anchor leak, (2) `triple_barrier.py:30` vertical-barrier off-by-one, (3) `triple_barrier.py:29` off-grid `searchsorted`. Relevant files: `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\labeling\cv.py`, `...\labeling\triple_barrier.py`.