# 架構決策：多 repo 切分 + 成本（我的深入評估）

> 日期：2026-06-14。回應使用者：「你是否認同 investment-dashboard 獨立分開且互相依賴？」+ $15/月 約束 + repos 結構設計。
> 細部資料：[ingestion-pipeline.md](ingestion-pipeline.md)（成本/pipeline）、[architecture-integration.md](architecture-integration.md)（dashboard 契約）。

## 1. 我認同切分嗎？認同——但要把「互相依賴」改成「單向資料流 DAG」

**認同獨立切分**，理由站得住腳：
- **語言邊界**：dashboard 是 Vue/TS、引擎是 Python → 用 JSON 檔交換最乾淨，本就該分。
- **部署節奏**：dashboard 改 UI 不該觸發引擎重跑；引擎改策略不該重建前端。
- **零 backend 維持**：dashboard 已是 GitHub Pages 靜態站，分開才保得住。
- **故障隔離 + 版本化**：data 一份 repo → 每次 ETL 是一個 diff，可回滾、可稽核。

**但「互相依賴（mutually dependent）」這個詞要修正。** 真正健康的形狀是**單向 DAG，不是循環依賴**——repo 之間循環依賴是反模式（建置/版本糾纏）。正確是：

```
trading-data  ──(raw JSON)──▶  trading-analysis  ──(signals/opinions JSON, 契約)──▶  investment-dashboard
   (攝取/儲存)                      (引擎/契約擁有者)                                  (純呈現消費者)
```

- **依賴方向單一**：dashboard 依賴 trading-analysis 定義的**契約**，trading-analysis 依賴 trading-data 的原始資料。沒有反向箭頭。
- **「介面由本專案(trading-analysis)提出並提供資料內容」——完全認同**。trading-analysis 是**契約擁有者**：用 pydantic 定義輸出 schema → 產 JSON Schema → dashboard 端用它驗證。這解決了既有 `dashboard_status.json` 無驗證/欄位 drift 的問題。
- dashboard 重構＝改成「讀 trading-analysis 產出的契約 JSON」，而非自己算 Phase-3（其進場訊號已被自家驗證判死，見 [architecture-integration.md](architecture-integration.md)）。

## 2. 「GitHub 當 serverless trigger + 當 database」——這個工作負載下我認同

使用者假設正確，**前提是這個工作負載**（append 為主、小資料 <1GB、單寫者、消費為靜態 JSON）：
- ✅ **GitHub Actions 當 cron/運算**：public repo 免費分鐘**無上限**。
- ✅ **git repo 當 DB**：單寫者無衝突、免費版本化稽核軌跡、git diff 即變更歷史。
- ⚠️ **何時會壞**：高頻寫（intraday tick）、並發寫（merge 衝突）、需要 `WHERE`/`JOIN`/聚合（git 無查詢引擎，得 clone 全部在記憶體 filter）、歷史無限膨脹。**緩解**：只把「最新」JSON 當服務 artifact、原始歷史定期 squash/分片、別 commit 大 blob（YouTube 音檔不進 git，只進蒸餾後文字）。要監控的一件事：每日 commit 會長 `.git` 歷史（working tree 雖平），但你的量級數年內 <1GB。
- ➕ **加 Cloudflare R2 當服務層**：零 egress（贏 S3/GCS 的 egress 收費），dashboard 從 R2 拉 JSON 不計流量。

## 3. $15/月 約束——輕鬆達標（實際 ~$2–7/月）

| 方案 | 判決 | 原因 |
|---|---|---|
| **GitHub Actions + git-as-DB + R2** | ✅ **採用** | 唯一經常成本是 LLM 萃取 ~$2.2/月（Haiku 4.5 Batch）。總計 ~$2–7 |
| AWS S3 + **Fargate** | ❌ **出局** | Fargate 1vCPU/2GB 24/7 ≈ **$35/月**，單它就 2.4× 預算；爬蟲是週期 batch 非常駐容器 |
| AWS S3 + Lambda | ⚪ 可但較差 | Lambda free 夠，但 S3 **收 egress** → 服務 JSON 要錢，R2 完勝 |
| **BigQuery** | ❌ 過度 | 分析倉儲（十億列掃描）；50 檔 universe 的 JSON 用不到 1TB/月，徒增複雜度。**留作日後大規模歷史回測再用** |
| Turso(SQLite)/D1 | ⚪ 需要才上 | 真的要 `WHERE`/`JOIN` 才加；否則 flat-JSON 更簡單免費 |

