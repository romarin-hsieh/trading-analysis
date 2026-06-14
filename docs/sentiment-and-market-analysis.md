# 情緒面 ＋ 市場面分析（Sentiment & Market-Regime）

> 日期：2026-06-14。對映 dashboard 願景的「情緒面與市場面分析」，與 Minervini/CANSLIM 的「M」（大盤方向）。

## A. 情緒面（Sentiment）

### A-1. 新聞 + 新聞情緒 API
| 來源 | 內建情緒分數 | 免費層 | 時戳 | 備註 |
|---|---|---|---|---|
| **Alpha Vantage `NEWS_SENTIMENT`** | ✅ overall + per-ticker(−0.35~0.35)+relevance | **25/日, 5/分** | `time_published` | **最佳免費內建分數源**；25/日很緊→按 ticker 批次+快取 |
| **Finnhub** news+sentiment | ✅(美股限定) | 60/分, ~1yr | `datetime`(unix) | rate 寬鬆 |
| Marketaux | ✅ per-entity(−1~1) | ~100/日 | `published_at` | per-entity 是強項 |
| GDELT DOC 2.0 | tone(全球多語) | **免費無 key** | 15 分更新 | 非股票特化、適合總經/全球情緒 |
| NewsAPI.org | ❌ | 100/日 但**延遲 24h** | publishedAt | 延遲扼殺即時 point-in-time |

→ 開箱即用分數：Alpha Vantage / Finnhub / Marketaux。其餘只給原始文字 → 自跑模型(A-4)。

### A-2. 社群/散戶情緒
- **ApeWisdom** — **免費無 key**，聚合 WSB/Reddit 提及+情緒%。低成本散戶訊號。⚠️ 只給滾動 24h、**無歷史 point-in-time**→自己每日快照。
- **StockTwits** — bull/bear tag + Sentiment API，但官方存取**時好時壞/受限**，多靠第三方爬。盡力而為。
- **Reddit** — **Pushshift 已被 Reddit 關閉(2023)**，無歷史；PRAW 只給近期。要自建 WSB 歷史得從今天起每日快照。
- **X/Twitter** — **無真免費層**，新開發者 pay-per-use($0.005/read)，舊 Basic $200/月已關。對 hobby 基本出局。

### A-3. 市場情緒指數
- **CNN Fear&Greed**（dashboard 已爬；社群端點 `production.dataviz.cnn.io/index/fearandgreed/graphdata` 有歷史+7 子指標）
- **VIX/VVIX**（CBOE 免費 CSV）、**CBOE put/call**（免費）、**AAII 投資人情緒調查**（週、無免費 API、aaii.com 下載）、**NAAIM 曝險指數**（週、爬）、alternative.me 加密 F&G（免費 JSON）

### A-4. 開源情緒模型（本地跑）
- **FinBERT（`ProsusAI/finbert`）** — BERT-base ~110M，pos/neu/neg，金融標準、**CPU 可跑**。⚠️ 授權 HF 卡片模糊，商用前確認。
- `mrm8488/distilroberta-financial-news-sentiment` — 更輕更快、CPU fallback。
- FinGPT 情緒(LoRA Llama，需 GPU、overkill)、VADER(詞典、通用、僅便宜 baseline)。
- → **選：FinBERT 主、distilRoBERTa fallback**。

### A-5. 台股情緒
- **FinMind `TaiwanStockNews`** — 免費 300-600/hr、含時戳 → **台股主要新聞源**。
- cnyes 鉅亨/工商（爬蟲、無乾淨 API）；PTT Stock 板（可爬；已有論文用 4M PTT 文 fine-tune Taiwan FinBERT → 可行）。Traditional Chinese 可用 bert-base-chinese 衍生 FinBERT，或翻譯→英文 FinBERT 的務實捷徑。

### A-6. 情緒 stack 建議
- **主新聞（免費）**：Alpha Vantage `NEWS_SENTIMENT`（內建 per-ticker 分數+乾淨時戳）+ Finnhub 補廣度 + GDELT 總經 tone。台股：FinMind。
- **本地模型**：FinBERT(CPU) 把任何原始標題打成 pos/neu/neg + 連續分數。
- **市場情緒**：保留 CNN F&G，加 VIX+put/call（免費程式化），週爬 AAII/NAAIM，散戶色彩用免費 ApeWisdom 快照。
- **DuckDB point-in-time 存法**：`news_sentiment(ticker, source, published_at, captured_at, headline, url, score_raw, model, label)`、`mood_index(name, as_of, captured_at, value, source)`。查詢永遠 `filter published_at<=:as_of`、依 url/headline 去重。社群/指數**每日快照**建立真實 as-of 歷史。

