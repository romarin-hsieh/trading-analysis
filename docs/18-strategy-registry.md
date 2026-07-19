# 策略/機制總註冊表 — 供持續回測與洞見發掘

> /goal(2026-07-07):整理所有嘗試過的策略與機制、fabric 判定、可重跑工具,並規劃情境化短中長期策略。
> 判定標準見 [docs/17 fabric 規格](17-fabric-acceptance.md)。新機制詳測見 `docs/tests/TR-*.md`。
> **判定效力範圍=被測座位×棲地**:每個機制的原生棲地/錯置風險/翻案條件見 [docs/19 機制分類學](19-mechanism-taxonomy.md);試驗數會計見 [trial-registry](trial-registry.md)。

## 1. Fabric 判定總表(全部機制,依判定分組)

### ✅ PASSED(達成原始宣稱且過 F5/F6/F7)
| 機制 | 判定重點 | 證據 | 可重跑 |
|---|---|---|---|
| 多 sleeve 風險平價組合(**HLZ 門檻:PASSED-borderline**) | 唯一穩健為正的 alpha(bootstrap P(α≤0)=0.001);2025 OOS +27.9%/MDD −5.7%、Sharpe~1.2、MDD≈VOO 半。**⚠️ TR-18 修正(F10 級聯):TR-15 的「t=3.38 過 HLZ」是日頻假象**——日頻低估 book 真實市場 beta(Dimson lagged-beta:0.22 日頻 vs 0.35 月頻)把因子報酬誤記為 alpha;在頻率對應的**月頻**(同時吻合月度再平衡與 HLZ 校準頻率)**Carhart t=2.64(OLS)/2.95(HAC)兩者 <3.0 → 不過 HLZ 3.0**,退回 docs/08 原始讀數 t=2.64。**由 PASSED 降為 PASSED-borderline**(仍是唯一存活的風險塑形交付,只是不過嚴格 HLZ);2× 成本 t=3.14 亦為日頻,同受此修正。**TR-20 強化**:月頻 alpha 對 FF5(+RMW+CMA)/FF6 穩健(alpha-t 2.63-2.88 跨 5 模型、RMW/CMA 不顯著)=真殘值 alpha,非未建模因子 beta。**TR-25 高原確認:權重 ±20-25%(210 變體)、週/月/季頻率、1000 條拔靴路徑下交付全部成立(99.8% 路徑回撤淺於 VOO);同時確認整個高原 t<3.0=邊際是結構性的**。**TR-33 疊加終審:加 GP sleeve 增量 alpha 為負(−1.19%/yr,t=−1.91),維持 5-sleeve**。**TR-35 機制 50 年回放:保護不對稱——股災回撤 0.07-0.16 倍(52 年 MDD 0.29 倍),利率主導窗零保護(1976-81/1994 ratio≈1);交付範圍條件=「股災回撤砍半;利率 regime 同淺無超額保護」,58% 債券腿為裸露面**。**TR-37 選擇誠實:DSR@N*=17=0.87/悲觀 226=0.56、懷疑先驗後驗≈0.8=大概率真但無角度能稱確定**。**TR-38 狀態成本:時間加權增量 +73bps/yr→state-cost t=2.35(HAC 2.55)仍過 2.0** | docs/08、TR-15、**TR-18/20/25** | `tr18_inference_robustness.py`、`tr20_ff5_attribution.py`、`tr25_robustness_grid.py` |
| gross_profitability 品質因子 | ICIR +0.30 跨期同號、regime-universal(bear 最強);TR-24B(年頻)+TR-28(季頻 HXZ 建構)確認 **subsumes ROE at both clocks**。**TR-26 深度確認(ROBUST-PLATEAU):持有期單調(ICIR 21d 0.10→252d 0.41=慢因子)、98% 半宇宙為正、毛多空僅 ~1%/yr=訊號非獨立策略**。**⚠️ TR-27 降級註記:遮罩到當日實際成員後 ICIR 只剩 +0.13(保留 59%)=入選前視灌高;誠實鏈 docs/10 +0.30→TR-26 +0.23→成員限定 +0.13**。**⚠️ WATCH:IC 2025-26 轉負——TR-26 量化:滾動 −0.050 vs 歷史最深 −0.109(2022,一年內復原)**;2026 全年仍負則啟動 F10 複測。**TR-33 組合層級終審(NO-STACK):成員限定頂/底五分位皆輸等權中段,頂−底 +0.04%/yr≈$0;GP=資訊(避開爛 GP 的濾網)非可入帳 sleeve**。**TR-34 FM 年代拆分把 WATCH 量化:2015-2020 獨立定價 t=+2.67、2021-2026 歸零 t=−0.85——F10 複測以 TR-34 C4 為基準面板** | docs/10、TR-24、**TR-26** | `scripts/fundamental_factors.py`、`tr26_gp_depth_grid.py` |
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
| 高波動「減法」規則 | 拿掉日停損+現金擇時:Sharpe 0.48→0.9;贏 B&H 不顯著(t=1.74) | docs/13 §12 | `scripts/highvol_ruleset.py` |
| Serenity 追蹤(情報源) | 宇宙情報真(placebo +18.7%/季);擇時無 edge | docs/16 | `scripts/notify/serenity_tracker.py` |
| LLM agent 框架(驗證者用法) | 對抗驗證抓 30+ 真錯;alpha 來源 FAILED | TR-10 | workflow 慣例 |

