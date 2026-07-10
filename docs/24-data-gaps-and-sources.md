# 資料缺口盤點 × 免費/極低成本資料源盡職調查(2026-07)

> 回應兩個問題:①哪些項目因無法免費取得資料而**無法實測**、或**測得淺可能有偏誤**?
> ②有沒有免費或**每月 <$5(硬上限、無爆量加價風險)**的方法取得股價/財報/消息/情緒等資料來補這些缺口?
> 方法:8-agent 工作流——1 個掃全部 docs 建需求清單(45 項),7 個分類研究員**上站驗證 2026-07 現行
> 定價與額度**(每項標注實際查證頁面與信心等級;70 個來源)。完整逐源細節在工作流輸出,本檔為決策版。
> 預算紀律:只推薦「免費」或「硬上限」方案(超額=429 拒絕,不扣款);**唯一要避開的地雷=GDELT 走
> BigQuery(pay-per-TB 無上限,一個查詢就能燒 $5+)——一律走 raw CSV**。

---

## Part A — 受阻與偏誤風險清單(45 項,三類)

### A1. 完全無法實測(untestable-N/A)

| 項目 | 缺什麼 | 本輪調查後的新狀態 |
|---|---|---|
| TR-09 BSM 定價、covered-call/CSP 收益 sleeve、VIX 期限結構 | PIT 歷史選擇權鏈 | **大幅解鎖**:OptionsDX 免費 2010-2023(SPY/SPX/QQQ+權值股)+ DoltHub 2019-至今(~2000 檔) |
| GEX(dealer gamma)回測 | 歷史 OI | **部分解鎖**:ThetaData 免費層有 **2023-06 起的 OI 歷史**——比自建快照(2026-07 起)多 3 年;pre-2023 OI 仍鎖(CBOE/DeltaNeutral 超預算) |
| 選擇權隱含預測子(Xing smirk、Cremers-Weinbaum、AABC ΔIV)、BKM/Carr-Wu 個股 VRP | 個股鏈 IV 橫斷面 | **部分解鎖**(同上兩源;個股覆蓋 2019+);指數層 VRP 可用 VIX²(免費 1990-)先測 |
| ORB(Zarattini)、LPS 精確版、日內 AR | 分鐘級歷史 | **解鎖(2016+)**:Alpaca 免費層 SIP 分鐘 bar;pre-2016 只有 QuantConnect 雲端(平台內,不可匯出) |
| 盤中 footprint/orderflow、Obizhaeva-Wang LOB 韌性 | tick/LOB | 仍鎖($0 不可達);Databento $125 credits 可做一次性 tick 抽查 |
| TSMOM/HOP 期貨原生棲地(docs/22 重測最高優先) | 20+ 品種 × 20+ 年連續合約 | **半解鎖**:Databento(2010-06+,$125 credits+月上限=硬上限)+ AQR TSMOM 因子序列(1985+,免費基準);完整長史唯一近預算解=**Pinnacle CLC $99 一次性買斷**(1969+,98 品種)→ 需使用者特批 |
| TR-17 KMZ 的 Goyal-Welch 95 年座位 | GW 總經預測子集 | **✅ 已執行(TR-17b,2026-07-11)**:Amit Goyal 官網免費;結果=REPLICATED-BUT-EXPLAINED(Nagel 源頭確認) |
| TR-21 吸收比率的產業面板+含 2008 長史 | ~50 產業組合日報酬 | **✅ 已執行(TR-21b,2026-07-11)**:KF 49 產業日頻;結果=水位反轉/尖峰弱複製/閘門第 5 死(分裂判定) |
| IBES 級分析師修正「歷史」 | 修正序列史 | **此路不通**($0-5 無合法途徑;Zacks ZEEH/IBES 數千美元/年)→ 見 Part C 的三件替代拼圖 |
| 噪音交易者 CEF 折價、A-C 機構規模、BLB 1897 原座位 | 各自特殊資料 | 仍鎖(影響低,誠實維持 N/A) |

### A2. 測得淺、可能有偏(shallow-bias-risk)——偏誤方向已標注

