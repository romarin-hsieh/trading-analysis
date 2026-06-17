# Algotrading 策略目錄 — 廣域搜尋（Reddit/論壇/論文/知名評論）＋ 對照本 session 已驗證

> 來源：r/algotrading（+r/quant/r/thetagang）、Quantpedia（700+ 策略 / ~70 免費）、Robert Carver《Systematic Trading》、Ernie Chan、QuantConnect 策略庫、ORB 論文(Zarattini-Barbon-Aziz)、Antonacci/Faber TAA、Kalman pairs(QuantStart)、londonstrategicedge.com。**價值在第三欄：對照本 session 已測/已建/已證偽，標出「真正值得試的新東西」。**

## 0. 跨來源的共通智慧（與本 session 發現高度一致）

- **多策略是必須的**（r/algotrading、Carver）：市場在 trend / mean-reversion / random 之間切換，沒有單一策略全天候有效 → 呼應我的多 sleeve 結論。
- **驗證才是真 sauce**（r/algotrading）：最多讚的「100% 勝率」策略多是 repainting / 多時框 bug，live 會死 → 呼應我三次對抗 review 抓 in-sample artifact。
- **alpha 會衰退**（學術 2024-26）：異象報酬 **OOS 低 26%、發表後低 58%**（Azevedo-Hoegner-Velikov、McLean-Pontiff）；ML 策略扣成本後仍存活但大幅縮水 → **精準對應我量到的 Minervini/動量衰退**。
- **波動目標 + 組合預測 > 單一策略**（Carver）→ 呼應我的 vol-target / 多 sleeve。

## 1. 策略目錄（按「我能否用現有資料試」分組）

### 🟢 A. 用現有日線資料就能試（最高優先 — 免費、低相關、未測）

| 策略 | 來源 | 本 session 對照 / 為何值得試 |
|---|---|---|
| **季節性/日曆異象**：turn-of-month、overnight effect、FOMC drift、OpEx-week、sell-in-May、月底再平衡 | Quantpedia(免費)、學術 | **未測、免費、與我的因子低相關** → 最佳新 sleeve 候選。overnight anomaly(夜間報酬>日間)尤其穩健 |
| **配對交易 + Kalman 動態 hedge ratio** | Chan、QuantStart、QuantConnect | **我已建 Kalman(docs/12)** → 補一個完整 cointegration pairs 回測即可；市場中性、低相關 |
| **橫截面短期反轉**(1-週/月 loser 反彈) | Quantpedia、Chan | 我測過 mega-cap 上 5 日反轉死(docs/06)，但**廣 universe + 風控版**值得重試 |
| **Betting-Against-Beta / 低 beta** | Frazzini-Pedersen、Quantpedia | ≈ 我的 low-vol(universe 特定 docs/09)；BAB 是槓桿調整版，值得做對 |
| **品質因子**(QMJ/gross profitability) | AQR、Novy-Marx | ✅ **已驗證=最強穩健因子**(docs/10 ICIR +0.30) |
| **絕對動量趨勢過濾**(價格>10mo SMA 才持有) | Faber GTAA | 我的 regime gate 變體；對廣資產類別有效 |

### 🟡 B. 需要新資料（中優先 — 對應 docs/11 換資料維度）

| 策略 | 來源 | 需要的資料 |
|---|---|---|
| **多資產 TAA：Antonacci Dual Momentum**(12mo 絕對+相對動量輪動 股/債/金/商品/REIT) | Antonacci、AllocateSmartly | 多資產 ETF(yfinance 免費)——**我測過集中版失敗，但正版在「廣、低相關資產類別」上是經典**；值得做對 |
| **Faber GTAA / Accelerating Dual Momentum** | Faber、Grzegorz Link | 多資產 ETF(免費)；加速版用 1+3+6mo 複合動量 |
| **波動率風險溢價(VRP) / The Wheel**(賣 ATM 短天期、CSP+CC) | r/thetagang、Quantpedia | **選擇權資料**(docs/11④)——隱含>實現波動是穩健溢價，但有尾部風險、需 delta hedge |
| **PEAD / 盈餘漂移 + 估計修正動量** | 學術、Quantpedia | 分析師估計(Finnhub/FMP 免費 tier，docs/11④) — **最有潛力的免費新因子** |
| **13F 聰明錢跟單** | Dataroma | 13F(免費季頻)；我規劃過(docs alt-data) |

### 🔴 C. 需要日內/高頻資料 + 執行基建（高潛力但門檻高 — docs/11③）

| 策略 | 來源 | 數字 |
|---|---|---|
| **ORB Stocks-in-Play**(5-min 開盤區間突破，限相對成交量前 20) | **Zarattini-Barbon-Aziz 2024**(SSRN 4729284) | **2.4 Sharpe、β≈0、2016-23 總報酬 1637% / IRR 41.6%**(扣成本後)——近年最亮眼的零售-quant 結果，但需日內資料＋低延遲＋與 NT$10M 容量/隔夜不留倉的取捨 |
| **Gap fade**(5-min 報酬 Z-score + 量過濾，淡化過度延伸) | r/algotrading、BuildAlpha | 區間日 / 財報後消化最有效 |
| **PCA 統計套利**(全市場殘差均值回歸) | Avellaneda-Lee | 高周轉、需低成本執行；容量受限 |
| **微結構/order-flow imbalance、VPIN** | Easley-LdP | tick 資料 |

