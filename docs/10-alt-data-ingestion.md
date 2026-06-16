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
| **SEC insider Form 4** | ✅ **已接入** | 內部人買賣（Lakonishok-Lee）| bulk 季度資料集（非逐檔），open-market P/S |
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

## 4c. 把品質 sleeve 併入組合 — 真實但**邊際**（誠實收尾）

把 gross-profitability sleeve 併入已驗證的多 sleeve 組合（[docs/08](08-recommended-strategy.md)，唯一顯著 alpha t=2.64），`scripts/add_quality_sleeve.py`：

| 組合 | Sharpe | MDD | Calmar | alpha (t) |
|---|---|---|---|---|
| 5-sleeve（docs/08）| 1.22 | −19.3% | **0.61** | +6.34% (**t=2.64**) |
| 6-sleeve 風險平價(+品質) | 1.21 | −15.1% | 0.52 | +3.69% (t=2.37) |
| **5-sleeve + 15% 品質 tilt** | **1.23** | −17.2% | 0.59 | +5.31% (t=2.60) |

- corr(品質, 5-sleeve combo) = **+0.16**（低、可加性）。
- **風險平價(+品質)** 反而變差：inverse-vol 權重**過度配置低波動的品質 L/S** → 稀釋報酬與 alpha（Calmar 0.61→0.52、alpha t 2.64→2.37）。
- **適度 15% tilt**：Sharpe 微升（1.22→**1.23**，全 session 最佳）、MDD 降，但 CAGR/Calmar/alpha 微降——**基本上打平**（用一點報酬換一點低回撤）。

> **誠實收尾**：另類資料交付了一個**真實、低相關的新因子**（gross profitability），但把它併入已經很好的組合，貢獻是**邊際的**（最佳情況 Sharpe 1.22→1.23 + 低一點回撤，alpha 沒有 step-change）。原因：5-sleeve 組合已捕捉大部分可得的分散，且品質單獨報酬 modest。**沒有銀色子彈**——這呼應整個 session：誠實、漸進、無捷徑。最佳可交付仍是多 sleeve 組合（可選擇加 15% 品質 tilt 換取最佳 Sharpe + 較低回撤）。

## 4d. 第二個另類資料源：insider Form 4 — 真實資料，但因子**弱且不穩**

接入 SEC bulk 季度 Form 4 資料集（`data/connectors/insider.py`，open-market 買(P)/賣(S)），ingest 2015-2024 **65,503 筆 (symbol, 申報日) / 494 檔**。資料真實（OXY 2024Q1 買入 $246M = Berkshire，已驗證）。建 net-purchase-ratio 因子（trailing 6/12mo，point-in-time、申報日 snap 次交易日）過閘門：

| 因子 | IC | ICIR | hit% | IC16-19 | IC20-24 | 判定 |
|---|---|---|---|---|---|---|
| insider_npr_6mo（value）| +0.011 | +0.14 | 57% | **−0.004** | **+0.027** | **FAIL（翻號）** |
| insider_npr count-based | +0.010 | +0.13 | 57% | −0.006 | +0.029 | FAIL（同樣翻號）|

- 整體**弱正向**（IC +0.01、hit 57%，方向符合 Lakonishok-Lee），但**跨期不穩**：2016-19 ~0/負，2020-24 才轉正 → **過不了穩定性閘門**。
- value-weighted 與 count-based **結果幾乎相同** → 不是 outlier 問題，是訊號本身弱/regime-依賴。
- **沒贏過 gross profitability**（ICIR +0.30 穩定）。內部人 alpha 自 2001 廣為人知後已衰退——又是 alpha decay。

**廣 universe 因子總排名（本 session）**：gross_profitability(ICIR +0.30 穩) > asset_growth(−0.22 弱) > insider(+0.13 不穩) > momentum(~0 死) > value(FAIL)。**唯一穩健的新 alpha 是基本面品質因子**；insider 弱、價值死、動量在廣市場死。

## 4e. 深掘品質因子 — quality 是 regime-**universal**，與動量互補（最有價值的發現）

`scripts/quality_research.py`：(1) quality 複合因子 vs gross profitability 單獨；(2) quality 的 regime 適用地圖。

**(1) 複合 vs 單一**：

| 因子 | cover | IC | ICIR |
|---|---|---|---|
| gross_profitability | 248（銀行無 GP）| **+0.034** | **+0.30** |
| quality_composite（GP+ROA+accruals z 平均）| **485**（近全 universe）| +0.024 | +0.20 |

複合因子 IC 較低但**覆蓋率近全市場**（銀行有 ROA/accruals）——用一點訊號強度換廣度。gross profitability 仍是最強單一訊號。

**(2) Quality 的 regime 適用地圖（vs 動量 docs/09）**：

| regime | quality IC | 動量 IC |
|---|---|---|
| **bear** | **+0.038** | −0.032（反轉！）|
| **drawdown** | **+0.050** | 死 |
| **high-vol** | **+0.048** | 死 |
| bull | +0.024 | +0.039 |
| low-vol / normal | +0.018 / +0.020 | 正 |

> **最有價值的發現：quality 在「每一個」regime 都是正的，且在 bear/壓力/高波動時「最強」——與動量完全相反（動量只在 bull 有效、bear 反轉）。** 這是教科書的「flight to quality」：壓力時投資人獎勵獲利能力強的公司。所以 **quality 與 momentum 跨 regime 互補**——quality 是更可靠的因子（從不翻號），且正好在動量失效時最強。誠實註記：逐 regime 經 FDR 校正後無單一 cell 達顯著（每 regime 樣本小），但**方向在所有 regime 一致為正**（動量則翻號），全樣本 ICIR +0.30 才是穩健證據。
>
> **總結整個另類資料弧線**：唯一穩健的新 alpha 是**基本面品質因子**，而且它的真正價值不只是 IC，而是 **regime-universal + 與動量互補**——這正是 docs/09「動量是 universe/regime 特定」缺口的補位。最佳組合方向：**集中動量（bull）+ 品質（bear/壓力）的 regime-互補配置**。

## 5. 下一步（讓另類資料真正提高 IC）

1. **擴到 S&P 500 基本面**（廣度×10，讓基本面因子有統計力——這正是 docs/09 缺的）。
2. **建真正的基本面因子**：Piotroski F-score、Sloan 應計項目、earnings yield（NI(TTM)/市值，需接價格）、asset growth、Novy-Marx gross profitability——每個都過 `factor_determination` 閘門。
3. **insider Form 4**（EDGAR，可免費接）：內部人淨買入是強訊號。
4. **把基本面因子併入多 sleeve 組合**（[docs/08](08-recommended-strategy.md)，唯一顯著 alpha 來源）——分散是已驗證有效的，加一個低相關的基本面 sleeve 最有望提升組合 alpha。

---
*工具：`src/trading_analysis/data/connectors/edgar.py`、`DuckStore.{upsert,load}_fundamentals`、`tests/unit/test_edgar.py`。2026-06-16。*
