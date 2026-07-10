# 量化／交易策略資源盤點（Research Inventory）

> 蒐集日期：2026-06-14。目的：為 trading-analysis 軟體尋找「已被驗證過」的開源量化指標、量化分析、交易策略，作為往下開發的起始點。
> 本階段為**情報盤點**，尚未下載驗證。star 數為研究 agent 即時抓取或搜尋片段所得，**clone 時需再核對**。

---

> **資料源盤點(2026-07 補)**:本檔是「策略/repo」的情報盤點;**資料源**的完整盡職調查(70 源×7 類:日內/選擇權/下市股/新聞情緒/基本面/總經期貨/產業國際,含免費/<$5 判定與 PIT 品質)在 [refs/data-sources.md](refs/data-sources.md),決策版在 [docs/24](24-data-gaps-and-sources.md)。

## 摘要（最重要的三個發現）

1. **驚人的收斂訊號**：三條獨立的線索——「最可機械複現的策略」、「US Investing Championship 真實對帳冠軍實際用的方法」、「GitHub 上現有的開源篩選器」——**全部指向同一處**：**Minervini Trend Template（8 條規則）＋ O'Neil CAN SLIM 動能成長股**。這是強烈的「先做這個」訊號。
2. **AI/LLM 交易框架沒有任何一個有真實資金的長期實績**。回測窗口短、易有 look-ahead bias，作者自己都警告勿實盤。它們的價值是**架構參考**（尤其 `ai-hedge-fund` 的投資人 persona 設計、`TradingAgents` 的多代理辯論）。
3. **USIC 冠軍是最可信的訊號來源**，因為它是**真實券商對帳單驗證報酬**的比賽，不是紙上交易。冠軍方法 → 可複現規則 → 現成開源實作，這條鏈最值得優先投入。

---

## A. 成熟、已驗證的量化基礎設施（GitHub）

### A-1. 核心研究／回測（我們最該建立在其上）

