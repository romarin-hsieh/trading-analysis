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

## 8. 已試：多資產 TAA「延長歷史」決定性測試 — **我上一條 commit 的預測一半被證偽**（自抓第 N 個失誤）

§6 我下了一個**可證偽的預測**：「2015-24 對 TAA 不利，延長到含熊市的多十年歷史，TAA 會大放異彩（Sharpe 應遠高於 0.74）」。我用 `scripts/taa_long_history.py` 直接驗證——同樣的 Antonacci/Faber 規則，換成有真實多週期記錄的 Vanguard 共同基金代理（含息調整，回溯到 1996，**窗口現在真的包含 2000-02 網路泡沫破裂 + 2007-09 GFC**）：

宇宙 risk=`VFINX(美) VGTSX(國際) VEIEX(EM) VGSIX(REIT)`、def=`VUSTX(長債) VBMFX(總債) VFITX(中債)`、cash=`VFISX(短債)`。

| 策略（1996-2024，淨 10bps） | CAGR | Sharpe | MDD | Calmar |
|---|---|---|---|---|
| Antonacci dual-mom | +8.6% | 0.64 | −40.1% | 0.22 |
| Faber GTAA | +5.8% | **0.58** | −35.0% | 0.16 |
| 60/40 (US/bond) | +7.6% | **0.70** | −34.7% | 0.22 |
| US buy&hold | +9.2% | 0.55 | **−55.3%** | 0.17 |

**各歷史片段總報酬（資本保護測試 — TAA 的整個賣點）：**

| 策略 | 網路泡沫 00-02 | 復甦 03-07 | GFC 07-09 | QE 牛 09-19 | 2015-24 | covid+22 |
|---|---|---|---|---|---|---|
| Antonacci dual-mom | **−8.0%** | +172% | **+3.6%** | +130% | +43% | +13% |
| Faber GTAA | **−1.9%** | +121% | **−12.1%** | +87% | +25% | +5% |
| 60/40 | −11.0% | +59% | −26.2% | +220% | +128% | +53% |
| US buy&hold | **−33.2%** | +88% | **−45.8%** | +400% | +238% | +96% |

**誠實對帳——我的預測一半對、一半錯：**

- ❌ **錯的一半（Sharpe）**：延長歷史**沒有**讓 TAA 的 Sharpe 變好。Faber 全週期 Sharpe **0.58 < 它在 2015-24 的 0.74**；Antonacci 0.64。**全宇宙、全策略、28 年，沒有一個 Sharpe 贏過簡單 60/40 的 0.70。** 我以為「換對窗口 TAA 就會發光」是錯的——TAA 不是被窗口埋沒了「Sharpe」。
- ✅ **對的一半（回撤/資本保護）**：TAA 在兩次真熊市**確實**保護資本，如設計所言。GFC 中 buy&hold −45.8%、60/40 −26.2%，而 **Antonacci 是 +3.6%（正報酬！因絕對動量正確輪到飆漲的長債）**、Faber −12.1%。網路泡沫中 buy&hold −33.2%，TAA 只 −2~8%。全週期 MDD：TAA −35/40% vs buy&hold −55%。

> **更鋒利的結論（比 §7 更強）**：TAA 是**「回撤保險」交易，不是報酬或 Sharpe 增強交易**。它用犧牲牛市漲幅換取熊市保護，兩者對稱 → 全週期 Sharpe 打平甚至略輸 60/40。**真正的鐵證是：這個資產類別宇宙的 Sharpe 天花板 ≈ 0.70，對「策略」不變、對「28 年歷史長度」也不變。** 我把 docs/11 ②「延長歷史」這根槓桿真的拉了，Sharpe 天花板紋風不動——**這是「綁定約束是資料維度（宇宙的資訊含量），不是策略、不是窗口」最強的一次證明。**

> **接回使用者的雙重目標**：使用者要「50-100% CAGR **且** 不承受大幅失本金風險」。Calmar 牆已證明 CAGR 那一半不可能；但**這次證明 TAA/防禦疊加能交付「不失本金」那一半**——把最大回撤從 −55% 壓到 −35%，且**安然度過（甚至獲利於）GFC 與網路泡沫**。對一個會計較「2008 我不能 −50%」的真實投資人，這個防禦價值是真的、可重現的——即使它永遠給不了 CAGR 那一半。這是這整輪研究第一個**對使用者實際效用為正**的可交付結論。

