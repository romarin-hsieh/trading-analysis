# trading-analysis 研究總報告（Executive Summary）

> 日期：2026-06-14。本檔是三輪研究的**單一進入點與總索引**；各主題的細節在連結的專文。
> 範圍：量化策略/指標、知名投資者量化、開源 repo 盤點與 code-level 評估、資料源、回測嚴謹度、與既有 dashboard 的整合架構。

## 文件地圖
| 主題 | 文件 |
|---|---|
| ★ **執行依據：Master 實作計畫**（M0-M7、契約、CI、第一個 PR）| [01-implementation-plan.md](01-implementation-plan.md) |
| 計畫生成輸入 BRIEF | [design-brief.md](design-brief.md) |
| 策略與投資者量化、USIC 冠軍 | [research-inventory.md](research-inventory.md) |
| 8 個 repo 的 code-level 評估＋萃取 | [repo-evaluation.md](repo-evaluation.md) |
| 台股/美股基本面資料源、回測嚴謹度 scorecard | [data-and-backtest-rigor.md](data-and-backtest-rigor.md) |
| 多 repo + dashboard 整合（含契約與 Phase-3 真相） | [architecture-integration.md](architecture-integration.md) |
| 情緒面（新聞/社群/模型）+ 市場面（regime/廣度/總經） | [sentiment-and-market-analysis.md](sentiment-and-market-analysis.md) |
| 攝取/輿論 pipeline + 爬蟲 + 排程 + <$15/月 成本 | [ingestion-pipeline.md](ingestion-pipeline.md) |
| 多 repo 切分決策（我的評估）+ repos 結構提案 | [architecture-decision-multirepo.md](architecture-decision-multirepo.md) |
| 另類資料訊號 + 事件/輿論內容擴充（補缺口）| [alt-data-and-content-expansion.md](alt-data-and-content-expansion.md) |
| **萃取待辦：gap repo → 我們的模組（build backlog）** | [extraction-backlog.md](extraction-backlog.md) |
| 爬蟲技術選型 | [tech-selection-scraping-tools.md](tech-selection-scraping-tools.md) |
| **參考資料索引（repos/articles/videos，版本戳記）** | [refs/README.md](refs/README.md) |

---

## 0. 一頁總結（TL;DR）

1. **收斂訊號**：「最可機械複現的策略」∩「USIC 真實對帳冠軍實際在用」∩「已有開源實作」＝ **Minervini Trend Template（8 條）＋ O'Neil CAN SLIM 動能成長股**。先做這個。
2. **trading-analysis 的定位**：多 repo 架構中的**策略/量化引擎**，輸出 JSON 餵給既有的 `investment-dashboard`。
3. **Smoking gun**：dashboard 既有 Phase-3 **進場訊號自家驗證判定「Toxic Alpha, DO NOT DEPLOY」**（選到輸家），且**完全沒有 RS/trend template/基本面**——正是我們要補的。→ **整合採 AUGMENT**：保留其 comet 視覺化與**唯一有 edge 的 ATR/Chandelier 出場**，由我們提供進場訊號。
4. **資料關鍵缺口**：我們 DuckStore 只有 OHLCV，**沒有基本面**。美股用 **SEC EDGAR（point-in-time）** 補，是解鎖 Magic Formula/Graham/QMJ 的前置。
5. **AI/Kronos 現實檢查**：所有 AI/LLM 交易框架與 Kronos 的 headline 數字**都禁不起嚴格回測檢驗**；當架構骨架/選配，不當已驗證 alpha。規則式核心優先。
6. **授權**：8 個參考 repo 授權全部寬鬆（MIT/Apache-2.0），無 copyleft 污染（唯 AI-Trader 缺 LICENSE 檔 → 勿複製碼）。

---

## 1. 策略與投資者量化（細節見 research-inventory.md）

**可複現性排名（由高到低，建議實作順序）**：
1. **Greenblatt Magic Formula** — 完全機械（ROC + Earnings Yield 排名）
2. **Minervini Trend Template** — 8 條 MA/RS 規則（RS 用近似）
3. **Buffett → QMJ + BAB** — AQR 學術量化（獲利/成長/安全/配息因子）
4. **CAN SLIM** — C/A/L/S/I 數值化（N/M 需判斷）
5. **Peter Lynch GARP/PEG**、6. **Schwartz**（10-EMA 可寫、進場裁量）、7. **Burry**（弱，只能追 13F）