| Repo | URL | ~Stars | 語言 | License | 狀態 | 為何可信 |
|---|---|---|---|---|---|---|
| **microsoft/qlib** | github.com/microsoft/qlib | ~44k | Python | MIT | 活躍 | AI 量化平台，內建 **Alpha158/Alpha360** 因子集 + 已發表 benchmark 排行榜（LightGBM/LSTM/Transformer）。進入「因子/ML 量化」最被驗證的路徑 |
| **vectorbt** | github.com/polakowo/vectorbt | ~7.9k | Python | Apache-2.0 + **Commons Clause** | 活躍(v1.0) | Numba 向量化回測，參數掃描最快。**我們已採用**。注意 Commons Clause（不可販售軟體本身）；vectorbt PRO 為閉源付費版 |
| **zipline-reloaded** | github.com/stefan-jansen/zipline-reloaded | ~1.8k | Python | Apache-2.0 | 活躍 | Quantopian Zipline 維護分支；**Pipeline API** 是美股橫截面因子研究的黃金標準（point-in-time、防倖存者偏差） |
| **TA-Lib (ta-lib-python)** | github.com/TA-Lib/ta-lib-python | ~12k | Cython | BSD-2 | 活躍 | 業界標準 C 核心，150+ 指標，最快最可信。**建議取代 pandas-ta** |
| **quantstats** | github.com/ranaroussi/quantstats | ~7.3k | Python | Apache-2.0 | 活躍 | 最普及的績效 tearsheet/指標庫，可直接吃 vectorbt 輸出 |
| **alphalens-reloaded / pyfolio-reloaded / empyrical** | github.com/stefan-jansen/* | ~0.6k 各 | Python | Apache-2.0 | 活躍 | 因子報酬/IC 分析、組合 tearsheet、底層風險指標。Apache-2.0 可安全內嵌 |

### A-2. 上線／實盤級引擎（未來路徑）

| Repo | ~Stars | 語言 | License | 備註 |
|---|---|---|---|---|
| **nautilus_trader** | ~23.5k | Rust+Python | LGPL-3.0 | 生產級、確定性事件驅動引擎，含股票。**未來實盤最佳成長標的**，LGPL 比 GPL 友善 |
| **freqtrade** | ~51k | Python | GPL-3.0 | 最久經考驗的開源實盤 bot（僅加密貨幣），含 FreqAI。GPL 對閉源產品是限制 |
| **QuantConnect Lean** | ~12k | C#/Python | Apache-2.0 | QuantConnect 雲端背後引擎，多資產、含實盤券商串接 |
| **backtesting.py** | ~8.5k | Python | **AGPL-3.0** | 小巧乾淨，但 AGPL 對閉源產品需注意 |

### A-3. 資料來源

| Repo | ~Stars | License | 備註 |
|---|---|---|---|
| **yfinance** | ~50k | Apache-2.0 | 免費美股日線預設來源（**我們已採用**）。非官方爬蟲，需包在 adapter 後面 |
| **akshare** | ~20k | MIT | 中國為主，覆蓋廣（未來台股/陸股可參考） |
| **OpenBB Platform** | ~69k | **AGPLv3** | 「Bloomberg-lite」資料聚合層，資料源整合強。AGPL 注意 |

### A-4. RL / ML

- **FinRL (AI4Finance)** ~15k, MIT — 最被引用的金融強化學習框架（research-grade，多為 notebook）。
- **stefan-jansen/machine-learning-for-trading** ~19k — 書的範例庫（~2021，非函式庫，挖技巧用）。

### A-5. 策展索引（必收藏）

- **wilsonfreitas/awesome-quant** ~27k — 量化領域的權威總索引。
- **wangzhe3224/awesome-systematic-trading** ~4.3k — 以程式碼品質為視角的系統交易策展。

### ⚠️ 重要警示

- **pandas-ta 原 repo（twopirllc）已被刪除**，PyPI 歷史被清空、社群信任崩壞。**勿採用**；改用 TA-Lib，或退而求其次用 `pandas-ta-classic` fork。（我們 MVP 最終自製 `ta_indicators.py`，此決策被驗證為正確。）
- **License 地雷**（若未來做閉源/再散布產品）：OpenBB、backtesting.py 為 **AGPL-3.0**；freqtrade 為 GPL-3.0；vectorbt 帶 **Commons Clause**。qlib / quantstats / alphalens / yfinance / TA-Lib / nautilus(LGPL) 較友善。

---

## B. AI / LLM 多代理交易框架 ＋ 近期（2025–2026）AI 打造的 repo

### B-1. 多代理 LLM 框架

| Repo | ~Stars | 重點 | 驗證程度 | 對我們的價值 |
|---|---|---|---|---|
| **TauricResearch/TradingAgents** | ~85k | 模擬交易公司：分析師→多空辯論→交易員→風控→基金經理，LangGraph 編排。多 LLM（GPT/Gemini/Claude/Grok/DeepSeek/Qwen/Ollama） | 有 arXiv 論文(2412.20138)；回測勝 5 個規則基準 **但僅 3 個月窗口、Sharpe 5–8 異常高、從未實盤、每次決策 11+ LLM 呼叫很貴** | **最佳架構參考**（多代理辯論設計）。非可直接用的策略 |
| **virattt/ai-hedge-fund** | ~60k | 19 代理：~14 個**投資人 persona**（Buffett/Graham/Munger/Lynch/**Burry**/Cathie Wood/Taleb/Ackman/Druckenmiller…）→ 風控 → 組合經理。含回測器 | 明確標示**教育用途、不碰真錢**；無實績/論文 | **最乾淨、最好讀的 persona 程式碼**，最適合 fork 當骨架。**直接呼應你問的 Burry/Buffett/Lynch 量化** |
| **HKUDS/AI-Trader** | ~19.7k | 港大資料科學實驗室，2025-10 建立。「100% 全自動 agent-native 交易」，比 TradingAgents 更模組化 | 機構出身可信、成長快；驗證待查 | **近期強力候選** |
| **AI4Finance/FinGPT** | ~20k | 開源金融 LLM（LoRA 微調做情緒/新聞） | 在情緒分析 benchmark 驗證，非 P&L | 當**情緒/NLP 元件**用，非端到端交易 |
| **AI4Finance/FinRobot** | ~7.3k | 疊在 FinGPT 上的金融 agent 平台（報告生成） | 定性驗證 | 研究自動化參考 |

### B-2. 近期 AI-built / "vibe-coded"（2025–2026）

