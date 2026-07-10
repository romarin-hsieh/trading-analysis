# 資料源完整目錄(70 源 × 7 類,2026-07 站上驗證)

> [docs/24](../24-data-gaps-and-sources.md) 的完整附錄:8-agent 工作流的逐源盡職調查結果。
> 預算判定:🟢 免費 / 🟡 <$5 月硬上限 / 🔴 超預算。信心:✅=今日站上驗證定價與額度、◐=部分、⚠️=僅記憶(用前需人工確認)。
> **地雷警告:GDELT 絕不可走 BigQuery(pay-per-TB 無上限);推薦組合中無任何 pay-per-use 無上限方案。**

## 1. 美股日內/分鐘級歷史

**類別判定**:可以在 $0 關閉這個缺口,而且不需要動用預算:主引擎 = Alpaca Market Data Basic(免費、硬上限型):SIP 全市場品質的分鐘 bar 自 2016 年起、200 calls/min、每 request 最多 10k bars,500 檔 × ~9.5 年一次性回填約 4-6 小時可完成,之後每日增量僅需 ~1-2 分鐘 API 時間——完全符合「一次回填+每日增量」的 $0 模式;唯一限制是查不到最近 15 分鐘(對隔夜/日內研究無礙,對即時執行有礙)。交叉驗證源 = Massive(前 Polygon)免費層(5 calls/min、約 2 年深度、EOD 延遲)與 FirstRate 免費樣本(10 檔大票 1 年 1-min)。tick 級微結構抽查 = Databento $125 一次性 credits + 帳戶級用量上限(超限即擋 request,非放任計費)。仍被封鎖的部分:(1) 2016 年之前的分鐘資料在 $0 無法取得原始檔——唯一免費路徑是 QuantConnect 雲端(1998 年起、無倖存者偏誤,但資料不可匯出、研究須搬進 LEAN);(2) 即時/近 15 分鐘資料所有免費層都沒有(研究不受影響,live 日內交易訊號受影響);(3) 含下市股票的完整 PIT 分鐘 universe:Alpaca 對 inactive 標的的分鐘資料覆蓋不保證,嚴格版需 FirstRate 一次性付費 bundle(>$100,超月預算)或 Databento。解鎖清單:ORB Zarattini(QQQ 版與 stocks-in-play 版 2016+)、LPS 隔夜/日內、日內 AR、微結構(Alpaca 免費層連歷史 trades/quotes tick 都有,受同樣 15 分鐘規則)。避開:Alpha Vantage(25 req/day 無法回填,premium $49.99 超budget)、Finnhub(免費 key 打 /stock/candle 回 403)、IBKR API(歷史資料強制要 L1 訂閱 + 60 req/10min pacing,回填 500 檔要數週,且有倖存者偏誤)。

### Alpaca Market Data — Basic (免費層)【首選主引擎】 — 🟢 free ✅站上驗證
- **URL**:https://alpaca.markets/data
- **提供**:美股歷史分鐘/日 bar、trades、quotes(tick)、snapshots、corporate actions;REST + websocket;官方 alpaca-py SDK。歷史 bar 為全市場(SIP)品質,即時串流僅 IEX。
- **免費層**:$0:200 API calls/min;歷史資料自 2016 年起(官網稱 7+ 年);限制 = 不能查詢「最近 15 分鐘」的 SIP 資料;websocket 限 30 symbols(IEX);每 request 最多 10,000 bars 可分頁。
- **最低付費**:Algo Trader Plus $99/mo:解除 15 分鐘限制、10,000 calls/min、全交易所即時、OPRA 選擇權——本專案不需要。
- **爆量模型**:硬上限:超過 rate limit 回 429,不會產生費用;免費層無任何計費管道,bug 最多被限流,不可能爆費用。
- **PIT 品質**:中上:歷史 bar 為 SIP 全市場成交聚合(2016+),支援 adjustment=raw/split/dividend/all,可搭配免費 corporate actions API 重建 PIT 價格;弱點 = 下市(inactive)標的的分鐘資料覆蓋不受官方保證 → 用 Alpaca 建 universe 時對 2016-今的下市股要抽查,嚴格的無倖存者偏誤研究需補源。
- **解鎖**:四項全解鎖(2016 年起):ORB Zarattini(QQQ/TQQQ 5-min 復刻 + stocks-in-play 全 universe 版)、LPS 隔夜/日內直接交易回測、日內 AR、盤中微結構(免費層含歷史 tick trades/quotes)。500 檔 × 9.5 年分鐘 bar ≈ ~44k requests ≈ 4-6 小時一次回填;之後每日增量 500 requests ≈ 2.5 分鐘。
- **接入工程**:S:alpaca-py SDK + 分頁迴圈即可;唯一設計點是回填腳本的斷點續傳。
- **驗證方式**:今日實際抓取 alpaca.markets/data(方案價格/limits)與 docs.alpaca.markets/docs/about-market-data-api(200/min、Since 2016、latest-15-minutes 限制、$99 Plus 對照表)。

### Massive(前 Polygon.io,2025 改名)免費層【交叉驗證源】 — 🟢 free ◐部分驗證
- **URL**:https://massive.com/pricing
- **提供**:美股 SIP 聚合 bar(分鐘/日)、trades、quotes、參考資料;REST;歷史上 Polygon 以保留下市股票聞名。
- **免費層**:$0:5 API calls/min、延遲(end-of-day 更新)、歷史深度約 2 年(2 年為 Polygon 長期政策,今日無法在改版後官網直接確認,由第三方 2026 比較文與搜尋摘要佐證 5 calls/min)。aggregates 端點單次可回傳最多 50k bars → 500 檔 × 2 年分鐘 bar ≈ ~2000 calls ≈ 7 小時(受 5/min 限制)。
- **最低付費**:Starter $29/mo(15-min 延遲、無限 calls、更深歷史);Developer $79 即時;Advanced $199 websocket。全部超預算。
- **爆量模型**:硬上限:免費層超額即 429,無計費卡;無爆費風險。
- **PIT 品質**:價格 PIT 佳(全市場 SIP 聚合、含下市標的的傳統紀錄);但免費層僅 ~2 年深度 → 只覆蓋單一 regime,不能當主回測源,適合對 Alpaca 資料做逐 bar 交叉驗證。
- **解鎖**:作為 Alpaca 分鐘 bar 的獨立第二源(抓資料 bug / 拼接錯誤);近 2 年的 ORB/LPS 樣本外驗證。
- **接入工程**:S:REST + 官方 client;5/min 需排程慢慢跑。
- **驗證方式**:polygon.io/pricing 301 轉址到 massive.com/pricing(今日確認改名事實);massive.com 頁面為 JS 渲染抓不到內文,定價細節由 WebSearch 摘要(free 5 calls/min delayed;$29/$79/$199)+ 2026 第三方比較文(ksred.com)佐證;「2 年歷史」為記憶+慣例,未能今日在官網確認。

### Databento(pay-as-you-go + $125 一次性 credits)【tick 級/PIT 黃金標準抽查】 — 🟡 <$5 硬上限 ◐部分驗證
- **URL**:https://databento.com/pricing
- **提供**:交易所原生歷史資料(XNAS.ITCH、EQUS 等):MBO/MBP/trades/OHLCV-1s/1m/1d,DBN 二進位格式,含下市標的、交易所時間戳;Python client。
- **免費層**:註冊送 $125 credits(6 個月過期),可用於任何 historical dataset;歷史 API 無訂閱門檻、按 uncompressed GB 計費;有 metadata.get_cost API 可在下單前精確報價。
- **最低付費**:訂閱制 Standard $179/mo(本專案不需要);pay-as-you-go 無月費。OHLCV-1m 記錄 56 bytes → 500 檔 × 5 年 ≈ ~14 GB;每 GB 單價(equities 衍生 schema)今日無法從 JS 渲染的計算器取得 → 回填是否超出 $125 credits 未確認,須先用 get_cost 報價。
- **爆量模型**:本質是 pay-per-use,但官方支援帳戶/成員層級的每月用量上限,「超限即封鎖後續 request」(官方 help 文句),加上 get_cost 事前報價 → 可設定成行為上的硬上限;不設上限則有爆費風險,務必先設。
- **PIT 品質**:最佳:交易所原生 feed、含下市股票、無倖存者偏誤、publisher timestamps 可重建當時可知資訊;是嚴格 PIT 研究的參考標準。
- **解鎖**:盤中微結構 TR 的 tick 級抽查(MBO/MBP 短窗口研究)、對 Alpaca bar 的權威校驗、含下市股的小樣本 PIT 檢定——在 $125 credits 內做一次性研究,不當常態源。
- **接入工程**:M:DBN 格式 + batch job 流程 + 必須先寫 get_cost 報價與 usage-limit 設定,約半天到一天。
- **驗證方式**:今日抓取 databento.com/pricing($125 credits/6mo 過期、$/GB 計費、Standard $179、可設 monthly limits);「超限封鎖 request」引自官方 help.databento.com 定價文章的搜尋摘要;equities OHLCV 的每 GB 單價未能取得。

### Tiingo 免費層(IEX intraday 端點) — 🟢 free ◐部分驗證
- **URL**:https://www.tiingo.com/pricing
- **提供**:EOD(含下市股、品質佳)+ /iex 歷史盤中價(可 resample 1min/5min);盤中價源為 IEX TOPS(僅 IEX 頂簿)。
- **免費層**:$0:50 req/hr、1,000 req/day、1 GB 頻寬/月、500 unique symbols/月;/iex 歷史盤中在文件中對免費層可用性未明示(經驗上可用但受頻寬限制)。
- **最低付費**:Power $30/mo:10k req/hr、100k req/day、40 GB/月、~108,758 symbols——超預算。
- **爆量模型**:硬上限:超額即拒絕,無自動扣費;無爆費風險。
- **PIT 品質**:盤中弱:IEX-only 頂簿價格,薄票與消費盤價格偏離 consolidated tape;volume 僅 IEX 成交(對 ORB stocks-in-play 的相對成交量訊號不可用);500 symbols/月上限剛好卡死 500 檔 universe 的回填+驗證並行。EOD 部分反而是它的強項(含下市)。
- **解鎖**:只適合當第三驗證源或 EOD 品質基準;不建議當分鐘資料主源(1 GB/月頻寬回填 500 檔 × 數年幾乎不可行)。
- **接入工程**:S-M:REST 簡單,但要做頻寬/symbol 配額管理。
- **驗證方式**:今日抓取 tiingo.com/pricing(免費層與 Power 全部限額數字)與 tiingo.com/documentation/iex(歷史盤中端點存在、IEX-only volume 警語);盤中歷史深度(約 2017 起)未能在頁面確認。

### FirstRate Data 免費樣本 — 🟢 free ✅站上驗證
- **URL**:https://firstratedata.com/free-intraday-data
- **提供**:下載式 CSV:1-min bar(timestamp,OHLC,volume,美東時間);付費 bundle 為一次性買斷,含 16,241 檔(含 7,000+ 下市股)自 2000 年起。
- **免費層**:免費:AAPL/AMZN/MSFT/META/TSLA + SPY/QQQ/VXX/DIA/EEM + SPX/DJI/VIX/NDX/RUT 各 1 年 1-min 資料;另外任何 ticker 頁可下載 2 週樣本;頁面未要求註冊。
- **最低付費**:bundle 一次性買斷(全市場 bundle 約 $100-300 量級,今日未逐一驗證單價);非月費制。
- **爆量模型**:無 API、純檔案下載;零爆費風險。
- **PIT 品質**:免費樣本 = 10 檔存活大票(取樣本身就有倖存者偏誤),僅適合 sanity check;付費 bundle 才有 7,000+ 下市股的無倖存者偏誤 universe(是低成本 PIT 分鐘資料的已知最佳一次性買斷,但超出月預算)。注意「零成交 bar 不輸出」的格式慣例。
- **解鎖**:$0 下:Zarattini QQQ ORB 的近 1 年重現與 Alpaca 資料逐 bar 校驗(SPY/QQQ);若未來願意一次性花 ~$100+:2000 年起含下市股的全 universe(解鎖 pre-2016 regime + 嚴格 PIT)。
- **接入工程**:S:手動下載 zip + pandas 讀 CSV,1 小時內。
- **驗證方式**:今日抓取 firstratedata.com/free-intraday-data(免費 ticker 清單、1 年免費、2 週樣本、格式與時區聲明);bundle 單價未逐一驗證。

### QuantConnect 免費雲端(LEAN) — 🟢 free ◐部分驗證
- **URL**:https://www.quantconnect.com/pricing
- **提供**:免費雲端回測平台:美股分鐘解析度資料庫(平台宣稱 1998 年起、無倖存者偏誤、PIT corporate actions/universe selection),Python/C#。
- **免費層**:$0:免費層含 Equity/Options/Futures 等資料 + 「Unlimited Backtesting」+ 分鐘/小時/日解析度;tick/秒級為付費功能;資料不可匯出、只能在平台內用。
- **最低付費**:Researcher 起的組合式計價(按 compute node 加購,無固定牌價);本用途 $0 即可。
- **爆量模型**:免費層無計費管道;硬上限(排隊/併發限制),零爆費風險。
- **PIT 品質**:極佳(這是它存在的意義):無倖存者偏誤 universe、PIT 除權息與成分變動、1998 年起分鐘資料——$0 預算下唯一能碰 pre-2016 分鐘資料 + 嚴格 PIT 的途徑;代價是研究必須遷入 LEAN 框架且原始資料拿不出來。
- **解鎖**:ORB/LPS 的 pre-2016 regime 穩健性檢定(dot-com、GFC)、含下市股的全 universe 回測——本地 pipeline 做不到的部分全在這裡補。
- **接入工程**:L:不是 ingestion 而是移植——策略要改寫成 LEAN algorithm/research notebook,估 1-3 天/策略。
- **驗證方式**:今日抓取 quantconnect.com/pricing(免費層含分鐘級資料、unlimited backtesting、免費 $0;1998 起與 tick 級歸屬未在該頁明示,1998 為平台長期宣稱)。

### Alpha Vantage【結論:不採用】 — 🔴 超預算 ✅站上驗證
- **URL**:https://www.alphavantage.co/premium/
- **提供**:TIME_SERIES_INTRADAY:美股 1/5/15/30/60min,月切片可回溯 20+ 年,consolidated 價格。
- **免費層**:$0 但僅 25 requests/day——500 檔 × 每檔每月一個切片 × 數年 = 數萬 requests,以 25/day 回填需數年,實務上不可用。
- **最低付費**:$49.99/mo(75 req/min)起——超預算 10 倍。
- **爆量模型**:免費層硬上限(超額拒絕),無爆費風險;但額度小到無意義。
- **PIT 品質**:中:20+ 年 intraday 深度是免費世界少見的,但不含下市股票(倖存者偏誤)且免費層即時性為延遲。
- **解鎖**:理論上解鎖 pre-2016 分鐘資料,實際被 25/day 封死;僅適合單一 ticker 的長歷史抽查(如 QQQ 一檔 ≈ 240 個月切片 ≈ 10 天配額)。
- **接入工程**:S(API 簡單)但配額使其無法服務本類別。
- **驗證方式**:今日抓取 alphavantage.co/premium(25 requests/day 免費、$49.99/mo 最低付費層)。

