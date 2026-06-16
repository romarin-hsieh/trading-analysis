# 另類資料 ingestion — 設計與接入（提高 IC 本身的唯一槓桿）

> 為什麼：[docs/09](09-methodology-and-factor-gate.md) 證明擴廣度與擇時都無效；提升成效的唯一物理路徑是**提高 IC 本身**＝另類資料。本文記錄架構、point-in-time 紀律、來源盤點，以及**已端到端接入的 SEC EDGAR 基本面**。

## 1. 架構（沿用既有 connector 模式）

```
data/connectors/{yahoo, edgar}.py   # 每個來源一個 connector
DuckStore.{upsert,load}_fundamentals # 新增 fundamentals/ parquet 分區（symbol=X/data.parquet）
edgar.point_in_time(fund, tag, dates, symbols) # as-of 對齊成 [date x symbol] 寬表
```

欄位：`symbol, cik, tag, unit, period_end, fy, fp, form, as_of, val`。

## 2. ⚠️ 另類資料的第一號洩漏陷阱：用「揭露日」不用「事件日」

基本面最致命的 look-ahead：用**會計期末（period_end）**對齊，等於讓因子**提前數週知道**財報——財報是在 period_end 之後 4-8 週才公開（10-K/10-Q `filed`）。

**本模組強制用 `as_of` = SEC `filed`（揭露日）**，從不碰 period_end。實測：AAPL FY2024（period_end 2024-09-28）的淨利是在 **filed 2024-11 才公開**。`point_in_time()` 只用 `as_of ≤ date` 的事實 ffill，且處理「同一份 10-K 把往年當比較數重列」（取每個 filing 的最新 period）。3 個單元測試鎖住這條防線（`tests/unit/test_edgar.py`）。同理：congress 用 `disclosure_date`（45 天 lag）、insider 用 Form 4 `filed`。

## 3. 來源盤點（免費、無金鑰優先；預算 $0，滿足 <$15/mo）

| 來源 | 狀態 | 訊號 | 備註 |
|---|---|---|---|
| **SEC EDGAR 基本面**（XBRL companyfacts）| ✅ **已接入** | quality/value/profitability/accruals | 官方、無金鑰、`filed` 即 point-in-time |
| SEC ticker→CIK map | ✅ 已接入 | — | `company_tickers.json` |
| SEC insider Form 4 | ⚠️ 可接（未建）| 內部人買賣 | EDGAR submissions API + XML 解析 |
| Congress 交易 | ❌ watcher S3 已 403 | 國會議員買賣 | 需 Quiver(金鑰) 或 House Clerk PTR 解析 |
| Google Trends 注意力 | ⚠️ pytrends（不穩）| 散戶注意力（Da 2011）| rate-limit |
| FINRA 短期利益 | ⚠️ 免費雙週 | 空方擁擠 | — |
| 新聞/LLM 情緒 | 💰 多需付費 API | 文本 alpha（Tetlock）| 超預算 |

## 4. 已端到端接入：SEC EDGAR 基本面

- **已 ingest**：us_study 51 檔的 **59,772 筆基本面事實**（10 個 tag：Revenues/NetIncome/GrossProfit/Assets/Equity/…），存於 `data/fundamentals/`。
- **示範因子**（證明 pipeline 通且防洩漏）：gross profitability = GrossProfit(年度)/Assets，point-in-time 對齊 → IC(fwd 63d) ≈ +0.002（25/51 檔有資料，銀行無 GrossProfit）。**因子弱（如預期：25 檔、慢年度因子），但基礎設施是交付物，且 leak-free。**
- 96 tests pass、ruff clean、預算 $0。

## 4b. S&P 500 基本面因子閘門結果（1+2 完成）— 另類資料**真的**帶來新訊號

已 ingest **全 S&P 500：731,085 筆事實 / 503 檔**。建 6 個 point-in-time 基本面因子（`factors/fundamentals.py`），過閘門（`scripts/fundamental_factors.py`，forward 63d IC）：

| 因子 | cover | IC | ICIR | IC16-19 | IC20-24 | 判定 |
|---|---|---|---|---|---|---|
| **gross_profitability**（Novy-Marx）| 248 | **+0.034** | **+0.30** | +0.048 | +0.019 | **最強、跨期同號** ✅ |
| asset_growth | 493 | −0.027 | −0.22 | −0.052 | −0.006 | weak（方向與文獻反，本十年高成長贏）|
| roa / accruals | ~480 | ~0 | ~0 | 翻號 | — | FAIL |
| earnings_yield / book_to_market（價值）| ~480 | 負 | 負 | 翻號 | — | **FAIL（價值的失落十年）** |

**關鍵對比（另類資料的價值主張被證實）**：在廣市場上 [docs/09](09-methodology-and-factor-gate.md) 證明**動量已死**（ICIR≈−0.01），但**gross profitability 活著**（ICIR **+0.30**，全 session 最強 IC）。實測 L/S sleeve：

- gross_profitability L/S：年化 +1.7%、**Sharpe +0.45**（正）
- 廣市場動量 L/S：年化 −1.3%、Sharpe **−0.14**（負，呼應 docs/09）
- **相關性 +0.08**（極低 → 真正分散）

> **結論：另類資料交付了一個真正的新訊號。** 在廣、有效率的 universe 上，**基本面品質因子（gross profitability）勝過價量動量**——這正是 alt-data 該做到的：價量做不到的、穩健、低相關的 IC 來源。它單獨 Sharpe 0.45 modest 但真實；與**集中**動量 sleeve（非廣市場動量）結合最有望提升組合 alpha。價值因子（earnings yield、B/M）在 2015-24 失效（價值失落十年）。

## 5. 下一步（讓另類資料真正提高 IC）

1. **擴到 S&P 500 基本面**（廣度×10，讓基本面因子有統計力——這正是 docs/09 缺的）。
2. **建真正的基本面因子**：Piotroski F-score、Sloan 應計項目、earnings yield（NI(TTM)/市值，需接價格）、asset growth、Novy-Marx gross profitability——每個都過 `factor_determination` 閘門。
3. **insider Form 4**（EDGAR，可免費接）：內部人淨買入是強訊號。
4. **把基本面因子併入多 sleeve 組合**（[docs/08](08-recommended-strategy.md)，唯一顯著 alpha 來源）——分散是已驗證有效的，加一個低相關的基本面 sleeve 最有望提升組合 alpha。

---
*工具：`src/trading_analysis/data/connectors/edgar.py`、`DuckStore.{upsert,load}_fundamentals`、`tests/unit/test_edgar.py`。2026-06-16。*
