# REF：GitHub Repos

> 版本＝git commit SHA。深度評估見 [../repo-evaluation.md](../repo-evaluation.md)。程度分級見 [README.md](README.md)。
> 比對更新：`git -C _ref_repos/<name> fetch && git rev-parse origin/HEAD`，與下方 SHA 比。

## A. 已 clone 研讀（16，位於 `../_ref_repos/`，clone 日 2026-06-14）

| Repo | 版本 (sha · commit date) | 授權 | 裡面有什麼 | 程度 | 採用/不採用原因 |
|---|---|---|---|---|---|
| **xang1234/stock-screener** | `6dd83f2` · 2026-06-13 | Apache-2.0 | Claude 打造全棧篩選器：Minervini 加權版、Pocket Pivot/Power Trend、CANSLIM、StockBee 廣度、RRG、criteria 組合模式、380+ 測試 | 🟡採用-萃取 | 最佳規格金礦；萃取門檻+組合模式。其 RS 非真 IBD、VCP 是 stub |
| **PKScreener** | `35bd3f6` · 2026-06-02 | MIT | VCP（`validateVCPMarkMinervini`，真量縮）+ cup&handle 偵測 + RS；印度為主 | 🟡採用-萃取 | **VCP 最佳參考**，乾淨重寫 `vcp.py` |
| **growth-stock-screener** | `4ba4c9f` · 2024-12-21 | MIT | Minervini+Kell stage-2、**RS Rating 公式**、SEC EDGAR 營收 | 🟡採用-萃取 | 萃取 RS 公式；Selenium 爬蟲脆，別跑 |
| **MagicFormula** | `c9f6e79` · 2024-02-13 | MIT | Greenblatt ROC/Earnings-Yield/排名相加 | 🟡採用-萃取 | 萃取三公式；依賴已棄置 yahoofinancials |
| **FinanceToolkit** | `6d15f61` · 2026-06-11 | MIT | 150+ 比率：Piotroski F、Altman Z、profitability/solvency；可吃自有 DataFrame | 🟡採用-萃取 | **lift Piotroski+Altman**；其 Magic Formula/Graham 定義錯→自寫；當測試 oracle |
| **PyPortfolioOpt** | `c524c6e` · 2026-03-10 | MIT | MVO、max-Sharpe、min-vol、HRP、Ledoit-Wolf shrinkage、DiscreteAllocation | 🟢採用-核心 | 組合層 Phase 1 主用（純 Python 易裝） |
| **ai-hedge-fund** | `2f0ba33` · 2026-06-09 | MIT | 19 投資人 persona 代理（Buffett/Burry/Lynch/Graham…）、`call_llm`（Ollama 一等）、deterministic analyze→thin LLM | 🔵參考-架構 | **V1 LLM persona 最佳模式捐贈者**；backtester 太慢別用 |
| **TradingAgents** | `04f434e` · 2026-06-01 | Apache-2.0 | LangGraph 多空辯論+裁判、多 LLM、structured→freetext fallback | 🔵參考-架構 | 借對抗+Ollama 辯手/雲端裁判+round cap 當預算；辯論預設僅 1 輪 |
| **qlib** | `d5379c5` · 2026-04-22 | MIT | Alpha158/360 因子表達式引擎（~20 運算子≈pandas rolling）、ML benchmark | 🟡採用-萃取 | 採櫻桃 Alpha158 因子字串；別整合 wholesale（.bin 格式/China-centric） |
| **Kronos** | `67b630e` · 2026-04-13 | MIT | OHLCV 基礎模型（BSQ tokenizer + decoder Transformer），mini~large | 🔵參考-選配 | 選配次要訊號；「93% RankIC」是相對非報酬、單窗口無重現 |
| **stock-pattern** | `85c710d` · 2025-12-02 | **GPL-3.0** | 型態偵測（H&S/雙頂底/三角/VCP/harmonic），最易讀 | 🔵參考-想法 | **GPL 不取碼**；VCP 是無量縮 5 點 zigzag，僅取 extrema/breach-reset 想法 |
| **Riskfolio-Lib** | `c732799` · 2026-06-03 | BSD-3 | risk-parity（ERC/HRP/HERC/NCO）+ ~35 風險度量（CVaR/CDaR） | ⚪僅情報→Phase 2 | 需 risk-parity 才上；重（C++/pybind11/astropy，Windows 用 wheel） |
| **marketsmith_pattern_recognition** | `cc56513` · 2024-01-06 | 無授權 | IBD MarketSmith API client（7 種 base，杯柄 schema） | ⚪僅情報 | 無演算法、需付費帳號；只當 schema checklist |
| **python-canslim** | `233903a` · 2024-03-20 | MIT | CANSLIM C/A（Macrotrends 爬，**已被封**） | 🔴不採用 | toy（silent try/except）+死資料層；僅借 C 公式形狀 |
| **CAN-SLIM-screener** | `d0a2e40` · 2019-05-08 | MIT | 只有 README（O'Neil 門檻 spec） | 🔴不採用（留 spec） | vaporware 零程式碼；README 當門檻參考（C 20/30/50/70、RS≥70、ROE≥17%、≥5 法人） |
| **HKUDS/AI-Trader** | `d03ff6c` · 2026-06-11 | ⚠️**無 LICENSE 檔** | 社交/跟單 SaaS 平台（非 agent 推理框架），FastAPI+Postgres | 🔴不採用 | 無回測、無 LICENSE、推理在外部 agent；與需求不符 |