## 9. 已試：兩根「換資料維度」槓桿（PEAD 新 IC 源 ∧ 修倖存者偏誤）— 多代理對抗式驗證

承使用者「三者可以都做嗎」，用 ultracode workflow 同時建 A/B 並各派**兩個對抗式 skeptic**（一個獵 PIT 洩漏、一個攻 in-sample/成本/自相關），第三件 C 我自己合成。兩個 skeptic 都抓到真問題並收緊了結論——這正是本 session 的鐵律：**新 alpha 宣稱必須先被攻擊才採信**。

### 9A — PEAD / SUE（docs/11 ③「新 IC 源」，免費版，只用既有 EDGAR）

`scripts/pead_sue.py`：Bernard-Thomas 季節性隨機漫步 SUE，**只用我們已有的 EDGAR NetIncomeLoss + filed(as_of) 揭露日**（不需 Finnhub）。14,634 個可操作公告。

- **資料品質發現（建構代理自抓）**：EDGAR 10-Q 的 NetIncomeLoss 是**年初至今累計**（~78-81% firm-years 有 |Q1|≤|Q2|≤|Q3| 簽名）→ 必須**逐季拆解** Q2=v(Q2)−v(Q1)…Q4=v(FY)−v(Q3)。直接把 10-Q 當單季會汙染 ~80% 觀測。
- **漂移測試（事件後超額報酬，vs 等權市場）**：Q5−Q1 = **−0.37%(t=−1.66) / −0.11%(t=−0.39) / +0.07%(t=+0.17)** 於 H=21/42/63 天。**無漂移、且分位非單調**（Q1 +0.17%、Q5 −0.20%）。
- **決定性的零訊號控制（baked into 腳本）**：long-only top-quintile sleeve 看似「幫」組合（alpha-t 2.64→2.91），**但這是 beta 不是訊號**——加一個**零訊號**等權全名 sleeve 給 2.89、隨機 20% 給 2.80，**一模一樣的 bump**。唯一隔離訊號的**市場中性 L/S**：Sharpe −0.12（gross 已 −0.04），corr +0.09，且**把 alpha-t 從 2.64 拉低到 2.05**。
- **對抗式驗證**：兩個 lens 都 `claim_holds=true`、high confidence。洩漏 lens：as_of 永不等於 period_end（gap 中位數 +42 天）、多加一根 lag 漂移僅 −0.37%→−0.30%（穩健非刀刃）、**placebo（隨機 SUE 標籤）給 −0.30%/t=−1.33 ≈ 真值** → 那個微負是橫截面/成本 artifact，不是被壓住的正訊號。

> **PEAD 在免費 EDGAR-only 資料上不存在可利用 alpha。** 但本流產出本 session **最重要的方法論升級**：**「long-only sleeve 抬高組合 alpha-t」根本不是 alpha 的證據**——零訊號籃子做得到一樣的事。**唯一有效的 sleeve 測試是市場中性版**。這**回頭打臉 docs/10 §4c**「品質 sleeve 邊際幫助」——那個「幫助」極可能也只是 beta；任何 long-only sleeve 的 incremental-α 主張都須用 L/S 重驗。

### 9B — 修倖存者偏誤（docs/11 ①「修偏誤」）

`scripts/survivorship_test.py`：抓 github 歷史成分股（1996+），補進 109 個**曾在 2015-24 於 S&P500、後被剔除/下市**的名字（BBBY/GME/FOSL/GNW/CZR/AAL…，僅持有到下市），重測兩個最受倖存者偏誤威脅的結論。

| 測試 | cur(501) | union(610) | 結論 |
|---|---|---|---|
| 等權買進持有 CAGR | +16.39% | +15.12% | 倖存者**膨脹 +126bps/yr**（下界）|
| 動量 mom_12_1 t(非重疊) | −0.13 | +0.34 | **兩者皆死**（符號在雜訊內翻）|
| 低波動 t(naive→非重疊) | −5.54→**−1.05** | −1.48→−0.20 | AC 校正後**兩 universe 都不顯著** |

