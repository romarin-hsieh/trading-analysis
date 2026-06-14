# 實作計畫（Master Implementation Plan）

> 由 ultracode 5-stream workflow 生成（2026-06-14）。輸入：[design-brief.md](design-brief.md)。背景：[00-executive-summary.md](00-executive-summary.md)。

# Master Implementation Plan — Multi-Repo Stock-Analysis System

## 1. Overview + DAG

A three-repo, **single-direction** stock-analysis system for US equities (TW secondary). `trading-data` fetches raw bytes on a GitHub-Actions cron and persists them point-in-time (git-as-DB + Cloudflare R2). `trading-analysis` is the single brain and **contract owner** — it reads raw data, runs the regime → labeling → features → factors → strategy → portfolio → opinion engines plus LLM distillation and rigor-gated backtests, then serializes a Pydantic-defined contract via `api.export_dashboard_json()`. `investment-dashboard` is a pure presentation consumer that renders the contract JSON, keeping only its proven-edge assets (the comet viz + ATR/Chandelier exit) and dropping the validation-failed Phase-3 entry signals. The contract is the **only** coupling between Python and TS, and it points downstream only — no cycles. (Full layouts: SECTION 1.)

```
trading-data ──raw JSON/parquet──▶ trading-analysis ──contract JSON──▶ investment-dashboard
 (ingest/store, Public)             (engine + contract SoT, Public)      (Vue3 presentation, Public)
        │                                   │                                    │
   Actions cron                    api.export_dashboard_json()           reads-by-key, no Zod
   git-as-DB + R2                  Pydantic SoT → JSON Schema/TS          comet + ATR exit kept
```

**Acyclicity invariant:** `trading-data` knows nothing of the others; `investment-dashboard` depends only on the *published contract artifact* (vendored JSON Schema + TS types), never on `trading-analysis` Python source.

## 2. Consolidated Milestones M0..M7 (across all three repos)

Milestone numbering follows the SECTION 5 engine roadmap as the spine, with `trading-data` (SECTION 4) and `investment-dashboard` (SECTION 3) work interleaved at the points where their outputs are first needed. The hard gate throughout is the rigor scorecard **#1/#2/#5/#6/#7** (look-ahead, survivorship, deflated-Sharpe, cost/slippage, OOS) — any Fail = the return claim is not trusted.

| M | trading-analysis | trading-data | investment-dashboard | Cross-repo dependency |
|---|---|---|---|---|
| **M0** | `regime/` (200-SMA gate + HMM + GARCH) + `labeling/` (triple-barrier, trend-scan, purged/embargoed CV). Add SPY to `configs/smoke.yaml`. | — (yfinance OHLCV already available in-repo) | — | none (bedrock; uses existing `DuckStore`) |
| **M1** | `features/` (ta lib, ADF screen, mean-reversion pack, MDI/MDA). Opportunistic thin `dashboard_status.json` superset stub. | **Repo bootstrap**: create `romarin-hsieh/trading-data` Public, `lib/store.py` + `as_of` schema, `prices/yfinance_us.py`, `ingest-fast.yml` cron + `push-r2.yml`. | **Phase 0** (additive): exporter writes `scores{}` + sibling JSON; dashboard structurally ignores. | dashboard Phase 0 consumes M1 stub output |
| **M2** | `strategy/rules/` (minervini_trend, vcp, magic_formula, graham, canslim, pair-cointegration, parabolic_sar, rsi); every entry AND-gated by M0 regime. | EDGAR `form4`/`form_8k`/`xbrl_facts` + congress (`stock_watcher`, `house_clerk_ptr`, `crosscheck`) + Dataroma scraper + FinMind/Finnhub. `ingest-slow.yml`. | — | M2 rules read EDGAR companyfacts from trading-data |
| **M3** | `factors/` (Alphalens IC harness, Alpha158 port, Fama-French/QMJ, PCA). Factor must pass IC validation before any backtest. | News/Substack RSS (`news_rss`, `extract`/trafilatura) + CF-Worker Medium proxy. | **Phase 1**: `VITE_DATA_SOURCE_URL` env-switch to R2 CDN, keep `/data/` fallback tier. | dashboard Phase 1 points at trading-data R2 |
| **M4** | `portfolio/` (PyPortfolioOpt MVO/max-Sharpe), walk-forward re-optimized weights into the sizing layer. | YouTube `detect_rss` + `channels.yml`; home-box companion cron (transcript-api → yt-dlp → faster-whisper). | — | — |
| **M5** | `opinion/` + `signals/` — all sources collapse into unified `opinion_event`; per-`source_name` scorecards (1/5/20/60d). | `opinion_event.jsonl` raw rows (insider cluster-buy, PEAD/SUE, congress disclosure-dated, Dataroma 13F, distilled transcripts). | — | M5 distillation reads transcripts/filings from trading-data |
| **M6** | `contract/` finalized → `api.export_dashboard_json()` emits validated `dashboard_status.json` + `opinions.json` + `creator_scorecards.json`. JSON Schema emitted to `contract/schema/`. | LLM (Haiku Batch) distillation stays in trading-analysis, not here. | **Phase 2**: consume our trend-template/RS/factor `signal` instead of toxic Phase-3; **keep** comet coordinates/trace + ATR/Chandelier exit. | dashboard Phase 2 consumes M6 contract |
| **M7** | Phase-2 deferrals: Riskfolio risk-parity, options GEX, short-interest/FTD signals; `shared-contracts` extraction *iff* a 2nd consumer appears. | `data/raw/` rolling-window prune job; R2 lifecycle. | **Phase 3**: retire in-repo ETL (`daily-data-update.yml`, `daily_update.py`); port comet+ATR math into trading-data first, then delete. | dashboard Phase 3 only after Phases 0–2 soak in prod |

**Key inter-repo ordering:** trading-data must ship its R2 mirror (M1/M3) before the dashboard can switch its source (Phase 1). The M6 contract must validate against the live `dashboard_status.json` superset before the dashboard consumes new `signal` values (Phase 2). The dashboard ETL retirement (Phase 3) is last and highest-blast-radius — it requires the comet+ATR math to be ported into trading-data first (SECTION 3 Phase 3), and only proceeds after Phases 0–2 are stable in production.

## 3. Critical Path + First PR

**Critical path:** `M0 regime+labeling` → `M2 minervini_trend rule (regime-gated)` → `M6 contract export` → `dashboard Phase 2 signal swap`. This is the thread that replaces the "Toxic Alpha" entry signal with a validated one and gets it onto the live dashboard. Everything else (features→factors→portfolio depth, opinion/alt-data, trading-data crawler tiers) enriches but does not block this spine. Building rules before the regime/labeling bedrock would re-create the exact trap the dashboard already hit — so M0 is non-negotiably first.

**First PR** (per SECTION 5, smallest shippable, all within the existing repo): **`feat(regime+rule): minervini_trend gated by 200-SMA regime on smoke universe`**

1. `regime/sma_gate.py` — `SMARegimeGate(window=200)` returning LONG-OK / risk-off per bar from the benchmark; add **SPY** to `configs/smoke.yaml`.
2. `strategy/rules/minervini_trend.py` — Trend Template + self-computed **RS Rating** (trailing-return percentile, RS≥70 gate), implementing the existing `Signal`/`Direction` + `to_pivot()` interface, AND-gated by the regime gate.
3. Register `"minervini_trend"` in `api.py:_RULES`; add a smoke config block.
4. Backtest on the existing 5-ticker smoke universe via the current vectorbt engine.

**PR-level verification:** scorecard **#1** (the +1-bar shift test — leaked returns must collapse), **#6** (net of the existing 5+5 bps fees/slippage), **#10** (seed-reproducible report). This validates the M0→M2 spine on infrastructure that already exists (`DuckStore`, `run_backtest`, `to_pivot`) before the heavier labeling/CV and EDGAR work lands. Branch from `main` per repo convention (current branch is `master`; promote `main` for PRs).

## 4. CI + Contract-Validation Gate (spanning repos)

The contract is a **versioned downstream artifact**, validated at three checkpoints. The single most important guard against silent three-repo drift is the pydantic→TS schema gate.

