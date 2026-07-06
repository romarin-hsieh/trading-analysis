# Fabric 驗收標準 v1 — 機制/演算法/模型/理論的統一測試規格

> /goal(2026-07-07):重新設計一套 fabric 驗收標準,對每個機制逐一測試並各出一份標準化測試報告(TR)。
> v1.1(2026-07-07):新增 F9/F10(TR-11 引入);對抗性框架審查(經濟學文獻/量化公司白皮書基點)進行中,結論將以 v1.2 修訂。
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

每份 TR 必含:①機制原始定義+理論假設+出處論文/連結 ②相關機制(本 repo 已測的近親) ③預期目標 ④測試設計(宇宙/期間/成本/樣本數) ⑤結果表(年化報酬、Sharpe、MDD、對照基準) ⑥**圖表**(權益曲線或分布圖,PNG 於 docs/tests/img/) ⑦判定 PASSED/PARTIAL/FAILED ⑧衰退估計(vs 原論文/宣稱數字) ⑨失敗原因歸因 ⑩可組合性(能和哪些既有 sleeve/機制搭)。

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

---
*對應執行工具:`scripts/tests/tr_*.py`(每份 TR 一支,可重跑);圖表 `docs/tests/img/`。2026-07-07。*
