# 爬取策略與開源 API 選型(Dataroma/13F、API wrapper、反爬蟲工具階梯)

> 2026-07-11,3-agent 工作流,全部**當日 GitHub/站上驗證**(stars/最後 commit/授權/反爬姿態)。
> 場景約束:$0 預算、Python/uv、GitHub Actions cron(**datacenter IP**——見 §3 的關鍵警告)、低頻研究抓取。

---

## §1 Dataroma 與 13F:研究級正路 = EDGAR 直取

| 路徑 | 判定 | 理由 |
|---|---|---|
| **SEC EDGAR 13F-HR 直取** | ✅ **adopt** | primary source、免費、官方;**PIT 完美**(acceptance timestamp 到秒,可做「訊號只在公開後可用」的滯後正確回測);~84 位經理人×季度的量級在 10 req/s 限制下毫無壓力;另有官方季度 bulk zip 可全市場回填。實測:帶合規 UA 打 `data.sec.gov/submissions/CIK0001067983.json` 成功(Berkshire,44 筆 13F) |
| **edgartools(dgunning)** | ✅ **adopt** | 2,462★、**兩天前才 push**、v5.42.0、MIT、原生 `ThirteenF` 物件直接給 holdings DataFrame;**同時是我們自寫 EDGAR connector 的升級路徑**(戰場驗證的 XBRL 標準化、20+ filing 類型)——增量遷移:舊已驗證流程保留,新 filing 類型(13F/Form 4/XBRL 跨公司)用它 |
| **Dataroma(爬站)** | ⚠️ **watch(僅策展)** | 實測:無 robots.txt、無 Cloudflare、裸 curl 都 200——**技術上零反爬,但那是因為它是 Bluehost 共享主機上的單人興趣站**。非 PIT(頁面=站主當前策展狀態,無版本紀錄)。**真正價值=「選誰」的 84 人名單**;正確整合=取名單→對映 CIK→從 EDGAR 取原始 13F。investment-dashboard 既有 ETL 保留作 UI/watchlist,本 repo 不在其數字上做研究 |
| Dataroma 開源爬蟲(op7ic 等) | ❌ reject | 生態不存在成熟品(最活躍僅 12★);「沒人認真維護 Dataroma scraper,因為認真的人直接去 EDGAR」 |
| 13f.info | ❌ reject(留作人工 QA) | 站活著、有未文件化 JSON endpoint(實測可用),但源碼 2024-08 停更、無 API 契約——不當 pipeline 依賴;開發期肉眼比對 edgartools 解析結果用 |

**訊號誠實性備忘**:13F 天生 45 天滯後+只有多頭+季度快照;文獻(Martin & Puthenpurackal 2008:延遲複製巴菲特持股 1976-2006 年勝 S&P ~10.75%)支持「慢速克隆」仍是可行研究方向——進 fabric 時照常 F0 預先承諾+Nagel 對照。

## §2 開源 API wrapper 選型(省接入碼)

**✅ adopt(六個,全部當日驗證活躍)**:

| 套件 | 用途 | 現況 |
|---|---|---|
| **edgartools** | EDGAR 全能(13F/Form4/XBRL) | 2,462★,push 昨天,MIT |
| **alpaca-py**(官方) | 分鐘 bar 回填(docs/24 主引擎) | 1,419★,push 今天,Apache-2.0 |
| **fredapi** | FRED+**ALFRED vintage**(`get_series_all_releases`=真 PIT 總經) | 1,623★,API 凍結穩定 |
| **simfin**(官方) | 基本面 bulk CSV+本地快取(完美貼合 Actions 批次模式) | 340★,MIT |
| **tiingo-python** | Tiingo EOD/下市股(薄封裝,死了也只是 50 行 requests) | 315★,MIT |
| **gdeltdoc** | GDELT DOC 查詢字串建構(免金鑰) | 224★,穩定 API 不腐 |

**❌ reject / ⚠️ watch(附理由,關閉線索)**:

