# Repo 評估 ＋ 可萃取邏輯報告（Download & Study）

> 日期：2026-06-14。對 6 個 shortlist repo 做 code-level 研讀（clone 於專案外 `../​_ref_repos/`，shallow）。
> 原則：因授權不同，**萃取＝理解規則後乾淨重寫，不直接複製原碼**；惟本批 6 個授權皆寬鬆，必要時可帶 attribution 複製。
> 配套：策略/投資者面見 [research-inventory.md](research-inventory.md)。

## 授權總表（全部寬鬆，零 copyleft 風險 ✅）

| Repo | 授權 | 與我們 Apache-2.0 相容 | 風險 |
|---|---|---|---|
| starboi-63/growth-stock-screener | **MIT** | ✓ | 無 |
| nblade66/MagicFormula | **MIT** | ✓ | 無 |
| xang1234/stock-screener | **Apache-2.0** | ✓（完全相同） | 無 |
| virattt/ai-hedge-fund | **MIT** | ✓ | 無（README「教育用途」是免責非授權限制） |
| TauricResearch/TradingAgents | **Apache-2.0** | ✓ | 無 |
| microsoft/qlib | **MIT** | ✓ | 無 |

---

## 1. growth-stock-screener（Minervini + Kell）— 規格好、程式碼別跑

- **品質**：6 階段 CLI 管線，可讀有測試；但**大量 Selenium 爬硬編 XPath**（tradingview/cnbc/marketbeat），DOM 一改就壞 → **當規格參考，別當程式跑**。
- **最有價值：RS Rating 公式**（`relative_strength.py` + `calculations.py:31`，乾淨可分離）：
  - 用 yfinance 抓 2 年日線；需 ≥252 交易日
  - `RS_raw = 0.2·ΔQ1 + 0.2·ΔQ2 + 0.2·ΔQ3 + 0.4·ΔQ4`（每季=63 日切片，最近一季雙權重）
  - **RS Rating = 全universe 橫截面百分位 × 100**（`df["RS_raw"].rank(pct=True)*100`），預設門檻 90
  - ⚠️ **無 benchmark**，是「相對同儕」非「相對 SPY」
- **Trend Template**（`trend.py:174-183`）：price≥SMA50、price≥SMA200、SMA10≥SMA20、SMA20≥SMA50、距 52 週高 ≤50%。**是部分版**（缺「200SMA 上升≥1 月」「距低點+30%」）。
- **可借**：RS 公式 + Trend 布林邏輯（自己用 OHLCV 算 SMA，丟掉爬蟲）。SEC EDGAR 營收成長（`sec_requests.py`）日後做 CANSLIM 可參考。

## 2. MagicFormula（Greenblatt）— 公式對、水管爛

- **品質**：884 行單檔，threading 爬 Yahoo，依賴**已棄置的 `yahoofinancials`**，TODO 滿天、有未解的外幣 bug → 只取公式。
- **公式（`magic_formula.py:70-95,352-361`，正確可萃取）**：
  - `ROC = EBIT / (NWC + FixedAssets)`；EBIT=近 4 季加總(TTM)；NWC=max(0, 流動資產−超額現金−應付帳款)；FixedAssets=總資產−流動資產−無形資產
  - `EarningsYield = EBIT / EV`；EV=max(0, 市值+總負債−超額現金)
  - `magic_rank = rank(ROC desc) + rank(EY desc)`，**升冪取最小**
  - 過濾：僅普通股、市值≥$50M、10 日均額≥$10M、剔除財報過舊(>400d)
- **可借**：三條公式 + 排名邏輯。其餘（yahoofinancials/SQLite/threading）用我們 DuckDB+yfinance 取代；修掉外幣/負分母（直接 skip 而非強制 max(0,·)）。

## 3. xang1234/stock-screener（Apache-2.0，Claude Code 打造的全棧）— 最佳規格金礦

