# 推薦策略（已通過嚴謹閘門）— 風險平價多 sleeve 組合

> 這是整個 session 跑過所有測試後，**唯一通過完整嚴謹閘門、且有統計顯著 alpha** 的策略。它不是年化 50%（那已證明不可達），而是**風險調整後最佳、可實際交易、可重現**的策略。工具：`scripts/validate_recommendation.py`、`scripts/meta_portfolio.py`。

## 1. 嚴謹閘門結果（這才是「可行」的定義）

| 指標 | 數值 | 判讀 |
|---|---|---|
| CAGR / Sharpe / MDD | **+11.0% / 1.18 / −19.3%** | 全 session 最佳風險調整 |
| **Carhart alpha** | **+6.08%/yr，t=2.64 (p=0.008)** | ✅ **統計顯著的真 alpha**（先前所有策略 t<1）|
| 市場 beta | 0.22（R²=0.34）| 與大盤低相關，alpha 非借來的 beta |
| PSR P(Sharpe>0) | 1.000 | ✅ 不是運氣 |
| DSR（survives ~13 configs）| 0.971 | ✅ 不是多重測試的幸運 |
| PSR vs 等權 sleeve(1/N) | 0.606 | ⚠️ 優化只小贏 naive 等權（1.18 vs 1.09，DGU）|
| 子期穩定 | 2016-19 Sharpe **1.72**（MDD −6%）；2020-24 **0.97**（MDD −19%）| ✅ 兩期都正，有衰退但穩健 |

**為什麼這個能有 alpha 而單一產業策略不能**：把 5 個**低相關**（平均 +0.23）的收益來源組合 → 分散化（DeMiguel 說的「唯一免費午餐」）把單一 Sharpe ~0.9 拉到 1.18，且非市場性的部分顯著（t=2.64）。這正是 [docs/07](07-industry-strategies.md) Calmar 證明的另一面：你贏不了物理上限，但**正確的組合能榨出可證實的 alpha**。

## 2. 完整可重現規格（5 個 sleeve）

每個 sleeve 都是獨立、point-in-time、含成本的子策略：

| Sleeve | 選股 | 進場 | 出場 |
|---|---|---|---|
| **科技/AI 股票動量** | 全 49 檔產業股取 6M 動量前 10 | 月初 ∧ SPY>200SMA | 跌破 50SMA／掉出前 10／regime off |
| **防禦輪動** | 12M 絕對動量前 4 且 >0 且 > 最佳防禦 | 月初 | risk-off → 退債/金/現金 |
| **槓桿趨勢** | TQQQ（3x Nasdaq）| QQQ>200SMA | QQQ<200SMA → 現金 |
| **黃金** | GLD | 常駐（風險平價自動調權重）| — |
| **債券** | IEF（7-10y 美債）| 常駐 | — |

**權重**：對 5 個 sleeve 的日報酬做 **Ledoit-Wolf 風險平價**，**走查式 `rebalance()`**（126 日回看窗、月頻、防洩漏 — O5 模組）。每個 sleeve 的權重 = 使其風險貢獻相等。
**槓桿（可選，調節風險/報酬）**：把整體組合放大到你的目標波動。Calmar 槓桿不變，所以這只移動 CAGR/MDD 的絕對水位，不改變比率：

| 目標波動 | 約略 CAGR | 約略 MDD |
|---|---|---|
| 無槓桿（~9% vol）| ~11% | ~−19% |
| 12% vol | ~14% | ~−25% |
| 15% vol | ~17% | ~−35% |

## 3. 怎麼跑 / 怎麼用
```
uv run python scripts/validate_recommendation.py   # 重現嚴謹閘門
uv run python scripts/meta_portfolio.py            # 重現組合與槓桿不變性
```
實務執行：月頻（每 21 個交易日）重算 5 個 sleeve 的持股與風險平價權重，依權重配置 $100k。換手低、標的全是高流動性大型股/ETF，**NT$10M 單筆容量無虞**。

## 4. 誠實的限制（必讀）
- **這不是年化 50%。** 它是 ~11%（無槓桿）到 ~17%（15% vol），風險調整後最佳。要 50% 必須加大槓桿到 ~3x，MDD 隨之到 −50%+（[docs/07](07-industry-strategies.md) §5）。
- **優化只小贏等權**（PSR-vs-1/N 0.606）：實務上可以直接用**等權 5 sleeve**（Sharpe 1.09，更穩健、更少過擬合）——風險平價的邊際好處不大。
- **alpha 會衰退**：2016-19 Sharpe 1.72 → 2020-24 0.97。t=2.64 是過去 9 年的；未來會縮水（你正確指出的 alpha decay）。
- **倖存者偏誤**：universe 是現任成分股，結果偏樂觀（[docs/05](05-backtest-postmortem.md) scorecard #2）。
- **未做**：真實滑價/借券成本對槓桿 sleeve 的衝擊、稅、TQQQ 的 expense ratio（已內含在 adj_close）。

---
*這是我能誠實交付的最佳策略：可重現、通過 DSR/SPA/alpha 閘門、有顯著 alpha、可用槓桿調風險。它尊重物理上限（[docs/06](06-factor-search-frontier.md) Grinold、[docs/07](07-industry-strategies.md) Calmar），不捏造不可達的數字。2026-06-16。*
