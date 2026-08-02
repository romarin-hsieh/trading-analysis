# 換資料維度 — 突破 Grinold 上限的具體項目與可能性

> **2026-07 更新**:本檔四根槓桿的**資料採購盡職調查已完成**——45 個缺口 × 70 個來源的免費/<$5 判定與行動計畫見 [docs/24](24-data-gaps-and-sources.md)(GW 總經集、KF 49 產業、ThetaData 免費 OI 等三大 $0 解鎖)。

> 承 [docs/00 §E7](00-executive-summary.md)：研究證明**演算法到頂**（自主因子搜尋 0/56 達 Sharpe 2、擴廣度 51→503 無幫助、唯一穩健因子=基本面品質、唯一顯著 alpha=多 sleeve 且邊際）。**唯一的突破口是換資料維度。** 本文是按「瓶頸 × 成本 × 影響」排序的具體清單。

## 框架：每個維度動的是 IR 公式的哪一項

**主動管理基本定律**：`IR = IC × √Breadth`（Grinold 1989）。可達 Sharpe ≈ IR，被廣度與 IC 鎖死在 ~1。突破只有四條路：
- **① 修偏誤**（survivorship → point-in-time）：不直接進 IR，但**現有所有結果都偏樂觀**，修了才知道真實值。
- **② 延長歷史**：增加獨立 regime 樣本（目前僅 ~3-4 個真熊），讓 regime-conditional 推論**有統計力**、降低過擬合。
- **③ 擴廣度**（更多標的/更高頻）：放大 √Breadth。
- **④ 提高 IC**（另類資料）：放大 IC——理論上**乘數效應最大**，但最難、最貴。

session 的瓶頸排名：**survivorship > 廣度/單一市場/日頻 > 短歷史 > 樣本內調參**。

---

## ① 修偏誤（最大槓桿，因為它讓「真實值」浮現）

