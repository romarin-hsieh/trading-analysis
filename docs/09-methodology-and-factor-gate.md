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

## 五、廣度測試結果 —— 我的假說被**推翻**（51 → ~500 檔）

我預測：擴廣度到 S&P 500 會收緊 ICIR、穩定因子符號（Grinold）。**ingest 501 檔（1.2M rows）實測後，假說被打臉**：

| 因子 | ICIR 51檔 | ICIR 500檔 | 符號穩定(51) | 符號穩定(500) |
|---|---|---|---|---|
| mom_12_1 | +0.03 | **−0.03** | 否(翻號) | 否(翻號) |
| mom_6_1 | **+0.11** | **−0.01** | 是 | 是 |
| mom_3_1 | +0.11 | −0.04 | 是 | 否(翻號) |
| lowvol | −0.15 | −0.11 | 是 | 是（唯一兩邊都 PASS）|

**真相（比假說更深刻）**：
1. **擴廣度沒有收緊 ICIR、也沒穩定符號**——又一次「先量測再斷言」：我預測會改善，量測說沒有。
2. **動量在廣市場反而變死/變負**（mom_6_1 ICIR +0.11 → −0.01）。它在 51 檔集中科技股強，是因為那 universe 被少數強勢趨勢股（NVDA 等）主導——**那不是穩健的橫截面動量因子，是對特定贏家的 beta**。換到分散、較有效率的 500 檔大盤，動量就消失（呼應 2009 後「動量已死」的學術爭論）。
3. **Grinold 的盲點**：`Sharpe = IC × √breadth` 假設 IC 不變；但**universe 越廣越有效率，IC 反而下降**。廣度與 IC 互相抵銷——廣度不是免費的 Sharpe。
4. **唯一跨 universe 存活的是 lowvol**（兩邊都負 IC、單調、穩定）——它是少數不隨 universe 改變的真效應。
5. **回頭重新詮釋本 session 的產業策略**：它們的「動量 edge」**大半是對少數贏家的 beta，不是因子 alpha**——這也解釋了為何因子搜尋的 alpha 都不顯著（[docs/06](06-factor-search-frontier.md)），而唯一顯著 alpha 來自**多 sleeve 分散**（[docs/08](08-recommended-strategy.md)），不是任何單一因子。

> **修正後的結論**：瓶頸不只是「廣度」——是「**沒有一個 universe-無關的穩健因子**」。提升成效的真正路徑不是盲目擴廣度，而是 (a) 為**每個 universe 分別驗證**因子（因子是 universe 特定的）、(b) 靠**多元分散**榨 alpha（已證實有效）、(c) 補**另類資料**提高 IC 本身。擴廣度單獨無效——這是這次實測最重要的修正。

## 六、B 落地：regime-conditional 歸因模組（filter 適用地圖）

建 `src/trading_analysis/regime/conditional_attribution.py`（`scripts/regime_applicability.py` demo、93 tests）：量測因子 IC **在每個 regime 桶內**，含防洩漏 lagged 標籤 + stationary-bootstrap CI。經 **10-agent 對抗式 review**（每個發現都實測），修了 5 個確認問題：

| # | 嚴重 | 問題 | 修正 |
|---|---|---|---|
| 1 | HIGH | ~14 個 (因子×regime×桶) cell 用 90% CI 無多重測試校正 → 純噪音因子 ~69% 機率亂中星 | 加 **Benjamini-Hochberg FDR**，決策旗標改 `significant_fdr`（家族層級）|
| 2 | MED | bootstrap block=10 太短（21d 重疊 IC 自相關 φ≈0.93、VIF=13）→ CI 過窄、假陽性率 0.32 | block = max(horizon, VIF)；並報 **n_eff = n/VIF**（350 天 regime 只 ~30 獨立觀測）|
| 3 | MED | 空 regime 桶丟 cryptic KeyError | 空 groupby 回傳空表 |
| 4 | LOW | ICIR 在重疊 IC 上被誤讀為顯著 | demo 移除 ICIR、改顯示 CI + n_eff |
| 5 | LOW | trend_regime 暖身期誤標 "bear" | 暖身 mask 成 NaN |

**修正後的適用地圖（更誠實）**：
- **動量**：FDR 後仍顯著於 **bull / low-vol / normal**（穩健）。
- **lowvol**：FDR + 正確 block 後**所有星號消失**——它先前的 regime「edge」**通不過多重測試**，是 review 抓到的假陽性。

> 教訓：選擇規則（「只在這些 regime 套用」）**必須做多重測試校正 + 自相關感知的 CI + 有效樣本數**，否則 regime-conditional 分析會系統性地亂中星。模組現在內建這三道防線。本 session 第二次靠對抗式 review 把自己的過度自信糾正回來。

## 七、C 結果：regime-conditional 切換**沒有**提升成效（誠實負面結果）

把適用地圖（動量顯著於 bull/low-vol/normal）做成實際切換規則，對照不切換與簡單 200SMA gate（`scripts/regime_switching.py`，net 10bps）：

| 變體 | CAGR | Sharpe | MDD | **Calmar** | 16-19 Sh | 20-24 Sh |
|---|---|---|---|---|---|---|
| **A 不切換（純動量）** | +23.5% | 1.06 | −37% | **0.63** | 1.22 | 1.10 |
| B 200SMA gate | +16.0% | 0.95 | −31% | 0.51 | 1.16 | 1.01 |
| C 適用地圖→現金 | +11.2% | 0.74 | −22% | 0.52 | 1.08 | **0.69** |
| D 適用地圖→債券 | +10.4% | 0.67 | −32% | 0.33 | 1.08 | 0.60 |
| 1/N 買進持有 | +18.8% | 1.02 | −33% | 0.56 | — | — |

**結論（清楚的負面結果）**：
- **不切換的純動量（A）Calmar 最高（0.63）、Sharpe 最高**——切換**犧牲的報酬大於省下的回撤**，風險調整後反而更差。
- **精緻的多 regime 條件化（C）≈ 簡單 200SMA gate（B）**（Calmar 0.52 vs 0.51）→ **複雜度毫無增益**。
- C/D 在 **2020-24 子期 Sharpe 大跌**（0.69/0.60 vs A 的 1.10）——gate 在 COVID/2022 後一直錯過反彈，**主動傷害**近期績效。
- 嚴謹閘門（A）：PSR-vs-0=0.999 但 **PSR-vs-1/N=0.58、SPA p=0.05**——純動量也只是勉強贏 1/N。

> **最深的教訓：conditional IC（描述性）≠ 可獲利的 gate（處方性）。** 適用地圖說「動量在 bull 的 IC 較高」是**對的**，但據此 gate 到 bull-only **不會**提升 Sharpe——因為 (a) regime 標籤有 lag、(b) **退出市場的機會成本 > 省下的回撤**（市場多數時間在漲，低-IC 的 bear 區段平均報酬仍為正）。這呼應整個 session 的反覆發現：**擇時/gating 傾向減損價值**。適用地圖適合**理解因子**，不適合直接當**擇時開關**。

---
*工具：`scripts/factor_determination.py`、`scripts/regime_applicability.py`、`scripts/regime_switching.py`、`src/trading_analysis/regime/conditional_attribution.py`。2026-06-16。*