**唯一變動成本是 LLM**：Haiku 4.5 + **Batch API（−50%）** ≈ $2.2/月（10 創作者×1 片/日）；或本地 **Ollama Qwen2.5 = $0**（精度較低）。**Batch 對不延遲敏感的萃取是免費的錢**。

## 4. Repos 結構提案（recommendation level；完整 spec 留待 ultracode 場次）

```
trading-data/            # 攝取 + 原始儲存（serverless 觸發）
├── .github/workflows/   # cron: 抓 OHLCV/基本面/新聞/逐字稿
├── crawlers/            # RSS(Tier0) / r.jina.ai+Crawl4AI(Tier1) / CF-Worker(Tier2)
├── youtube/             # RSS 偵測 + 逐字稿(api/yt-dlp/whisper)
├── data/                # 版本化原始 JSON/parquet（git-as-DB；大檔→R2）
└── (push 最新 → Cloudflare R2)

trading-analysis/        # ★ 本 repo：引擎 + 契約擁有者
├── src/trading_analysis/
│   ├── strategy/rules/  # minervini_trend / vcp / magic_formula / graham / canslim
│   ├── factors/         # Alpha158 移植 + Fama-French/QMJ
│   ├── opinion/         # YouTuber call 萃取(LLM) + finfluencer 式回測 + 創作者評分
│   ├── regime/          # 市場 regime/廣度（CANSLIM「M」）
│   ├── portfolio/       # PyPortfolioOpt → 權重
│   ├── contract/        # ★ pydantic 輸出 schema → 產 JSON Schema（契約 SoT）
│   └── api.py           # export_dashboard_json() 等公開介面
└── (讀 trading-data，產 signals/opinions/scores JSON 符合契約)

investment-dashboard/    # 純呈現消費者（既有，重構為讀契約 JSON）
└── 去掉自算 Phase-3，改讀 trading-analysis 契約（保留 comet 視覺 + ATR 出場）

# 選配第 4 個：shared-contracts（pydantic↔TS 型別）——初期可內嵌在 trading-analysis/contract/
```

**邊界原則**：trading-data 做「取得原始 bytes」（價格/基本面/新聞文字/逐字稿）；trading-analysis 做「原始→訊號/觀點/分數 + dashboard JSON」（含 LLM 蒸餾、回測、契約）。LLM 呼叫放 trading-analysis 的 Actions。這讓 trading-analysis 是**單一大腦 + 契約擁有者**。

**YouTuber pipeline 落點**：fetch/逐字稿在 trading-data（機械、便宜）；蒸餾+回測+評分在 trading-analysis（`opinion/`，這是分析）。產 `opinions.json`/`creator_scorecards.json` 入契約。

## 5. 留待下一場 ultracode 產出（重設計工作）
本檔是 recommendation 級。以下**重型產出**適合專場 ultracode：
1. **完整契約 schema spec**（trading-analysis `contract/` pydantic 模型逐欄 + 與既有 `dashboard_status.json` 的對映/擴充/遷移）。
2. **investment-dashboard 重構遷移計畫**（additive→切換讀外部 contract 的逐步步驟、不破壞既有 production）。
3. **trading-data repo 完整檔案佈局 + GitHub Actions workflow YAML + R2 推送**。
4. **三 repo 的 CI 串接與版本/契約驗證**（pydantic↔TS、契約變更 gate）。
5. **端到端框架圖**（攝取→量化→輿論→組合→契約→dashboard）落到可執行任務。