**In `trading-analysis` (the SoT, per SECTION 2 §4):**
- `scripts/emit_schema.py` runs `DashboardStatus.model_json_schema(mode="serialization")` → commits `contract/schema/dashboard_status.schema.json` + `opinion_event.schema.json`. CI fails if the committed schema is stale (regenerate-and-diff).
- **Contract-version diff gate:** CI diffs the new schema against the previous committed schema. A **MINOR** change (new *optional* field / new enum member / new sibling artifact) is the only class allowed to ship unilaterally — CI asserts every new field is `Optional`/has a default. A **MAJOR** change (rename / removal / type-narrowing / required-promotion) **fails the build** unless `meta.contract_version` got a major bump *and* a coordinated dashboard release is linked. `meta.version` (the dashboard's own field) is copied through unchanged and is never bumped for additive change.
- Export validation **is** the gate: `export_dashboard_json()` runs `DashboardStatus.model_validate(...)` and aborts the atomic write (`*.tmp` → `os.replace`) on any invalid contract, so a half-written or invalid file is never published.

**In `investment-dashboard` (the consumer, per SECTION 3 risk #4):**
- Vendors the generated `*.schema.json` + TS types (committed file or version-pinned release asset) — does **not** install the Python package.
- CI validates sample fixtures against the vendored JSON Schema (e.g. `ajv`) and **fails the build on incompatible contract drift**. A second CI check generates JSON Schema from pydantic, diffs it against types derived from `src/types/index.ts`, and fails on any removed/renamed field.
- **Producer-side `signal` enum guard:** because `signal` is a free string the front end renders unknown values as neutral (a typo renders grey and looks "fine," masking a logic break), CI asserts every emitted `signal` value maps to a known visual bucket.

**In `trading-data`:** `JSON.parse`/schema-validate every emitted file in CI; assert `as_of` present and non-null on every row of every PIT table (the load-bearing column).

## 5. Monthly Cost (re-checked < $15)

| Item | Repo | $/mo |
|---|---|---:|
| GitHub Actions cron (all **Public** repos) | all | $0 |
| git-as-DB store (<1 GB) | trading-data | $0 |
| Cloudflare R2 (serve ~1–2 GB, $0 egress, within 10 GB free) | trading-data | $0 |
| Cloudflare Worker (Medium proxy, within 100k req/day) | trading-data | $0 |
| Crawlers (RSS, r.jina keyless, Crawl4AI self-host, trafilatura) | trading-data | $0 |
| YouTube detect (RSS) + transcripts (api/yt-dlp) | trading-data | $0 |
| EDGAR / FinMind / Finnhub-free / stock-watcher / Dataroma | trading-data | $0 |
| Whisper + Camoufox (home box, residential IP) | trading-data | $0 (≈ electricity) |
| **LLM distillation — Haiku 4.5 Batch** | trading-analysis | ~$2.2 |
| Buffer (Worker Paid $5 if Medium volume grows; extra Whisper) | trading-data | ~$2–5 |
| **System total** | | **~$2–7** |

Pessimistic path (private repo + all-Sonnet distillation + paid Worker) ≈ $10–12, still inside the $15 cap. The all-Public-repo constraint is what keeps Actions minutes at $0 and is the single biggest cost lever.

## 6. Open Decisions (§9) — recommended defaults

| # | Decision | Recommended default | Rationale |
|---|---|---|---|
| 1 | Creator list (~10 + UC id + watchlist) | Start with **~10 large-cap-focused US equity channels**, pinned in `youtube/channels.yml`, each mapped to the smoke→top-50 universe. Treat the list as data, not code, so it's revisable without a release. | Keeps M5 finfluencer scorecards honest (DSR per source) without over-committing; expandable additively. |
| 2 | Whisper host | **Home PC GPU** (faster-whisper large-v3), not Pi. | Only ~20–40% of videos lack captions; GPU clears the queue fast and is $0 marginal. Pi can't run large-v3 at usable speed. |
| 3 | Backtest hold horizon default | **20-day default**, but **always emit 1/5/20/60d** in the scorecard (the `opinion_event` model already carries all four). | Matches the unified scorecard; 20d balances signal decay vs noise; multi-horizon emission avoids re-running. |
| 4 | data-repo visibility | **Public** (hard constraint anyway). | Free unlimited Actions minutes — the cost model depends on it. No private data is stored (raw bytes only). |
| 5 | Extraction model | **Haiku 4.5 Batch** as default; escalate to Sonnet only for low-confidence/high-value docs; Ollama as the $0 fallback if budget ever tightens. | ~$2.2/mo keeps the whole system at ~$2–7; tiered escalation preserves quality where it matters. |
| 6 | Dashboard: replace vs parallel Phase-3 | **AUGMENT now**, retire old Phase-3 entry signals only after Phases 0–2 soak (keep the old `signal` writer dormant one release for instant A/B rollback). | Don't-break-prod; the data-driven swap makes rollback a source flip, not a code revert. |

## 7. Risks + Enforcement of the Three Iron Rules

**Point-in-time (the load-bearing discipline).** Enforced *in the stored tables*, not at serialization: every backtestable row carries `as_of` = disclosure/filing date, never the event date. Congress uses **disclosure date** (the 45-day-lag trap is the #1 look-ahead failure mode — a unit test rejects any txn-date `as_of`); Form 4 uses filing date; 13F uses filing date; EDGAR companyfacts are visible only on/after `filed`. Re-running `export_dashboard_json(as_of=D)` must reproduce exactly what was knowable at date D — that reproducibility is what makes the `creator_scorecards.json` honest. Enforced by scorecard **#1/#2** unit tests (the +1-bar shift test must collapse leaked returns) and the cross-repo `as_of`-non-null CI assertion. (SECTION 2 §5, SECTION 4 storage table, SECTION 5 M5.)

**License discipline.** All repos Public + MIT. AGPL-derived logic is referenced only, never copied. jo-cho and other no-LICENSE sources are **rewritten from upstream** (de Prado AFML / mlfinlab / the `ta` library) — e.g. triple-barrier is rewritten from AFML Ch3, indicator breadth uses the `ta` dependency rather than hand-copied code. vectorbt's Commons Clause is fine (we don't sell). Permissively-licensed code carries attribution. (Brief §2; SECTION 5 feeds.)

**Don't-break-prod.** The four dashboard phases (SECTION 3) are each reversible and ship behind additivity or env-config: Phase 0 writes data prod structurally ignores (rollback = delete sibling JSON); Phase 1 is a one-variable env flip with the local `/data/` fallback tier intact; Phase 2 is a data-driven `signal` swap (rollback = source flip, comet coordinates asserted numerically identical); Phase 3 (ETL retirement, highest blast radius) is last and only after soak. The drift traps to watch (SECTION 3): **`sector_trace` is undocumented yet present on 558/558 entries and read — treat as mandatory**; the exporter MUST emit `coordinates`/`trace[30]`/`sector_trace[30]`/`ticker`/`sector`/`signal`/`price`/`change_percent`/`date` or the comet silently breaks; no Zod means nothing fails loudly, so the pydantic→TS CI gate (§4) is the real safety net; and `config/stocks.json` (not `universe.json`) is the shared universe truth — a mismatch yields missing comet dots with no error.

**Top residual risks:** (a) *silent contract drift* across three repos — mitigated by the §4 schema-diff gate, the single highest-value guard; (b) *look-ahead via mis-dated alt-data* — mitigated by the as_of discipline + M5 unit tests; (c) *data-snooping inflation* across the many strategies/factors/creators tried — mitigated by scorecard #5 (Deflated Sharpe with disclosed N) and #9 (selection counts toward N, hold out a period); (d) *over-building before validation* — mitigated by the M0-first sequencing and the thin first PR that proves the spine end-to-end.

---

**Relevant files (all absolute):**
- Brief / DAG / contract facts: `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\design-brief.md`, `...\docs\architecture-decision-multirepo.md`, `...\docs\architecture-integration.md`
- Rigor scorecard + extraction order: `...\docs\data-and-backtest-rigor.md`, `...\docs\extraction-backlog.md`
- First-PR touch-points: `...\src\trading_analysis\api.py` (`_RULES` registry + add `export_dashboard_json`), `...\src\trading_analysis\strategy\rules\sma_crossover.py` (Signal/`to_pivot` interface to mirror), `...\configs\smoke.yaml` (add SPY)
- Contract module to author: `...\src\trading_analysis\contract\models.py`, `...\src\trading_analysis\contract\exporters.py`, `...\src\trading_analysis\contract\schema\` (generated)
- Convention anchors: `...\src\trading_analysis\strategy\signal.py`, `...\src\trading_analysis\data\schema.py`
- New repo to create: `romarin-hsieh/trading-data` (Public); dashboard touch-points: `.env`/`.env.production` (`VITE_DATA_SOURCE_URL`), `src/types/index.ts`, `docs/specs/DATA_DICTIONARY.md`, `config/stocks.json`, `.github/workflows/daily-data-update.yml` (Phase 3 retirement).


---

# 附錄：五個設計分區詳述



## 附錄 A — Repo 結構

# Repo Structure

This section specifies the multi-repo layout for the stock-analysis system: the repo set, their responsibilities, the single-direction dependency DAG, the full target tree for `trading-analysis`, where each capability lives, how contracts are shared without cycles, and naming/remote setup.

## 1. The repo set + dependency DAG

Three repos, plus an optional fourth deferred to Phase 2. Data and dependencies flow **one direction only** — no cycles.

```
trading-data ──raw JSON/parquet──▶ trading-analysis ──contract JSON──▶ investment-dashboard
 (ingest/store)                     (engine + contract owner)            (pure presentation)
```

| Repo | Responsibility | Visibility | Language | Depends on |
|---|---|---|---|---|
| **trading-data** | Ingestion + raw storage only: fetch raw bytes (OHLCV, EDGAR filings, FinMind chips, congress PTR, Dataroma 13F, news, YouTube transcripts). GitHub Actions cron as serverless trigger; git-as-DB (<1GB) + push latest to Cloudflare R2. No analysis. | **Public** (free unlimited Actions) | Python 3.12 (crawlers, connectors) + workflow YAML | nothing (leaf source) |
| **trading-analysis** | The single brain + **contract owner**. Reads raw data, runs regime/labeling/features/factors/strategy/portfolio/opinion engines + LLM distillation + backtest. Defines pydantic output schema → emits contract JSON. *(this repo)* | **Public** | Python 3.12 + DuckDB + vectorbt + Streamlit | `trading-data` (reads its raw JSON via R2/git) |
| **investment-dashboard** | Pure presentation consumer. Reads contract JSON, renders. Keeps comet visual (coordinates/trace) + ATR/Chandelier exit (only proven edge); drops self-computed Phase-3 entry signals. *(exists)* | **Public** (already) | Vue 3 + TypeScript + Vite (GitHub Pages) | `trading-analysis` **contract** (JSON Schema + TS types), never its Python |
| **shared-contracts** *(optional, Phase 2)* | Pydantic↔TS type mirror + generated JSON Schema, versioned independently. **Initially embedded in `trading-analysis/contract/`** — only extracted when a third consumer appears. | Public | Python + TS (codegen) | nothing (pure types) |

**Acyclicity invariant:** `trading-data` knows nothing of the others; `investment-dashboard` depends only on the *published contract artifact*, not on `trading-analysis` source. The contract is the only coupling between Python and TS, and it points downstream only.

## 2. `trading-analysis` target tree under `src/trading_analysis/`

`api.py`, `cli.py`, `config.py`, `__init__.py` stay at package root (existing). `api.py` remains the **only** public surface — UI/CLI/exporters import from it; everything below is private (existing rule, preserved).

```
src/trading_analysis/
├── api.py                  # public surface; add export_dashboard_json() + export_signals()
├── cli.py                  # CLI entrypoints (existing)
├── config.py               # AppConfig/UniverseConfig loader (existing)
│
├── data/                   # raw-data access layer: read trading-data outputs + local cache
│   ├── connectors/         # yahoo (exists) + edgar, finmind, news, congress, dataroma, youtube readers
│   ├── store.py            # DuckStore over local/R2 parquet (exists)
│   └── schema.py           # internal in-memory frames (NOT the public contract) (exists)
├── models/                 # forecasters: kronos, naive, ta_indicators, ensembles (exists)
├── regime/                 # NEW — 200-SMA market gate (primary) + HMM/MarkovRegression overlay + GARCH (CANSLIM "M")
├── labeling/               # NEW — triple-barrier, trend-scanning labels, purged/embargoed CV splitters (ML foundation)
├── features/               # NEW — ta/pandas-ta indicators, ADF screen, mean-reversion pack (Hurst/half-life), microstructure (Amihud/VPIN), MDI/MDA importance
├── factors/                # NEW — qlib Alpha158 port, Fama-French/QMJ, Alphalens validation harness, PCA
├── strategy/               # signal models + risk + sizing (exists)
│   └── rules/              # minervini_trend, vcp, magic_formula, graham, canslim, pairs_cointegration, parabolic_sar, rsi + sma_crossover/kronos_trend (exist)
├── portfolio/              # NEW — equal-weight → PyPortfolioOpt (MVO/max-Sharpe) → Riskfolio risk-parity (Phase 2)
├── opinion/                # NEW — LLM distillation of YouTuber/earnings-call/analyst/congress/Dataroma into unified opinion_event + finfluencer-style per-source backtest & scorecards
├── signals/                # NEW (alt-data) — insider cluster-buy (Form4), PEAD/SUE, events (8-K), congress, short/GEX (Phase 2)
├── backtest/               # vectorbt engine + metrics + report (exists)
├── execution/              # paper broker + base (exists)
├── contract/               # NEW — pydantic output models = contract SoT; JSON Schema + TS codegen; dashboard_status superset
│   ├── models.py           # Signal, Score, OpinionEvent, DashboardEntry, DashboardStatus
│   ├── exporters.py        # serialize engine results → contract JSON (dashboard_status, sibling files)
│   └── schema/             # generated JSON Schema + emitted .ts types (build artifact)
├── orchestration/          # pipeline wiring: regime→features→factors→strategy→portfolio→opinion→export (exists, to fill)
├── observability/          # structured logging (exists)
└── ui/                     # Streamlit dev/research UI (exists) — NOT the product surface
```

## 3. Where each capability lives

| Capability | Repo | Why |
|---|---|---|
| **Crawling** (RSS Tier0 → r.jina/Crawl4AI → CF-Worker → Playwright/Camoufox; trafilatura extraction) | **trading-data** | Mechanical byte-fetching; cheap, cron-driven |
| **Transcript** (RSS detect → youtube-transcript-api/yt-dlp/faster-whisper) | **trading-data** | Fetch is mechanical; audio never enters git, only distilled text leaves |
| **LLM distillation** (Haiku Batch → `opinion_event`) | **trading-analysis** (`opinion/`) | It *is* analysis; keeps the API-key + Anthropic SDK call in the brain repo |
| **Quant engine** (regime/labeling/features/factors/strategy/portfolio + alt-data signals) | **trading-analysis** | Single brain |
| **Backtest** (vectorbt + point-in-time, per-source scorecards) | **trading-analysis** (`backtest/` + `opinion/`) | Needs full feature/label context |
| **Contract** (pydantic SoT → JSON Schema/TS) | **trading-analysis** (`contract/`) | Engine owns the schema it produces; solves dashboard field-drift |
| **Presentation** (comet viz, watchlists, ATR exit) | **investment-dashboard** | Pure consumer; zero backend preserved |

Boundary rule: **trading-data = "raw bytes in"; trading-analysis = "raw → signals/opinions/scores + contract JSON out"; investment-dashboard = "contract JSON → pixels."** All LLM calls run in trading-analysis Actions.

## 4. Sharing contracts without cycles

The contract is a **versioned downstream artifact**, not a shared dependency both sides import.

- **`trading-analysis/contract/models.py`** (pydantic) is the single source of truth. CI runs `export_dashboard_json()` schema generation → emits `contract/schema/*.json` (JSON Schema) and `*.ts` (via `datamodel-code-generator`/`pydantic2ts`).
- **investment-dashboard vendors the generated TS types + JSON Schema** (committed file or release asset pinned by version) — it does **not** install the Python package. A CI gate validates produced JSON against the schema and fails the dashboard build on incompatible contract drift.
- Backward-compat discipline (dashboard has no Zod on `dashboard_status.json`): only **add** optional fields — new `scores{}` per entry or sibling files (`signals_minervini.json`, `opinions.json`, `creator_scorecards.json`) keyed by ticker. Never rename/remove fields or bump `meta.version` casually (= breaking).
- **shared-contracts** is extracted into its own repo only when a second consumer needs the types; until then the embedded `contract/` package + vendored TS is sufficient and avoids premature multi-repo overhead.

## 5. Naming + remote setup

- **trading-analysis** — exists, this repo (`origin` = GitHub `romarin-hsieh/trading-analysis`, branch `master`). Promote `main` for PRs per repo convention.
- **investment-dashboard** — exists, Public, GitHub Pages. No rename. Add a `contract/` vendoring dir + CI schema-validation step.
- **trading-data** — **create new, Public** (`romarin-hsieh/trading-data`). Public for free unlimited Actions minutes. Standard layout: `.github/workflows/` (cron ingest), `crawlers/`, `youtube/`, `data/` (git-as-DB), R2 push step.
- **shared-contracts** — defer; create Public only at extraction time, then update both Python (`contract/`) and dashboard to consume it.

All repos Public (hard constraint), MIT-licensed; AGPL-derived logic referenced only, never copied; permissive-licensed code carries attribution.

---

Key grounding notes for the master plan: the existing package already keeps a strict `api.py`-only public boundary (UI imports nothing internal), so adding `contract/exporters.py` behind `api.export_dashboard_json()` fits cleanly. Config files live in `configs/` (plural) today; the brief's `config/stocks.json` is the *dashboard's* universe SoT, in the investment-dashboard repo — not this one. Relevant files: `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\api.py` (extend), `...\docs\architecture-decision-multirepo.md` (DAG), `...\docs\architecture-integration.md` (dashboard contract + AUGMENT decision).


## 附錄 B — 資料契約

# Data Contract

> **Ownership.** `trading-analysis` is the contract's single source of truth (SoT). It defines the shapes in Pydantic v2, serializes them via `api.export_dashboard_json()`, and emits JSON Schema for cross-language validation. `investment-dashboard` is a pure consumer: it reads the JSON and renders. The contract is **additive-safe** — the dashboard has **no Zod on `dashboard_status.json`** and reads by key, so adding fields never breaks it (`DATA_DICTIONARY.md:463`). The rule below is absolute: **never rename/remove existing keys and never bump `meta.version` for additive change.**

All models live in a new module `src/trading_analysis/contract/models.py`. They reuse repo conventions already in `strategy/signal.py` and `data/schema.py` (Pydantic v2 `BaseModel`, `Field`, `field_validator`, `model_config`).

## 1. Pydantic v2 models

### Shared enums / aliases

```python
from __future__ import annotations
from datetime import date, datetime
from enum import IntEnum
from typing import Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

Stance      = Annotated[float, Field(ge=-1.0, le=1.0)]   # bearish..bullish
Unit        = Annotated[float, Field(ge=0.0, le=1.0)]    # 0..1 conviction/score
Ticker      = Annotated[str, Field(min_length=1, max_length=12)]
Market      = Literal["US", "TW"]
SourceType  = Literal["earnings_call","sec_filing","youtube","substack",
                      "podcast","analyst_rating","congress","superinvestor_13f","news"]
```

### Signal — a rule's per-bar opinion (contract-facing superset of the internal `strategy.signal.Signal`)

```python
class Direction(IntEnum):
    SHORT = -1; FLAT = 0; LONG = 1

class Signal(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    ticker: Ticker
    as_of: date                 # POINT-IN-TIME: bar/disclosure date this signal is keyed to
    strategy: str               # e.g. "minervini_trend", "magic_formula", "kronos_trend"
    direction: Direction = Direction.FLAT
    strength: Unit = 0.0
    horizon_days: int | None = None
    entry: float | None = None
    stop: float | None = None        # reuse existing ATR/Chandelier exit layer
    target: float | None = None
    reason: str | None = None
    @field_validator("ticker")
    @classmethod
    def _up(cls, v): return v.strip().upper()
```

### FactorScore — one named score for one ticker, point-in-time

```python
class FactorScore(BaseModel):
    ticker: Ticker
    as_of: date
    name: str                   # "rs_rating","magic_formula_rank","factor_quality",...
    value: float
    rank: int | None = None     # cross-sectional rank if applicable
    percentile: Unit | None = None
    universe: str = "us_top50"  # which universe the rank/percentile is relative to
```

### OpinionEvent — the unified "voice" model (all `source_type` variants in one table)

Mirrors the brief §6 exactly. Modality-agnostic so YouTuber / earnings call / 13F / congress all backtest the same way (enter at `published_at`, measure 1/5/20/60d forward returns).

```python
class OpinionEvent(BaseModel):
    source_type: SourceType
    source_name: str            # channel/author/fund/lawmaker; the scorecard key
    url: str | None = None
    published_at: datetime      # == as_of (DISCLOSURE date; congress uses disclosure, NOT txn)
    ticker: Ticker | None = None
    market: Market = "US"
    doc_type: str | None = None # "PTR","13F-HR","8-K","transcript","video",...
    stance: Stance = 0.0
    conviction: Unit = 0.0
    horizon_days: int | None = None
    entry: float | None = None
    exit: float | None = None
    target: float | None = None
    stop: float | None = None
    event_class: str | None = None      # "insider_cluster_buy","pead","item_2.02",...
    sentiment_finbert: float | None = Field(default=None, ge=-1.0, le=1.0)
    raw_text_ref: str | None = None     # pointer into trading-data store, not the blob
    extracted_by: str | None = None     # "haiku-4.5-batch","finbert","rule:edgar-form4"
```

Source-specific fields (e.g. congress `amount_range`, 13F `shares_delta`, news `provider`) ride in an **optional** `meta: dict[str, Any] = {}` — keeps the table single while staying additive.

### DashboardEntry — superset of the existing `dashboard_status.json` entry

Every existing key is **required** (it is de-facto required in production, incl. `sector_trace`, which is undocumented but present on 558/558 entries). `signal` is typed as free `str` to match reality (the documented enum drifted; front-end renders unknown strings as neutral). The two new keys — `scores` and `opinions` — are **optional** and default to `None`/empty so old readers ignore them.

```python
class Coordinates(BaseModel):
    x_trend: float; y_momentum: float; z_structure: float

class TracePoint(BaseModel):
    x_trend: float; y_momentum: float; z_structure: float
    date: str | None = None     # oldest-first ordering preserved by list order

Trace30 = Annotated[list[TracePoint], Field(min_length=0, max_length=30)]

class EntryScores(BaseModel):        # the NEW augmentation block (all optional)
    minervini_trend_template: bool | None = None
    magic_formula_rank: int | None = None
    factor_value: float | None = None
    factor_quality: float | None = None
    rs_rating: int | None = Field(default=None, ge=1, le=99)
    insider_cluster: float | None = None     # Form-4 cluster-buy intensity
    pead_sue: float | None = None            # standardized earnings surprise
    congress_net: float | None = None        # net disclosed buy/sell pressure
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)

class DashboardEntry(BaseModel):
    model_config = ConfigDict(extra="allow")   # tolerate future dashboard-side keys
    # --- existing contract (do NOT change) ---
    ticker: Ticker
    sector: str
    strategy: str
    signal: str
    reason: str
    commentary: str
    price: float
    change_percent: float
    date: str
    coordinates: Coordinates
    trace: Trace30
    sector_trace: Trace30
    # --- NEW, additive-safe ---
    scores: EntryScores | None = None
    opinions: list[OpinionEvent] | None = None
```

## 2. Top-level envelope

```python
class Meta(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: str                       # echo the dashboard's value; never bump for additive change
    generator: str = "trading-analysis"
    contract_version: str = "1.0.0"    # OUR additive semver (see §4); lives beside, not replacing, version

class DashboardStatus(BaseModel):
    meta: Meta
    updated_at: str                    # ISO-8601 string (matches dashboard)
    global_regime: str                 # free string, e.g. "RISK_ON" / "200SMA_GATE_OPEN"
    data: list[DashboardEntry]
```

**Backward-compatible emission.** Read the live `dashboard_status.json`, copy `meta` through **unchanged** (preserving the existing `version`), set our additive marker only in `meta.contract_version`, and append `scores`/`opinions` to each entry. Because the dashboard reads by key and has no schema gate on this file, untouched keys + new optional keys = zero regression. `extra="allow"` on `Meta`/`DashboardEntry` means if the dashboard later adds its own keys, round-tripping through our models won't drop them.

## 3. `api.export_dashboard_json()` contract

Add to `src/trading_analysis/api.py`, following the existing export-function style.

```python
def export_dashboard_json(
    cfg: AppConfig | str | Path | None = None,
    *,
    signals: list[Signal],
    scores: list[FactorScore],
    opinions: list[OpinionEvent],
    base_status_path: str | Path,     # existing dashboard_status.json to augment
    out_dir: str | Path,
    as_of: date | None = None,        # PIT cutoff; defaults to today
) -> dict[str, Path]:
    ...
```

**Inputs → artifacts.** Loads `base_status_path`, indexes `signals`/`scores`/`opinions` by `ticker`, merges them into each `DashboardEntry.scores`/`.opinions`, runs `DashboardStatus.model_validate(...)` (validation **is** the gate — invalid contract aborts the write), and emits to `out_dir`:

| Artifact | Source model | Content |
|---|---|---|
| `dashboard_status.json` | `DashboardStatus` | the validated superset envelope |
| `opinions.json` | `list[OpinionEvent]` | full raw opinion feed (denormalized, for the opinion view) |
| `creator_scorecards.json` | derived | per-`source_name` finfluencer scorecard: hit-rate / IR / win-loss / Sharpe / MDD over 1/5/20/60d forward returns |

Returns `{"dashboard_status": Path, "opinions": Path, "creator_scorecards": Path}`. Writes are atomic (`*.tmp` → `os.replace`) so a half-written file is never published. Add `"export_dashboard_json"` to `__all__`.

## 4. JSON Schema generation + contract versioning

Generate schema from the SoT in a tiny build step (CI gate, e.g. `scripts/emit_schema.py`):

```python
import json
from trading_analysis.contract.models import DashboardStatus, OpinionEvent
for model, name in [(DashboardStatus,"dashboard_status"),(OpinionEvent,"opinion_event")]:
    schema = model.model_json_schema(mode="serialization")
    (Path("contract/schema")/f"{name}.schema.json").write_text(json.dumps(schema, indent=2))
```

These `*.schema.json` files are committed and consumed cross-language: the dashboard repo validates its sample fixtures (e.g. via `ajv`) and can codegen TS types from the same JSON Schema — one SoT, two languages, no hand-kept duplicate.

**Contract-versioning rule (`meta.contract_version`, semver, independent of dashboard's `meta.version`):**
- **PATCH** — docs/description only.
- **MINOR** — *additive only*: new optional field, new enum member, new sibling artifact. This is the **only** change class allowed to ship to production unilaterally (dashboard reads-by-key absorbs it). CI gate asserts every new field is `Optional`/has a default.
- **MAJOR** — any rename/removal/type-narrowing/required-promotion. **Forbidden** on the live `dashboard_status.json` shape — requires a coordinated dashboard release first. CI diffs the new schema against the previous committed schema and fails the build if a MAJOR-class change appears without a `contract_version` major bump.

## 5. Point-in-time `as_of` discipline behind the contract

Every contract field that can be backtested carries an `as_of`/`published_at` that is the **disclosure/filing date**, never the event date — the discipline is enforced in the stored DuckDB tables that feed `export_dashboard_json()`, not at serialization time:

- **Signals/FactorScores**: stored per `(ticker, as_of, name)`; emission selects `as_of <= cutoff`.
- **Fundamentals (EDGAR companyfacts)**: keyed by `filed` date — the row only becomes visible on/after `filed`.
- **Congress (PTR)**: `published_at` = **disclosure date** (sidesteps the 45-day reporting lag); the transaction date is informational `meta` only.
- **13F / earnings / Form-4 / 8-K**: `published_at` = filing/accepted timestamp.

So the contract is a **point-in-time snapshot**: re-running `export_dashboard_json(as_of=D)` reproduces exactly what was knowable at date `D`, which is what makes the downstream scorecards in `creator_scorecards.json` honest.

---

**Relevant files** (all absolute): new module to author — `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\contract\models.py`; export to extend — `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\api.py`; existing convention anchors — `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\strategy\signal.py` and `...\src\trading_analysis\data\schema.py`; schema output dir to create — `...\contract\schema\`.


## 附錄 C — Dashboard 重構遷移

# Dashboard Refactor / Migration Plan (investment-dashboard)

> **Prime directive: never break production.** `investment-dashboard` is a live Vue3 static SPA on GitHub Pages (Public), v2.5 "Quant Edition", ~412 commits, zero runtime backend. Every front-end read is a static JSON precomputed by its in-repo GitHub Actions ETL. The decision is **AUGMENT, not replace**. We move in four reversible phases; each phase ships behind additivity or env-config, and is independently rollback-able. We never rename/remove an existing field, never bump `meta.version` casually, and we keep the comet viz + the validated ATR/Chandelier exit untouched.

## Phase 0 — Additive: emit new optional signals, dashboard ignores them

**Goal:** trading-analysis writes *new* data that the live dashboard structurally ignores, so we can A/B our Minervini/RS/factor signals against the (validation-failed) Phase-3 entry signals with **zero front-end change**.

**Approach.** trading-analysis `api.export_dashboard_json()` writes our signals two ways, both zero-risk per the contract analysis (`DATA_DICTIONARY.md:463` — no Zod on `dashboard_status.json`, front-end reads by key):
- **Per-entry `scores:{}`** — `minervini_trend_template`, `rs_rating`, `stage`, `trend_template_pass`, `magic_formula_rank`, `factor_value`, `factor_quality`. Unknown keys are dropped by the key-based reader.
- **Sibling files** — `public/data/signals_minervini.json` etc., keyed by ticker, that the production bundle does not fetch yet.

**File touch-points (investment-dashboard):** *none required for safety.* The only commits land in `public/data/` (data lake) via the ETL/our exporter. Optionally add a hidden A/B inspector route (e.g. `src/views/SignalLab.vue` + a lazy route) that fetches the sibling file *only when navigated to* — it cannot affect the default render path.

**A/B method.** For the shared universe (`config/stocks.json`, ~50 tickers), tabulate our `signal`/`stage` vs Phase-3's `BUY_BREAKOUT/BUY_DIP/SELL_CLIMAX` per ticker per day. Run the same forward-return scorecard (1/5/20/60d) the `TAG_VALIDATION_REPORT` used, so we beat "Toxic Alpha" (real 0.78 vs random 1.09) on its own yardstick before any switch.

**Rollback.** Delete the sibling JSON / stop writing `scores{}`. Nothing in prod referenced them.

**Verify no regression.** Diff a built `dist/` before vs after the data change — identical. `JSON.parse` every emitted file in CI. Confirm production view renders unchanged (comet, classifications, exits) with the augmented JSON loaded locally (`npm run preview`).

## Phase 1 — Switch the data source to the external data-repo / R2 CDN

**Goal:** point the dashboard's fetch at the external `trading-data` repo / Cloudflare R2 CDN via env-config, **keeping the local `public/data/` fallback intact**. This decouples *where* data comes from before we touch *what* signals mean.

**File touch-points.**
- **`.env` / `.env.production`** — add `VITE_DATA_SOURCE_URL` (empty = current relative `/data/` behavior; preserves today's path).
- **The data-fetch layer** — the services the brief names `precomputedOhlcvApi` / `QuantDataService` (locate via the `fetch('...data/...')` / `import.meta.env` call sites). Introduce one `resolveDataUrl(path)` helper: `BASE = import.meta.env.VITE_DATA_SOURCE_URL ?? ''`. Every existing fetch becomes `resolveDataUrl('dashboard_status.json')`. Default base = `''` ⇒ byte-for-byte current behavior.
- **3-tier cache** — preserve it exactly (memory → static JSON → Yahoo live fallback). Add the CDN as the *primary* tier and keep same-origin `/data/` as the **fallback tier on fetch failure** (try CDN, `catch` → local). CORS/caching: R2 must send `Access-Control-Allow-Origin` for the Pages origin and sane `Cache-Control`.

**Rollback.** Unset `VITE_DATA_SOURCE_URL` (or revert the env in the Pages build) and redeploy — fetches snap back to same-origin `/data/`. The in-repo ETL is still running in Phase 1, so local data is fresh. One-commit / one-variable revert.

**Verify no regression.** In the browser Network tab, confirm requests hit the CDN with 200s and CORS headers; kill the CDN (bad URL) and confirm the local fallback still renders (cache tier proven). Schema-diff the CDN `dashboard_status.json` against the locally-produced one — must be a structural superset (Phase-0 additivity guarantees this).

## Phase 2 — Replace the (validation-failed) Phase-3 ENTRY signals; KEEP comet + ATR/Chandelier EXIT

**Goal:** the front end now *consumes* our trend-template/RS/factor entry signals instead of the toxic Phase-3 entry signals — while **keeping the comet coordinates/trace/sector_trace viz and the validated ATR/Chandelier exit logic** (the only proven-edge asset, 5.8x even on random entries).

**Critical separation.** `daily_update.py` produces *two distinct things* in the same file: (a) `coordinates{x_trend,y_momentum,z_structure}` + `trace[30]` + `sector_trace[30]` (the comet — keep), and (b) the rule entry `signal` strings (toxic — replace). We swap only (b).

**File touch-points.**
- **trading-data / exporter** — `coordinates`+`trace`+`sector_trace` keep coming from the ATR/Chandelier+comet logic ported from `daily_update.py` (do **not** re-derive these from our engine; reuse the validated math). The `signal`/`reason`/`commentary` fields are now written by trading-analysis (Minervini stage → BUY/HOLD/SELL). `signal` is a de-facto free string (front end renders unknown strings neutral), so introduce new values carefully and map them to the existing visual buckets.
- **investment-dashboard** — minimal: wherever `signal` drives color/label, ensure our new enum values map to existing styles (extend the signal→style lookup, e.g. in the comet component / legend). **Do not** touch coordinate math or exit logic. Update `src/types/index.ts` + `DATA_DICTIONARY.md` to *document* the new `signal` values and `scores{}` (doc-only, no Zod break).

**Rollback.** This is why Phase 0/1 exist: flip `VITE_DATA_SOURCE_URL` back to a data bundle whose `signal` field is the old Phase-3 output (the in-repo ETL or a pinned CDN prefix). Because the swap is *data-driven*, rollback is a data-source flip, not a code revert. Keep the old Phase-3 `signal` writer alive (dormant) one release for instant A/B.

**Verify no regression.** Comet renders identically (coordinates/trace unchanged — assert numeric equality vs Phase-1 output). Exit markers (ATR/Chandelier) unchanged. New `signal` values all resolve to a visual bucket (no "neutral fallback" leaks for known values). Run the Phase-0 scorecard on the now-live signals to confirm the edge held.

## Phase 3 — Retire the in-repo ETL (move to trading-data)

**Goal:** delete the dashboard's in-repo ETL now that data flows from `trading-data` → CDN.

**File touch-points (investment-dashboard).** Remove `.github/workflows/daily-data-update.yml` (Phase 1/2/3 ETL: yfinance, yahoo-finance2, Puppeteer F&G, Dataroma, `scripts/production/daily_update.py`, `strategy_selector.py`). Move/port the comet+ATR/Chandelier code into `trading-data` *first*, then delete here. Drop now-dead `package.json` ETL deps (puppeteer, yahoo-finance2). `public/data/` may stop being committed (front end reads CDN) — but **keep a small frozen `public/data/` seed** as the Phase-1 fallback tier unless we accept losing offline/fallback.

**Rollback.** Revert the workflow-deletion commit (it's a pure delete) → ETL runs again and repopulates `public/data/`; combined with unsetting `VITE_DATA_SOURCE_URL`, the dashboard is fully self-contained again. This is the highest-blast-radius phase, so do it last and only after Phases 0–2 have soaked in production.

**Verify no regression.** With ETL gone, the site must still fully render purely from the CDN (disable network to the old ETL outputs and confirm). Confirm GitHub Actions minutes drop to ~0 for the dashboard repo.

## Contract-drift risks (flag throughout)

1. **No Zod on `dashboard_status.json`** is a double edge: additive fields are safe, but it also means **nothing fails loudly** if trading-analysis stops emitting a *required-by-usage* field. Highest risk: **`sector_trace` is undocumented yet present in 558/558 entries and is read** — treat it as mandatory. Our exporter MUST emit `coordinates`, `trace[30]`, `sector_trace[30]`, `ticker`, `sector`, `signal`, `price`, `change_percent`, `date` or the comet silently breaks.
2. **`signal` is a free string** (front end renders unknown values neutral). A typo'd enum won't throw — it'll just render grey and look "fine," masking a logic break. Guard with a producer-side enum + a CI check that every emitted `signal` maps to a known visual bucket.
3. **`meta.version` semantics** — do not bump on additive changes; the front end may branch on it. Treat a version bump as a breaking signal reserved for true contract breaks.
4. **Pydantic↔TS divergence** — `src/types/index.ts` is the dashboard's SoT but has no automated tie to our pydantic models. Add a CI gate (Phase 0 onward): generate JSON Schema from pydantic, diff against types derived from `index.ts`; fail the build on a removed/renamed field. This is the single most important guard against silent drift across the three repos.
5. **`config/stocks.json` is the real universe** (not the nonexistent `universe.json`). trading-analysis must read the same file/coverage; a universe mismatch yields missing comet dots without any error.

---

**Key file paths referenced (investment-dashboard):** `.env` / `.env.production` (new `VITE_DATA_SOURCE_URL`), the `precomputedOhlcvApi`/`QuantDataService` fetch layer (Phase 1 `resolveDataUrl` helper), `src/types/index.ts` + `docs/specs/DATA_DICTIONARY.md` (doc-only updates), the comet component's `signal`→style lookup (Phase 2), `.github/workflows/daily-data-update.yml` + `scripts/production/daily_update.py`/`strategy_selector.py` (Phase 3 retirement), `public/data/` (data lake / frozen fallback seed), `config/stocks.json` (shared universe). Section is self-contained and drops into the plan as **"Dashboard Refactor."**


## 附錄 D — trading-data 攝取 repo

# Ingestion (trading-data)

The `trading-data` repo is the **acquisition + raw-storage tier** of the DAG: `trading-data ──raw JSON──▶ trading-analysis ──contract JSON──▶ investment-dashboard`. It is a **Public** repo (free unlimited Actions minutes). It owns *no* business logic — it fetches, normalizes to point-in-time rows, and persists. Two infra primitives carry the whole design: **GitHub Actions as a serverless cron** and **git-as-DB** (versioned cold store) mirrored to **Cloudflare R2** (zero-egress hot serving).

## Directory layout

```
trading-data/
├── .github/workflows/
│   ├── ingest-fast.yml          # 2×/day: RSS detect + EDGAR + Finnhub + FinMind (light)
│   ├── ingest-slow.yml          # 1×/day: congress, Dataroma, XBRL, article/transcript fetch
│   └── push-r2.yml              # reusable: rclone sync data/latest → R2 (called by both)
├── crawlers/
│   ├── tiers.py                 # Tier0..3 dispatcher (RSS→r.jina→Crawl4AI→Worker→Playwright)
│   ├── extract.py               # trafilatura.extract(html, output_format="markdown")
│   ├── news_rss.py              # feedparser: Reuters/Yahoo/SeekingAlpha/Substack /feed
│   └── medium_worker.py         # CF-Worker proxy client for medium.com/_/graphql
├── youtube/
│   ├── detect_rss.py            # feeds/videos.xml?channel_id=UC… diff vs seen-set
│   ├── transcript.py            # youtube-transcript-api → yt-dlp --write-auto-sub
│   └── channels.yml             # ~10 creators: UC… id + watchlist universe
├── edgar/
│   ├── form4.py                 # edgartools: insider transactions
│   ├── form_8k.py               # 8-K item codes (2.02/1.01/5.02/8.01)
│   └── xbrl_facts.py            # companyfacts EPS for PEAD/fundamentals
├── congress/
│   ├── stock_watcher.py         # senate/house-stock-watcher JSON (primary)
│   ├── house_clerk_ptr.py       # disclosures-clerk.house.gov PTR (verification)
│   └── crosscheck.py            # Capitol Trades / Quiver web (cross-check only)
├── dataroma/
│   └── scrape.py                # dataroma.com/m/home.php (ports dashboard's Phase-2 scraper)
├── fundamentals/
│   ├── finmind_tw.py            # TW price + 籌碼/三大法人 + 融券
│   └── finnhub_ratings.py       # analyst ratings (already-structured "calls")
├── lib/
│   ├── schema.py                # row dataclasses; enforces as_of on every source
│   ├── store.py                 # write partitioned parquet/JSON, dedup, manifest
│   └── state/seen.json          # video/filing dedup sets (committed)
├── data/                        # ← git-as-DB store (see below)
└── prices/yfinance_us.py        # US OHLCV (yfinance)
```

## Storage: git-as-DB + R2 (point-in-time on every source)

The store is **single-writer** (only Actions commits), partitioned, total **< 1 GB**. Hot tables → daily-partitioned **parquet**; small/append-mostly opinion/event rows → **JSON Lines** (readable diffs). `data/latest/` holds the newest snapshot mirrored to R2; `data/raw/` keeps the versioned audit trail.

```
data/
├── latest/                              # mirrored to R2 (hot, $0 egress)
│   ├── insider_txns.parquet
│   ├── congress_txns.parquet
│   ├── superinvestor_holdings.parquet
│   ├── opinion_event.jsonl              # youtube/substack/earnings_call/analyst/congress/13F
│   ├── events_8k.parquet
│   ├── xbrl_eps.parquet
│   ├── analyst_ratings.parquet
│   ├── tw_chips.parquet                 # FinMind 三大法人/融券
│   └── manifest.json                    # {table: {rows, sha, generated_at}}
└── raw/
    ├── ohlcv/us/dt=2026-06-14/*.parquet
    ├── edgar/form4/dt=2026-06-14/*.json
    ├── congress/dt=2026-06-14/*.json
    ├── articles/dt=2026-06-14/*.md      # trafilatura markdown + metadata
    └── transcripts/raw/<videoId>.json   # captions; Whisper output lands here from home box
```

**The `as_of` rule (the load-bearing column).** Every row carries `as_of` = the **publication/disclosure/filing** instant, never the event instant, so `trading-analysis` can `filter as_of <= sim_date`:

| Table | `as_of` source | Trap avoided |
|---|---|---|
| `congress_txns` | **`disclosure_date`** (not `txn_date`) | 45-day PTR lag → look-ahead |
| `insider_txns` | **`filing_date`** (not transaction date) | Form 4 filing delay |
| `superinvestor_holdings` | **13F filing date** | ~45-day quarterly 13F lag |
| `analyst_ratings` | rating publish date | vendor "history" is current-snapshot, not PIT |
| `opinion_event` | `published_at` | dated-call discipline |

`congress_txns(politician, chamber, ticker, txn_type, amount_range, txn_date, disclosure_date AS as_of, source)`. Capitol Trades / Quiver are written only into a `*_xref` sidecar for reconciliation, never as backtest truth.

**Why two stores:** git gives free, conflict-free versioned system-of-record (single writer ⇒ no merge pain) + audit trail; R2 gives zero-egress serving the Vue site reads. Push via `rclone sync data/latest <r2>:bucket/latest` (S3-compatible). To stay under 1 GB, `data/raw/` keeps a rolling window (e.g. shallow-prune partitions > 18 months via a monthly maintenance job).

## Crawler tiers — Actions vs home box

| Tier | Tool | Targets | Runs in |
|---|---|---|---|
| **0** | feedparser (RSS) | News/Substack/YouTube detect; EDGAR/Finnhub/FinMind/stock-watcher APIs | **Actions** |
| **1** | `r.jina.ai` + Crawl4AI → **trafilatura** | Article body → Markdown + publish-date | **Actions** (foreign IP dodges AWS-range block) |
| **2** | **Cloudflare Worker** proxy | `medium.com/_/graphql` | Worker (in-network → bypasses 403) |
| **3** | Playwright(Python) + **Camoufox**; curl_cffi for JSON | Cloudflare-hard pages, scripted auth, XHR/GraphQL capture | **Home box (residential IP)** |
| — | yt-dlp / youtube-transcript-api; **faster-whisper large-v3** | Captions, then ASR fallback | **Home box** (YouTube throttles cloud IPs) |

**Decision rule = cheapest layer first** (RSS → trafilatura → r.jina/Crawl4AI → curl_cffi → Camoufox). The real lever is **IP placement, not code**: anything anti-bot or YouTube-throttled runs on the home box; Actions keeps RSS detection, the EDGAR/congress/Finnhub/FinMind/Dataroma fetches, trafilatura extraction, dedup, commit, and R2 push. Whisper (the 20–40% of videos lacking captions) is **offloaded to the home box GPU**; its output is committed back into `data/raw/transcripts/` on the next run.

## Representative workflow YAML

`ingest-slow.yml` (the heavier 1×/day job; `ingest-fast.yml` is the same shape with the RSS/EDGAR/Finnhub steps only). Cron uses an **odd minute, off the hour** (`:23`) since scheduled triggers are best-effort and `:00` is congested; `workflow_dispatch` is the manual fallback; the daily cadence itself keeps the repo from auto-disabling after ~60 idle days.

```yaml
name: ingest-slow
on:
  schedule:
    - cron: "23 9 * * *"        # 09:23 UTC daily (odd minute, off-hour)
  workflow_dispatch:            # manual fallback
permissions:
  contents: write              # single writer commits to git-as-DB
concurrency:
  group: ingest                # never two writers at once
  cancel-in-progress: false
jobs:
  ingest:
    runs-on: ubuntu-latest
    timeout-minutes: 50
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -e . feedparser trafilatura edgartools yt-dlp \
               youtube-transcript-api crawl4ai duckdb pandas pyarrow
      - name: News + Substack RSS (Tier0) + article text (Tier1)
        run: python -m crawlers.news_rss && python -m crawlers.extract
      - name: YouTube RSS detect (transcripts run on home box)
        run: python -m youtube.detect_rss          # diffs seen.json, queues videoIds
      - name: EDGAR Form4 / 8-K / XBRL EPS
        env: { SEC_USER_AGENT: ${{ secrets.SEC_UA }} }   # SEC requires UA
        run: python -m edgar.form4 && python -m edgar.form_8k && python -m edgar.xbrl_facts
      - name: Congress (stock-watcher JSON primary; Clerk PTR verify; CT/Quiver xref)
        run: python -m congress.stock_watcher && python -m congress.house_clerk_ptr \
               && python -m congress.crosscheck
      - name: Dataroma 13F (ports dashboard Phase-2 scraper)
        run: python -m dataroma.scrape          # writes as_of = 13F filing date
      - name: FinMind TW (price + 籌碼/三大法人) + Finnhub ratings
        env: { FINMIND_TOKEN: ${{ secrets.FINMIND }}, FINNHUB_KEY: ${{ secrets.FINNHUB }} }
        run: python -m fundamentals.finmind_tw && python -m fundamentals.finnhub_ratings
      - name: Commit git-as-DB
        run: |
          git config user.name  "trading-data-bot"
          git config user.email "bot@users.noreply.github.com"
          git add data/ lib/state/seen.json
          git commit -m "ingest $(date -u +%FT%TZ)" || echo "no changes"
          git push
      - name: Push latest → Cloudflare R2 (zero egress)
        uses: ./.github/workflows/push-r2.yml      # rclone sync data/latest R2:bucket/latest
        env:
          R2_ENDPOINT:   ${{ secrets.R2_ENDPOINT }}
          R2_ACCESS_KEY: ${{ secrets.R2_ACCESS_KEY }}
          R2_SECRET_KEY: ${{ secrets.R2_SECRET_KEY }}
```

The home box runs a small companion cron (its own residential-IP script, not Actions) that pulls the queued `videoId`s, runs `youtube-transcript-api → yt-dlp → faster-whisper`, and pushes transcripts/Camoufox-fetched pages back into the repo. LLM (Haiku Batch) distillation lives in `trading-analysis`, not here — `trading-data` stops at raw rows.

## Monthly cost (< $15)

| Item | Tier | $/mo |
|---|---|---:|
| GitHub Actions (cron, **public** repo) | free, unlimited | **$0** |
| git `trading-data` store (< 1 GB) | free | **$0** |
| Cloudflare R2 (serve ~1–2 GB, $0 egress) | within 10 GB free | **$0** |
| Cloudflare Worker (Medium proxy) | within 100k req/day | **$0** |
| Crawlers (RSS, r.jina.ai keyless, Crawl4AI self-host, trafilatura) | free | **$0** |
| YouTube detect (RSS) + transcripts (api/yt-dlp) | free, no quota | **$0** |
| EDGAR / FinMind / Finnhub free / stock-watcher JSON / Dataroma | free | **$0** |
| Whisper + Camoufox (home box, residential IP) | self-host | **$0** (≈ electricity) |
| Buffer (Worker Paid $5 if Medium volume grows; extra Whisper) | — | **~$2–5** |
| **trading-data subtotal** | | **$0–5** |

LLM distillation (Haiku 4.5 Batch ≈ $2.2/mo) is billed in `trading-analysis`; combined system stays at **~$2–7/mo**, well inside the $15 cap (pessimistic private-repo + all-Sonnet + paid-Worker path ≈ $10–12).

---

Relevant source files I read: `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\design-brief.md`, `docs\ingestion-pipeline.md`, `docs\alt-data-and-content-expansion.md` (incl. §G), `docs\tech-selection-scraping-tools.md`, `docs\architecture-integration.md` (existing dashboard Phase-1/2/3 ETL + Dataroma per-symbol scraper at 02:00 UTC daily). No files were written per instructions — this section is returned above for inclusion as the "Ingestion (trading-data)" section.


## 附錄 E — 引擎 build roadmap

# Engine Roadmap (trading-analysis)

> Phased build plan M0..M7 for the quant/opinion engine. Every phase is **zero-new-cost** (OHLCV via yfinance + SEC EDGAR companyfacts only — no paid feeds). Ordering follows **dependency + value**: the ML/regime bedrock first (it gates everything labeled "M" or meta-labeled), then features → rules → factors → portfolio → opinion/alt-data → contract. Each phase names its modules, the **extraction specs / source repos** that feed it (per `extraction-backlog.md`), the **deliverable**, and the **verification** (which `data-and-backtest-rigor.md` scorecard items must pass + the concrete vectorbt test). The hard gate throughout: scorecard **#1 / #2 / #5 / #6 / #7** — any Fail = the return claim is not trusted.

## Sequencing principle

`regime/` + `labeling/` are the bedrock because the CANSLIM **"M"** gate and any meta-labeled/ML strategy depend on them; building rules first would re-create the "Toxic Alpha" trap the dashboard already hit. Features feed factors feed portfolio. Opinion/alt-data is value-additive but rides on the same `as_of`/point-in-time plumbing established in M0–M1, so it lands once the rigor harness exists to score it. The `contract/` export is last because it should serialize *validated* signals, not raw ones — though a thin `dashboard_status.json` superset stub can land opportunistically in M1.

---

## M0 — Foundation: labeling/ + regime/ (the "M" bedrock)

**Modules:** `regime/` (200-SMA gate + HMM/MarkovRegression overlay + GARCH feature), `labeling/` (triple-barrier + trend-scanning + purged/embargoed CV).

**Feeds (extraction specs / repos):**
- 200-SMA gate ← QuantResearch `mebane_faber_taa.py:52` (simplest defensible "M", aligns Minervini "market in confirmed uptrend").
- HMM 2-state ← QuantResearch `hidden_markov_chain.py:79` + `gaussian_mixture_markov_switching.ipynb`. **Must add** state-label alignment (HMM state index is random) + VIX/SMA cross-check the repo omits; emit high-vol probability as a continuous risk-off scalar.
- GARCH conditional vol ← QuantResearch `arima_garch.ipynb` (`arch`); cache the AIC grid, never fit live.
- Triple-barrier ← rewritten from **de Prado AFML Ch3 / mlfinlab** (jo-cho only discusses, never implements). pt/sl + vertical barrier.
- Trend-scanning (t-value = sample weight) ← jo-cho `trend_scanning.py:32-99` (portable).
- Purged + embargoed / Combinatorial Purged CV ← jo-cho `cross_validation.py`, preferring upstream mlfinlab/`timeseriescv`.

**Deliverable:** `regime.classify(ohlcv) -> {regime_state, risk_off_prob, cond_vol}` on the smoke universe + benchmark (add SPY to smoke). `labeling.triple_barrier(...)`, `labeling.trend_scan(...)`, and a `PurgedKFold`/`CombinatorialPurgedCV` splitter compatible with vectorbt's `Splitter`.

**Verification:** Scorecard **#1 (look-ahead)** — labels must use only forward bars within the barrier window; unit test that shifting the entry +1 bar changes labels deterministically. **#10 (reproducible)** — seed-fixed HMM + labels reproduce identically. **vectorbt test:** wrap SMA-crossover in a purged-CV `Splitter` loop and confirm no train/test bar overlap (assert embargo gap ≥ label horizon). Regime gate verified by overlaying classified risk-off windows on 2022 drawdown.

---

## M1 — features/ (breadth + ADF + mean-reversion pack)

**Modules:** `features/`.

**Feeds:** Mean-reversion pack (Hurst / variance-ratio / half-life) ← QuantResearch `mean_reversion.py:30-102` (pure NumPy, easiest lift). Indicator breadth (Donchian/Keltner/Ulcer/ADX/Vortex/CCI/Aroon/MFI/CMF/TSI/Williams%R/PPO…) ← jo-cho `tautil.py` — **add the `ta` library as a dependency, do not hand-code**. ADF stationarity filter ← same; keep only stationary series as ML inputs. Microstructure (Corwin-Schultz, Amihud/Kyle λ, VPIN) ← jo-cho `microstructure_features.py` (AFML Ch19, rewritten). MDI/MDA importance + >0.8 correlation pruning ← jo-cho plain sklearn, **adding per-tree mean±std + MDA permutation**.

**Deliverable:** `features.build(ohlcv) -> DataFrame` with an ADF-survivor column set, a mean-reversion sub-pack, and a feature-importance/correlation-prune report.

**Verification:** Scorecard **#1** — every feature carries `available_at <= bar_ts`; the +1-bar shock test on any feature-driven signal must not collapse returns. **#2 (survivorship)** — features computed on point-in-time-adjusted prices (dividend/split-adjusted), never `SELECT DISTINCT ticker`. **vectorbt test:** feed top mean-reversion features into a z-score reversion sim on the smoke universe; confirm IC sign stability across the purged-CV folds from M0.

---

## M2 — strategy/rules/ (Minervini/CANSLIM family + pair-cointegration)

**Modules:** `strategy/rules/` — `minervini_trend`, `vcp`, `magic_formula`, `graham`, `canslim`, pair-cointegration; plus `parabolic_sar`, `rsi`.

**Feeds:** Pair/cointegration (EG 2-step + rolling z-score + per-step re-test) ← quant-trading `Pair trading backtest.py:64,108,157` — **highest value, port the math, vectorize the loops**. Parabolic SAR ← `Parabolic SAR backtest.py:30,98`. RSI ← `RSI…backtest.py:60,86`. Minervini Trend Template + RS Rating: trailing-return percentile across the universe (no IBD feed), RS≥70 gate (per `data-and-backtest-rigor.md` §A.1). Magic Formula / Graham / CANSLIM fundamentals ← SEC EDGAR companyfacts (point-in-time, `filed` date), ratios via FinanceToolkit (MIT) — never hand-code Graham/Piotroski/QMJ.

**Deliverable:** Each rule implements the existing `Signal`/`Direction` + `to_pivot()` interface and registers in `api.py:_RULES`. Every entry is **AND-gated by the M0 regime state**.

**Verification:** Scorecard **#6 (cost/slippage)** — net of fees+slippage, survives a ≥25 bps cost sweep. **#8 (regime robustness)** — backtest spans ≥1 full cycle incl. 2022; report Sharpe/DD per regime. **#2** — fundamentals filtered `as_of (filed_date) <= sim_date`. **vectorbt test:** pair-cointegration as a market-neutral long/short `Portfolio` on a cointegrated pair (e.g. two same-sector smoke names); confirm rolling z-score entries/exits and that cointegration re-test breaks the position when the relationship decays.

---

## M3 — factors/ (Alphalens validation + Alpha158 + QMJ + PCA)

**Modules:** `factors/`.

**Feeds:** Alphalens IC-decay/quantile harness ← QuantResearch `volume_factor_alphalens.ipynb` (**every factor passes IC validation before entering a backtest**). qlib Alpha158 port (already inventoried). Fama-French/QMJ + Fama-MacBeth 2-step ← QuantResearch `fama_french.ipynb`. PCA eigen-factors ← ML_Finance `PCA-SP500.ipynb` / QuantResearch `ch1_pca`.

**Deliverable:** `factors.validate(factor, fwd_returns) -> {ic, ic_decay, quantile_spread}` gate + an Alpha158 factor bank + QMJ exposures computed on EDGAR point-in-time fundamentals.

**Verification:** Scorecard **#5 (Deflated Sharpe)** — disclose number of factors tried N; DSR>0 required before a factor is promoted. **#9 (data-snooping)** — factor *selection itself* counts toward N; hold out a period. **vectorbt test:** rank-sort the smoke (then top-50) universe into quantile portfolios from a validated factor; confirm monotone quantile return spread out-of-sample and that IC decays gracefully (not a single-bar spike = leakage).

---

## M4 — portfolio/ (PyPortfolioOpt)

**Modules:** `portfolio/`.

**Feeds:** SciPy objectives (GMV / max-Sharpe / max-diversification / **risk-parity**) ← QuantResearch `portfolio_optimization.py:43-58` (framework-agnostic, wires into vectorbt sizing); productionized via PyPortfolioOpt (MVO/max-Sharpe), Riskfolio risk-parity deferred to Phase 2.

**Deliverable:** `portfolio.optimize(expected_returns, cov) -> weights` plugged into the backtest sizing layer, replacing fixed-fraction.

**Verification:** Scorecard **#4 (walk-forward)** — weights re-optimized in rolling out-of-sample windows via vectorbt `Splitter` (no full-sample covariance). **#3 (train/val/test)** — covariance/expected-returns estimated on train only. **vectorbt test:** walk-forward max-Sharpe vs equal-weight baseline on the validated-factor portfolio from M3; confirm OOS Sharpe uplift net of turnover cost, not in-sample.

---

## M5 — opinion/ + signals/ (alt-data: insider, PEAD, congress, Dataroma, finfluencer)

**Modules:** `opinion/`, `signals/`. All sources collapse into the unified **`opinion_event`** model (`source_type, published_at(=as_of), ticker, stance, conviction, horizon, …`).

**Feeds:** insider cluster-buy ← **edgartools** Form 4 ownership summary → `insider_txns`, rolling-30d ≥N distinct `Code='P'`, `as_of = filing_date` (not txn date). events ← edgartools 8-K `CurrentReport.items`. PEAD ← PEAD-Strategy formula + drift window only (discard its backtester, swap paid analyst denominator for **time-series SUE** = `(EPS_q − EPS_{q-4})/σ(ΔEPS ~8q)` from EDGAR XBRL `EarningsPerShareDiluted`), `as_of = 8-K Item 2.02 filing_date`. congress ← House Clerk PTR + house/senate-stock-watcher JSON, **`as_of = disclosure date` (the 45-day-lag trap)**. Dataroma 13F + YouTuber/earnings distillation (level-1 transcripts) → finfluencer-style backtest.

**Deliverable:** `opinion_event` DuckDB table + per-`source_name` scoreboard: `published_at` entry → 1/5/20/60d forward returns → hit-rate/IR/WLO/Sharpe/MDD.

**Verification:** Scorecard **#1 + #2** — *the* failure mode here; congress especially must use disclosure date, asserted by a unit test rejecting any txn-date `as_of`. **#5** — finfluencer scoreboard reports DSR per source (many sources tried = high N). **vectorbt test:** event-driven entries from insider cluster-buy and PEAD on the top-50 universe; confirm the published_at→fwd-return drift is positive net of cost and vanishes (as it should) when `as_of` is wrongly set to transaction/period_end.

---

## M6 — contract/ (export_dashboard_json)

**Modules:** `contract/` → `api.export_dashboard_json()`.

**Feeds:** Design brief §7 contract facts. Pydantic models are the contract SoT → JSON Schema; serialize the `dashboard_status.json` superset (`{meta, updated_at, global_regime, data[]}` with per-entry `coordinates/trace[30]/sector_trace[30]` + additive `scores{}`). **No Zod downstream → new fields must be backward-compatible; never bump `meta.version` casually.** Universe truth = `config/stocks.json`.

**Deliverable:** Validated `dashboard_status.json` emitting M0–M5 signals + `global_regime` from M0.

**Verification:** Scorecard **#10** — code+data+seed reproduce the exact exported JSON. Contract round-trip test: pydantic → JSON → re-parse is lossless; additive-field change does not break the existing dashboard schema. **vectorbt test:** N/A (serialization layer) — instead assert every exported signal traces back to a backtest that passed its phase's gates.

---

## First PR (smallest shippable)

**`feat(regime+rule): minervini_trend gated by 200-SMA regime on smoke universe`**

Scope, kept deliberately thin:
1. `regime/sma_gate.py` — `SMARegimeGate(window=200)` returning LONG-OK / risk-off per bar from the benchmark (add **SPY** to `configs/smoke.yaml`).
2. `strategy/rules/minervini_trend.py` — Trend Template + a self-computed **RS Rating** (trailing-return percentile, RS≥70 gate), implementing the existing `Signal`/`Direction` + `to_pivot()` interface, AND-gated by the regime gate.
3. Register `"minervini_trend"` in `api.py:_RULES`; add a smoke config block.
4. Backtest on the existing 5-ticker smoke universe via the current vectorbt engine.

**PR-level verification (subset of the full scorecard):** **#1** the +1-bar shift test (returns must not survive a leak), **#6** net of the existing 5+5 bps fees/slippage, **#10** seed-reproducible report. This ships one regime module + one rule + the RS primitive on infrastructure that already exists (`DuckStore`, `run_backtest`, `to_pivot`), validating the M0→M2 spine end-to-end before the heavier labeling/CV and EDGAR fundamentals work lands.

---

Relevant files (all absolute):
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\design-brief.md`
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\extraction-backlog.md`
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\docs\data-and-backtest-rigor.md`
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\api.py` (`_RULES` registry — where new rules register)
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\src\trading_analysis\strategy\rules\sma_crossover.py` (the `Signal`/`to_pivot` rule interface the first PR mirrors)
- `C:\Users\Romarin\Documents\Software Projects\trading-analysis\configs\smoke.yaml` (smoke universe to extend with SPY)