## B. 市場面：Regime + 廣度（操作化 CANSLIM 的「M」）

### B-1. Regime 分類法
- **趨勢過濾（最便宜最穩）**：`SPY>SMA200` 且 `SMA200 上升`；golden/death cross（SMA50 vs 200）當確認。
- **O'Neil 分布日/跟進日（字面的「M」引擎）**：
  - **分布日**：主要指數收 **跌≥0.2%** 且 **量大於前日**。**25 個交易日內 ≥5-6 個分布日** = 機構出貨→停止買進。分布日 25 日後失效，或指數從該日盤中漲~5-6% 即失效。
  - **跟進日（底部訊號）**：下跌後「嘗試反彈」第 1 個上漲日起算，**第 4 日起**（最佳 4-7 日）主要指數 **強漲（經典≥1.25-1.5%、過濾用≥1.5-2%）且量大於前日** → 確認新上升趨勢=綠燈。非每個都成但無大多頭不始於 FTD。
- **HMM（hmmlearn）**：`GaussianHMM(n_components=3)` 配 `[returns, realized_vol, VIX]`。⚠️ 標籤會 switching、易 overfit/out-of-sample 不穩 → **只當側訊號別當主 gate**。
- **波動 regime**：VIX <15 平靜 / 15-20 正常 / 20-30 升高 / >30 壓力。

### B-2. 市場廣度（從自有 universe 算）
令 A=上漲家數、D=下跌家數：
- **AD line** = 累積 Σ(A−D)；**AD ratio**=A/D；看 AD 與指數背離。
- **McClellan Oscillator** = EMA19(A−D) − EMA39(A−D)（>0 多、<0 空）；Summation Index = 累積。
- **% 在 50/150/200 日 MA 上**：>70% 多、30-70% 中性、<30% 弱。**單一最佳廣度計**。
- **52 週新高-新低**：NH/(NH+NL)，>50 多 <50 空。
- **Zweig Breadth Thrust**：EMA10(A/(A+D)) 在 10 日內由 <0.40 升破 >0.615 = 強多頭啟動。
- **StockBee 廣度**（xang1234 有實作）：日 **漲≥4% vs 跌≥4%** 家數；**10 日比 = Σ漲4%/Σ跌4%**，≥2.0 多頭推力、≤0.5 偏空。

### B-3. 總經 risk-on/off（FRED/yfinance 免費）
| 指標 | 來源 | risk-OFF |
|---|---|---|
| 殖利率曲線 10y−2y(`T10Y2Y`) | FRED | <0 倒掛 |
| 信用利差 HYG/LQD | yfinance | 比值跌破 50d MA |
| VIX 期限結構(`^VIX` vs `^VIX3M`) | yfinance | VIX>20-30、VIX/VIX3M>1 倒掛(恐慌) |
| 美元 DXY | yfinance | 急升=全球 risk-off |
→ 當 gate/overlay 不當單獨觸發（曲線倒掛領先衰退 6-24 月）。

### B-4. Regime+廣度建議（複合 `global_regime`，取代裸 SPY>MA200）
每日從免費 yfinance 指數 + 自有 universe 算，計 0-6 分，**不把 HMM 放進 gate**（只當側訊號，除非 out-of-sample 驗證有 edge）：
- **A 指數趨勢(0-2)**：+1 SPY>上升 200d；+1 SPY 50d>200d
- **B O'Neil 方向(−2~+2)**：+2 有效跟進日；−2 trailing 25 日分布日 ≥5
- **C 廣度(0-2)**：+1 universe %>200d MA > 50%；+1 10 日 漲4%/跌4% >1（或 McClellan>0）

對映：`RISK_ON`(≥5) 全進場 / `NEUTRAL`(3-4) 半倉只做 A 級 / `RISK_OFF`(≤2 或分布群聚 active 或 VIX/VIX3M>1) 不新進、收緊停損。

**進場 gate（Minervini「M」）**：只在 regime∈{RISK_ON,NEUTRAL} 且無 active 分布群聚時做多。**dashboard 欄位**：`global_regime` enum + 原始子分數（`pct_above_200, dist_day_count, mcclellan_osc, up4_down4_ratio, ftd_active`）讓 UI 顯示「為什麼」。VIX 帶 + 10y−2y 當**顯示用 risk context** 非硬 gate（避免 overfit）。全部 deterministic、可回測、用既有資料即可算。

### 開源參考
xang1234/stock-screener（StockBee 廣度+IBD RS）、hmmlearn(~3.4k★)、namuan/trading-utils（StockBee monitor）。McClellan/Zweig/%-above-MA 公式以 StockCharts ChartSchool 為準。
