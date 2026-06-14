# 資料源評估 ＋ 回測嚴謹度（Data Sources & Backtest Rigor）

> 日期：2026-06-14。涵蓋：台股資料源、美股基本面連接器建議、回測方法論嚴謹度 scorecard。

## A. 台股（TW）資料源

| 來源 | URL | ~★ | 費用 | 資料 |
|---|---|---|---|---|
| **FinMind** | github.com/FinMind/FinMind | ~2.6k | 免費+贊助 | 50+ 資料集：OHLCV、**三大法人**、融資融券、借券、股權分級、財報、月營收、股利 |
| twstock | github.com/mlouielu/twstock | ~1.4k | 免費(爬蟲) | TWSE/TPEX OHLCV + 即時 |
| shioaji 永豐 | github.com/Sinotrade/Shioaji | ~463 | 免費(需開戶) | 報價+歷史 kbar+tick+**下單** |
| Fugle 富果 | github.com/fugle-dev/fugle-marketdata-python | ~21 | 免費層+付費 | REST+WebSocket 報價/K線/tick |
| TEJ/tejapi | github.com/tejtw | 小 | **付費(權威)** | 黃金標準、調整後、**無倖存者偏差**歷史 |
| 官方 OpenAPI | openapi.twse.com.tw / tpex / **MOPS** | — | 免費 | 證交所/櫃買 open data、季報年報(MOPS) |

**台股獨有資料（殺手級）**：**三大法人 buy/sell（外資/投信/自營）**、融資融券、借券、股權持股分級、外資持股%、**月營收**（每月10號公布、是 CANSLIM「C」的早期訊號）。美股沒有這麼乾淨的籌碼面。

**市場結構影響策略**：
- **±10% 漲跌停**：強勢突破可能鎖漲停無法成交 → 進出場 slippage 與美股不同，「突破日」盤中可能不可交易。
- T+2；**集中市場(TWSE) vs 櫃買(TPEX)** 是兩個 venue，universe 要 union。
- 小 universe（~1,800 檔 vs 美股 ~8,000）；流動性尾巴薄 → 需 ADV/turnover 過濾否則回測成交是假的。

**Minervini/CANSLIM 可移植到台股嗎？可以，但需改：**
1. **RS Rating 自己算**（無 IBD feed）：對 TWSE+TPEX union 用 trailing return 百分位排名，保留 RS≥70 門檻。
2. union TWSE+TPEX 並標 venue。
3. 加流動性過濾（min ADV）排除薄 OTC 尾巴。
4. 處理 ±10% 漲跌停：標記漲停/跌停日為不可成交，別假設盤中成交。
5. **用調整後價格**算 MA/RS（爬來的原始價未還原股息/拆股 → 不改是真 bug）。
6. **台股獨有訊號**值得加：投信買超連續、月營收 YoY 加速（比美股更好對映 CANSLIM 的 I 與 C）。

**台股整合判決**：V2 台股**主用 FinMind**（唯一免費、單一 API 同時涵蓋價格+基本面+籌碼），twstock/TWSE OpenAPI 當免費 fallback/對照，shioaji 等要實盤下單再上。免費層**按日批次抓**（一次回傳全市場某日）別 per-ticker 迴圈。深度調整後回測資料或無倖存者偏差才考慮付費 FinMind/TEJ。

## B. 美股基本面連接器建議（解鎖 Magic Formula/Graham/QMJ 的關鍵缺口）

**核心問題：point-in-time**。yfinance/FMP/financialdatasets 給的是**今日視角**的歷史（重編後數字 + 最新修正 + 只含現存 ticker）→ 回測注入 **look-ahead + 倖存者偏差**。Magic Formula/Graham/QMJ 排名的正是最常被重編的科目（EBIT/權益/ROE），偏差很實質。