- **意外發現**：不是小篩選器，而是**認真工程**——895 py 檔、380 後端+64 前端測試、5 道 CI（含 temporal-integrity + golden regression，AI-slop 不會做這些）、227+ PR 歷史被 squash。FastAPI+Celery+Postgres+Redis / React。**12 市場**動能/成長篩選。
- **策略（純動能成長，無 value）**：Minervini、CANSLIM、IPO、Volume Breakthrough、Qullamaggie/O'Neil-Morales。
  - **Minervini 加權版**（`minervini_scanner.py`）：RS 20 / Stage-2 20 / MA對齊 15(50>150>200,200上升) / 52w位置 15（距低≥30% @`:542`、距高≤25% @`:543`）/ VCP 20；通過＝score≥70 且 rs≥70 且 stage==2。
  - **Pocket Pivot**（`:258`）：上漲日量 > 前 10 日最大下跌量、在 50MA 上。**Power Trend**、**Episodic Pivot**（跳空≥10%+2×量）定義皆教科書正確。
  - **CANSLIM**（`canslim_scanner.py`）：N=距 52w 高 15% 內、S=漲跌量比≥1.5、L=RS≥90→20分、I=法人持股 50-70% 甜蜜區。
  - ⚠️ **RS rating 是 benchmark-spread 百分位**（stock−benchmark，權重 0.40/0.20/0.20/0.20），**非真 IBD**；**VCP 偵測是 10 行 stub（未完成）**。
- **可借**：① `BaseStockScreener` + criteria 組合模式（≈我們 `strategy/rules/`）② 上述精確閾值 ③ composite scoring（weighted_avg/max/min）④ RRG 時序 z-score ⑤ 5 道 golden/temporal 測試思路。**跳過** Celery/Redis/Postgres/主題管線/chatbot。

## 4. ai-hedge-fund（MIT）— V1 LLM persona 層最佳「模式捐贈者」

- **品質**：persona 邏輯**有真材實料、非 prompt 包裝**。每個 persona ~300-800 行：先 deterministic 算指標，再丟精簡 facts 給 LLM 下 bull/bear/neutral 結論。
  - **Buffett**（`warren_buffett.py`）：ROE/負債/毛利評分 + 多因子 moat + **owner earnings**(NI+D&A−維護capex−ΔWC) + **三階段 DCF** + 15% 安全邊際
  - **Burry**（`michael_burry.py`）：**FCF yield≥15%→+4**、EV/EBIT<6→+2、淨內部人買進、逆向情緒（≥5 則負面新聞加分）
  - **Lynch**（`peter_lynch.py`）：**PEG<1→+3**，明確權重 30%成長/25%估值/20%基本面/15%情緒/10%內部人
  - **Graham**（`ben_graham.py`）：NCAV>市值→+4、**Graham Number √(22.5·EPS·BVPS)**
- **架構**：LangGraph 單向 fan-out/fan-in（analyst→risk_manager→portfolio_manager，**無辯論迴圈**）。風控只算倉位上限**不投方向**；組合經理用 deterministic `compute_allowed_actions` 算現金/保證金（LLM 不碰算術）。
- **LLM 層**：`src/utils/llm.py` `call_llm` — provider 無關、JSON-mode 偵測 + 手動解析 fallback + 3 次重試 + `default_factory` 優雅降級；**Ollama 一等公民**。≈我們 V1「Ollama 預設+雲端 fallback」目標。
- **可借**：persona 模板（`analyze_*`→`{score,max_score,details}`→thin LLM）、`call_llm` wrapper、風控/方向解耦、`ANALYST_CONFIG` 單一登錄、財務公式（MIT）。**避開**：每日跑 LLM 的 backtester（太貴太慢→用我們 vectorbt）、line-length=420 格式、Lynch 的 P/E 近似。

## 5. TradingAgents（Apache-2.0）— 借「多空辯論+裁判」模式

