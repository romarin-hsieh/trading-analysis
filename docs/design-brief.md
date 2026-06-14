# 設計 BRIEF（交給 ultracode 生成計畫）

> 日期：2026-06-14。本檔是**計畫生成的單一輸入**：把六輪研究的決策濃縮，供 ultracode 多 agent 產出完整實作計畫。
> 背景全貌見 [00-executive-summary.md](00-executive-summary.md)；模組萃取見 [extraction-backlog.md](extraction-backlog.md)；整合見 [architecture-integration.md](architecture-integration.md)、[architecture-decision-multirepo.md](architecture-decision-multirepo.md)；攝取見 [ingestion-pipeline.md](ingestion-pipeline.md)、[alt-data-and-content-expansion.md](alt-data-and-content-expansion.md)。

## 1. 目標與終態
打造一套**多 repo、互為單向資料流**的美股（次台股）量化+輿論分析系統，最終所有訊號集中在既有的 **investment-dashboard**（Vue3 靜態站）呈現。trading-analysis 是**引擎 + 契約擁有者**。

## 2. 硬約束（不可違反）
- **成本 < $15 USD/月**（實際目標 ~$2–7）。
- **Point-in-time 鐵律**：所有資料存「揭露/申報日」當 `as_of`，回測 `filter as_of<=sim_date`。國會交易尤其：用 disclosure date 非 transaction date（45 天延遲陷阱）。
- **授權紀律**：寬鬆(MIT/Apache/BSD)可帶 attribution 採用；AGPL 只參考不複製進公開 repo；jo-cho 等無 LICENSE → 從上游(de Prado/mlfinlab/ta)重寫；vectorbt Commons Clause（不販售即無感）。
- **不破壞 investment-dashboard production**：先 additive，再切換。
- 技術棧：Python 3.12 + DuckDB + vectorbt + Streamlit；repos 為 **Public**（免費無上限 Actions）。

## 3. 架構決策（已定）
單向 DAG（非循環互依）：
```
trading-data (攝取/原始儲存) ──raw JSON──▶ trading-analysis (引擎+契約擁有者) ──contract JSON──▶ investment-dashboard (純呈現)
```
- **trading-data**：GitHub Actions cron 當 serverless trigger + 爬蟲 + 原始儲存（git-as-DB <1GB + Cloudflare R2 零 egress 服務）。
- **trading-analysis**（本 repo）：策略/因子/labeling/regime/portfolio/opinion 引擎；用 pydantic 定義輸出 schema（契約 SoT）→ `api.export_dashboard_json()`。
- **investment-dashboard**（既有 Public Vue3）：去掉自算 Phase-3，改讀契約 JSON。**保留** comet 視覺(coordinates/trace) + **唯一有 edge 的 ATR/Chandelier 出場**；**取代**已被自家驗證判死的進場訊號（TAG_VALIDATION_REPORT「Toxic Alpha, DO NOT DEPLOY」）。
- 選配第 4 repo：shared-contracts（pydantic↔TS），初期內嵌 trading-analysis/contract/。

## 4. 資料源（含本輪新增）
- **價格**：yfinance（美股）；**台股**：FinMind（價格+基本面+**籌碼/三大法人**）。
- **基本面**：**SEC EDGAR companyfacts（point-in-time，filed 日）**主源；FMP/yfinance 便利 fallback（非回測真相）。
- **情緒/新聞**：Alpha Vantage NEWS_SENTIMENT + Finnhub + GDELT；本地 **FinBERT**；市場情緒 CNN F&G + VIX + put/call。
- **YouTuber 輿論**：頻道 RSS 偵測 → youtube-transcript-api/yt-dlp/faster-whisper（家機）→ Haiku 萃取 → finfluencer 式回測。
- **國會交易（新增）**：House Clerk `disclosures-clerk.house.gov` PTR + senate/house-stock-watcher JSON 主源；Capitol Trades / Quiver / InsiderFinance 對照；**用 disclosure date 當 as_of**。
- **Dataroma（新增爬取）** `dataroma.com/m/home.php`：superinvestor 13F；dashboard 既有爬法統一到 trading-data。
- **內部人**：EDGAR Form 4（edgartools）。**事件**：EDGAR 8-K item codes。**PEAD**：EDGAR XBRL EPS + yfinance（時序 SUE，無付費）。**法說**：earningscall（level-1 全文免費）。
- 後續：options GEX、short interest/FTD（Phase 2）。