## B. 評估但未 clone（web 研究，依 [../research-inventory.md](../research-inventory.md)）

| 來源 | 程度 | 一句話 |
|---|---|---|
| **vectorbt** | 🟢採用-核心 | 已是回測引擎 dependency（Commons Clause 只限販售，對我們無感） |
| **DuckDB / yfinance** | 🟢採用-核心 | 已是儲存/行情 dependency |
| **FinMind**（台股） | 🟢採用-核心(V2) | 台股價格+基本面+籌碼，V2 主用 |
| **FinBERT (ProsusAI)** | 🟡採用-萃取 | 情緒模型本地跑（CPU）；授權待確認 |
| **quantstats / alphalens-reloaded** | 🟡採用-萃取 | 績效 tearsheet / 因子 IC 分析，計畫用 |
| **TA-Lib** | ⚪僅情報 | 指標庫；MVP 已自製 `ta_indicators.py`，需要再上 |
| **ML4T (stefan-jansen)** | 🔵參考-架構 | 因子建構教材（~19k★） |
| **zipline-reloaded / bt** | ⚪僅情報 | 因子 Pipeline / 組合再平衡回測，未來選配 |
| **nautilus_trader** | ⚪僅情報 | 未來實盤級引擎（LGPL） |
| **OpenBB** | 🔴不採用 | AGPL-3.0，資料聚合層；僅情報，勿複製碼 |
| **freqtrade / FinRL / FinGPT/FinRobot** | ⚪僅情報 | crypto bot / RL / 金融 LLM；元件級參考 |
| **pandas-ta（原 twopirllc）** | 🔴不採用 | 原 repo 已被刪除、PyPI 史被清；改 TA-Lib |
| **awesome-quant / awesome-ai-in-finance** | ⚪索引 | 策展索引，發現用 |

## C. 廣度 GitHub sweep（2026-06-14；GitHub API topic 掃描 + 文章 roundup）

**搜尋框架（套用中）**：⭐stars · 🍴forks · 📈star velocity（近期建立卻高星=上升）· 🔧維護（last push）· ⚖️寬鬆授權 · 🎯補缺口。Tier S=clone 研讀 / A=知道 / B=僅記錄。
> ⚠️ `gh` 未認證（keyring 失敗）；改用**未認證 GitHub Search API** 取得權威星/叉/授權/last-push 數據。要做「近期上升趨勢」的精準掃描需 `gh auth login`（可協助設定）。