- **架構**：LangGraph，analyst（依序）→ **Bull/Bear 辯論** → Research Manager(裁判) → Trader → 風險 3 人組 → Portfolio Manager。
- **辯論真相**：**預設 `max_debate_rounds=1`**＝一次多方+一次空方+裁判，**非真多輪**（`conditional_logic.py:52`）。勝負由**裁判 LLM**裁定非投票。誠實評價：預設下偏「兩份對立簡報+裁判」，辯論的迭代價值要 rounds≥2 才出現（成本翻倍）。對抗框架確實減少單邊偏誤。
- **LLM**：`quick_thinking_llm` vs `deep_thinking_llm` 分流（只有兩個裁判用 deep）；Ollama 經 OpenAI 相容端點一等支援；structured→free-text 優雅降級。**無 token 預算、無 backtester**（README 自承是 research scaffold）。
- **可借**：① 裁判仲裁的對抗模式（**Ollama 當辯手、雲端只給裁判** → 天然控雲端花費）② round cap 當 token 預算旋鈕 ③ `structured_or_freetext` fallback ④ 寫得好的 prompts ⑤ append-to-history 狀態。**跳過**：V1 不必上 LangGraph（固定 DAG 用簡單 loop 即可）、3 人風險組（先只做多空）。

## 6. qlib（MIT）— 因子層「採櫻桃」而非整合

- **內容**：完整 AI 量化平台。**Alpha158**（~158 技術 alpha，字串表達式 `loader.py:72`）、**Alpha360**（60 日原始 OHLCV，給序列模型 `loader.py:15`）。
  - 範例因子：`"($close-$open)/$open"`(KMID)、`"Mean($close,N)/$close"`(MA)、`"Std($close,N)/$close"`、`"Corr($close,Log($volume+1),N)"`、`"($close-Min($low,N))/(Max($high,N)-Min($low,N))"`(RSV)、`"Slope($close,N)/$close"`(BETA)
  - ⚠️ **Alpha158 全是技術/量價 alpha，無基本面、無 Fama-French、無 QMJ**。
- **金礦＝表達式引擎**：字串→運算樹（`$close`→`Feature("close")`），~20 個運算子（Ref/Mean/Std/Sum/Max/Min/Slope/Corr…）語意**≈ pandas rolling 1:1**，極易移植到我們 pandas/DuckDB。
- **資料摩擦**：用自有 `.bin` 二進位格式（非 Parquet），須 `dump_bin.py` 轉檔（支援美股 yfinance + `--region us`），等於資料第二份副本 + 學習曲線。
- **建議**：**採櫻桃（option b+c）**——把 Alpha158 的因子字串 + ~20 運算子在我們 pandas/DuckDB 重寫成 `factors/` 模組；可選 side-car 裝 `pyqlib` 跑樣本對照驗證。**不整合 wholesale**（重複我們 vectorbt 回測、China-centric）。Fama-French/QMJ 需自建（qlib 給文法不給因子）。

---

## 綜合：建置路線圖（由低風險、零新資料 → 高價值）

| 階段 | 做什麼 | 需要的新資料 | 來源參考 |
|---|---|---|---|
| **1（即可做）** | `strategy/rules/minervini_trend.py` — 8 條 + `rs_rating()` helper（放 `models/ta_indicators.py`） | **無**（只用現有 OHLCV） | growth-stock-screener RS 公式；xang1234 加權版閾值 |
| **2（關鍵缺口）** | 在 `DuckStore` 加 **fundamentals** partition + `schema.Fundamentals` + yfinance 季報抓取（`Ticker.quarterly_balance_sheet/income_stmt`） | **基本面**（EBIT/資產/負債/市值…） | 取代 MagicFormula 死掉的 yahoofinancials |
| **3** | `strategy/rules/magic_formula.py` + `graham.py`（Graham Number/NCAV） | 用階段 2 的基本面 | MagicFormula 公式；ai-hedge-fund `ben_graham.py` |
| **4** | `factors/` 模組：移植 qlib Alpha158 運算子 + 因子字串；接 vectorbt 做 IC/分位分析 | 無（OHLCV）/ 部分基本面 | qlib `loader.py`/`ops.py`；自建 Fama-French/QMJ |
| **5（V1 LLM）** | persona agent 層：借 ai-hedge-fund 模板 + TradingAgents 多空辯論；Ollama 辯手 / 雲端裁判；round cap 當預算 | — | ai-hedge-fund `call_llm`/persona；TradingAgents 辯論 |
| **6（組合層）** | Markowitz/risk-parity 組合建構 + Bogle 被動基線 + Shiller CAPE regime overlay | — | PyPortfolioOpt / riskfolio-lib（見 research-inventory C-3） |

