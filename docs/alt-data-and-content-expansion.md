# 缺口補強：另類資料訊號 + 事件/輿論內容擴充

> 日期：2026-06-14。回答「針對缺口還有什麼建議、能否納入其他類型內容」。
> 核心紀律：**所有來源存「公布/申報/揭露日」當 `as_of`，回測 `filter as_of<=sim_date`**——insider/congress/short 最常見的陷阱是用「事件日」而非「揭露日」→ 注入 look-ahead、虛灌 Sharpe。

## A. 另類資料訊號（signal layers，接進 trading-analysis）

| 訊號 | 邊際 edge | 免費來源（<$15/月）| 可回測 | 優先 |
|---|---|---|---|---|
| **內部人交易 SEC Form 4** | **cluster/opportunistic buys ~10-21%/年**（Cohen-Malloy-Pomorski 2012）；最強最常複現 | **EDGAR 免費**（已在我們 stack）；openinsider 聚合 | ✅ 乾淨（filed_date PIT）| **HIGH #1** |
| **國會/政治交易** | 資訊優勢代理；45 天延遲、2022 後擁擠 → 當主題/注意力 tilt | **免費 scrape 原始揭露**（senate/house-stock-watcher JSON repo，非 QuiverQuant 付費 API）| ✅（disclosure_date PIT）| **HIGH** |
| **PEAD + 分析師預估修正** | PEAD（盈餘漂移）+ revisions momentum，最持久 anomaly 之一 | **PEAD 可從 EDGAR earnings + yfinance 算（$0）**；revisions 用 Finnhub 免費(60/min) | PEAD ✅；revisions **只能往前 snapshot**（vendor「歷史預估」非 PIT、勿當回測真相）| **HIGH** |
| **選擇權 GEX / 流向** | dealer gamma 定位（regime-conditional）；「異常流」多是行銷 | **免費 CBOE EOD chain → 自算 GEX**；付費(Unusual Whales~$48)跳過 | 指數級 GEX ✅；個股/intraday flow ❌（需貴 tick）| MED（Phase 2 指數 regime overlay）|
| **放空比例 / 借券 / FTD** | 高 SI%+days-to-cover+FTD → 軋空燃料；SI 異常本身是因子 | **全免費**：FINRA 雙週 SI、SEC FTD、FINRA 每日空量 | ✅（用 publication date）；雙週較 stale | MED（確認用）。台股 bonus：FinMind 已給融券/借券 |
| **Google Trends / Wikipedia 瀏覽** | 散戶注意力代理；弱、雜訊、確認用 | **免費**：pytrends（相對值、脆）、**Wikimedia pageviews（絕對值、官方、較適回測）** | Wikipedia ✅；Google Trends ❌（視窗重正規化）| LOW（晚點加）|

## B. 事件/輿論文字內容（多數可重用既有 YouTuber 蒸餾管線）

| 內容 | 為何高槓桿 | 免費來源 | 優先 |
|---|---|---|---|
| **公司法說會逐字稿** | 管理層 guidance/語氣強訊號；**與 YouTuber 蒸餾管線相同、但免 Whisper**（已是文字）| API Ninjas 免費層 / earningscall-python 免費層先試；FMP/EarningsAPI 全文要付費（緊）| **P0**（最高槓桿）|
| **SEC 8-K 事件 + 10-K/10-Q MD&A** | 8-K **item code** ≈ 免費事件分類（2.02 財報/1.01 M&A/5.02 高管/8.01 買回）；MD&A 文字接 FinBERT | **EDGAR 免費**（edgartools）| **P0**（事件骨幹）|
| **分析師評等 / 目標價變動** | 已是結構化「call」、無需 LLM；revisions/PEAD edge | **Finnhub 免費 60/min** | **P0** |
| **Substack / 電子報** | 公開 RSS `/feed`，= 既有文章蒸餾路徑 | 免費 | **P0** |
| **Podcast** | RSS enclosure → faster-whisper（本地$0）= YouTube 路徑換前端 | 免費 | **P1** |
| **台股 PTT 股票板 / cnyes 鉅亨** | 中文情緒/輿論；PTT 可爬（jwlin/ptt-web-crawler）| 免費 | **P2**（需中文情緒）|
| **X/Twitter finfluencer** | ⚠️ **超預算**：新 API pay-per-use $0.005/read 上限~$10k；Nitter 已死 | — | **P3 defer**（要做只手選 3-5 人）|
| **Seeking Alpha** | Cloudflare 硬擋、需 stealth+residential proxy | — | **P3**（skip）|