### ⚫ D. 研究性 / 高過擬合風險（謹慎 — 已被 session 證明易過擬合）

LSTM/Transformer 價格預測(Kronos)、強化學習(Deng)、GNN 股票關聯(AlphaStock)——**學術也警告 spurious predictability**(arxiv 2604.15531)；只有配豐富 alt-data 特徵才有意義，否則=在弱訊號上過擬合(正如 regime-rotation 被證偽 docs/10 §4g)。

## 2. 對照本 session：已測 / 已建 / 待試

| 狀態 | 策略 |
|---|---|
| ✅ **已測且有結論** | 動量(universe 特定)、短期反轉(mega-cap 死)、low-vol/BAB(universe 特定)、品質(✅最強)、價值(死)、insider(弱)、regime gating(減損)、多 sleeve 風險平價(唯一顯著 alpha)、集中 dual-momentum(防禦失敗)、regime-rotation(in-sample 雜訊 證偽) |
| ✅ **已建工具** | Kalman(動態 beta/hedge)、O5 risk-parity、O1 DSR/PBO/SPA、regime-conditional 歸因、2 個 alt-data connector |
| 🎯 **最該試的新東西** | **①季節性/日曆異象 ②完整 Kalman pairs ③正版多資產 dual-momentum TAA ④PEAD/估計修正(免費 alt-data)** |

## 3. 我的建議（給現有資料 + 預算 $0 + session 結論）

> 在「日線美股 + 基本面 + 多 sleeve」的現狀下，**最高槓桿、低相關、可立即做的三個新 sleeve**：
> 1. **季節性 sleeve**（turn-of-month + overnight + FOMC drift）——免費、與動量/品質低相關、文獻穩健 → 餵進多 sleeve 組合(唯一顯著 alpha 源)。
> 2. **Kalman 配對交易 sleeve**——市場中性、已有 Kalman 工具、與方向性 sleeve 低相關。
> 3. **正版多資產 dual-momentum**（廣資產類別，非我之前的集中失敗版）。
>
> 需換資料才能解鎖的高潛力標的：**ORB stocks-in-play(日內，2.4 Sharpe)** 與 **VRP/options**——對應 [docs/11](11-data-dimensions.md) 的頻率/選擇權維度。
>
> **但仍守 session 鐵律**：每個新策略都要過嚴謹閘門(DSR/SPA/PSR-vs-1N + 對抗 review)，且預期**單一策略貢獻邊際、真價值在多個低相關 sleeve 的分散**。網路上的「2.4 Sharpe」「1637% 報酬」幾乎都有資料偏誤/容量/執行假設——當靈感，不當已驗證 alpha。

## 4. 已試：季節性 sleeve（結果：**衰退/邊際**，誠實負面）

實作 turn-of-month + overnight 兩個日曆 overlay（`scripts/seasonality_sleeve.py`，SPY、含成本）：

| 策略 | CAGR | Sharpe | MDD | %在市場 |
|---|---|---|---|---|
| buy & hold | +13.1% | 0.79 | −33.7% | 100% |
| **turn_of_month** | +0.6% | **0.12** | −10.2% | 24% |
| **overnight**(close→open) | +6.7% | 0.62 | −29.4% | 99% |

- **TOM 已衰退到雜訊**（Sharpe 0.12）——它是最有名的日曆異象之一，被重度套利掉了。
- overnight 真實但 **Sharpe 0.62 < buy-hold 0.79**，且與股票 sleeve 相關（corr to combo +0.22）。
- **加進多 sleeve 組合反而傷害**：alpha t 從 **2.64 掉到 1.94（跌破顯著）**、Calmar 0.61→0.54——風險平價過配近零報酬的 TOM 而稀釋。

> **直接印證目錄自己的警告**（alpha OOS −26%/發表後 −58%）：TOM 這種廣為人知的日曆異象在 2015-24 已被套利殆盡。**又一個「網路熱門策略≠可驗證 alpha」的實證**。（註：僅測 SPY 市場擇時版；橫截面 overnight-return 因子或其他資產上可能不同，但簡單版已衰退。）

## 5. 已試：Kalman 配對交易（結果：**真市場中性但已死**，精煉教訓）

用 Kalman 動態 hedge ratio（`scripts/kalman_pairs.py`）測 6 組經典配對（V/MA、KO/PEP、XOM/CVX、GS/MS、HD/LOW、MSFT/GOOGL），z-score 均值回歸、含成本：

| | Sharpe | corr to combo | 加進組合 |
|---|---|---|---|
| 配對 sleeve | **−0.50**（全部 −0.43~+0.10）| **+0.01**（真市場中性 ✅）| 反而傷害：alpha t 2.66→**1.79** |