### ❌ FAILED(未達成宣稱)
| 機制 | 失敗模式 | 證據 |
|---|---|---|
| 廣市場動量/價值/低波動因子 | 動量死(ICIR≈0)、價值失落十年、低波動=t 灌水假象 | docs/09、倖存者修正 |
| **IVOL/MAX/52wH/BAB 四經典異象(TR-23,wave-1 批次)** | 463 檔座位全數未過閘門:IVOL −0.02、MAX +0.06、52wH −0.04(6/12月期限也 ~0)全 FAIL;BAB raw 反向 −0.14 但 **EIV-clean alpha-level ≈0**(反向=beta×牛市機械補償,非 FP 反證);校準列獨立重現 docs/09(mom≈0、-vol −0.13);n=95 CI 蓋 ±0.20=「偵測不到」非「證偽」;**GP 品質(+0.30)仍是唯一倖存橫斷面訊號**;翻案=小型股/國際宇宙+熊市長史。**T1 回掃(2026-07-18):MAX 實為 MAX(5) 變體、BAB 為 FP-lite 訊號層(504d corr、無收縮/秩權重/槓桿至 β=1;FP 組合宣稱未測,由 TR-06 SML 反轉獨立封死)、評估 EW rank-IC 非 VW 組合——皆註記,無判定翻轉** | TR-23、[T1 回掃](tests/T1-audit-sweep-202607.md) |
| PEAD-SUE、insider、7 個本業營運因子 | 無漂移/不穩/全 WEAK;無一超越 GP | docs/10、13 §10 |
| regime-rotation、gate 到現金、regime-switch 選股 | in-sample 雜訊(13 agent 證偽);擇時減損鐵律 | docs/09/10 |
| Kalman pairs 統計套利 | 真市場中性(corr+0.01)但賠錢;套利殆盡 | docs/13 §5 |
| 季節性(TOM/隔夜) | 衰退/成本牆(隔夜毛 0.89→淨 −0.97) | docs/13 §4、15 |
| 帶狀突破(Keltner/Bollinger breakout) | 日線 whipsaw 稅吃光(Sharpe 0.25) | docs/15 §2 |
| **IBS 均值回歸**(TR-16 完整審判後**反轉 FAILED**) | TR-11 的 robust-PASS 建立在「2015-26 窗×same-close 成交×無靜態控制」三重偏惠;**next-close 誠實成交 exSR +0.44 < B&H +0.45 ≈ 靜態 38% 曝險 +0.45**;gap 只在 1999-2007 為正(Connors 時代衰退);殘值=進場擇日器(贏隨機 p95) | TR-16 |
| **XS 動量 top-K「選股增量」**(F9 複測降級) | 隨機 3 年窗 P(beat EW-47)=23%、隨機子集 30%——點估計榜首是路徑錨定假象;動量=beta | TR-11 |
| 手挑清單回測、事後宇宙 | 純選股偏誤(+62.8% 幻覺) | docs/13 §11 |
| 50-100% CAGR 低風險、2×VOO 每年、Sharpe>2 持續 | 數學不可達(Calmar 牆/前沿證明) | docs/07/14 |
| **3×VOO 每年∧虧損不超過 VOO(本輪 goal 目標)** | **最佳 4/10 年(12-1 季動量);無策略 10/10**;需持續 Calmar~3+,此資料不存在 | `scripts/gate_3x_voo.py` |
| **吸收比率(KLPR 2010)診斷+閘門** | TR-21(reel→主要來源→一天判定):465 檔個股座位上**不領先大跌**(PIT 百分位 62,p=0.40;忠實尖峰版 4/10 vs 基準率 39%)、與平均相關 +0.97 同物、閘門(含忠實三態)輸靜態 69% 與隨機安慰劑——**擇時鐵律第三案例**;經雙向對抗稽核(反 AR 偏誤已修、美化閘門已修,FAIL 更穩)。**TR-21b 原生座位重測(KF49 產業,1970-2026):水位宣稱反轉(中位 37)、dAR>1 尖峰弱複製(7/10 vs 33%,suggestive)、閘門第 5 次死亡(0.28 vs 0.46)**——診斷半條命回來(棲地特異),擇時結論不變 | TR-21/21b、docs/23 |