**擴充投資者（數學地基）**：Markowitz（均值變異最佳化）、Sharpe（Sharpe ratio/CAPM）、Fama（Fama-French 因子）、Graham（Graham Number/Net-Net）、Bogle/Siegel（被動/基本面加權配置）、Shiller（CAPE）、Cathie Wood（每日持股可追蹤）、Soros（不可複現）。→ 新增**因子層**與**組合/配置層**。

**USIC 冠軍收斂**：真實對帳報酬比賽，現代冠軍（Minervini 1997/2021、Oliver Kell 2020 +941%、David Ryan、Marsten Parker 系統化）**壓倒性使用 CAN SLIM/Minervini 動能**。這是最可信的訊號來源。

---

## 2. 開源 repo 評估（細節見 repo-evaluation.md）

8 個已 clone 於 `../_ref_repos/`，授權全寬鬆。

| Repo | 判決 | 取用 |
|---|---|---|
| **xang1234/stock-screener** | Apache-2.0，Claude 打造的認真全棧，380+ 測試 | **最佳規格金礦**：Minervini 加權版、Pocket Pivot、criteria 組合模式 |
| growth-stock-screener | MIT，規格好碼別跑（爬蟲脆） | **RS Rating 公式** |
| MagicFormula | MIT，公式對水管爛 | ROC/EY/排名三公式 |
| **ai-hedge-fund** | MIT，邏輯有真材實料 | **V1 LLM persona 模式捐贈者**（Buffett/Burry/Lynch/Graham 計算 + `call_llm` Ollama 一等公民） |
| TradingAgents | Apache-2.0 | 多空辯論+Ollama辯手/雲端裁判+round cap 當預算 |
| qlib | MIT | 採櫻桃 Alpha158 因子表達式（~20 運算子≈pandas rolling）；別整合 wholesale |
| Kronos | MIT | **選配 plug-in 非主引擎**（見 §4） |
| HKUDS/AI-Trader | ⚠️無 LICENSE | **跳過**（其實是社交跟單 SaaS，無回測） |

---

## 3. 資料源（細節見 data-and-backtest-rigor.md）

- **美股基本面（關鍵缺口）**：主用 **SEC EDGAR companyfacts**（免費、權威、**point-in-time 有 filed 申報日**→避免 look-ahead）；FMP/yfinance 當便利 fallback 絕不當回測真相；simfin bulk seed；FinanceToolkit(MIT) 算 Graham/Piotroski/QMJ。DuckDB 存 `as_of=filed_date`，查詢永遠 `filter as_of<=sim_date`。
- **台股（V2）**：主用 **FinMind**（免費、唯一同時涵蓋價格+基本面+**三大法人籌碼**）。Minervini/CANSLIM 可移植但需：自算 RS、union TWSE+TPEX、流動性過濾、處理 ±10% 漲跌停不可成交、用調整後價、加投信買超/月營收訊號。

---

## 4. Kronos 判決

MIT、我們 wrapper 已驗證相容（唯一修：mini 配 `Kronos-Tokenizer-2k`）。但「93% RankIC」是**相對 rank-IC 提升非報酬**，扣成本恐無價值；repo 回測僅單一 11 月窗口、無第三方重現；獨立評論：「研究方向非 production alpha 引擎」。**判決：選配次要訊號**（如預測隱含期望漲幅做進場/停損 sizing，或合成 K 線做回測壓測），**別凌駕已驗證的規則式核心**。

---

## 5. 回測嚴謹度 Scorecard（細節見 data-and-backtest-rigor.md）

10 點：look-ahead、倖存者偏差、train/val/test、walk-forward、**Deflated Sharpe**、成本/滑點、台股±10%限制、regime 穩健、data-snooping、可重現。**#1/#2/#5/#6/#7 任一 Fail = 不信任報酬**。所有 AI 框架與 Kronos headline 都過不了。我們自己的策略上線前也要過這關。

---

## 6. dashboard 整合（細節見 architecture-integration.md）