| 來源 | 費用 | Point-in-time | 備註 |
|---|---|---|---|
| **SEC EDGAR companyfacts** | 免費 | ✅ **有 `filed` 申報日** | 權威、美股限定、需自己組 XBRL；~1996/2009 起 |
| yfinance 季報 | 免費 | ❌ 重編、無申報日 | 方便但脆（429/空表/欄位錯位 bug #2584），僅 ~4-8 季 |
| FMP | 免費 250/日；付費 ~$20-80/月 | ❌ | 深、易用、FinanceToolkit 預設後端；付費才 30 年 |
| simfin | 免費 | 部分 | **bulk CSV** 適合一次灌進 DuckDB |
| financialdatasets.ai | $20/1k req；$200/月僅1年；$2000/月才30年 | ❌ | ai-hedge-fund 用它；歷史回測太貴 |
| **JerBouma/FinanceToolkit** | MIT | — | 非資料源是**比率層**：150+ 指標含 Graham/Piotroski/Altman/QMJ |
| EODHD | 付費 ~€60/月 | ❌ | 全球含**台股**，TW-later 選項 |

**連接器建議**：
- **主（美股歷史回測）：SEC EDGAR companyfacts** — 免費、權威、point-in-time（用 `filed` 日）。
- **fallback/便利**：FMP 免費層（現值對照）+ yfinance（臨時快照，**絕不當回測真相**）；**simfin bulk CSV** 初次 seed。
- **比率層**：把正規化後報表餵 **FinanceToolkit**（MIT）算 Graham/Piotroski/QMJ，別手刻。
- **台股 later**：FinMind / TWSE OpenAPI / EODHD（付費）。連接器**對來源不可知**（一個介面後面換來源）。
- **DuckDB 存法**（一張 `fundamentals` 表）：`ticker, cik, period_end, fiscal_period, form_type, filed_date AS as_of, accession, source, currency` + 數值欄（ebit, total_assets, total_liabilities, total_equity, net_income, eps, bvps, fcf, market_cap, roe…）+ `is_amendment` flag。key 在 `(ticker, period_end, as_of)`。
- **最大地雷**：只用 `period_end` 查基本面 → look-ahead。**永遠 filter `as_of (filed_date) <= simulation_date`**，且優先原始申報、修正當作另一筆較晚日期的 row。

## C. 回測方法論嚴謹度 Scorecard

> 為何重要：研究發現**所有 AI/LLM 交易框架、甚至 Kronos 的 headline 數字都禁不起嚴格檢驗**（窗口短、無成本模型、非 point-in-time）。任何策略（含我們自己的）信任前先過這關。為 vectorbt+DuckDB stack 操作化。

| # | 準則 | 通過條件 |
|---|---|---|
| 1 | **Look-ahead** | 訊號 lag ≥1 bar（t 收盤決策 → t+1 開盤執行）；特徵用 `available_at<=bar_ts` 過濾。測試：訊號全 +1 bar，若報酬崩潰就是有洩漏 |
| 2 | **倖存者偏差** | universe 用 point-in-time 成分（含已下市 ticker + 下市報酬），別 `SELECT DISTINCT ticker` |
| 3 | **train/val/test** | 時序切分；test set 只碰一次 |
| 4 | **Walk-forward** | 滾動窗口 out-of-sample 重新最佳化（vectorbt `Splitter`） |
| 5 | **Deflated Sharpe** | 揭露嘗試次數 N；DSR>0（Sharpe 撐過多重檢定調整，Bailey & López de Prado） |
| 6 | **成本/滑點** | 淨of fees+slippage；過 cost sweep（≥25 bps 仍存活） |
| 7 | **台股 ±10% 限制** | 漲停買/跌停賣**拒絕成交**，不假設限價成交 |
| 8 | **Regime 穩健** | 跨 ≥1 完整循環（多+空，含 2022）；分 regime 報 Sharpe/DD |
| 9 | **Data-snooping** | 策略**選擇本身**算進嘗試次數；保留 held-out 期 |
| 10 | **可重現** | code+data+seed 能重現權益曲線 |

**決策規則**：#1/#2/#5/#6/#7 任一 Fail = **不信任該報酬宣稱**。只報單一 headline Sharpe、無嘗試次數、無成本模型、用現存成分股的 repo，預設當作 overfit。