| Repo | ~Stars | 建立 | 備註 |
|---|---|---|---|
| **NoFxAiOS/nofx** | ~12.5k | 2025-10 | **Go** 寫的 AI 交易終端助理（美股/期貨/外匯/加密）。高 star 但助理 ≠ 已驗證策略 |
| **tradermonty/claude-trading-skills** | ~1.9k | 2025-10 | **Claude Code skills** 給股票交易者：市場分析、技術線圖、篩選器、"Druckenmiller 策略合成器"。**直接命中「用 Claude Code 打造」的主題**。是工具包非回測系統 |
| **EthanAlgoX/LLM-TradeBot** | ~281 | 2025-12 | 多代理＋兩階段選股＋多標的回測 CLI＋HTML 權益曲線。認真但小／早期 |

### B-3. 範例 X 貼文（無法取得）

`x.com/yoshio_nocode/status/2064617130046452023` **無法擷取**（x.com 回 HTTP 402，所有 nitter/鏡像皆失敗）。
- 作者 **@yoshio_nocode = 「スモビジ開発ラボ」**，日本 **no-code / micro-SaaS 開發者**，教 Bubble、Google Antigravity 等快速做產品。
- 該貼文**很可能展示一個 no-code / AI 輔助打造的交易 app**（符合你的偏好），但**具體工具/repo/技術棧無法確認**。要取得需登入 X 或用瀏覽器 MCP。

### B-4. 成熟度判決

- **可信（值得研究/fork）**：① TradingAgents（唯一有論文+可複現回測，但窗口窄）② ai-hedge-fund（最乾淨的 persona 骨架，誠實標示教育用）③ HKUDS/AI-Trader（機構出身，需獨立驗證）。
- **元件級**：FinGPT（情緒）、FinRL（RL 環境）、FinRobot（報告）。
- **現實檢查**：**幾乎沒有任何一個有真實資金實績**。全部當**工程起始點**，不是已驗證的 alpha。最佳組合＝ai-hedge-fund 的結構 ＋ TradingAgents 的辯論設計 ＋ 我們自己嚴謹的 walk-forward 回測。

---

## C. 知名投資者策略「量化／可複現」程度

### C-1. 各家重點（含實際數字準則）

**① Mark Minervini — Trend Template & SEPA（高度可機械複現）**
- 風格：動能/成長，買確認進入 Stage 2 上升趨勢、盈餘加速的領導股，於低波動收斂（VCP）進場。
- **8 條 Trend Template 規則（純機械）**：
  1. 股價 > 150 日 SMA 且 > 200 日 SMA
  2. 150 日 SMA > 200 日 SMA
  3. 200 日 SMA 向上 ≥ 1 個月
  4. 50 日 SMA > 150 日 SMA > 200 日 SMA
  5. 股價 > 50 日 SMA
  6. 股價 ≥ 距 52 週低點 +30%
  7. 股價在 52 週高點的 25% 以內
  8. IBD 相對強度 RS Rating ≥ 70