- **skeptic 抓到的關鍵**：所有 IC t-stat 用**重疊 21 天窗 + 日抽樣**（AC1≈0.93）→ naive t **被灌水 ~3.7 倍**。改用**非重疊每 21 天**重算後，低波動的「−5.54 顯著性崩塌」其實是**拿兩個灌水數字對比**——真相是低波動**在兩個 universe 上本來就不顯著**（n_eff=117）。已把非重疊 t 寫進腳本。
- **+126bps 的成分**：~97% 是**世代稀釋**（現成分股是事後贏家），只有 ~+6bps 來自 9 個真正窗內下市者（且用樂觀的「以最後價出場」模型，真倒閉是 −100% → 仍是下界）。
- **覆蓋率誠實註記**：只救回 111/262=42%；最慘的 bankrupt-to-zero（AABA/CBS/ENDP 等）被資料源清掉 → **每個數字都是下界**。

> **修倖存者偏誤後，動量依舊死（強化 docs/09），沒有新 alpha 冒出來**；它揭露的是「單一 universe 的因子顯著性被偏誤+自相關雙重灌水」這個**方法論**問題，不是一個新訊號源。

### 9C — 可交付：回撤預算前緣（`scripts/defensive_overlay.py`）

把已證實的防禦價值變成**可直接用**的東西：在唯一顯著-alpha 策略（5-sleeve 組合，docs/08）上，列出**選你能承受的最大回撤 → 讀出配置 → 接受它誠實的 CAGR**：

| 配置（2015-24, 淨10bps） | CAGR | Sharpe | MDD | Calmar |
|---|---|---|---|---|
| combo 100%（無防禦）| +11.0% | 1.18 | −19.3% | 0.57 |
| 靜態 de-lever L=60% | +7.3% | 1.30 | −11.3% | 0.65 |
| 靜態 de-lever L=40% | +5.4% | 1.45 | −7.0% | 0.78 |
| trend overlay floor=0% | +10.4% | 1.17 | −12.7% | **0.82** |

同回撤(−12.7%)下 trend overlay 比靜態 de-lever 多 +2.5% CAGR（in-sample；已附 §8 的「趨勢擇時不改善全週期 Sharpe」誠實警告 → 靜態 de-lever 是零擇時風險的安全預設）。腳本另印**今日目標權重**（債 49.5%/金 21.9%/股動量 15.7%/防禦 7.7%/槓桿趨勢 5.2%）。

### 9D — 元結論：docs/11 四根槓桿已拉三根

| docs/11 槓桿 | 狀態 | 結果 |
|---|---|---|
| ②延長歷史(1996+) | ✅已試(§8) | Sharpe 天花板 ≈0.70 不動 |
| ③新 IC 源(PEAD) | ✅已試(§9A) | 免費 EDGAR 上無 PEAD alpha |
| ①修倖存者偏誤 | ✅已試(§9B) | 動量仍死、只揭露顯著性灌水 |
| ④日內(ORB) | ❌未試 | 需日內資料（無、且超預算）|

> **三根可用免費資料拉的槓桿都拉了，天花板紋風不動。** 結合 §7/§8，**「綁定約束是資料維度」現在從三個獨立角度被證實**。剩下的 ④日內 ORB 需要我們沒有、且 <$15/月 預算內拿不到的資料。**研究弧線到此徹底收斂**：誠實的可交付不是 50% CAGR 策略（Calmar 牆證明不可能），而是**多 sleeve 組合 + 回撤預算前緣（§9C）**——交付使用者「不失本金」那一半目標。

### 9E — 「組合是不是都輸給 VOO？」誠實對帳（`scripts/combo_vs_voo.py`）— **修正我自己 §9C 的單邊框架**

使用者一針見血：raw CAGR 上組合確實輸 VOO。我跑了完整對帳，**不洗白**：

| 2015-07..2024-12（$10k 起） | CAGR | Sharpe | vol | MDD | Calmar | 終值 |
|---|---|---|---|---|---|---|
| **VOO（S&P 500）** | +13.7% | 0.80 | 18.1% | −34.0% | 0.40 | **$33,775** |
| combo（未槓桿）| +11.0% | 1.18 | 9.2% | −19.3% | 0.57 | $26,954 |
| **combo 槓桿 ×1.96（=VOO 波動，淨 T-bill 融資）** | **+19.8%** | 1.09 | 18.0% | −36.1% | 0.55 | **$55,583** |

