# Fabric 驗收標準 v1 — 機制/演算法/模型/理論的統一測試規格

> /goal(2026-07-07):重新設計一套 fabric 驗收標準,對每個機制逐一測試並各出一份標準化測試報告(TR)。
> v1.2(2026-07-07):對抗性框架審查完成(雙代理:文獻攻擊 A1-A10、程式碼攻擊 B1-B13,White/Hansen/Harvey-Liu/AHM/FIM/Shumway/Lo/Cederburg/Hoffstein 為基點)→ §5 修訂案。v1.1:新增 F9/F10(TR-11 引入)。
> 本規格把整個專案 60+ commits 的教訓法典化:每一條 F 規則都對應一個我們真實踩過、抓過的坑。

## 1. 驗收規則(每份 TR 必須逐條核對)

| # | 規則 | 來源教訓 |
|---|---|---|
| **F1 無洩漏** | 所有訊號 ≥1 bar lag;基本面用 `as_of`(揭露日);時區換算後嚴格次日進場 | CV embargo 洩漏、PEAD period_end 陷阱、Serenity 時區 |
| **F2 淨成本** | ETF ≥5bps/腿、個股 ≥10bps/腿,計在換手上;報告年化換手 | 隔夜效應毛 Sharpe 0.89 → 淨 −0.97(成本牆) |
| **F3 可投資基準** | 對照「同宇宙 buy&hold」+「VOO/QQQ」,絕不對零 | 動量 sleeve「贏」其實輸給同清單 B&H 57pp |
| **F4 樣本量** | 每組實驗 ≥3,000 個觀測(單位須明示:bar×資產/事件/橫截面×日),橫跨 ≥5 個日曆年度 | 單年 n=1 教訓(2025 OOS) |
| **F5 多重測試** | 宣稱 alpha 須報 null bar(E[max Sharpe|N trials])或 DSR/PBO;N 必須誠實含所有試過的變體 | zoo 59 變體 null bar 0.84;DSR 被共線性騙 |
| **F6 控制組** | 任何 alpha 宣稱配一個零訊號/隨機/placebo 控制 | 零訊號籃子抬 alpha-t 至 2.89;Serenity placebo +18.7% |
| **F7 子期穩定** | 2015-19 vs 2020-26 同號;報告聚類校正 t(月度 CR1 或 block bootstrap) | 低波動 t −5.54 → 非重疊 −1.05;事件聚類 t 灌水 |
| **F8 判定** | **PASSED** = 達成原始宣稱且過 F5/F6/F7;**PARTIAL** = 機制如設計運作但無 alpha(風控/工程價值);**FAILED** = 未達成原始宣稱 | 「有效」≠「賺錢」:vol-target 是 PARTIAL 不是 FAILED |
| **F9 路徑隨機化** | 假設不知未來:PASSED 宣稱須附 K≥300 個隨機起點視窗的 Sharpe **分布**(vs 同視窗基準);P(beat)≥60% 才算 robust。單一起點的全期點估計不足採信 | TR-11:XS 動量點估計「zoo 榜首」→隨機視窗 P(beat)=23% FAILED;RF 理論(bagging/OOB)的移植 |
| **F10 複測政策** | 驗收標準有實質變更時,先前已關閉的機制**必須**在新標準下複測——除非其原測試邏輯與新標準相同(記錄豁免理由) | TR-11 複測 5 個舊機制:2 個判定改變(動量降級、IBS 升級)=政策的存在證明 |

## 2. TR 報告模板(docs/tests/TR-XX-name.md)

每份 TR 必含:**⓪ F0 適用分類聲明(動工前先寫,v1.2-A10+分類學擴充)**:可證偽宣稱、PASSED/PARTIAL 判準、**機制的功能分類與原生棲地(資產×頻率×廣度×年代×用途,見 [docs/19 分類學](19-mechanism-taxonomy.md))、本次測試座位、座位錯置風險自評(低/中/高)、若 FAILED 的翻案條件**——這讓未來能區分「機制失效」vs「切入座位錯誤」;①機制原始定義+理論假設+出處論文/連結 ②相關機制(本 repo 已測的近親) ③預期目標 ④測試設計(宇宙/期間/成本/樣本數) ⑤結果表(年化報酬、Sharpe、MDD、對照基準) ⑥**圖表**(權益曲線或分布圖,PNG 於 docs/tests/img/) ⑦判定 PASSED/PARTIAL/FAILED(**效力範圍=被測座位×棲地**) ⑧衰退估計(vs 原論文/宣稱數字) ⑨失敗原因歸因(區分:機制衰退/棲地錯置/成本/樣本) ⑩可組合性(能和哪些既有 sleeve/機制搭)。

