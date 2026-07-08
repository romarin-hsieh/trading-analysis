# trading-analysis 研究總報告（Executive Summary）

> 更新：2026-07-08。本檔是**單一進入點與總索引**；細節在連結的專文。**現行機制判定以 [docs/18 註冊表](18-strategy-registry.md) 為單一事實來源**。
> **兩部分**：第一部分（規劃/盤點，2026-06-14，§0-§8）＋ **第二部分（實證研究結論，2026-06~07，§E0-E9，docs 05-21）**。
> 範圍：量化策略/repo/資料源/整合（第一部分）＋ 真實回測、因子搜尋、另類資料、嚴謹度證偽（第二部分）。

## 文件地圖
| 主題 | 文件 |
|---|---|
| **★ 實證研究（讀這個）：回測 postmortem（17 錯誤+三輪自我修正）** | [05-backtest-postmortem.md](05-backtest-postmortem.md) |
| **自主因子搜尋：適應度函數下的前沿（Grinold 上限）** | [06-factor-search-frontier.md](06-factor-search-frontier.md) |
| **產業策略（5+ 可重現）+ 50-100% 目標的 Calmar 證明** | [07-industry-strategies.md](07-industry-strategies.md) |
| **推薦策略（唯一通過嚴謹閘門、顯著 alpha 的多 sleeve 組合）** | [08-recommended-strategy.md](08-recommended-strategy.md) |
| **方法論：樣本盤點 + 因子確定閘門 + regime 切換** | [09-methodology-and-factor-gate.md](09-methodology-and-factor-gate.md) |
| **另類資料 ingestion（EDGAR 基本面 + insider）+ 品質因子發現** | [10-alt-data-ingestion.md](10-alt-data-ingestion.md) |
| 投資組合對抗審查（O5） | [04-portfolio-review.md](04-portfolio-review.md) |
| **換資料維度：突破 Grinold 上限的具體項目與優先序** | [11-data-dimensions.md](11-data-dimensions.md) |
| **量化方法地圖（Kalman/GARCH/HRP/de Prado…）+ 實作示範** | [12-quant-methods-survey.md](12-quant-methods-survey.md) |
| **Algotrading 策略目錄（Reddit/論壇/論文/評論廣搜）+ 對照已驗證** | [13-strategy-catalog.md](13-strategy-catalog.md) |
| 六槽位框架+全面復盤+判斷依據（2026-06 快照） | [14-horizon-framework.md](14-horizon-framework.md) |
| 100+ 策略目錄+混合設計（2026-06 快照） | [15-strategy-catalog-100.md](15-strategy-catalog-100.md) |
| Serenity 剖析+追蹤機制+跟單回測 | [16-serenity-analysis.md](16-serenity-analysis.md) |
| **★ Fabric 驗收標準 v2.0（F0-F13 統一規則表）** | [17-fabric-acceptance.md](17-fabric-acceptance.md) |
| **★ 策略/機制總註冊表（現行判定的單一事實來源）** | [18-strategy-registry.md](18-strategy-registry.md) |
| 機制分類學（原生棲地×被測座位×翻案條件） | [19-mechanism-taxonomy.md](19-mechanism-taxonomy.md) |
| 理論再審思（七篇經典對帳；G-S 經濟學地基） | [20-theory-review.md](20-theory-review.md) |
| Paper-to-TR 管線（持續論文驅動複測） | [21-paper-to-tr-pipeline.md](21-paper-to-tr-pipeline.md) |
| **★ 論文台帳 + >500 引用深讀計畫（52 篇已參照含重測優先度 + 177 篇前瞻分波、含年份/作者）** | [22-paper-ledger-and-plan.md](22-paper-ledger-and-plan.md) |
| 標準化測試報告 TR-01~17（各機制含圖表判定） | docs/tests/ |
| 試驗登記簿（campaign 級，≈226 變體） | [trial-registry.md](trial-registry.md) |
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

# 第二部分：實證研究結論（§E，2026-06~07，docs 05-21）

> 把第一部分的規劃**真的做出來並嚴格回測**之後的誠實結論。一句話：**沒有穩健的 edge 超過「長部位 + modest 品質傾斜 + 多 sleeve 分散」；50-100% 安全報酬是獨角獸；唯一統計顯著的 alpha 是多 sleeve 風險平價組合（且邊際）。**

