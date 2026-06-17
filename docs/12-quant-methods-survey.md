# 量化方法深掘 — 更多可能性的地圖（含 Kalman 實作示範）

> 承使用者要求「深入加強搜尋量化分析的更多可能性」，以 Kalman filter 為例。本文是**方法空間的地圖**：每個方法的一句話原理、交易用途、**誠實評估**（真有用 vs 被高估）、與本專案的適用性。已實作的標 ✅。
> **貫穿全文的誠實前提**（承 [docs/00 §E](00-executive-summary.md)、[docs/11](11-data-dimensions.md)）：這些是**改善估計/執行的工具**，但 session 已證明**綁定約束是資料（IC/廣度/偏誤）不是方法複雜度**。Gu-Kelly-Xiu(2020) 證明 ML 勝線性——**但那是在豐富特徵上**；用弱特徵（純價量），再炫的方法也變不出 alpha。

## A. 狀態空間與濾波（Kalman 等）— **已實作示範**

Kalman filter：維護未觀測狀態 x 與其變異 P。每步 **predict**（model 推進 x、Q 抬高不確定性）→ **update**（用 Kalman gain K×innovation 修正）。Q/R 比是唯一旋鈕：高=信資料（快、雜）、低=信 model（穩、滯後）。

| 方法 | 交易用途 | 誠實評估（本專案實測）|
|---|---|---|
| **Kalman local-linear-trend** ✅ | 自適應趨勢/regime 訊號（lag 比固定 SMA 小）| 實測：turn 比 200SMA 早 10-25 天，**但當 regime gate 反而 whipsaw 更差**（Sharpe 0.87 vs SMA 0.99）。**快≠好**——SMA 的滯後反而濾掉雜訊。|
| **Kalman dynamic regression（動態 beta/hedge ratio）** ✅ | pairs 動態避險比(Elliott 2005)、時變市場 beta | 實測：NVDA 對 SPY 的 beta **0.99→2.88**（靜態 OLS 逼成一個數）。**這是真正有用的應用**——時變參數無爭議。|
| HMM / Markov regime-switching(Hamilton) | 機率式 regime 偵測（取代我固定門檻 regime 標籤）| 比 200SMA 更原則，但 in-sample 擬合風險高、regime 數需指定；session 已證 regime gate 多半減損。中等優先。|
| Extended/Unscented Kalman、Particle filter | 非線性/非高斯狀態 | 過度工程 for 日線股票；留給選擇權/微結構。|

> **結論**：Kalman 的價值在**時變參數估計（動態 beta/hedge ratio）與自適應平滑**，不在「更快的擇時」。已建 `models/kalman.py` + 3 tests + demo。

## B. 均值回歸與統計套利

| 方法 | 用途 | 評估 |
|---|---|---|
| 共整合(Engle-Granger/Johansen) | pairs/籃子配對 | 真效應(Gatev 2006)但 alpha 已衰退、需借券成本；台股/小型股更有空間 |
| Ornstein-Uhlenbeck(half-life) ✅(half_life 已建) | 價差動態、回歸速度 | 配 Kalman 動態 hedge ratio 是經典 stat-arb 棧 |
| PCA stat-arb(Avellaneda-Lee 2010) | 全市場殘差均值回歸 | 高周轉、需低成本執行；容量受限 |

## C. 波動率建模

| 方法 | 用途 | 評估 |
|---|---|---|
| GARCH 家族(ARCH/GARCH/EGARCH/GJR) | 波動率預測 → **vol-targeting/風控** | **高價值且穩健**——vol clustering 是真的；接到我的 vol-target sizing 改善回撤控制 |
| HAR-RV、已實現波動 | 日內→日波動 | 需日內資料(docs/11 ③)|
| 隨機波動/Heston | 選擇權定價 | 需選擇權資料 |

## D. 機器學習（de Prado 棧已部分建）

