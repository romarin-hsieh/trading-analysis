# 策略/機制總註冊表 — 供持續回測與洞見發掘

> /goal(2026-07-07):整理所有嘗試過的策略與機制、fabric 判定、可重跑工具,並規劃情境化短中長期策略。
> 判定標準見 [docs/17 fabric 規格](17-fabric-acceptance.md)。新機制詳測見 `docs/tests/TR-*.md`。
> **判定效力範圍=被測座位×棲地**:每個機制的原生棲地/錯置風險/翻案條件見 [docs/19 機制分類學](19-mechanism-taxonomy.md);試驗數會計見 [trial-registry](trial-registry.md)。

## 1. Fabric 判定總表(全部機制,依判定分組)

### ✅ PASSED(達成原始宣稱且過 F5/F6/F7)
| 機制 | 判定重點 | 證據 | 可重跑 |
|---|---|---|---|
| 多 sleeve 風險平價組合 | 唯一顯著 alpha(Carhart t=2.64);2025 OOS +27.9%/MDD −5.7%。**v1.2 改標 PASSED(borderline):t=2.64 < HLZ t≥3.0,僅在有效試驗數 ≲10 時存活**(docs/17 §5 A1) | docs/08 | `scripts/validate_recommendation.py` |
| gross_profitability 品質因子 | ICIR +0.30 跨期同號、regime-universal(bear 最強) | docs/10 | `scripts/fundamental_factors.py` |
| Ensemble 投票混合(E1) | holdout Sharpe 0.99 vs B&H 0.84、MDD 減半;混合>選一(0.99 vs 0.63) | docs/15 §3 | `scripts/ensemble_mix.py` |
| 回撤預算/雙向槓桿刻度 | L≥1.5 支配 VOO(終值∧Calmar);風險塑形如設計兌現 OOS | docs/13 §9C/9E | `scripts/defensive_overlay.py` |
| 嚴謹驗證機制本身 | DSR/PBO/SPA/placebo/零訊號控制:抓 30+ 真幻覺 | docs/05-17 全域 | O1 模組+workflow 慣例 |

### 🟡 PARTIAL(如設計運作,無 alpha;風控/工程價值)
| 機制 | 判定重點 | 證據 | 可重跑 |
|---|---|---|---|
| 波動目標(vol-target) | 降 MDD 如宣稱;高波動宇宙反而傷(§12 R2) | docs/13 §12、zoo | `scripts/strategy_zoo.py` |
| 防禦 TAA(Antonacci/Faber) | 回撤保險真(GFC +3.6%),Sharpe 增強假(全週期 ≤60/40) | docs/13 §8 | `scripts/taa_long_history.py` |
| 五維出場投票(VIX+倉位+乖離+RSI+MACD) | 預警紀律工具;≥3/5 未勝最佳單維;槓桿標的才值錢 | docs/15 §4 | `scripts/multi_exit.py`+Telegram bot |
| 三重濾網 AND(趨勢∧動量∧量能) | 低 MDD 取向合理(holdout 0.94/−14%) | docs/15 §3 | `scripts/ensemble_mix.py` |
| Kalman 濾波(趨勢/動態 beta) | 轉折早 10-25 天真;當 gate whipsaw;動態 beta 是真用途 | docs/12 | `src/.../models/kalman.py` |
| Minervini/USIC Trend Template | 結構檢查有效;alpha 衰退(Sharpe 1.17→0.64)、無顯著 α | docs/05/07 | `strategy/rules/minervini_trend.py` |
| Vegas 雙通道 | Sharpe 1.00=趨勢濾網外衣(≈SMA200);TR-11 隨機視窗 P(beat)=44%(F9 PARTIAL) | docs/15 §2、TR-11 | `scripts/strategy_zoo.py` |
| IBS 均值回歸 | zoo TS 最佳(1.03/−16%);**TR-11 隨機視窗 P(beat)=66% = 唯一 robust-PASS 的 TS 規則**(F9) | docs/15 §2、TR-11 | `scripts/tests/tr11_bagged_backtest.py` |
| 高波動「減法」規則 | 拿掉日停損+現金擇時:Sharpe 0.48→0.9;贏 B&H 不顯著(t=1.74) | docs/13 §12 | `scripts/highvol_ruleset.py` |
| Serenity 追蹤(情報源) | 宇宙情報真(placebo +18.7%/季);擇時無 edge | docs/16 | `scripts/notify/serenity_tracker.py` |
| LLM agent 框架(驗證者用法) | 對抗驗證抓 30+ 真錯;alpha 來源 FAILED | TR-10 | workflow 慣例 |