| 項目 | 偏誤方向 | 本輪後的補救路徑 |
|---|---|---|
| **倖存者偏誤(全域)** | 全部絕對報酬偏樂觀 [+1.26%, +2.02%]/yr | fja05680/sp500(PIT 成分 1996+)+ AV LISTING_STATUS(下市清單+as-of 宇宙 2010+)+ **Tiingo 免費層有下市股價格序列**(14,760 檔 endDate<2020;500 symbols/月輪換回填)→ ~80% 可 $0 關閉;殘餘=2008 大型破產股價格(LEH/BSC 缺)→ QuantConnect 免費雲端做一次性驗證重放 |
| 下市終端報酬只有區間(TR-13) | 真值未定 | 同上組合可收斂大半;CRSP 級點估計仍需付費 |
| 短歷史(僅 3-4 個真熊) | regime 推論無統計力;高 beta 假 PASS/防禦假 FAIL | Tiingo 30+ 年史 + KF 49 產業(1969+)+ GW(1871+)→ 大幅補強 |
| GP regime-universality(唯一 PASSED 因子)+ **2025-26 IC 轉負 WATCH** | 時代特定風險 | 長史+PIT 宇宙落地後複驗(同上) |
| 旗艦月頻 n=131(HLZ 差 0.05-0.36) | 統計力不足非方向偏誤 | 長史重放(QuantConnect/Tiingo)可增月數 |
| curated 47 檔、手挑清單 | 絕對數字偏樂觀 | 僅相對宣稱(F11 已制度化) |
| McLean-Pontiff haircut ~35% 未自校準 | 方向未知 | OSAP 資料 ingest(免費)後可系統性量測 |
| LPS 拆解用 open/close 近似 | 無法分辨衰退 vs 度量誤差 | Alpaca 分鐘資料落地後做精確版 |

### A3. 在錯的座位測過(wrong-seat-tested)——FAILED 不定罪機制本身

| 項目 | 原生座位 | 解鎖狀態 |
|---|---|---|
| 價值(FF)、PEAD、內部人、彩券異象(IVOL/MAX)、BAB | 小型股/國際/長歷史 | 組合層級:KF size/國際因子免費;**股票層級小型股面板=部分受阻**(Tiingo 輪換或 EDGAR+市值自建;歷史 Russell 成分=FTSE 授權品,無 $5 解) |
| KMZ 複雜度 | 95 年 GW 總經預測子 | **✅ $0 解鎖**(GW 免費) |
| Vegas 雙通道 | FX 日內 | 仍鎖(範圍外,無採購計畫) |
| Donchian/突破家族、Kalman pairs 日內版 | 多市場期貨/日內 | 期貨=Databento/Pinnacle 路徑;日內=Alpaca 2016+ |

---

## Part B — 資料源判定(七類,只列推薦與明確排除)

### B1. 日內分鐘資料 → **$0 可關閉(2016+)**
- **主引擎:Alpaca Market Data Basic(免費,今日站上驗證)**:SIP 全市場分鐘 bar 2016+、200 calls/min、
  歷史 tick trades/quotes 也有;唯一限制=查不到最近 15 分鐘(研究無礙)。500 檔×9.5 年一次回填 ~4-6
  小時,之後每日增量。**硬上限:超速 429,免費層無計費管道。**
- 交叉驗證:Massive(前 Polygon)免費層(5/min、~2 年)、FirstRate 免費樣本(SPY/QQQ 等 1 年 1-min)。
- pre-2016:QuantConnect 免費雲端(1998+,無倖存者偏誤,但研究須移植進 LEAN、資料不可匯出)。
- **排除**:Alpha Vantage(25 req/day 回填不可行)、Finnhub(candle 端點免費層 403)、IBKR(API 要 L1 訂閱+pacing 極慢)。

### B2. 選擇權歷史 → **$0 可大幅關閉**
- **OptionsDX(免費,站上驗證)**:SPY/SPX/QQQ/TSLA/AAPL/NVDA 等 10 檔 EOD 鏈 **2010-2023**(含 IV/greeks),月度 CSV,免結帳資訊。
- **DoltHub post-no-preference/options(免費,今日 SQL 實測)**:~2000 檔 EOD 鏈 **2019-02 至 2026-07-08**(兩天前still updating!),git 版本化=可稽核 PIT;無 OI。
- **ThetaData FREE 層(站上驗證,本類 sleeper hit)**:EOD + **歷史 OI 自 2023-06-01**、30 req/min、免綁卡——**唯一免費 OI 歷史,GEX 回測直接多 3 年**。
- 自建 yfinance 快照(已運轉)降級為前向交叉驗證。**pre-2023 OI 誠實維持鎖死**(CBOE DataShop/DeltaNeutral $585+/yr 超預算)。
- 注意:免費源的 vendor IV/greeks 應從報價重算(順便就是 TR-09 的驗證)。

