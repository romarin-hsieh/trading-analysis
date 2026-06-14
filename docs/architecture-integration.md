# 架構整合計畫：trading-analysis × investment-dashboard（多 repo）

> 日期：2026-06-14。使用者揭露最終願景後的策略重定位。完整 dashboard 探索結論見本檔。

## Context
使用者最終目標：把現在的 trading-analysis **重構整合**進既有的 `investment-dashboard` 生態。假想多 repository 互相依賴：資料抓取 repo（GitHub Action 定期抓）→ 獨立 data repo → dashboard 呈現；而股票分析/交易策略/量化計算/情緒面市場面分析集中在 dashboard 呈現。

## 既有 investment-dashboard 現況（探索結論）
**比預期成熟得多——它已經是 production 專案，且已有一套 ETL + 量化訊號引擎。**
- **技術**：Vue 3 + Vite 靜態 SPA，部署 GitHub Pages，**零 runtime backend**。v2.5「Quant Edition」，~412 commits YTD，有完整 docs（7 ADR、PRD、DATA_DICTIONARY、QUANT_STRATEGY_DOSSIER、RUNBOOK、SLA）。
- **資料流**：所有資料是 **GitHub Actions ETL 每日（02:00 UTC / 台北 10:00）預算好的靜態 JSON**，前端只讀。3-tier cache（記憶體 → 靜態 JSON → Yahoo live fallback）。
- **既有 ETL 三階段**（`.github/workflows/daily-data-update.yml`）：
  - Phase 1：OHLCV（yfinance）+ fundamentals（yahoo-finance2）+ Fear&Greed（Puppeteer 爬 CNN）
  - Phase 2：Dataroma 13F 法人持股爬取 → `public/data/dataroma/`
  - Phase 3：**量化訊號引擎**（`scripts/production/daily_update.py`：McGinley Dynamic + StochRSI + Bollinger Squeeze → 3D **Trend × Momentum × Structure** 座標）→ `public/data/dashboard_status.json`，分類 Launchpad / Climax / Dip-Buy
- **資料契約**：`src/types/index.ts` 是 single source of truth（Zod 驗證）。schema 文件在 `docs/specs/DATA_DICTIONARY.md`。
- **資料湖**：`public/data/{ohlcv,fundamentals,dataroma,technical-indicators,daily,quotes}/*.json`；universe 在 `config/stocks.json`（~50 檔）。

## 重新定位 trading-analysis
**trading-analysis = 多 repo 架構的「策略/量化計算引擎」**，輸出符合 dashboard 資料契約的 JSON，**餵給（擴充或取代）Phase-3 訊號引擎**。這正好呼應我們既有的「核心 lib 與 UI 嚴格解耦、UI 只能呼叫 `api.py`」原則——現在 UI 換成了 dashboard，解耦更顯重要。

## 目標多 repo 架構
```
┌──────────────────────────────────────────────┐
│ 1. trading-analysis（本 repo）               │
│    純策略/量化 lib：Minervini/Magic Formula/  │
│    因子/Kronos/(V1)LLM persona。              │
│    輸出：訊號 + 因子分數 + 篩選結果 (JSON)     │
└───────────────────┬──────────────────────────┘
                    │ import / CLI 呼叫
┌───────────────────▼──────────────────────────┐
│ 2. trading-data（待建）                      │
│    把 dashboard 現有 ETL 抽出來；             │
│    GitHub Action 定期抓 OHLCV/基本面/籌碼，    │
│    呼叫 trading-analysis 算訊號 → commit JSON │
│    到獨立 data repo（GitHub Pages/CDN）       │
└───────────────────┬──────────────────────────┘
                    │ 讀靜態 JSON (CDN)
┌───────────────────▼──────────────────────────┐
│ 3. investment-dashboard（既有，純前端化）     │
│    去掉內建 ETL，讀 data repo CDN 呈現         │
└──────────────────────────────────────────────┘
```

## 整合點（具體、按既有程式對應）
1. **資料契約對齊（最關鍵）**：dashboard 的 `src/types/index.ts` + `docs/specs/DATA_DICTIONARY.md` + `public/data/dashboard_status.json` schema 是契約。trading-analysis 要能輸出**符合（或擴充）此 schema** 的 JSON。
   - 在 `api.py` 加 `export_dashboard_json()`：把我們的 Signal/factor/screener 結果序列化成 dashboard 吃的形狀。
   - 建議：用 pydantic 對映 dashboard 的 TS 型別，並產 JSON Schema 雙向驗證，避免契約 drift。
2. **概念重疊可直接利用**：dashboard 既有的 3D **Trend × Momentum × Structure** ≈ Minervini stage 分析（趨勢/動能/結構）。我們的 **Minervini Trend Template + RS rating + 因子分數**可以**餵入或取代** Phase-3 的 `daily_update.py`，且語意天然對齊。
3. **資料源統一**：dashboard 與我們都用 yfinance → 抽到 trading-data repo 統一管理；基本面改用 SEC EDGAR point-in-time（見 [data-and-backtest-rigor.md](data-and-backtest-rigor.md)）。
4. **語言邊界用 JSON 解耦**：dashboard 是 JS/TS、我們是 Python → **不直接 import，透過 JSON 檔交換**（正是「data-as-repo」多 repo 設計的好處）。