### ❌ FAILED(未達成宣稱)
| 機制 | 失敗模式 | 證據 |
|---|---|---|
| 廣市場動量/價值/低波動因子 | 動量死(ICIR≈0)、價值失落十年、低波動=t 灌水假象 | docs/09、倖存者修正 |
| PEAD-SUE、insider、7 個本業營運因子 | 無漂移/不穩/全 WEAK;無一超越 GP | docs/10、13 §10 |
| regime-rotation、gate 到現金、regime-switch 選股 | in-sample 雜訊(13 agent 證偽);擇時減損鐵律 | docs/09/10 |
| Kalman pairs 統計套利 | 真市場中性(corr+0.01)但賠錢;套利殆盡 | docs/13 §5 |
| 季節性(TOM/隔夜) | 衰退/成本牆(隔夜毛 0.89→淨 −0.97) | docs/13 §4、15 |
| 帶狀突破(Keltner/Bollinger breakout) | 日線 whipsaw 稅吃光(Sharpe 0.25) | docs/15 §2 |
| **XS 動量 top-K「選股增量」**(F9 複測降級) | 隨機 3 年窗 P(beat EW-47)=23%、隨機子集 30%——點估計榜首是路徑錨定假象;動量=beta | TR-11 |
| 手挑清單回測、事後宇宙 | 純選股偏誤(+62.8% 幻覺) | docs/13 §11 |
| 50-100% CAGR 低風險、2×VOO 每年、Sharpe>2 持續 | 數學不可達(Calmar 牆/前沿證明) | docs/07/14 |
| **3×VOO 每年∧虧損不超過 VOO(本輪 goal 目標)** | **最佳 4/10 年(12-1 季動量);無策略 10/10**;需持續 Calmar~3+,此資料不存在 | `scripts/gate_3x_voo.py` |

### 🧪 本輪新測(TR-01~08,fabric 工作流;詳見 docs/tests/)
| TR | 機制 | 判定 | 摘要(稽核員重跑全部 8 支腳本,數字一對一吻合) |
|---|---|---|---|
| TR-01 | 共整合 pairs 統計套利 | **FAILED** | OOS +2.0%/yr < 現金(BIL +2.7%);GGR 2006 的 +11% 衰退 >100%;9/10 對集中 AI 半導體、SMCI 醜聞炸出 −29.7% MDD;殘值=|z|>4 當單一股異常警報 |
| TR-02 | Markov 變異變遷 regime | **PARTIAL** | regime 辨識真(低/高波動 16.9% vs 31.2%)、shuffle null 97-98 pctile;**當現金 gate 輸 B&H**(0.84 vs 0.90)=鐵律在最有理論根據的濾波器上再證;MDD 減半;正確用法=波動預測器/連續縮放 |
| TR-03 | PCA 統計因子模型 | **PARTIAL** | 5 PC 解釋 65%(PC1 41.8%=一個大 beta);因子共變異 min-var ≈ LW、勝 sample-cov 0.66 vol pt;無 alpha,估計工程價值 |
| TR-04 | VaR 測量+目標化 | **PARTIAL** | 常態 VaR 99% 違規率 2.9% vs 名目 1%(Kupiec p<1e-14)=RiskMetrics 常態假設全滅;歷史/CF 較誠實;VaR-target ≈ vol-target |
| TR-05 | GBM Monte Carlo | **FAILED**(作為股票風險模型) | 實現最慘日 −12% = GBM 下 −11.8σ(機率 1e-32);GBM 對尾部/MDD 低估數量級;**block bootstrap 才是誠實的 MC**(P(MDD≤實現)=8.1% vs GBM 誇張樂觀) |
| TR-06 | CAPM | **PARTIAL** | 本宇宙 SML **反轉陡升**(FM 斜率 +1.9%/mo t=2.69,高 beta 大勝)=BAB 在 AI 牛市反向(低−高 Sharpe −0.79);截距 −1.02%/mo 違反 CAPM;歸因工具價值保留 |
| TR-07 | HRP 階層風險平價 | **PARTIAL** | 決策相關結論:**我們的 log-barrier risk-parity 勝 HRP**(sleeves 上 1.44 vs 1.04,HRP 過配債券 70%);LdP 的 −31% 變異數優勢縮到 −8%;不換 |
| TR-08 | ML 混合預測(GBM) | **FAILED** | OOS IC −0.0013、R² −4.8%;Sharpe 0.91 ≈ shuffled 控制 0.88、輸笨動量 1.16 與 EW 1.09;GKX 效應在此宇宙完全衰退;判定校準被稽核員點名為模範 |
| TR-09 | Black-Scholes | **N/A** | 無 PIT 選擇權資料(預算);假設層由 TR-05 代測 |
| TR-10 | LLM agent 框架 | **PARTIAL/FAILED** | 驗證者用法有效;alpha 來源無效 |
| TR-12 | 再平衡相位平均(F12 首行)+2×成本壓力 | **方法 PASSED;3 修正生效** | 季動量 timing-luck 帶寬 **1,753bps/yr**(單相位數字自此不足採信)、月動量 746bps(2×成本下只 38% 相位贏 EW);**旗艦 combo 相位免疫(30bps)無需修改**;相位-0 其實偏倒楣(10-14 pctile)=無 cherry-pick 但單相位不可靠,判定改引 tranche(+1.21);實盤動量應 K=4 分批 |
| TR-11 | RF 理論 bagged 回測(F9 首行)+ RF 預測器 | **方法 PASSED / 預測器 FAILED** | 300 隨機 3 年窗:**XS 動量 P(beat EW)=23% 降級 FAILED、IBS 66% 升級 robust-PASS**、Vegas 44% 降級;RF 預測 IC −0.013、shuffle 控制反而 +0.011;複測改寫 2 個舊判定=F10 存在證明 |