## E0. 目前狀態
- master **41 commits、102 tests、ruff clean、預算 $0**（全部未推 GitHub，待使用者 PAT）。
- 樣本：**519 檔美股日線 2015-2024（1.26M bar）+ 731k SEC 基本面事實（503 檔）+ 65,503 insider 列**。
- 已建：修正版 order-independent 回測引擎、O1 嚴謹閘門（DSR/PBO/SPA）、O5 組合（risk-parity）、regime-conditional 歸因模組（FDR）、2 個另類資料 connector（EDGAR 基本面 + insider Form 4，皆 point-in-time）。

## E1. 硬目標證明：50-100% CAGR + 低回撤 = 不可達（docs/07,08）
- 它等於 **Calmar(CAGR/|MDD|) ≈ 3.3**；跨所有方法（單一/槓桿 0.5-3x/混合/O5 風險平價）**可達最佳 Calmar = 0.64**，差 5 倍。
- **槓桿是 Calmar 不變量**（同比放大報酬與回撤）；SOXL/TQQQ+趨勢濾網在多頭期確能 40-84% CAGR，但 **MDD −50~−90%**。
- 三條件（≥5策略 ∧ 低風險 ∧ 50-100%）**數學互斥**。根因：Calmar≈Sharpe 函數，Sharpe 被廣度鎖在 ~1（Grinold）。

## E2. 因子發現：沒有穩健的單因子，**除了基本面品質**（docs/06,09,10）
| 因子 | 廣 universe ICIR | 判定 |
|---|---|---|
| **gross profitability（基本面品質）** | **+0.30 穩定** | ✅ 唯一穩健新 alpha，**regime-universal**（bear/壓力最強=flight-to-quality）|
| momentum | ~−0.01（廣市場死）| universe 特定（集中科技才強）＝對少數贏家的 beta，非因子 |
| value（earnings yield, B/M）| 負/翻號 | FAIL（價值失落十年）|
| insider net-buying | +0.13 不穩 | FAIL（alpha 已衰退）|
| low-vol | universe 特定 | 不可外推 |
- 自主因子搜尋 **0/56 配置達 Sharpe 2**；SPA 顯示**無一配置勝 1/N**；擴廣度 51→503 檔**沒幫助**（IC 隨 universe 變廣而下降）。

## E3. 擇時/gating 的真相（docs/05,09,10）
- **gate 到「現金」減損價值**（退出機會成本 > 省下回撤；200SMA 錯過 SMA 之下反彈）。
- **但在兩個互補因子間 switch（動量↔品質）有幫助**（off 狀態是生產性替代訊號非現金）——量級小。
- conditional IC（描述性）≠ 可獲利 gate（處方性）。

## E4. 唯一顯著的 alpha：多 sleeve 風險平價組合（docs/08）
- 5 sleeve（動量/防禦輪動/槓桿趨勢/黃金/債券）風險平價：**Carhart alpha +6.34%/yr, t=2.64**、Sharpe 1.22、MDD −19%——全 session 唯一統計顯著、過 DSR 的策略。
- 加品質 sleeve = **邊際**（Sharpe 1.22→1.23、alpha t 降到 2.60）——無 step-change、無銀色子彈。

## E5. Minervini / USIC 驗證：仍有效但**顯著衰退**（docs/05,07）
- 趨勢/動量是真效應，但 alpha 砍半（Minervini Sharpe 2016-19 1.17 → 2020-24 0.64；AI 集中動量 CAGR 48%→10%；太空軍工 18%→−1%）。正如使用者預測的 alpha decay。

## E6. 嚴謹度是真正的交付物：3 次對抗式 review 抓到真問題
- **sizing 排序相依**（我「修好」的 value sizing 其實讓 headline 是字母排序 artifact，差 12.4pp；改 from_orders）。
- **regime-attribution 假陽性**（~14 cell 無多重測試校正，加 Benjamini-Hochberg FDR）。
- **regime-rotation in-sample 雜訊**（+0.05 Sharpe edge bootstrap P=0.59、OSS 反轉；flight-to-quality 防禦在 2022 反而多虧 7pp；CAGR 被倖存者 CVNA 灌水）。
- 加上回測 postmortem 自己抓的（等股數 sizing、無除息、distutils）——**共 17+13 個錯誤**，全靠「先量測、deflate、對抗驗證」。