- **OpenBB**:健康(70k★)但**三振**——只覆蓋我們已直連的 5 個源、**AGPLv3 授權地雷**(與 investment-dashboard 整合/散布計畫衝突)、重依賴樹。留作 provider 標準化的參考實作。
- **thetadata-python**:官方已 **ARCHIVED**(2024-06)→ ThetaData 要自寫薄 REST v3 client(官方文件有逐端點 Python 範例);docs/24 的選擇不變,只是沒有 wrapper 紅利。
- **alpha_vantage wrapper**:近期 commit 全是行銷帳號改 README=實質休眠;AV 免費層 25 req/day,15 行 requests 勝過殭屍依賴。
- **akshare**:21k★ 很活但**沒有台股**(A股/HK/US)——FinMind 仍是台股正解。
- **yahooquery**:比 yfinance 停更(14 個月),同一批非官方端點——只進事故手冊當 yfinance 斷裂時的備援名字。
- findatapy(機構終端取向)、pyfredapi(與 fredapi 冗餘)、sec-edgar-downloader(edgartools 真子集)。

## §3 反爬蟲工具階梯(輕→重)與我們四面牆的對應解

**階梯**:
- **Tier 0**:requests/httpx(預設)。
- **Tier 1:curl_cffi** ✅ **adopt now** — TLS/JA3 指紋模擬(impersonate chrome),~6k★ 活躍、純 wheel 零基建;**已經是我們的傳遞依賴**(yfinance 0.2.50+ 原生使用)。三面牆的完整答案。
- **Tier 2**:patchright(Playwright 反偵測 fork,1.4k★、貼著上游更新、Apache-2.0)或 Scrapling StealthyFetcher(BSD-3,v0.4.10)——**adopt-later**:需要 JS 渲染+隱身時才引入(CI 安裝重)。
- **Tier 3**:nodriver(u-c 官方繼任者,4.5k★,AGPL-3.0;真 Chrome、可執行 JS)、camoufox(指紋級最強但維護搖擺)——最後手段。
- **❌ 淘汰**:cloudscraper(只破已退役的舊 Cloudflare 世代)、hrequests(discontinued)、undetected-chromedriver(作者自己指向 nodriver)、playwright-stealth(被 patchright 支配)。

**逐牆對應**(docs/24 實際撞到的):

| 牆 | 解 |
|---|---|
| (a) **Stooq SHA-256 PoW** | 需執行 JS=只有 Tier 3(nodriver)過得去;**但每週一個 CSV,誠實答案=手動下載/鏡像**(docs/24 已降級)——ToS 紅線相鄰+瀏覽器基建不值得。Stooq 變 load-bearing 時再議 |
| (b) AAII 403 | 先試 Tier 1 curl_cffi(多數是純 TLS 指紋擋);不行才 Tier 2 |
| (c) marketaux/FMP Cloudflare | curl_cffi 先試(很多 CF edge 403 是純 JA3);cloudscraper 無效 |
| (d) Yahoo/yfinance | **已在堆疊內解決**(yfinance 內建 curl_cffi)——紀律=鎖版本、讓 yfinance 自管 session、盯 issue tracker |
| (e) **NBER RSS**(2026-07-11 實戰驗證) | 純 TLS 指紋牆的教科書案例:plain urllib/requests 帶瀏覽器 UA 仍 403,**curl_cffi impersonate chrome 直接 200**——Tier-1 首選的第一個實戰戰果(`paper_scout.py`);另注意正確路徑是 `/rss/new.xml`,搜尋結果流傳的 `/papers.rss` 是 404 |

**⚠️ 關鍵警告(經驗證)**:GitHub Actions runner 是 **datacenter IP**,Cloudflare 類系統對其信任分天生低——**凡是靠 IP 信譽擋的牆,任何 $0 客戶端工具都不可靠**;誠實出路=官方免費 API 層/資料鏡像/手動下載,不是更重的爬蟲(下一級是住宅代理=超出 $0 且不做)。

**合規紅線**:只取公開頁面;Stooq/AAII/FMP ToS 均限制自動化——頻率最小化、優先官方管道;不做帳號偽造、付費牆繞過、CAPTCHA 農場。

---
*完整逐項評估(31 項:6 Dataroma/13F + 13 API + 12 反爬工具)在工作流輸出;本檔為決策版。
資料源本體目錄見 [data-sources.md](data-sources.md),缺口對照見 [docs/24](../24-data-gaps-and-sources.md)。*