### 🧪 標準化測試報告 TR-01~39 + 03b/04b/17b/21b/30b/39b(詳見 docs/tests/;**docs/20 論文佇列全清**;TR-01~08 由稽核員重跑全部腳本、數字一對一吻合)
| TR | 機制 | 判定 | 摘要 |
|---|---|---|---|
| TR-01 | 共整合 pairs 統計套利 | **FAILED** | OOS +2.0%/yr < 現金(BIL +2.7%);文獻錨(GGR 2006 距離法 +11%)為脈絡非重現對象——本 TR 測 EG 共整合建構(T1 回掃 2026-07-18 註記:來源-機器錯配已修語言;兩套獨立建構 EG+docs/13 Kalman 同座位皆虧+Do-Faff 已載距離法衰退);9/10 對集中 AI 半導體、SMCI 醜聞炸出 −29.7% MDD;殘值=|z|>4 當單一股異常警報 |
| TR-02 | Markov 變異變遷 regime | **PARTIAL(v1.2 收窄:波動辨識 only)** | regime 辨識真(16.9%/31.2%)、gate 輸 B&H;**TR-02b Cederburg 控制:靜態 57% 恆定曝險同 MDD(−20.7 vs −20.1)、更高 exSharpe(0.79 vs 0.62)、零交易——「MDD 減半」用常數就能複製**,regime 模型對曝險決策零增值 |
| TR-03 | PCA 統計因子模型 | **PARTIAL** | 5 PC 解釋 65%(PC1 41.8%=一個大 beta);因子共變異 min-var ≈ LW、勝 sample-cov 0.66 vol pt;無 alpha,估計工程價值 |
| TR-04 | VaR 測量+目標化 | **PARTIAL** | 常態 VaR 99% 違規率 2.9% vs 名目 1%(Kupiec p<1e-14)=RiskMetrics 常態假設全滅;歷史/CF 較誠實;VaR-target ≈ vol-target |
| TR-05 | GBM Monte Carlo | **FAILED**(作為股票風險模型) | 實現最慘日 −12% = GBM 下 −11.8σ(機率 1e-32);GBM 對尾部/MDD 低估數量級;**block bootstrap 才是誠實的 MC**(P(MDD≤實現)=8.1% vs GBM 誇張樂觀) |
| TR-06 | CAPM | **PARTIAL** | 本宇宙 SML **反轉陡升**(FM 斜率 +1.9%/mo t=2.69,高 beta 大勝)=BAB 在 AI 牛市反向(低−高 Sharpe −0.79);截距 −1.02%/mo 違反 CAPM;歸因工具價值保留 |
| TR-07 | HRP 階層風險平價 | **PARTIAL** | 決策相關結論:**我們的 log-barrier risk-parity 勝 HRP**(sleeves 上 1.44 vs 1.04,HRP 過配債券 70%);LdP 的 −31% 變異數優勢縮到 −8%;不換 |
| TR-08 | ML 混合預測(GBM) | **FAILED** | OOS IC −0.0013、R² −4.8%;Sharpe 0.91 ≈ shuffled 控制 0.88、輸笨動量 1.16 與 EW 1.09;GKX 效應在此宇宙完全衰退;判定校準被稽核員點名為模範 |
| TR-09 | Black-Scholes | **N/A** | 無 PIT 選擇權資料(預算);假設層由 TR-05 代測 |
| TR-10 | LLM agent 框架 | **PARTIAL/FAILED** | 驗證者用法有效;alpha 來源無效 |
| TR-11 | RF 理論 bagged 回測(F9 首行)+ RF 預測器 | **方法 PASSED / 預測器 FAILED** | 300 隨機 3 年窗:**XS 動量 P(beat EW)=23% 降級 FAILED、IBS 66% 升級 robust-PASS**、Vegas 44% 降級;RF 預測 IC −0.013、shuffle 控制反而 +0.011;複測改寫 2 個舊判定=F10 存在證明 |
| TR-12 | 再平衡相位平均(F12 首行)+2×成本壓力 | **方法 PASSED;3 修正生效** | 季動量 timing-luck 帶寬 **1,753bps/yr**(單相位數字自此不足採信)、月動量 746bps(2×成本下只 38% 相位贏 EW);**旗艦 combo 相位免疫(30bps)無需修改**;相位-0 其實偏倒楣(10-14 pctile)=無 cherry-pick 但單相位不可靠,判定改引 tranche(+1.21);實盤動量應 K=4 分批 |
| TR-13 | 下市終端報酬(Shumway,B10 首行) | **方法 PASSED;區間化完成** | 9 個窗內下市**全為併購型**(注 −30% 幾乎不動 +1.26→+1.31%);151 個被清除名的合成上界 → **倖存者膨脹誠實區間 [+1.26%, +2.02%]/yr**;凡引 610 union 絕對數字自此標注區間 |
| TR-14 | 有效樣本 n_eff(F4 v2 首行) | **方法 PASSED** | TR-02 的 F4 改判 FAIL(n_eff 2,206<3,000);面板類 PASS(7.5k/7.7k);**zoo 59 變體有效試驗數僅 1.8(ρ=0.54)**=同一場趨勢賭注 |
| TR-15 | 旗艦全成本+2× 壓力(F2 v2) | **旗艦升級 PASSED** | 補收 TQQQ 翻轉+RP 再平衡成本後 **t=3.38 ≥ HLZ 3.0、2× 壓力 t=3.14**;成本拖累僅 12-72bps;順手修復 FF loader 上游格式 break(attribution 全面恢復) |
| TR-16 | IBS 完整審判(B1 成交敏感度首行) | **FAILED(反轉 TR-11)** | same-close +0.63 → **next-close +0.44 < B&H +0.45 = 靜態控制 +0.45**;四檔指數一致;gap 僅 1999-2007 為正;F9 全歷史 37%;**技術規則章節全數關閉**;B1 敏感度成為快速規則強制關卡 |
| TR-17 | KMZ 複雜度的美德(RFF+ridge 擇時)+ Nagel 控制 | **PARTIAL** | VoC 曲線在本座位嘈雜微弱(SPY P=12k +0.15>P=12 −0.01;QQQ 反而 P=12 最佳);**Nagel 控制決定性獲勝:1/σ² 波動管理 +0.67 支配全部 18 個複雜度變體**(alpha-t 0.48);淨成本+截倉 +0.37<B&H +0.61;不推翻 KMZ 定理(95年×總經預測子的原生棲地不可及),ML FAILED 判定維持;翻案條件=ingest Goyal-Welch 資料集(**已執行:TR-17b**) |
| TR-17b | KMZ 原生座位重開(GW 15 預測子 1929-2024;docs/24 行動 #1) | **REPLICATED-BUT-EXPLAINED** | 第一次運行 NO-VoC-SHAPE 被稽核判為**建構假陰性**(TR-17 的 12 月視窗內 z-score 使 RFF 核退化為單位矩陣);KMZ 忠實建構(擴張窗標準化、γ=2 sin/cos、z·T 原始 K ridge、波動標準化目標、多 seed)後 **R1 ✓:VoC 曲線每個 z 單調上升,P=12k 達 +0.33~+0.41(對上發表值 0.47)**;**R2 ✗:SR +0.42 < 1/svar MM +0.50 = vol-std 市場 +0.50;對 vol-std 市場 alpha-t +2.41(呼應發表 2.6-2.9)但加 Nagel VTM 對照塌到 +0.89(部位相關 +0.49)**=12k 特徵學到的≈波動擇時+波動加權動能;**Nagel 批評在源頭確認,ML 章節維持關閉**;擇時鐵律案例 #4 |
| TR-18 | 旗艦 alpha 推論穩健性(Newey-West + Politis-Romano;讀計畫 wave-1) | **PARTIAL(旗艦降級 F10)** | **旗艦 t=3.38 是日頻假象**:日頻 HAC(含 lag63)與拔靴皆過 3.0,但**月頻(頻率對應)Carhart t=2.64 OLS/2.95 HAC 兩者 <3.0**;Dimson lagged-beta(0.22 日 vs 0.35 月)使日頻誤記因子報酬為 alpha;alpha 仍穩健為正(P(α≤0)=0.001)但不過嚴格 HLZ,退回 docs/08 t=2.64。**同時捕捉自身流程失誤**(原腳本偷偷加未預先承諾的 ≥2.5 keep-PASSED 分層被稽核員抓出、已移除、照 F0 三分規則判 PARTIAL) |
| TR-20 | 旗艦 alpha vs 更嚴因子模型(FF5 +RMW +CMA、FF6;讀計畫 wave-1) | **ROBUST(旗艦不變、強化)** | 加 RMW(獲利)+CMA(投資)後月頻 alpha 幾乎不動(Carhart-4 5.90%→FF6 6.02%,alpha-t 2.63→2.69);RMW/CMA beta 皆小且不顯著(\|t\|≈1)=book 無獲利/投資傾斜、無可吸收;**旗艦邊際 alpha 是真殘值,非未建模因子 beta**。alpha-t 跨 5 模型穩定 2.63-2.88、持續 <HLZ 3.0(與 TR-18 一致)。q-factor(HXZ ROE+I/A,需 EDGAR 自建)仍佇列 |
| TR-21 | 吸收比率(KLPR 2010;creator-reel 線索→主要來源) | **FAILED(本座位)** | C1 診斷(PIT 百分位 62,p=0.40)與 C1b 忠實尖峰版(4/10 vs 39% 基準)皆 FAIL;C2:與平均相關 +0.97 同物;C3 閘門(含忠實三態)輸靜態 69%(0.40 vs 0.65)與隨機安慰劑 p95;**雙向對抗稽核**修正反 AR 偏誤(全樣本→PIT 排名 44→62)與美化閘門(單門檻→三態,FAIL 更穩)、51 組合維度檢查不改結論;翻案=真 GICS 產業面板+含 2008 長史(**已執行:TR-21b**) |
| TR-21b | AR 原生座位重開(KF 49 產業日頻 1970-2026;docs/24 行動 #2) | **閘門 FAILED / 診斷 WEAK-PARTIAL(稽核分裂判定)** | **水位宣稱反轉**:最差 10 月前月 AR PIT 百分位中位僅 **37**(p=0.75)——「高 AR=脆弱」在自家棲地不成立;**KLPR 招牌 dAR>1 尖峰弱複製:7/10 vs 基準 33%**(iid p=0.020、群聚公平 null p=0.034,僅 K=10 過檻;領先窗≈一季、3/7 含事中反應)且 **AR-特異**(波動安慰劑 3/10、平均相關 5/10);**C3 閘門第 5 次死亡:exSR 0.28 vs 靜態 0.46,躲過 4.5/10 最差月仍排猴子閘門第 7 百分位**=至今最乾淨「診斷真、擇時死」;F0 樹漏 C1b 分支的「does not replicate at home」屬錯殺,依稽核以分裂判定登錄(F0 未回改);AR 至多入 E1 儀表板候選,永不作閘門 |
| TR-23 | 四經典價量異象批次(AHXZ IVOL/BCW MAX/GH 52wH/FP BAB;讀計畫 wave-1) | **全數 FAIL/FLAT** | 因子閘門(fwd 21d rank-IC、n=95 月):IVOL −0.02/MAX +0.06/52wH −0.04 FAIL、BAB raw −0.14 反向但 **alpha-level(EIV-clean disjoint-beta 對沖)≈0**;稽核零 CONFIRMED-BUG(本系列首見);校準列重現 docs/09;**「唯一倖存=GP」強化**;同輪 `factor_alpha_monthly()` 入庫(TR-18 接線) |
| TR-24 | q-factor 雙重檢驗(HXZ 已發布因子 + EDGAR 年度 ROE;讀計畫 wave-1) | **A:ROBUST-in-magnitude(TR-20 獨立確認)/ B:GP subsumes ROE** | A:同窗(n=114)q5 alpha +4.13% vs Carhart +4.20%=**縮水僅 +2%**(初版「30%」是混窗 CONFIRMED-BUG,稽核修正);IA beta −0.32(t−3.8)真(TQQQ/防禦的高投資成長曝險)但沒吃掉 alpha;t 1.77=截斷窗 power 非吸收(HAC 2.21>同窗 Carhart 2.17)。B:年度 ROE WEAK(+0.11)、GP 正交增量 −0.10 翻號=**GP subsumes**(Novy-Marx 論點);季頻 ROE 留翻案。**WATCH:GP 的 IC 2025-26 轉負(−0.05)**——若 2026 全年仍負啟動 F10 複測 |
| TR-19 | LPS 隔夜/日內拆解(診斷型;讀計畫 wave-1) | **診斷完成(無閘門)** | book 報酬 **85-90% 住隔夜**(動量 top-10 隔夜 +31.7%/yr vs 日內 +7.3%;宇宙層現象:SPY 63%/EW-47 72%);**稽核歸因修正:隔夜超額 +11.4%/yr 被無動量的 vol top-10 對照複製(+11.2%)=主詞是 vol/beta 傾斜,非動量選股(與 TR-11 一致)**;2023-26 日內轉正=非「LPS 未衰退」;交付=F1 成交慣例一階性確認+成本牆仍立;21 相位全正(F12) |
| TR-22 | 旗艦 combo 家族 CSCV/PBO(F5 缺口) | **CREDIBLE(24.5%)/配置器非 edge** | F0 家族(12 configs)PBO=24.5%<30%;**分層**:剔 min-variance 稻草人 41.8%、決賽圈 RP/IV/EW 對 IV 慣例敏感(27%→89%);修兩個 CONFIRMED-BUG(inverse_vol 零波動 fillna 假象值 0.12 Sharpe、稻草人組成);**操作結論:RP/IV/EW-of-sleeves 近乎可互換(DGU),不再報第一名 config;alpha 家族無關**(EW-5s 也有 t=2.92 日頻) |
| TR-25 | 主力組合穩健度網格(深度系列首份:權重×頻率×路徑) | **ROBUST-PLATEAU** | 基準 exSharpe +1.12/月頻 alpha-t +2.69;**C1:210 個權重傾斜變體(±20-25%)100% alpha-t≥2.0、t∈[2.46,2.86]**;**C2:週/月/季再平衡 exSharpe 差距僅 0.02**;**C3:1000 條聯合拔靴路徑 99.8% 回撤淺於 VOO**,exSharpe 5-95% 帶 [+0.67,+1.58]。**雙面讀法:交付(回撤砍半)非挑選產物;但整個高原 t<3.0=「邊際」是結構性的,不是權重假象**。反 HARKing:變體=探針非候選,F5 試驗數+0;基準維持 RP 126/21 |
| TR-26 | GP 品質因子深度網格(深度系列 #2:持有期×建構×年度×宇宙) | **ROBUST-PLATEAU** | CAL 過(63d IC +0.025/ICIR +0.23,docs/10 頭條重現);**C1:ICIR 隨持有期單調上升 0.10→0.23→0.30→0.41(21→252d)=慢因子,實作應低換手**;C2:三種建構毛多空全正但僅 +0.66~+1.34%/yr(**訊號≠獨立策略,數字化 docs/10 定位**);C3:7/10 年為正(負:2016/2022/2025);C4:98% 半宇宙為正。**WATCH 基準率:目前滾動 IC −0.050,歷史最深 −0.109(2022-10)一年內回升 +0.072——現段深度約前例一半,唯一前例復原收場**;TR-24 升級規則(2026 全年負→F10)維持武裝(YTD −0.005) | 
| TR-27 | GP 成員資格前視×市值分層(深度系列 #3;PIT 成分面板首用) | **INCLUSION-LOOKAHEAD-SENSITIVE / 市值 PASS** | **C1 FAIL:遮罩到「當天真的在指數」後 IC +0.015/ICIR +0.13,只保留未遮罩值的 59%**(<70% 門檻)——現任成分面板把「高 GP 未來入選者贏過低 GP 現任者」的跨群排序(回測當下不可知)計入了因子能力;C2:PIT 市值大/小兩半皆正(+0.019/+0.010)。**不對稱推論:同面板的 TR-23 四 FAIL 因偏誤方向(灌高)反而更穩**;GP 完整翻案=含下市股 PIT 宇宙(Tiingo,已定價)。CAL v1 覆蓋率規則誤把真實汰換當對映錯誤,自抓修正(POST-RUN note) |
| TR-28 | 季頻 ROE(HXZ 建構;TR-24B 翻案項執行) | **SUBSUMED-CONFIRMED** | 10-Q YTD 差分還原單季 NI(25,031 季度事件、485 檔、PIT=較晚申報日;動工前抽查抓到「庫存值=YTD 累計」地雷);**C1 季頻單獨 ICIR +0.08(WEAK)、C2 GP 正交殘差 −0.07 轉負=GP 在年頻(TR-24B)與季頻(TR-28)兩種時鐘下都吸收 ROE**;「年報太舊」假說否決,Novy-Marx「毛利比淨利乾淨」二度確認;成員限定讀數 +0.08(無 TR-27 型折價,但本來就弱);q-factor ROE 腿對本面板關閉 |
| TR-29 | 持有期×換手率曲線(主力兩個動能 sleeve;深度系列) | **HOLD-PLATEAU** | CAL:hold=21 掃描格=主力 equity_mom 輸入(corr 1.0000);**equity_mom:hold=21 正是淨成本網格頂點(+0.84)**——5 天毛優勢被 143bps/年換手成本吃掉、63 天訊號衰減(+0.63);dual_mom:21 天 +0.92 vs 最大 +1.02(5/10 天),壓 0.10 容忍帶邊界過。與 TR-25 合計,主力組合全部自由參數(權重/頻率/路徑/持有期)都有高原證據;**「持有期是機制屬性非全域常數」**(動能半衰期<<GP 的季-年尺度,TR-26 對照);反 HARKing:dual_mom 較快格子不觸發配置變更 |
| TR-30 | Larry Williams 外包線反轉(YouTube 影片線索→主要文獻) | **FAILED(NO-EDGE)——⚠️ 機器忠實度失效,判定由 TR-30b 取代** | 外包線多頭(次日開盤成交,SPY/QQQ/IWM/DIA 1993-2026);R1 訊號日 +5d +0.40% vs 基準 +0.20% t=4.11(過);**R2 勝率陷阱只對一半:FPO 73%→對稱 59%,但期望值仍正**;**R3 決定性:只 1/4 標的贏隨機進場 p95=擇時對 beta 零增值**;影片自招「勝率高因止損寬 FPO 小」對一半,更深死因是漂移非不對稱。**擇時=beta 第 6 案**;創作者管線第 2 次產 TR(前例 TR-21)兩次皆 FAILED | 
| TR-30b | 外包線忠實引擎重測(**使用者稽核**觸發:TR-30 四處不忠實——2× 實體過濾漏實作/無止損/FPO 錯/安慰劑未共用引擎) | **NO-ENTRY-EDGE(同類判定,忠實機器)** | CAL v2 定位宣稱:勝率=止損緩衝的單調函數(0.2→3.0×ATR:35%→81%)=影片自招的賠付不對稱曲線;判定固定在最小達標緩衝 1.0×ATR(勝 65%):期望 +0.018%/筆(賠付比 0.56),**同引擎隨機進場 p95=+0.082%,外包線僅第 76 百分位=進場零增值**;SPY 樣本內尾段 1993-98 期望 −0.036%(更差);最佳格 0.9%/年無槓桿=冠軍報酬不可能來自此機制。制度化:創作者影片 T1(逐字稿規則表逐條映射)、未公布參數用 CAL-locate、安慰劑共用出場引擎 | 
| TR-31 | Campbell-Thompson 符號約束股權溢酬(GW 原生座位;docs/22 已付成本項) | **符號約束方向複製/經濟為零/波動擇時張成**(F0 樹嚴格=NO-OOS-RESCUE 邊界失敗) | CAL 過(未約束 R²_OS 中位 −0.40%=重現 GW);**C1 邊界失敗:符號約束 6/15 轉正(數量達標)但最佳 +0.48%<+0.50% 差 0.02%**;C2 經濟價值過(CT 擇時器 +0.52>B&H +0.44);**C3 決定性:CT +0.52 打平 vol-std 市場、輸 MM +0.53、alpha-t 1.99<2**。結論不靠 0.02% 門檻——即使救回的預測力轉擇時,仍贏不過波動三對照=**TR-17b 同款 Nagel 在源頭確認**;RFF 複雜度+符號約束線性兩條最強免費擇時路線同倒 | 
| TR-32 | Moskowitz-Grinblatt 產業動量(KF49 月頻,J=6/K=6 重疊、頭尾 15%) | **REPLICATED-BUT-SPANNED** | CAL 過(1970-95 月均 +0.516% vs 錨 +0.43%);全樣本 +0.543% t=3.50;**發表後僅衰退 2%(我們測過衰退最少的機制,McLean-Pontiff 平均 −58%)**;但 **FF5+UMD 張成後 alpha 全窗歸零(全 t=0.40/發表後 1.06/2015+ 1.34)+ M-G「不跳月更強」指紋反轉**=穿產業外衣的 UMD 曝險,無獨立 alpha;橫斷面拼圖補完:個股動能死→XS=beta→產業動量=UMD;唯一獨立倖存訊號仍是 GP | 
| TR-33 | 兩個倖存者疊加終審:主力組合 × GP 成員限定 sleeve | **NO-STACK** | CAL a 過(主力月頻 Carhart t=2.69 重現錨 2.64);CAL b v1 設計錯(「頂桶勝等權」非上游證據)→ v2 重現 TR-27 成員限定 ICIR +0.097 過帶;**黃金診斷:頂/底五分位皆輸等權中段(−3.56/−3.60%/yr),頂−底=+0.04%/yr≈$0=誠實鏈終點站**;C2 疊加價差 alpha −1.19%/yr(t=−1.91/HAC −2.05)=增量為負;C1 的 Sharpe 微升是風險平價稀釋非訊號;固定權重格 HAC t>3 屬描述性、alpha 增量為負不可提報;**主力維持 5-sleeve,GP=資訊非 sleeve** | 
| TR-34 | Fama-MacBeth 多變量特徵面板(方法補完;成員限定月頻 2015-2026) | **WEAK-INDEPENDENT(GP t=1.17)** | CAL a 過(GP 單變量 +16.9bps/mo、ICIR +0.097);CAL b v1 設計錯(進口他座位文獻符號:STR 必須為負)→ v2 錨自家 TR-06:**beta FM +161bps/mo t=2.51 重現 SML 反轉**;聯合面板:GP +30.7bps/mo t=1.17(控制後反而較乾淨)、**價值死(bm t=0.13)、反轉符號翻轉、beta=本年代唯一顯著定價特徵(t=2.39)**;**C4 年代拆分=WATCH 量化:GP 2015-2020 t=+2.67 顯著、2021-2026 t=−0.85 歸零**;`fm_slopes()` 留作可重用模組,新特徵宣稱一律先進面板;第三堂校準課:CAL 只能錨「相關座位實際量測過的統計量」 | 
| TR-35 | 主力機制 50 年回放(docs/25 A1;KF49/GEM/2×趨勢/倫敦金/DGS10 月頻類比 1975-2026) | **保護不對稱**(F0 嚴格=REGIME-CHILD,POST-RUN 三段式為準) | CAL 三腿全過(債 0.993/金同口徑 0.997/類比 vs 真實 0.72);**52 年:組合 MDD −14.6% vs 市場 −50.3%(0.29 倍)、CAGR 10.0% vs 12.8%**;**股災主導回撤 ratio 0.07-0.16(強保護)、利率主導窗(1976-81/1994)ratio≈1=零保護**;合併正相關 regime(52% 樣本)0.49;C3 證實預測:停滯性通膨扛家=金(+12.1%)非債(+3.6%);1973-74 四腿無金仍 −9% vs −46.5%(股災保護不靠金);交付語言更新=「股災回撤砍半;利率衝擊 regime 同淺無超額保護」;首輪 CAL 抓到月均 vs 月底 Working 對齊誤差(GS10→DGS10 EOM) | 
| TR-36 | 選擇權賣方溢酬指數層檢定(docs/25 突破口 #1/A5;CBOE PUT/BXM 免費官方史) | **NO-PREMIUM** | 首輪 CAL 抓到檔案陷阱(2007 前只有 7 個零星點→143 缺月→假 25% 波動),座位重宣告 2007-2026;CAL 過(vol 10.8%、beta 0.59、零缺月);**C1 決定性:CAPM alpha −0.25%/yr(t=−0.17)=股票 beta 之外零溢酬**;C3 量化本質:**下跌 beta 0.85 vs 上漲 beta 0.45**——「不錯的 Sharpe」全是 beta 補償(TR-30b 勝率 vs 期望值同款拆解);BXM/FF3+UMD 一致零;C2 共線殘差 +3.56%(t=2.34)僅好奇心非可收割;**B3 自建鏈 VRP 降為低優先,突破口遞補=台股棲地**;純 delta-對沖 VRP 留待(先驗已下修) | 
| TR-37 | 戰役層級 deflated alpha(docs/25 攻擊 1+7/A2;BLdP DSR+Harvey-Liu 後驗) | **FRAGILE-SURVIVES** | 試驗盤點先於計算:組合層級實際評估 N*=17(TR-22 的 12+品質傾斜 2+TAA 1+combo-2× 1+ensemble 1);**DSR 曲線:N*=17→0.87、悲觀全戰役 226→0.56**(alpha 流 IR 0.87,偏態/峰度已校正);懷疑先驗(90% null)後驗 P(α>0)≈0.77-0.81;Šidák N*=17 調整 p=0.129;首輪 BF 方向反置由「後驗≤偏袒上界」一致性檢查抓到並修;「邊界」完整語言=**大概率為真、無誠實角度能說成確定**;與 TR-22(PBO)/TR-25(高原)三刀分工 | 
| TR-38 | Corwin-Schultz 狀態相依成本(docs/25 攻擊 5/A3;$0 價差面板 from OHLC) | **NO-VERDICT-CHANGE(級聯執行後)** | 首輪 CAL-b 抓到漏掉 CS 2012 隔夜調整(危機月跳空→γ 爆炸→全地板 0,2020-03 讀 0bps);補上後 CAL 3/3(2020-03 尖峰 169bps=2019 的 ×6.9、排序、ETF 地板 12bps);股票宇宙中位 30bps/p90 179bps;**F0 樹按全壓力上界(+235bps)觸發級聯→級聯內執行:時間加權真實拖累 88bps/yr(增量 +73bps)→主力 alpha +6.04→+5.28%/yr、t 2.69→2.35(HAC 2.55)仍過 2.0**;平坦 5bps 對股票 sleeve 正式標記樂觀(誠實基準=中位 30bps);F2 升級:CS 面板為高換手 TR 標準選項;已 FAILED 高換手策略在狀態成本下死得更透(無翻轉) | 
| TR-39 | 台股棲地 FM 面板(docs/25 B4/突破口 #1;TWSE 1,151 檔日頻 2014-2026,F0 於滴灌 863/1220 時預先登記) | **SIGNAL-CANDIDATE×4(倖存者條件化)** | FinMind 面板一下午收齊(1,220 檔零失敗;token 倍速);CAL 三抓:close=0 毒 inf、切窗差一、**CAL-a v1 等權對比市值加權 TAIEX=蘋果橘子(v2 成交金額加權 0.942)**;**聯合 FM:mom122 +91bps t=2.67、max5 +105 t=2.11、avol +90 t=3.31(全場最強)、logdv −84 t=−2.28;bp +59 t=1.87 差一步**;符號=「延續市場」故事(散戶羊群延續,非美式樂透高估——MAX 符號與美國文獻相反);**2021-2026 更強(與美股衰退相反)=稀薄套利假說第一證據**;⚠️ 倖存者方向翻轉:預告的 MAX-負情境偏向零,實際 MAX-正=偏誤變向上灌水,四候選全暴露→**b 系列關卡:b1 TWSE 終止上市補丁(先於一切)→b2 成本 45bps RT→b3 桶經濟性** | 
| TR-39b | 台股去倖存補丁(b1 關卡;TWSE 官方終止名單 72 檔+官方日截斷;F0 於補丁判讀前登記) | **SPLIT:mom/avol/logdv 確認、max5 退役** | 三發現:(1) FinMind 宇宙其實含歷史條目(72 檔早已在庫);(2) 幽靈列真實(54/72 檔下市後仍有零星列=代號重用,官方日截斷);(3) **pandas pct_change 預設 ffill 把死尾巴變假 0% 報酬(3474:713 存活日生 2,420 零報酬日)→幽靈過濾器精準殺死股——回溯適用 TR-39 as-run,CAL-d 14/72 抓到**;修正後 66/72 入面板;**逐候選:mom122 +84bps t=2.44 確認、avol +94 t=3.39 確認(最強)、logdv −106 t=−2.77 確認、max5 2.11→1.64 倖存者假象退役(一半 ffill 修正、一半死股補丁;F0 方向分析叫中自己的靶)**;敘事修正=延續真、樂透溢價是倖存幻覺(更符 Barber 台灣證據);b2 成本關卡(45bps RT)next | 
| TR-03b | 共變異清理競技場(MP 譜+clipping+特徵向量端 BAHC;docs/20+23) | **clip≈LW 平手;BAHC PARTIAL;LW 慣例確認** | 463 檔 min-var 座位、判準=OOS 實現波動:LW 13.2-14.2%、clip 13.6-14.6%(**同族平手**,docs/20 預測獲支持)、BAHC 14.1-15.5%(贏 naive 沒贏 LW=特徵向量清理在 vol 通道無增值);**稽核抓幽靈資產 bug**(SW 97%/AMCR 45% 平價回填被當免費分散器,美化 LW→已加恰零報酬濾網);「賺回門票」限 vol 通道(淨報酬 inv-variance 全勝);47 檔子面板訊號特徵值中位 4=docs/20 預測在其 N 成立 |

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