**既有 investment-dashboard**：成熟 production（Vue 3 靜態站、GitHub Pages、零 backend），已有每日 ETL（OHLCV+Dataroma 13F+Phase-3 量化引擎）+ 招牌 3D comet 視覺化。

**目標多 repo 架構**：`trading-analysis`（策略引擎，輸出 JSON）→ `trading-data`（待建 ETL repo，GitHub Action 定期抓資料+呼叫我們算訊號+commit JSON）→ `investment-dashboard`（純前端讀 CDN）。跨語言用 JSON 解耦。

**整合決策：AUGMENT**（證據導向）：
- 既有進場訊號自驗失敗（Toxic Alpha）→ 由我們的 Minervini/RS/因子**補進場**。
- 既有 **ATR/Chandelier 出場是唯一有 edge 的**→ **重用當出場層**。
- 既有 **comet coordinates/trace 是招牌 UI**→ 保留。
- 我們的訊號當**新平行欄位**（每 entry 加 `scores{}`）或 sibling JSON，**零回歸**（`dashboard_status.json` 無 Zod、新增欄位向後相容）。

**資料契約**：`dashboard_status.json` = `{meta,updated_at,global_regime,data[]}`，每 entry 必含 `ticker/sector/strategy/signal/reason/commentary/price/change_percent/date/coordinates{x_trend,y_momentum,z_structure}/trace[30]/sector_trace[30]`。`api.py` 需加 `export_dashboard_json()`。

---

## 7. 統一建置路線圖

| 階段 | 內容 | 新資料 |
|---|---|---|
| 1 | `strategy/rules/minervini_trend.py`（8 條 + `rs_rating()`） | 無（現有 OHLCV） |
| 1b | **市場 regime gate**（複合 global_regime：趨勢+O'Neil 分布/跟進日+廣度）= CANSLIM「M」 | 無（指數+universe） |
| 1c | `vcp.py` 進場精修（本於 PKScreener MIT Minervini 變體；收縮+量縮+突破 pivot） | 無 |
| 2 | DuckStore 加 **fundamentals**（SEC EDGAR point-in-time）+ schema + 連接器 | 基本面 |
| 3 | `magic_formula.py` + `graham.py`（自寫標準定義；lift FinanceToolkit 的 Piotroski/Altman） | 用階段 2 |
| 3b | `canslim.py`（L/RS+N+S 現可做；C/A/I 待基本面；M 用 1b） | 部分基本面 |
| 4 | `factors/`（qlib Alpha158 移植 + 自建 Fama-French/QMJ）+ vectorbt IC 分析 | 部分基本面 |
| 5 | 整合 adapter：`api.export_dashboard_json()` 對齊 dashboard 契約（先 additive 驗證） | — |
| 6 | 組合/配置層：equal-weight → **PyPortfolioOpt**（Phase1）→ Riskfolio（Phase2 risk-parity）+ Shiller CAPE overlay | — |
| 7 | **情緒面**：Alpha Vantage/Finnhub 新聞 + FinBERT(本地) + 市場情緒指數(F&G/VIX/put-call)，point-in-time 存 DuckDB | 新聞/情緒 |
| 8 | V1 LLM persona 層（ai-hedge-fund 模板 + TradingAgents 辯論；Ollama 辯手/雲端裁判） | 用階段 7 |
| 9（V2） | 台股（FinMind 價格+基本面+籌碼）+ trading-data ETL repo 抽出 + dashboard 改讀外部 CDN | 台股 |

每階段策略上線前過 §5 scorecard。

---

## 8. 待決策 / 開放問題
- **取代 vs 平行**已定 AUGMENT；但「最終是否逐步淘汰既有 Phase-3 進場訊號、全面改用我們的」可日後 A/B 後再定。
- trading-data ETL repo 的建立時機（V2 才抽，或更早）。
- LLM 預算與雲端供應商（V1 才需要）。
- 台股是否要拉到更前面（目前排 V2）。

## 附錄：參考 repo 位置
`C:\Users\Romarin\Documents\Software Projects\_ref_repos\`（8 個 shallow clone：growth-stock-screener、stock-screener、MagicFormula、ai-hedge-fund、TradingAgents、qlib、Kronos、AI-Trader）。不在我們 git 內，研究完可刪。