| 方法 | 用途 | 評估（誠實）|
|---|---|---|
| 樹集成(GBDT/LightGBM) ✅(meta-labeling) | 非線性選股(Gu-Kelly-Xiu) | ML 勝線性**只在豐富特徵上**；純價量 → 邊際。配 alt-data(docs/11④)才有意義 |
| de Prado AFML：triple-barrier ✅、meta-labeling ✅、PurgedKFold ✅ | 標籤/防洩漏 CV | **已建且是對的工程**；防過擬合的基礎建設 |
| **分數差分(fractional differentiation)** | 平穩化同時保留記憶 | **值得補**——比 ADF 後直接差分保留更多訊號；de Prado 招牌 |
| 神經網路(LSTM/Transformer/Kronos) | 序列預測 | headline 數字禁不起嚴格回測(docs/00 §4)；當骨架非已驗證 alpha |
| 強化學習(Deng 2017) | 端到端決策 | 樣本效率差、易過擬合；研究性 |
| 自動編碼器(deep portfolios) | 潛在因子 | 需大資料；研究性 |

## E. 因子萃取/降維

| 方法 | 用途 | 評估 |
|---|---|---|
| PCA/統計因子 | 風險模型、stat-arb | 標準工具；風險模型有用 |
| IPCA(Kelly-Pruitt-Su) | 條件式潛在因子(beta 隨特徵變)| 進階、需豐富特徵 |
| **HRP 層次風險平價(de Prado)** | 組合配置(不需逆共變異) | **值得補**——比我 O5 的 risk-parity 更穩健(用聚類不用逆矩陣)；接 docs/08 多 sleeve |

## F. 訊號處理
分數差分(見 D，值得補)、小波/EMD(去噪，研究性)、Kalman 平滑 ✅。

## G. 機率/貝氏
Black-Litterman(觀點+均衡，值得補做配置層)、貝氏收縮(Ledoit-Wolf ✅、James-Stein ✅)、高斯過程(研究性、貴)。

## H. 尾部風險
**CVaR 優化(Rockafellar-Uryasev)** — 值得補(取代/補充 risk-parity，控尾部)；EVT、copula(相依結構，進階)。

## I. 微結構/執行（已部分建）
Almgren-Chriss sqrt-impact ✅、Kyle-λ/Amihud ✅、VPIN/order-flow imbalance(需日內，docs/11③)。

## J. 網路/圖
GNN 股票關聯(AlphaStock)、lead-lag 網路 — 研究前沿、需大資料、易過擬合。

---

## 誠實的整合優先序（哪些真能動針）

按「已建/值得補/研究性」分類，並對齊 session 結論（瓶頸是資料不是方法）：

1. ✅ **已建且正確**：Kalman(動態 beta/hedge)、de Prado 標籤/PurgedKFold、Ledoit-Wolf/James-Stein、Almgren/Kyle/Amihud、O5 risk-parity。
2. 🔧 **值得補（改善風控/配置，低過擬合風險）**：**GARCH vol-target**(改善回撤)、**HRP**(更穩健配置)、**分數差分**(平穩+記憶)、**CVaR 優化**(尾部)、**Black-Litterman**(觀點融合)。這些**改善估計/執行**，不靠它們變出 alpha。
3. ⚗️ **研究性（高風險、需新資料）**：HMM regime、IPCA、NN/RL/autoencoder/GNN——**只有配 alt-data 豐富特徵(docs/11④)才有意義**；否則是用炫方法在弱訊號上過擬合(正如 regime-rotation 被證偽 docs/10 §4g)。

> **元結論**：這些方法**90% 是改善「風控、執行、配置、估計穩健度」**，那是真價值（Kalman 動態 beta、GARCH vol-target、HRP、CVaR 都該補）。但**指望任何方法在純價量上製造 alpha 是幻覺**——session 已反覆證明。真正的 alpha 提升仍是 [docs/11](11-data-dimensions.md) 的**換資料維度**（修偏誤+延長歷史+多個低相關 IC 來源），方法只是把那些訊號榨得更乾淨。**先補資料，再用這些方法把訊號榨乾——順序不能反。**

---
*工具：`src/trading_analysis/models/kalman.py`、`scripts/kalman_demo.py`、`tests/unit/test_kalman.py`。接續 docs/00 §E、docs/11。2026-06-17。*