- **市場中性假說正確**：corr +0.01——配對確實是「不同 beta」的東西，理論上能分散。
- **但配對 alpha 已死**：6 組全部 net-negative，成本吃光（Gatev 2006 之後人人在做，pairs 套利衰退殆盡）。
- **精煉教訓：「不相關」不夠，必須「不相關 ∧ 有利可圖」。** 一個賠錢但不相關的 sleeve，風險平價仍給它權重 → 拖累。

> **三連敗（rotation→seasonality→pairs）的鐵律**：每個網路/論文熱門新策略，不是 in-sample 雜訊、就是衰退、就是賠錢。**多 sleeve 風險平價組合（docs/08，alpha t=2.64）仍是這個資料上的天花板，加任何東西都不改善。** 要突破只剩 [docs/11](11-data-dimensions.md) 的換資料維度（PEAD 需估計資料、ORB 需日內、正版 TAA 需更多資產類別）。

## 6. 已試：多資產 TAA（Antonacci/Faber）— **此十年弱，但這正是「短歷史偏誤」的鐵證**

正版多資產 TAA（`scripts/taa_dual_momentum.py`，10 個資產類別 ETF：美/國際/EM 股、REIT、商品、金、債、現金）：

| 策略 | CAGR | Sharpe | MDD | Calmar | 16-19 | 20-24 |
|---|---|---|---|---|---|---|
| Antonacci dual-mom | +7.5% | 0.54 | −29% | 0.26 | 0.55 | 0.55 |
| **Faber GTAA** | +6.6% | 0.74 | **−15.5%** | 0.42 | 0.82 | 0.71 |
| 60/40 (SPY/AGG) | +9.6% | **0.87** | −21.7% | 0.44 | 1.32 | 0.71 |
| SPY buy&hold | +14.6% | 0.85 | −33.7% | 0.43 | 1.11 | 0.75 |

- TAA（0.54/0.74）**輸給簡單 60/40（0.87）和 SPY（0.85）**——Faber 確實壓低回撤（−15.5%）但犧牲報酬。
- 對組合 corr **+0.66**（高，因組合已有 trend/債/金 sleeve）→ 加進去稀釋（alpha t 2.64→2.27）。
- **但這是 period-specific**：2015-24 是「持續股票多頭」十年，**對 TAA 最不利的環境**（它一直去風險、錯過漲幅）。TAA 在**熊市十年（2000-2010）大放異彩**（Faber 原始回測橫跨多次熊市）——而我的樣本只有 ~3-4 個熊市。

> **這是 docs/11 ②「延長歷史」最乾淨的鐵證**：一個有真實百年 OOS 記錄的策略（TAA），在一個刻意對它不利的 10 年窗口上看起來很弱。**用 2015-24 評斷 TAA 是不公平的——這正是短歷史偏誤。** 這個結果不削弱 TAA，反而**強化「綁定約束是資料/歷史長度，不是策略」**的結論。

## 7. 四連敗的結論（rotation→seasonality→pairs→TAA）

| 候選 | 結果 | 失敗模式 |
|---|---|---|
| regime-rotation | 證偽 | in-sample 雜訊 |
| seasonality(TOM/overnight) | 邊際 | 異象衰退 |
| Kalman pairs | 賠錢 | 套利殆盡、成本吃光（但**真市場中性** corr +0.01）|
| 多資產 TAA | 此十年弱 | 短歷史偏誤（樣本是 TAA 最差環境）|

> **鐵律確立**：在「2015-24 美股日線 + 基本面」這個資料上，**多 sleeve 風險平價組合（docs/08，alpha t=2.64）是天花板，加任何網路/論文熱門策略都不改善**——它們不是 in-sample、就是衰退、就是賠錢、就是被短歷史誤判。**這不是策略不夠多，是資料維度到頂。** 真正的下一步只剩 [docs/11](11-data-dimensions.md)：①修偏誤(PIT 成分股) ②延長歷史(1990s，讓 TAA/品質/regime 能被公平驗證) ③新 IC 來源(PEAD/13F/估計修正) ④日內(ORB)。**先換資料，策略才有意義。**

---
**Sources（主要）**：[Quantpedia Explains](https://quantpedia.com/quantpedia-explains-trading-strategies/) · [Carver Systematic Trading](https://qoppac.blogspot.com/p/systematic-trading-start-here.html) · [QuantConnect 策略庫](https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library) · [Ernie Chan blog](http://epchan.blogspot.com/) · [ORB 論文 SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) · [ML 異象預期報酬 SSRN 4702406](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4702406) · [Antonacci Dual Momentum GTAA](https://quantpedia.com/active-dual-momentum-gtaa-strategy/) · [The Wheel](https://www.predictingalpha.com/wheel/) · [Kalman pairs QuantStart](https://www.quantstart.com/articles/Dynamic-Hedge-Ratio-Between-ETF-Pairs-Using-the-Kalman-Filter/) · [londonstrategicedge.com](https://londonstrategicedge.com/)
*接續 docs/00 §E、docs/11(換資料維度)、docs/12(方法地圖)。2026-06-17。*