**Tier S — 已 clone 待研讀（補我們的 feature-eng / ML / 微結構缺口）**
| Repo | ~★ | 授權 | 裡面有什麼 | 為何 |
|---|---|---|---|---|
| **letianzj/QuantResearch** | 2.9k | MIT | 27 notebooks：backtest（組合opt/VaR/pairs）+ ML（**Kalman/HMM regime/GARCH/PCA/GMM**）+ Fama-French | 直接可用的**特徵工程+regime偵測**，我們缺 |
| **jo-cho/Technical_Analysis_and_Feature_Engineering** | ~200 | — | 80+ 技術指標 + **meta-labeling + MDI 特徵重要性**（建於 de Prado/Jansen） | 正中**特徵工程缺口** |
| **mfrdixon/ML_Finance_Codes** | 2.6k | MIT | 《ML in Finance》(Dixon) 官方碼：機率建模/GP/NN/**可解釋性/序列模型/RL** | **機構級 ML pipeline** 參考 |
| **je-suis-tm/quant-trading** | 10.1k | Apache-2.0 | ~20 策略**含回測**（MACD/Bollinger/SAR/Heikin-Ashi/Dual Thrust/pairs/Monte Carlo） | 策略+訊號 pattern 金礦 |

**Tier A — 知道/參考（高價值，暫不 clone）**
| Repo | ~★ | 授權 | 一句話 |
|---|---|---|---|
| **vnpy/vnpy** | 41.6k | MIT | 主流事件驅動量化交易平台（含實盤）；架構參考 |
| **HKUDS/Vibe-Trading** | 12.1k | MIT | 港大同實驗室（AI-Trader）新作，2026 上升中的 AI 交易 |
| **goldmansachs/gs-quant** | 10.6k | Apache-2.0 | 機構級風險/衍生品/情境分析（部分需 Marquee key） |
| **nkaz001/hftbacktest** | 4.1k | MIT | HFT/微結構回測（Python/Rust）；補 HFT 缺口 |
| **VisualHFT** | 1.1k | Apache-2.0 | 微結構視覺化（C#）；萃取 **VPIN/LOB imbalance** 公式（非移植 app） |
| **man-group/ArcticDB** | 2.4k | BSL-1.1 | 大規模時序 DataFrame DB（版本/time-travel）；資料量大才用，注意授權 |
| **firmai/financial-machine-learning** | 8.6k | — | ML-finance awesome 索引（發現更多 repo 用） |
| **paperswithbacktest/awesome-systematic-trading** | 8.4k | — | 系統交易策展 + 資料集/回測角度 |
| **robertmartin8/MachineLearningStocks** | 1.95k | MIT | PyPortfolioOpt 作者的 ML 選股教學 |
| **LastAncientOne/Stock_Analysis_For_Quant** | 2k | MIT | 大量 quant 分析合集 |
| **TradeMaster-NTU/TradeMaster** | 0.5k | Apache-2.0 | RL 量化平台 + PRUDEX 評測（與 FinRL 重疊） |

**Tier A（華語/A 股平台，TW/中文相關，多為 A 股）**：`bbfamily/abu`(17.4k,GPL)、`UFund-Me/Qbot`(17.6k,MIT)、`yutiansut/QUANTAXIS`(10.7k)、`myhhub/stock`(12.9k,Apache)、`zvtvz/zvt`(4.2k,MIT)、`akfamily/akshare`(20.3k,已知)。

**Tier B — 僅記錄**：`jpmorganchase/python-training`(13.5k, 教育)、`SparkAbhi/SignalProcessingWithPython`(32, 太泛)、`StockSharp`(C#)、`askmike/gekko`(stale)、`hummingbot`(18.9k, crypto MM)、`man-group` 之外的 C#/Go 平台。
**⚠️ 待查異常**：`ZhuLinsen/daily_stock_analysis`(42.5k★/**40k forks** — fork 數異常高，疑為「fork 即用」模板，實質待驗)、`RyanCodrai/turbovec`(11.4k, 疑 quant topic 誤標)。

**爬蟲工具評估**：見 [../tech-selection-scraping-tools.md](../tech-selection-scraping-tools.md)（Agent 產出）。重點：**最大缺口＝文章正文抽取 → 採 `trafilatura`**（F1 最高、原生 Markdown+publish-date）；`Scrapling`(63.6k) 一包含 curl_cffi+Camoufox+Turnstile；**Playwright 已安裝**（價值＝網路控制/request 攔截，放家機驅動 Camoufox）。

## D. 另類資料 / 事件 / 輿論來源 repos（2026-06-14；詳見 [../alt-data-and-content-expansion.md](../alt-data-and-content-expansion.md)）

| Repo | ~★ | 授權 | 用途 | 程度 |
|---|---|---|---|---|
| **dgunning/edgartools** | 2.3k | MIT | SEC 8-K/Form4/10-K/XBRL 解析，best-in-class | 🟡採用（事件+內部人骨幹）|
| **EarningsCall/earningscall-python** | 31 | MIT | 法說逐字稿 client | 🟡採用 |
| **timothycarambat/senate-stock-watcher-data**(+house) | — | — | **免費國會交易 JSON**（非 QuiverQuant 付費）| 🟡採用 |
| **aladinbouddat/PEAD-Strategy** | — | — | PEAD long-short 回測參考 | 🔵參考 |
| **Matteo-Ferrara/gex-tracker** | 196 | — | CBOE GEX 計算（Phase 2 指數 regime）| 🔵參考 |
| **GeneralMills/pytrends** | 3k | Apache-2.0 | Google Trends（Wikipedia pageviews 更適回測）| ⚪→LOW |
| **SYSTRAN/faster-whisper** | 23.6k | MIT | podcast/無字幕影片轉錄 | 🟡採用 |
| jadchaar/sec-edgar-downloader | 703 | MIT | EDGAR bulk 下載（edgartools 更佳）| ⚪ |
| sd3v/openinsiderData | 83 | 無 | Form4 scraper（用 EDGAR 自解更佳）| ⚪ |
| jwlin/ptt-web-crawler | 450 | MIT | 台股 PTT 爬蟲 | ⚪→P2 |

**topic-sweep 額外 notable**：
| Repo | ~★ | 授權 | 一句話 | 程度 |
|---|---|---|---|---|
| **JerBouma/FinanceDatabase** | 7.9k | MIT | 300k+ 金融商品 symbol/分類 DB | 🟡採用（universe 建構）|
| **hugo2046/QuantsPlaybook** | 5.3k | — | 量化策略 playbook（中文，含因子/擇時）| 🔵參考 |
| **tradytics/surpriver** | 1.9k | GPL | 用 volume/另類資料盤前找異常股 | 🔵參考-想法（GPL）|
| klinecharts/KLineChart | 3.9k | Apache-2.0 | 輕量 K 線圖表庫（dashboard 視覺選配）| ⚪ |
| ValueCell-ai/valuecell | 10.8k | Apache-2.0 | 2026 新、AI agent 投資平台 | ⚪待查 |
| huseinzol05/Stock-Prediction-Models | 9.4k | Apache-2.0 | 多種預測模型合集（stale 2023）| ⚪ |
| shashankvemuri/Finance | 3.9k | MIT | 150+ 金融分析腳本 | ⚪ |

_最後更新：2026-06-14_
