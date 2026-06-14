# 資料攝取 + 輿論層 + 成本架構（Ingestion & Opinion Pipeline）

> 日期：2026-06-14。來源：背景 workflow（4 研究員 + 綜合）。成本以 Anthropic 官方價目核對。
> 硬限制：**每月基礎設施總開銷 < $15 USD**。結論：實際落在 **~$2–7/月**，餘裕約 $8–11。

## 0. 結論一句話
**GitHub Actions（免費 cron/運算）→ 量化引擎 + LLM 萃取 → git data-repo（版本化冷儲存）+ Cloudflare R2（零 egress 服務 JSON）→ Vue dashboard。** 唯一經常性成本是 LLM 萃取（Haiku 4.5 Batch ≈ $2.2/月）。**BigQuery 過度、Fargate 出局**（1 vCPU 24/7 ≈ $35/月，單它就 2.4× 預算）。

## 1. 端到端架構
```
GitHub Actions (cron, PUBLIC repo — 免費分鐘無上限)
  ├─ 偵測: YouTube RSS + 新聞 RSS (feedparser) — 無 key 無 quota
  ├─ 爬取: r.jina.ai / Crawl4AI (文章) ; Cloudflare Worker proxy (Medium GraphQL)
  ├─ 逐字稿: youtube-transcript-api → yt-dlp --write-auto-sub → (Whisper 在家機)
  ├─ 萃取: Claude Haiku 4.5 Batch + 嚴格 JSON schema + 快取 watchlist 前綴
  ├─ 量化: trading-analysis lib → 訊號/分數 ; 向量化回測
  ├─ commit: JSON → "trading-data" git repo (版本化冷儲存, <1GB)
  └─ push:   最新 JSON → Cloudflare R2 (熱服務, $0 egress)
Vue 靜態站 (GitHub Pages) ── 讀 R2 的 JSON
[家機 / Raspberry Pi] ── Whisper fallback + 選配 Ollama (免費溢位 worker)
```
**為何這樣分**：爬取/RSS/量化/回測/LLM API 呼叫都跑在 ephemeral GitHub Actions（public repo 免費分鐘無上限）。Actions **不能**做的兩件事：(1) 持久/headful 瀏覽器——其資料中心 IP 會被 Cloudflare 403 → Medium 走免費 **Cloudflare Worker** proxy 或 `r.jina.ai`（用它自己 IP 抓）；(2) 長時間 Whisper → 卸載到**家機/Pi**。資料**存兩份**：git data-repo 是版本化 system-of-record（免費稽核軌跡、單寫者無衝突），R2 是零 egress 服務層（贏 S3/GCS 的 egress 收費）。

## 2. 每月成本明細（< $15）
| 項目 | 用的層級 | $/月 |
|---|---|---:|
| GitHub Actions（cron, **public** repo）| 免費無上限 | **$0** |
| git "trading-data" repo（版本化儲存 <1GB）| 免費 | **$0** |
| Cloudflare R2（服務 JSON ~1-2GB, $0 egress）| 10GB 免費內 | **$0** |
| Cloudflare Worker（Medium proxy）+ Cron | 100k req/日免費內 | **$0** |
| 爬蟲（RSS、r.jina.ai 無 key、Crawl4AI 自架）| 免費層 | **$0** |
| YouTube 偵測（RSS）+ 逐字稿（api/yt-dlp）| 免費無 quota | **$0** |
| Whisper fallback + 選配 Ollama（家機/Pi）| 自架 | **$0**（≈電費）|
| **LLM 萃取 — Haiku 4.5 + Batch API** | ~2.85M in / 0.3M out | **~$2.2** |
| Buffer（Whisper 多跑、cache miss、模型漲價）| — | **~$2** |
| **合計** | | **≈ $2–7** |

悲觀路徑（private data-repo + 全 Sonnet 萃取 + $5 Cloudflare Workers Paid）約 **$10–12**，仍在 cap 內。