## 2. 目標閘門實測(本輪 goal:每年 ≥3×VOO ∧ 虧損年不劣於 VOO)

`scripts/gate_3x_voo.py`(2016-2025):**QQQ 1/10、年度等權 2/10、月動量 3/10、季動量 4/10(最佳)、combo 2/10、combo 2× 1/10。無策略全過。** 對照:2×VOO 閘門最佳 7/10 且是 beta+curation(docs/14)。10/10 需持續 Calmar≈3+——docs/07 已證可投資前沿 ~0.7。**結論:此目標在此資料維度上不可達;可達的是「風險調整支配 VOO」(L≥1.5 槓桿 combo)與「防守年不劣於 VOO」(combo 在 2018/2022 皆過)。**

## 3. 情境化策略規劃(短/中/長;接 docs/14 §6 rulebook)

| 情境 | 尺度 | 推薦 | 進出場/停損 |
|---|---|---|---|
| 資料只有日線+免費(現況) | 短 1-4 週 | **不做**(成本牆+資料頻率) | — |
| 〃 | 中 1-12 月 | 產業動量 top-K(認知=beta+)或 E1 票池曝險 | 月度 rank-out;❌日停損❌現金擇時;高波動 K≥20 |
| 〃 | 長 1-3 年+ | 年度等權 47 或 combo+L 刻度 | 組合層回撤預算(L 選 MDD);月度結構切 |
| 進攻(接受 −38% MDD) | 長 | combo 槓桿 2×(支配 VOO) | 同上+槓桿融資紀律 |
| 防守(2008 恐懼) | 長 | combo L=0.4-0.6(MDD −7~−11%) | 同上 |
| 高波動主題股(Serenity 宇宙) | 中 | 減法規則:動量+分散+無停損+無擇時 | 126 日低結構切;單檔 ≤5% |

## 4. 持續回測迴圈(供未來洞見)

1. **新想法 → docs/17 fabric**:先寫 TR 模板的 §1-§4(定義/親屬/預期/設計),再寫程式。
2. **執行**:`scripts/tests/tr_XX.py` 慣例;圖出 `docs/tests/img/`;≥3000 樣本、跨 ≥5 年。
3. **判定進本表**:PASSED/PARTIAL/FAILED 各節;FAILED 也入表(負結果防重複踩坑)。
4. **年度儀式**:每年初重跑 `oos_2025.py` 型年檢+`gate_3x_voo.py`+`trades_2025.py`(出手審計)。
5. **洞見觸發器**:任何 PASSED 出現 → 觸發對抗 workflow 驗證;連續兩個同族 FAILED → 該族封頂,資源轉向資料維度。

---
*接續 docs/17(fabric 規格)、docs/14(六槽位)、docs/15(100+ 目錄)。2026-07-07。*