- **可複現性缺口**：RS Rating 是 IBD 專有（百分位），開源都用近似（報酬排名或 63 日回歸斜率）。SEPA/VCP 進場點偏「藝術」。
- 實作：`RyanJHamby/stock-screener`、`icedevil2001/mark_minervini_stock_screener`(Streamlit)、`marco-hui-95/vcp_screener`、`douglasg-fintec/stocksscreener`、[github.com/topics/minervini](https://github.com/topics/minervini)

**② Joel Greenblatt — Magic Formula（完全可複現）**
- **精確公式**：ROC = EBIT/(淨營運資金+淨固定資產)；Earnings Yield = EBIT/EV（EV=市值+淨負債）。兩者各自排名 → 排名相加最低者買入（取 20–30 檔），排除金融/公用事業，市值 >$50M，持有 1 年。**零裁量**。
- 實作：`nblade66/MagicFormula`、`thobiast/magicformulabr`(巴西)、AAII screen #46、magicformulainvesting.com

**③ Warren Buffett — Quality+Value（已被學術量化）**
- **AQR「Buffett's Alpha」**(Frazzini/Kabiller/Pedersen, FAJ 2018)：Berkshire 的超額報酬在控制 **BAB(Betting-Against-Beta) + QMJ(Quality-Minus-Junk)** 與 ~1.7× 槓桿後變不顯著。
- **QMJ 因子**(Asness-Frazzini-Pedersen)：依 **獲利性/成長/安全/配息** 排名 → 多前 30%、空後 30%。這是 Buffett 的機械代理。
- 論文：[SSRN 3197185](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197185)、[QMJ SSRN 2312432](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2312432)（AQR.com 有資料集）。
- Buffett 式篩選：ROE>15% 持續、低負債、穩定毛利、owner earnings、FCF。

**④ Peter Lynch — GARP / PEG（中度可複現）**
- **PEG = P/E ÷ EPS 成長率 < 1.0**（理想 0.5）；股息調整 PEG = (成長+殖利率)÷P/E。
- **Lynch Fair Value** = PEG × 5 年成長 × EPS(TTM)，成長上限 25%、<5% 不算。
- 分類：快速成長(20–25%+)、穩健(10–20%)、慢速(>$1B 營收、殖利率≥3%)；負債/權益 <50–80%。
- 6 大類別歸類需裁量。實作：Validea/GuruFocus/AAII 有 Lynch 模型；GitHub 專屬 repo 少（PEG/GARP 極易自己寫）。

**⑤ Martin Schwartz「Pit Bull」— 技術短線（部分可複現）**
- **10 日 EMA 紅綠燈**：只在其上做多、其下做空（機械）。MACD 交叉、超買超賣震盪指標皆標準。
- **"Magic T"(Terry Laundry T-Theory)**：時間對稱理論，概念像規則但 T 的放置主觀，無公認公式。
- 結論：趨勢過濾器可寫；進場/時機偏裁量。無專屬 repo（10-EMA/MACD 各 TA 庫皆內建）。

**⑥ Michael Burry — 深度價值逆向（弱可複現）**
- 部分篩選：高 **FCF yield(>8–10%)**、低 P/B、正/成長 FCF、淨淨值(net-net) 類。但選題與宏觀時機純裁量，**無法規則化**。
- 複現法＝**追蹤 13F**：GuruFocus / Insider Monkey / stockcircle。注意 13F 落後 45 天、不含做空/選擇權/非美股，且 Burry 換手快 → 抄單不可靠。

**⑦ William O'Neil — CAN SLIM（多數可複現）**
- 7 條：**C** 當季 EPS +18–25% YoY；**A** 年 EPS 成長 ≥25%(3 年)、ROE~17%；**N** 新產品/新高(質化)；**S** 量能突破、低流通；**L** 領導股 **RS≥80**；**I** 法人持股上升；**M** 大盤確認上升(裁量)。C/A/L/S 機械，N/M 需判斷。
- AAII 長期追蹤 CAN SLIM 為其最佳篩選之一。實作：`fswzb/python_canslim`、`KhoiUna/python-canslim`、`ssshah86/CAN-SLIM-screener`

### C-2. 可複現性排名（建議由上而下實作）

| 排名 | 策略 | 可複現性 | 理由 |
|---|---|---|---|
| 1 | **Greenblatt Magic Formula** | 完全機械 | 兩條精確公式+排名相加，零裁量，多參考 repo |
| 2 | **Minervini Trend Template** | 高度機械 | 8 條明確 MA/RS 規則；僅 RS 需近似（VCP 進場是軟的部分） |
| 3 | **Buffett via QMJ+BAB** | 學術已量化 | 同儕審查因子（獲利/成長/安全/配息）+槓桿，可從 AQR 資料複現 |
| 4 | **CAN SLIM** | 多數機械 | C/A/L/S/I 為數值(RS≥80, EPS+25%)；N 與 M(大盤方向)需判斷 |
| 5 | **Peter Lynch GARP/PEG** | 中度機械 | PEG<1 與 Fair Value 精確，但 6 類別歸類質化 |
| 6 | **Martin Schwartz** | 部分可複現 | 10-EMA 過濾+MACD 可寫；Magic T 與進場裁量 |
| 7 | **Michael Burry** | 弱可複現 | 僅鬆散 FCF/P/B 篩選；選題+宏觀純裁量 → 13F 追蹤而非規則複現 |

### C-3. 擴充：量化金融數學地基 ＋ 更多投資者（2026-06-14 加查）

> 使用者補充的名單把研究**從「選股名人」升級到「量化金融的數學地基」**——Markowitz/Sharpe/Fama/Scholes 不只是投資人，他們**發明了量化工具本身**。這替我們的軟體新增兩個原 MVP 沒有的層：**因子層** 與 **組合/配置層**。

**第 0 層 — 數學地基（這些「就是」量化工具，100% 可實作）**

| 人物 | 量化產物（公式） | 可實作性 | Python 工具 |
|---|---|---|---|
| **Harry Markowitz** | MPT 均值變異最佳化（QP）：`min wᵀΣw` s.t. 報酬/權重限制；效率前緣、max-Sharpe、min-var | 高（教科書 QP） | **PyPortfolioOpt**、**riskfolio-lib**、cvxportfolio、skfolio |
| **William Sharpe** | CAPM `E[Rᵢ]=R_f+βᵢ(E[Rₘ]−R_f)`；β=Cov/Var；**Sharpe ratio** | 極高（幾乎免費） | quantstats、statsmodels |
| **Eugene Fama** | **Fama-French 3/5 因子**（Mkt, SMB, HML, RMW, CMA）+ Carhart 動能(UMD) | 高（資料是關鍵） | statsmodels + **Ken French Data Library**（`pandas_datareader`） |
| **Scholes/Merton** | Black-Scholes-Merton 選擇權定價、IV、Greeks | 高，但屬**選擇權**非選股 | py_vollib、QuantLib → **暫緩** |
| **Martin Leibowitz** | 債券 duration / immunization；後期 factor 配置 | 中（債券數學） | QuantLib → **對股票平台低用處，跳過** |
| **Robert Shiller** | **CAPE (PE10)** = 實質股價 / 10 年通膨調整 EPS 均值；均值回歸 | 高（一行 pandas） | pandas + shillerdata.com → **市場層級估值 overlay** |

> ⚠️ 更正：Leibowitz **非**諾貝爾獎得主；Markowitz/Sharpe/Fama/Shiller/Scholes/Merton 才是。

**第 1 層 — 完全可機械化的價值篩選**
- **Benjamin Graham**（史上最可複現、實證最強）：
  - **Graham Number** = √(22.5 × EPS × BVPS)，買進若 price < Graham Number
  - **Net-Net / NCAV**：price < ⅔ ×（流動資產 − 總負債）/股數；嚴格版 NNWC
  - **防禦型投資人 7 條**：營收門檻、流動比≥2、長債≤淨流動資產、10 年正盈餘、20 年連續股利、10 年 EPS 成長≥33%、P/E≤15 且 P/B≤1.5（P/E×P/B≤22.5）
  - **進取型投資人** 另有較寬鬆門檻
  - 實證：NCAV 股 1970–82 約 29.4%/年（Oppenheimer）；2026 RFE 研究(1969–2019)仍勝大盤。但多為微型、流動性差、現代美股 net-net 常 <10 檔
  - 實作：`JerBouma/FinanceToolkit`(~5k★, 含 Graham 指標)、`wlamont/securities-screener`、GrahamValue.com、GuruFocus NCAV、AAII screen #34
- （**Greenblatt Magic Formula** 已於 C-1，完全機械）

**第 2 層 — 可篩選的價值/全球**
- **John Templeton**：全球深度價值逆向（最大悲觀點）。可碼化成全球低 P/E + 低 P/B + 盈餘成長篩選；Stockopedia 有 Templeton GuruScreen。無單一公式、無知名專屬 repo（任何 value 因子庫即可建）。

**第 3 層 — 配置／被動層（可程式化，但屬「配置」非「選股」）**
- **John Bogle**：3-fund 組合、**age-based 債券%（= age 或 age−10/−20）**、成本篩選（依 TER/turnover 排序）、band 再平衡。→ **配置引擎 + 成本過濾**
- **Charles Ellis**（《Winning the Loser's Game》）：固定策略配置 + turnover 護欄 + 抑制行為性交易。→ **政策/限制層**
- **Jeremy Siegel**：基本面加權指數（股利加權 `w=D/ΣD` 或盈餘加權 `w=E/ΣE`，內含 value/股利傾斜）；Siegel constant 實質報酬 ~6.7% 當資本市場假設。⚠️ 2025 CFA 專論質疑其 out-of-sample 可靠性
- 衍生可程式化配置：**RAFI 基本面加權**（Arnott：sales/CF/book/dividends 複合，宣稱 ~2%/年超額，但部分是 value/size 因子重包裝）、**Risk Parity / All-Weather**（Dalio：等風險貢獻 `w∝1/σ`；零售靜態版 30%股/40%長債/15%中債/7.5%金/7.5%商品）
- Python：PyPortfolioOpt（含 HRP）、**riskfolio-lib**（risk parity 最完整：ERC/HRP/HERC）、skfolio、**bt**（再平衡回測）

**第 4 層 — 持股追蹤（非規則複現）**
- **Cathie Wood / ARK**：顛覆性創新主題成長股。選股邏輯裁量，但 **每日公布全持股**（比季度 13F 忠實太多）→ **最佳持股追蹤標的**；可近似成「高營收成長 + 高 R&D/營收」成長篩選。記錄 boom-bust（2020 暴漲、2021–22 重挫）
- （**Burry** — 13F 追蹤，已於 C-1）

**第 5 層 — 不可複現（純裁量）**
- **George Soros**：reflexivity / 全球宏觀 / 大方向押注。**無機械規則可碼化**；13F 只是殘缺代理（漏掉 FX/衍生品/做空）。誠實結論：不可複現為篩選器。

**對映我們架構的啟示**：原 MVP 只有「選股訊號 → 回測」。這次擴充清楚指出應補上**因子層**（Fama-French/QMJ，配 qlib）與**組合/配置層**（Markowitz 最佳化 / risk parity / Bogle 被動基線），形成完整的 **選股 → 因子評分 → 組合建構 → 配置基線 → 市場 regime overlay(CAPE)** 管線。

---

## D. US Investing Championship（USIC）歷年冠軍

### D-1. 背景
- **Norm Zadeh（Zada）1983 創辦**（作業研究 PhD，模糊邏輯之父 Lotfi Zadeh 之子），跑約 15 年後沉寂，**2019 復辦**。
- **核心可信點**：**真實資金、券商對帳單驗證報酬**，非紙上交易。依帳戶規模分組（股票 <$1M 組、$1M+ 組，另有選擇權/期貨組），全年最高報酬獲勝。

### D-2. 冠軍與策略

| 年 | 冠軍 | 報酬 | 風格 |
|---|---|---|---|
| 1984 | **Martin Schwartz** | 在年內 $25 萬→$100 萬+（資格賽常引 ~781%） | 裁量技術/選擇權當沖；《Pit Bull》 |
| 1985–90 | **David Ryan** | 3 次冠軍，約 ~161%/年 | 純 **O'Neil CAN SLIM** 成長股（O'Neil 門徒） |
| 1997 | **Mark Minervini** | **~155%**（僅約一半時間在場內） | **SEPA/VCP/Trend Template** 動能 |
| 2019 | Leif Soreide | +60.9%(股票組) | 成長動能（受 Minervini 影響） |
| 2020 | **Oliver Kell** | **+941.1%** | **Cycle of Price Action**（CAN SLIM 衍生） |
| 2020 | Ryan Pierpont | +448.4% | 成長動能/突破 |
| 2021 | **Mark Minervini**($1M+) | **+334.8%**（破紀錄） | SEPA/VCP |
| 2021 | Roy Mattox 等 | +214.4% 等 | 成長動能 |
| 2022 | Afzal Lokhandwala | +447% | 成長動能 |
| 2023 | Goverdhan Gajjala | **+805.1%** | 成長動能 |
| 2023 | **Marsten Parker** | +103.5%（最佳系統交易者） | **100% 系統化/演算法** |
| 2024 | J Law(港,$1M+) | **+353.9%**（破 $1M+ 紀錄） | 成長動能 |

> 注：2019 前數字（Schwartz/Ryan）文件較不精確，標為近似。

### D-3. 共同主線（已確認）
- 復辦後冠軍**壓倒性使用 O'Neil CAN SLIM / Minervini 式動能 + Stage 2 趨勢跟隨於高成長股**。
- **Minervini 的 MPA/Private Access 學生稱霸**：近 5 年有 3 年由其學生或本人奪冠；2024 年 79 位領先者中 27 位是其客戶。
- **例外**：**Marsten Parker**（純系統，含動能＋**均值回歸**＋IPO 突破系統；《Unknown Market Wizards》唯一純系統交易者，~20%/年、20+ 年僅 2 年虧損）；**Marty Schwartz**（裁量當沖/選擇權）。

### D-4. 可複現性（文件化程度）
- **Minervini** — 文件最佳。《Trade Like a Stock Market Wizard》《Think & Trade Like a Champion》。Trend Template = 8 條可寫規則。
- **Oliver Kell** —《Victory in Stock Trading》。**Cycle of Price Action = 6 個命名、可圖形化的型態**：Reversal Extension → Wedge Pop → EMA Crossback → Base n' Break → Exhaustion Extension → Wedge Drop，錨在 **10/21 EMA**（"Kell Channel"）。
- **Marsten Parker** — 規則公開於《Unknown Market Wizards》+訪談；**IPO 系統完全可規格化**（IPO<90 天、第 2 天起買新歷史高收盤、~20 檔、~20% 目標/~10% 移動停損，回測 ~17.8% CAGR、Sharpe ~1.42）。自建 RealTest 回測器。
- **現成 GitHub 實作（已驗證存在）**：
  - `starboi-63/growth-stock-screener` — 明確建於 **Minervini + Kell** Stage 2 準則，用 SEC EDGAR XBRL
  - `xang1234/stock-screener` — CAN SLIM + Minervini，80+ 過濾
  - `icedevil2001/mark_minervini_stock_screener` — Streamlit，8 條
  - `RyanJHamby/stock-screener` — 每日 Stage 2 掃描 + GitHub Actions 自動化

### D-5. 可複現性總結（排名）
1. **Minervini Trend Template** — 8 條純機械 MA/RS，已有多個可用 Python 篩選器。最高保真。
2. **Marsten Parker IPO/動能系統** — 明確機械、參數與回測已公開，本就為了寫程式設計。
3. **CAN SLIM (Ryan)** — 數值門檻可寫；領導股/大盤方向需判斷。
4. **Oliver Kell Cycle of Price Action** — 6 型態可定義於 10/21 EMA，但進場偏型態裁量；適合做篩選非全自動進場。
5. **Minervini VCP** — 演算法可辨識（收斂計數、量縮）但 pivot 主觀；中保真。
6. **Marty Schwartz** — 裁量盤中/選擇權，**不實際可複現**為篩選器。

> **重大警示**：驗證報酬證明的是**交易者**，不代表機械複製能重現報酬（倉位管理、市場時機、裁量貢獻了大部分 edge）。

---

## E. 綜合建議：對 trading-analysis 的下一步

### E-1. 三條線索的收斂 → 優先順序
「最可複現」∩「真實冠軍實際在用」∩「已有開源實作」＝
1. **Minervini Trend Template（8 條）** ← 第一個要做的新策略
2. **CAN SLIM 數值門檻**（C/A/L/S/I）
3. **Magic Formula**（純基本面、與上面動能策略互補，可做「價值對照組」）
4. **Buffett QMJ 因子**（學術級，進入因子分析的橋樑，配 qlib）

### E-2. 對映到現有架構
我們的 `src/trading_analysis/strategy/rules/` 已有 `kronos_trend.py` 與 `sma_crossover.py`，可平行新增：
- `minervini_trend.py`（8 條規則；RS Rating 用 63 日回歸斜率 vs SPY 近似）
- `magic_formula.py`（需基本面資料源：EBIT/EV/淨營運資金 → 觸發 V1 的 fundamentals connector）
- `canslim.py`（EPS/營收成長 + RS + 量能）
- 未來 `qmj_factor.py`（接 qlib / AQR 因子）

### E-3. 建議優先下載研究的 repo（shortlist）
- **策略複現**：`starboi-63/growth-stock-screener`（Minervini+Kell，最對味）、`xang1234/stock-screener`（CANSLIM+Minervini）、`nblade66/MagicFormula`
- **架構參考**：`virattt/ai-hedge-fund`（persona 骨架，呼應 Burry/Buffett/Lynch）、`TauricResearch/TradingAgents`（多代理辯論）
- **因子量化路徑**：`microsoft/qlib`（Alpha158/360）
- **指標/績效**：`TA-Lib`、`quantstats`、`alphalens-reloaded`

### E-4. 必記的現實檢查
- AI 框架無真實實績 → 只當骨架，務必自己做嚴謹 walk-forward 回測。
- RS Rating 是 IBD 專有 → 開源都近似，輸出會與官方不同，clone 時先查其 RS 實作。
- License：閉源/再散布前避開 AGPL（OpenBB、backtesting.py）與 Commons Clause（vectorbt 販售）。
- 報酬數字／star 數為研究階段所得，下載時務必再核對。