## 3. YouTuber 創作者 call pipeline（輿論層）
```
[cron 1-2×/日, 家機/residential IP]
 → poll N 個 YouTube RSS (feeds/videos.xml?channel_id=UC…), diff yt:videoId vs seen-set
 → 新片: youtube-transcript-api(zh-TW/zh-Hant/en) ─fail→ yt-dlp auto-sub ─fail→ faster-whisper large-v3(家GPU)
 → Claude Haiku 4.5 + 嚴格 JSON schema + 快取 watchlist → 結構化 calls
 → append calls.parquet(creator,ticker,stance,conviction,entry/target/stop,date,video_url,ts)
 → 向量化回測(pandas): per-creator WLO/LO/LS, Win%, Sharpe, Beta, MDD, Vol; ticker heating/YOLO 排名
 → 產 opinions.json + creator_scorecards.json → Vue dashboard
```
- **新片偵測**：**YouTube 頻道 RSS** `youtube.com/feeds/videos.xml?channel_id=UC…`（已實測：Atom XML，含 `yt:videoId`、最近 15 部，**無 key 無 quota**）。channel_id 是 `UC…` 24 字元（非 @handle），可用 `yt-dlp --print channel_id` 取得。Data API 只在首次回補歷史時用。
- **逐字稿**：caption-first（`youtube-transcript-api`，免費；⚠️ YouTube 擋雲端 IP → 從**家機 residential IP** 跑可免代理成本）→ `yt-dlp --write-auto-sub` → **faster-whisper large-v3**（家 GPU，$0；繁中財經詞 ASR 較雜，預估 20-40% 影片需 Whisper，是最大品質風險）。
- **萃取 schema**（每 call）：`ticker, company, stance(buy/sell/hold/trim/add), entry/exit/target/stop_price, conviction, timeframe, rationale≤200c, quote(逐字), timestamp_sec` + `video_summary`。用 **structured outputs（strict JSON）** 免 regex。**watchlist + schema 當快取前綴**（~0.1× read，解決中文公司名→ticker，如 台積電→2330.TW）。
- **成本**：10 creators×1 片/日 ≈ 300 片/月 ≈ 2.85M in + 0.3M out。**Haiku 4.5 + Batch ≈ $2.2/月**（Sonnet ≈ $6.5；Ollama Qwen2.5 = $0 但精度低）。不延遲敏感 → **Batch API（−50%）是免費的錢**。
- **finfluencer 式回測**：每個 dated call → 隔日開盤建倉，反向 call 或固定 horizon(20/60/120 日，**設定旋鈕、報多個**)平倉。per-call 報酬 → **Win Rate**；日報酬序列 → **三條權益曲線**（LO / 信心加權 WLO / LS）+ Sharpe/Vol/MDD/Beta（一趟 NumPy，秒級）。ticker groupby → **Most-Heating**（提及數）/ **YOLO**（高提及低勝率逆向）。
- **餵 dashboard**：第三訊號層（與基本面 EDGAR/FinMind、技術面並列）。per ticker 呈現：共識情緒（淨多空、近 N 日）、**創作者可信度加權**（用其歷史 Win Rate/Sharpe 加權其 call）、近期意見 feed（深連結 `&t=<sec>` 跳到原話）。**創作者情緒與量化訊號背離本身就是訊號**。

## 4. 爬蟲堆疊（文章/新聞/Medium）— 預設 $0 分層
- **Tier 0 — RSS first**（免費、最合法）：Reuters/Bloomberg/Yahoo/Seeking Alpha/每個 Medium 作者(`medium.com/feed/@user`)。Actions 內 `feedparser`。**存衍生訊號非全文**（著作權）。
- **Tier 1 — 主抓取：`r.jina.ai` + Crawl4AI**：URL 前綴 `https://r.jina.ai/` 得乾淨 Markdown（從 Jina IP 抓，繞過 Actions IP 封鎖）；自架 Crawl4AI。皆免費、Actions 原生。
- **Tier 2 — Medium/Cloudflare**：`medium.com/_/graphql` 經**免費 Cloudflare Worker** proxy（請求源自 Cloudflare 網內 → 過 403）。即使用者提供的 zhgchg.li 技法。
- **Tier 3 — 硬 JS/auth fallback**：Apify $5 免費 credits → 本地 **Camoufox**（最佳免費 stealth）或已裝的 **agent-browser** skill。Browserbase 免費 1 小時/月當緊急。
- **避開（超預算）**：Firecrawl($16)、ScrapingBee($49)、Bright Data($499)。

## 5. 排程
- **編排器 = GitHub Actions cron** + `workflow_dispatch` 手動 fallback。排程觸發是 best-effort 偶爾延遲/掉（避開 `:00`，挑 `:23`/`:47`）；1-2×/日無妨。週期性 commit 防 ~60 天無 push 自動停用。
- **重/持久工作**（Whisper、Ollama）→ 家機/Pi 免費溢位 worker。Cloudflare Workers Cron（10ms CPU）只能當 pinger。
- **NotebookLM + Obsidian = 手動輔助、明確在自動化路徑之外**：NotebookLM 無穩定消費級 API；Obsidian 外掛只在 app 開著時跑。當研究輔助/知識庫，**不要當 cron 引擎**。

## 6. 待決策（OPEN）
1. **萃取模型**：Haiku-only(~$2.2) vs Haiku→Sonnet 升級(~$3-4) vs 本地 Ollama($0 低精度)？建議起手 Haiku+Batch。
2. **Whisper 主機**：家 PC（有 GPU？→large-v3 快）vs Pi（whisper.cpp 慢但夠 1-2 片/日）？確認哪台常開。
3. **回測持有規則**：dashboard 的標準 horizon（20/60/120 日 / 持到反向）？會大幅改變所有指標 → 選預設、報多個。
4. **data-repo 公開性**：public（Actions 免費無上限，但邏輯/衍生資料可見）vs private（2000 分鐘/月）。public 是便宜路徑。
5. **創作者清單**：先種哪 ~10 位財經 YouTuber + 其 `UC…` channel id + watchlist universe。
6. **著作權姿態**：確認「存衍生訊號非全文逐字稿」可接受。
7. **SQL 層**：現在加 D1/Turso，還是維持 flat-JSON 直到 screener 真的需要 `WHERE`/`JOIN`？建議 defer。