- **raw 報酬**：VOO 贏 +2.7%/yr（$33.8k vs $27.0k）。使用者是對的——但這是**拿半風險的組合（9.2% vol）比全風險的指數（18.1% vol）**，對組合不公平。
- **同波動對打（公平戰）**：把組合槓桿到 VOO 的 18% 波動，**組合反過來大勝 VOO**——CAGR +19.8% vs +13.7%、終值 $55.6k vs $33.8k、Calmar 仍贏(0.55 vs 0.40)，兩個子期(+148%/+124% vs +71%/+98%)都贏。
- **回撤才是組合的命**（存在理由）：2020 COVID 崩盤 VOO −33.7% **組合僅 −3.9%**；2018Q4 VOO −18.8% 組合 −5.2%；2022 VOO −24.1% 組合 −15.8%。
- **滾動 1 年**：未槓桿組合只 37% 時間贏 VOO，**槓桿組合 56%**——多頭年輸、跌/盤整年贏。
- **誠實警告**：×1.96 槓桿用 T-bill 融資是樂觀下界（真實 margin 更貴、gap risk、LETF 損耗）；它的 −36% MDD 比 VOO 還深一點。2015-24 是史上最強多頭十年之一=VOO 近最佳、防禦近最差；全週期(§8 含 2000-02/2008)VOO 優勢縮小、−55% MDD 是代價。

> **自我修正**：我 §9C 的回撤前緣**只展示了「de-lever（降風險降報酬）」方向**，害組合看起來像「報酬比 VOO 低的產品」。但組合的高 Sharpe 真正發光處是**槓桿「up」**：同風險下贏 VOO ~+6%/yr。**正確的一句話**：raw 比、且你撐得過 −34~−55% 回撤又只想要多頭終值最大 → 直接買 VOO 完全理性；想要同/更高報酬但控制回撤 → 槓桿組合（承擔槓桿風險）；想睡得著、回撤砍半 → 未槓桿組合。**沒有免費午餐，只有你選哪個軸。**

**雙向槓桿前緣（`scripts/defensive_overlay.py` 已改成完整雙向菜單，借款以 BIL+1.5%/yr 融資）：**

| L | CAGR | Sharpe | vol | MDD | Calmar | $10k→ | vs VOO |
|---|---|---|---|---|---|---|---|
| 0.40（重防禦）| +5.4% | 1.45 | 3.7% | −7.0% | 0.78 | $16,527 | |
| 1.00（組合本體）| +11.0% | 1.18 | 9.2% | −19.3% | 0.57 | $26,954 | 風險調整贏、raw 輸 |
| 1.50 | +14.8% | 1.07 | 13.8% | −29.1% | 0.51 | $36,913 | **勝 VOO($) ∧ 支配(Calmar≥VOO)** |
| 1.75 | +16.6% | 1.03 | 16.1% | −33.6% | 0.49 | $42,872 | **勝 ∧ 支配** |
| 2.00（≈VOO 波動）| +18.4% | 1.01 | 18.4% | −37.9% | 0.49 | $49,543 | **勝 ∧ 支配** |
| VOO 基準 | +13.7% | 0.80 | 18.1% | −34.0% | 0.40 | $33,775 | — |

**L≥1.5 整段都「支配」VOO**（終值更高 ∧ Calmar 更高），因為 VOO 的 Calmar(0.40) 太差。代價：L=2 的 MDD −37.9% 比 VOO 略深、且承擔保證金/gap/融資風險。腳本另印**今日權重**（債49.5/金21.9/股動量15.7/防禦7.7/槓桿趨勢5.2），乘上你選的 L 即可。

## 10. 外部掃描（Falak Khan / London Strategic Edge）＋ 本業面（營運）基本面因子實測

使用者給了 IG @falaktb 三支 reel ＋ londonstrategicedge.com/backtest?mode=auto，要「依本業面參數想更多量化可能」。