## 3. 測試矩陣(本輪)

| TR | 機制 | 出處 | 狀態 |
|---|---|---|---|
| TR-01 | 統計套利:共整合 pairs(Engle-Granger) | bradleyboyuyang/Statistical-Arbitrage、Medium pairs 教學 | 本輪新測(Kalman 版已測=虧損) |
| TR-02 | Markov 變異變遷(regime-switching)模型 | Hamilton 1989 | 本輪新測 |
| TR-03 | 統計因子模型(log-return PCA)組合 | theaiquant factor modeling | 本輪新測 |
| TR-04 | VaR(歷史/參數/Monte Carlo)+ VaR-target 部位 | ibaris/VaR、RiskMetrics | 本輪新測 |
| TR-05 | Monte Carlo 模擬(GBM 路徑) | Black-Scholes-Merton 假設 | 本輪新測 |
| TR-06 | CAPM(β/α)與市場模型 | Sharpe 1964 | 本輪新測(Carhart 版已在用) |
| TR-07 | HRP 階層風險平價 vs 我們的 risk-parity | Lopez de Prado 2016 / PyPortfolioOpt | 本輪新測 |
| TR-08 | ML 混合預測(GBM/LSTM-XGBoost 精神) | manuhup hybrid、GKX 2020 | 本輪新測(LightGBM 代理) |
| TR-09 | Black-Scholes 選擇權定價 | BSM 1973 | **N/A**:無選擇權資料(預算),文件化不可測原因 |
| TR-10 | Agent 框架(TradingAgents/hermes/OpenBB/bullgpt/hyperliquid) | 各 repo | 質性評測(非回測型機制) |
| 既有已測 | 動量/品質/Minervini/risk-parity combo/TAA/PEAD/季節性/Kalman pairs/vol-target/ensemble/五維出場… | docs/05-16 | **整理進 docs/18 註冊表**(依 goal「以既存文件整理」) |

## 4. 宇宙與期間

科技/軟體/衛星航太/半導體:`sector_strategies.SECTORS`(47 檔)+ 已 ingest 的衛星/高波動延伸(ASTS/RKLB/LUNR/PL/OKLO…)+ QQQ/SPY/VOO 基準。期間 2015-01 → 2026-07(≥11 個日曆年)。

## 5. v1.2 修訂案(對抗性框架審查產出;審查全文見 workflow 紀錄)

**立即生效(已執行)**:
| # | 修訂 | 文獻基點 |
|---|---|---|
| **A1** | 旗艦組合判定改標:「PASSED」→「**PASSED(borderline)**:Carhart t=2.64 < Harvey-Liu-Zhu t≥3.0 新因子標準;僅在有效試驗數 ≲10 時存活」。**alpha 的 F8 PASSED 門檻升為 t≥3.0 或 BHY-FDR 1%**;建立 campaign 級 append-only 試驗登記簿,任何 DSR 的 N 必須引用它 | HLZ RFS 2016;Harvey-Liu JPM 2015(Man Group 採納) |
| **A8** | 閘門可行性預審:目標若等價於「1× 下檔 + 3× 上檔」的免費選擇權(狀態優勢),自動標記「aspirational——預期 FAILED」,不再消耗回測資源 | 無套利;SPIVA(89.5% 大型基金 15 年輸 1× S&P) |
| **A10** | 採納 AHM 檢查表為 **F0 封面**:每份 TR 動工前先寫下可證偽宣稱與 PASSED/PARTIAL 判準(docs/18 §4 迴圈已要求先寫 §1-§4,補一句硬性化) | Arnott-Harvey-Markowitz JFDS 2019 |