## 落地順序建議（先 additive、不破壞既有 production）
1. **先在 trading-analysis 內把策略做好**（Minervini → 基本面連接器 → Magic Formula/Graham → 因子層）。
2. **研讀 dashboard 契約**（`docs/specs/DATA_DICTIONARY.md`、`src/types/index.ts`、`dashboard_status.json` 範例），定義 trading-analysis 的輸出 schema + `export_dashboard_json()` adapter。
3. **以 additive 方式驗證**：先讓 trading-analysis 產出相容 JSON，用 dashboard 既有讀取路徑（換 data URL 或塞新檔）驗證，**不改既有 Phase-3**。
4. 確認可行後，再抽 ETL → trading-data repo，dashboard 改讀外部 data repo CDN。

## 風險/注意
- **不要急著動 dashboard production**：先 additive（新 JSON 欄位/新檔），不改既有契約。
- **資料契約 drift**：用共享 schema（pydantic ↔ TS）+ CI 驗證。
- dashboard 已有自己的 Phase-3 量化邏輯（McGinley/StochRSI/Squeeze）——取代 vs 平行新增的決策見下方「深讀結論」（已定 AUGMENT）。

---

## 深讀結論（2026-06-14 二次深挖 dashboard 內部）

### 資料契約：`dashboard_status.json`（trading-analysis 必須產出的形狀）
- 根：`{ meta{version,…}, updated_at(str), global_regime(str), data[] }`。
- 每個 `data[]`：`ticker, sector, strategy, signal, reason, commentary, price, change_percent, date, coordinates{x_trend,y_momentum,z_structure}, trace[30], sector_trace[30]`（trace 點同三鍵、oldest-first）。
- **關鍵：`dashboard_status.json` 無 Zod 驗證**，前端按 key 直接讀 → **新增欄位安全、向後相容**（`DATA_DICTIONARY.md:463` 自承）。
- ⚠️ 文件與實際 drift：`sector_trace` 未文件化但 558/558 entry 都有、實際被讀（de-facto 必填）；`signal` enum 文件與實際不符（實際 `HOLD/NO_DATA/SELL_CLIMAX/BUY_BREAKOUT/BUY_DIP/NO_TRADE`），但前端對未知 signal 字串渲染為中性 → **signal 實務上是自由字串**。
- universe 真實來源是 `config/stocks.json`（`{symbol,exchange,sector,industry,enabled,priority}`），非 `universe.json`（不存在）。
- **擴充落點**：在每個 entry 加 optional `scores:{ minervini_trend_template, magic_formula_rank, factor_value, factor_quality, rs_rating, … }`，或加 sibling 檔（`signals_minervini.json` 等）keyed by ticker。兩者都零風險。**勿** rename/移除既有欄位或亂 bump `meta.version`（= breaking）。

### Phase-3 真相（smoking gun）
- **有兩套引擎**：production 跑的是 `daily_update.py` + `strategy_selector.py`（出 coordinates + 規則訊號 BUY_BREAKOUT/BUY_DIP/SELL_CLIMAX/…）。文件吹的 **Launchpad/Climax/Dip-Buy 分類器是孤兒研究碼**（`quant_engine.py`），不在 workflow 內。
- **既有進場訊號自己驗證失敗**：`docs/archive/TAG_VALIDATION_REPORT.md` 判定「**Toxic Alpha… DO NOT DEPLOY… Scrap the Entry Signals**」（真實 0.78 vs 隨機 1.09，p=0.818；進場邏輯實際選到輸家）。`V5_FINAL_VALIDATION_REPORT.md` 的 Max DD −72%~−93% 且是合成單位權益曲線非真組合。**唯一有 edge 的是出場/風控（Chandelier/ATR）**（隨機進場上仍 5.8x）。
- **既有引擎完全缺**：RS rating、trend template、52 週結構、MA stack(50>150>200)、基本面（fetch 了但沒用）。Z 軸 Bollinger squeeze→breakout 算是 VCP-lite 的遠親。

### 決策：AUGMENT（平行新增），不是 REPLACE
證據導向結論：
1. 既有**進場訊號已被自家驗證判死** → 沒什麼好保留；但**出場/風控（ATR/Chandelier）是唯一被證明有 edge 的資產 → 應重用當我們的出場層**。
2. 既有**comet 視覺化（coordinates/trace/sector_trace）是產品招牌 UI**、與訊號品質無關 → 保留，繼續算座標。
3. 我們的 **Minervini trend template + RS rating + 因子 + 基本面**正好補滿既有引擎所缺 → 屬**互補**，當**新平行欄位/檔**最自然。
具體：保留 `daily_update.py` 產 coordinates+trace；**新增** `scripts/production/stage_signals.py`（或我們 trading-analysis 的 export）寫入 `scores{}`/sibling 檔（rs_rating、stage、trend_template_pass、magic_formula_rank、factor_score）；**出場沿用既有 ATR/Chandelier**。前端零回歸，可 A/B 兩種訊號哲學。
