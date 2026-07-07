# 100+ 策略總目錄與驗證狀態 + 混合設計結論

> ⚠️ **本檔為 2026-06-19 快照。** 其後修正:zoo 的 null bar 0.84 已被有效試驗數修正(TR-14:59 變體 n_eff=1.8);**IBS 已由 TR-16 完整審判反轉為 FAILED**(成交慣例假象);XS 動量降級(TR-11)。現行判定以 [docs/18](18-strategy-registry.md) 為準。

> /goal part 1(2026-06-19):擴大到 ≥100 則策略並驗證,再評估混合(FILTER/加權)設計。
> 驗證工具:`scripts/strategy_zoo.py`(59 變體批量)+ `scripts/ensemble_mix.py`(混合設計,train/holdout)+ 本專案先前已驗證 ~55 個(docs/05-14)。**合計 in-house 實測 114+**,另掛 [Chen-Zimmermann OSAP 212 個學術訊號](https://www.openassetpricing.com/)為外部已複現目錄。

## 1. 目錄總表(族系 × 變體 × 狀態)

### A. 本次 zoo 批量驗證(59 個,QQQ/47 檔,2015-2026,leak-free,net)
| 族系 | 變體 | 最佳(Sharpe) |
|---|---|---|
| SMA/EMA 交叉 | 8×2 網格 + close>SMA20/50/200 = 19 | close>SMA200(1.01) |
| **Vegas 雙通道** | strict/loose = 2 | loose(1.00)≈趨勢濾網 |
| Donchian 突破 | 20/10、55/20、10/5 = 3 | 55/20(0.80) |
| Bollinger | 均值回歸×2 + 突破×2 = 4 | meanrev 皆弱(≤0.42) |
| RSI | Connors RSI2、RSI14×2 = 3 | RSI14_30_70(0.63) |
| MACD | 訊號交叉、零軸 = 2 | 零軸(0.86) |
| 時序動量 ROC | 21/63/126/252d = 4 | 126d(0.85) |
| 52 週高 | 5%/10% 近高 = 2 | 10%(0.79) |
| Keltner/Chandelier | 2 | Chandelier(0.79) |
| **均線×成交量** | 金叉+量能、量能突破、OBV、MA∧OBV = 4 | OBV(0.86) |
| IBS 均值回歸 | 1 | **1.03,MDD −16%(TS 最佳)** |
| 日曆 | TOM、避週一 = 2 | 皆弱 |
| VIX 規則 | risk-off25、spike 反轉、calm-only = 3 | calm-only(0.84) |
| 波動目標 | 12% = 1 | 1.02 |
| 橫截面(47 檔) | 動量×4、52wH、低波、量能驚奇 = 7 | mom6-1 top5(1.24,=beta+curation) |

### B. 本專案先前已驗證(~55 個,docs/05-14)
Minervini Trend Template、SMA crossover、Kronos trend、S1-S7 產業策略(7)、槓桿×趨勢(SOXL/TQQQ/TECL/SPXL/USD=5)、防禦雙動量、regime rotation(證偽)、TOM/隔夜(2)、Kalman pairs、Antonacci/Faber TAA(日線+長歷史=4)、5-sleeve combo+槓桿刻度(7)、高波動 R0-R4(5)、自選宇宙 V1-V8(8)、horizon 六槽(6)、基本面因子(GP/ROA/應計/EY/BM/資產成長/品質綜合/insider/PEAD-SUE/本業 7 因子=16)。

### C. 外部已複現目錄(不重測,掛參照)
[OSAP 212 橫截面訊號](https://github.com/OpenSourceAP/CrossSection)(價值/品質/投資/動量/微結構五大類,附複現碼+資料)——我們已實測其中代表(GP=唯一穩健、value 失效、動量廣市場死),其餘 200 個的**先驗**由 McLean-Pontiff 給定:發表後平均衰退 58%。

**合計:59 + 55 = 114 個 in-house 實測 + 212 外部目錄 ≥ 100 ✅**

## 2. Zoo 的誠實讀法(多重測試)

- QQQ B&H Sharpe 0.93;**只有 10/59 贏它**。N=59 的 null bar E[max Sharpe]≈0.84 → 榜上大半「贏家」與選擇運氣不可分。
- 有結構意義的倖存者:**IBS(1.03/−16%)**、**VolTarget(1.02/−18%)**、**SMA200(1.01/−22%)**——全是「風險塑形」型,不是報酬增強型。
- **Vegas 通道實測 1.00**:有效,但本質=另一件趨勢濾網外衣(≈SMA200),無獨特 alpha。
- 突破帶類(Keltner/Boll-breakout)墊底(0.25)——日線上的帶狀突破被 whipsaw 稅吃光。

## 3. 混合設計結論(回答「你都只用一種」)

`ensemble_mix.py`,52 條規則,holdout 2021+:

| 設計 | 全期 Sharpe/MDD | **Holdout** Sharpe/MDD |
|---|---|---|
| QQQ B&H | 0.93 / −35% | 0.84 / −35% |
| **E1 投票比例曝險**(所有規則多空票的平均) | 0.98 / −16% | **0.99 / −16%** |
| E2 過半數才滿倉 | 0.70 / −24% | 0.83 / −17% |
| E3 追蹤近 1 年 Sharpe 前 10 走動式 | 0.87 / −19% | 0.73 / −19% |
| E4 三重濾網 AND(SMA200∧動量126∧OBV) | 0.81 / −16% | 0.94 / **−14%** |
| E5 樣本內最佳單規則(holdout 對照) | 0.84 / −22% | **0.63** / −22% |

**三個可交付結論**:
1. **混合贏過「選最好的一個」**:E1(0.99)>> 樣本內最佳單規則的 holdout(0.63)。這是 ensemble 的核心價值——**穩健性**,把「猜哪條規則未來有效」的選擇風險分散掉。
2. **混合的贏面在風險,不在報酬**:單資產 long/flat 規則的混合**數學上不可能**贏 B&H 的 CAGR;它給的是 MDD 砍半(−35%→−16%)+ Sharpe 提升。
3. **追績效的動態加權(E3)反而最差**——「近期誰強就加碼誰」在規則層面也是動量崩潰。**靜態等權票池 > 聰明的動態選擇**。三重濾網(E4)是低 MDD 取向的合理精簡版(你的 FILTER 直覺是對的,但用 AND 疊 =犧牲報酬換低回撤)。

**推薦用法**:把 E1 票數(0-52 條規則中多少看多)當**市場健康度儀表**接進通知系統;倉位=票數比例(連續曝險),避免二元 all-in/all-out。

## 4. 與止損/通知系統的銜接(goal part 2 交付)

- 五維止損投票(VIX+倉位+乖離+RSI+MACD)實測:`scripts/multi_exit.py`——**確認堆疊≥3/5 未勝過最佳單維(乖離率)**;槓桿標的上止損才有價值(TQQQ MDD −82%→−58%)。→ 定位=**預警紀律工具**。
- 已建成:`scripts/notify/exit_monitor.py`(每日投票推播)+ `serenity_tracker.py` + `.github/workflows/monitor.yml`(Actions cron→Telegram,$0)。

---
*接續 docs/13(第一版目錄)、docs/14(六槽位框架)、docs/16(Serenity)。2026-06-19。*