### Finnhub【結論:已封鎖,剔除】 — 🔴 超預算 ◐部分驗證
- **URL**:https://finnhub.io/pricing
- **提供**:quote/基本面/新聞等免費;/stock/candle(歷史+盤中 OHLCV)已移出免費層。
- **免費層**:60 calls/min,但免費 key 呼叫 stock candles 回 403「You don't have access to this resource」——本類別所需的端點正好被鎖。
- **最低付費**:個人付費方案數十至百餘美元/月量級(定價頁 JS 渲染,今日未能取得確切數字)——無論如何超預算。
- **爆量模型**:免費層硬上限,無爆費;但無關緊要因為端點本身 403。
- **PIT 品質**:n/a(拿不到資料)。
- **解鎖**:無。列出僅為了關閉這條候選線索:候選清單裡的「Finnhub 分鐘 API」在 2026 已不存在於免費層。
- **接入工程**:n/a
- **驗證方式**:finnhub.io/pricing 頁面 JS 渲染抓不到內文;candles-403-on-free 由官方 GitHub issue(finnhubio/Finnhub-API #349)與多個第三方 2025-26 來源交叉確認。

### IBKR TWS API【結論:不適合本用途】 — 🔴 超預算 ◐部分驗證
- **URL**:https://interactivebrokers.github.io/tws-api/historical_limitations.html
- **提供**:券商 API 歷史 bar(1-min 起)、多年深度;需開戶。
- **免費層**:無真正免費路徑:官方 API 文件明示「API 取歷史資料一律需要 L1 即時行情訂閱」(TWS 的免訂閱 delayed chart 不適用於 API);pacing = 60 requests/10 min 且單次僅數千 bars。
- **最低付費**:US Securities Snapshot & Futures Value Bundle $10/mo(月佣金滿 $30 可豁免);Network A/B/C 單點訂閱各約 $1.5/mo 的說法今日未能在官網驗證(定價頁 403)。
- **爆量模型**:訂閱費固定(硬上限),不會爆;但 $10/mo 已超 $5,豁免條件($30 佣金)本身就是花費。
- **PIT 品質**:差:下市標的無資料(倖存者偏誤)、深度因商品而異、bar 為 IB 自建聚合非原始 SIP。
- **解鎖**:幾乎無新增解鎖:60 req/10min 下回填 500 檔 × 5 年 1-min 需連跑數週;Alpaca 免費層在每個維度都優於它。僅在未來需要「下單執行」時才值得開戶,順便拿它做即時行情,而非歷史資料源。
- **接入工程**:L:開戶+入金+TWS/Gateway 常駐+pacing 管理。
- **驗證方式**:今日抓取官方 TWS API docs(historical_limitations / delayed_data:API 需 L1、60 req/10min);interactivebrokers.com 定價頁 403,bundle $10/滿 $30 豁免由搜尋摘要確認;$1.50 單網路價未驗證。

### Stooq 盤中資料庫【今日無法驗證】 — 🟢 free ⚠️僅記憶
- **URL**:https://stooq.com/db/h/
- **提供**:(記憶)免費 bulk ASCII 下載:全球日線 + 美股小時/5-min 壓縮包,每日更新。
- **免費層**:(記憶)完全免費、無 key;但盤中壓縮包深度有限(非多年完整 1-min),且有每日下載量的軟性限制。
- **最低付費**:無付費層。
- **爆量模型**:純檔案下載,零爆費風險。
- **PIT 品質**:未知/偏弱:資料來源與聚合方法不透明、下市股覆蓋不明、盤中深度不足以支撐多年回測。
- **解鎖**:最多作為免 key 的備援校驗;不解鎖任何主 TR。
- **接入工程**:S(若壓縮包如記憶所述)。
- **驗證方式**:今日兩次抓取 stooq.com/db 相關頁面均失敗(空內容/404,疑似擋爬蟲),所有描述均來自記憶——使用前需人工開瀏覽器確認現況。

### yfinance(Yahoo Finance 非官方)【僅前向蒐集】 — 🟢 free ⚠️僅記憶
- **URL**:https://github.com/ranaroussi/yfinance
- **提供**:非官方 Yahoo 介面:1-min bar 僅能取最近 ~30 天(每次 request 最多 ~8 天)、5m/15m ~60 天、1h ~730 天。
- **免費層**:免費無 key;非官方 scraping,ToS 灰色地帶,端點隨時可能變動(2024-25 已多次斷裂後由社群修復)。
- **最低付費**:無。
- **爆量模型**:零計費;風險是可靠性而非費用。
- **PIT 品質**:差:無法回溯(30 天窗)、無下市股、資料修訂不可追;僅適合「從今天開始滾動蒐集」的前向資料庫,但這個角色 Alpaca 也做得更好。
- **解鎖**:實質上被 Alpaca 完全支配;僅在 Alpaca 帳戶不可用時作為臨時 fallback。
- **接入工程**:S:pip install 即用。
- **驗證方式**:未做今日驗證(30 天/8 天窗為社群長期共識+記憶);列出僅為完整性。

## 2. 選擇權歷史

**類別判定**:YES — this gap is substantially closeable at $0/month with a three-source free stack, all verified live today (2026-07-10): (1) OptionsDX free EOD chains 2010–2023 for SPY/SPX/QQQ + mega-caps (IV+greeks+volume, monthly CSVs) gives 14 years of index-options depth for TR-09 BSM validation, VRP, and IV-skew; (2) DoltHub post-no-preference/options gives EOD bid/ask/IV/greeks for ~2,000+ symbols 2019-02→2026-07-08 (still updating, git-versioned = auditable PIT) and bridges OptionsDX's 2023 cutoff to the present; (3) ThetaData's FREE tier is the sleeper hit — historical EOD + OPEN INTEREST endpoints from 2023-06-01 at 30 req/min with zero payment method attached, which is the only free OI history found and buys the GEX/dealer-gamma backtest ~3 years of runway instead of starting from the 2026-07 self-built snapshots. All three are structurally overage-proof (no metered billing anywhere; worst case is rate-limit 429s). Key caveat driving the residual gap: NEITHER OptionsDX nor DoltHub carries open interest, so OI-dependent work (GEX) is capped at 2023-06 onward; pre-2023 OI history exists only behind CBOE DataShop pay-per-order (prices hidden pre-checkout, realistically tens-to-hundreds of dollars) or DeltaNeutral ($585+/yr) — both over budget, so treat pre-2023 GEX as blocked and design the backtest for the 2023-06+ window. Secondary caveats: vendor-precomputed greeks/IV in the free sources should be recomputed from quotes (which doubles as TR-09 validation); OptionsDX updates quarterly (archive, not feed); DoltHub has no explicit data license (fine for internal research, check before publishing); keep the yfinance snapshot pipeline running as forward cross-validation. Not recommended: marketdata.app free tier (credit-per-contract math kills chain pulls), Massive/ex-Polygon and Alpha Query (paid-only for options, over budget).

### DoltHub post-no-preference/options (free versioned SQL DB) — 🟢 free ✅站上驗證
- **URL**:https://www.dolthub.com/repositories/post-no-preference/options
- **提供**:US equity/ETF options EOD chains in a git-versioned Dolt SQL database: option_chain table with date, symbol, expiration, strike, call/put, bid, ask, IV (vol), delta, gamma, theta, vega, rho; plus volatility_history table (per-symbol HV/IV history). ~2,000+ symbols. CRITICAL GAP: no open interest, no volume, no last-trade columns (schema verified by DESCRIBE today).
- **免費層**:Entirely free. Verified via live SQL API today: option_chain spans 2019-02-09 to 2026-07-08 (updated within 2 days of today — actively maintained). Web SQL API has per-query timeouts (COUNT DISTINCT over full table timed out); full access = clone with dolt CLI (large DB, expect tens of GB). No account needed to clone public repos.
- **最低付費**:None needed — DoltHub public repos are free to clone/query. (DoltHub paid plans exist only for private repo hosting.)
- **爆量模型**:No billing at all — zero overage risk. Worst case is query timeouts on the web API, pushing you to a local clone.
- **PIT 品質**:Best-in-class for a free source: Dolt is git-for-data, so commit history lets you reconstruct exactly what the DB contained on any past date (true PIT audit). Delisted symbols' rows persist in history (low survivorship bias for 2019+). Caveats: greeks/IV are collector-computed (unknown model — recompute from bid/ask mid for rigor); community-maintained single collector = gap risk; no explicit data license stated on the repo (fine for internal research, flag before publication).
- **解鎖**:TR-09 BSM validation, VRP, and IV-skew predictors from 2019 → present across ~2,000 symbols — 7+ years instead of accumulating from 2026-07. Does NOT unlock GEX/dealer-gamma (no OI). Extends the self-built snapshot pipeline backward by 7 years.
- **接入工程**:M — install dolt, clone (tens of GB, hours), then it's plain MySQL-dialect SQL; or S if you only need slices via the free web SQL API (paginated, timeout-limited).
- **驗證方式**:Ran live SQL today via dolthub.com/api/v1alpha1: SHOW TABLES, DESCRIBE option_chain, MIN(date)=2019-02-09, MAX(date)=2026-07-08 on option_chain; volatility_history same range. Also DoltHub blog 2024-09-27 (maintainer publishing since April 2021).

### OptionsDX (free EOD option chains, 10 tickers) — 🟢 free ✅站上驗證
- **URL**:https://www.optionsdx.com/
- **提供**:Historical option chains for SPY, SPX, QQQ, VIX, TSLA, AAPL, NVDA, UVXY, SLV, BTC(Deribit). Monthly CSV zips; fields (verified column spec): QUOTE_DATE, UNDERLYING_LAST, EXPIRE_DATE, DTE, C_/P_ BID/ASK/LAST/SIZE/VOLUME, C_/P_ IV, full first-order greeks + rho, STRIKE. CRITICAL GAP: no OPEN INTEREST column. Intervals: EOD, 30m, 15m, 5m, 1-min.
- **免費層**:SPY product page verified: ALL variants $0.00 — years 2010–2023, at every frequency incl. EOD (shop shows other tickers $0–$20/50 range, so some ticker/interval combos are paid but EOD is the free anchor). Checkout requires no billing info; instant download links. FAQ: datasets updated quarterly, so recent quarters lag (newest ~2024+ availability varies per ticker; 2010–2023 verified free for SPY).
- **最低付費**:Intraday for non-free combos: roughly $5 per symbol-year at 15-min, up to ~$20–50 for 1-min/SPX — ONE-TIME purchases, not subscriptions.
- **爆量模型**:One-time downloads only, price shown at checkout — structurally impossible to overrun. A la carte intraday buys are hard-capped by each explicit purchase.
- **PIT 品質**:EOD/intraday snapshots as-recorded (no restatement mechanism, which is fine — options quotes aren't revised). Survivorship moot for its universe (index products + still-listed mega-caps). Vendor-precomputed IV/greeks (recompute for TR-09 rigor — actually ideal as an independent cross-check for your BSM implementation). Quarterly update lag means it's a backtest archive, not a live feed. License terms not explicit on site — personal research use is the marketed purpose; check Disclaimer/Terms before redistribution.
- **解鎖**:TR-09 BSM (14 years of SPY/SPX chains with vendor IV+greeks to validate against), VRP (SPX/SPY 2010–2023 covers 2 vol regimes incl. 2020), IV-skew predictors on index + mega-cap names. NOT GEX-via-OI (no OI; volume-weighted gamma proxy only).
- **接入工程**:S — free checkout, download monthly CSV zips, pandas-ready. A few GB per ticker at EOD.
- **驗證方式**:Fetched optionsdx.com homepage, /shop/ (10 products, $0–$50 ranges), /product/spy-option-chains/ (all variants $0, 2010–2023, fields list, monthly CSVs), /faq/ (quarterly updates, no billing info for free items); column spec incl. absence of OI confirmed via optionsdx.com/option-chain-field-definitions/ (surfaced in search).

### ThetaData — FREE tier — 🟢 free ✅站上驗證
- **URL**:https://docs.thetadata.us/Articles/Getting-Started/Subscriptions.html
- **提供**:API (local Theta Terminal, Java + REST/Python SDK) for US options. Free tier endpoints verified in docs: historical EOD OHLC, historical OPEN INTEREST, chains — the only free source found with historical OI. Greeks/IV endpoints are gated to Standard ($80/mo) and above, but you can compute IV/greeks yourself from free EOD quotes + underlying.
- **免費層**:FREE tier: EOD granularity, history from 2023-06-01, 30 requests/min, 1-day delayed. Verified on docs subscription matrix today: FREE row = EOD + Open Interest + OHLC endpoints, both historical and 'real-time' (delayed).
- **最低付費**:Options Value $40/mo (real-time, 1-min intervals, history to 2020-01-01) — over budget. Standard $80/mo adds tick + IV/greeks endpoints + history to 2016.
- **爆量模型**:Flat subscription tiers, 'unlimited requests' with rate limits — no usage-based billing anywhere, so a runaway script hits 429s, not your card. Free tier has no payment method attached at all.
- **PIT 品質**:Exchange-sourced EOD + OI as-published; OI is T+1 by nature (OCC cycle) — model it as known next morning, standard practice. History only from 2023-06 on free tier (short: ~3 years, one regime). Survivorship: coverage is of the live listed universe from their collection start. No revision issues for quotes/OI.
- **解鎖**:THE unlock for GEX/dealer-gamma backtests: daily OI per contract from 2023-06-01 (vs. your self-built snapshots starting 2026-07 — buys back ~3 years). Also TR-09 BSM inputs (EOD quotes + underlying to self-compute IV) and cross-validation of your snapshot pipeline. VRP/IV-skew possible but only 3 years deep.
- **接入工程**:M — run Theta Terminal locally (Java), free account signup, then REST/Python; 30 req/min means bulk history pulls need patient batching (bulk-chain endpoints help).
- **驗證方式**:Fetched thetadata.net/pricing (Value $40 / Standard $80 / Pro $160, flat monthly) and docs.thetadata.us subscriptions page (FREE tier matrix: EOD granularity, 2023-06-01 start, 30 req/min, 1-day delay, EOD+OI+OHLC endpoints) today.

### yfinance self-built snapshots (incumbent baseline) — 🟢 free ⚠️僅記憶
- **URL**:https://github.com/ranaroussi/yfinance
- **提供**:Current-day option chain snapshots only (bid/ask/last, volume, OI, Yahoo-computed IV) — no historical chains, ever. This is your existing 2026-07 collection pipeline.
- **免費層**:Free, unofficial Yahoo scrape; no formal limits but throttling/breakage risk (Yahoo has tightened scraping repeatedly).
- **最低付費**:N/A.
- **爆量模型**:No billing. Risk is availability, not cost.
- **PIT 品質**:Perfect PIT by construction (you record what you saw, when you saw it) but zero backfill; survivorship-free going forward. Yahoo IV is low-quality — recompute.
- **解鎖**:Keeps accumulating forward data with OI for GEX; now demoted to (a) cross-validation of ThetaData free-tier OI/quotes and (b) realtime-ish complement. No TR unblocked retroactively.
- **接入工程**:S — already running.
- **驗證方式**:Not re-verified this session (no pricing to verify; capability is well-established: Options.option_chain returns current expirations only).

### CBOE DataShop (Option EOD Summary) — 🔴 超預算 ◐部分驗證
- **URL**:https://datashop.cboe.com/option-eod-summary
- **提供**:Authoritative OPRA-derived EOD summaries: two daily snapshots (15:45 ET + close) with NBBO+size, OHLC, volume, VWAP, and OPEN INTEREST for all US listed options; IV+greeks available as paid 'Calcs' add-on. History from January 2012.
- **免費層**:None (free sample files only). Prices are NOT displayed publicly — cart shows $0.00 until you configure an order.
- **最低付費**:Pay-per-order (one-time historical purchases or monthly subscription). Order-configurator pricing; historically on the order of ~$1–2 per symbol-month for EOD summaries (could not verify current numbers on-page) — meaningful multi-year multi-symbol history will run well past $5, likely tens to hundreds of dollars.
- **爆量模型**:One-time explicit orders — no runaway/overage risk (you approve every dollar), but each useful order alone likely exceeds the monthly budget. A single cheap symbol-month as a QA benchmark against free sources might squeak under $5 occasionally.
- **PIT 品質**:Gold standard: exchange-official OPRA snapshots incl. OI, full delisted-symbol coverage from 2012 — no survivorship issues. This is the reference dataset the free sources should be validated against.
- **解鎖**:Would fully unlock GEX/dealer-gamma pre-2023 and deep VRP/IV-skew (2012+) — but only if budget were lifted. Within budget: at most spot-check QA orders.
- **接入工程**:S per order (CSV download) — the barrier is price, not plumbing.
- **驗證方式**:Fetched datashop.cboe.com/option-quotes and /option-eod-summary today (coverage from Jan 2012, snapshot contents, Calcs add-on confirmed; dollar prices not exposed pre-checkout) + search results.

### marketdata.app — 🔴 超預算 ✅站上驗證
- **URL**:https://www.marketdata.app/pricing/
- **提供**:REST API + Sheets add-on for OPRA option chains with strikes, expirations, pricing, IV, greeks, OI.
- **免費層**:Free Forever plan verified today: 100 API credits/day, options data 24-hour delayed, history capped at 1 year. Warning: chain requests bill 1 credit PER CONTRACT returned, so one full SPY chain can exhaust the daily quota — free tier is only good for tiny targeted pulls.
- **最低付費**:Starter $12/mo billed annually ($30 month-to-month): 10k credits/day, full chains with IV/greeks, 5-year history, 15-min delay. Flat fee, no overage (requests fail when credits exhausted).
- **爆量模型**:Hard-capped credit system — no surprise billing on any tier; but the cheapest useful tier is $12/mo > $5 cap, and the free tier's credit math makes systematic backtesting impractical.
- **PIT 品質**:Vendor-served history (1yr free / 5yr Starter); no stated revision policy; survivorship handling undocumented. Adequate for spot checks, not for building the PIT archive.
- **解鎖**:On free tier: essentially nothing systematic — occasional single-contract history spot-checks to QA other sources. Starter would partially unlock VRP/IV-skew (5yr) but is over budget.
- **接入工程**:S — clean REST API, no local terminal.
- **驗證方式**:Fetched marketdata.app/pricing/ today (Free Forever 100 credits/day, delayed options, 1-yr history; Starter $12/mo annual with 5-yr history + full chains).

### Massive.com (formerly Polygon.io) — 🔴 超預算 ◐部分驗證
- **URL**:https://massive.com/pricing
- **提供**:Institutional-grade OPRA options: trades, quotes, aggregates, chain snapshots with greeks/IV, via REST/WebSocket + flat files.
- **免費層**:Free tier = 5 API calls/min, ~2 years history, EOD — but per current third-party/KB info, options endpoints effectively require a paid options plan; pricing page is JS-rendered and did not expose plan details to fetch. Polygon rebranded to Massive in 2025 (301 redirect verified).
- **最低付費**:Options Starter historically $29/mo (flat) — could not confirm current figure on-page today; all plausible figures are well over $5.
- **爆量模型**:Flat monthly plans with rate limits, no usage billing — no overage risk, just over budget.
- **PIT 品質**:Good as-recorded exchange data with delisted coverage on paid tiers; irrelevant at this budget.
- **解鎖**:Nothing within budget.
- **接入工程**:S (API) — moot.
- **驗證方式**:Fetched polygon.io/pricing (301 → massive.com, rebrand confirmed) and massive.com/pricing (JS shell, no content extractable); free-tier 5 calls/min + options-requires-paid via massive.com KB search results. Pricing numbers NOT directly confirmed on-page — hence partially-verified.

### DeltaNeutral / historicaloptiondata.com — 🔴 超預算 ✅站上驗證
- **URL**:https://historicaloptiondata.com/
- **提供**:Full US equity options EOD archive since 2002 (5,840 underlyings): L1 = quotes+volume+OI; L2 adds greeks/IV; L3 adds IV surface/skew metrics. Bulk file delivery.
- **免費層**:Free sample files only.
- **最低付費**:Subscriptions $585–865/yr (~$49–72/mo); one-time bundles $615–2,035. Verified on homepage today.
- **爆量模型**:Flat one-time/annual pricing — no overage risk, simply 10x over budget.
- **PIT 品質**:Deep 24-year archive incl. OI and delisted names — strong PIT/survivorship properties on paper; quality reputation mixed in community reports (worth QA if ever purchased).
- **解鎖**:Would unlock everything (GEX pre-2023, 24-yr VRP/IV-skew, TR-09) — the 'if budget were $50/mo' answer, not the $5 one.
- **接入工程**:M — bulk CSVs, large volumes.
- **驗證方式**:Fetched historicaloptiondata.com homepage today (2002–present, level tiers, exact prices).

### Alpha Query / VolVue — 🔴 超預算 ✅站上驗證
- **URL**:https://www.alphaquery.com/
- **提供**:Web research platform with current IV, put/call ratios, OI stats and charts; historical downloads (CSV/API) only via its premium VolVue product.
- **免費層**:Free web charts for eyeballing single names — no free bulk/historical download of chains.
- **最低付費**:AlphaQuery platform $19.95/mo (1-week trial); VolVue pricing unpublished.
- **爆量模型**:Flat subscription — no overage risk, but over budget and not chain-level data anyway (derived vol metrics, not full chains).
- **PIT 品質**:Derived/aggregated metrics with undocumented methodology; unsuitable as a primary PIT source.
- **解鎖**:Nothing systematic; at most a free visual sanity-check of IV/OI levels. Drop from candidate list.
- **接入工程**:L relative to value — scraping web charts is not worth it.
- **驗證方式**:Fetched alphaquery.com homepage today ($19.95/mo, VolVue upsell, no free downloads).

## 3. 下市股/PIT 成分/長歷史

**類別判定**:Closeable at $0 for ~80% of the gap, with one honest residual. The $0 stack: (a) fja05680/sp500 GitHub CSVs (1996-present, actively maintained, last update 2026-06-08) + Wikipedia's changes table (rows back to at least 1980, day-precision effective dates) give PIT S&P 500 membership -> unlocks F11 PIT universe and the constituent side of TR-13; (b) Alpha Vantage LISTING_STATUS (live-tested today with demo key) gives the full delisted list with ipoDate/delistingDate and a `date` param that reconstructs the listing universe as of any date back to 2010-01-01 -> delisting-date ground truth for survivorship-interval convergence; (c) Tiingo free tier is the only $0 source of actual PRICE SERIES for delisted tickers - live-checked supported_tickers.csv contains 14,760 tickers with endDate<2020 (e.g., MER to 2008-12-31, AAI to 2011-11-30, AAMRQ to 2013-12-17) and 9,635 tickers with pre-2001 history -> unlocks TR-21/DeBondt long-history and value/small-cap native habitat on a substantially de-survivorshipped panel. All three are hard-capped free (no card on file, throttle-not-bill) = zero overage risk. RESIDUAL BLOCKED: the 2008 mega-bankruptcy price series (LEH, BSC, CFC, old GM absent from Tiingo; WB overwritten by Weibo ticker reuse) - a complete local survivorship-free panel including those names starts at EODHD $19.99/mo (4x budget) or Norgate Platinum ~$52.50/mo (10x, retail gold standard). The $0 escape hatch for full-fidelity 2008 replay is QuantConnect's free cloud tier (27,500 US equities incl. delisted, survivorship-bias-free from Jan 1998), but it locks the combo replay into LEAN in-platform (no free export) = large migration effort. Practical recommendation: build TR-13/F11 on AV+GitHub+Wikipedia+Tiingo now at $0; treat Tiingo's missing-2008-bankruptcies as a documented bias bound (direction: overstates returns in 2008-09 windows); reserve QuantConnect for a one-off validation replay of the combo through 2008; only pay EODHD if that validation shows the bias bound is material.

### Alpha Vantage LISTING_STATUS — 🟢 free ✅站上驗證
- **URL**:https://www.alphavantage.co/query?function=LISTING_STATUS&state=delisted&apikey=YOUR_KEY
- **提供**:CSV of ALL delisted US stocks/ETFs with symbol, name, exchange, assetType, ipoDate, delistingDate; `date` parameter returns the listing/delisting universe AS OF any historical date (docs: back to 2010-01-01). Live-tested: date=2014-07-10&state=delisted returned thousands of rows with day-precision delisting dates. NOTE: gives the delisted LIST, not price series - AV time series for delisted tickers is generally unavailable (memory, untestable with demo key).
- **免費層**:25 API requests/day (verified on premium page today); LISTING_STATUS works on free tier (verified via live demo-key call)
- **最低付費**:$49.99/mo for 75 req/min - irrelevant here, adds rate not data
- **爆量模型**:Hard cap: requests simply refuse after 25/day; no card on file, no pay-per-use path. Zero risk of billing overage from a bug.
- **PIT 品質**:Good for metadata: day-precision delisting dates; `date` param = true PIT listing universe but ONLY back to 2010-01-01, so 2008 universe cannot be reconstructed from this endpoint alone. No prices for delisted names.
- **解鎖**:TR-13 survivorship-interval convergence (delisting-date ground truth to bound bias windows); F11 PIT universe for 2010+ directly; join key (delistingDate) for cleaning any other price source
- **接入工程**:S - one CSV GET per date snapshot; a handful of calls total
- **驗證方式**:Live API call today: /query?function=LISTING_STATUS&date=2014-07-10&state=delisted&apikey=demo returned real delisted CSV; free-tier limit from alphavantage.co/premium/

### Tiingo (free tier) — 🟢 free ✅站上驗證
- **URL**:https://www.tiingo.com/documentation/end-of-day
- **提供**:EOD adjusted price series with 30+ yrs history; ticker universe INCLUDES delisted names with exact start/end dates. Live-checked supported_tickers.csv (107,364 rows): 14,760 tickers with endDate<2020 (delisted/inactive), 9,635 with startDate<2001. Spot checks: MER covered to 2008-12-31, AAI (AirTran) to 2011-11-30, AAMRQ (AMR) to 2013-12-17 - end dates match AV's delisting dates exactly. HOWEVER: LEH, BSC, CFC, NCC, ABK, old-GM absent; WB is Weibo from 2014 (Wachovia history gone) - 2008 mega-bankruptcies are a real hole.
- **免費層**:1,000 req/day, 50 req/hr, 500 UNIQUE SYMBOLS per month (verified on pricing page today); full history depth available on free tier
- **最低付費**:$30/mo Power plan (verified today - note this has risen from the old $10) - lifts symbol/rate caps
- **爆量模型**:Hard throttle: 429s when caps hit, free tier has no card on file - no billing risk. The binding constraint is 500 unique symbols/month, meaning a ~1,200-symbol historical S&P universe backfill takes ~3 calendar months of rotation (one-time cost, prices are static once fetched).
- **PIT 品質**:Best free option but imperfect: delisted tickers carry exact end dates; ticker reuse is NOT namespaced (WB=Weibo overwrote Wachovia) so joins must be (ticker,date-range) keyed via supported_tickers.csv; 2008 bankruptcy cohort partially missing -> residual survivorship bias that must be documented and bounded, not ignored
- **解鎖**:TR-21/DeBondt long-history (30+ yrs, thousands of pre-2001 tickers), value/small-cap native habitat, combo long-history replay 1996+ on a mostly-de-survivorshipped panel; pairs with fja05680 constituents for TR-13
- **接入工程**:M - free API key signup, simple REST, but multi-month symbol-rotation plan needed for full universe backfill; supported_tickers.csv (no auth) is the master join table
- **驗證方式**:Pricing page fetched today (tiingo.com/pricing: 50/hr, 1000/day, 500 symbols/mo, $30 paid); downloaded and analyzed apimedia.tiingo.com/docs/tiingo/daily/supported_tickers.zip today - counted delisted coverage and spot-checked 2008-era tickers

### fja05680/sp500 (GitHub historical S&P 500 constituents) — 🟢 free ✅站上驗證
- **URL**:https://github.com/fja05680/sp500
- **提供**:CSV time series of S&P 500 membership 1996-present ('S&P 500 Historical Components & Changes'), built from Andreas Clenow's Trading Evolved dataset (1996-2019) + ongoing Wikipedia-sourced maintenance. MIT licensed, 883 stars.
- **免費層**:Fully free, unlimited (git clone)
- **最低付費**:n/a
- **爆量模型**:None - static files
- **PIT 品質**:Day-level membership snapshots; known caveats: 1996 start list has only 487 symbols (early years incomplete), tickers not namespaced against reuse, and author explicitly notes delisted-name PRICE data requires a paid source. Community-maintained = audit a sample of 2008-09 changes against S&P press releases before trusting
- **解鎖**:F11 PIT universe 1996+ at day precision; TR-13 constituent side; membership mask for combo long-history replay including full 2008 crisis membership churn
- **接入工程**:S - single CSV, direct pandas read
- **驗證方式**:GitHub API today: last commit 2026-06-08 ('Update for 2026-06-08'), pushed_at 2026-06-09, 883 stars; README fetched for provenance/caveats

### Wikipedia - List of S&P 500 companies (changes table) — 🟢 free ✅站上驗證
- **URL**:https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
- **提供**:'Selected changes to the list of S&P 500 components' table: effective date, added ticker/name, removed ticker/name, reason - the upstream source fja05680 maintains from. Page revision history additionally allows reconstructing what the list looked like at any past date (a genuine PIT audit trail for the page itself).
- **免費層**:Free, unlimited (respect crawl etiquette); full page is 1.5MB HTML
- **最低付費**:n/a
- **爆量模型**:None
- **PIT 品質**:Change rows verified back to at least 1980 (ISO dates 1980-03-31 in table sort keys; prose dates to Dec 1998); table is titled 'Selected' = explicitly not complete in early decades, generally regarded complete ~2000+. Day-precision effective dates. Crowd-sourced: cross-check 2008-09 rows against S&P announcements
- **解鎖**:Independent verification layer for fja05680; extends constituent-change record before 1996 (sparse); reason-for-removal field distinguishes M&A vs bankruptcy vs index rebalance - useful for TR-13 bias decomposition
- **接入工程**:S-M - one HTML table parse (pandas.read_html works); revision-history mining is M
- **驗證方式**:Downloaded full page today (1.49MB), grepped table structure and earliest change dates (1980-03-31 sort keys, 6,447 table cells)

### QuantConnect (free tier, in-platform) — 🟢 free ◐部分驗證
- **URL**:https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-equity-security-master
- **提供**:US Equity Security Master: ~27,500 US equities from Jan 1998, explicitly survivorship-bias-free - includes delisted companies (the 2008 bankruptcy cohort Tiingo misses), splits/dividends/mergers/ticker changes tracked through history. Usable ONLY inside their cloud (LEAN engine backtests + research notebooks).
- **免費層**:Free plan: unlimited backtesting, 1 research node, access to equity/index/forex/crypto/futures/options data in-cloud (verified on pricing page today)
- **最低付費**:Paid tiers are configurable node bundles (Researcher tier and up, price varies); data EXPORT for local use costs prepaid QCC credits per file
- **爆量模型**:Hard cap by construction: free tier is compute-limited; the only pay-per-use surface (QCC data download) is PREPAID - you cannot spend money without explicitly buying credits first. No bug-driven overage possible.
- **PIT 品質**:Best-in-class at $0: survivorship-bias-free from 1998, delistings force position liquidation in backtests, ticker changes handled by security master (no WB/Weibo-style collisions). Constraint: it is a walled garden - results reproducible only in LEAN, raw panel not extractable for the local pipeline
- **解鎖**:The one $0 path to a FULL-fidelity 2008 replay (Lehman/Bear/old-GM included): re-implement the combo in LEAN as a validation replay to bound the bias in the local Tiingo-based panel; TR-21 long-history from 1998
- **接入工程**:L - rewrite strategy in LEAN (Python API), learn platform; no data ingestion into local stack (that is the point and the limitation)
- **驗證方式**:quantconnect.com/pricing fetched today (free tier contents); Security Master specs (27,500 equities, Jan 1998 start, survivorship-bias-free, delisted included) from quantconnect.com docs/dataset pages via search snippets today

### EODHD (EOD Historical Data) — 🔴 超預算 ✅站上驗證
- **URL**:https://eodhd.com/pricing
- **提供**:Delisted-inclusive EOD prices: 26,000+ US delisted tickers, coverage mostly from Jan 2000 (their academy article) - i.e., 2008 crisis names covered with price series. Delisted tiering verified on docs page: pre-2018 delistings = EOD prices only; post-2018 adds fundamentals/divs/splits; post-2021 adds intraday. Exchanges API lists delisted tickers per exchange; delisted data stated available in paid packages.
- **免費層**:Free: 20 API calls/day and only PAST YEAR of history (verified on pricing page today) - useless for 2008 work
- **最低付費**:$19.99/mo 'EOD Historical Data - All World' ($199/yr) - the cheapest tier with full-depth history incl. delisted EOD (verified pricing page today; plan-level delisted gating from their docs' 'available in any of our packages' statement)
- **爆量模型**:Fixed subscription with daily call caps (100k/day paid); limit increases 'by request' - no automatic overage billing. Safe model, wrong price.
- **PIT 品質**:Good: delisted price series from ~2000 = covers 2008 cohort; delisting metadata via Exchanges API. Not CRSP-grade on ticker-reuse namespacing; index constituent history is a separate API. Cheapest COMPLETE local fix if budget ever rises to ~$20/mo
- **解鎖**:Would fully unlock local combo long-history replay incl. 2008 bankruptcies, TR-13 closure, value/small-cap habitat - everything - at 4x budget
- **接入工程**:M - clean REST API, delisted workflow documented (exchange ticker list w/ delisted=1, then EOD per ticker)
- **驗證方式**:eodhd.com/pricing fetched today (Free=20/day+1yr history; All World $19.99/mo); eodhd.com/financial-apis/delisted-stock-companies-data fetched today (pre/post-2018 tiering); 26,000+ US delisted from their survivorship academy article via search

### Norgate Data (US Stocks Platinum) — 🔴 超預算 ◐部分驗證
- **URL**:https://norgatedata.com/prices.php
- **提供**:Retail gold standard for this exact category: Platinum = daily US price history back to 1990 INCLUDING delisted securities + historical index constituents (S&P 500/400/600, Russell) with day-precision membership; padded/capital-adjusted, ticker-namespaced (delisted get unique symbols - no WB-collision problem). Diamond extends to 1950. Python API (norgatedata package).
- **免費層**:None (free trial only)
- **最低付費**:US Stocks Platinum: US$346.50/6mo or US$630/12mo = ~$52.50/mo effective; no monthly billing option exists
- **爆量模型**:Prepaid fixed term - zero overage risk, but 10x the monthly budget and requires $315-630 upfront
- **PIT 品質**:Best available outside CRSP: survivorship-bias-free by design, historical index constituents built-in (solves both halves of this category in one product), delisting dates + unique delisted symbology. This is the benchmark other options should be measured against
- **解鎖**:Everything in this category at day precision incl. TR-13 closure, F11, DeBondt, combo replay to 1990 - if budget were ~$50/mo
- **接入工程**:S-M - official Python package, Windows-native updater (fits this machine)
- **驗證方式**:prices.php fetched today (tier features: Platinum=1990+delisted+historical constituents, Diamond=1950; 12mo=10% discount); exact USD figures ($346.50/6mo, $630/12mo) via search results quoting norgatedata.com prices page - calculator is JS so numbers not re-confirmed in raw HTML

### Sharadar Equity Prices / Core US Equities (Nasdaq Data Link) — 🔴 超預算 ◐部分驗證
- **URL**:https://data.nasdaq.com/databases/SEP
- **提供**:EOD prices for 21,000+ ACTIVE AND DELISTED US tickers from 1998, with corporate-actions table incl. delist reasons and ticker changes; the bundle (via QuantRocket listing) adds S&P 500 constituents 1957-present and fundamentals 1990+. Institutional-quality PIT discipline at prosumer price.
- **免費層**:No usable free tier (sample data only)
- **最低付費**:Price is login-gated on data.nasdaq.com (could not verify today); from memory ~$499-599/yr (~$42-50/mo) for SEP/Core US bundle - treat as unverified
- **爆量模型**:Fixed annual subscription - no overage risk, but ~10x budget and annual commitment
- **PIT 品質**:Excellent: delisted included from 1998, explicit delist-reason + ticker-change tables (solves reuse), 1957+ S&P constituents in bundle - CRSP-adjacent quality. The 'if this project ever gets a real budget' answer alongside Norgate
- **解鎖**:Full category closure: TR-13, F11 (1957+ constituents!), DeBondt/TR-21 long history, combo replay
- **接入工程**:M - Nasdaq Data Link API/bulk CSV, well-documented, pandas-friendly
- **驗證方式**:Coverage (21,000+ active+delisted, 1998 start, delist reasons; S&P 500 constituents 1957+) verified today via data.nasdaq.com/quantrocket.com pages and search snippets; PRICE could not be verified (data.nasdaq.com renders client-side, QuantRocket pricing behind login) - price figure is memory-only

### Stooq bulk database — 🟢 free ◐部分驗證
- **URL**:https://stooq.com/db/h/
- **提供**:Free bulk daily ASCII downloads (d_us_txt.zip, ~333MB) covering US stocks/ETFs, some series 30+ years deep. Third-party docs (mssqltips, QuantStart, ml4trading) confirm the files exist and parse cleanly. Delisted coverage is UNDOCUMENTED - no delisting-date field exists, and community reports are mixed on whether dead tickers persist in the dump.
- **免費層**:Entirely free; daily-download byte quotas apply informally
- **最低付費**:n/a
- **爆量模型**:None (no account, no billing)
- **PIT 品質**:Poor for this category: no delisting metadata, no constituent data, unknown delisted retention policy, no revision history. NEW FINDING: as of today the entire site (including the CSV endpoint /q/d/l/) sits behind a JavaScript proof-of-work anti-bot challenge - curl/scripted access is blocked; manual browser download of the bulk zip still works. Fine as a bulk price cross-check, unfit as the PIT backbone
- **解鎖**:At most: independent price cross-validation for long-history series obtained elsewhere; NOT a survivorship or constituent unlock
- **接入工程**:M - manual browser download of zips (automation now blocked), then trivial CSV parse; ticker mapping to other sources is the real work
- **驗證方式**:Attempted stooq.com/db/h/ and /q/d/l/ CSV endpoint today - both returned SHA-256 proof-of-work challenge pages (anti-bot wall confirmed first-hand); bulk file contents/depth from third-party documentation via search

### Financial Modeling Prep (FMP) — 🔴 超預算 ◐部分驗證
- **URL**:https://site.financialmodelingprep.com/developer/docs/stable/delisted-companies
- **提供**:Has both category-relevant endpoints: Delisted Companies API (list w/ delisting dates) and Historical S&P 500 constituents API (additions/removals with dates). Price series for delisted tickers: unclear.
- **免費層**:Basic free: 250 calls/day, EOD only, 500MB/30-day bandwidth cap; docs pages for the delisted and historical-constituents endpoints carry 'upgrade to premium' gating language (could not confirm directly - docs returned 403 to fetcher)
- **最低付費**:Starter $22/mo, Premium $59/mo, Ultimate $149/mo (per findmymoat review, added 2025-08); the category-relevant endpoints appear to sit at Premium
- **爆量模型**:Fixed plans with daily call + bandwidth caps, no automatic overage billing - safe model, but the needed endpoints are behind $59/mo
- **PIT 品質**:Unverifiable today: endpoint docs blocked (403), plan gating uncertain, and FMP's historical-constituents data has community-reported quality gaps vs Wikipedia-derived lists. Do not build on this without a free-key smoke test first
- **解鎖**:If the delisted-list endpoint turns out free-tier accessible it duplicates what Alpha Vantage already gives us verified; the S&P constituents endpoint duplicates fja05680 at $59/mo - so realistically unlocks nothing the free stack doesn't
- **接入工程**:S - trivial REST, but gated
- **驗證方式**:site.financialmodelingprep.com docs pages returned 403 today; plan prices from findmymoat.com review (fetched today) + FMP docs/search snippets; endpoint existence confirmed via FMP's own docs URLs in search results

## 4. 新聞/情緒

**類別判定**:可以在 $0/月 關閉這個缺口(連 $5 都不用花)。免費骨幹:(1) SEC EDGAR 8-K = PIT 完美的事件流(accepted-timestamp 精確到秒、1994+、免費 10 req/s)→ 事件研究首選;(2) GDELT = 免費全量新聞+tone,2015+ 有 15 分鐘級 PIT 時戳(Events 1.0 回溯 1979)→ 注意力/新聞量異象;(3) Baker-Wurgler SENTIMENT.xlsx(1965-07~2023-12)+ AAII 週頻調查(1987+)= 長史情緒指數,直接解鎖 B-W 情緒因子;(4) Alpha Vantage NEWS_SENTIMENT 免費 25 req/day(硬上限、limit=1000/請求)= ticker 級金融情緒回溯至 ~2022-03,夠 docs/11 LLM 情緒層的驗證樣本;(5) Finnhub 免費層 company-news(北美、1 年史、60 calls/min 硬上限)補近期 headline,搭配專案既有的每日收集管線(如 options-chain)向前累積。所有推薦源都是免費或硬上限(429 拒絕、不扣款),無用量爆表風險——唯一要避開的地雷是「GDELT via BigQuery」路徑:BigQuery on-demand 按掃描 TB 計費、無上限,一個查詢就可能燒 $5+,務必走 raw CSV 下載。仍然無解的部分:(a) 2022 前的 ticker 級金融調校新聞情緒史(RavenPack/GDELT-finance 級,免費層無解,只能用 8-K+GDELT tone 代理);(b) 社群面即時 firehose——StockTwits API 已關閉新註冊、Twitter/X 付費牆,Reddit 免費 100 QPM 只能向前收集(Pushshift 已死,歷史回溯不可得);(c) Baker-Wurgler 2023-12 之後的更新(需自行用 6 個代理變數重建,且注意該指數為全樣本 PCA 構建、本質非 PIT,只適合因子研究不適合即時訊號)。

### GDELT Project (Events 2.0 / GKG / DOC 2.0 API) — 🟢 free ✅站上驗證
- **URL**:https://www.gdeltproject.org/data.html
- **提供**:全球新聞事件資料庫:Events 1.0 回溯 1979(日更)、Events 2.0/GKG 2015+ 每 15 分鐘更新(65 語言機翻)、DOC 2.0 API 全文檢索 2017-01+,含 tone(情緒)分數、主題、實體、新聞量 timeline
- **免費層**:整庫 100% 免費開放,無 API key。DOC 2.0 API 免費(無官方文件化限速,社群慣例 ~1 req/5s 以免被封);raw CSV 每 15 分鐘一檔可全量下載;另可經 Google BigQuery 查詢(危險,見 overage)
- **最低付費**:無付費方案——資料本身永遠免費;唯一花錢路徑是 BigQuery 查詢費
- **爆量模型**:raw 檔下載與 DOC API = 零費用、零爆表風險。警告:BigQuery 路徑是 pay-per-TB-scanned 無上限,對 GDELT 這種 TB 級表一個 SELECT 就能超過 $5——絕對不要走 BigQuery,走 raw CSV
- **PIT 品質**:好(2015+):每 15 分鐘 append-only 快照,可精確重建「當時已知」;2015 前只有日頻。無倖存者偏誤(新聞非上市清單)。缺點:tone 是通用情緒非金融調校,雜訊高;來源組成隨年代漂移(監控源增加)需 normalize by 當期總量
- **解鎖**:注意力/新聞量異象(news-volume attention proxy)、事件研究的新聞面確認、docs/11 LLM 情緒層的原始文本來源(有 URL 可回抓原文)、Baker-Wurgler 式情緒代理的新聞成分
- **接入工程**:M-L:DOC API 做定向查詢是 M;raw CSV 全量管線是 L(檔案量大,需只抓 finance 相關過濾)
- **驗證方式**:今日 fetch gdeltproject.org/data.html(明載 '100% free and open'、1979+、15-min 更新)與 blog.gdeltproject.org DOC 2.0 API 發布文(全文檢索回溯 2017-01-01)

### SEC EDGAR 8-K 事件流(daily index + full-text search API) — 🟢 free ✅站上驗證
- **URL**:https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- **提供**:美股全體上市公司的 8-K 重大事件申報(earnings 2.02、M&A 1.01、高管變動 5.02…按 item code 分類)、每日索引檔、submissions JSON API、full-text search API(efts.sec.gov,2001+)
- **免費層**:完全免費、無 key(只需自報 User-Agent);限速 10 requests/second(今日在官方頁面驗證原文 '10 requests/second');電子申報史回溯 ~1994
- **最低付費**:無付費方案,政府公開資料
- **爆量模型**:零費用;超速只會被暫時封 IP(10 分鐘),不可能產生帳單
- **PIT 品質**:全類別最佳:acceptance timestamp 精確到秒、法定不可竄改、可完美重建任意時點的已知資訊集;倖存者偏誤=無(下市公司申報全保留)。專案已有 EDGAR 基本面管線(見 docs/data-and-backtest-rigor.md),邊際成本極低
- **解鎖**:事件研究(earnings/M&A/guidance 8-K)的黃金標準事件時戳;新聞異象研究的 PIT 錨點(用 8-K 時戳對齊新聞時戳);docs/11 LLM 情緒層可直接對 8-K 全文跑情緒
- **接入工程**:S-M:專案已有 EDGAR 存取程式碼,加 8-K item-code 解析是 S;full-text search 集成是 M
- **驗證方式**:以聲明 User-Agent curl 官方頁 sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data,grep 到限速原文 '10 requests/second'(2026-07-10)

### Baker-Wurgler Investor Sentiment Index(Wurgler NYU 網站) — 🟢 free ✅站上驗證
- **URL**:https://pages.stern.nyu.edu/~jwurgler/
- **提供**:Baker-Wurgler (2006) 投資人情緒指數本尊:SENTIMENT.xlsx,月頻,1965-07 至 2023-12,含正交化版本與 6 個成分代理變數
- **免費層**:整檔免費直接下載,無註冊
- **最低付費**:無付費方案
- **爆量模型**:靜態檔案,零風險
- **PIT 品質**:差(誠實警告):指數用全樣本 PCA 構建且歷史值隨每次更新被修訂——有 look-ahead,不能當即時交易訊號,只適合學術式因子研究(這正是「B-W 情緒因子」文獻的標準用法)。更新停在 2023-12,已滯後 ~2.5 年;之後要自行用 6 代理重建。倖存者偏誤不適用(市場級指數)
- **解鎖**:直接解鎖 Baker-Wurgler 情緒因子複現(目標用例點名的項目);當 docs/11 LLM 情緒層的長史 ground-truth 對照基準
- **接入工程**:S:一個 xlsx,pandas 讀入即用
- **驗證方式**:今日 fetch pages.stern.nyu.edu/~jwurgler/main.htm,確認 'Investor sentiment data' 連結 SENTIMENT.xlsx、標注涵蓋 196507–202312、免費

### AAII Investor Sentiment Survey(週頻散戶情緒) — 🟢 free ◐部分驗證
- **URL**:https://www.aaii.com/sentimentsurvey/sent_results
- **提供**:美國散戶 bull/neutral/bear 週頻調查,1987 年至今,週四發布;完整歷史 Excel(sentiment.xls)含 S&P 500 對照
- **免費層**:歷史檔在 sent_results 頁底 'Download Complete Historical Data' 下載;多個來源指出免費(至少需免費 basic 帳號註冊);週頻新值每週四公開
- **最低付費**:AAII 正式會員 ~$49/年,但情緒調查資料本身不需要
- **爆量模型**:靜態下載+每週一筆,零爆表風險
- **PIT 品質**:好:調查週期週四 00:01 至週三 23:59、週四發布——以 1 天滯後使用即為 PIT;歷史檔記錄 week-ending 日期,已發布數字不修訂。39 年史對情緒因子足夠長。限制:僅市場級(非 ticker 級)
- **解鎖**:Baker-Wurgler 式情緒因子的週頻成分、情緒反轉(contrarian)研究、與 CNN Fear&Greed(已有)互補的長史散戶情緒
- **接入工程**:S:一個 xls + 每週手動或半自動更新(aaii.com 擋爬蟲,自動化需帶 session)
- **驗證方式**:aaii.com 對 fetcher 回 403(含瀏覽器 UA 的 curl 也 403);經 WebSearch 由 AAII 官方 Confluence 支援頁與多個引用源確認下載路徑(sent_results 頁底)、檔名 sentiment.xls、1987 年起。未能親自完成下載流程確認是否強制註冊

### Alpha Vantage News & Sentiment API(NEWS_SENTIMENT) — 🟢 free ✅站上驗證
- **URL**:https://www.alphavantage.co/documentation/
- **提供**:ticker 級金融新聞+情緒分數(每篇文章含 per-ticker relevance + sentiment score)、topic 過濾(earnings/ipo/M&A/貨幣政策等 15 類)、time_from/time_to 歷史查詢、每請求最多 1000 篇
- **免費層**:免費 key = 25 requests/day(2026-07 在官方 premium 頁驗證);NEWS_SENTIMENT 在免費層可用(docs 直接掛免費 key 申請連結,無 premium 標記)。歷史約起於 2022-03(官方 docs 範例最早 2022-04;確切起點 docs 未載,為社群共識)
- **最低付費**:$49.99/月(75 req/min)——超預算
- **爆量模型**:硬上限:第 26 個請求直接被拒,無信用卡、無扣款可能。25/day × 1000 篇 = 每日最多 2.5 萬篇回填,慢但零風險
- **PIT 品質**:中:文章有發布時戳(PIT 可用),但情緒分數是 AV 模型算的——模型版本是否隨時間重算歷史未文件化(訊號非凍結,回測時要當 as-of-today 的標註而非 as-of-then);歷史僅 ~4 年,不夠因子長史,夠事件研究與 LLM 層驗證。無倖存者問題(按 ticker 查已下市股仍有舊文)
- **解鎖**:docs/11 LLM 情緒層的現成基線(拿 AV 分數當 benchmark 對照自建 LLM 分數)、2022+ 的 ticker 級新聞事件研究、注意力異象的 ticker 級新聞計數
- **接入工程**:S:單一 REST endpoint,25/day 排程即可;回填 2022+ 全市場需按 ticker×時段切片、耗時數週但可自動化
- **驗證方式**:今日 fetch alphavantage.co/premium/(免費層 25 req/day、付費 $49.99 起)並 curl alphavantage.co/documentation/ 抽出 NEWS_SENTIMENT 完整段落(參數、limit=1000、免費 key 連結、2022-04 範例)

### Finnhub 免費層(company-news + market news) — 🟢 free ◐部分驗證
- **URL**:https://finnhub.io/docs/api/company-news
- **提供**:/company-news:按 symbol 查公司新聞(headline+summary+時戳+來源),僅北美公司;/news:市場新聞流;注意 /news-sentiment 是 Premium-only(免費層拿不到現成情緒分數,要自己對 headline 跑 LLM)
- **免費層**:官方 API spec 內嵌欄位實測:company-news freeTier='1 year of historical news and new updates'(滾動 1 年史);market news 無 premium 標記=免費;限速 60 calls/min(多個 2026 二手源一致,官方 rate-limit 頁為 JS 渲染無法直讀,另有源稱 30 calls/sec burst 上限)
- **最低付費**:付費方案(All-In-One 等)遠超 $5/月量級,官方頁 JS-only 無法讀到確切數字;二手源稱 $50~100+/月
- **爆量模型**:硬上限:超速回 429,免費 key 無綁卡、不可能扣款
- **PIT 品質**:中下:滾動 1 年窗=無法回測 1 年前(除非從今天開始每日收集向前累積——與專案現行 options-chain 每日收集同模式);文章時戳可用;歷史窗滾動意味著同一查詢不可重現(要落地存檔)
- **解鎖**:docs/11 LLM 情緒層的近期文本源(免費拿 headline、自己標情緒)、近 1 年事件研究、與 Alpha Vantage 交叉驗證新聞覆蓋
- **接入工程**:S-M:REST 簡單;要建每日 append 落地管線才有長期價值(M)
- **驗證方式**:curl finnhub.io/docs/api/company-news 並解析頁內嵌 OpenAPI JSON:company-news 的 freeTier 欄位原文、news-sentiment 的 'Premium Access Required' 標記皆來自官方 spec;限速數字(60/min)僅二手源,官方 pricing/rate-limit 頁 JS 渲染失敗

### Reddit Data API(r/wallstreetbets 等散戶注意力) — 🟢 free ◐部分驗證
- **URL**:https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki
- **提供**:subreddit 貼文/留言流(標題、內文、score、created_utc),散戶注意力與 meme-stock 情緒的原始素材
- **免費層**:非商用(個人專案/學術研究)免費,100 queries/min per OAuth client(以 10 分鐘窗平均);需註冊 app 並可能需審批;無歷史檢索——API 只給近期+熱門,Pushshift 學術存檔已死
- **最低付費**:商用 $0.24/1000 calls(需 Reddit 審批的付費協議)——非商用研究用不到
- **爆量模型**:免費層零扣款(無綁卡),超速 429;唯一風險是被判定商用而斷權,非金錢風險
- **PIT 品質**:差-中:created_utc 時戳可靠,但貼文可編輯/刪除——今天抓的舊文 ≠ 當時可見內容,嚴格 PIT 只能靠即時收集落地;歷史回溯基本不可得(Pushshift 死後)。只適合 forward-collection 的注意力代理
- **解鎖**:散戶注意力異象(mention counts)、meme-stock 情緒的向前收集;不解鎖任何歷史回測
- **接入工程**:M:OAuth app 註冊+PRAW 排程收集+落地存檔
- **驗證方式**:reddit 官方 wiki 未直接 fetch;經 WebSearch 交叉三個 2026 專文(octolens、socialcrawl、techloy)對免費層 100 QPM/非商用/商用 $0.24 每千次的描述完全一致

### marketaux 免費層 — 🟢 free ◐部分驗證
- **URL**:https://www.marketaux.com/pricing
- **提供**:全球金融新聞 API 含 entity 級情緒分數(200k+ entities、5000+ 來源、80+ 市場)——帳面上像免費版 RavenPack
- **免費層**:100 requests/day 但每請求僅 3 篇文章 = 每日上限 300 篇,研究級回填不可行;含情緒分數與 metadata;無需綁卡
- **最低付費**:$24/月(年繳)= 2500 req/day、20 篇/請求——超預算
- **爆量模型**:硬上限(免費層無卡、超量即拒),零爆表風險
- **PIT 品質**:中:文章有發布時戳;但免費層吞吐太低,歷史回填等效不可用,只能當即時零星補充;情緒模型黑箱且版本不透明
- **解鎖**:嚴格說幾乎不解鎖——300 篇/日對日頻研究不夠;僅可當 Alpha Vantage 的備援情緒源做交叉檢查
- **接入工程**:S:REST 簡單,但價值有限
- **驗證方式**:marketaux.com/pricing 與 /faq 對 fetcher 回 403;經 WebSearch 由其被索引的官方定價文案與 FreeAPIHub/apispine 等引用確認 100 req/day、3 篇/請求、$24 年繳起

### NewsAPI.org(對照組——不推薦) — 🔴 超預算 ✅站上驗證
- **URL**:https://newsapi.org/pricing
- **提供**:通用新聞 API(非金融專用、無情緒分數)
- **免費層**:100 req/day、文章延遲 24 小時、歷史僅 1 個月、禁止 production 使用——對研究幾乎無價值
- **最低付費**:$449/月——嚴重超預算,且是自動計費 overage 模式
- **爆量模型**:付費層有 opt-in 自動計費 overage(正是使用者要避開的模式);免費層本身硬上限但太弱
- **PIT 品質**:差:24h 延遲+1 個月窗,無法做任何回測
- **解鎖**:無——列入僅為排除:被 GDELT(免費、更深史、有 tone)全面支配
- **接入工程**:S(但不值得做)
- **驗證方式**:今日 fetch newsapi.org/pricing:100 req/day、24h delay、1 個月史、dev-only、Business $449/月、overage 自動計費描述皆為頁面原文

### StockTwits API(對照組——目前死路) — 🔴 超預算 ◐部分驗證
- **URL**:https://api.stocktwits.com/developers
- **提供**:散戶 ticker 級留言流+bullish/bearish 自標情緒(理論上是最乾淨的散戶情緒源)
- **免費層**:官方開發者頁聲明:API 審查中、「不接受新註冊」——新專案實際上拿不到 key;既有公開 JSON endpoints 未文件化、ToS 灰色、隨時可斷
- **最低付費**:企業/partner 級(Databricks Marketplace 上架),價格不公開,遠超預算
- **爆量模型**:n/a——無法取得存取權
- **PIT 品質**:理論上好(訊息時戳+使用者自標情緒),實務上不可得
- **解鎖**:無(現況);若日後重開免費註冊值得重評
- **接入工程**:n/a
- **驗證方式**:WebSearch 摘錄 api.stocktwits.com/developers 現行聲明(reviewing APIs, not accepting new registrations);未直接 fetch 該頁

## 5. 基本面擴充/分析師預估

**類別判定**:兩半結論不同。(1) 基本面擴充:可在 $0 關閉大半 — SimFin 免費層(5,000 檔美股、bulk CSV、REPORT/PUBLISH/RESTATED_DATE 欄位=真 PIT)是 EDGAR companyfacts 之上最好的免費補充,可交叉驗證標準化與 q-factor 季頻 ROE;但免費層只有 5 年歷史,GKX 豐富特徵「深歷史」翻案在此預算下仍只能靠既有 EDGAR 自建(SimFin 供近窗驗證)。所有推薦來源均為硬上限/免 key 模式,零爆量計費風險。(2) 分析師預估/修正:歷史修正序列的「回填」在 $0-5 判定此路不通 — IBES(WRDS)、Zacks ZEEH(1979 起的真修正史)、Estimize 全是機構級數千美元/年,無合法免費副本。最便宜合法途徑是三件免費拼圖:(a) 立即可用的部分歷史 — yfinance upgrades_downgrades(有日期的多年評級變動史,注意倖存者偏誤)+ Alpha Vantage EARNINGS(每季公告時點 estimatedEPS/surprise 深歷史,25 calls/day 硬上限慢爬,直接餵 SUE 精緻版)+ Finnhub 免費 recommendation trends 月頻歷史;(b) 從現在開始 collect-forward — 每週 cron 快照 yfinance eps_trend/eps_revisions/price targets 自建 PIT 修正檔案庫,約 12-18 個月後 docs/11 頭號 alt-data 因子才有可回測樣本。FMP/EODHD/Finnhub 的估值端點全在付費牆後($22-100/mo)且不解鎖修正「歷史」,不值得為此破預算。

### SimFin (Free plan) — 🟢 free ✅站上驗證
- **URL**:https://www.simfin.com/en/prices/
- **提供**:Standardized fundamentals (income/balance/cashflow + derived ratios) for ~5,000 US stocks, plus share prices; bulk CSV download and Python API (pip simfin). This is the fundamentals-expansion play, not analyst estimates.
- **免費層**:Free plan: 5,000 US companies, 5 years of fundamentals + price history, bulk CSV download, 500 'high-speed' API credits/month, screener/backtest UI. Paid START adds deeper history and more datasets.
- **最低付費**:START $15/mo ($180/yr, listed at 40% off annual); BASIC $35/mo; PRO $71/mo — all over budget.
- **爆量模型**:Hard cap (credits/month + rate limits); no pay-per-use, a runaway script just gets throttled. Zero overage risk.
- **PIT 品質**:Genuinely PIT-capable: bulk fundamentals carry REPORT_DATE, PUBLISH_DATE, RESTATED_DATE columns (verified via SimFin's own docs/tutorials), so you can reconstruct 'known at time t' and detect restatements. Caveats: free tier = only ~5y history (too shallow for a full GKX-era panel); coverage is current-universe-leaning, so assume some survivorship in the free slice; standardization is SimFin's own mapping (cross-check vs your EDGAR companyfacts).
- **解鎖**:GKX 豐富特徵面板翻案 — partially: adds pre-computed ratios/TTM aggregates and a standardized panel to cross-validate your EDGAR-derived features on the recent 5y window (not the deep-history reversal). q-factor 季頻 ROE cross-check. Not analyst data.
- **接入工程**:S — one bulk CSV per statement type via the maintained simfin Python package; join on PUBLISH_DATE for PIT.
- **驗證方式**:Fetched simfin.com/en/prices/ today (plan prices + free-tier contents); PUBLISH_DATE/RESTATED_DATE columns confirmed via SimFin fundamental-data-download page and simfin-tutorials in search snippets; GitHub package last release 2023 (maintenance is slow but API v3 live).

### yfinance (Yahoo Finance analyst data, unofficial) — 🟢 free ✅站上驗證
- **URL**:https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- **提供**:Analyst consensus (earnings_estimate, revenue_estimate, analyst_price_targets), eps_trend (consensus EPS now vs 7/30/60/90 days ago — a built-in 90-day revision window), eps_revisions (# up/down revisions last 7/30 days), growth_estimates, and upgrades_downgrades (dated multi-year history of broker rating changes). Yahoo's estimates are IBES-lineage (LSEG-powered).
- **免費層**:Free, no key, no documented quota — but it is unofficial scraping of Yahoo; 2025-26 saw repeated blocking/rate-limit crackdowns (documented in multiple 2026 posts), so treat as best-effort with retry/backoff and low request rates.
- **最低付費**:None (no official paid tier exists; the 'upgrade' path is a real vendor).
- **爆量模型**:No billing at all → zero cost risk; the risk is availability (IP blocks), not money.
- **PIT 品質**:Snapshot-only for estimates: eps_trend's 7/30/60/90d lookback is the ONLY native history, so a real PIT revision series must be built collect-forward (cron a weekly snapshot; ~12-18 months to a usable factor). upgrades_downgrades IS dated history (usable immediately for ratings-change event studies) but is queryable only for currently listed tickers → survivorship bias in any backfill; also grades can be silently revised. ToS grey zone: fine for personal research, do not redistribute.
- **解鎖**:docs/11 頭號 alt-data (analyst revision factor) — the only $0 path: start the weekly snapshot archive NOW; eps_revisions up/down counts map directly onto the classic revisions factor. Also immediate: upgrades/downgrades event study (with survivorship caveat stated).
- **接入工程**:S to start (pip install, ~10 lines/ticker), M to run properly (weekly snapshot cron + block-resilient retry + your own PIT store).
- **驗證方式**:Fetched the official yfinance API reference today — confirmed exact columns of eps_trend (current/7/30/60/90daysAgo), eps_revisions (upLast7days/30, downLast7days/30), and that upgrades_downgrades is indexed by grade date; blocking issues confirmed via 2026 articles in search.

### Alpha Vantage (EARNINGS history; free key) — 🟢 free ◐部分驗證
- **URL**:https://www.alphavantage.co/documentation/
- **提供**:Free fundamentals suite incl. EARNINGS (quarterly reportedEPS + estimatedEPS + surprise + surprisePercentage + reportedDate, deep multi-year history) and earnings calendar. A newer 'Earnings Estimates' endpoint exists but appears premium-badged.
- **免費層**:25 requests/day, 5/min on free key (confirmed by multiple 2026 sources; down from 500→100→25). At 25/day, a 500-name universe takes ~20 days per full refresh — bounded but slow.
- **最低付費**:Premium ~$49.99/mo (third-party reported; AV doesn't publish it) — over budget.
- **爆量模型**:Hard cap — free key simply stops answering after 25 calls/day. No card on file, zero overage risk.
- **PIT 品質**:The EARNINGS surprise history embeds the consensus estimate as it stood at announcement (estimatedEPS) with reportedDate → announcement-time PIT for SUE construction. It does NOT give the revision path between announcements. Coverage is current-universe queries → survivorship risk for delisted names in backfill.
- **解鎖**:盈餘預估 SUE 精緻版 — historical estimatedEPS/surprise per quarter is exactly the consensus-based SUE numerator input, free and deep-history. Complements (doesn't replace) the revisions factor.
- **接入工程**:M — trivial API, but the 25/day cap forces a multi-week batched crawl + local cache; write the crawler once, let it drip.
- **驗證方式**:Fetched alphavantage.co/documentation today (endpoint list; EARNINGS under free Fundamental Data, 'Earnings Estimates' carries a premium-ish badge — could not fully confirm its tier, docs truncated); 25/day limit verified via 2026 sources incl. macroption and two 2026 pricing reviews. EARNINGS field list (estimatedEPS/surprise) from prior direct use — flagging that detail as memory-level.

### Finnhub (free tier) — 🟢 free ◐部分驗證
- **URL**:https://finnhub.io/pricing
- **提供**:Free: real-time US quotes, company news, BASIC fundamentals (metrics), SEC filings, insider transactions, and recommendation trends (monthly buy/hold/sell/strongBuy counts WITH multi-year history). Premium-only: EPS estimates, revenue estimates, price target, financials-as-reported deep history.
- **免費層**:60 API calls/min hard rate limit, free key. Recommendation trends returns dated monthly history on the free key (2025 examples confirm); estimate/price-target endpoints 403 on free keys.
- **最低付費**:Estimates live in paid market-data bundles ~ $50-100+/mo (2026 comparison cites ~$99/mo; Finnhub hides exact tiers behind contact/checkout) — far over budget.
- **爆量模型**:Hard rate limit (429 when exceeded), no metered billing on free key. Zero overage risk.
- **PIT 品質**:Recommendation-trends history is vendor-restated only in edge cases; monthly period stamps make it near-PIT for a ratings-consensus factor. It's rating COUNTS, not EPS estimates — a revisions-adjacent, not revisions-proper, signal. No delisted-ticker access → survivorship in backfill.
- **解鎖**:A free, immediately-backfillable analyst-sentiment series (docs/11 adjacent): monthly consensus rating mix + its changes, usable as a cheap proxy while the yfinance collect-forward archive matures.
- **接入工程**:S — REST + official python client; one call per ticker returns full trend history.
- **驗證方式**:Pricing page fetch returned JS shell (marketing text only); free-tier 60/min + free-vs-premium split verified via 2026 comparison articles, Finnhub docs search snippets, and IBKR/RobotWealth walkthroughs showing recommendation_trends on free keys; 'estimates=premium' matches Finnhub's long-standing 403 behavior — that specific piece is memory + secondary sources, not the live docs page.

### Financial Modeling Prep (FMP) — 🔴 超預算 ◐部分驗證
- **URL**:https://site.financialmodelingprep.com/pricing-plans
- **提供**:Broad US fundamentals + an Analyst Estimates / Price Targets / Grades (upgrades-downgrades) dataset family with dated historical entries — on paid plans. Free 'Basic' is now an EOD sandbox: 250 calls/day, profile/reference/EOD data, shallow statement history.
- **免費層**:250 calls/day, described by FMP's own 2026 materials as an 'EOD sandbox' for individual use; post-2025 API restructure moved analyst datasets out of reliable free access. Worth a 10-minute empirical test with a free key (costs nothing), but do not plan around it.
- **最低付費**:Starter $22-29/mo (sources differ on current promo), Premium $59, Ultimate $149 — all over budget.
- **爆量模型**:Subscription with daily call caps per tier — hard-capped, no pay-per-use; budget risk is zero but the needed tier itself busts the budget.
- **PIT 品質**:FMP price-target and grades endpoints are announcement-dated (decent event-level PIT); their 'analyst estimates' endpoint is per-fiscal-period consensus, and whether historical revision states are preserved is undocumented — assume current-consensus with limited vintages unless proven otherwise. Known vendor-side restatement of fundamentals without vintage tracking.
- **解鎖**:If budget ever rises to ~$25/mo it is the cheapest API with dated price-target/ratings feeds; at $0-5 it unlocks nothing beyond what yfinance already gives.
- **接入工程**:S — clean REST, good docs (when you can access them).
- **驗證方式**:FMP's own pricing/docs pages 403'd (Cloudflare) on direct fetch today; plan prices and free-tier scope triangulated from FMP search snippets ('250 calls/day EOD sandbox'), FMP's plan-choice insight page, and a 2026 third-party review (findmymoat). Could not verify the exact plan gate for analyst estimates on-site — hence the ambiguity flag.

### EODHD — 🔴 超預算 ✅站上驗證
- **URL**:https://eodhd.com/pricing
- **提供**:EOD prices + a Fundamentals Data Feed (incl. analyst ratings/target fields inside its fundamentals JSON) for global equities.
- **免費層**:20 API calls/day, ~1 year of EOD data, demo-only fundamentals (a few sample tickers). Effectively useless for panel building.
- **最低付費**:Fundamentals Data Feed $59.99/mo standalone; All-In-One $99.99/mo. Cheapest plan of any kind $19.99/mo (EOD only, no fundamentals).
- **爆量模型**:Paid plans hard-capped at 100k calls/day, 1k/min — no metered overage, but irrelevant given price.
- **PIT 品質**:Fundamentals are current-state restated; no vintage/publish-date discipline advertised. Analyst fields are current consensus snapshots, no revision history.
- **解鎖**:Nothing at this budget. Listed to close the loop: it is NOT a cheap backdoor to estimates.
- **接入工程**:S if paid (bulk endpoints exist); N/A at free.
- **驗證方式**:Fetched eodhd.com/pricing today — plan names, prices, 20 calls/day free tier confirmed on-site; free-tier 1yr/demo-fundamentals detail from prior knowledge of their docs.

### Zacks estimates via Nasdaq Data Link (ZEEH / ZSEE) — the 'real IBES-like' option — 🔴 超預算 ◐部分驗證
- **URL**:https://data.nasdaq.com/databases/ZEEH
- **提供**:Zacks Earnings Estimates History: daily-updated consensus estimate HISTORY back to 1979, 2,600+ analysts, 5,000+ US/CA names — i.e., exactly the historical revision series the project wants. ZSEE = current street estimates.
- **免費層**:None for the estimates databases (NDL free tier covers unrelated open datasets). zacks.com's free web pages show per-ticker consensus + 7/30/60/90-day-ago trend, but ToS prohibits scraping — a grey channel that duplicates what yfinance already exposes; not recommended and adds nothing.
- **最低付費**:Unpublished institutional pricing (contact sales); historically quoted in the low thousands USD/yr per database.
- **爆量模型**:Flat subscription, no overage — moot at this price.
- **PIT 品質**:This is the gold standard tier: true vintage-stamped estimate history (revision-by-revision), delisted names included, survivorship-free back to 1979. Everything the free channels lack.
- **解鎖**:Would fully unlock docs/11 analyst-revision factor with a survivorship-free backtest — but only if budget grows ~100x. Named so the 'blocked' boundary is explicit.
- **接入工程**:M — NDL tables API is clean, but schema is large.
- **驗證方式**:Verified product pages exist and coverage claims (1979+, 2,600 analysts) via NDL/Zacks pages surfaced in search today; direct ZEEH page fetch returned only site chrome; price not published anywhere public — pricing level is memory/industry knowledge.

### IBES (LSEG via WRDS) / Estimize (ExtractAlpha) — 🔴 超預算 ◐部分驗證
- **URL**:https://extractalpha.com/estimize/
- **提供**:IBES: the canonical academic analyst-estimates detail/summary history (what GKX-class papers actually use). Estimize: crowdsourced EPS/revenue estimates, 100k+ contributors, still alive under ExtractAlpha (2025 retrospective confirms; distributed via WRDS, QuantConnect, IBKR).
- **免費層**:IBES: none — WRDS access requires an institutional subscription (no personal tier). Estimize: per-ticker web pages viewable; the old 'contribute estimates → see data' free model's current status is unclear post-acquisition, and bulk/history is sold as an institutional dataset.
- **最低付費**:Both institutional, thousands/yr; QuantConnect cloud access to Estimize is the cheapest sanctioned touchpoint but is platform-locked (your code runs there, no bulk export) and still exceeds budget for data access.
- **爆量模型**:Flat institutional licenses — moot.
- **PIT 品質**:IBES detail file = fully PIT, survivorship-free, revision-level — the reference standard. Estimize is timestamped and PIT by construction but is crowd (not sell-side) consensus.
- **解鎖**:Nothing at $0-5. Included as the formal '此路不通' verdict for historical revision backfill: no legal free replica of IBES exists — the frequently-rumored free mirrors are all either dead, pirated, or current-snapshot-only. If the user ever gets a university affiliation, WRDS/IBES is the single highest-value unlock for docs/11.
- **接入工程**:L (institutional onboarding) — academic access only realistic route.
- **驗證方式**:Estimize status verified today via ExtractAlpha's own pages + WRDS vendor pages + 2025 retrospective (alive, institutional). IBES/WRDS institutional-only nature is stable, well-known fact — not re-verified on-site today.

## 6. 總經長史/期貨連續合約

**類別判定**:兩個子類的答案不同。【總經預測子長史:完全可在 $0 關閉】Goyal-Welch 官網免費檔已更新到 2025(今日上站逐字確認『Updated data (up to 2025)』)——TR-17 KMZ 95 年翻案的明碼標價條件直接滿足,加 Shiller(1871+,免費)交叉驗證、FRED/ALFRED(免費,120 req/min)補真 PIT vintage;唯一誠實 caveat:GW 檔是 full-sample 修訂序列非 vintage,若 TR-17 要 PIT 嚴格版,用 ALFRED 重建可修訂預測子、GW 當 as-published 基準。【期貨連續合約:可關閉但有一道 2010 年縫】$0-5 內最乾淨的組合是 Databento $125 免費 credits + 官方月用量上限(超限直接封鎖請求 = pay-per-use 變硬上限,爆表風險歸零;日線量級只吃幾美分 credits)——給 2010-06 之後的逐合約+官方連續 symbology(c/n/v 三種明確 roll 規則,PIT 最乾淨),配 AQR 免費 TSMOM 因子序列(1985+)當 40 年外部基準、Yahoo =F(實測 2000 年起、未調整拼接、僅 prototype 用)。仍被擋的:『20+ 品種×20+ 年的原始連續面板』沒有乾淨的 $0 解——Stooq 有長史但今日實測已被 anti-bot PoW 擋程式化抓取且 roll 完全不可審計;CHRIS 已死;CSI/Norgate 超預算。唯一近預算破口是 Pinnacle CLC $99 一次性買斷(今日上站確認:98 品種、1969 起、三種明確連結法、不訂更新也能用)——嚴格月費框架下超budget,但這是 docs/22 HOP/MOP 重測完整棲地的唯一 ≤$99 路徑,建議作為一次性支出提請使用者特批;不批的話,HOP/MOP 只能做 2010+(Databento)的縮短版重測 + AQR 序列對表。

### Goyal-Welch predictor dataset (Amit Goyal 個人網站) — 🟢 free ✅站上驗證
- **URL**:https://sites.google.com/view/agoyal145
- **提供**:正典 Goyal-Welch 股權溢酬預測子集 (dp/dy/ep/bm/ntis/tbl/lty/ltr/dfy/dfr/infl 等),月/季/年頻,1871 起;另有 GWZ(2024, RFS) 的 29 個新預測子合併檔 (up to 2024)。這正是 TR-17 KMZ 95 年總經座位翻案的明碼標價資料,也是 Campbell-Thompson OOS 檢定的原生資料。
- **免費層**:完全免費:『Updated data (up to 2025)』Google Sheet;『All data up to 2024 (GW 2008 + GWZ 2024 合一檔)』Excel(僅 full-sample 版);matlab/zipped csv 亦有。無註冊、無額度限制。
- **最低付費**:無付費層,學術公開資料
- **爆量模型**:無計費,零爆表風險
- **PIT 品質**:中等偏弱:full-sample 修訂後序列,非 vintage PIT——GW 傳統即是拿此檔做 expanding-window OOS(文獻接受但非真 PIT)。網站明註『From 2022, data on lty from FRED, ltr/corpr from Bloomberg indices』= 2022 起來源切換,序列一致性需留意。指數層級無倖存者偏誤問題;個別預測子(如 ik)有已知的發布延遲/回填爭議,重現 KMZ 時要照原論文口徑。
- **解鎖**:TR-17 KMZ Goyal-Welch 95 年翻案(直接滿足其明碼條件,且更新到 2025 比多數複製研究更新);Campbell-Thompson 原生座位
- **接入工程**:S — 單一 xlsx/Google Sheet,三個頻率分頁,pandas 直讀
- **驗證方式**:今日 WebFetch 了 sites.google.com/view/agoyal145 本人頁面,逐字確認連結文字『Updated data (up to 2025)』與 2024 合併檔說明

### Shiller 長史資料 (shillerdata.com / ie_data.xls) — 🟢 free ◐部分驗證
- **URL**:https://shillerdata.com/
- **提供**:月頻 S&P 價格/股利/盈餘、CPI、長期利率、CAPE,1871–present;另有 1890 起房價指數(月更)。GW 檔 1871–1926 段的上游來源之一,可交叉驗證。
- **免費層**:完全免費下載 xls;無註冊。Yale 舊頁 (econ.yale.edu/~shiller/data.htm) 今日實測 ECONNREFUSED,官方家已遷至 shillerdata.com。
- **最低付費**:無
- **爆量模型**:無計費
- **PIT 品質**:弱:回溯重建+修訂序列,非 vintage;月頻盈餘為內插(已知學界 caveat);非用於 PIT 檢定,用於長史水準與 CAPE 類預測子。
- **解鎖**:GW 輸入交叉驗證;CAPE 預測子;TR-17 的 150 年 sanity-check 序列
- **接入工程**:S — 單一 xls,格式古怪(表頭多行)但一次性處理
- **驗證方式**:今日 WebFetch shillerdata.com 確認免費下載與房價月更;ie_data 最後更新日期頁面未明示(故降級 partially)

### FRED + ALFRED API (St. Louis Fed) — 🟢 free ◐部分驗證
- **URL**:https://fred.stlouisfed.org/docs/api/fred/
- **提供**:80 萬+ 美國總經序列;ALFRED 提供真正的 vintage(每次發布當時的值,realtime_start/realtime_end 參數)——整個 stack 裡唯一的真 PIT 總經來源。可重建『當時可知』的通膨/工業生產/利率預測子。
- **免費層**:免費 API key;約 120 requests/min 速率限制(多個官方週邊與客戶端庫確認);無月額度上限。
- **最低付費**:無付費層
- **爆量模型**:無計費;超速僅被 throttle,零金錢風險
- **PIT 品質**:優(ALFRED):逐 vintage 重建當時已知資訊,是修訂型總經序列做 PIT 檢定的黃金標準;FRED 本體則是最新修訂值(非 PIT),兩者要分清楚用。
- **解鎖**:TR-17 的 PIT 穩健性檢查(把 GW 中會被修訂的總經預測子換成 ALFRED vintage 重跑);Campbell-Thompson 的總經座位;GW 檔 2022 後 lty 的上游即 FRED
- **接入工程**:S(FRED)/ M(ALFRED vintage 邏輯:每序列×每 vintage 的對齊程式要寫對)
- **驗證方式**:官方 docs 頁 403(Cloudflare 擋 fetch);以 WebSearch 交叉多個來源(官方 Terms of Use 頁、fredr/fedfred 客戶端文件)確認免費+120 req/min+ALFRED vintage 參數

### Databento (GLBX.MDP3 CME 期貨,$125 credits + 月用量硬上限) — 🟡 <$5 硬上限 ◐部分驗證
- **URL**:https://databento.com/datasets/GLBX.MDP3
- **提供**:CME Globex 全品種逐合約資料,OHLCV-1d 到 MBO;原生連續合約 symbology(ES.c.0 / ES.n.0 / ES.v.0:calendar / open-interest / volume 三種 roll 規則,stype_in='continuous'),roll 方法明確可審計。ICE Futures Europe/Endex 亦支援。
- **免費層**:新帳戶 $125 免費 credits(6 個月到期,僅限 historical);註冊需綁卡。日線量級成本趨近零:OHLCV-1d 每筆 56 bytes,30 品種×16 年×252 天 ≈ 數 MB 未壓縮,按 $/GB 計費是幾美分——$125 夠這種用法用好幾年。
- **最低付費**:usage-based $/GB(小額);訂閱制 CME Standard plan $179/月(完全不需要)
- **爆量模型**:預設 pay-per-use(理論上無上限=風險),但官方 portal 支援 Owner/Admin 設定每月 usage limit,超限後直接封鎖資料請求到次月——設 $0–5 月上限後即為硬上限,bug 迴圈也刷不爆。這是本類唯一把 pay-per-use 變硬上限的付費源。
- **PIT 品質**:本類最佳:逐合約原始資料+明確 roll 規則,自己用 roll 日拼接『報酬』即為 PIT-clean 連續序列;無倖存者偏誤(所有掛牌合約都在);時戳來源有官方文件(2010–2017 段回填自 CME DataMine legacy FIX/FAST,ts 來自 tag 52)。注意:官方連續 symbology 給的是未調整拼接價,back-adjusted 仍是 roadmap 上的 feature idea——需自行 stitch returns(對 TSMOM 反而是正確做法)。
- **解鎖**:HOP/MOP TSMOM 多資產期貨原生棲地(docs/22 重測最高優先)的 2010-06 之後段:嚴謹、可審計的 20+ 品種面板;致命缺口:CME 歷史僅回溯到 2010-06-06(官方 blog『CME history extended to 2010』),單靠它湊不滿『20+ 品種×20+ 年』,需與 Pinnacle/AQR 拼接前段
- **接入工程**:M — API 順手(Python client 佳),但要寫 roll 報酬拼接 + 設 usage limit + 管理 credits 到期
- **驗證方式**:官方頁面 JS 渲染擋直接 fetch;經 WebSearch 取得官方頁面摘要:$125 credits/6 個月到期/需綁卡(官方 FAQ+cloudcredits)、月用量上限會封鎖請求(官方 portal billing docs)、2010-06-06 起點(官方 blog)、continuous symbology 三 roll 規則(官方 docs/blog/X)

### Yahoo Finance / yfinance 期貨 (=F) — 🟢 free ✅站上驗證
- **URL**:https://finance.yahoo.com/quote/ES%3DF/history/
- **提供**:免費前月連續期貨日線(=F 代碼),數十品種(CME/COMEX/NYMEX/CBOT 主力+部分外盤)。今日直接打 chart API 驗證:ES=F firstTradeDate=2000-09-18,GC=F=2000-08-30 ⇒ 約 25 年深度(多數品種 2000 年起,micro 類僅 2019+)。
- **免費層**:全免費、無 key;非官方 API,rate limit 與 ToS 風險自負(yfinance 每隔一陣子就要修)。
- **最低付費**:無
- **爆量模型**:無計費;風險是可用性(被擋)而非費用
- **PIT 品質**:差:未調整前月拼接——實測 ES=F chartPreviousClose=1485.25(2000 年真實價位)證明無 back-adjustment,roll 時點無文件 ⇒ roll 日的價格跳空會直接污染日報酬,TSMOM 月報酬會混入 carry 量級的假訊號;無逐合約資料可自行修正;偶有壞 tick。只能當 prototype/交叉驗證,不能當 HOP/MOP 正式檢定面板。
- **解鎖**:HOP/MOP 的快速 prototype 與 2000 年後 sanity check;不解鎖正式重測(roll 污染不可審計)
- **接入工程**:S — yfinance 兩行;但要自建壞資料過濾
- **驗證方式**:今日直接 curl query1.finance.yahoo.com/v8/finance/chart/ES=F 與 GC=F (range=max),讀取 firstTradeDate 與 chartPreviousClose 原始 JSON

### Stooq 連續期貨 (.f 代碼) — 🟢 free ◐部分驗證
- **URL**:https://stooq.com/db/h/
- **提供**:免費連續期貨日線(gc.f、cl.f、es.f、fgbl.f 等數十品種,含歐亞品種)+ 大宗歷史 zip 包;部分品種歷史遠早於 2000(記憶中 S&P 1982-、穀物更早),是免費源中唯一可能提供 20+ 年×20+ 品種的。
- **免費層**:免費、無註冊;但今日實測:per-symbol CSV 端點 (stooq.com/q/d/l/) 與 /db/h/ 頁面均回傳 SHA-256 PoW anti-bot JS challenge,curl/pandas-datareader 被擋——程式化抓取已死或不穩,手動瀏覽器下載(每 symbol CSV 或 bulk zip,有每日下載量上限的舊報告)仍可行。
- **最低付費**:無付費層
- **爆量模型**:無計費;風險是存取穩定性
- **PIT 品質**:弱-未知:roll 方法完全無文件、close 為調整後價(調整方式不透明)、無逐合約資料可審計 ⇒ 長史雖誘人但無法證明 PIT 乾淨;品種清單即當前活躍品種(宇宙層級有倖存者傾向)。
- **解鎖**:HOP/MOP 的 pre-2010 免費延伸候選——但因 roll 不可審計,只能當第二意見/交叉驗證,不能單獨承載 docs/22 重測
- **接入工程**:M — anti-bot 後只剩手動下載+整理數十個 CSV;一次性建檔可接受,月更麻煩
- **驗證方式**:今日 curl 六個 .f 代碼的 CSV 端點,實得 PoW challenge 頁(存取受阻已驗證);品種覆蓋與歷史深度來自記憶+第三方指南(chartoasis 確認 GC.F/CL.F 可下載,深度未確認)

### Pinnacle Data CLC (Continuously Linked Commodity) Database — 🔴 超預算 ✅站上驗證
- **URL**:https://pinnacledata2.com/clc.html
- **提供**:98 個期貨品種的連結連續序列,最深回溯 1969(黃豆系),多數 1970s 起;OHLC+量+未平倉;三種明確連結法:Reverse (Back) Adjusted / Non-Adjusted / Ratio Adjusted——正是學界與 TSMOM 複製研究常用的廉價長史標準。
- **免費層**:無免費層
- **最低付費**:$99 一次性買斷(買斷日為止的全歷史);更新 $20/月(3 個月起)或年約 $18/月
- **爆量模型**:固定價,零爆表風險;問題純粹是超出 $5/月框架($99 一次性攤 12 個月≈$8.25/月;更新訂閱是預算的 4 倍)。但注意:20+ 年回測本質上不需要更新——$99 買斷一次即拿到 1969–2026 靜態面板,之後用 Databento 續接。這是唯一 ≤$99 拿到 1969+ 原生連續期貨的路,值得使用者特批一次性支出。
- **PIT 品質**:中上:連結方法明確且提供未調整版可自行審計 roll;缺點:98 品種為『最受歡迎品種』= 宇宙層級有倖存者傾向;逐合約層級不提供(extended 版另購)。
- **解鎖**:HOP/MOP TSMOM 的完整原生棲地(20+ 品種 × 50+ 年)——docs/22 重測最高優先項的『唯一近預算解』;與 Databento 2010+ 拼接可互相驗證 roll 品質
- **接入工程**:M — ASCII/CSV 類格式,一次性 parser;無 API
- **驗證方式**:今日 WebFetch pinnacledata2.com/clc.html 逐字確認 $99.00、98 Commodities、1969 起點、三種連結法、更新 $20/月(3 個月 min)/$18 年約

### AQR Data Library — Time Series Momentum Factors (Monthly) — 🟢 free ◐部分驗證
- **URL**:https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Factors-Monthly
- **提供**:Moskowitz-Ooi-Pedersen TSMOM 因子月報酬(58 個流動期貨/遠期標的:股指/債/匯/商品),1985-01 起、月更;另有 Century of Factor Premia(1920 起)與原論文 data。不是原始期貨價格,是策略層報酬。
- **免費層**:完全免費 xlsx 直鏈下載,無註冊
- **最低付費**:無
- **爆量模型**:無計費
- **PIT 品質**:作為基準堪用:AQR 自建、方法照原論文、含交易成本假設文件;但它是廠商計算的策略報酬(不可分解 roll/宇宙),不能替代原始面板做方法變體檢定。
- **解鎖**:HOP/MOP 重測的長史外部基準(1985+,40 年):自建 TSMOM(Databento/Pinnacle)結果與 AQR 官方序列對表,是 docs/22 重測最便宜的正確性錨點
- **接入工程**:S — 單一 xlsx
- **驗證方式**:WebSearch 確認官方 dataset 頁與直鏈 xlsx 存在、1985-01 起、月更(未實際下載檔案)

### Nasdaq Data Link CHRIS (Wiki Continuous Futures) — 已死,除名 — 🟢 free ◐部分驗證
- **URL**:https://data.nasdaq.com/data/CHRIS-wiki-continuous-futures/documentation/introduction
- **提供**:(過去)99 個 ratio-adjusted 連續期貨。現況:官方標記 deprecated、不再更新——GitHub 上多個教科書 repo 的 CHRIS 範例已確認失效。Nasdaq Data Link 免費層已無任何可用期貨資料集。
- **免費層**:已無(dataset deprecated)
- **最低付費**:n/a
- **爆量模型**:n/a
- **PIT 品質**:n/a(死源)
- **解鎖**:無——列出僅為了正式關閉這條候選線索,避免之後再浪費時間
- **接入工程**:n/a
- **驗證方式**:WebSearch:官方 doc 頁仍在但 deprecated,PacktPublishing cookbook GitHub issue #5 確認範例失效

### CSI Data (Unfair Advantage) — 超預算,僅存檔 — 🔴 超預算 ⚠️僅記憶
- **URL**:https://www.csidata.com/
- **提供**:學術界常用的期貨長史商業源(Moskowitz et al. 原論文即用類似級別資料);逐合約+連續,1949 起部分品種。
- **免費層**:無
- **最低付費**:價目不公開(需聯絡銷售);記憶中個人版期貨訂閱歷來 $40+/月量級
- **爆量模型**:訂閱固定價,無爆表,但遠超預算
- **PIT 品質**:優(逐合約、含已下市合約)——但與本預算無關
- **解鎖**:無(預算外);僅在未來預算放寬時重訪
- **接入工程**:L — 專有軟體 Unfair Advantage 匯出
- **驗證方式**:WebSearch:官方站現行價目不公開、僅『聯絡銷售』;未能驗證現價,故 memory-only

## 7. 產業分類/小型股/國際/台股

**類別判定**:此缺口可在 $0/月 幾乎全數關閉，且推薦組合裡沒有任何 pay-per-use 爆表風險（全部是免費靜態檔或硬 rate-limit 拒絕制）。核心答案:(1) 產業分類——Ken French 49 產業組合(日+月、更新至 2026-05、zip 於 2026-07-01 剛更新、含 2008 全程、CRSP 建構無倖存者偏誤)「直接」解鎖 TR-21 產業面板翻案與 Moskowitz-Grinblatt 產業動量,完全不必自建分類管線;ticker→產業用 EDGAR SIC(實測可用)+FF49 SIC 定義檔,即 TR-03b 的免費 GICS 類先驗塊——真 GICS ticker 指派是 MSCI/S&P 授權品,免費世界不存在,SIC/FF49 是正確替代而非妥協。(2) 國際——Ken French developed/EM 3+5 因子(日+月)免費解 FF 國際價值;Stooq 有重大新發現:已部署 proof-of-work 反爬,程式化抓取實測全擋,只能瀏覽器手動批次,降級為輔助源。(3) 小型股是唯一部分受阻項:FF size 排序/雙排序組合免費解「組合層級」棲地,但「股票層級」歷史小型股面板受限——Tiingo 免費層 500 unique symbols/月是硬瓶頸、IWM CSV 只有現行成分(回測用=倖存者偏誤,且 bot 防護擋自動化)、歷史 Russell 成分是 FTSE 授權品;務實路線=EDGAR 全宇宙+市值過濾自建,或接受組合層級。(4) 台股 V2 全解:FinMind 免費 600 req/hr(實測文件)+TWSE 官方端點(實測可回溯 2010)+Fugle 免費層 60 calls/min 做即時端;FinMind Sponsor Pro 價格未能驗證(SPA)但免費層已夠用。仍被鎖:PIT 版 ticker-level GICS 史、歷史 Russell 成分清單、美股即時資料——三者皆無 $5 內解法,但對列出的 TR 翻案均非必要。

### Ken French Data Library — 49 Industry Portfolios + Size 組合 + 國際因子 — 🟢 free ✅站上驗證
- **URL**:https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- **提供**:現成的 5/10/12/17/30/38/48/49 產業組合報酬（日+月，含/不含股利，value/equal weighted），SIC→產業定義檔；另有 size 十分位組合、25 size×BM / size×momentum 雙排序組合；國際部分有 Developed/Europe/Japan/APxJ/NA 的 3+5 因子（日+月）與 Emerging 5 因子及國別組合。全部 CSV/TXT zip 直接下載
- **免費層**:完全免費、無註冊、無金鑰。已驗證資料更新至 2026-05；49_Industry_Portfolios_daily_CSV.zip 為 4.2MB、last-modified 2026-07-01。49 產業日報酬回溯至 1969、月報酬更早（含 2008 全程）
- **最低付費**:無付費層——學術公開資料
- **爆量模型**:無計費機制，零爆表風險（靜態檔案下載）
- **PIT 品質**:最佳等級：由 CRSP 建構，含下市股票（無倖存者偏誤），產業歸屬按當年 6 月的 SIC 指派（PIT 紀律）。注意：歷史值會隨 CRSP 修訂微幅重述（vintage 不凍結），且 2025 起改用 CIZ 格式檔（頁面明示），對月度研究影響極小
- **解鎖**:TR-21 吸收比率產業面板翻案（直接給 49 產業日報酬長史含 2008，不用自建分類管線——這是本類別最大解鎖）；Moskowitz-Grinblatt 產業動量（原論文即用此資料）；TR-03b GICS 先驗塊（用其 SIC 區間定義作免費分塊標準）；FF 國際價值（developed/EM 因子現成）；彩券異象小型股棲地可先用 size 十分位/雙排序組合層級近似
- **接入工程**:S — 單一 zip、格式眾所周知；建議直接 requests+pandas 解析（pandas-datareader 的 famafrench reader 可用但維護不穩）。唯一小坑：CSV 內含多個子表（VW/EW/annual）需切段
- **驗證方式**:WebFetch 主頁（確認資料集清單、更新至 2026-05、國際覆蓋、免費）；curl -I 直接 HEAD 49 產業日報酬 zip（HTTP 200、2026-07-01 更新）

### SEC EDGAR（submissions API + SIC codes + full index） — 🟢 free ✅站上驗證
- **URL**:https://data.sec.gov/submissions/
- **提供**:全體美股申報公司的 SIC 產業代碼、CIK/ticker 對照（company_tickers.json）、全部歷史申報索引與原文。SIC 可對映到 Ken French 49 產業定義，形成免費的 ticker→產業管線
- **免費層**:完全免費，fair-access 政策約 10 requests/秒（需自報 User-Agent）。實測 submissions API 正常：AAPL 回傳 SIC 3571 'Electronic Computers'+1000 筆近期申報
- **最低付費**:無付費層
- **爆量模型**:硬限制（超速=暫時封鎖 IP，無任何計費），零爆表風險
- **PIT 品質**:submissions API 的 SIC 是「現行」分類（非 PIT）；但歷史 PIT 可重建：每季 full index 與各 filing header 含申報當時的 SIC——工作量中等。倖存者偏誤：優——下市/破產公司檔案全保留
- **解鎖**:TR-03b GICS 先驗塊的 ticker→產業指派（美股全宇宙）；TR-21 若要股票層級產業面板（補 FF49 的成分視角）；小型股宇宙建構（全申報公司清單含微型股，比任何指數成分表更完整、無倖存者偏誤）
- **接入工程**:M — API 本身簡單（JSON），但 PIT 版 SIC 需解析歷史 filing headers；現行版 SIC 則是 S
- **驗證方式**:curl 實測 data.sec.gov/submissions/CIK0000320193.json 成功取得 SIC（sec.gov 說明頁對 fetcher 回 403，但 API 本體實測可用；10 req/s 政策為既有常識+未於本次頁面重新確認）

### FinMind（台股開源資料 API） — 🟢 free ✅站上驗證
- **URL**:https://finmind.github.io/
- **提供**:50+ 台股資料集：日價（含還原）、財報三表、三大法人買賣超、融資融券、股權分散、股利政策、即時/歷史 tick（2019-05 起）。台股 V2 的主資料源
- **免費層**:已驗證現行額度：未註冊 300 requests/hr；免費註冊+token 後 600 requests/hr（quickstart 頁原文引述）。專案活躍：release 2.0.4 於 2026-06-26
- **最低付費**:有 Sponsor / 新推出的 Sponsor Pro 付費層（FB 社群貼文證實存在），但價格頁是 SPA 無法抓取、本次未能驗證確切價格——記憶中約數百 TWD/月級距，需登入官網確認。免費 600/hr 對日更批次已足夠
- **爆量模型**:硬限制（超額直接拒絕請求，可查 user_info 端點看用量），無信用卡、無爆表風險
- **PIT 品質**:中等：價量與籌碼資料為逐日快照存檔（近似 PIT）；財報有公告日欄位可做 PIT 對齊但需自己小心用公告日而非期末日；下市股覆蓋不完整（倖存者偏誤需抽查）；產業分類僅現行版
- **解鎖**:台股 V2 全部資料需求（價量+籌碼+財報）；台股產業分類（現行）
- **接入工程**:S — 官方 Python SDK（pip install finmind）或直接 REST，文件完整
- **驗證方式**:WebFetch finmind.github.io/quickstart/（300/600 per hr 原文）+ WebSearch 確認 Sponsor Pro 存在 + WebFetch GitHub repo（2.0.4 release 2026-06、維護中）；Sponsor 價格頁（SPA）抓取失敗故價格未驗證

### TWSE 官方端點（OpenAPI + 舊制 exchangeReport） — 🟢 free ✅站上驗證
- **URL**:https://openapi.twse.com.tw/
- **提供**:OpenAPI：上市公司每日成交、指數、本益比/殖利率、財報摘要（按產業別分組）、ESG 等——多為現時快照。舊制 www.twse.com.tw/rwd/.../STOCK_DAY：逐月歷史日 K，實測 2330 可取回 2010-01（民國 99 年）資料。另 isin.twse.com.tw 有含產業別的上市證券清單
- **免費層**:完全免費、無金鑰無註冊。無正式文件化 rate limit，但社群共識：twse.com.tw 高頻抓取會被暫時封 IP（安全速率約 3 req/5s）
- **最低付費**:無付費層
- **爆量模型**:硬限制（IP ban，非計費），零爆表風險；但需在爬取管線內建節流
- **PIT 品質**:價格資料為交易所原始紀錄（權威、可回溯 2010）；但僅上市（TWSE），上櫃需另打 TPEx 同型端點；產業別為現行分類非 PIT；下市股歷史仍可查（依代碼），倖存者偏誤可控
- **解鎖**:台股 V2 的權威價格校驗源（對 FinMind 交叉驗證）；台股產業分類（現行）；OpenAPI 財報按產業分組可輔助台股產業面板
- **接入工程**:M — 逐股逐月分頁抓取需節流與 ROC 年份轉換；OpenAPI 單端點則是 S
- **驗證方式**:WebFetch openapi.twse.com.tw/v1/swagger.json（端點清單、無驗證機制）+ curl 實測 STOCK_DAY?date=20100104&stockNo=2330 回傳 stat:OK、20 筆 2010 年資料

### Fugle 富果行情 API — 🟢 free ✅站上驗證
- **URL**:https://developer.fugle.tw/docs/pricing
- **提供**:台股即時行情 WebSocket、盤中 intraday API、歷史 K 線。台股 V2 若需要準即時行情的候選
- **免費層**:已驗證：免費層需註冊富果會員（不需開券商戶）：WebSocket 5 訂閱數/1 連線、intraday 與歷史各 60 calls/min；不含 snapshot/技術指標/選擇權
- **最低付費**:Developer NT$1,499/月（≈US$46）：300 訂閱、600 calls/min——遠超預算
- **爆量模型**:硬限制（rate limit 拒絕），免費層無計費資訊、零爆表風險
- **PIT 品質**:即時/近期資料源，非歷史研究用；歷史 K 線深度有限。PIT 不適用（拿來做執行端而非回測端）
- **解鎖**:台股 V2 的即時報價/監控端（回測資料仍靠 FinMind+TWSE）
- **接入工程**:S — 官方 SDK 與文件完整
- **驗證方式**:WebFetch developer.fugle.tw/docs/pricing（免費層限額與 NT$1,499 Developer 價格原文）

### yfinance sector/industry 欄位（Yahoo Finance 非官方） — 🟢 free ✅站上驗證
- **URL**:https://github.com/ranaroussi/yfinance
- **提供**:任意 ticker 的現行 sector/industry（Yahoo 自有分類，粒度近似 GICS sector/industry），美股+台股皆可。實測 AAPL=Technology/Consumer Electronics、2330.TW=Technology/Semiconductors
- **免費層**:免費、無金鑰；無明文限額但為爬蟲性質，Yahoo 改版即斷（2025-26 已多次發生 decrypt/ratelimit 事件），需視為易碎源
- **最低付費**:無付費層（Yahoo Finance 官方 API 已不存在）
- **爆量模型**:硬限制（被 Yahoo 暫時封鎖），零計費風險；但穩定性風險高——不可當管線關鍵路徑
- **PIT 品質**:差：僅現行分類，無歷史版本——拿今天的分類套整段回測=前視偏誤；下市股票常無資料=倖存者偏誤。只能用於「現行宇宙」的標註，不可用於歷史面板
- **解鎖**:TR-03b 現行宇宙的快速產業標註（與 EDGAR SIC 交叉驗證）；台股現行分類補充。不解鎖任何需要 PIT 的翻案
- **接入工程**:S — 專案已在用 yfinance
- **驗證方式**:本機 python 實測 yf.Ticker('AAPL').info 與 2330.TW 均回傳 sector/industry（2026-07-09 當日）

### GitHub GICS 結構對照資料（uknj gist / py-gics / NAICS crosswalks） — 🟢 free ◐部分驗證
- **URL**:https://gist.github.com/uknj/c9bcf66ab379a35fcc8758f9a6c86ceb
- **提供**:GICS 代碼層級樹（sector→industry group→industry→sub-industry，2023-03 版）、py-gics 解析庫、NAICS↔SIC↔GICS 概念對照表。注意：只有「分類體系結構」，沒有 ticker→GICS 的指派——那是 MSCI/S&P 授權資料，免費世界拿不到
- **免費層**:免費（GitHub 公開）
- **最低付費**:真正的 ticker-level GICS 歷史指派需 MSCI/S&P 授權（機構級價格，完全超預算）
- **爆量模型**:靜態檔案，無風險
- **PIT 品質**:結構表本身有版本（2023-03 GICS 改版），但無 ticker 指派故 PIT 問題不適用；若用 NAICS/SIC crosswalk 近似 GICS，映射是多對多、有雜訊
- **解鎖**:TR-03b 若想把先驗塊標成 GICS 語彙：用此結構樹+EDGAR SIC crosswalk 近似。誠實結論：GICS『類』的先驗塊該直接用 FF49/SIC 定義，別執著 GICS 本尊
- **接入工程**:S — 單一 CSV/gist
- **驗證方式**:WebSearch 定位 gist 與 py-gics repo（未逐檔開啟驗證內容完整性）

### iShares IWM holdings CSV（Russell 2000 現行成分） — 🟢 free ◐部分驗證
- **URL**:https://www.ishares.com/us/products/239710/ishares-russell-2000-etf
- **提供**:IWM 全持股每日更新 CSV（~1,900 檔，含 ticker、名稱、sector、權重、市值）＝免費的 Russell 2000 現行成分近似
- **免費層**:免費瀏覽器下載；本次 curl 實測被 bot 防護擋（.ajax 端點回 HTML 而非 CSV）——自動化管線需帶 cookie/瀏覽器或改手動月更
- **最低付費**:無付費層；但「歷史」成分清單是 FTSE Russell 授權資料（超預算）
- **爆量模型**:靜態下載，無計費風險
- **PIT 品質**:差（用於歷史研究時）：僅現行快照，無歷史成分——用今天的成分回測=倖存者偏誤+指數重構偏誤。可從今天起逐月存檔自建 PIT（前瞻性補救）
- **解鎖**:彩券異象小型股棲地的「現行宇宙」定義與 live 監控；不解鎖歷史小型股面板（該用 FF size 排序組合或 EDGAR 全宇宙+市值過濾替代）
- **接入工程**:M — bot 防護使自動化不穩；手動每月下載+存檔則 S
- **驗證方式**:curl 兩次實測 .ajax CSV 端點（含 referer/browser UA）均回 HTML bot 頁——確認免費但自動化受阻；持股 CSV 可下載為業界常識+未能於本次程式化重現

### Tiingo（免費層） — 🟢 free ✅站上驗證
- **URL**:https://www.tiingo.com/about/pricing
- **提供**:美股+部分國際 EOD 30+ 年歷史、基本面 5 年（免費層）、IEX 即時。小型股覆蓋佳（含微型股）
- **免費層**:已驗證現行：50 req/hr、1,000 req/day、每月 500 個 unique symbols、1GB 頻寬——500 symbols/月是小型股面板的硬瓶頸（Russell 2000 全宇宙需 4 個月輪完，無法月度全刷）
- **最低付費**:Power US$30/月（解鎖全部 10 萬+ symbols、10k req/hr）——超預算 6 倍
- **爆量模型**:硬限制（配額用完即拒絕，非後計費），零爆表風險
- **PIT 品質**:中等：EOD 調整價品質好、含部分下市股；但無 PIT 宇宙/成分概念，基本面免費僅 5 年且非 PIT 快照
- **解鎖**:小型股「子樣本」研究（每月 500 檔內，例如彩券異象 top-decile 候選池的深度驗證）；yfinance 的品質校驗源。不解鎖全宇宙小型股面板
- **接入工程**:S — REST+官方文件清楚，token 制
- **驗證方式**:WebFetch tiingo.com/about/pricing（50/hr、1000/day、500 symbols、Power $30 原文）

### EODHD — 🔴 超預算 ✅站上驗證
- **URL**:https://eodhd.com/pricing
- **提供**:全球 60+ 交易所 EOD（含台股 .TW、國際小型股）、30+ 年歷史、基本面
- **免費層**:已驗證：20 API calls/day——僅夠 demo，做不了任何面板
- **最低付費**:All World US$19.99/月（10 萬 calls/day）——最便宜層即超預算 4 倍；基本面層 $59.99
- **爆量模型**:訂閱制硬額度（無 pay-per-use 爆表），但入場價即超budget
- **PIT 品質**:中等：EOD 品質可，含下市股（宣稱）；無 PIT 成分史
- **解鎖**:理論上一站解鎖國際+小型股+台股，但在本預算下不解鎖任何東西——列入以誠實排除
- **接入工程**:S（若付費）
- **驗證方式**:WebFetch eodhd.com/pricing（20 calls/day 免費、$19.99 最低付費層原文）

### Stooq — 🟢 free ◐部分驗證
- **URL**:https://stooq.com/db/h/
- **提供**:免費歷史 CSV：美股、波蘭、德/日/英/港指數與個股、外匯、加密，日/小時/5分線；db/h 有整包歷史資料庫下載。國際指數長史的免費補充源
- **免費層**:免費無註冊，但（a）眾所周知的低「daily hits limit」（超過回 'Exceeded the daily hits limit'）；（b)重要新發現：本次 curl 實測所有 CSV 端點（^spx、2330.tw、^dax）均被 SHA-256 proof-of-work JS 挑戰擋下——目前程式化抓取已基本不可行，pandas-datareader 的 stooq reader 很可能已壞
- **最低付費**:無付費層
- **爆量模型**:硬限制（daily hits + PoW 反爬），零計費風險；但可用性風險高
- **PIT 品質**:中等：指數層級長史 OK；個股含部分下市但覆蓋不透明；台股個股覆蓋未能驗證（被擋）
- **解鎖**:國際指數/市場長史的手動批次補充（瀏覽器下載 db/h 整包仍可行）；不建議作為自動化管線依賴。FF 國際因子（Ken French）才是國際擴充的主力
- **接入工程**:M — 需瀏覽器/手動下載繞過 PoW；整包 db 下載後本地解析為 S
- **驗證方式**:curl 實測三個 CSV 端點全部回 proof-of-work 挑戰頁（2026-07-09）+ WebSearch 確認 daily hits limit 慣例

### Damodaran Data（NYU Stern） — 🟢 free ✅站上驗證
- **URL**:https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html
- **提供**:產業層級聚合資料（beta、margins、multiples、成本資本）按美國/全球/區域分，每年 1 月更新（最近 2026-01-09），含歷年 Archived Data。注意：公司層級清單已因資料商授權停止分享（頁面明示）
- **免費層**:完全免費
- **最低付費**:無付費層
- **爆量模型**:靜態 Excel 下載，零風險
- **PIT 品質**:產業聚合為年度 vintage（archived 歷年版本=難得的 PIT 產業特徵史）；但無公司→產業成分明細，無法建 ticker 面板
- **解鎖**:TR-03b 產業先驗的輔助特徵（產業 beta/槓桿年度史）；不解鎖 TR-21（需要報酬面板，FF49 已解）
- **接入工程**:M — Excel 格式逐年不一致，archived 需逐檔清理
- **驗證方式**:WebFetch data.html（2026-01-09 更新、archived data 存在、公司層級停止分享之原文）