## 5. trading-analysis 引擎模組 backlog（來源見 extraction-backlog.md）
- `regime/`：200-SMA gate（主）+ HMM/MarkovRegression overlay + GARCH（CANSLIM「M」）
- `labeling/`（新）：triple-barrier + trend-scanning + **purged/embargoed CV**（ML 地基）
- `features/`：`ta`/pandas-ta 補指標 + ADF 篩選 + 均值回歸包(Hurst/half-life) + 微結構(Amihud/VPIN) + MDI/MDA
- `factors/`：qlib Alpha158 移植 + Fama-French/QMJ + Alphalens 驗證 harness + PCA
- `strategy/rules/`：minervini_trend、vcp、magic_formula、graham、canslim、配對共整合、Parabolic SAR、RSI、sma_crossover(已有)、kronos_trend(已有)
- `portfolio/`：equal-weight → PyPortfolioOpt(MVO/max-Sharpe) → Riskfolio(risk-parity, Phase2)
- `opinion/`：YouTuber/法說/分析師/國會/Dataroma 蒸餾 + finfluencer 式回測（統一 `opinion_event` 模型）
- `signals (alt-data)`：insider cluster-buy(Form4)、PEAD、events(8-K)、congress、short/GEX(Phase2)
- 既有：data(DuckDB+yfinance)、models(kronos+ta+naive)、backtest(vectorbt+metrics)、execution(paper)、ui(streamlit)、api、observability

## 6. 統一 `opinion_event` 模型（所有「聲音」同一張表、模態無關回測）
欄位：`source_type(earnings_call|sec_filing|youtube|substack|podcast|analyst_rating|congress|superinvestor_13f|news), source_name, url, published_at(=as_of), ticker, market, doc_type, stance(-1..1), conviction(0..1), horizon, entry/exit/target/stop, event_class, sentiment_finbert, raw_text_ref, extracted_by`。回測：published_at 進場 → 1/5/20/60d 前向報酬 → per source_name 記分板（hit-rate/IR/WLO/LO/LS/Sharpe/MDD）。

## 7. dashboard 契約事實（trading-analysis 要產出）
`dashboard_status.json` = `{meta, updated_at, global_regime, data[]}`；每 entry：`ticker/sector/strategy/signal/reason/commentary/price/change_percent/date/coordinates{x_trend,y_momentum,z_structure}/trace[30]/sector_trace[30]`。**無 Zod → 新增欄位向後相容**（加 `scores{}` 或 sibling JSON）。universe 真實來源 `config/stocks.json`。勿亂 bump `meta.version`。

## 8. 攝取/成本/排程（已定）
GitHub Actions(public 免費) cron → 爬蟲(RSS Tier0 / r.jina+Crawl4AI Tier1 / CF-Worker Medium Tier2 / Playwright+Camoufox Tier3 / **trafilatura 正文抽取**) + EDGAR/FinMind/congress/Dataroma + 逐字稿 → Haiku **Batch** 蒸餾(~$2.2/月) → 量化引擎 → commit git data-repo + push R2 → dashboard 讀。家機/Pi 跑 Whisper/Ollama。

## 9. 待決策（plan 要列出選項 + 建議）
- 創作者清單（~10 位 + UC channel id + watchlist universe）
- Whisper 主機（家 PC GPU vs Pi）
- 回測持有 horizon 預設（20/60/120 / 持到反向）
- data-repo 公開性（public 便宜 vs private）
- 萃取模型（Haiku-only vs Haiku→Sonnet vs Ollama）
- dashboard：取代 vs 平行新增 Phase-3（已傾向 AUGMENT；長期是否淘汰舊進場）

## 10. ultracode 計畫要產出什麼（plan deliverables）
1. **三/四 repo 結構 spec**：trading-data / trading-analysis / investment-dashboard (/shared-contracts) 的目錄佈局、職責、依賴 DAG、邊界。
2. **資料契約 spec**：pydantic 模型（signals + scores + `opinion_event` + dashboard_status 超集）→ JSON Schema；與既有 dashboard_status.json 的對映/擴充。
3. **investment-dashboard 重構遷移計畫**：additive→切換讀外部 contract 的逐步步驟，不破壞 production。
4. **trading-data 攝取 repo 設計**：目錄 + GitHub Actions workflow YAML（cron、各來源含 congress/Dataroma/EDGAR/YouTube、R2 push、git-as-DB layout、point-in-time as_of）。
5. **trading-analysis build roadmap**：模組分階段（先 labeling/+regime/ 地基 → features/factors → rules → opinion/alt-data → portfolio），每階段驗證(過 [data-and-backtest-rigor.md] scorecard)，含 export_dashboard_json 契約對接。
6. **三 repo CI 串接 + 契約驗證 gate**（pydantic↔TS、契約變更阻擋）。
7. **端到端框架圖 + 里程碑 M0..Mn + 第一個 PR 定義**。
8. 每月成本表（< $15）複核 + 待決策建議。