### 唯一的真實資料缺口
我們的 `DuckStore` 目前只存 **OHLCV + forecasts**（`store.py:31-34`），**沒有基本面表**。階段 2 是解鎖 Magic Formula / Graham / CANSLIM / QMJ 的關鍵前置，建議優先補。

### 參考 repo 位置
`C:\Users\Romarin\Documents\Software Projects\_ref_repos\`（8 個 shallow clone，不在我們 git 內；研究完可刪）。

---

## 7. Kronos（MIT）— 留作「選配 plug-in」，非主引擎

- **授權**：MIT（含 HF 權重），可用於我們 Apache-2.0 專案。
- **是什麼**：decoder-only autoregressive Transformer，對 OHLCV K 線做**離散 token**（兩段式：BSQuantizer tokenizer + DualHead predictor）。sizes：mini 4.1M / small 24.7M / base 102.3M / large 499.2M(未開源)，context 512。`predict(df, x_timestamp, y_timestamp, pred_len, T, top_k, top_p, sample_count)` 是**隨機生成式預測**（nucleus sampling，多路徑平均）。
- **✅ 我們的 wrapper 已驗證相容**（`models/kronos.py` 簽名/kwargs/max_context 都對）。**唯一要修**：`mini` 應配 `Kronos-Tokenizer-2k` 而非 `-base`。
- **驗證宣稱要懷疑**：「93% RankIC 提升」是 **rank-IC 的相對提升、非 93% 報酬/準確率**；小基數上的大提升可能**扣成本後無經濟價值**。獨立評論（Kinlay）：優化的是 MSE/CRPS 統計指標非經濟指標，「是研究方向、非 production alpha 引擎」。repo 回測僅 CSI-300 單一 ~11 個月 OOS 窗口，README 自承「簡化範例、非 production」，無第三方重現。
- **判決**：**選配 plug-in，不是主引擎**。機率性下一根 K 線預測難直接對映波段決策（最終都要塌成方向/波動訊號），而那正是已驗證的**規則式 Minervini/Magic Formula+因子**更勝之處。保留在既有 `KronosForecaster` 介面後當**實驗性次要訊號**（如預測隱含期望漲幅做進場/停損 sizing）或用其**合成 K 線**做回測壓力測試。別讓未經審計的「93%」凌駕已驗證的規則式核心。
- **替代**：Chronos(Amazon)/TimesFM(Google)/Moirai(Salesforce) 等通用 TS 基礎模型。Kronos 是唯一原生建模 OHLCV 聯合 K 線+訓練於金融資料者（表徵有結構優勢），但**獲利能力未證**；通用模型對波段同樣堪用且更易跑。

## 8. HKUDS/AI-Trader（⚠️ 無 LICENSE 檔）— 跳過，與我們需求不符

- **意外**：**不是 agent 推理框架**，而是**社交/跟單 SaaS 平台**（「bot 版 Robinhood」留言板）+ 研究資料管線。FastAPI+Postgres+Redis+web3。**repo 內無任何 LLM/agent 推理碼**——推理發生在外部連入的 agent（Claude/Cursor…）。「agent-native」只是註冊協定。
- **授權**：README badge 寫 MIT 但**無 LICENSE 檔**（`git ls-files` 無）→ 技術上 all-rights-reserved。**勿複製碼**。
- **驗證**：**無回測**（grep 無 backtest/walk-forward/slippage）。「排行榜」是自報 $100k 紙上帳戶、無成本模型。「research」是 agent 參與度的行為 A/B 實驗、非報酬。
- **判決**：**對我們參考價值低**。19.7k★ 反映病毒式 hook 非已驗證 alpha。V1 LLM 層仍以 **ai-hedge-fund（persona）+ TradingAgents（辯論）** 為準。唯一可借：SKILL.md 當 API 契約的點子（若日後對外開放 agent）。

---

## 9. 第三輪 scout 盤點：更多值得 clone 的 repo（填補特定缺口）

> 偵察 GitHub 找尚未評估的高價值 repo。star/授權 2026-06-14 查。已 clone 的見下方各深讀（§10 起陸續補）。

**VCP/型態偵測（我們最大缺口——xang1234 的 VCP 是 stub）**：
- **BennyThadikaran/stock-pattern**（~381★, **GPL-3.0**）：獨立、可讀的型態偵測（H&S/雙頂底/三角/**VCP**/harmonic）。**最佳獨立 VCP 引擎**，但 GPL（只參考別複製進公開 repo）。
- **pkjmesra/PKScreener**（~355★, **MIT**, 超活躍）：含「VCP (Minervini)」掃描 + RS rating + 突破。印度為主但 **MIT 可直接用**，VCP/RS 實作可挖。
- **HumanRupert/marketsmith_pattern_recognition**（~34★, 無授權）：唯一偵測 7 種 MarketSmith bases（杯柄/碟形/平台…）的 O'Neil base 偵測器。

**因子建構（vs 只有 alphalens）**：
- **stefan-jansen/machine-learning-for-trading**（~19.1k★）：ML4T 書範例，alpha 因子建構 + Fama-French + Alphalens + Zipline pipeline。**最佳因子建構學習資源**。
- **stefan-jansen/zipline-reloaded**（~1.8k★, Apache-2.0）：Pipeline API 是橫截面因子計算的標準範式。

**回測框架（補充 vectorbt）**：**pmorissette/bt**（~2.9k★, MIT，組合/再平衡層回測）；backtesting.py（AGPL）；lumibot（GPL，活躍，含實盤執行）。

**AI/agent 雷達**：georgezouq/awesome-ai-in-finance（~6k★, 索引）、LLMQuant/awesome-trading-agents（~216★, 新）、EthanAlgoX/LLM-TradeBot（~282★, MIT, 含 regime）。

**台股**：**FinLab/finlab**（TW 量化主流平台、900+ 指標、整合不 clone）；hu0937/FinPilot（~16★, MIT, **Claude 生成策略 over FinLab API + Telegram**，與你 TW+LLM 方向最對味但不成熟）。

**仍未被 OSS 良好覆蓋的缺口**：單一高品質 Piotroski/Altman/Acquirer's Multiple 庫（最好從 FinanceToolkit 取）、無 WRDS 依賴的乾淨 Fama-French builder。

**已 clone 待深讀**：stock-pattern、PKScreener、marketsmith_pattern_recognition、FinanceToolkit、PyPortfolioOpt、Riskfolio-Lib、python-canslim、CAN-SLIM-screener（評估見下方 §10+）。

---

## 10. FinanceToolkit（MIT）— 比率層：lift 公式，別當依賴

- **關鍵好消息**：**可吃我們自己的 DataFrame**（`toolkit_controller.py:98-101,528-531` 的 `balance/income/cash` 參數，純本地轉換無網路）→ **不綁 FMP key**，不擋我們的 EDGAR point-in-time 計畫。
- **可用且正確**：**Piotroski F-Score**（`models/piotroski_model.py`，完整 9 條）、**Altman Z**（`models/altman_model.py`）、profitability/solvency 原子（ROE/ROA/margin/ROIC）。
- **⚠️ 不可直接用**：**Graham Number 不存在**（docstring 還把 NCAV 誤標成 Graham number）；**Magic Formula 的 ROC/EY 是非標準定義**（其 ROIC≠Greenblatt 的 EBIT/(NWC+固定資產)，earnings yield 是 EPS/price 非 EBIT/EV）。EV 本身正確（`valuation_model.py:251`）。
- **判決**：**lift Piotroski + Altman 兩模組**（純函式、MIT、~5-40 行）進我們的因子/`graham.py`，**Magic Formula/Graham Number/QMJ 自己照標準定義寫**；FinanceToolkit 當**參考實作 + 測試 oracle**（cross-check 我們的 Piotroski/Altman 數字）。不引入整包依賴（transitive deps 太重）。

## 11. PyPortfolioOpt（MIT）+ Riskfolio-Lib（BSD-3）— 組合層：分階段

- **PyPortfolioOpt**：精簡（cvxpy/sklearn/scipy，純 Python 無編譯）。`EfficientFrontier.max_sharpe()/min_volatility()`、`HRPOpt`、`CovarianceShrinkage.ledoit_wolf()`、`DiscreteAllocation`。吃 prices 或 returns。**易整合**。
- **Riskfolio-Lib**：risk-parity（ERC/HRP/HERC/NCO）+ ~35 風險度量（CVaR/CDaR…）最完整。但**重**：需 C++ 編譯（pybind11）+ astropy/statsmodels/arch hard-deps，Windows 裝要用預編 wheel。
- **判決（分階段、可抽換 `allocate(returns, method)->weights` adapter）**：**Phase 1** 先 equal-weight 基線 → 接 PyPortfolioOpt（MVO/max-Sharpe）；**Phase 2** 需要真 risk-parity/All-Weather 才加 Riskfolio（包 try/except ImportError 不破壞主路徑）。DuckDB returns → optimizer → `{ticker:weight}` → vectorbt `from_orders(size_type="targetpercent")`，handoff 與哪個 lib 無關。

## 12. CANSLIM 篩選器（python-canslim / CAN-SLIM-screener）— 兩個都別借碼

- **CAN-SLIM-screener（ssshah86, MIT）**：**vaporware**，只有 README 無程式碼。但 **README 是好的門檻 spec**（C 分級 20/30/50/70；A: EPS+25~50%/3Y、**ROE≥17%**；S: 突破量 +50~100%；**L: RS≥70（理想 80+/90+）**；I: ≥5 法人）。
- **python-canslim（KhoiUna, MIT）**：toy，silent `try/except`，**Macrotrends 已封鎖**（死資料層），只實作 C/A 部分、無 N/S/L/I/M。
- **判決**：**借碼價值≈0**；ssshah86 README 當門檻參考。**萃取**：**現在就能從 OHLCV 做** L/RS（**重用 Minervini 的 `rs_rating()`**，O'Neil 與 Minervini RS 同義）、N/新高、S/量（突破量≥1.5×SMA50）；**C/A/I 等 EDGAR 基本面**；**M=市場 regime gate**（接 [sentiment-and-market-analysis.md](sentiment-and-market-analysis.md) §B）。

## 13. VCP 偵測（stock-pattern / PKScreener / marketsmith）— 我們最大缺口，已有乾淨重寫 spec

- **PKScreener（MIT）的 `validateVCPMarkMinervini`（`ScreeningStatistics.py:7502`）是最佳參考**：Stage-2 趨勢 gate + **變動數量收縮** + **真正的量縮**（收縮量/上漲量<0.7，`:7642`）+ 突破量 pivot（量>1.2×近均、距高<10%）。另有 `validateVCP:7082`（嚴格固定 3 段，70% 收縮比數學乾淨可參考）+ 真實 cup-with-handle 偵測（`:3768`）。
- **stock-pattern（GPL）**：最易讀但 VCP 是**無量縮的 5 點 zigzag 啟發式**→ 只取「extrema walk」「C 突破失效重置」的**想法**（GPL 不複製碼）。
- **marketsmith（無授權）**：只是 IBD API client，**無演算法**，僅當 schema checklist。
- **判決**：**乾淨重寫 `strategy/rules/vcp.py`**，主要本於 MIT PKScreener Minervini 變體 + `validateVCP` 的 70% 收縮比數學，避開固定 3 段僵化與 RVM 當量縮的混淆。詳細偽碼 spec 已備（趨勢 gate→pivots→變動收縮→收緊 ratio≤0.75→higher lows→量縮<0.7→突破量 pivot→C-breach 重置→strength 評分）。當作 Minervini 規則的進場精修層。

