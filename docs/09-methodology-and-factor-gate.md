# 規劃階段：樣本盤點 + 因子確定方法論（A）

> 回到規劃階段的兩個問題：(1) 用了什麼樣本、樣本數、時間窗？(2) 如何確定變因（因子）、確認 filter、確認 filter 的適用情境？本文記錄答案與**可執行的因子閘門**（`scripts/factor_determination.py`）。

## 一、樣本盤點

| Universe | 標的 | 時間窗 | bars/檔 | 用途 |
|---|---|---|---|---|
| smoke | 6 | 2023-01→2024-06 | 374 | 早期測試（單一多頭，棄用）|
| **us_study** | 52 | 2015→2024 | 2515 | 主力 |
| us_sectors | 49 | 2015→2024 | 2515 | 產業策略 |
| us_leveraged | 8 ETF | 2015→2024 | 2515 | 槓桿路徑 |

~70 不重複標的、**全美股、全日線、yfinance adj_close**。窗口 10 年，暖身後有效從 2016。

**⚠️ 有效樣本遠小於 2515**：對策略/regime 層級推論，獨立樣本只有**個位數**——真熊市僅 ~3-4 個（2015-16、2018、2020、2022），動量週期 ~10-20 個。這是 50–100% 目標脆弱、DSR/PBO 必要的根因。
**限制**：倖存者偏誤、廣度僅 ~50（Grinold 把 Sharpe 鎖 ~1）、單一市場/頻率/窗口、無基本面/另類資料、樣本內調參。

## 二、如何「確定變因」（A，已執行：`scripts/factor_determination.py`）

閘門（分辨真因子 vs 資料挖掘）：① 多 horizon IC/ICIR/hit-rate ② **跨子期同號穩定**（2016-19 ∧ 2020-24）③ 分位單調 ④ **對 12-1 動量正交後的增量 IC** ⑤ 多重測試膨脹。

實測（us_study 51 檔、forward 21d）：

| 因子 | IC | IC 16-19 | IC 20-24 | 單調 | 增量IC | 判定 |
|---|---|---|---|---|---|---|
| mom_12_1 | +0.008 | **−0.013** | **+0.025** | False | — | **FAIL（跨期變號！）** |
| mom_6_1 | +0.029 | +0.029 | +0.029 | False | +0.021 | weak |
| mom_3_1 | +0.027 | +0.026 | +0.027 | False | +0.021 | weak |
| rev_5 | +0.001 | −0.002 | +0.003 | False | +0.002 | FAIL |
| **lowvol** | **−0.041** | −0.057 | −0.026 | **True** | −0.028 | **PASS** |
| prox_52w_high | −0.011 | −0.021 | −0.002 | False | −0.014 | weak |
| vol_accum | −0.011 | −0.002 | −0.019 | False | −0.013 | weak |

**教訓（這才是方法論的價值）**：
- **教科書的 12-1 動量在這個 universe 竟然跨期變號（FAIL）**——證明「廣為人知的因子也未必穩定」，必須親自驗。
- 唯一 PASS 的是 **lowvol，但 IC 是負的**＝在這個 AI/科技高 beta universe，**高波動股反而贏**（低波動異象被反轉）。這是 universe 特定效應，不是可外推的 alpha。
- 7 個因子裡只有 1 個過全閘門 → 大多數候選是雜訊；**閘門（跨期穩定+單調+增量+多重測試）正是分辨真假的工具**。
- 50 檔廣度下 IC 都很小（~0.02-0.04）、誤差大 → **因子推論需要更大廣度才有統計力**。

## 三、如何確認 FILTER + 其適用情境（B/C，方法論）

- **確認 filter**：比較 filter ON vs OFF 子集的 edge 是否分離；閾值附近要「平台非尖峰」（熱力圖）；每個閾值是一次 trial → 對 filter 配置跑 PBO；PurgedKFold walk-forward；經濟理由 + 成本後淨值。
- **確認適用情境（已 grounding）**：動量 IC 在 **BULL +0.039 / BEAR −0.032**（訊號熊市反轉）——這就是 regime gate 有用的根因。方法＝**條件化績效歸因**：按 regime（趨勢/波動/利率/相關性）分桶，量測 filter 每桶貢獻，建「適用地圖」。**統計警告**：10 年僅 ~3-4 真熊 → regime-conditional 推論誤差極大，需更長歷史 + 跨市場 + stationary-bootstrap 壓力測試。

## 四、優先序（按槓桿）
🥇 擴廣度（S&P500/全市場）｜🥈 PIT 成分股（修倖存者）｜🥉 更長歷史（更多 regime cycle）｜4 regime 條件歸因模組｜5 把 PurgedKFold+DSR/PBO 用在搜尋階段。
**瓶頸不是演算法，是資料地基**：廣度 > 歷史長度 > 另類資料 > 演算法。

---
*工具：`scripts/factor_determination.py`、`scripts/{factor_search,sector_strategies,leveraged_strategies,meta_portfolio,validate_recommendation}.py`。2026-06-16。*