**規則修訂(自 v1.2 起對新 TR 生效;舊 TR 重跑列入 backlog)**:
| # | 修訂 | 文獻基點 |
|---|---|---|
| **A2/B5** | **F4 v2**:3000 門檻改套用**有效樣本** n_eff = N/(1+(N−1)·ρ̄)(同日橫斷聚類);時序宣稱另須 years ≥ MinTRL(SR, trials, skew, kurt)。TR-02 的 QQQ+SPY(ρ~0.95)誠實讀數 ~2.2k,不達標 | Bailey-LdP 2014 MinTRL;Petersen RFS 2009;Grinold 1989 |
| **A3/B2** | **F2 v2**:個股成本改 max(門檻, 波動/價格縮放 spread 代理);**每份 TR 增加「2× 成本壓力」欄**;宣告書規模;PASSED 策略附容量曲線。小型股(ASTS/RKLB 級)10bps 已知低估 | Frazzini-Israel-Moskowitz JF 2018;Novy-Marx-Velikov RFS 2016 |
| **A4** | **F6 v2**:風控類 PARTIAL 必附**風險匹配被動控制**(常數曝險=策略平均曝險),報告對它的增量——Markov 的「MDD 減半」尚未對 0.59× 靜態控制驗證 | Cederburg et al. JFE 2020(vol-managed 不勝靜態) |
| **A5/B3** | **指標修訂(critical)**:`sharpe()` 全域補 **rf=BIL**、空手日計 BIL 收益(現制 rf=0 在 4-5% 利率世界高估所有絕對 Sharpe,擇時家族尤甚);|lag-1 自相關|>0.05 時報 **Lo (2002) 校正 Sharpe**;A-vs-B 裁決附 Ledoit-Wolf Sharpe 差檢定;PSR 欄位常設 | Lo FAJ 2002;Sharpe 1994;GISW RFS 2007(可操縱性) |
| **A6/B11** | **F11 宇宙合法性**:宇宙須可逐再平衡日機械重建(成分/流動性/PIT 標籤);hindsight 清單僅限相對性宣稱,**絕對數字必標「curated-universe」** | AHM 2019 cat.3;Shumway JF 1997 |
| **A7** | **F7 v2**:經濟故事涉及 2015-26 缺席 regime(長熊/利率衝擊/失落十年)者,授予普遍性判定前須長歷史重放(`taa_long_history.py` 模式) | Dimson-Marsh-Staunton 126 年全球證據 |
| **B1** | **F1 補充**:統一「訊號=收盤 t、成交=收盤 t+1」;中位持有 <10 bar 的規則須附 same-close vs next-close 敏感度 | Perold 1988;Almgren-Chriss 2001 |
| **B6/B9** | **F5 v2**:變體家族以 **SPA(White/Hansen)為主要工具**(closed-form E[max] 只當保守篩;65 個相關變體的真 null 遠低於 0.85);TR 模板增「**設計參數登記**」節(refit 頻率/門檻/視窗全列,跑過替代值就計入 N) | White 2000;Hansen 2005;AHM 2019 |
| **B7** | **F12 再平衡相位**:hold ≥21 bar 的策略須跑全部相位偏移(或 K 分批),判定用相位平均序列(單一相位=抽一張運氣牌,常 >100bps/年) | Hoffstein-Sibears-Faber JII 2019 |
| **B8** | 日曆年閘門只作目標敘述;判定計分改用**全部滾動 252 日窗通過率**+bootstrap 分布 | Lo 2002;Bailey-LdP 2012 |
| **B10** | **資料層規則**:價格在最後真實成交後轉 NaN(ffill 上限 5 bar);store 記下市日+原因;下市注入終端報酬(已知者用實值,否則 −30%/NASDAQ −55%) | Shumway JF 1997;Shumway-Warther 1999 |
| **B12/B13** | 橫斷成本改「漂移權重 vs 目標」記帳(TR-08 迴圈移植進 xsect);隔夜報酬補除息分解(現制方向保守) | FIM 2018;CRSP 慣例 |

**審查同時確認存活(不改)**:F1 洩漏紀律(≥LdP 標準)、F3 同宇宙可投資基準(Sharpe 1991/SPIVA 邏輯,正是抓出動量假象的機制)、F6 零訊號/shuffle 控制(超過多數已發表因子研究)、PSR/DSR/PBO/SPA 工具箱(Bailey-LdP 精確實作)、F7 聚類 t、負結果登記簿(AHM cat.7,「連量化公司都罕見」)、衰退會計(McLean-Pontiff 操作化)、大型 ETF 5bps(FIM 實測下保守)、vectorbt 引擎路徑(order-independent)、TR-05 以 block bootstrap 取代 GBM(Politis-Romano)。

---
*對應執行工具:`scripts/tests/tr_*.py`(每份 TR 一支,可重跑);圖表 `docs/tests/img/`。2026-07-07。*