**來源辨識**：@falaktb = **Falak Khan**，**London Strategic Edge(LSE) 創辦人**（£5.5M seed）——IG 帳號與那個 backtest 工具是同一個產品。LSE = 免費「Bloomberg 替代」：tick 級回測 30 年、ML Studio(XGBoost/LSTM/**transformer**)、策略語言 Brue、16,000+ 商品、「訓練在自家所有回測上的 LLM」（=reel3 的 20B LoRA 微調）。三支 reel：①transformer attention 動態加權 returns/vol/autocorr——**他自己的結論正是本 session 主軸**：「測 attention 在**樣本外**是否成立，還是只是擬合 regime 一變就消失的結構」；②gamma scalping/delta hedging(選擇權，需我們沒有的資料)；③微調 20B LLM 做「機構級」分析。

> **戰略判讀**：LSE 是**技術/ML/tick 強權，但明說「非基本面」**（"rather than traditional fundamental analysis"）。那個盲點正是我們**已證實的唯一 edge**：point-in-time **本業基本面**。而 `mode=auto`＝**自動策略優化器**＝Falak reel#1 自己警告、也正是我們 DSR/PBO/SPA＋市場中性 L/S-vs-beta 控制專門在抓的**過擬合機器**。哲學一致，工具的誘惑就是陷阱。→ 正確的事是往 LSE 忽略的軸（本業基本面）加碼。

**實測：7 個新「本業（營運）基本面」因子**（`scripts/core_business_factors.py`，500 檔 S&P500，2015-24，leak-free，市場中性 L/S 淨10bps，加零訊號控制）：

| 因子 | ICIR | t | IR16-19 | IR20-24 | L/S Sharpe | a_t+LS | verdict |
|---|---|---|---|---|---|---|---|
| op_margin_level（營益率 OpInc/Rev）| −0.07 | **−3.63** | −0.07 | −0.08 | −0.60 | 1.17 | **反號(穩定)** |
| op_margin_trend（營益率擴張）| +0.10 | +4.52 | +0.00 | +0.16 | +0.13 | 2.17 | WEAK(前半死) |
| gp_level（毛利/資產，已知贏家）| +0.15 | +7.43 | +0.20 | +0.11 | +0.36 | 2.53 | 重現但 <控制 |
| gp_trend（品質動量）| −0.04 | −2.03 | −0.09 | −0.01 | +0.01 | 2.22 | FAIL |
| cfo_profitability（現金獲利）| +0.04 | +1.77 | +0.10 | +0.02 | −0.05 | 2.02 | FAIL |
| revenue_growth（營收成長）| +0.04 | +2.08 | +0.06 | +0.03 | +0.19 | 2.15 | WEAK(beta) |
| quality_improving（高∧改善品質）| +0.05 | +2.60 | +0.02 | +0.08 | +0.12 | 2.31 | WEAK |
| **零訊號 EW 控制(beta baseline)** | | | | | | **2.89** | combo base 2.64 |

- **沒有任何新因子是真訊號（winners=空）**。決定性發現：**零訊號 EW-all 控制 sleeve 把 combo alpha-t 從 2.64 抬到 2.89**，而**每個因子的市場中性 L/S sleeve 都 <2.89** → 組合層級「加分散 beta」勝過「疊因子訊號」。連 gp_level(L/S 2.53)都過不了這嚴格 portfolio bar。
- **兩個有意思的真發現**：(1)**`op_margin_level` 穩定反號**（高營益率→低報酬，IC t=−3.63，兩半都負）——這**完全符合 Novy-Marx**：毛利/**資產**有效，但**營益率/營收**無效(高margin被追捧/擁擠)。(2)**portfolio 教訓**：combo 的 edge 是**分散/beta-shaping，不是因子 alpha**——這從新角度再次證實本 session 主軸。
- **誠實註記**：portfolio bar(贏零訊號 beta 控制)很嚴，連 gp_level 都「WEAK」——這不代表 GP 無用(它**獨立** ICIR+0.15/兩半同號/L/S+0.36 都真、重現已知贏家)，而是**沒有新本業因子超過 GP**＋組合不需更多因子 sleeve。

> **§10 鐵律**：**本業基本面因子空間在 gross_profitability 到頂**，7 個新營運因子無一超越。結合 §4-9，**所有「能用現有資料測」的 alpha 路徑都已測盡**。剩餘真路：(A)需新資料的 alpha(日內 ORB／選擇權 VRP-gamma／分析師估計修正／sector-relative 需 sector map)；(B)**非 alpha 但有產品價值**＝Falak/LSE 式的 **LLM 分析層**（把我們的因子/regime/combo 輸出轉成機構級敘述餵 dashboard，對齊使用者 V1 LLM 路線）。**alpha 的綁定約束仍是資料維度；新增量價值在分析/呈現層，不在再找因子。**

## 11. 使用者自選宇宙（137 檔高波動）的動量規則消融實驗（2025，多代理驗證）

使用者問「把規範套到這 137 檔、2025 賺多少」＋「測高波動友善變體能否不輸 buy&hold」。`scripts/custom_universe_2025.py`＋`scripts/custom_universe_variants.py`（8 變體消融），2 個 skeptic 驗證（洩漏＋框架）。

| 操作 | 2025 報酬 | Sharpe | 波動 | MDD | 年換手 |
|---|---|---|---|---|---|
| V6 純動量 k=20 | **+67.9%** | 1.13 | 64% | −45% | 806% |
| **等權 buy&hold（全宇宙）** | **+62.8%** | **1.75** | 31% | −26% | 0% |
| V5 純動量 k=10（無規則）| +62.7% | 1.02 | 77% | −47% | 927% |
| VOO | +17.8% | 0.98 | 19% | −19% | 0% |
| V3 拿掉現金擇時 | +12.0% | 0.48 | 50% | −38% | 2359% |
| V1 baseline（全規則）| +6.8% | 0.38 | 49% | −38% | 2056% |
| V4 只留上升趨勢濾網 | +2.3% | 0.36 | 66% | −52% | 1351% |
| V7 寬停損(150日) | −1.3% | 0.29 | 63% | −45% | 1331% |
| V2 拿掉停損、留擇時 | **−10.4%** | 0.15 | 64% | −50% | 1290% |

- **單調鏈 V1(+6.8%)→V3(+12.0%)→V5(+62.7%)**：每拿掉一條規則就多賺。**最大元兇＝SPY-200SMA 現金擇時**（春季賣壓轉現金、錯過 V 型反彈，拿掉它報酬翻倍）；**日 50 日線停損是第二稅**（48-54% 波動股被甩耳光，換手 2000%+）。
- **唯二追平/贏 buy&hold 的（V5/V6）是「拿掉所有選股、退化成宇宙本身」**——而且**風險調整輸**（Sharpe 1.13 vs 1.75、MDD −45% vs −26%）。V6 的「贏」是 k 旋鈕的抽籤（k-sweep 非單調：k=15 +54.9% 反輸 buy&hold；50bps 真實成本下優勢消失），**非 alpha**。
- **非單調的誠實皺褶**：V2(拿掉停損但留擇時)=−10.4% 比 baseline 還差——留著現金擇時又拿掉下檔阻尼，壞 regime 全曝險。
- **對抗式驗證（都 high confidence、claim_holds=true）**：額外 +1/+2 bar lag 報酬**不崩反升**（V6 67.9→77.6→79.0%）＝真實慢速動量訊號、非洩漏；故意洩漏控制證明 1-bar timing 無法解釋 headline；5 檔 2025 IPO 正確排除。選股偏誤實證：宇宙 79% 上漲、中位 +23.8%、PL +397%/BE +272%/ASTS +236%/OKLO +228%。

> **§11 鐵律**：**在「事後挑出的飆股清單」上,規則只會減分,贏 buy&hold 的唯一方法是「停止選股、直接持有整個清單」——而那就是選股偏誤本身,不是策略。** 規則沒壞,是這套「有序大型股趨勢」規則與「高波動小型火箭股」宇宙**錯配**。要在高波動主題股上做,得設計**另一套**規則（無日停損、無現金擇時、高 K 分散）並嚴格 OOS 驗證——但 2025=n=1,任何變體的「edge」都過不了樣本外。**沒有可信的前瞻獲利數字:`+62.8%` 是回測幻覺,`+6.8%` 是規則被高波動洗掉。**

## 12. 為高波動標的量身設計規則 ＋ 嚴格 OOS 驗證（機械式 PIT、倖存者-aware 宇宙，多代理對抗驗證）

承使用者選 (A)：設計一套**為高波動標的量身做**的規則並嚴格驗證。**關鍵誠實設計**：宇宙必須**機械式 PIT 定義**（非手挑清單，避開 §11 的選股偏誤）＋**倖存者-aware**（610 檔=501 現任+111 已剔除，讓爆掉/下市的高波動股**被納入**）。每月取**滾動 126 日實現波動前 30%** 為「高波動 cohort」（全 PIT、lagged）。`scripts/highvol_ruleset.py`，5 變體消融，2 skeptic 驗證。

| 變體（2015-24） | CAGR | Sharpe | MDD | Calmar | 換手 |
|---|---|---|---|---|---|
| R0 舊規則（日50SMA停損+SPY現金擇時, eq-wt, K=10）| 10.9% | **0.48** | **−73%** | 0.15 | 889% |
| R1 量身版（逆波動權重+25%波動目標+無停損+K=20）| 19.7% | 0.88 | −33% | 0.59 | 1027% |
| **R2 = R1 拿掉波動目標** | 23.7% | **0.95** | −33% | **0.71** | 1076% |
| R3 = R1 拿掉逆波動(等權) | 21.2% | 0.86 | −38% | 0.56 | 931% |
| R4 = R1 拿掉 cohort 篩選(全610) | 19.2% | 0.89 | −31% | 0.62 | 1189% |
| **BENCH cohort 等權 buy&hold（公平標竿）** | 16.2% | 0.71 | −39% | 0.42 | 223% |
| VOO | 13.1% | 0.79 | −34% | 0.39 | 0% |

- ✅ **量身版「決定性」勝過舊規則**（設計診斷正確）：**拿掉日停損＋現金擇時**，同一 cohort 從 Sharpe 0.48 / MDD −73%（R0）→ ~0.9 / −33%。**這是這次唯一穩健、可部署的大發現**：舊的停損+擇時 overlay 在高波動股上是災難。
- 🔧 **資料糾正了我兩個設計選擇**（measure don't assume）：**波動目標反而傷害**（R2 拿掉它最佳 Sharpe 0.95）；**cohort 篩選幾乎無效**（R4 套全宇宙打平）；逆波動只是 wash。**最誠實的最小設計＝動量選股 + (等權或逆波動) + 無停損 + 無現金擇時**，比我提的還簡單。
- ❌ **但 R1「贏 cohort buy&hold」只在 point estimate，統計上不顯著**：skeptic 把 R1 對 cohort buy&hold 回歸 → **corr 0.71、beta 0.65、~70% 只是 cohort beta**；alpha 年化 ~9.6% 但 **t(alpha)=1.74 < 1.96**；主動價差 Sharpe 僅 0.128、**11 年只有 7 年為正**（2016 −23.7%、2021 −14.4% 大虧）、PSR(R1−BH)=0.66。**時間集中、符號不穩 → 非結構性 edge。** （腳本印的 DSR=0.98 是用 5 個高度相關變體當 null 的假象,**別引用**;可信的是 t=1.74 / PSR 0.66。）
- **換手 1000%+**:高波動股真實滑價遠超 10bps,會進一步侵蝕這個薄 edge。**2025 OOS（薄,僅 86/610 有資料）**：R1 +67.0% 小輸自己的 cohort buy&hold +76.8%,VOO +18.3%——與全期一致（R1 機制贏不過 cohort 本身）。

> **§12 鐵律（與整個 project 完全一致）**：為高波動標的量身設計**確實**做出比失敗版好太多、且 point-estimate 贏 buy&hold 的規則——**但嚴格驗證後,贏 buy&hold 的部分是「風險塑形 + 一個薄、不顯著(t=1.74)、年份不穩」的價差,不是 proven alpha。** 真正穩健的可交付結論是**減法**:在高波動股上,**別用日停損、別用現金擇時**,動量+分散+不擇時就贏過那套精巧的舊規則。要超越 buy&hold 本身,這個資料(單一 10 年路徑)給不了統計證據。

---
**Sources（主要）**：[London Strategic Edge](https://londonstrategicedge.com/) · [LSE GitHub](https://github.com/londonstrategicedge) · [Quantpedia Explains](https://quantpedia.com/quantpedia-explains-trading-strategies/) · [Carver Systematic Trading](https://qoppac.blogspot.com/p/systematic-trading-start-here.html) · [QuantConnect 策略庫](https://www.quantconnect.com/docs/v2/writing-algorithms/strategy-library) · [Ernie Chan blog](http://epchan.blogspot.com/) · [ORB 論文 SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) · [ML 異象預期報酬 SSRN 4702406](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4702406) · [Antonacci Dual Momentum GTAA](https://quantpedia.com/active-dual-momentum-gtaa-strategy/) · [The Wheel](https://www.predictingalpha.com/wheel/) · [Kalman pairs QuantStart](https://www.quantstart.com/articles/Dynamic-Hedge-Ratio-Between-ETF-Pairs-Using-the-Kalman-Filter/) · [londonstrategicedge.com](https://londonstrategicedge.com/)
*接續 docs/00 §E、docs/11(換資料維度)、docs/12(方法地圖)。2026-06-17。*