| 項目 | 修什麼 | 免費? | 複雜度 | 來源/路徑 | 誠實 caveat |
|---|---|---|---|---|---|
| **Point-in-time 指數成分股** | 倖存者偏誤(#1) | ⚠️半 | 高 | Wikipedia 版本歷史(免費但髒)、iShares/SPDR 歷史持股、github `fja05680/sp500`(免費歷史成分)、Compustat/CRSP(付費學術) | 沒這個，現有 +30% CAGR 都灌水(docs/07 CVNA) |
| **下市報酬(delisting returns)** | 倖存者偏誤 | ❌付費 | 高 | CRSP(WRDS 學術)、部分 yfinance 殘留 | 下市虧損名單缺失=系統性高估 |
| **財報重編(restatement) point-in-time** | look-ahead | ✅有 | 中 | EDGAR 已用 filed-date(docs/10)——已處理 | 已做對，延伸到其他資料即可 |

> **結論**：先接 **github 免費的 PIT S&P500 成分股歷史**(fja05680/sp500 等)，重跑所有回測——這是最便宜、最高槓桿的一步，會把樂觀偏誤擠出來。下市報酬要 CRSP(付費)，可暫緩。

## ② 延長歷史（讓 regime-conditional 推論有統計力）

| 項目 | 影響 | 免費? | 來源 | caveat |
|---|---|---|---|---|
| **延長到 1990s–2024** | ~3-4 → ~8 個真熊(2000/2008/2020/2022 + 1990/1998/2001/2008) | ✅大致 | yfinance(部分回 1970s)、Stooq(免費 EOD 全球)、Nasdaq Data Link | yfinance 長歷史**綁倖存者**(下市名消失)，需配①|
| **Ken French / AQR 因子長序列** | 因子 OOS 驗證 | ✅ | Ken French Data Library(已接 pandas_datareader)、AQR datasets | 只有因子報酬非個股 |
| **跨多次危機壓力測試** | regime 穩健 | ✅ | 用 spa.py stationary bootstrap(已建)在長序列上 | — |

> **結論**：擴到 1990s 是免費的，且直接解決「只有 3-4 個熊市、regime 推論誤差大」這個我反覆撞到的牆(docs/09 §三、docs/10 §4e FDR 後無 cell 顯著)。配①才乾淨。

## ③ 擴廣度（放大 √Breadth）

| 項目 | √breadth 增益 | 免費? | 來源 | caveat |
|---|---|---|---|---|
| **全美市場(~3000+ 中小型)** | 廣度 ×6 vs S&P500 | ✅ | yfinance + Russell/全市場 ticker list | 中小型流動性差→**與 NT$10M 容量要求衝突**;且更倖存者 |
| **全球股(歐/日/EM)** | 廣度 ×N + 低相關 | ✅大致 | yfinance(.L/.T/.HK 後綴)、Stooq | 時區/匯率/交易日對齊、台股用 FinMind(docs 第一部分) |
| **多資產(期貨/FX/商品/債/加密)** | 真正低相關、CTA 趨勢 | ⚠️混 | 期貨:Nasdaq Data Link/Databento(付費全)、加密:免費(ccxt)、債/商品 ETF:yfinance | 期貨歷史接續(roll)複雜;但**時間序列動量在期貨上是真效應**(Moskowitz 2012) |

> **結論**：擴廣度單獨**docs/09 已證實效果有限**(IC 隨 universe 變廣而下降)，因為加進來的名訊號更弱。真正有價值的是**低相關的多資產**(期貨趨勢、債、加密)——但那是「不同 alpha 來源」非「同因子更多名」。中小型股與容量要求衝突，慎入。

## ④ 提高 IC（另類資料——乘數效應最大，但最難最貴）

| 項目 | 文獻訊號 | 免費? | 來源 | 預期 |
|---|---|---|---|---|
| **分析師估計修正(estimate revisions)** | PEAD/估計動量(強) | ⚠️免費限量 | Finnhub/FMP 免費 tier、yfinance(僅當前)、IBES(付費歷史) | **最有潛力的免費-ish 因子**;修正動量是穩健 alpha |
| **13F 機構持股** | 超級投資人跟單 | ✅ | Dataroma(已規劃,docs alt-data)、EDGAR 13F 解析 | 季頻+45 天 lag;Buffett/聰明錢 |
| **財報/電話會文本(NLP/LLM)** | Loughran-McDonald/Tetlock/LLM 情緒 | ✅文本免費 | EDGAR 10-K 文本(免費)、transcripts、**本地 Ollama 算**(預算內) | 接 session 自己的 LLM 方向;計算成本=本地 LLM |
| **選擇權(IV/skew/put-call/gamma)** | Cremers-Weinbaum、gamma | ⚠️混 | yfinance 當前 chain、CBOE 免費部分、ORATS(付費歷史 IV) | 歷史 IV 付費;當前可做即時訊號 |
| **短期利益(short interest)** | 擁擠/軋空 | ✅ | FINRA 免費雙週 | 低頻;crowding 訊號 |
| **散戶注意力(Google Trends)** | Da-Engelberg-Gao 2011 | ✅但脆 | pytrends | rate-limit/不穩;需公司名映射 |
| **網路/衛星/信用卡/App** | nowcast 營收 | ❌付費貴 | 第三方供應商 | 超預算;機構級 |
| **總經/跨資產(利率/信用價差/VIX 期限結構)** | regime 分類、macro overlay | ✅ | FRED(免費) | 不是選股 alpha,是 regime/配置輸入 |

> **結論(按免費-ish × 影響)**：① **分析師估計修正**(Finnhub/FMP 免費 tier)是最值得接的下一個因子——PEAD/修正動量是文獻最穩健的之一,且與品質/動量低相關。② **13F**(Dataroma)免費、季頻、聰明錢。③ **文本/LLM 情緒**接上 session 自己的 Ollama 方向(預算內)。④ **FRED 總經**做 regime 分類(改善 docs/05/09 那個太慢的 200SMA gate)。

---

## 優先序建議（預算 <$15/mo + 影響 + 接續現有發現）

1. 🥇 **PIT S&P500 成分股歷史(免費)** → 重跑回測,把倖存者偏誤擠出來(最高槓桿,讓真實值浮現)。
2. 🥈 **延長到 1990s(免費)** → 解決「只有 3-4 個熊市」的統計力瓶頸,讓 regime-conditional/品質的 flight-to-quality 能真正驗證。
3. 🥉 **分析師估計修正(免費 tier)** → 最有潛力的免費新因子,與品質/動量低相關 → 餵進多 sleeve 組合(唯一顯著 alpha 源)。
4. **FRED 總經 → 更好的 regime 分類器**(取代太慢的 200SMA gate;接 docs/10 §4f「互補因子 switch」的發現)。
5. **多資產(期貨趨勢/債/加密)** → 真正低相關的新 alpha 來源,放進多 sleeve。
6.（後）**13F、文本/LLM 情緒、選擇權**。

> **誠實的元結論**：①②(修偏誤+延長歷史)**不會給新 alpha,但會讓現有結論可信**——這是科學誠信的前提,該先做。③④⑤(新因子/低相關資產)才有機會**實質提高組合 alpha**,但 session 已證明單一新因子貢獻多半邊際(品質就是例子);真正的提升來自**多個低相關來源的分散**(docs/08 多 sleeve)。**沒有單一資料維度是銀色子彈;突破來自「修偏誤 + 延長歷史 + 多個低相關 IC 來源的組合」。**

---
*接續 docs/00 §E7、docs/06(Grinold)、docs/09(廣度測試)、docs/10(另類資料)。2026-06-17。*