## C. 統一「創作者/事件觀點」資料模型（一張表吃所有模態）
區分 **opinion**（某人的立場）與 **event**（發生某事）；兩者都變成 dated call：
```
opinion_event {
  id, source_type      # earnings_call | sec_filing | youtube | substack | podcast | x | analyst_rating | ptt | news
  source_name, url, published_at,        # published_at = dated "call" 時戳 (UTC, =as_of)
  ticker, market(US|TW), doc_type,
  stance(-1..+1), conviction(0..1), horizon(intraday|swing|long),
  entry_hint, exit_hint, price_target,   # nullable
  event_class,         # nullable: guidance_change|M&A|buyback|exec_change|upgrade|downgrade
  sentiment_finbert, raw_text_ref, extracted_by(haiku|finbert|api_native)
}
```
回測層**模態無關**：每列 = 在 `published_at` 進場、量 1/5/20/60d 前向報酬，per `source_name` 聚合 → finfluencer 式記分板（hit-rate/avg fwd return/IR），同一套同時排名 YouTuber、分析師、電子報、法說 guidance。

## D. 建議優先順序（綜合兩研究員）
1. **P0 內部人 Form 4**（最強 edge、資料已在 EDGAR、$0）→ `insider_txns` 表 + cluster_buy 特徵
2. **P0 EDGAR 8-K + MD&A**（免費精準事件骨幹，edgartools）
3. **P0 法說逐字稿**（最大管線重用；先用免費層限 watchlist）
4. **P0 Finnhub 分析師評等**（免費、已結構化、無需 LLM）+ **PEAD**（從既有資料算）
5. **P0 Substack RSS** → **P1 Podcast**（faster-whisper 本地）
6. **HIGH 國會交易**（免費 JSON、與 YouTuber 輿論層 UI 綜效）
7. **P2 台股 PTT/cnyes**；**Defer** X/Twitter、Seeking Alpha、GEX(Phase2)、Google Trends

## E. 待 clone/採用的新 repo
- **dgunning/edgartools**(2.3k,MIT) — 8-K/Form4/10-K 解析，best-in-class
- **EarningsCall/earningscall-python**(31,MIT) — 法說逐字稿 client
- **timothycarambat/senate-stock-watcher-data**(+house) — 免費國會 JSON
- **aladinbouddat/PEAD-Strategy** — PEAD long-short 回測參考
- **Matteo-Ferrara/gex-tracker**(196) — GEX（Phase2）
- **GeneralMills/pytrends**(3k,Apache) / Wikimedia pageviews REST
- **SYSTRAN/faster-whisper**(23.6k,MIT) — podcast/無字幕影片轉錄（已在 ingestion 規劃）

## F. 不採用/注意
- QuiverQuant API 付費（$30+）→ 走免費原始揭露 scrape。
- Finnhub/FMP/yfinance 分析師資料 = 現值快照非 PIT → 安全用於 live、**不可當回測真相**（往前自存 snapshot）。
- 多個 scraper repo 無授權（openinsiderData、部分 GEX）→ 重寫或確認後用。
- SEC FTD / 部分站擋資料中心 IP → 從家機 residential 抓（與既有 ingestion 設計一致）。

## G. 國會交易 + Dataroma 來源細節（2026-06-14 使用者補充）

**國會/政治交易（HIGH，免費）— 第三方追蹤站（快、好用）**
- **Capitol Trades**（capitoltrades.com，**首選**）：UI 乾淨，直接給 Issuer / Buy-Sell / 金額範圍（如 $15K–$50K）；延遲數小時~1 天。
- **Quiver Quantitative**（quiverquant.com/congress-trading）：WSB 散戶愛用，**分析議員績效有無打敗大盤**。API 付費 → 免費走 web/原始揭露。
- **InsiderFinance**：資料庫全，可直接搜議員名。
- **官方第一手（驗證用）**：**Office of the Clerk, U.S. House** `disclosures-clerk.house.gov` → "Search Financial Disclosure Reports" → 找 **PTR (Periodic Transaction Report)**（議員須在交易後 **45 天內**申報）。免費可 scrape。參議院對應 senate/house-stock-watcher JSON repo。
- X/Twitter：盯國會錢包的帳號最快爆料 → 當**快訊來源、非回測真相**。
- **⚠️ 45 天延遲陷阱（鐵律）**：務必區分 **Transaction Date** vs **申報日**。2 月的新聞可能是 1 月初甚至去年 12 月底買的（可能已買在低點、現價已漲）。**回測一律用 disclosure/申報日當 `as_of`，絕不用 transaction date** — 否則嚴重 look-ahead。
- 落點：`congress_txns(politician, chamber, ticker, txn_type, amount_range, txn_date, disclosure_date AS as_of, source)`。主源 House Clerk PTR + senate/house-stock-watcher JSON；Capitol Trades 當對照。

**Dataroma（新增爬取目標）** `dataroma.com/m/home.php`
- 追蹤知名價值投資人（superinvestors）13F 持股與動向。**investment-dashboard 既有 ETL 已在爬 Dataroma per-symbol** → 統一搬到 trading-data repo。
- 落點：併入 `opinion_event`（`source_type=superinvestor_13f`）或專表 `superinvestor_holdings`。⚠️ 13F 季度、落後 ~45 天 → 持股追蹤非即時訊號。