## E7. 誠實的最佳交付 + 限制
- **最佳可交付 = 多 sleeve 風險平價組合**（docs/08，唯一顯著 alpha）；可選 +15% 品質 tilt 換最佳 Sharpe(1.23)+較低回撤。
- 要更高報酬只能加槓桿（報酬與回撤同比放大）。要 50-100% 必須接受 −50%+ 回撤。
- **核心限制（按影響）**：倖存者偏誤（現任成分股）> 廣度/單一市場/日頻 > 無更長歷史（僅 ~3-4 個真熊）> 樣本內調參。要真突破需**換資料維度**（更長歷史、更多市場、更高頻、更強另類資料 IC），非換演算法。

## E8. 收斂證明：拉了 docs/11 三根免費「換資料維度」槓桿，天花板皆不動（docs/13 §4-9）
- **策略空間窮盡（5 連敗）**：regime-rotation（in-sample 雜訊）→ seasonality（衰退）→ Kalman pairs（賠錢）→ 多資產 TAA（短歷史偏誤）→ 全部不改善 docs/08 組合。
- **§8 延長歷史（Vanguard 代理回溯 1996，含網路泡沫+GFC）**：資產類別宇宙 Sharpe 天花板 ≈0.70 對「策略」∧對「28 年歷史」皆不變。**TAA 是「回撤保險」非 Sharpe 增強**（GFC Antonacci +3.6% 正報酬、全週期 MDD −35% vs buy&hold −55%）。
- **§9A PEAD/SUE（新 IC 源，免費 EDGAR）**：無漂移（Q5−Q1 t≤|1.66|）。**方法論升級**：long-only sleeve 抬組合 alpha-t（2.64→2.91）是 **beta 不是訊號**——零訊號籃子一樣抬到 2.89；唯一隔離訊號的市場中性 L/S 反而把 alpha-t 拉到 2.05。→ **回頭打臉 E2/docs10 §4c 品質 sleeve「幫助」**：任何 long-only incremental-α 須用 L/S 重驗。
- **§9B 修倖存者偏誤（補 109 個被剔除名）**：CAGR 膨脹 +126bps（下界，~97% 世代稀釋）；動量仍死。**第 4 次對抗式 review（workflow skeptic）抓到 IC t-stat 重疊窗自相關灌水 ~3.7倍**（低波動 naive −5.54 → 非重疊 −1.05，本來就不顯著）。
- **§9C 可交付 = 回撤預算前緣**（`scripts/defensive_overlay.py`）：選你能承受的 MDD → 讀出配置 → 接受其誠實 CAGR；印今日權重。**交付使用者「不失本金」那半目標**。
- **鐵律**：docs/11 四槓桿拉三根（②③①）天花板紋風不動 → **「綁定約束是資料維度」三角度證實**；剩 ④日內 ORB 需無/超預算資料。**誠實最佳交付 = 多 sleeve 組合 + 回撤前緣，不是 50% CAGR 策略。**

## E9. Fabric 時代（2026-07）：驗收標準化 + 17 份 TR + 理論地基
- **fabric v2.0**（docs/17）：F0-F13 統一規則表，經文獻/程式碼雙面向對抗審查（Harvey-Liu/AHM/FIM/Cederburg/Lo/Shumway/Hoffstein 為基點）並以 TR-12~16 逐條執行；**Grossman-Stiglitz 均衡採納為經濟學前提**（$0 資訊成本→$0 alpha；翻案條件必須標價成資訊成本）。
- **TR-01~17 判定**（docs/18 為單一事實來源）：**旗艦升級**——全成本 Carhart **t=3.38 ≥ HLZ 3.0、2× 成本壓力 t=3.14**；**IBS 反轉 FAILED**（TR-16：成交慣例假象+靜態控制打平——技術規則章節全數關閉）；KMZ 複雜度 PARTIAL（TR-17：1/σ² 控制支配全部 18 變體）；統計套利/GBM-MC/ML 預測 FAILED；Markov/PCA/VaR/CAPM/HRP PARTIAL（工程價值）。
- **量測修正全面生效**：rf=BIL 超額 Sharpe、相位平均（季動量 timing-luck 1,753bps/yr）、倖存者區間 [+1.26%, +2.02%]/yr、有效樣本 n_eff（zoo 59 變體實為 1.8 個獨立賭注）、成交時點敏感度（持有 <10 bar 必附）。
- **監控管線 live**：五維出場投票+Serenity 追蹤，GitHub Actions 每日推 Telegram（$0）；Paper-to-TR 管線設計完成（docs/21）。

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