### B3. 倖存者/PIT 宇宙/長歷史 → **$0 關閉 ~80%**
- **fja05680/sp500(GitHub,2026-06-08 仍在維護)**:PIT S&P 成分 1996+;Wikipedia 變動表(1980+)當上游驗證。
- **Alpha Vantage LISTING_STATUS(免費,今日 live 實測)**:全下市清單+`date` 參數可重建 2010+ 任意時點上市宇宙。25 req/day 硬上限(此用途只需幾個呼叫)。
- **Tiingo 免費層(站上驗證)**:**下市股價格序列**(107,364 ticker 清單中 14,760 檔 endDate<2020,如 MER 到 2008-12-31);500 unique symbols/月=輪換回填數月。Ticker 重用要用 (ticker, 日期區間) 鍵(WB=Weibo 蓋掉 Wachovia)。
- 殘餘:2008 大型破產股(LEH/BSC/舊 GM)Tiingo 缺 → **QuantConnect 免費雲端一次性驗證重放**定界偏誤;若證明 material 再考慮 EODHD $19.99/mo(4× 預算,先不買)。
- **排除/存檔**:Norgate ~$52.5/mo、Sharadar ~$40-50/yr 級(皆 10× 預算);Stooq **今日實測已上 anti-bot PoW 牆**,程式化抓取死,降級為手動備援。

### B4. 新聞/情緒 → **$0 可關閉**
- **SEC EDGAR 8-K(免費,10 req/s)**:PIT 最完美事件流(accepted timestamp 到秒,1994+)——事件研究黃金標準;專案已有 EDGAR 管線,邊際成本極低。
- **GDELT(免費)**:1979+(日頻)/2015+(15 分鐘級)全量新聞+tone;**只走 raw CSV,絕不走 BigQuery**。
- **Baker-Wurgler 情緒指數(免費,站上驗證)**:SENTIMENT.xlsx 1965-07~2023-12——直接解鎖 B-W 情緒因子(注意:全樣本 PCA 構建,非 PIT,只適合因子研究);**AAII 週頻調查(1987+)**免費補充。
- **Alpha Vantage NEWS_SENTIMENT(免費 25/day)**:ticker 級金融情緒 ~2022-03 起,LLM 情緒層的現成 benchmark。
- 仍鎖:2022 前 ticker 級金融情緒史(用 8-K+GDELT tone 代理)、社群歷史(Pushshift 已死、StockTwits 關新註冊、X 付費牆)→ 只能前向收集。

### B5. 基本面擴充/分析師預估 → **基本面 $0 大半可關;修正史此路不通,三件替代拼圖**
- **SimFin 免費層(站上驗證)**:5,000 檔美股標準化三表+比率,bulk CSV,**有 REPORT/PUBLISH/RESTATED_DATE=真 PIT**;5 年史(近窗交叉驗證 EDGAR 用)。
- **分析師修正史=正式判「此路不通」**(IBES/WRDS、Zacks ZEEH 皆機構級數千美元/年,無合法免費副本)。替代:
  1. **Alpha Vantage EARNINGS(免費)**:每季公告時點的 estimatedEPS/surprise 深歷史 → **共識版 SUE 精緻化直接可做**;
  2. **yfinance eps_trend/eps_revisions/price targets 每週快照 collect-forward——立即啟動**(同 options 快照模式,12-18 個月後 docs/11 頭號 alt-data 因子才有樣本;時間敏感);
  3. Finnhub 免費 recommendation trends(月頻多年史)當評級面代理。

### B6. 總經長史/期貨 → **總經 $0 完全關閉;期貨半關閉+一個 $99 特批選項**
- **Goyal-Welch(免費,今日站上確認「Updated data (up to 2025)」)**:TR-17 KMZ 翻案條件**直接滿足**;配 Shiller(1871+)交叉驗證、**FRED/ALFRED**(免費;ALFRED vintage=全 stack 唯一真 PIT 總經)。
- 期貨:**Databento $125 註冊 credits + 官方月用量上限(超限封鎖請求=硬上限)**——CME 2010-06+ 逐合約+官方連續 symbology(三種 roll 規則可審計);日線量級只吃幾美分。**AQR TSMOM 因子序列(1985+,免費)**當外部基準。Yahoo `=F`(2000+)僅 prototype(未調整拼接,roll 跳空污染)。
- **完整 20+ 品種×20+ 年原始面板:唯一近預算解=Pinnacle CLC $99 一次性買斷**(98 品種、1969+、三種連結法、買斷不需訂閱)→ **提請使用者特批的一次性支出**;不批則 HOP/MOP 做 2010+ 縮短版+AQR 對表。
- 排除:Nasdaq CHRIS 已死(deprecated 確認)、CSI 超預算。

### B7. 產業分類/國際/台股 → **$0 幾乎全關**
- **Ken French 49 產業組合(免費,zip 2026-07-01 剛更新)**:日報酬 1969+、CRSP 建構無倖存者偏誤、含 2008 全程——**直接解鎖 TR-21 產業面板翻案 + Moskowitz-Grinblatt 產業動量,零工程**;SIC 區間定義檔+EDGAR SIC(免費)=TR-03b 的 GICS 類先驗塊。真 GICS ticker 指派=MSCI/S&P 授權品,免費不存在,SIC/FF49 是正確替代。
- 國際:KF developed/EM 3+5 因子(日+月)免費。
- 小型股:組合層級 KF size 排序免費;**股票層級=唯一部分受阻**(歷史 Russell 成分=FTSE 授權品;務實路線=EDGAR 全宇宙+市值過濾自建,或 Tiingo 輪換)。
- 台股 V2:FinMind 免費 600 req/hr + TWSE OpenAPI(2010+ 實測)+ Fugle 免費層。

---

## Part C — 行動計畫(依解鎖價值排序;除注明外全部 $0)

| # | 行動 | 解鎖 | 成本/模式 |
|---|---|---|---|
| 1 | ~~**ingest Goyal-Welch** → 重跑 TR-17 KMZ 95 年座位~~ **✅ 完成(2026-07-11,TR-17b)**:VoC 複現但被 vol-timing+VTM 張成=REPLICATED-BUT-EXPLAINED;Campbell-Thompson 原生座位成 S 級佇列項 | KMZ 翻案(已執行)、C-T 解鎖 | $0,S 工程 |
| 2 | ~~**ingest KF 49 產業日報酬** → TR-21 產業版~~ **✅ 完成(2026-07-11,TR-21b)**:水位反轉/尖峰弱複製/閘門第 5 死;M-G 產業動量 + TR-03b GICS 塊仍佇列(面板已接線) | 三個翻案(1 done,2 解鎖) | $0,S 工程 |
| 3 | **ThetaData 免費層 + OptionsDX + DoltHub** → GEX(2023-06+)/VRP/TR-09 | 選擇權維度提前 3-16 年 | $0,M 工程(Theta Terminal 本地跑) |
| 4 | **yfinance 分析師預估每週快照 collect-forward——立即啟動(時間敏感)** | docs/11 頭號 alt-data 因子(12-18 個月後可測) | $0,S(仿 options 快照) |
| 5 | **AV EARNINGS 慢爬**(25/day)→ 共識版 SUE | PEAD 精緻版 | $0,寫一次讓它滴灌 |
| 6 | **Alpaca 分鐘回填 2016+**(一次 4-6 小時) | ORB/LPS 精確版/日內 AR | $0,S-M |
| 7 | **Tiingo 下市股輪換回填 + fja05680 PIT 成分** | 倖存者區間收斂、F11、長史 | $0,M(數月輪換) |
| 8 | SimFin bulk + EDGAR 交叉驗證;GDELT/8-K/B-W/AAII 情緒層 | 基本面品質保險+情緒因子 | $0,S-M |
| 9 | **[特批項] Pinnacle CLC $99 一次性** | HOP/MOP TSMOM 完整棲地(1969+)——docs/22 重測最高優先項的唯一近預算解 | 一次性 $99(超月費框架,**待使用者決定**;不批做 Databento 2010+ 縮短版) |
| 10 | QuantConnect 一次性 2008 重放(驗證 Tiingo 面板的破產股偏誤界) | 旗艦長史重放的誠實性 | $0,L(LEAN 移植) |

**仍然無 $5 解、誠實維持鎖死**:pre-2023 個股 OI、盤中 tick/LOB 常態源、IBES 修正史回填、
真 GICS ticker-level 歷史、歷史 Russell 成分、美股即時(<15 分鐘)資料。每項的翻案條件維持
在 docs/19/22,價格標籤已更新(例:修正史=數千美元/年=機構級)。

**工具選型補篇(2026-07-11)**:Dataroma/13F 取得路徑、開源 API wrapper(edgartools/alpaca-py/fredapi-ALFRED/simfin/tiingo/gdeltdoc 六個 adopt)、反爬蟲工具階梯(curl_cffi 為 Tier-1 首選;GHA datacenter-IP 對 Cloudflare 類牆無 $0 解的誠實警告)→ 見 [refs/scraping-and-apis.md](refs/scraping-and-apis.md)。

*2026-07-10。工作流:8 agents、70 sources、258 tool calls;信心等級 verified-on-site 為主。
G-S 註腳:這次調查本身就是「用工程時間換資訊成本」——多數缺口的市價其實是 $0+工程,真正的
稀缺品(修正史、tick、pre-2023 OI)才有正的美元價格。*
