# 論文台帳與深讀計畫 — 分類、重測優先度、與 >2000 引用選書排程

> 建立(2026-07-08):回應「記錄已參照論文的分類/洞見/用途/結果 + 為日後重測留下判斷依據 + 挑 >2000 引用經典排程深讀」。
> 本檔三部分:**Part A 分類與重測中繼資料設計**(判斷「是否該優先重測」的規則)、**Part B 已參照論文台帳**(約 50 篇,含重測訊號)、**Part C >2000 引用深讀計畫**(尚未深測、可用免費資料重建的經典,分波排程)。
> 現行判定以 [docs/18 註冊表](18-strategy-registry.md) 為單一事實來源;棲地/座位/翻案語言見 [docs/19 分類學](19-mechanism-taxonomy.md);驗收標準見 [docs/17 fabric v2.0](17-fabric-acceptance.md);論文驅動的持續管線見 [docs/21](21-paper-to-tr-pipeline.md)。

---

## Part A — 分類架構與重測優先度中繼資料

一篇論文之所以要留紀錄,不只是「摘要+我們做了什麼」,而是為了在**日後**能一眼判斷:**這篇該不該重測?為什麼?** 核心洞見(來自本專案 30+ 次自我打臉,尤其 IBS 反轉與 KMZ)是:**一個機制「FAILED」有兩種完全不同的原因——機制本身無效,或我們當初從錯的座位切入。** 只有後者值得重測。所以每篇論文我們沿五個軸標記。

### A1. 五個分類軸(查找與歸類用)

| 軸 | 值域 | 用途 |
|---|---|---|
| **領域 domain** | 資產定價/因子、資料窺探與嚴謹度、組合與部位、執行與微結構、時序與波動、行為財務、報酬可預測性、衍生品與尾部、ML 實證定價 | 主題查找 |
| **機制族 mechanism family** | 橫斷面因子、時序動量、均值回歸/統計套利、regime/擇時、執行/成本、組合建構、風險/波動模型、ML/預測、市場效率理論 | 對應 docs/19 分類學;判斷「同族連敗→封頂」 |
| **原生棲地 native habitat** | 資產類別 × 頻率 × 廣度 × 年代 × 用途(docs/19 語言) | 判斷我們的「被測座位」是否吻合 |
| **我們的接觸狀態 engagement** | 採納為慣例 / TR 已測(PASSED·PARTIAL·FAILED)/ 佇列 / 未測 | 知道做到哪 |
| **重測優先度 retest priority** | 高 / 中 / 低 + 觸發類別(見 A2) | **本檔的重點** |

### A2. 重測觸發類別(決定優先度的關鍵)——為什麼要重測?

每篇論文標一個(或多個)觸發類別。**排序即優先序**:

| 代碼 | 觸發類別 | 意義 | 優先度 | 例 |
|---|---|---|---|---|
| **T1 座位錯置** | 我們在【它不居住的棲地】測了它 | 當初切入角度錯,FAILED 不算數 | **最高** | KMZ 用橫斷面樹模型測(TR-08/11),但它是單資產擇時論文→TR-17 才在正確座位測 |
| **T2 缺關鍵資料** | 因無 point-in-time 免費資料而【無法測/標 N/A】 | 一旦資料維度打開就該測(付了資訊成本) | **高** | Black-Scholes(TR-09 N/A)、LPS 隔夜拆解、任何需選擇權/日內的機制 |
| **T3 標準演進** | fabric 規則自上次測後【改過】(F10 級聯) | 舊判定可能在新標準下翻盤 | **中-高** | IBS 在 F1 成交時點慣例加入後由 PASS→FAILED(TR-16);任何 rf=0 時代的舊 Sharpe |
| **T4 時間衰退複查** | 已累積足夠新的樣本外年份,值得重量 alpha 衰退 | 年度儀式 | **中** | 動量/價值/品質因子每年一月複查 ICIR |
| **T5 從未證偽** | 【採納為慣例】但從未在我們資料上正式跑過對照 | 盲點,可能是未被檢驗的假設 | **中** | Ledoit-Wolf、Kelly sizing、Campbell-Thompson 約束 |
| **T6 已定案** | 在【正確棲地】測過、且輸了 | 除非資料維度改變,否則不重測 | **低** | 廣市場動量(廣宇宙正確座位測過=死)、擇時轉現金鐵律 |

> **判讀規則**:T1/T2 = 幾乎一定要重測(只是缺角度或缺資料);T6 = 幾乎不重測(是真的無效)。這正是「區分機制失效 vs 切入方式錯」的可操作化。

### A3. 每篇台帳記錄的欄位(Part B 的 schema)

`key / 作者年份 / 標題 / 領域 / 分類(機制族+棲地)/ 摘要 / 核心結論 / 我們的洞見 / 用在哪(TR·docs·模組)/ 怎麼用 / 我們的結果 / angle_risk(座位是否錯)/ reopen_condition(什麼事件觸發重測,依 G-S 標成資訊成本)/ retest_priority(高中低+觸發類別)`

### A4. 選書與排程原則(Part C 的門檻)

新論文要進「深讀計畫」須同時滿足:
1. **引用 >500**(2026-07 由 >2000 放寬:canonical 與次-canonical 皆納,把中間帶補厚;引用數為估計,實際以 Google Scholar 覆核);
2. **與股票交易/選股邏輯相關**(不只是純理論);
3. **可用我們的免費資料重建**(日線 OHLCV + EDGAR 基本面 + 指數長歷史);需日內/選擇權/tick 的標 T2(排程但等資料維度);
4. **尚未在正確座位深測**(已參照且已在正確棲地測過的→不重排)。
排波原則:**第一波 = 高引用 × 免費資料可重建 × 高洞見潛力**;需付資訊成本(新資料)的順延為後波,但先寫下「翻案條件=哪筆資料」。

---

## Part B — 已參照論文台帳(52 篇)

六大主題、52 篇論文,每篇含分類、summary/結論、我們的洞見與用途、結果,以及重測中繼資料(angle_risk / reopen / 優先度)。
先給**重測優先度索引**(依優先度排序,快速看『先重測誰』),再按主題列完整記錄。

### B.0 重測優先度索引

| 優先度 | 論文 | 作者 | 年份 | 我們的結果 | 重測觸發(reopen 濃縮) |
|---|---|---|---|---|---|
| 🔴 高 | Hurst-Ooi-Pedersen 2017 | Hurst, Ooi & Pedersen | 2017 | PARTIAL/mixed (理論背書採納;我們測的動量座位=衰退/FAIL | 取得多資產期貨資料(股指/債/商品/FX 期貨,數十個低相關市場)→建構 HOP 原生的 vol-target TSMOM 組合書,檢驗 crisis-alph… |
| 🔴 高 | Lou-Polk-Skouras 2019 (Overnight/Intraday) | Lou, Polk & Skouras | 2019 | queued | 用已有 OHLC 的 open/close 近似 (收→開 = prev-close→open、開→收 = open→close),對 47/503 檔動量 t… |
| 🟡 中 | Bailey-Borwein-Lopez de Prado (PBO/CSCV) | Bailey, Borwein, López d | 2016 | adopted-as-convention(已用於 Minervini);旗 | 對旗艦 combo 家族(8 配置)跑 CSCV-PBO 並在 F5 加門檻註記 → 資訊成本≈$0(既有回測,小算力)。 |
| 🟡 中 | Bollerslev 1986 | Bollerslev | 1986 | not-yet-tested (建議採納方向但從未實作、從未跑;現行以 tr | 當波動預測品質成為 binding(vol-target sizing 或 Kelly 部位在 regime 轉折被打臉,或要正式比較 forecast-σ v… |
| 🟡 中 | Brown-Goetzmann-Ibbotson-Ross 1992 | Brown, Goetzmann, Ibbots | 1992 | adopted-as-convention(倖存者紀律已採納;經 TR-13 | ingest 點對點指數成分史(Wikipedia 版本史=免費但髒 / iShares-SPDR 歷史持股 / CRSP=付費學術)+ 下市報酬 → 資訊成本… |
| 🟡 中 | Campbell-Thompson 2005 | Campbell & Thompson | 2005 | adopted-as-convention(擇時層約束)——但 C-T 的符 | ingest Goyal-Welch 總經預測子資料集(與 TR-17/KMZ 翻案條件共享的資訊成本)→ 在其原生單資產擇時座位跑符號約束股權溢酬迴歸。 |
| 🟡 中 | Fama-French 1992 | Fama & French | 1992 | 混合:value 因子 FAILED(docs/09/10 失落十年、價值死 | 取得中小型股 + 國際 PIT 宇宙(資訊成本:全市場/國際下市-aware 資料),或延長歷史回 1990s 涵蓋價值友善年代 → 在價值原生棲地重測 BE/… |
| 🟡 中 | GISW (Sharpe manipulation) | Goetzmann, Ingersoll, Sp | 2007 | not-yet-tested(全專案未引用;為候選採納項) | 當任一策略具選擇權式/負偏態 payoff(現有 L≥1.5 槓桿 combo、防禦 overlay,或未來 covered-call/short-vol sl… |
| 🟡 中 | Gatev-Goetzmann-Rouwenhorst 2006 | Gatev, Goetzmann & Rouwe | 2006 | FAILED (OOS +1.96%/yr < 現金 BIL +2.70%; | (a) 便宜且該先做:用 GGR 原生 distance 選對(而非共整合)+更廣宇宙(跨 ETF/ADR/全市場)以現有日線重測——資訊成本=工程;(b) 真… |
| 🟡 中 | Gu-Kelly-Xiu 2020 | Gu, Kelly & Xiu | 2020 | FAILED(TR-08/11)——但 docs/19 標錯置風險=高:FA | 610 檔倖存者-aware 宇宙 + 基本面/另類資料特徵(資訊成本=ingest 94 式豐富特徵面板 × 數千檔)。注:部分已做——docs/10 廣宇宙… |
| 🟡 中 | KMZ 2024 (Virtue of Complexity) | Kelly, Malamud & Zhou | 2024 | PARTIAL | Ingest 公開的 Goyal-Welch 月度總經預測子資料集 (1926-present),在 95 年長樣本 × 15 個總經序列的原生棲地上完整復現並… |
| 🟡 中 | Kelly 1956 | Kelly, J. L. | 1956 | adopted/implemented(half-Kelly 已實作)並作為 | 任何 sleeve 產出穩健 OOS edge (p,b) 時,Kelly-by-probability 座位重開——但那 gated on 先突破 alpha… |
| 🟡 中 | Lopez de Prado HRP | López de Prado | 2016 | PARTIAL(TR-07:機制如設計降波動 −3.9pp,permuted | 取得 50+ 檔真異質多資產宇宙(跨股/債/商品/國際/另類)即重測 HRP 於其原生棲地。資訊成本=多資產 PIT 資料 ingest(收斂回 docs/11… |
| 🟡 中 | Moreira-Muir 2017 (Volatility-Managed Portfolios) | Moreira & Muir | 2017 | PARTIAL | 把 1/σ² 波動管理升級為 F6 v2 正式 sleeve 時,需加:(a) 交易成本 (換手高);(b) Cederburg 靜態恆定曝險二階控制;(c) … |
| 🟡 中 | Nagel 2025 / Buncic 2025 (VoC critique) | Nagel | 2025 | PARTIAL | 同 KMZ 條:取得 Goyal-Welch 長歷史總經資料集後,在原生棲地上重跑,才能檢驗 Nagel 批評是否在 KMZ 自己的座位也成立 (而非只在我們的… |
| 🟡 中 | Sharpe 1964 (CAPM) | Sharpe | 1964 | PARTIAL(TR-06)——作為定價模型在本宇宙被拒(SML 反轉),作 | 廣/全市場 PIT 宇宙(610 檔倖存者-aware + 含非科技產業 + 跨多年代/regime)重測 SML 斜率——資訊成本=擴宇宙+更長歷史。 |
| 🟡 中 | Shumway 1997 (delisting) | Shumway | 1997 | PASSED(方法;TR-13 區間化完成) | ingest CRSP 型下市代碼面板(WRDS 學術付費)→ 把 [+1.26%,+2.02%] 區間收成點估計;資訊成本=付費 CRSP/WRDS。 |
| 🟡 中低 | Lakonishok-Lee (Insider) | Lakonishok & Lee | 2001 | FAILED | 擴充 insider 宇宙到小型股 PIT (Form 4 電子申報始於 ~2003,無法回補更早年代,唯一可及擴充=小型股廣度 + cluster-buy/高… |
| 🟡 中低 | Ledoit-Wolf 2004 | Ledoit & Wolf | 2004 | adopted-as-convention(全域強制);間接於 TR-03/ | 執行 TR-03b:47/610 宇宙特徵值譜 vs MP 帶(幾個真訊號特徵值?),把 MP-clipping 加入 TR-03 競技場(vs LW vs P… |
| 🟡 中低 | Marcenko-Pastur 1967 | Marčenko & Pastur | 1967 | adopted-as-convention (經 LW shrinkage  | TR-03b:畫 47/610 宇宙樣本共變異特徵值譜 vs MP 帶(幾個真訊號特徵值?預期 3-5),把 MP-clipping 加入 TR-03 競技場(… |
| ⚪ 低 | Almgren-Chriss 2000 | Robert Almgren & Neil Ch | 2000 | adopted-as-convention（設計採納為容量檢查；因規模不符誠 | 資本規模達機構級或交易流動性差宇宙，使參與率>0、市場衝擊變一階；具體觸發=某部位使 AC 交易半衰期 τ=1/κ > 再平衡視窗（docs/19：F2 v2 … |
| ⚪ 低 | Arnott-Harvey-Markowitz 2019 (AHM) | Arnott, Harvey & Markowi | 2019 | adopted-as-convention(F0 檢查表即其操作化) | n/a — meta 協定不需重測;若協定更新版發布可增修 F0 → 資訊成本≈$0。 |
| ⚪ 低 | Bailey-Lopez de Prado 2014 (DSR) | Bailey & López de Prado | 2014 | adopted-as-convention(scorecard 核心工具) | 若返回分布嚴重非常態、需更新 PSR 的 skew/kurt 動差估計,或 N 定義有爭議 → 資訊成本≈$0(既有 trial-registry)。 |
| ⚪ 低 | Bertsimas-Lo 1998 | Dimitris Bertsimas & And | 1998 | adopted-as-convention（TWAP 基線 + IS 會計原 | ① 當 execution/ 真正動工、需要 implementation-shortfall 帳本（arrival price vs 實際成交）時。② 資本規… |
| ⚪ 低 | Brock-Lakonishok-LeBaron 1992 | Brock, Lakonishok & LeBa | 1992 | adopted-as-convention (資料窺探防線採納為 fabri | (a) 若要正式引用 BLB 量化結論→需 OCR 或取得可抽取文字版做 spot-verify;(b) 若要原座位復現→需長歷史單指數日線(DJIA 1897… |
| ⚪ 低 | Carhart 1997 | Carhart | 1997 | adopted-as-convention(作為 alpha 標尺/歸因基準 | 若懷疑我方 UMD 建構偏離 Carhart 定義、或需國際動量因子;或若某配方數字變 load-bearing → OCR 原始 PDF。實務上隨宇宙擴充重建… |
| ⚪ 低 | Cederburg-ODoherty-Wang-Yan 2020 | Cederburg, O'Doherty, Wa | 2020 | adopted-as-convention(TR-02b/TR-17 的控制 | n/a — 控制工具已採納入 F6;無翻案概念。若未來要把 1/σ² 波動管理當策略而非控制,才需重評其穩健性 → 資訊成本≈$0。 |
| ⚪ 低 | Cover 1991 | Cover, T. | 1991 | not-yet-tested(刻意延後為 optional benchmar | 想要一個 μ/Σ-free 的穩健對照時(例如質疑 risk-parity 的估計依賴),花小成本實作 UP / online-Newton-step 當 be… |
| ⚪ 低 | DeMiguel-Garlappi-Uppal 2009 | DeMiguel, Garlappi & Upp | 2009 | adopted-as-convention(強制 1/N benchmark | 宇宙擴到大 N 異質(50+ 跨資產)且有長歷史時,optimizer 才有機會勝 1/N。資訊成本=多資產 PIT 資料 ingest + 長歷史。 |
| ⚪ 低 | Engle 1982 | Engle | 1982 | adopted-as-convention (波動叢聚⇒block boot | 若要正式報告我們宇宙的條件異質性強度、或把 heteroskedasticity-robust 標準誤自動化進 rigor→加 ARCH-LM 為 scorec… |
| ⚪ 低 | Fama 1970 | Fama | 1970 | adopted-as-convention(認識論框架;聯合假設紀律)——非 | 非直接可重測;每次採用新基準模型(如加 QMJ/q-factor 到歸因)聯合假設 caveat 就重現、alpha 判定可能位移。具體=基準變更時重跑全部歸因… |
| ⚪ 低 | Fama-French 1993 | Fama & French | 1993 | adopted-as-convention(作為風險調整/歸因基準,非被測策 | 若換更廣/更長宇宙 → 需在該宇宙重建 SMB/HML;或若加入 QMJ/q-factor 基準,alpha 判定可能位移(資訊成本=擴宇宙 PIT 財報)。 |
| ⚪ 低 | Grinold (fundamental law / breadth) | Grinold | 1989 | adopted-as-convention(天花板/組織定律)+ 經驗確認: | 定律本身是數學不可測;但『廣度天花板』判定隨換資料維度而重開——ingest 數千低相關名(多資產/期貨/全球)或高 IC alt-data(每項皆 docs/… |
| ⚪ 低 | Grossman-Stiglitz 1980 | Sanford J. Grossman & Jo | 1980 | adopted-as-convention（框架哲學/元理論；非可測策略，無 | 非策略、無單一重開事件；它是為所有其他翻案條件『定價』的元條件。實務觸發=任何一次付出新的資訊成本（ingest 日內資料、選擇權鏈、另類資料、小型股 PIT … |
| ⚪ 低 | Hansen 2005 | Hansen | 2005 | adopted-as-convention(F5 主要工具) | 若子期/資產顯示強 block 相依(ARCH/GARCH-M),需改用 block/wild-bootstrap 版 SPA 而非 iid 版 → 資訊成本≈… |
| ⚪ 低 | Harvey-Liu-Zhu 2016 | Harvey, Liu & Zhu | 2016 | adopted-as-convention(alpha 門檻;旗艦以 t=3 | 收緊到 campaign 級 FWER(Bonferroni t≈3.66)或全面改用 BHY-FDR 1% → 資訊成本≈$0(既有 trial-regist… |
| ⚪ 低 | Hoffstein (rebalance timing luck) | Hoffstein, Sibears & Fab | 2019 | PASSED(方法;TR-12 揭露 timing luck,3 修正生效) | n/a — 已於原生棲地窮舉相位測完;若新增其他日曆錨定策略,F12 直接套用 → 資訊成本≈$0。 |
| ⚪ 低 | Jegadeesh-Titman 1993 | Jegadeesh & Titman | 1993 | FAILED(TR-11,作為『選股增量』;動量=beta)——已在兩個座位 | 國際/小型股宇宙(需國際或中小型 PIT 資料);或 TR-19 隔夜/日內歸因拆解(診斷角度,非交易——成本牆仍立)。 |
| ⚪ 低 | Kyle 1985 | Albert S. Kyle | 1985 | adopted-as-convention（成本模型設計；costs.py  | ① 立即工程觸發：把 backtest/costs.py 的 size_dependent_cost 接線進回測（目前實作但未接線，v1.2 審查點名）。② 機… |
| ⚪ 低 | Lo 2002 | Lo | 2002 | adopted-as-convention(已實作於 restate_rf_ | n/a(已實作);若要擴充到完整 IID/GMM 的 Sharpe 推論或多期重疊校正 → 資訊成本≈$0。 |
| ⚪ 低 | Lo-MacKinlay 1988 | Lo & MacKinlay | 1988 | adopted-as-convention (作為特徵採納;從未作為策略跑  | 當 VR 要從『描述性特徵』升格為『trend-vs-revert 交易 gate』時——升級為 Lo-MacKinlay 異質穩健 z*(q)、per-ass… |
| ⚪ 低 | Markowitz 1952 | Markowitz, H. | 1952 | adopted-as-convention(基礎框架公理,未單獨跑 TR;c | 公理層,不需『重測』。唯一會改變用法的事件:取得夠長且穩定的 μ 估計(DGU:25 資產需 ~3000 月)——現實不可及,故 E-V 的 max-retur… |
| ⚪ 低 | McLean-Pontiff 2013 | McLean & Pontiff | 2013 | adopted-as-convention(衰退 haircut/先驗)+  | 僅當我方累積的發表後衰退量測系統性偏離~35% 時才修訂 haircut 量級;具體=對 200 個 OSAP 訊號做系統性發表後 walk-forward(需… |
| ⚪ 低 | Michaud 1989 | Michaud, R. | 1989 | adopted-as-convention(建構約束;塑造『不建 naked | 若取得穩健的 robust/resampled-MVO 實作 + 顯著更長的估計窗,可測『約束後 MVO 是否勝 risk-parity』——但 DGU 已預示… |
| ⚪ 低 | Novy-Marx (gross profitability) | Novy-Marx | 2013 | PASSED / adopted(ICIR +0.30;docs/18 PA | 它 PASSED,故『翻案』=強化而非推翻:延長歷史(1990s)+更多真熊市確認 flight-to-quality 的 regime-universalit… |
| ⚪ 低 | Obizhaeva-Wang 2013 | Anna Obizhaeva & Jiang W | 2013 | not-yet-tested / queued（韌性壓力旋鈕設計，資料閘控未 | 取得日內 LOB / 訂單簿韌性資料（G-S 意義下的資訊成本；<$15/mo 下目前受阻）+ 交易規模達到 ≥ 簿深度。具體觸發=ingest 日內 LOB … |
| ⚪ 低 | Petersen 2009 (clustered SE) | Petersen | 2009 | adopted-as-convention(已實作 n_eff + 聚類 t | n/a(已實作);若要從 by-time 聚類擴到雙向聚類(firm×time)或 Driscoll-Kraay → 資訊成本≈$0(既有資料重算)。 |
| ⚪ 低 | Rahimi-Recht 2007 (Random Fourier Features) | Rahimi & Recht | 2007 | adopted-as-convention | 僅在 TR-17 重跑 (見 KMZ 條) 或懷疑 RFF 數值正確性時才回看;無獨立重測意義。 |
| ⚪ 低 | Ross 1976 (APT) | Ross | 1976 | adopted-as-convention(架構授權)。注:image-on | 非可測策略;只有在我們加入超越 TR-03 PCA 的正式 APT 載荷迴歸/統計因子步驟時才『重開』。具體:在更大更異質宇宙擴展 TR-03 PCA。 |
| ⚪ 低 | Sullivan-Timmermann-White 1999 | Sullivan, Timmermann & W | 1999 | adopted-as-convention(操作化為 trial-regis | 新增任何未登記的大型規則家族(如新的通道/濾網族)時,重跑 SPA + 更新 trial-registry → 資訊成本≈$0(既有資料重算)。 |
| ⚪ 低 | White 2000 | White | 2000 | adopted-as-convention(F5 地基;SPA 為實作首選, | 若需要 max-statistic 的完整 bootstrap 分布做 SPA 的交叉檢核,或 SPA 對我們 GARCH/block 相依結構失準時 → 資訊… |
| ⚪ 低 | de Prado AFML | López de Prado | 2018 | adopted-as-convention | HRP:取得 50+ 檔多資產異質宇宙後重測 (docs/19 標 HRP 錯置中-高,優勢隨 N 與異質性增長)。meta-labeling lift:補 p… |

### B.1 A. 資產定價與因子 (docs/03 附錄A)

#### Fama-French 1992 — asset pricing / cross-section (size, value, beta)
- **作者 · 年份**:Fama & French · 1992
- **分類**:機制族=α 產生(價值/規模橫斷面特徵)+ 方法慣例(decile 排序 harness)。原生棲地:資產=美股全市場、頻率=月頻、廣度=廣橫斷面(數百~數千)、年代=1963-1990、用途=橫斷面定價檢定。docs/19『價值(Fama-French)』列:座位=503 檔、錯置風險=低-中(價值溢酬本源於小型股)。
- **Summary / 結論**:size(ME)與 book-to-market(BE/ME)吸收橫斷面平均報酬;控制 size 後市場 β 與報酬『無關』(SML 平坦)。用 NYSE breakpoints、decile 排序——正是我們 quantile-spread 設計的原型。 結論:β 單獨不是報酬預測子;size+value 才是。全交易所 breakpoints 會讓組合在 NASDAQ 進入後全變小型股 → 必須用 NYSE breakpoints。
- **我們的洞見**:兩件事:(1)不要讓 CAPM β 以『alpha』洩入 factors/,β 只作風險中和/風險調整分母;(2)橫斷面特徵 decile 排序 + NYSE breakpoints 採為 rank-IC/ICIR harness 慣例。價值因子在我們 2015-24 座位=失落十年(FAILED)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1 VALIDATES + 附錄A;docs/09/10(value FAIL);docs/00 §E2;factors/validation.py;O3 SMB/HML 建構配方 — 橫斷面 rank-IC / quantile-spread harness 的設計原型(factors/validation.py);驅動 O3 建 SMB/HML(EDGAR book equity 依賴)。價值(earnings yield / B-M)當因子實測。 → **混合:value 因子 FAILED(docs/09/10 失落十年、價值死);橫斷面 decile+NYSE breakpoint harness = adopted-as-convention**
- **angle_risk(座位是否切錯)**:中(對 value 這條腿):我們在 S&P500 大型股 × 2015-24(公認的價值失落十年)測價值,而價值溢酬的原生棲地是小型股 × 含價值友善年代的長歷史。β-平坦結論則低風險(與我們一致、只當風險中和用)。
- **reopen(重測觸發=資訊成本)**:取得中小型股 + 國際 PIT 宇宙(資訊成本:全市場/國際下市-aware 資料),或延長歷史回 1990s 涵蓋價值友善年代 → 在價值原生棲地重測 BE/ME 溢酬。
- **重測優先度**:🟡 中 — medium — 價值的原生棲地(小型股+長歷史)尚未在我們資料測到;但失落十年是全行業共識,急迫度不高。β-中和用法與 harness 慣例=不需重測。

#### Fama-French 1993 — asset pricing / 因子模型與歸因基準
- **作者 · 年份**:Fama & French · 1993
- **分類**:機制族=估計工程·描述歸因(風險調整基準,非賺錢策略)。原生棲地:資產=美股(+債)、頻率=月頻、廣度=廣橫斷面、年代=1963-1991、用途=共同風險因子/把 alpha 壓到 0 的基準。屬 docs/19 §4『歸因/估計工程』家族。
- **Summary / 結論**:3 因子(Mkt/SMB/HML)+2 債券因子;模仿組合捕捉 size/value 的共同變異、把截距(alpha)驅近 0。給出 2×3 size×BE/ME 排序、價值加權、每年 6 月再平衡、BE 取 t-1 的精確配方。 結論:判斷 edge 的正確標尺是『alpha net of Mkt/SMB/HML』而非原始/超額 Sharpe——因為動量/趨勢策略重載於這些因子。
- **我們的洞見**:把 raw Sharpe 換成因子調整後 alpha 當作驗收門檻;FF3→Carhart-4 迴歸步驟寫進 backtest/歸因層,每個策略都報 alpha 而非只報 Sharpe。配方直接移植。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O3 + 附錄A;TR-15(旗艦 Carhart alpha t=3.38 的建構基礎);factors/;backtest/ 歸因 — 建 SMB/HML(2×3 排序、VW、6 月再平衡、BE t-1);FF3(→+動量)迴歸步驟成為所有策略的歸因引擎。TR-15 順手修復 FF loader 上游格式 break。 → **adopted-as-convention(作為風險調整/歸因基準,非被測策略)**
- **angle_risk(座位是否切錯)**:低 — 完全按原意當歸因基準使用,座位正確。唯一 caveat=Fama-1970 聯合假設問題:alpha 判定只與此基準模型一樣好。
- **reopen(重測觸發=資訊成本)**:若換更廣/更長宇宙 → 需在該宇宙重建 SMB/HML;或若加入 QMJ/q-factor 基準,alpha 判定可能位移(資訊成本=擴宇宙 PIT 財報)。
- **重測優先度**:⚪ 低 — low — 基礎設施/慣例,座位正確;隨宇宙變更才需重建,不需推翻。

#### Jegadeesh-Titman 1993 — asset pricing / cross-sectional momentum
- **作者 · 年份**:Jegadeesh & Titman · 1993
- **分類**:機制族=α 產生(XS 動量)。原生棲地:資產=美股全市場、頻率=月頻、廣度=廣橫斷面(數百~數千)、年代=1965-1989、用途=相對強弱選股。docs/19『XS 動量(Jegadeesh-Titman)』:座位=47 檔同產業(高相關)+503 檔 S&P500,錯置風險=低(兩棲地皆測)。
- **Summary / 結論**:3-12 月相對強弱動量 ~1%/月;12 月形成/3 月持有最佳 1.31%/月(加 1 週 skip 1.49%),非系統風險可解釋,約半在後 24 個月反轉。背書我們的 1-bar lag(=skip-week 微結構衛生)與 RS 特徵。 結論:動量是真效應(JT+Rouwenhorst+AMP 背書),但其 IR 天花板被廣度鎖死~1;需 skip-period 與持有期上限(24 月反轉)。
- **我們的洞見**:動量真、但在我們座位=beta 不是選股 alpha:廣市場 ICIR≈0、47 檔 top-K P(beat EW)=23%(TR-11 F9 降級 FAILED)。1-bar lag=誠實最小 skip(HOP 證延遲會侵蝕報酬,別加更多)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1+附錄A;docs/06(因子搜尋湧現最佳=純多頭 6-1 動量);docs/09;TR-11;TR-12;docs/19 — 背書 minervini_trend、RS/動量特徵、1-bar lag、reversal guardrail;XS 動量當策略實測;TR-12 相位平均證單相位不可信(季動量 timing-luck 1,753bps/yr)。 → **FAILED(TR-11,作為『選股增量』;動量=beta)——已在兩個座位(47 高相關 + 503 廣市場)皆測皆死**
- **angle_risk(座位是否切錯)**:低(docs/19 明列雙棲地皆測)。殘餘角度風險=(a)原生棲地也含國際/小型股,未測;(b)LPS(2019)診斷角度:動量溢酬可能全住在隔夜——我們從未做隔夜/日內拆解(TR-19 佇列)。
- **reopen(重測觸發=資訊成本)**:國際/小型股宇宙(需國際或中小型 PIT 資料);或 TR-19 隔夜/日內歸因拆解(診斷角度,非交易——成本牆仍立)。
- **重測優先度**:⚪ 低 — low — 已在正確廣棲地測過且輸(ICIR≈0),效應真但 IR 被廣度鎖死。唯一 medium 的子項是 LPS 隔夜診斷(TR-19),屬歸因非翻案。

#### Carhart 1997 — asset pricing / 4 因子模型 · 基金績效歸因
- **作者 · 年份**:Carhart · 1997
- **分類**:機制族=估計工程·描述歸因(動量因子基準)。原生棲地:資產=美國共同基金/股票、頻率=月頻、廣度=廣橫斷面、年代=1962-1993、用途=把績效持續性歸因到 UMD+費用。屬 docs/19 §4 歸因家族。
- **Summary / 結論**:在 FF3 上加動量因子(UMD/WML)=4 因子;基金『持續性』大多是動量因子+費用,不是技能。(image-only 掃描,由既有知識覆蓋並已標注) 結論:趨勢/動量系統的 edge 若只是 UMD 載荷,就不是技能——必須報 alpha net of Carhart-4。這是趨勢系統最重要的單一基準。
- **我們的洞見**:動量該對『被定價的動量因子』基準化,不能當免費 alpha。UMD 加入 factors/ 迴歸面板,minervini_trend/旗艦 alpha 一律報 Carhart-4 淨值。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O3+附錄A;TR-15(旗艦 t=3.38≥HLZ 3.0 判 PASSED);factors/ 歸因面板 — UMD 當第 4 因子;TR-15 旗艦的 Carhart alpha t-stat 就是 HLZ(t≥3.0)門檻的度量;所有策略歸因。 → **adopted-as-convention(作為 alpha 標尺/歸因基準)。注:原文 image-only 掃描,配方細節依既有知識**
- **angle_risk(座位是否切錯)**:低 — 當歸因基準按原意使用。唯一 caveat=image-only 掃描,若某數值細節成為 load-bearing,需 OCR 原文核對。
- **reopen(重測觸發=資訊成本)**:若懷疑我方 UMD 建構偏離 Carhart 定義、或需國際動量因子;或若某配方數字變 load-bearing → OCR 原始 PDF。實務上隨宇宙擴充重建 UMD。
- **重測優先度**:⚪ 低 — low — 慣例/基準,座位正確,按設計運作。

#### Sharpe 1964 (CAPM) — asset pricing / 均衡定價(單因子 β)
- **作者 · 年份**:Sharpe · 1964
- **分類**:機制族=估計工程·描述歸因(市場因子/風險中和)。原生棲地:資產=全市場、頻率=不限、廣度=全市場、年代=1960s、用途=均衡下期望報酬線性於 β(SML)。docs/19『CAPM』:座位=47 檔科技(極窄棲地),錯置風險=中。
- **Summary / 結論**:均衡下期望報酬只線性於市場 β(SML),β 是唯一被定價的風險。TR-06 在我們宇宙實測 CAPM。 結論:FF1992 實證殺死 β-報酬關係 → 不可加 raw β 當 alpha 因子;β 只作風險中和與風險調整分母。
- **我們的洞見**:β 純作風險中和(portfolio 的 beta-neutral/beta-target)。TR-06 發現本宇宙 SML『反轉陡升』(FM 斜率 +1.9%/mo t=2.69,高 beta 大勝=BAB 在 AI 牛市反向)、截距 −1.02%/mo 違反 CAPM;歸因工具價值保留。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;TR-06(PARTIAL);docs/19 CAPM 列;portfolio/ beta 中和 — 市場因子概念 + regime-gate 到市場狀態(200-SMA/HMM 粗版);β 風險中和;TR-06 Fama-MacBeth SML 檢定。 → **PARTIAL(TR-06)——作為定價模型在本宇宙被拒(SML 反轉),作為風險中和/歸因工具保留**
- **angle_risk(座位是否切錯)**:中-高 — docs/19 明列座位極窄(47 檔科技)。SML 反轉是『此棲地』現象(AI 牛市高 beta 補償),非對 CAPM 的普遍反駁;我們從一個極窄科技座位切入。原生棲地=全市場定價。
- **reopen(重測觸發=資訊成本)**:廣/全市場 PIT 宇宙(610 檔倖存者-aware + 含非科技產業 + 跨多年代/regime)重測 SML 斜率——資訊成本=擴宇宙+更長歷史。
- **重測優先度**:🟡 中 — medium — PARTIAL 判定明顯棲地特定(窄科技座位),SML 反轉大概不普遍化;但 CAPM 定價非我方 alpha 目標,故非 high。切入角度窄=值得標記。

#### Ross 1976 (APT) — asset pricing / 多因子無套利定價
- **作者 · 年份**:Ross · 1976
- **分類**:機制族=估計工程·描述歸因(多因子架構授權)。原生棲地:資產=不限、頻率=不限、廣度=廣橫斷面(共同因子結構)、年代=1976、用途=報酬由少數共同因子驅動、無套利釘價、對『哪些因子』不可知論。屬 docs/19 §4 因子/歸因家族。
- **Summary / 結論**:報酬由一組共同因子驅動,期望報酬線性於因子載荷,無套利釘住價格——多因子、對因子身分理論中立。(image-only 掃描,由既有知識覆蓋並已標注) 結論:APT 是『不需 CAPM 推導即可用經驗動機因子(動量/價值/品質)』的執照——授權整個多因子 factors/ 方向與 IC/quantile-spread 機制。
- **我們的洞見**:把 factors/ 結構化為 APT 式多因子面板 + 明確因子載荷迴歸(Mkt/SMB/HML/UMD/QMJ),使任何策略報酬可做因子風險分解。TR-03 的 PCA 統計因子是其經驗對應。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;TR-03(PCA);factors/ 架構;歸因分解 — factors/ 架構授權;IC/quantile-spread 機制的理論正當性;TR-03(PCA 統計因子=APT 風味的經驗版,PC1=41.8% 一個大 beta)。 → **adopted-as-convention(架構授權)。注:image-only 掃描,由既有知識覆蓋;TR-03 PCA 是其經驗近親**
- **angle_risk(座位是否切錯)**:低 — 當架構授權使用,正確。APT 不指定『哪些因子』→ 沒有具體座位可切錯,它是 meta-執照。caveat=image-only 掃描。
- **reopen(重測觸發=資訊成本)**:非可測策略;只有在我們加入超越 TR-03 PCA 的正式 APT 載荷迴歸/統計因子步驟時才『重開』。具體:在更大更異質宇宙擴展 TR-03 PCA。
- **重測優先度**:⚪ 低 — low — 基礎架構慣例,無獨立可重測的策略面。

#### Gu-Kelly-Xiu 2020 — asset pricing / ML 橫斷面預測
- **作者 · 年份**:Gu, Kelly & Xiu · 2020
- **分類**:機制族=α 產生(ML 橫斷面預測)。原生棲地:資產=全美股 ~3 萬檔、頻率=月頻、廣度=巨量橫斷面 × 60 年 × 94 特徵、年代=1957-2016、用途=非線性 ML 選股。docs/19『ML 預測(GKX 2020)』:座位=47 檔×8 年×11 特徵(≈原生棲地 0.1%),錯置風險=高。
- **Summary / 結論**:樹/神經網路約『雙倍』線性模型的 L/S Sharpe(NN VW decile Sharpe 1.35 vs OLS 0.61);900+ 預測子的裸 OLS OOS 轉負;跨方法 top 預測子=價格趨勢、流動性、波動。 結論:ML 勝線性『但那是在豐富特徵上』(docs/12);用弱特徵(純價量)再炫的方法也變不出 alpha;股票級 R²~0.3% → 須在組合層評估。
- **我們的洞見**:背書 LightGBM(淺樹>深網)、我方特徵屬其 top-3 類、須正則化+組合層評估。但在我方座位:TR-08 OOS IC −0.0013、R² −4.8%、Sharpe≈shuffled 控制——GKX 效應在此宇宙完全衰退。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1+附錄A;TR-08(FAILED);TR-11(RF 預測器 FAILED);docs/12;docs/19 ML 列 — 驗證 LightGBM 選型與特徵面板;ML 混合預測實測 TR-08(LightGBM)、TR-11(RF 預測器)。 → **FAILED(TR-08/11)——但 docs/19 標錯置風險=高:FAILED 只證『小而相關宇宙+價量特徵』無效,與 GKX 主張不衝突**
- **angle_risk(座位是否切錯)**:高 — 這是使用者點名的旗艦『切錯座位』案例(如 KMZ)。我方座位=其原生棲地 ~0.1%(47 檔 vs 3 萬檔、11 特徵 vs 94)。FAILED 不觸及 GKX 的座位。
- **reopen(重測觸發=資訊成本)**:610 檔倖存者-aware 宇宙 + 基本面/另類資料特徵(資訊成本=ingest 94 式豐富特徵面板 × 數千檔)。注:部分已做——docs/10 廣宇宙因子≈死,此證據『支持不翻案』。
- **重測優先度**:🟡 中 — medium — 角度明顯錯(高錯置),但已有緩解證據(docs/10 廣宇宙因子近死)傾向不翻案;僅在同時 ingest 豐富特徵+廣宇宙時才值得正確規模重測,故非 high。

#### McLean-Pontiff 2013 — asset pricing / 異常衰退元研究
- **作者 · 年份**:McLean & Pontiff · 2013
- **分類**:機制族=驗證方法·描述(異常衰退元發現/先驗)。原生棲地:資產=82 個已發表異常、頻率=月頻、廣度=跨異常元研究、年代=1970s-2010s、用途=量化樣本外+發表後衰退。用作 rigor scorecard 的 haircut 先驗——座位正確。
- **Summary / 結論**:82 個已發表異常:樣本外衰退~10%(統計偏誤、不顯著)、發表後衰退~35%(套利)。衰退對高特異波動/流動性差/小型股最小。 結論:已發表異常回測高估活體 alpha ~35-50% → 須 haircut;並偏好較少被套利的角落 + 發表後起算的 walk-forward 窗。
- **我們的洞見**:把~35% 衰退 haircut 與『發表後起算窗』寫進 rigor scorecard;作為 OSAP 212/200 個未測訊號的先驗(docs/15:發表後平均衰退 58%)。我方自身結果反覆佐證(TR-01 pairs GGR +11%衰退>100%、TR-16 IBS Connors 時代衰退、動量 ICIR≈0)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O4+附錄A;docs/15(OSAP 先驗);rigor scorecard;TR-01/TR-16(自身衰退佐證) — rigor scorecard 的衰退 haircut 線(O4);OSAP 未測訊號的先驗;偏好 illiquid/小型/高特異波動角落。 → **adopted-as-convention(衰退 haircut/先驗)+ 被我方自身衰退發現反覆佐證**
- **angle_risk(座位是否切錯)**:低 — 當 meta-先驗/haircut 按設計使用,未切錯座位;我方自身衰退觀察(pairs、IBS、動量)正好佐證其量級。
- **reopen(重測觸發=資訊成本)**:僅當我方累積的發表後衰退量測系統性偏離~35% 時才修訂 haircut 量級;具體=對 200 個 OSAP 訊號做系統性發表後 walk-forward(需 ingest OSAP 資料+PIT)。
- **重測優先度**:⚪ 低 — low — 慣例、已被佐證、座位正確。

#### Campbell-Thompson 2005 — asset pricing / 股權溢酬 OOS 擇時預測
- **作者 · 年份**:Campbell & Thompson · 2005
- **分類**:機制族=估計工程·風險塑形(擇時層約束)。原生棲地:資產=單一大盤(股權溢酬)、頻率=月頻、廣度=單資產時序、年代=1927-2005、用途=用 Goyal-Welch 型預測子做市場擇時、加符號限制。座位=擇時,類 KMZ 的單資產月頻總經預測子棲地。
- **Summary / 結論**:股權溢酬預測子只有在加『係數符號限制 + 非負溢酬下限』後才 OOS 勝歷史均值;OOS R² 很小(<0.5%/月)但有經濟意義。 結論:無限制 OLS 時序預測子 OOS 幾乎必敗,除非加經濟符號約束——對 regime/擇時層是廉價高值的規則。
- **我們的洞見**:在任何擇時/regime overlay 上強制加符號限制+非負溢酬下限(O8)。我方擇時/gate 一律 FAILED(TR-02、docs/09 gate-to-cash)與 C-T 警告一致——但那是不同建構(Markov/200-SMA gate),非 C-T 的符號約束 OLS 溢酬預測子本身。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O8+附錄A;TR-02(Markov gate);docs/19 Markov gate 列;擇時 overlay 慣例 — regime/擇時 overlay 的約束慣例(O8);與 TR-02(Markov gate FAILED)、200-SMA/HMM gate 的擇時失敗互相呼應。 → **adopted-as-convention(擇時層約束)——但 C-T 的符號約束溢酬預測子『從未在其原生單資產擇時座位跑過』**
- **angle_risk(座位是否切錯)**:中 — C-T 原生座位=市場級月頻股權溢酬擇時(Goyal-Welch 總經預測子 + 符號約束),與 KMZ 同棲地。我們只把它當慣例/約束採納,我方擇時 FAILED(TR-02)是不同建構(Markov/200-SMA gate)非 C-T 的約束 OLS 溢酬預測子。
- **reopen(重測觸發=資訊成本)**:ingest Goyal-Welch 總經預測子資料集(與 TR-17/KMZ 翻案條件共享的資訊成本)→ 在其原生單資產擇時座位跑符號約束股權溢酬迴歸。
- **重測優先度**:🟡 中 — medium — 採為規則卻從未在原生座位測;翻案與 TR-17(KMZ)共享 Goyal-Welch 資料成本,一旦該資料落地即為廉價 add-on。

#### Fama 1970 — market efficiency / 認識論(聯合假設)
- **作者 · 年份**:Fama · 1970
- **分類**:機制族=驗證方法·描述(市場效率認識論)。原生棲地:資產=全市場、頻率=不限、廣度=全市場資訊效率、年代=1970、用途=弱/半強/強式分類 + 聯合假設問題。作為 rigor scorecard 與整個負結果專案的認識論框架——座位正確。
- **Summary / 結論**:弱/半強/強式效率分類;價格『充分反映』資訊,故任何可預測性檢定=效率+假設報酬模型的『聯合檢定』。 結論:聯合假設問題:我方 IC/alpha 結果只與基準模型一樣好——強化 FF3/Carhart-4 風險調整的必要。
- **我們的洞見**:整個負結果專案=EMH 的經驗面;結合 Grossman-Stiglitz(docs/20 §6):免費資料上 alpha≈0 正是 EMH/G-S 均衡預言。alpha 判定的謙遜(不能完全分離『無 alpha』與『錯基準』)寫進 scorecard 哲學。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;docs/00 §E;docs/20 §6(G-S 均衡);rigor scorecard 哲學 — rigor scorecard 的認識論框架;docs/00 §E 的判斷哲學;與 docs/20 Grossman-Stiglitz 段落連結。 → **adopted-as-convention(認識論框架;聯合假設紀律)——非可測策略,是我方全專案量測所對的 null**
- **angle_risk(座位是否切錯)**:低 — 當認識論框架使用,正確;無座位被切錯。唯一『風險』是哲學性的:永遠無法完全分離『無 alpha』與『錯基準』(這就是聯合假設問題本身=永久 caveat,非可修的座位)。
- **reopen(重測觸發=資訊成本)**:非直接可重測;每次採用新基準模型(如加 QMJ/q-factor 到歸因)聯合假設 caveat 就重現、alpha 判定可能位移。具體=基準變更時重跑全部歸因。
- **重測優先度**:⚪ 低 — low — 基礎認識論慣例,非策略。

#### Novy-Marx (gross profitability) — asset pricing / 基本面品質因子
- **作者 · 年份**:Novy-Marx · 2013
- **分類**:機制族=α 產生(基本面品質)。原生棲地:資產=美股全市場、頻率=年頻財報、廣度=廣橫斷面、年代=1963-2010、用途=毛利/資產橫斷面選股。docs/19『品質 GP(Novy-Marx)』:座位=503 檔 PIT EDGAR ✓,錯置風險=低,『已在正確棲地確認』。
- **Summary / 結論**:gross profitability = 毛利/總資產,是穩健的品質因子。我方以 EDGAR PIT 對齊實作,是 alt-data pipeline 的示範因子,現已進旗艦當 +15% 品質 tilt。 結論:全 session 唯一穩健的新 alpha:廣有效率宇宙上 GP(基本面品質)勝價量動量——ICIR +0.30、跨期同號、regime-universal(bear/壓力最強=flight-to-quality)。
- **我們的洞見**:這是『對照組的正例』:在正確棲地測、而且贏了。GP L/S 單獨 Sharpe +0.45(modest 但真)。與集中動量低相關(+0.16)可加性。caveat:long-only sleeve 抬 alpha-t 是 beta 不是訊號(docs/00 §E9A,零訊號籃子一樣抬),須用 L/S 隔離。
- **用在哪 · 怎麼用 · 結果**:docs/10 §4b/4e;docs/00 §E2;docs/18 PASSED;docs/19 GP 列(低錯置);scripts/fundamental_factors.py、quality_research.py — gross_profitability=GrossProfit/Assets、PIT EDGAR;實測因子;旗艦 +15% 品質 tilt / 品質 sleeve;深掘 regime 適用地圖。 → **PASSED / adopted(ICIR +0.30;docs/18 PASSED)——已在正確廣橫斷面年頻財報棲地確認**
- **angle_risk(座位是否切錯)**:低 — docs/19 明列『已在正確棲地確認』(503 檔 PIT EDGAR、廣橫斷面、年頻財報)。這是反例:座位對、且贏。唯一 live 方法論再查=long-only 增量-α 須以 L/S 重驗(docs/00 §E9A)。
- **reopen(重測觸發=資訊成本)**:它 PASSED,故『翻案』=強化而非推翻:延長歷史(1990s)+更多真熊市確認 flight-to-quality 的 regime-universality;且任何 long-only 併入須以市場中性 L/S 重驗隔離訊號。
- **重測優先度**:⚪ 低 — low — 唯一在正確座位 PASSED 的因子;僅為強化(更長歷史/更多熊市/L-S 隔離複驗)而重測,非為推翻。

#### Grinold (fundamental law / breadth) — portfolio / 主動管理 IR 預算
- **作者 · 年份**:Grinold · 1989
- **分類**:機制族=驗證方法·描述(主動管理基本定律 IR=IC×√Breadth)。原生棲地:資產=不限、頻率=不限、廣度=IR 預算之核心變數、年代=1989、用途=把可達 IR 拆成 IC×獨立賭注數。作為我方全部負結果的組織性天花板——座位正確,且被 51→503 廣度實驗直接佐證。
- **Summary / 結論**:IR = IC × √Breadth。可達 Sharpe≈IR 被廣度與 IC 鎖死~1。是解釋我方全部負結果的物理上限。 結論:免費日線資料的 IC×廣度把可達 Sharpe 鎖在~1:0/56 配置達 Sharpe 2;三條件(≥5 策略 ∧ 低風險 ∧ 50-100%)數學互斥,根因是 Calmar≈f(Sharpe)、Sharpe 被廣度鎖死。突破只有換資料維度(廣度×16、或高 IC alt-data、或更高頻)。
- **我們的洞見**:演算法到頂;瓶頸是資料不是方法複雜度。唯一出路=換資料維度(docs/11 四條路)。並被 TR-14 深化:√breadth 假設獨立賭注,而我方 47 同產業高相關(zoo 59 變體有效試驗僅 1.8,ρ=0.54)→ 有效廣度≪名目。
- **用在哪 · 怎麼用 · 結果**:docs/06 §1;docs/11(四條路);docs/14 §75;docs/00 §E1;docs/08;TR-14(有效廣度 n_eff) — 因子搜尋前沿的物理上限(docs/06);換資料維度清單的組織原則(docs/11);解釋 Calmar 牆/Sharpe 天花板(docs/14、docs/00 §E1)。 → **adopted-as-convention(天花板/組織定律)+ 經驗確認:擴廣度 51→503 沒幫助(IC 隨 universe 變廣而降,docs/09)、0/56 配置達 Sharpe 2**
- **angle_risk(座位是否切錯)**:低 — 當正確組織定律使用,51→503 廣度實驗直接佐證。微妙點:√breadth 假設獨立賭注,我方高相關名使有效廣度≪名目(TR-14)——若有偏差是『低估廣度懲罰』而非切錯座位。
- **reopen(重測觸發=資訊成本)**:定律本身是數學不可測;但『廣度天花板』判定隨換資料維度而重開——ingest 數千低相關名(多資產/期貨/全球)或高 IC alt-data(每項皆 docs/11 的一筆資訊成本)。
- **重測優先度**:⚪ 低 — low — 已經驗確認的數學定律(擴廣度沒幫助);無可推翻,僅 docs/11 的資料維度變更會移動可達前沿。

### B.2 B. 資料窺探·過擬合·倖存者 (docs/03 附錄B)

#### White 2000 — 回測嚴謹性 / 資料窺探多重測試
- **作者 · 年份**:White · 2000
- **分類**:功能=驗證方法;原生棲地=規格搜尋下的交易規則資料窺探檢定(資產無關×任意頻率×規則家族選擇×用途=挑出贏家後的族群層 p 值)。docs/19 §5 歸為 fabric 自身工具、原生座位=回測稽核。
- **Summary / 結論**:用平穩 bootstrap 對「規格搜尋出的最佳模型相對基準無優越預測力」的虛無做檢定,產出考慮到全部 L 個被搜尋模型(而非只有贏家)的漸近有效 p 值。Example 2.2 本身就是一個多空交易訊號 vs buy&hold。 結論:單一策略的樣本內 Sharpe 在做過參數掃描後系統性樂觀;正解是對整族參數化取 max-statistic 的族群層 p 值。
- **我們的洞見**:我們選鉤子時(minervini 的 8 門檻、RS/ATR 掃描)必須有族群層 p 值;但實作首選 Hansen SPA(見下),White RC 只當概念基礎與保守篩。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B(逐篇);F5 多重測試 v2;docs/19 §5;O1 backtest/spa.py 設計 — 作為 F5 多重測試門檻的理論地基;closed-form E[max] Sharpe 當保守篩,SPA 當主要檢定。 → **adopted-as-convention(F5 地基;SPA 為實作首選,未單獨跑純 White RC)**
- **angle_risk(座位是否切錯)**:低。原生棲地就是交易規則的規格搜尋,與我們的座位完全一致;唯一刻意偏離=改用 Hansen SPA 因 RC 的檢定力會被垃圾策略稀釋到零(已在 docs/03 附錄B 記錄)。
- **reopen(重測觸發=資訊成本)**:若需要 max-statistic 的完整 bootstrap 分布做 SPA 的交叉檢核,或 SPA 對我們 GARCH/block 相依結構失準時 → 資訊成本≈$0(既有資料,純算力)。無外部觸發需求。
- **重測優先度**:⚪ 低 — low — 正確棲地、且被 Hansen 依設計取代;是工具非策略,無翻案動機

#### Hansen 2005 — 回測嚴謹性 / 多重測試
- **作者 · 年份**:Hansen · 2005
- **分類**:功能=驗證方法;原生棲地=策略族群選擇的多重測試(資產無關×任意頻率×用途=回測稽核)。docs/19 §5 原生座位=回測稽核。
- **Summary / 結論**:White RC 的嚴格改良版:studentize 損失差、採 sample-dependent 虛無以降權「差且無關」的替代策略。只要往候選集塞垃圾策略,RC 的檢定力可被打到零;SPA 免疫此問題。 結論:SPA 是我們選擇閘門的最佳多重測試工具——用每個策略自身 bootstrap 標準差 studentize,給出一致的 p 值。
- **我們的洞見**:把整個 gridded 規則族丟進一個檢定時,壞策略不會稀釋 SPA;定為 F5 的主要工具而非 plain RC。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;F5 多重測試 v2(主要工具);docs/19 §5;O1 backtest/spa.py — F5 變體家族的主要多重測試工具(closed-form E[max] 僅作保守篩)。 → **adopted-as-convention(F5 主要工具)**
- **angle_risk(座位是否切錯)**:低。原生棲地=策略選擇多重測試,與我們用途一致;無錯置。
- **reopen(重測觸發=資訊成本)**:若子期/資產顯示強 block 相依(ARCH/GARCH-M),需改用 block/wild-bootstrap 版 SPA 而非 iid 版 → 資訊成本≈$0(既有資料,計算成本)。
- **重測優先度**:⚪ 低 — low — 在原生座位、如設計運作的核心工具

#### Sullivan-Timmermann-White 1999 — 回測嚴謹性 / 技術交易規則資料窺探
- **作者 · 年份**:Sullivan, Timmermann & White · 1999
- **分類**:功能=驗證方法;原生棲地=股指、日頻、~100 年 DJIA、~7,846 條交易規則家族的窺探校正——這是本專案座位的最直接鏡像。
- **Summary / 結論**:把 White RC 套到 100 年 DJIA 上 ~7,846 條交易規則:最佳規則樣本內(1897–1986)撐過窺探校正,但樣本外(1987–1996)p≈0.12=無顯著經濟價值;S&P 期貨含實際成本後無一勝基準。 結論:從規則家族挑出的技術規則,樣本內漂亮但很可能是窺探驅動;必須以整個 grid 為宇宙報告被選 config 的 SPA 校正 p 值 + 硬性樣本外保留期。
- **我們的洞見**:把 Minervini/RS/ATR 全部變體視為宇宙;zoo 家族的有效變體數要計(TR-14 證 59 變體=1.8 個獨立賭注);設凍結的 post-2010 holdout 讓 optimizer 永不見。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B + 附錄E(BLB 警世案例);trial-registry(≈226);TR-14(zoo 59→1.8);F5 + 凍結 post-2010 holdout — 作為 zoo/變體家族窺探會計(trial-registry)與凍結 holdout 紀律的直接依據。 → **adopted-as-convention(操作化為 trial-registry + TR-14 有效變體計數 + 凍結 holdout)**
- **angle_risk(座位是否切錯)**:低-中。座位本身高度吻合(技術規則家族選擇);殘留風險=我們是否真的窮舉登記了完整試驗數 N——trial-registry 是我們的答案,但新增未登記家族會破功。
- **reopen(重測觸發=資訊成本)**:新增任何未登記的大型規則家族(如新的通道/濾網族)時,重跑 SPA + 更新 trial-registry → 資訊成本≈$0(既有資料重算)。
- **重測優先度**:⚪ 低 — low — 已操作化;只在未登記新家族時觸發

#### Bailey-Lopez de Prado 2014 (DSR) — 回測嚴謹性 / 過擬合校正
- **作者 · 年份**:Bailey & López de Prado · 2014
- **分類**:功能=驗證方法;原生棲地=回測稽核(試驗數 N × 非常態 × 軌跡長度校正;資產無關)。docs/19 §5 原生座位=回測稽核。
- **Summary / 結論**:DSR 依 (a) 試驗數、(b) 偏態/峰態(經 PSR)、(c) 軌跡長度校正觀測 Sharpe。明言 holdout/k-fold 不能防過擬合(「跑 20 次 holdout,偽陽性是預期內的」)。 結論:未控制搜尋規模的回測毫無價值;PurgedKFold 只擋洩漏、不擋選擇偏誤,必須在 CV 之上加 DSR 層,吃真實試驗數 N。
- **我們的洞見**:scorecard 的『Deflated Sharpe』點必須引用 trial-registry 的實際 N;時序宣稱另加 MinTRL(F4 時間維)。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;F4(MinTRL)/F5;docs/05(抓 Minervini);docs/19 §5;O1 backtest/deflated_sharpe.py — O1 backtest/deflated_sharpe.py(PSR+DSR)核心工具;F4 的 MinTRL 判準。 → **adopted-as-convention(scorecard 核心工具)**
- **angle_risk(座位是否切錯)**:低。原生棲地=回測稽核,與用途一致;無錯置。
- **reopen(重測觸發=資訊成本)**:若返回分布嚴重非常態、需更新 PSR 的 skew/kurt 動差估計,或 N 定義有爭議 → 資訊成本≈$0(既有 trial-registry)。
- **重測優先度**:⚪ 低 — low — 在原生座位的核心工具,如設計運作

#### Bailey-Borwein-Lopez de Prado (PBO/CSCV) — 回測嚴謹性 / 過擬合機率診斷
- **作者 · 年份**:Bailey, Borwein, López de Prado & Zhu · 2016
- **分類**:功能=驗證方法;原生棲地=回測稽核(組合對稱交叉驗證 CSCV 估 IS-best 在 OOS 低於中位的機率;自由度隨 N 升、隨 T 降)。
- **Summary / 結論**:CSCV 估計『樣本內最佳策略在樣本外低於中位』的機率。全過擬合虛無(N 策略真 Sharpe 皆 0)下 PBO≈1;它給出 DSR 給不了的『選擇程序本身是否脆弱』診斷。 結論:PBO 是選擇程序的脆弱度診斷;經驗法則 <30% 可信、>50% 雜訊;策略晉升應 gate 在 PBO<0.5。
- **我們的洞見**:用 CSCV 抓過我們自己的 Minervini(docs/05 PBO=0.93=嚴重過擬合);把 <30%/>50% 經驗法則寫進 F5。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;docs/05(Minervini PBO=0.93);docs/20 §4(旗艦 combo 缺口);F5;O1 backtest/pbo.py — O1 backtest/pbo.py;抓 Minervini 過擬合;F5 的 PBO 門檻註記。 → **adopted-as-convention(已用於 Minervini);旗艦 combo 8 配置的 PBO=queued(docs/20 §4 明列缺口)**
- **angle_risk(座位是否切錯)**:低。工具在原生座位;唯一缺口是覆蓋範圍——旗艦 combo 家族從未正式跑 PBO,不是切入角度錯而是尚未套用。
- **reopen(重測觸發=資訊成本)**:對旗艦 combo 家族(8 配置)跑 CSCV-PBO 並在 F5 加門檻註記 → 資訊成本≈$0(既有回測,小算力)。
- **重測優先度**:🟡 中 — medium — 工具正確,但『旗艦 combo 從未跑 PBO』是具體且已登記的缺口,值得清掉

#### Brown-Goetzmann-Ibbotson-Ross 1992 — 資料完整性 / 倖存者偏誤
- **作者 · 年份**:Brown, Goetzmann, Ibbotson & Ross · 1992
- **分類**:功能=資料完整性/驗證;原生棲地=基金績效樣本因存活截斷(廣宇宙×多年×用途=證明存活製造虛假持續性)。
- **Summary / 結論**:以存活截斷樣本會讓『波動-報酬』關係偽裝成績效持續性——單靠倖存者就能從純雜訊製造出『hot hands』,強到足以解釋已發表的可預測性。 結論:由當前上市代碼建的橫斷面 RS 排名與任何宇宙都是倖存者偏誤;下市/已死名必須在每個日期在冊,否則橫斷面因子可信度全毀。
- **我們的洞見**:點對點 universe 成分(含下市)是廉價現在做、昂貴事後補的硬前提(R3);TR-13 已給出倖存者膨脹的誠實區間 [+1.26%,+2.02%]/yr。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B(§1 VALIDATES + R3);docs/11(#1 倖存者);TR-13(區間化);F11/F13 — 驗證 scorecard 的倖存者線;F11 宇宙合法性 + F13 資料層下市注入的依據。 → **adopted-as-convention(倖存者紀律已採納;經 TR-13 部分處理);完整 PIT 宇宙=queued/受阻於資料**
- **angle_risk(座位是否切錯)**:低-中。論文主張已正確採納,但我們的宇宙仍非完整 PIT——610 union 無下市代碼、以價格行為分類。BGIR 的完整防護需要真正的逐日成分史,這是尚未買到的資料維度,不是切入角度錯。
- **reopen(重測觸發=資訊成本)**:ingest 點對點指數成分史(Wikipedia 版本史=免費但髒 / iShares-SPDR 歷史持股 / CRSP=付費學術)+ 下市報酬 → 資訊成本:從免費髒資料到付費 CRSP。
- **重測優先度**:🟡 中 — medium — 論文已採納,但底層 PIT 成分/下市資料缺口未解、且 gate 住所有橫斷面因子的可信度;是缺關鍵資料型的重測

#### Harvey-Liu-Zhu 2016 — 回測嚴謹性 / 因子多重測試門檻
- **作者 · 年份**:Harvey, Liu & Zhu · 2016
- **分類**:功能=驗證方法;原生棲地=因子動物園的領域級多重測試(數百因子×橫斷面×用途=校正後的顯著性門檻)。
- **Summary / 結論**:考量整個學界因子搜尋後,新因子的 t 門檻應提高到 ~3.0(而非 2.0);領域級多重測試把大量『發現』重新歸類為偽陽性。 結論:alpha 的 PASSED 門檻設 t≥3.0(或 BHY-FDR 1%)——這是領域級多重測試後的 alpha 標準。
- **我們的洞見**:把 t≥3.0 定為 F5/F8 的 alpha 硬門檻;旗艦多 sleeve 組合全成本 Carhart t=3.38 恰過此門檻(2× 成本壓力仍 t=3.14)。
- **用在哪 · 怎麼用 · 結果**:F5/F8(t≥3.0);docs/18 TR-15(t=3.38);docs/00 E9;README 核心公式表 — F5/F8 的 alpha PASSED 門檻;旗艦升級判定(TR-15)的達標線。 → **adopted-as-convention(alpha 門檻;旗艦以 t=3.38 過線)**
- **angle_risk(座位是否切錯)**:低。作為領域級門檻使用,棲地一致;殘留註記=旗艦過 HLZ 3.0 但未過全 campaign Bonferroni(需 t≈3.66),已誠實記錄。
- **reopen(重測觸發=資訊成本)**:收緊到 campaign 級 FWER(Bonferroni t≈3.66)或全面改用 BHY-FDR 1% → 資訊成本≈$0(既有 trial-registry 重算)。
- **重測優先度**:⚪ 低 — low — 慣例如設計運作;只有『收緊到 campaign 級』這一個已知且已記錄的開放項

#### Arnott-Harvey-Markowitz 2019 (AHM) — 回測嚴謹性 / 回測協定與研究紀律
- **作者 · 年份**:Arnott, Harvey & Markowitz · 2019
- **分類**:功能=驗證方法(meta 協定);原生棲地=ML 時代的回測紀律檢查表(資產無關×用途=動工前的預先承諾)。
- **Summary / 結論**:提出 ML 時代回測的協定/檢查表:預先承諾研究計畫、避免多重測試與過擬合、要求樣本外與經濟合理性、對成本與資料窺探誠實。 結論:每個 TR 動工前應先寫可證偽宣稱、判準、原生棲地/座位、錯置風險與翻案條件——即 AHM 檢查表的操作化。
- **我們的洞見**:F0『預先承諾聲明』就是 AHM 檢查表的落地;並作為 v1.2 對抗性框架審查的基點之一。
- **用在哪 · 怎麼用 · 結果**:F0(預先承諾檢查表);docs/17 v1.2 審查基點;docs/00 E9 — F0 動工前預先承諾聲明的模板;fabric v1.2 審查基點。 → **adopted-as-convention(F0 檢查表即其操作化)**
- **angle_risk(座位是否切錯)**:低。作為 meta 協定/檢查表使用,原生用途就是 ML 時代回測紀律,與我們一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a — meta 協定不需重測;若協定更新版發布可增修 F0 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 流程紀律,已內化為 F0

#### Lo 2002 — 績效統計 / Sharpe 推論
- **作者 · 年份**:Lo · 2002
- **分類**:功能=風險測量/統計;原生棲地=任何報酬序列的 Sharpe 統計推論(自相關校正的年化調整)。
- **Summary / 結論**:Sharpe 的年化與其標準誤受報酬序列相關性影響;有正自相關時 naive √252 年化會高估,需以自相關校正的除子調整。 結論:|lag-1 自相關|>0.05 時,Sharpe 年化須做 Lo (2002) 自相關校正,否則平滑/相依報酬的 Sharpe 灌水。
- **我們的洞見**:F3 規定超額-over-BIL Sharpe 且在自相關顯著時附 Lo 校正;已在 restate_rf_sharpe.py 實作 lo_factor 除子。
- **用在哪 · 怎麼用 · 結果**:F3;scripts/restate_rf_sharpe.py(lo_factor,lag-1..5);README 核心公式表 — F3 rf/基準慣例的一部分;restate 每個絕對 Sharpe。 → **adopted-as-convention(已實作於 restate_rf_sharpe.py)**
- **angle_risk(座位是否切錯)**:低。原生棲地=Sharpe 的自相關統計校正,與用途完全一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a(已實作);若要擴充到完整 IID/GMM 的 Sharpe 推論或多期重疊校正 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 已實作、在原生座位

#### Shumway 1997 (delisting) — 資料完整性 / 下市偏誤
- **作者 · 年份**:Shumway · 1997
- **分類**:功能=資料層/驗證;原生棲地=含下市代碼的 CRSP 型面板(NYSE/AMEX 績效型下市 ~−30%、Nasdaq ~−55%)。被測座位=無下市代碼的 610 檔 union、以價格行為分類。
- **Summary / 結論**:CRSP 遺漏的績效型下市報酬平均約 −30%(Nasdaq ~−55%);忽略它=以最後觀測價出場=系統性樂觀高估報酬。 結論:下市須注入終端報酬(併購型不注),否則凍結在最後價=教科書級倖存者高估。
- **我們的洞見**:TR-13:9 個窗內下市全為併購型(注 −30% 幾乎不動);真偏誤在 151 個被清除名,合成上界給出倖存者膨脹誠實區間 [+1.26%,+2.02%]/yr;凡引 610 union 絕對數字自此標區間。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-13;F13 資料層;docs/11(下市報酬);trial-registry — TR-13 跑實測並產出區間;F13 資料層下市注入規則(併購不注)。 → **PASSED(方法;TR-13 區間化完成)**
- **angle_risk(座位是否切錯)**:中。原生棲地=含下市代碼的 CRSP 面板;我們的座位無代碼、只能以價格行為分類——核心紀律=併購絕不能注 −30%(TR-13 自評錯置=中)。這是真實的錯置風險,但已被規則吸收;殘留=區間非點估計。
- **reopen(重測觸發=資訊成本)**:ingest CRSP 型下市代碼面板(WRDS 學術付費)→ 把 [+1.26%,+2.02%] 區間收成點估計;資訊成本=付費 CRSP/WRDS。
- **重測優先度**:🟡 中 — medium — 方法已過,但誠實數字只是區間;收緊需付費下市資料(明碼標價的資訊成本)

#### Hoffstein (rebalance timing luck) — 回測嚴謹性 / 再平衡時點運氣
- **作者 · 年份**:Hoffstein, Sibears & Faber · 2019
- **分類**:功能=驗證方法/風險塑形診斷;原生棲地=任何日曆再平衡策略(棲地無關)。TR-12 F0 自評錯置=低。
- **Summary / 結論**:同一策略在不同再平衡錨定日之間的績效差是非技能雜訊,量級常超過策略間的比較差;正解=K 分批(每相位 1/K)或以相位平均序列作判定。 結論:單相位錨定的數字不可獨立採信;判定須用相位平均(tranche)序列。
- **我們的洞見**:TR-12:季動量 timing-luck 帶寬 1,753bps/yr(單相位數字自此不足採信)、月動量 746bps;旗艦 combo 相位免疫(30bps)無需改;實盤動量應 K=4 分批;定為 F12。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-12;F12;docs/18 TR-12(1,753bps) — TR-12 量化各家族帶寬 + 相位-0 位置檢驗;F12 再平衡相位規則。 → **PASSED(方法;TR-12 揭露 timing luck,3 修正生效)**
- **angle_risk(座位是否切錯)**:低。原生棲地=日曆再平衡策略(棲地無關),我們就在此座位窮舉全部相位測試;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a — 已於原生棲地窮舉相位測完;若新增其他日曆錨定策略,F12 直接套用 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 完全在原生座位、方法已過並已成 F12 強制關卡

#### Cederburg-ODoherty-Wang-Yan 2020 — 回測嚴謹性 / 波動管理的懷疑性控制
- **作者 · 年份**:Cederburg, O'Doherty, Wang & Yan · 2020
- **分類**:功能=驗證方法/控制組;原生棲地=股票波動管理組合、月頻——作為 Moreira-Muir(1/σ² 波動管理)宣稱的懷疑性靜態控制。
- **Summary / 結論**:對 Moreira-Muir 的波動管理組合做樣本外檢驗:風險匹配的靜態/恆定曝險常能複製甚至勝過波動管理的表現,顯示其樣本外優勢不穩健。 結論:任何『MDD 減半 / 風控增益』宣稱都要配風險匹配的靜態(常數曝險)控制;能被一個常數旋鈕複製的就不算增值。
- **我們的洞見**:TR-02b:靜態 57% 恆定曝險同 MDD、更高 exSharpe、零交易——Markov regime gate 對曝險決策零增值;TR-17:1/σ² 波動管理支配 KMZ 全部 18 變體但 Cederburg 警告其對靜態的優勢不穩健、勿直接當策略;定為 F6 v2 靜態控制 + Nagel 三件套之一。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-02(§Cederburg 補跑);F6 v2 靜態控制;TR-17(波動管理控制);docs/18 TR-02 — TR-02b/TR-17 的靜態控制組;F6 v2『擇時/複雜度類必答:哪個最簡單的控制能解釋它』。 → **adopted-as-convention(TR-02b/TR-17 的控制組;F6 標準攻擊武器)**
- **angle_risk(座位是否切錯)**:低。作為懷疑性控制工具使用,原生用途就是檢驗波動管理宣稱,與我們一致;控制『贏了』正是它該做的事。
- **reopen(重測觸發=資訊成本)**:n/a — 控制工具已採納入 F6;無翻案概念。若未來要把 1/σ² 波動管理當策略而非控制,才需重評其穩健性 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 控制工具在原生座位正確使用,v1.2 審查已確認

#### GISW (Sharpe manipulation) — 績效測量 / 操縱防護度量
- **作者 · 年份**:Goetzmann, Ingersoll, Spiegel & Welch · 2007
- **分類**:功能=風險測量;原生棲地=任何具選擇權式/凹型 payoff 的策略——Sharpe 等常見度量可被賣選擇權/動態策略人為拉高,MPPM 是不可操縱的替代度量。
- **Summary / 結論**:標準績效度量(含 Sharpe)可被具凹型/選擇權式報酬的策略系統性拉高(如賣尾部保險);作者提出理論上不可操縱的 MPPM(冪效用型)。 結論:當策略有負偏態/選擇權式 payoff 時,Sharpe/t 值會被操縱式高估,需以 MPPM 做操縱防護交叉檢核。
- **我們的洞見**:(尚未採納)——本專案整條評估鏈重度依賴超額-over-BIL Sharpe、Lo 校正 Sharpe 與 t 值,但從未套用 MPPM;而 L≥1.5 槓桿 combo 與防禦 overlay 正是 GISW 針對的偏態 profile。
- **用在哪 · 怎麼用 · 結果**:(無——repo 未引用);候選落點=F3/F8 的 Sharpe 評估層 — 未使用。repo 全域 grep Ingersoll/Spiegel/manipulat/MPPM 皆無命中(僅 Goyal-Welch 與一處 Welch t-test)。 → **not-yet-tested(全專案未引用;為候選採納項)**
- **angle_risk(座位是否切錯)**:尚未切入,故無『切錯座位』——但這正是盲點:我們用 Sharpe/t 評估的槓桿與防禦 sleeve 具凹型/負偏 payoff,恰是 GISW 警告 Sharpe 會被高估之處。等於我們一直用一把可被這些 payoff 操縱的尺。
- **reopen(重測觸發=資訊成本)**:當任一策略具選擇權式/負偏態 payoff(現有 L≥1.5 槓桿 combo、防禦 overlay,或未來 covered-call/short-vol sleeve)→ 加算 MPPM 作操縱防護交叉檢核;資訊成本≈$0(純度量、免費資料,唯一成本是實作)。
- **重測優先度**:🟡 中 — medium — 真實盲點(整條評估鏈依賴 Sharpe,且已有偏態 sleeve 落在 GISW 靶心),但採納極廉價;適合開一個小 TR / F3 增修

#### Petersen 2009 (clustered SE) — 計量統計 / 面板標準誤
- **作者 · 年份**:Petersen · 2009
- **分類**:功能=風險測量/統計;原生棲地=面板資料標準誤(跨時間/跨個體相依→需聚類校正)。docs/19 §5 原生座位=fabric 工具。
- **Summary / 結論**:面板迴歸的 OLS 標準誤在存在跨時間或跨個體相依時嚴重低估;比較 Fama-MacBeth、聚類(by firm / by time)等方法,指出應依相依結構選擇聚類維度。 結論:跨相依的變體/事件不是獨立樣本;有效樣本數與 t 值須做聚類校正(n_eff、月度 CR1 或 block bootstrap)。
- **我們的洞見**:TR-14:n_eff = k·n/(1+(k−1)·ρ̄) 套回各 TR 的 F4 宣稱(zoo 59 變體實為 1.8 個獨立賭注、QQQ+SPY ρ=0.94→n_eff 2,206 FAIL);Serenity(docs/16)月度聚類把 t=2.49 打回 ~1.0-1.4;定為 F4/F7 的聚類 t。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-14(tr14_neff.py);F4/F7(聚類 t);docs/16 Serenity(t 2.49→1.0-1.4) — scripts/tests/tr14_neff.py 實作 n_eff 聚類邏輯;F7 子期聚類校正 t。 → **adopted-as-convention(已實作 n_eff + 聚類 t)**
- **angle_risk(座位是否切錯)**:低。原生棲地=面板標準誤,與我們用途(跨相依變體/事件的聚類校正)完全一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a(已實作);若要從 by-time 聚類擴到雙向聚類(firm×time)或 Driscoll-Kraay → 資訊成本≈$0(既有資料重算)。
- **重測優先度**:⚪ 低 — low — 已實作、在原生座位、v1.2 審查確認

### B.3 C. 組合與部位 (docs/03 附錄C)

#### Markowitz 1952 — 組合理論 / capital allocation (portfolio construction)
- **作者 · 年份**:Markowitz, H. · 1952
- **分類**:機制族=風險塑形·配置(mean-variance 框架公理)。原生棲地:資產=任意(需 N≥2)、頻率=任意(靜態單期)、廣度=需 μ 與 Σ 兩組輸入、年代=1950s 前指數化時代、用途=單期組合選擇。
- **Summary / 結論**:拒絕『最大化折現期望報酬』(該準則不蘊含分散),改以 E-V 規則:效率集在均值對變異數間取捨,且是共變異數(不是個別變異數)驅動分散效益。純理論/公理層論文,非可證偽的實證假設。 結論:選到好名字 ≠ 好組合;決定組合風險的是被選名單的 covariance structure,不是個別資產的優劣。
- **我們的洞見**:portfolio/ 必須消費一個 Σ 而非只吃 expected-return scores;相關性高的 Minervini winners(常同產業/同因子)不做 covariance-aware sizing 就會集中風險。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C；src/trading_analysis/portfolio/covariance.py 與 allocators.py(covariance-aware 配置的前提)；docs/18 §3 rulebook(組合層再平衡) — 作為 portfolio 模組的框架公理:所有配置器都建立在『吃 Σ』之上,而非另做一個實證測試去驗證 E-V 本身。 → **adopted-as-convention(基礎框架公理,未單獨跑 TR;covariance-aware sizing 的地基)**
- **angle_risk(座位是否切錯)**:低。E-V 是公理不是我們去證偽的假設,無『錯座位』問題。唯一潛在錯置:把它當『max-Sharpe MVO 藍圖』照做——我們刻意沒有(見 Michaud/DGU),改用 risk-parity。因此真正被實證檢驗到的其實是它的 naive 實作(MVO),而非 E-V 原則;不要把 MVO 的失敗記在 Markowitz 頭上。
- **reopen(重測觸發=資訊成本)**:公理層,不需『重測』。唯一會改變用法的事件:取得夠長且穩定的 μ 估計(DGU:25 資產需 ~3000 月)——現實不可及,故 E-V 的 max-return 版永遠讓位給只用 Σ 的 risk-only 版。資訊成本=極長且 PIT 乾淨的歷史。
- **重測優先度**:⚪ 低 — low — 公理層框架,已內建於 portfolio 模組;本身不是可證偽的座位。

#### Michaud 1989 — 組合最佳化 / estimation risk
- **作者 · 年份**:Michaud, R. · 1989
- **分類**:機制族=估計工程(對 MVO 的批判/警示)。原生棲地:資產=任意、頻率=任意、廣度=估計誤差顯著的 N、年代=1980s、用途=警示 naive optimizer、界定 robust/resampled MVO 為 baseline。
- **Summary / 結論**:MV 最佳化是『estimation-error maximizer』——系統性 overweight 報酬被高估、變異被低估、負相關為假象的資產,因此 unconstrained MV 樣本外可劣於等權。 結論:絕不上 naked/unconstrained MVO;要 box/turnover 約束,並以 resampling/robust MVO 為 baseline 而非 vanilla MVO。
- **我們的洞見**:O5 建構約束:never ship unconstrained MVO;把 max-Sharpe MVO 降為必須自證的 also-ran(R8),portfolio/ 改以 risk-parity/min-var 為主。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §1 VALIDATES + §2 O5;docs/18 §3(demote MVO);portfolio/allocators.py(改用 risk_parity/min_variance 的決策依據) — 作為負面設計約束寫死在 roadmap:攔截『PyPortfolioOpt MVO』roadmap 線的字面照做;塑造了『不建 naked MVO』的決策,而非跑一張 TR。 → **adopted-as-convention(建構約束;塑造『不建 naked MVO』的架構決策)**
- **angle_risk(座位是否切錯)**:低。Michaud 的主張=『naive MVO 壞』,我們正是在這座位上採納它(從不建 naked MVO),無錯置。它是負面約束不是我們去證偽的 alpha 機制;不會有『機制未定罪但座位錯』的疑慮。
- **reopen(重測觸發=資訊成本)**:若取得穩健的 robust/resampled-MVO 實作 + 顯著更長的估計窗,可測『約束後 MVO 是否勝 risk-parity』——但 DGU 已預示於我們的資產數不太可能。資訊成本=更長歷史 + 更多(異質)資產的 PIT 資料。
- **重測優先度**:⚪ 低 — low — 已在正確座位採納為約束;非決策路徑上的可證偽機制。

#### DeMiguel-Garlappi-Uppal 2009 — 組合配置 / optimizer benchmark
- **作者 · 年份**:DeMiguel, Garlappi & Uppal · 2009
- **分類**:機制族=風險塑形·配置的 hurdle/benchmark(naive 1/N)。原生棲地:資產=股票組合、頻率=月頻、廣度=各資料集約 10-25 資產、年代=1970-2004、用途=作為任何 optimizer 的樣本外門檻。
- **Summary / 結論**:14 個模型 × 7 個資料集,無一在 Sharpe、CEQ、換手上穩定勝 naive 1/N;sample-MVO 要勝 1/N 所需估計窗約 3,000 月(25 資產)、6,000 月(50 資產)——實務不可及。 結論:1/N 是 mandatory benchmark;任何 optimizer 必須在 walk-forward 上『淨換手』勝等權才准 size 實盤部位。
- **我們的洞見**:把等權設為硬性 scorecard 線(新增一條);start with risk-parity/min-var(避開 DGU 證明無望的 μ 估計),max-Sharpe MVO 必須自證。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §1;src/.../portfolio/allocators.py::equal_weight;TR-07 兩 Arena 皆列『等權(DGU 門檻)』;scripts/gate_3x_voo.py 的年度等權對照 — 在每個組合類 TR 都放『等權(DGU 門檻)』作對照;gate_3x_voo 也放年度等權 47 作 beta 對照。 → **adopted-as-convention(強制 1/N benchmark)+ 於我們座位 empirically CONFIRMED — TR-07 中 1/N 勝或平所有 optimizer(Arena A 等權 sleeves +24.95%/Sh 1.26;Arena B 月度等權 Sh 1.26 ≥ HRP 1.22 ≥ min-var(LW) 1.12)**
- **angle_risk(座位是否切錯)**:低-中。我們座位(5 sleeves N=5;47 同質高相關股)N 比 DGU 更小、相關更高,對 1/N 更有利,故 1/N 勝出是 DGU 的直接預言而非錯置。唯一 caveat:sleeves 是先前研究的樣本內產物(繼承偏誤),但那只影響絕對水準,不影響 1/N vs optimizer 的相對比較。
- **reopen(重測觸發=資訊成本)**:宇宙擴到大 N 異質(50+ 跨資產)且有長歷史時,optimizer 才有機會勝 1/N。資訊成本=多資產 PIT 資料 ingest + 長歷史。
- **重測優先度**:⚪ 低 — low — 已在正確(甚至更有利)座位確認;1/N 作為門檻是常態運作,不是待翻案項。

#### Ledoit-Wolf 2004 — 共變異數估計 / estimation engineering
- **作者 · 年份**:Ledoit & Wolf · 2004
- **分類**:機制族=估計工程(covariance shrinkage)。原生棲地:資產=廣橫斷面、頻率=任意、廣度=N 接近/超過 T 的樣本共變異、年代=2000s、用途=為任何 Σ-based 步驟提供穩健輸入。
- **Summary / 結論**:sample Σ 在 N→T 時充滿估計誤差;向結構化目標(此處 constant-correlation 模型)以解析最適強度 δ* 收縮;所有測試情境給最高 information ratio、最低實現波動。 結論:任何 Σ-based 步驟(MVO/min-var/risk-parity)都必須用 LW 收縮,絕不用 raw sample Σ。
- **我們的洞見**:全域強制的建構約束(一個 sklearn import、CPU-trivial、zero infra cost),讓 risk-parity/min-var 從第一天就吃收縮後的 Σ。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §2 O5;src/.../portfolio/covariance.py::shrunk_covariance(LedoitWolf/OAS);TR-03(PCA vs LW)、TR-07(min-var 用 LW)、docs/08 combo build(validate_recommendation.build_combo) — shrunk_covariance() 包住 sklearn 的 LedoitWolf/OAS,是所有配置器與因子共變異的預設輸入。 → **adopted-as-convention(全域強制);間接於 TR-03/TR-07 驗證有效 —— TR-07 中 LW 收縮讓 min-var 波動(18.17%)反而低於 HRP,先行解決了 HRP 想解的病態矩陣問題**
- **angle_risk(座位是否切錯)**:低。LW 用在其原生用途(共變異估計清理),座位正確。唯一『未做』不是錯置而是同族第三方法未橫評:尚未畫我們宇宙的特徵值譜 vs Marčenko-Pastur 帶、未比 LW vs eigenvalue-clipping vs 非線性 LW2020(docs/20 §2 的 TR-03b 佇列)。
- **reopen(重測觸發=資訊成本)**:執行 TR-03b:47/610 宇宙特徵值譜 vs MP 帶(幾個真訊號特徵值?),把 MP-clipping 加入 TR-03 競技場(vs LW vs PCA vs sample)。觸發=想在更大 N 宇宙做共變異估計時;資訊成本低(現有資料即可跑)。
- **重測優先度**:🟡 中低 — low-medium — 已全域採納且有效;medium 僅在於『LW vs MP-clipping vs LW2020』估計器 horse-race 尚未跑(TR-03b 佇列,便宜、可隨時執行)。

#### Kelly 1956 — 部位 sizing / growth-optimal capital allocation
- **作者 · 年份**:Kelly, J. L. · 1956
- **分類**:機制族=風險塑形·配置(growth-optimal sizing)。原生棲地:資產=任意、頻率=任意、廣度=需已知且穩定的 edge/odds (p,b)、年代=1956、用途=把二元 side 轉成 sized position。
- **Summary / 結論**:以最大化 G=E[log(wealth)] 下注(二元賭注 fraction=edge/odds)使資本以最大指數率成長,且在非終止賽局以機率 1 支配任何其他策略;押全資本雖最大化期望財富但幾乎必破產。 結論:用 fractional/half-Kelly(full Kelly 給定估計誤差太激進)由 meta-label 機率 p 與 triple-barrier payoff ratio b 來 size,而非固定比例或 raw signal strength。
- **我們的洞見**:sizing 應由機率驅動;half-Kelly 是 Michaud/DGU『估計誤差』教訓在 sizing 層的對應。真正存活並產生價值的用法是回撤預算 / 雙向槓桿 L 刻度。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + R2;src/.../portfolio/sizing.py::kelly_leverage(fraction=0.5, cap);docs/18 PASSED『回撤預算/雙向槓桿刻度』+ scripts/defensive_overlay.py;docs/19 §3(Kelly/回撤預算/L 刻度=如設計運作) — kelly_leverage(expected_return, variance, fraction=0.5, cap) 實作 half-Kelly;在防禦 overlay 以回撤預算/L 刻度落地(L≥1.5 combo 支配 VOO)。 → **adopted/implemented(half-Kelly 已實作)並作為『回撤預算/L 刻度』屬 PASSED 風險塑形(L≥1.5 支配 VOO)。但 R2 原案『Kelly 由 ML 機率驅動』因餵它的 meta-label edge(TR-08/11)FAILED 而未 productive 部署——存活的是 drawdown-budget/L-scale 這支。**
- **angle_risk(座位是否切錯)**:中。原生 Kelly 需要『已知且穩定的 edge (p,b)』。我們的 ML p(TR-08/11)FAILED,所以『Kelly 由 ML 機率驅動』這座位其實從未有可靠 edge 可 size——不是 Kelly 機制錯,是上游 alpha 缺席(G-S:$0 資訊成本 → $0 edge → 無可 size 之物)。因此『Kelly 有沒有幫助』的判定被上游 alpha 缺席污染;存活座位(drawdown-budget/L-scale on beta 曝險)是 Kelly 另一種、可運作的用法。
- **reopen(重測觸發=資訊成本)**:任何 sleeve 產出穩健 OOS edge (p,b) 時,Kelly-by-probability 座位重開——但那 gated on 先突破 alpha 牆(付資訊成本:日內/選擇權/另類資料)。否則維持 drawdown-budget/L 刻度用法。
- **重測優先度**:🟡 中 — medium — 機制本身如設計運作(已實作、L-scale PASSED);待重測的是『有真 edge 時的機率驅動 Kelly』,但它 gated on 先有 alpha,故非獨立高優先。

#### Cover 1991 — online 配置 / regret-minimizing allocation
- **作者 · 年份**:Cover, T. · 1991
- **分類**:機制族=風險塑形·配置(assumption-free online allocation)。原生棲地:資產=多資產、頻率=(隱含)長 horizon 再平衡、廣度=CRP 家族、年代=1991、用途=無統計假設下追平事後最佳 CRP 的 regret benchmark;關鍵:無交易成本。
- **Summary / 結論**:對所有 constant-rebalanced portfolios 做表現加權平均即為『universal』:不需任何市場統計假設(明確允許 1929/1987 崩盤),漸近成長率追平事後選定的最佳 CRP,(1/n)·ln(S*_n/S_n)→0。 結論:一個 no-estimation、no-Σ、no-μ 的 online 配置 baseline;定位為 research benchmark,而非核心依賴。
- **我們的洞見**:regret/robustness 心態支撐我們的 walk-forward 紀律;可作 assumption-free 對照,但明確標為低優先(R8),不進核心。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C(明列 optional low-priority benchmark)+ §3 R8 demote 段;docs/18(未見於任何 TR);未實作於 src/ — 僅作為觀念上的『無假設對照』寫入 roadmap;未寫任何程式。 → **not-yet-tested(刻意延後為 optional benchmark;未建 module)**
- **angle_risk(座位是否切錯)**:中-高(潛在)。Cover 原生棲地=長 horizon、**無交易成本**、CRP 家族,且 regret bound 是漸近的(需極長 n 才收斂)。若在我們日線、含成本、少資產、~10 年樣本座位測它,幾乎必因『無成本假設 + regret 未收斂』看似失敗——那會是錯置而非機制被駁。務必先想清楚座位再測。
- **reopen(重測觸發=資訊成本)**:想要一個 μ/Σ-free 的穩健對照時(例如質疑 risk-parity 的估計依賴),花小成本實作 UP / online-Newton-step 當 benchmark。資訊成本低(現有日線即可),但必須在誠實層下:含成本 + 標註『漸近保證、短樣本 regret 未收斂』。
- **重測優先度**:⚪ 低 — low — 刻意延後的 optional benchmark,非決策路徑;若實作,重點在避免錯置誤判(含成本 + 短樣本註記),而非搶跑。

#### Lopez de Prado HRP — 組合配置 / hierarchical (graph-based) allocation
- **作者 · 年份**:López de Prado · 2016
- **分類**:機制族=風險塑形·配置(hierarchical/graph-based allocation)。原生棲地:資產=大 N 異質宇宙(數十~百資產)、頻率=任意、廣度=越大 N 越異質越有利、年代=2016、用途=不需反矩陣、避開 Markowitz 之咒的樣本外穩健配置。明示為風險配置器,不宣稱選股 alpha。
- **Summary / 結論**:相關矩陣→距離 d=√(0.5(1-ρ))→single-linkage 樹→準對角化→遞迴二分,兩半各以叢集內反變異數算變異、按 α=1-v0/(v0+v1) 分配。不需反矩陣;MC 中樣本外變異比 CLA min-var 低約 31%、優於天真反變異數(IVP)。 結論:(我們的)於兩個被測座位 HRP 輸現役 log-barrier risk-parity(5 sleeves 上 Sharpe 1.44 vs 1.04,HRP 把 69.9% 塞進債券);LdP 的 −31% 變異優勢在真實資料縮到 −8%;字面『勝 1/N』不成立(Sh 1.22 vs 等權 1.26)→ 不換權重引擎。
- **我們的洞見**:不換配置引擎;但保留 HRP 的樹/dendrogram 當『約束』——47 檔選股設『每叢集最多 k 檔』防單一叢集(半導體/軟體/國防)集中,F6 permuted-HRP 控制組證明此結構資訊有真增量。純降波動則反波動以 1/7 換手拿到多數效果、更划算。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C(R8);docs/tests/TR-07-hrp.md(PARTIAL);docs/18 TR-07;docs/19 §3(錯置中-高);scripts/tests/tr07_hrp.py;src/.../portfolio/allocators.py — TR-07 兩 Arena(5 sleeves 13,045 bar×asset;47 檔 119,863 bar×asset),月頻 walk-forward、10bps/腿、permuted-HRP 20-seed 控制組;scipy 重寫 HRP 對打現役 risk_parity/min-var/等權/反波動。 → **PARTIAL(TR-07:機制如設計降波動 −3.9pp,permuted-HRP 控制證明來自叢集結構而非權重分布;但決策問題輸現役 risk_parity → 不換)**
- **angle_risk(座位是否切錯)**:中-高 —— 本批最需注意錯置的一篇。HRP 原生棲地=大 N 異質;我們兩座位都對它不利(N=5 太小,single-linkage 在小 N 鏈化、切點不穩;47 檔同質高 beta 叢集 2022 一起跌)。TR-07 的 PARTIAL/輸只關閉『小 N』與『同質』兩座位,**不定罪 HRP 於其原生大 N 異質宇宙**。此外 LW 收縮已先替我們解掉 HRP 想解的病態矩陣問題,削弱了它相對 min-var 的原始賣點。
- **reopen(重測觸發=資訊成本)**:取得 50+ 檔真異質多資產宇宙(跨股/債/商品/國際/另類)即重測 HRP 於其原生棲地。資訊成本=多資產 PIT 資料 ingest(收斂回 docs/11『資料維度是綁定約束』)。
- **重測優先度**:🟡 中 — medium — 錯置風險中-高(座位明顯偏離原生棲地),但『要不要換(決策問題)』已在我們實際使用的座位穩固回答、且 LW 已解掉其核心賣點,故 HRP 本身重測是 medium(待有大 N 異質宇宙資料時),不是 high。

### B.4 D. 執行與微結構 (docs/03 附錄D)

#### Kyle 1985 — 市場微結構 / 最適執行（price impact）
- **作者 · 年份**:Albert S. Kyle · 1985
- **分類**:機制族=執行·流程類（價格衝擊/市場微結構）。原生棲地：資產=單一風險資產；頻率=連續拍賣/tick；廣度=單資產；年代=1985；用途=策略性知情下單下的價格發現。座位對照：docs/19 執行類。錯置風險=中——我們從未在其原生『策略性知情下單』座位使用，只借 λ 當 Amihud 成本代理。
- **Summary / 結論**:Kyle 1985 建立線性均衡：知情交易者的淨訂單流以單一常數 λ 推動價格，市場深度=1/λ，衝擊永久且線性、λ∝√(雜訊變異/私有資訊變異)。我們沒在其原生的『策略性知情下單/價格發現』座位使用，只借 λ 當 Amihud 成本代理，把回測的固定 bps 成本升級為 size-dependent。在 $100k 零售規模衝擊項近乎零，spread 才是一階成本。 結論:價格衝擊由單一常數 Kyle-λ 治理（市場深度=1/λ），衝擊永久且線性、與訂單/ADV 成比例——固定 bps 成本假設在結構上錯誤。
- **我們的洞見**:採納 Kyle-λ≈(每日σ)/(每日$成交)=Amihud 流動性代理，把回測成本改成 size-dependent cost = spread/2 + λ·(trade_$/ADV)；但誠實記錄：$100k 零售書參與率≈0→衝擊項≈0、spread 才是一階，故 λ 項在我們的座位近乎惰性。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Kyle + §2 O2；backtest/costs.py（size_dependent_cost，已實作未接線）；docs/19 §1 執行類（Almgren-Chriss 列引用 costs.py） — docs/03 附錄D §Kyle + O2：設計 size-dependent 成本模型（backtest/costs.py 的 size_dependent_cost，λ=Amihud 代理）；docs/19 執行類引用。狀態：已實作、v1.2 審查（docs/20 §3）指出『從未接線』進回測。 → **adopted-as-convention（成本模型設計；costs.py 已實作但未接線進回測，非跑過 TR）**
- **angle_risk(座位是否切錯)**:中。我們從未在 Kyle 的原生座位（策略性知情下單、價格發現、機構/內線規模）使用它——只借了 λ 價格衝擊常數當 Amihud 每日流動性成本代理，套在 $100k 零售書上。此規模參與率≈0、衝擊項→0，等於把 Kyle 描述的核心機制（訂單流推動價格）用在它幾乎失效的座位；spread 才是一階。這不是誤判 Kyle（沒跑 TR），而是借來的機制在我們的座位近乎惰性——若日後規模放大或交易流動性差的小型股，λ 才會變成一階。
- **reopen(重測觸發=資訊成本)**:① 立即工程觸發：把 backtest/costs.py 的 size_dependent_cost 接線進回測（目前實作但未接線，v1.2 審查點名）。② 機制重開：資本規模放大到在所交易標的參與率>0，或改交易流動性差的小型股，使 λ·(trade_$/ADV) 變一階。③ 取得日內/tick 資料以直接估 λ（而非 Amihud 每日代理）——此為 G-S 意義下的一筆資訊成本。
- **重測優先度**:⚪ 低 — low — 已採納為成本慣例；零售規模衝擊項≈0（spread 一階），唯一待辦是工程接線 costs.py 而非重測

#### Bertsimas-Lo 1998 — 最適執行 / 交易成本分析
- **作者 · 年份**:Dimitris Bertsimas & Andrew W. Lo · 1998
- **分類**:機制族=執行·流程類（區塊最適執行/實施落差）。原生棲地：資產=機構區塊單；頻率=日內 N 期分批；廣度=單標的區塊；年代=1998；用途=最小化期望執行成本。錯置風險=低——採納的是 implementation-shortfall 會計原則與 TWAP 基線，非在零售規模硬套 DP。
- **Summary / 結論**:Bertsimas-Lo 1998 把最佳執行寫成動態規劃（Bellman），證明在算術隨機漫步+線性永久衝擊的最簡假設下等量分批（TWAP）最適，資訊態加一個線性 shifting 修正。並以 Perold 實施落差（紙上 20%/yr→實盤 2.5%/yr）點出執行成本就是紙上-實盤缺口。我們採納 TWAP 基線與 implementation-shortfall 會計原則，TR-12 的 K=4 分批即此直覺。 結論:最適執行=Bellman 動態規劃；在算術隨機漫步+線性永久衝擊下最適解=等量分批（TWAP）；Perold 實施落差（紙上 20%/yr→實盤 2.5%/yr）證明紙上-實盤差距就是執行成本。
- **我們的洞見**:採納兩件事：(a) TWAP/等量分批為 execution/ 預設基線（最簡假設下可證最適、零調參）；(b) 以 implementation shortfall（arrival vs 實際成交）取代無摩擦 Sharpe 當頭條成本指標——直接對治 Perold 紙上-實盤缺口。TR-12 的 K=4 分批即 TWAP 直覺的體現。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Bertsimas-Lo + §3 R5 + §2 O2；TR-12（K=4 分批=TWAP 直覺）；rigor scorecard 的 implementation-shortfall 行（規劃中） — docs/03 附錄D §Bertsimas-Lo + R5：TWAP 為 execution/ 預設基線 + implementation-shortfall 頭條成本指標；TR-12 K=4 分批體現 TWAP 直覺對抗 timing-luck。 → **adopted-as-convention（TWAP 基線 + IS 會計原則；TR-12 K=4 體現，非獨立跑過 TR）**
- **angle_risk(座位是否切錯)**:低。採納的是正確高度的教訓（implementation shortfall 會計 > 無摩擦 Sharpe，Perold 20%→2.5% 例）與 TWAP 基線，而非在零售規模硬套區塊執行 DP。零售 $100k 幾乎不存在『單一大單需跨期分批』的問題，所以我們沒把 DP 誤置；TR-12 的 K=4 分批只是借用 TWAP 直覺對抗 timing-luck，座位相符。
- **reopen(重測觸發=資訊成本)**:① 當 execution/ 真正動工、需要 implementation-shortfall 帳本（arrival price vs 實際成交）時。② 資本規模使單筆單>數% ADV、必須跨期分批時，BL 的 TWAP-最適與 shifting 修正才有可測內容。零售規模下無此觸發。
- **重測優先度**:⚪ 低 — low — 原則已採納、TR-12 已體現 TWAP；零售規模無區塊分批問題可測

#### Almgren-Chriss 2000 — 最適執行 / 清算軌跡與風險
- **作者 · 年份**:Robert Almgren & Neil Chriss · 2000
- **分類**:機制族=執行·流程類（風險趨避最適清算/交易半衰期）。原生棲地：資產=機構清算部位；頻率=日內排程；廣度=可組合層；年代=2000；用途=成本-風險效率前沿。docs/19 §1 已收錄：原生棲地=機構規模（參與率>0 的市場衝擊）。錯置風險=低——已辨識規模不符、誠實跳過，未誤測。
- **Summary / 結論**:Almgren-Chriss 2000 在 Bertsimas-Lo 上加入風險罰項，得成本期望-變異數效率前沿與封閉解交易半衰期 τ=1/κ（波動越高/流動性越差交易越快，τ 與外加期限 T 無關）。我們採納 τ 當容量檢查，但辨識原生棲地=機構規模、在 $100k 零售大型股座位衝擊項→0，故誠實跳過未開 TR，costs.py 留給 F2 v2 容量曲線。 結論:在 BL 上加風險罰項→成本期望-變異數效率前沿與封閉解交易半衰期 τ=1/κ；波動越高/流動性越差→交易越快；τ 是波動·流動性·趨避決定的內在時間尺度、與外加期限 T 無關。
- **我們的洞見**:採納『交易速度應為 σ 與流動性的函數』與 τ=1/κ 容量檢查（部位若 AC 半衰期>再平衡視窗即過大）；但誠實判定我們的規模不符其原生棲地（參與率≈0、衝擊項→0、spread 一階），故 costs.py 已實作但不另開 TR，留給 F2 v2 容量曲線引用。
- **用在哪 · 怎麼用 · 結果**:docs/20 §3；docs/19 §1 執行類（誠實跳過列）；docs/03 附錄D §Almgren-Chriss + §3 R5；backtest/costs.py（F2 v2 容量曲線待用） — docs/03 附錄D §Almgren-Chriss + R5 + docs/20 §3 + docs/19 §1 執行類：τ=1/κ 容量檢查納入路線圖；因規模不符誠實跳過未開 TR；costs.py 已實作留 F2 v2 容量曲線。 → **adopted-as-convention（設計採納為容量檢查；因規模不符誠實跳過、未開 TR；costs.py 已實作未接線）**
- **angle_risk(座位是否切錯)**:低（座位錯置已被正確辨識並規避）。docs/19 明確標註原生棲地=機構規模（參與率>0 的市場衝擊）；在 $100k 零售大型股座位參與率≈0、衝擊項→0，AC 的交易排程是二階問題、spread 是一階，因此誠實跳過未開 TR——即沒有把機構級清算模型誤測在零售座位上。殘餘角度風險純為『規模』：一旦資本放大或交易流動性差標的，AC 半衰期>再平衡視窗的容量檢查就變成一階。
- **reopen(重測觸發=資訊成本)**:資本規模達機構級或交易流動性差宇宙，使參與率>0、市場衝擊變一階；具體觸發=某部位使 AC 交易半衰期 τ=1/κ > 再平衡視窗（docs/19：F2 v2 容量曲線引用 costs.py 的 size_dependent_cost 時）。此為需要更大資金/更差流動性座位的重開。
- **重測優先度**:⚪ 低 — low — 已辨識規模不符、誠實跳過（未誤測）；僅機構規模/流動性差宇宙才重開

#### Obizhaeva-Wang 2013 — 市場微結構 / LOB 韌性最適執行
- **作者 · 年份**:Anna Obizhaeva & Jiang Wang · 2013
- **分類**:機制族=執行·流程類（LOB 韌性/供需動態）。原生棲地：資產=限價簿；頻率=日內訂單簿回補；廣度=單標的大單（20× 深度）；年代=2013；用途=韌性感知最適排程。錯置風險=低——未測、資料閘控（需日內 LOB），刻意只收斂成單一壓力旋鈕，非誤測。
- **Summary / 結論**:Obizhaeva-Wang 2013 證明最適排程取決於 LOB 韌性（訂單簿回補速度）而非靜態深度/點差，最適形狀是大初始單+小連續單+末端區塊（非等量），相對 TWAP 的節省隨回補時間增長（0.33%→1.88%→7.41%，20× 深度單）。我們決定不建 LOB 模擬器，只把韌性收斂成單一『回補半衰期』壓力旋鈕；因缺日內 LOB 資料，此旋鈕仍為設計未建。 結論:最適排程取決於韌性（LOB 回補速度）而非靜態深度/點差；最適形狀=大初始單+小連續單+末端區塊（非等量）；相對 TWAP 的成本節省隨回補時間增長（0.33%→1.88%→7.41%，20× 深度單）——挑戰 BL/AC 的 TWAP-最適結論。
- **我們的洞見**:採納『不建 LOB 模擬器，改把韌性收斂成單一回補半衰期敏感度旋鈕』，在成本模型/rigor scorecard 上以快/慢回補帶寬壓力測試淨 Sharpe——避免容量宣稱被樂觀日內流動性綁架。但因缺日內 LOB 資料，此旋鈕仍為設計、尚未建置。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Obizhaeva-Wang + §3 R5；rigor scorecard 的 resilience-sensitivity 行（規劃中，未建） — docs/03 附錄D §Obizhaeva-Wang + R5：韌性=單一壓力旋鈕（回補半衰期）寫入 execution/ 成本模型與 rigor scorecard 設計；未建（需日內 LOB）。 → **not-yet-tested / queued（韌性壓力旋鈕設計，資料閘控未建）**
- **angle_risk(座位是否切錯)**:低（尚未測、資料閘控）。從未在任何座位套用，故無誤置；唯一角度風險是它的原生棲地（日內 LOB 韌性、訂單簿回補動態、機構單 20× 深度）需要我們在 <$15/mo 下沒有的日內 LOB 資料。我們刻意不建 LOB 模擬器、只把韌性收斂成單一『回補半衰期』敏感度旋鈕——這是正確的規避，不是誤測。
- **reopen(重測觸發=資訊成本)**:取得日內 LOB / 訂單簿韌性資料（G-S 意義下的資訊成本；<$15/mo 下目前受阻）+ 交易規模達到 ≥ 簿深度。具體觸發=ingest 日內 LOB 資料後，把『回補半衰期』從單一壓力旋鈕升級為真實估計。
- **重測優先度**:⚪ 低 — low — 資料閘控（需日內 LOB），現有資料維度無法測；正確延後

#### Grossman-Stiglitz 1980 — 資訊經濟學 / 市場效率（元理論）
- **作者 · 年份**:Sanford J. Grossman & Joseph E. Stiglitz · 1980
- **分類**:機制族=描述·歸因 / 元理論（資訊經濟學均衡）。原生棲地：資產=理性預期資產市場均衡；頻率=跨頻率通用；廣度=市場整體、知情 vs 未知情交易者；年代=1980；用途=解釋為何完全效率不可能。錯置風險=中——作為框架哲學採納、非可測策略；風險=過度外推成『免費資料 alpha 全不可能』。
- **Summary / 結論**:Grossman-Stiglitz 1980 證明資訊有成本則完全效率不可能，均衡下知情交易的期望毛利恰等於資訊成本，alpha 被競爭到資訊成本線（永不歸零也永不免費）。這是本專案全部負結果的經濟學基礎：免費日線=$0 資訊成本→均衡 $0 alpha，能留下的只有風險溢酬與組合層風險塑形；每個翻案條件都是一筆資訊成本。 結論:資訊有成本→完全效率市場不可能；均衡=部分無效率，知情交易的期望毛利恰好等於資訊成本；alpha 被競爭到資訊成本線，永不歸零也永不免費。
- **我們的洞見**:把 G-S 定為全專案負結果的經濟學基礎：我們 130+ 機制實證收斂（免費日線上選股 alpha≈0、唯一 PASSED=組合層風險塑形）正是 G-S 均衡的直接預言——資訊成本=$0→均衡 $0 alpha。並據此重寫 alpha 判定哲學：任何 PASSED 的 alpha 必須能講出『誰在付我們資訊成本的補償』；每個翻案條件都是一筆資訊成本。
- **用在哪 · 怎麼用 · 結果**:docs/20 §6；README『我們如何判斷』；fabric F8 alpha 判定哲學註記；docs/11（資料維度=綁定約束）；作為全專案負結果的經濟學基礎 — docs/20 §6（本輪寫入）+ README『我們如何判斷』段 + fabric F8 alpha 判定哲學註記：定為全專案負結果的經濟學基礎與 alpha 判定哲學；docs/11『資料維度是綁定約束』的更深表述（要買 alpha 先付資訊成本）。 → **adopted-as-convention（框架哲學/元理論；非可測策略，無 TR）**
- **angle_risk(座位是否切錯)**:中（框架哲學採納，非可測機制）。角度風險不在『測錯座位』而在『過度外推』：我們把資訊成本=$0（免費日線）→均衡 alpha=$0 當作全專案負結果的解釋。但 G-S 本身預言 alpha 存活於資訊成本高、套利者少之處（小型股、被忽略角落）——若拿 G-S 當『免費資料上 alpha 一律不可能』的萬用擋箭牌，反而違背其精神。正確用法：它是為每一個『翻案條件』標價的透鏡（每筆資訊成本=一次潛在買回 alpha 的機會），而非否證一切的封口令。
- **reopen(重測觸發=資訊成本)**:非策略、無單一重開事件；它是為所有其他翻案條件『定價』的元條件。實務觸發=任何一次付出新的資訊成本（ingest 日內資料、選擇權鏈、另類資料、小型股 PIT 基本面）——每一筆都是 G-S 的資訊成本，付了就應重新檢查對應座位是否浮現超額報酬。
- **重測優先度**:⚪ 低 — low（作為重測目標）/ 但作為框架透鏡=高重要性常駐 — 非可測策略，每次付資訊成本時被重新援引以檢查 alpha 是否浮現

### B.5 E. 時序·均值回歸·波動 (docs/03 附錄E)

#### Lo-MacKinlay 1988 — time-series econometrics / random-walk test (trending vs mean-reverting structure)
- **作者 · 年份**:Lo & MacKinlay · 1988
- **分類**:機制族=估計工程·描述診斷(隨機漫步檢定,非α產生)。原生棲地:資產=美股 CRSP 指數與個股／頻率=週報酬／廣度=廣橫斷面(EW 指數的 VR>1 由小型股驅動)／年代=1962-1985／用途=統計檢定。本框架被測座位=日線滾動 VR 特徵(features/timeseries),用途正確但實作為簡化版。
- **Summary / 結論**:變異比(VR)檢定拒絕週報酬的隨機漫步:EW CRSP 指數 VR 隨 q 單調升破 1(q=2 的 1.30 到 q=16 的~2.0)、指數一階自相關 +30%(指數層動量,小型股驅動),但個股呈負自相關。對非同步交易與時變波動穩健。 結論:VR 是正典的無洩漏隨機漫步檢定;關鍵限定:指數層 VR>1 但單股 VR<1 ⇒ VR 依 regime／橫斷面座位而變,單一全域 VR 會誤標結構。
- **我們的洞見**:採納 VR 為 features/ 均值回歸包(Hurst/half-life/VR)的正典無洩漏工具;並內化『VR 符號依座位而變、單一全域 VR 會誤標』的限定。
- **用在哪 · 怎麼用 · 結果**:src/trading_analysis/features/timeseries.py (variance_ratio / rolling_variance_ratio, 預設 q=2);docs/03 附錄E + VALIDATES 表 line 17;docs/12 — 實作為 causal rolling feature 餵給趨勢／均值回歸辨識;從未單獨跑 TR。目前用同質性(homoskedastic)版本、固定 q=2、未報告 per-asset 符號分佈。 → **adopted-as-convention (作為特徵採納;從未作為策略跑 TR)**
- **angle_risk(座位是否切錯)**:低-中。棲地方向正確——它本就是診斷工具而非α來源,我們也用在對的地方。缺口在實作:用了會 over-reject 的同質性版本、固定 q=2、只算全域/單股卻未輸出符號分佈,而論文明確要求 heteroskedasticity-robust z*(q)、per-asset、多 q(2/4/8/16)+符號分佈。這是實作缺角,不是機制錯置。
- **reopen(重測觸發=資訊成本)**:當 VR 要從『描述性特徵』升格為『trend-vs-revert 交易 gate』時——升級為 Lo-MacKinlay 異質穩健 z*(q)、per-asset 計算、輸出符號分佈、q 參數化。無需新資料(現有日線即可),資訊成本=工程時間。
- **重測優先度**:⚪ 低 — low。目前僅描述性特徵,誤標成本尚未實現;一旦要拿 VR 當交易 gate 才升 medium。

#### Brock-Lakonishok-LeBaron 1992 — technical trading rules / 資料窺探警示的正典案例
- **作者 · 年份**:Brock, Lakonishok & LeBaron · 1992
- **分類**:機制族=α產生(技術規則:MA 關係 VMA + 區間突破 TRB)+驗證方法(bootstrap null)。原生棲地:資產=DJIA 指數／頻率=日／廣度=單指數／年代=1897-1986／用途=技術訊號可預測性。注意:掃描版影像 PDF、由既有知識摘要,確切數字需 spot-verify。
- **Summary / 結論**:DJIA 1897-1986,簡單移動平均(VMA)與區間突破(TRB)規則具預測力:買訊~12%年化 vs 賣訊為負,買日報酬變異低於賣日——與常數風險隨機漫步不一致;經 AR(1)/GARCH-M bootstrap null 顯著。 結論:MA/突破規則帶資訊——但它是資料窺探的正典警示:Sullivan-Timmermann-White 後續證明 BLB 的特定規則過不了全宇宙資料窺探校正。
- **我們的洞見**:兩件:(a) validates minervini_trend 前提(MA 關係規則帶資訊);(b) 更重要——它是反資料窺探的教科書,直接催生把 White Reality Check / Hansen SPA / DSR / PBO 加進 rigor scorecard,且 bootstrap null 應用 AR(1)/GARCH-M 而非 iid。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 263-266 + VALIDATES 表 line 13 + Theme Takeaway #1;催生 backtest/spa.py (Hansen SPA)、DSR、PBO(O1 模組);規則前提實測落在 docs/05/07(Minervini Sharpe 1.17→0.64)、TR-16(技術規則章節全關) — 作為方法論錨(反資料窺探)而非跑過的策略;其『技術規則帶資訊』前提體現在 Minervini/Vegas/ensemble 的實測(全數衰退/關閉)。 → **adopted-as-convention (資料窺探防線採納為 fabric 慣例;規則前提在我們座位實測=衰退/FAILED,但未以 BLB 原座位單獨跑 TR)**
- **angle_risk(座位是否切錯)**:中。我們從未在 BLB 原生座位(單一指數 DJIA、百年日線、VMA/TRB 精確規則)復現;而是把『技術規則帶資訊』搬到個股橫斷面(Minervini/Vegas)測,得衰退/FAILED。BLB 的正面結論本身已被 STW 全域窺探校正推翻,故我們的負結果與『校正後共識』一致——真正的殘餘風險是:掃描版摘要的確切數字(12%/yr 等)尚未 spot-verify。
- **reopen(重測觸發=資訊成本)**:(a) 若要正式引用 BLB 量化結論→需 OCR 或取得可抽取文字版做 spot-verify;(b) 若要原座位復現→需長歷史單指數日線(DJIA 1897-)。兩者皆低優先:方法論教訓已內化、正面結論已被文獻校正。
- **重測優先度**:⚪ 低 — low。方法論教訓已內化為 fabric 慣例,正面結論已被 STW 校正;僅摘要數字待 spot-verify。

#### Gatev-Goetzmann-Rouwenhorst 2006 — 統計套利 / 市場中性相對價值
- **作者 · 年份**:Gatev, Goetzmann & Rouwenhorst · 2006
- **分類**:機制族=α產生(統計套利·均值回歸)。原生棲地:資產=全市場股票配對／頻率=日線(部分日內調整)／廣度=廣橫斷面 distance-match(全 CRSP)／年代=1962-2002／成本=機構級／用途=市場中性套利。docs/19 §1 錯置=中。
- **Summary / 結論**:距離法配對(正規化價格差平方和最小配對,2σ 發散進場、收斂出場)在 1962-2002 賺~11%年化超額,超過保守交易成本、與單純反轉獲利有別,獲利載於一個未識別的共同潛在因子。 結論:~11%/yr 市場中性超額,但作者自陳 post-2002 因容量/擁擠而衰退;Do-Faff(2010/2012)證實 post-2010 淨成本後趨近 0。
- **我們的洞見**:2σ/0σ 進出=天然 triple-barrier;實測後結論=日線棲地衰退>100%,連現金都輸;共整合篩選本身有微弱訊號(勝 90% 隨機非共整合對)但絕對報酬不及格;『不相關∧不賺錢』sleeve 入組合反拖累 alpha t(2.66→1.79)。殘值=|z|>4 結構斷裂偵測可當個股異常警報。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-01-stat-arb-pairs.md;scripts/tests/tr01_stat_arb_pairs.py;docs/18 註冊表 TR-01 列;docs/19 §1 pairs 列;docs/03 附錄E line 268-271 + Theme Takeaway #3 — TR-01 完整審判:47 檔同產業對、Engle-Granger 共整合選對(訓練 2015-19)、OOS 2020-2026(1,633 日)、10bps/腿、含 20 組隨機非共整合控制。 → **FAILED (OOS +1.96%/yr < 現金 BIL +2.70%;對現金超額 −0.7%/yr,衰退>100%,與 Do-Faff 一致)**
- **angle_risk(座位是否切錯)**:中-高——本批最需注意的錯置。(1) 選對方法錯位:GGR 用 distance(正規化價格 SSD 最小)選對,我們用 Engle-Granger 共整合檢定——不同座位,且共整合更嚴格、『訓練期最共整合的對往往後來結構斷裂最猛』(Type-II,SMCI/INTC −75% MDD);(2) 宇宙錯位:GGR 是全 CRSP 廣配對,我們只配 47 檔同產業高相關名字(9/10 對 AI_semis、6 對含 SMCI),集中度風險把 sleeve 綁在單一醜聞股;(3) 日線收盤 vs GGR 部分日內。文獻(Do-Faff)證實日線棲地整體衰退,故 FAILED 方向大致可信,但我們測的是 GGR 一個窄且非原生的切片。
- **reopen(重測觸發=資訊成本)**:(a) 便宜且該先做:用 GGR 原生 distance 選對(而非共整合)+更廣宇宙(跨 ETF/ADR/全市場)以現有日線重測——資訊成本=工程;(b) 真正救活需日內資料(ORB 級)+動態對池輪換(docs/11 ④)。各為一筆 G-S 資訊成本。
- **重測優先度**:🟡 中 — medium。原座位(distance+廣宇宙)未測,且我們用了非原生的共整合選法+極窄集中宇宙=真錯置;但文獻已示日線 pairs 整體衰退,故非 high。優先做便宜的 (a) distance+廣宇宙日線重測。

#### Engle 1982 — 波動計量 / 條件異質變異(ARCH)
- **作者 · 年份**:Engle · 1982
- **分類**:機制族=風險測量·估計工程(條件變異數建模,非α產生)。原生棲地:資產=總經時間序列(UK 通膨)／頻率=不限／廣度=單序列／年代=1982／用途=條件變異數估計 + ARCH-LM 檢定。注意:掃描版影像 PDF、由既有知識摘要。
- **Summary / 結論**:提出 ARCH:條件變異數為過去平方誤差的函數,附 ARCH 效應的 LM 檢定,應用於 UK 通膨不確定性(2003 諾貝爾)。波動叢聚且可預測,即使報酬本身不可預測。 結論:報酬波動叢聚 ⇒ 任何假設同質 iid 報酬的顯著性/bootstrap 檢定皆設定錯誤;需 block/wild bootstrap 與 GARCH/AR(1) null。
- **我們的洞見**:核心教訓被採納:波動叢聚⇒拒絕 iid null⇒改用 block/wild bootstrap 與 GARCH/AR(1) null。但論文建議的 ARCH-LM 診斷本身未建入 rigor scorecard。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 273-276 + Theme Takeaway #1 flag;實踐 scripts/tests/tr05_gbm_mc.py(block bootstrap)、TR-11;ARCH-LM 未見於 src(grep 無) — 作為方法論約束(拒絕 iid null)。實踐落在 TR-05 用 stationary block bootstrap(Politis-Romano, b=21)當誠實 MC、TR-11 bagged/區塊重抽。ARCH-LM 檢定=建議未實作。 → **adopted-as-convention (波動叢聚⇒block bootstrap 教訓已採納;ARCH-LM 診斷=not-yet-implemented,GARCH 亦未建)**
- **angle_risk(座位是否切錯)**:低。我們沒有『測』ARCH 這個機制(它是計量工具非策略),而是採納其推論且用對了地方(block bootstrap)。殘餘風險僅在:未把 ARCH-LM 正式列為 scorecard 診斷、未量化我們資料的 ARCH 效應強度;加上掃描版摘要數字待 spot-verify。
- **reopen(重測觸發=資訊成本)**:若要正式報告我們宇宙的條件異質性強度、或把 heteroskedasticity-robust 標準誤自動化進 rigor→加 ARCH-LM 為 scorecard 診斷(現有日線即可,資訊成本=工程)。
- **重測優先度**:⚪ 低 — low。核心教訓已內化;ARCH-LM 僅把已知異質性顯性化,邊際價值低。

#### Bollerslev 1986 — 波動預測 / 條件σ 模型
- **作者 · 年份**:Bollerslev · 1986
- **分類**:機制族=風險測量·估計工程(前瞻條件σ 預測)。原生棲地:資產=金融時間序列／頻率=日／廣度=單序列／年代=1986／用途=波動預測(GARCH(1,1)=現代波動預測工作馬)。
- **Summary / 結論**:推廣 ARCH,讓當期條件變異數依賴過去的條件變異數(GARCH(1,1)),得到簡約的長記憶波動模型——現代波動預測的工作馬。 結論:GARCH(1,1) 預測 σ 用於『前瞻』風險遠優於滾動窗 std;部位規模應以『預測』波動(而非已實現波動)縮放。
- **我們的洞見**:認知採納(GARCH σ 優於滾動 std 用於前瞻風險、應以預測波動 size 部位),但從未實作。我們實際的波動估計仍是 trailing-window std / rvol / ATR;vol-target sizing 用已實現波動而非 GARCH。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 278-281 + Theme Takeaway #2;src 內無 garch 實作(grep 無);portfolio/sizing.py 現用已實現波動代理 — 建議 features/garch_vol(GARCH(1,1) 一步預測 σ,PIT/expanding fit)餵 portfolio/ risk-parity sizing 與 ml/ meta-label sizing——建議未建。 → **not-yet-tested (建議採納方向但從未實作、從未跑;現行以 trailing-std/rvol 代理前瞻風險)**
- **angle_risk(座位是否切錯)**:中。我們從未在任何座位測過 GARCH——既非採納也非否證,是純缺口。錯置風險=我們用 realized-vol 代理『前瞻風險』,而 GARCH 的整個賣點正是前瞻;若 vol-target/Kelly/MDD 門檻對前瞻 σ 敏感,realized 代理可能在 regime 轉折點系統性錯估(呼應 TR-05:平靜期校準外推到高波動必失真)。
- **reopen(重測觸發=資訊成本)**:當波動預測品質成為 binding(vol-target sizing 或 Kelly 部位在 regime 轉折被打臉,或要正式比較 forecast-σ vs realized-σ 的部位規模差異)→加 features/garch_vol(arch 套件, PIT fit, CPU 便宜合 <$15/mo, 現有日線即可)。純工程成本、無新資料。
- **重測優先度**:🟡 中 — medium。從未測=真缺口且便宜(現有資料+CPU 便宜);但現行 realized-vol sizing 已『如設計運作』(vol-target PARTIAL),GARCH 增量價值未證,故非 high。做一次 forecast-vs-realized σ 的 sizing 對照即可定案。

#### Hurst-Ooi-Pedersen 2017 — 時序動量 TSMOM / managed futures / 趨勢跟隨
- **作者 · 年份**:Hurst, Ooi & Pedersen · 2017
- **分類**:機制族=α產生(時序動量 TSMOM)+風險塑形(vol-target)。原生棲地:資產=**67 個市場多資產(股/債/商品/FX 期貨)**／頻率=日-月／廣度=**跨資產低相關的組合書**／年代=1880-2016／用途=10% 波動目標的趨勢書。docs/19 §1 對應 Donchian/TAA 家族(原生多市場期貨)。
- **Summary / 結論**:波動縮放的 TSMOM(等權 1/3/12 月訊號、10% 年化波動目標、67 市場)在 1880-2016 每個十年皆獲利(前~100 年純 OOS),於股熊/回撤期賺最多(TSMOM smile),過 2-and-20 費用,但訊號延遲(尤其短視窗)顯著侵蝕報酬。 結論:趨勢跟隨是真實、非資料探勘的溢酬;兩個設計教訓:(1) vol-target 部位規模(書層 10% 波動);(2) 訊號延遲顯著侵蝕報酬——我們的 1-bar lag 是誠實最小值,別再加。
- **我們的洞見**:validates 趨勢跟隨為真溢酬 + 200-SMA/HMM regime gate + 1-bar lag=誠實最小值;vol-target sizing=最高槓桿的組合改動。但我們自己的動量實測=衰退:廣市場動量 ICIR≈0、XS 動量 P(beat EW)=23% FAILED、TAA/雙動量 crisis 保險真但 Sharpe 增強假。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 283-286 + VALIDATES 表 line 13-15 + Theme Takeaway #2;實測 docs/09、TR-11、docs/13 §8;docs/19 §1 Donchian/TAA 列 — 作為趨勢引擎+regime gate 的理論背書;動量的實測散落 docs/09(廣宇宙 ICIR≈0)、TR-11(XS 動量 FAILED)、docs/13 §8(TAA PARTIAL)。TSMOM 原生形式(67 市場多資產 vol-target 書)從未建構。 → **PARTIAL/mixed (理論背書採納;我們測的動量座位=衰退/FAILED;TAA 版=PARTIAL(crisis 保險真、Sharpe 增強假);HOP 原生 67 市場 TSMOM=not-yet-tested)**
- **angle_risk(座位是否切錯)**:高——本批第二大錯置。HOP 主張是**跨 67 個低相關市場多資產(股/債/商品/FX 期貨)的時序動量+10% vol-target 組合書**,其 alpha 與 TSMOM smile(危機賺錢)本質來自跨資產分散。我們測的是**單一資產類(47-503 檔美股)的橫斷面動量**——既非時序動量、無多資產分散、無 67 市場廣度。我們的動量 FAILED 只關閉『窄同質股票 XS 動量』座位,完全不觸及 HOP 原生座位。docs/19 已明列為 Donchian/TAA 家族(單一股指座位失敗不能外推)。
- **reopen(重測觸發=資訊成本)**:取得多資產期貨資料(股指/債/商品/FX 期貨,數十個低相關市場)→建構 HOP 原生的 vol-target TSMOM 組合書,檢驗 crisis-alpha smile。這是整個新資料維度(期貨連續合約)=明確的 G-S 資訊成本。TAA 版已用 ETF proxy 部分覆蓋(docs/13 §8)但無法複製 67 市場廣度。
- **重測優先度**:🔴 高 — high。角度明顯錯(我們用單資產 XS 測、HOP 是多資產 TSMOM)且缺關鍵資料(期貨宇宙)=docs/19 明列高錯置。但需新資料維度,屬『high 優先但被資料成本 gated』——取得期貨資料前無法在正確座位測。

#### Marcenko-Pastur 1967 — 隨機矩陣理論 / 共變異矩陣的雜訊底
- **作者 · 年份**:Marčenko & Pastur · 1967
- **分類**:機制族=估計工程(共變異矩陣去雜訊,非α產生)。原生棲地:資產=不限／頻率=不限／廣度=**大 N(P/N 比為關鍵,漸近性需大 N)**／年代=1967／用途=共變異清理(RMT 雜訊底)。
- **Summary / 結論**:純雜訊樣本共變異的特徵值有封閉形式分布,支撐區間 [(1±√(P/N))²σ²];將 MP 帶疊在真實資料的特徵值譜上即可分離訊號與雜訊特徵值。 結論:MP 帶給出雜訊底:帶內特徵值=雜訊、帶上=訊號——據此可做 eigenvalue clipping(第三種共變異清理法,對比 shrinkage 與 sample)。
- **我們的洞見**:LW shrinkage(全域強制)+ TR-03 PCA 因子共變異是同一去雜訊問題的解;MP 視角預測 47/610 宇宙除少數(TR-03 量到 PC1=41.8% 一個大 beta)外多落雜訊帶內。但從未畫過我們宇宙的特徵值譜 vs MP 帶、也沒測過 eigenvalue clipping。
- **用在哪 · 怎麼用 · 結果**:docs/20 §2(理論再審思,含 TR-03b 佇列行動);概念上等同 LW shrinkage 全域 + TR-03 PCA(docs/18 TR-03 列、scripts)。注意:docs/03 VALIDATES 表 line 22 的『MP』是 McLean-Pontiff,非本篇。 — 作為為何做共變異 shrinkage 的理論底(採納同族解 LW/PCA);MP 特有的譜圖+clipping 診斷=佇列 TR-03b 未跑。 → **adopted-as-convention (經 LW shrinkage + TR-03 PCA 採納同族解) + queued (TR-03b:MP 譜圖 vs 帶 + eigenvalue clipping 對照,未跑)**
- **angle_risk(座位是否切錯)**:低。棲地方向正確——共變異估計就是它的原生座位,我們也確實在做共變異清理(LW/PCA)。唯一缺口:採納了『族』(shrinkage)卻沒跑 MP 的『特定診斷』(譜圖分離訊號/雜訊 + clipping 對照)。是診斷完整度缺口,非機制錯置。附註:我們宇宙 N 小(47-610),MP 的 P/N 漸近性在小 N 下較弱。
- **reopen(重測觸發=資訊成本)**:TR-03b:畫 47/610 宇宙樣本共變異特徵值譜 vs MP 帶(幾個真訊號特徵值?預期 3-5),把 MP-clipping 加入 TR-03 競技場(vs LW vs PCA vs sample)。現有日線即可,純工程成本,已在佇列。
- **重測優先度**:🟡 中低 — low-medium。已在正確棲地用同族方法(LW/PCA 皆『如設計運作』);MP 特定診斷是錦上添花且便宜、已佇列;預期 clipping≈LW(同族),增量價值可能小,故不急。

### B.6 F. 複雜度·近期 (docs/20)

#### KMZ 2024 (Virtue of Complexity) — 資產定價 / 單資產市場擇時 (high-dimensional return prediction, ML)
- **作者 · 年份**:Kelly, Malamud & Zhou · 2024
- **分類**:α 產生類 — 機制族=單資產市場擇時 (RFF + ridge(less) 超參數化高維回歸)。原生棲地:資產=美股大盤指數;頻率=月;廣度=1 (單資產,非橫斷面);年代=1926-2020 (95 年,含多次衰退);用途=return-timing。docs/19 §1 標記錯置風險=中-高。
- **Summary / 結論**:在 P>T 的超參數化 ridgeless 回歸下,單資產擇時的 OOS 期望表現隨特徵數 P 嚴格遞增,最適 shrinkage 再增益。15 個 Goyal-Welch 總經預測子經 Rahimi-Recht 隨機傅立葉特徵展開到 P=12,000、T=12 月滾動窗,1926-2020 擇時 Sharpe 增益約 0.47 (t≈3);R² 大幅為負但被論文論證為無經濟意義。 結論:複雜度(更多參數)在低訊噪的金融擇時裡是美德而非詛咒:負 R² 與高 Sharpe 並存,倉位自發學會近 long-only 並在 15 次衰退前撤出 14 次。
- **我們的洞見**:「keep it simple」在本框架應是實證結論而非教條;我們的 ML FAILED (TR-08/11) 是在 47 檔橫斷面樹模型的座位得到,從未在 KMZ 的座位 (單資產 + RFF + ridge + T=12 滾動) 上測過,必須實測而非援引。
- **用在哪 · 怎麼用 · 結果**:TR-17 (docs/tests/TR-17-virtue-of-complexity.md);docs/20 §1;docs/18 註冊表 TR-17 列;docs/19 §1 α 產生表 KMZ 列 — 在我們的資料上復現機制形狀:SPY 1993-2026 (~389 OOS 月) + QQQ,15 個可建構的價格/利率預測子,RFF + kernel-form ridge,T=12 滾動,P 從 2 掃到 12,000 畫 VoC 曲線;加 fabric 誠實層 (Nagel 控制 + 淨成本 + 截倉 + n_eff 註記)。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:中-高。配方對、棲地錯:我們用了正確的 RFF+ridge+T=12 機制,但切入的是 33 年 vs 論文 95 年、純價格/利率訊號 vs Goyal-Welch 總經預測子、有成本+截倉 vs 無成本+無限倉。TR-17 承認這是「機制形狀」復現而非 alpha 宣稱 (n_eff<3000)。VoC 乾淨階梯沒出現 (SPY 曲線嘈雜非單調、QQQ 甚至 P=12 最佳),且被 1/σ² 波動管理控制決定性支配。結論=棲地差異,非機制證偽——KMZ 定理未被推翻。
- **reopen(重測觸發=資訊成本)**:Ingest 公開的 Goyal-Welch 月度總經預測子資料集 (1926-present),在 95 年長樣本 × 15 個總經序列的原生棲地上完整復現並重跑 TR-17 腳本。資訊成本=取得+對齊 GW 資料集 (公開、成本低)。
- **重測優先度**:🟡 中 — medium — 屬「配方對但缺關鍵資料 (長歷史+總經預測子)」,GW 資料集公開使成本低;但 TR-17 已在可及座位判 PARTIAL 且 Nagel 控制決定性獲勝,原生棲地重測的邊際資訊有限。

#### Rahimi-Recht 2007 (Random Fourier Features) — 機器學習 / 核方法近似 (kernel approximation)
- **作者 · 年份**:Rahimi & Recht · 2007
- **分類**:估計工程類 (工具組件,非交易機制) — 機制族=隨機特徵映射逼近 shift-invariant kernel。原生棲地=通用監督式 ML,不綁定任何資產/頻率/廣度;在本專案僅作為 KMZ 高維特徵生成器的數值組件。
- **Summary / 結論**:以隨機取樣的正弦/餘弦特徵逼近 shift-invariant (如 RBF) kernel,把 kernel 回歸轉成 P 個隨機特徵上的線性回歸;P 越大逼近越準,大幅降低算力。 結論:可用有限 P 個隨機傅立葉特徵近似無限維 kernel,使高維非線性回歸在計算上可行——KMZ 正是靠這個把 15 個預測子展開到 P=12,000。
- **我們的洞見**:採納為 TR-17 的實作組件:RFF 生成高維特徵,配合 kernel-form ridge (T=12 使 12,000 特徵的解只需 12×12 線性系統);它不是被測的 alpha 機制,而是復現 KMZ 的必要工具。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 F0 + 實作 (RFF 特徵生成、kernel 形式 ridge);docs/19 §1 KMZ 列括號註記「RFF+ridge」 — TR-17 特徵生成層:γ=1、seed=3、特徵權重按 P 固定、訊號視窗內標準化,登記為 18 變體試驗的基礎映射。 → **adopted-as-convention**
- **angle_risk(座位是否切錯)**:低 / 不適用。它是數值方法組件,沒有交易「棲地」,我們未把它當 alpha 測,故無錯置風險。唯一間接風險:若 RFF 實作 (特徵權重/標準化) 有 bug 會污染 TR-17 結論——但 seed/γ/特徵權重已固定並登記。
- **reopen(重測觸發=資訊成本)**:僅在 TR-17 重跑 (見 KMZ 條) 或懷疑 RFF 數值正確性時才回看;無獨立重測意義。
- **重測優先度**:⚪ 低 — low — 工具而非機制,沒有 alpha 宣稱要平反;只有 KMZ 重測時才會連帶用到。

#### Moreira-Muir 2017 (Volatility-Managed Portfolios) — 資產定價 / 因子擇時 (volatility timing)
- **作者 · 年份**:Moreira & Muir · 2017
- **分類**:風險塑形·配置類 — 機制族=波動管理 (以 1/σ² 逆向縮放曝險)。原生棲地:資產=股市因子組合 (市場/動量/價值等);頻率=月;廣度=不限;年代=戰後美股;用途=提升因子 Sharpe。在本專案作為擇時複雜度的對照控制 (Nagel 批評的化身);與 docs/19 §3 vol-target 列同族。
- **Summary / 結論**:按上月已實現變異數的倒數 (1/σ²) 縮放因子曝險,可在不擇報酬方向下顯著提升多數股市因子的 Sharpe 與 alpha:波動可預測但報酬不可預測,故低波期加倉、高波期減倉即賺。 結論:一個簡單的波動旋鈕 (1/σ²) 就能大幅提升風險調整報酬——正是 Nagel 用來質疑 KMZ「複雜度增益其實是偽裝的波動擇時」的基準。
- **我們的洞見**:作為 TR-17 的決定性控制:任何 KMZ 複雜度變體必須勝過 1/σ² 波動管理且對其 alpha-t≥2 才算真增益。結果 1/σ² 控制 (SPY +0.67 / QQQ +0.73) 決定性支配全部 18 個複雜度變體 → 複雜度在本座位=波動擇時的複雜包裝。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 R2 + §5 (Moreira-Muir 1/σ² = 決勝控制);docs/20 §1 (F6 v2 控制);docs/19 §3 vol-target 列;docs/13 §12 (vol-target 實測) — TR-17 §5 R2 判準的基準控制;registry 內另有 vol-target 家族 (strategy_zoo/highvol_ruleset) 獨立測過,判 PARTIAL:降 MDD 真、alpha 假、高波動宇宙反傷。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:中。用在正確的功能座位 (風險塑形控制) 且它贏了;但有未平角度:Cederburg (TR-02b) 已警告 1/σ² 對「靜態恆定曝險」的優勢通常不穩健,TR-17 也承認波動管理控制本身未扣成本、未對靜態曝險做二階控制。故「贏 KMZ」穩,「值得當獨立策略」尚未在扣成本+靜態控制下確立。
- **reopen(重測觸發=資訊成本)**:把 1/σ² 波動管理升級為 F6 v2 正式 sleeve 時,需加:(a) 交易成本 (換手高);(b) Cederburg 靜態恆定曝險二階控制;(c) 高波動宇宙反傷檢查。觸發事件=想把 TR-17 的控制轉成獨立配置策略。資訊成本=低 (資料已在手,只是加控制)。
- **重測優先度**:🟡 中 — medium — 作為控制的角色已確立且穩健;作為獨立 alpha 的座位 (扣成本+靜態控制) 未測,但 vol-target 家族已 PARTIAL 提示 alpha 大概為假,故非高優先。

#### Nagel 2025 / Buncic 2025 (VoC critique) — 資產定價 / 方法論批評 (ML market-timing critique)
- **作者 · 年份**:Nagel · 2025
- **分類**:驗證方法類 / α 產生類的反命題 — 機制族=對 KMZ VoC 的證偽 (主張複雜度增益=波動擇時 artifact)。原生棲地=與 KMZ 相同 (單資產月頻擇時),但立場=歸因/證偽;在本專案作為 TR-17 預先承諾判準 R2 的來源。
- **Summary / 結論**:Nagel/Buncic 質疑 KMZ 的複雜度 Sharpe 增益並非來自高維非線性學習,而是被複雜模型偶然重現的波動擇時 (1/σ²) artifact;控制掉波動擇時成分後複雜度的邊際貢獻消失。KM (2025) 有回應辯護。 結論:KMZ 的增益可能是波動管理的偽裝;正確檢驗是加入 Moreira-Muir 波動管理控制,看複雜度是否還有增量 alpha。
- **我們的洞見**:直接寫進 TR-17 預先承諾判準 R2:策略須勝波動管理控制且對其 alpha-t≥2,否則判定=波動擇時 artifact。這把誠實層建進復現裡,避免我們自己重蹈 KMZ 被批評的坑。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 R2 + §6;docs/20 §1 (直接檢驗 Nagel 批評);docs/19 §1 KMZ 列 (被 1/σ² 支配) — TR-17 §0 R2 判準 + §6 判定;結果站在 Nagel/Buncic 一側 (複雜度被 1/σ² 決定性支配),但明確聲明不推翻 KMZ 定理。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:低-中。批評本身是歸因/證偽立場,我們用它當控制判準=正確用法。角度風險在於:我們只在可及的短樣本×技術訊號集上驗證了 Nagel 一側,無法在 KMZ 原生棲地 (95 年×總經) 上裁決 Nagel vs KM 的真正學術爭論——我們的 PARTIAL 不是對這場爭論的最終票。
- **reopen(重測觸發=資訊成本)**:同 KMZ 條:取得 Goyal-Welch 長歷史總經資料集後,在原生棲地上重跑,才能檢驗 Nagel 批評是否在 KMZ 自己的座位也成立 (而非只在我們的座位)。資訊成本=GW 資料集 (公開、低)。
- **重測優先度**:🟡 中 — medium — 與 KMZ 綁定;在我們的座位證據已足 (Nagel 側決定性獲勝),進一步裁決學術爭論需 GW 資料集,邊際價值中等。

#### Lou-Polk-Skouras 2019 (Overnight/Intraday) — 資產定價 / 報酬時段拆解 (return decomposition, clientele effects)
- **作者 · 年份**:Lou, Polk & Skouras · 2019
- **分類**:描述·歸因類 (診斷座位,非賺錢座位) — 機制族=隔夜 (收→開) vs 日內 (開→收) 報酬拆解。原生棲地:資產=美股大型股;頻率=日頻拆時段;廣度=廣橫斷面;年代=1993-2013;用途=歸因診斷 (溢酬住哪個時段、散戶近開盤 vs 機構近收盤的客群效應)。docs/19 §1 季節性/隔夜列。
- **Summary / 結論**:把日報酬拆成隔夜與日內兩段:大型股風險溢酬幾乎全在隔夜,動量溢酬約 +0.98%/月全在隔夜 (隔夜 Sharpe 0.77 vs 全日 0.31),低波動/價值反在日內賺;散戶近開盤、機構近收盤交易,形成時段客群效應。 結論:同一因子的報酬有強烈時段結構;動量的錢在隔夜,這改變再平衡成本假設與成交慣例的含義 (即使不拿來交易)。
- **我們的洞見**:值得做「診斷性拆解」而非交易:我們宇宙的動量/GP 溢酬住在哪個時段?若動量 book 報酬全在隔夜,月度收盤再平衡的成本與成交假設含義不同。我們只測過 QQQ 隔夜『作為策略』(毛 0.89/淨 −0.97 撞成本牆),從未做歸因拆解。
- **用在哪 · 怎麼用 · 結果**:docs/20 §7 (行動 → TR-19 佇列);docs/18 §行動總表隱含;docs/13 §4/§15 (隔夜『作為策略』=FAILED 成本牆);docs/19 §1 季節性/隔夜列 — 尚未執行;規劃為 TR-19 (佇列):47/503 檔動量 top-K book 與 GP 品質做隔夜/日內報酬拆解,預期動量偏隔夜 (LPS 複製) 但幅度衰退。 → **queued**
- **angle_risk(座位是否切錯)**:中-高。作為策略,我們在正確棲地 (SPY/QQQ 隔夜) 測過並撞成本牆=誠實負結果;但作為診斷歸因 (LPS 的原生用途),我們根本還沒切入,缺開/收盤分離資料。目前等於用錯座位 (整日報酬) 看一個時段性現象——動量歸因診斷的正確座位需要開盤價/收盤價分離。
- **reopen(重測觸發=資訊成本)**:用已有 OHLC 的 open/close 近似 (收→開 = prev-close→open、開→收 = open→close),對 47/503 檔動量 top-K book 與 GP 品質做時段拆解;若要精確再 ingest 日內資料。資訊成本=低 (OHLC 已在手,可低成本近似;精確版才需日內資料=中)。
- **重測優先度**:🔴 高 — high — 屬「診斷座位從未切入 + 資料 (open/close) 已可低成本近似」;不是為了交易 (成本牆仍立),而是為了修正動量 book 的成本/成交假設,是本批中最該優先做的小型診斷 (TR-19)。

#### Lakonishok-Lee (Insider) — 資產定價 / 另類資料因子 (insider trading signals)
- **作者 · 年份**:Lakonishok & Lee · 2001
- **分類**:α 產生類 — 機制族=內部人淨買入因子 (Form 4 open-market P/S 的橫斷面選股)。原生棲地:資產=美股廣橫斷面 (含小型股,小公司訊號最強);頻率=月/季;廣度=全市場;年代=1975-1995 (訊號廣為人知前);用途=選股 alpha。在本專案座位大致對,但廣度受限於 494 檔大中型股 + 2015-2024。
- **Summary / 結論**:內部人交易可預測報酬,尤其小公司內部人買入;內部人是逆向投資者,淨買入預示正報酬。訊號自 2001 公開後已廣為人知。 結論:內部人淨買入是方向正確的選股訊號,但屬已被廣泛知曉、易衰退的 alpha。
- **我們的洞見**:實測確認:方向對 (IC +0.011、hit 57%、與 Lakonishok-Lee 同號) 但因子弱且跨期不穩 (2016-19 約 0/負、2020-24 才轉正),過不了穩定性閘門,沒贏過 gross profitability (ICIR +0.30)。又一個 alpha decay 案例——唯一穩健的新 alpha 是基本面品質。
- **用在哪 · 怎麼用 · 結果**:docs/10 §4d (insider Form 4 因子實測);docs/13 §10 (FAILED 因子);docs/18 FAILED 表 (insider);docs/19 §1 需補列 (現以文字散見) — 接入 SEC bulk 季度 Form 4 (data/connectors/insider.py),ingest 2015-2024 共 65,503 筆 / 494 檔,建 net-purchase-ratio 因子 (trailing 6/12mo、以 filed 申報日 point-in-time snap 次交易日),過 factor_determination 閘門;value-weighted 與 count-based 結果幾乎相同 (訊號本身弱,非 outlier)。 → **FAILED**
- **angle_risk(座位是否切錯)**:中。座位大致對 (橫斷面選股、Form 4 filed PIT、open-market P/S)=棲地匹配良好;但廣度受限:只 2015-2024 × 494 檔大中型股,缺了 Lakonishok-Lee 最強的小型股 + 資訊未擴散的 1975-1995 年代。FAILED 誠實但可能低估——我們測的是訊號公開衰退後 (2001+) 的大中型股殘值,正是其最弱棲地。
- **reopen(重測觸發=資訊成本)**:擴充 insider 宇宙到小型股 PIT (Form 4 電子申報始於 ~2003,無法回補更早年代,唯一可及擴充=小型股廣度 + cluster-buy/高階主管加權等更細訊號結構)。資訊成本=取得小型股 PIT Form 4 + 小型股價格 (中)。
- **重測優先度**:🟡 中低 — low-medium — 已在大致正確的座位測過且輸 (符合『正確棲地輸=低』);但小型股廣度缺口使它非純低,若日後建小型股宇宙可順帶重測,否則 alpha decay 共識使重測價值有限。

#### de Prado AFML — 量化方法論 / 回測與 ML 工程 (financial ML methodology)
- **作者 · 年份**:López de Prado · 2018
- **分類**:驗證方法類 + 估計工程/執行類 — 機制族=金融 ML 工程慣例 (triple-barrier labeling、trend-scanning、PurgedKFold+embargo、meta-labeling、CSCV/PBO、HRP)。原生棲地=通用量化回測稽核,不綁定資產;在本專案多數採納為 convention,HRP 例外=跑過 TR-07。docs/19 §5 驗證方法類。
- **Summary / 結論**:AFML 提供一整套對抗過擬合與洩漏的金融 ML 工程慣例:triple-barrier 標記、purged K-fold + embargo 交叉驗證、meta-labeling、CSCV/PBO 過擬合機率、HRP 階層風險平價。 結論:在低訊噪的金融資料上,正確的洩漏控制 (purge+embargo)、過擬合稽核 (PBO/DSR) 與淺樹/meta-labeling,比追求模型複雜度更重要。
- **我們的洞見**:大量採納為 fabric 慣例:triple-barrier/trend-scanning 標記 (σ-band=水平障礙,直接對應 pairs 2σ/0σ 進出場)、PurgedKFold 嚴格 purge+embargo (洩漏控制)、meta-labeling 淺樹、CSCV/PBO 當過擬合閘門 (O1)。也修正一條:purge 修的是洩漏不是選擇偏誤 (PBO/DSR 才管 selection),不能把 PurgedKFold OOS 機率當過擬合保護。HRP 我們實際跑了 TR-07。
- **用在哪 · 怎麼用 · 結果**:labeling/、labeling/cv.py、ml/meta_labeling.py、O1 (DSR/PBO/SPA);docs/03 §meta-labeling 對抗審查 (E1 修正);TR-07 (HRP);docs/19 §5 驗證方法類 — labeling/ (triple-barrier, cv.py PurgedKFold)、ml/meta_labeling.py (淺樹 meta-label)、O1 DSR/PBO/SPA 模組全域用於 docs/05-17;HRP 在 TR-07 於 5 sleeves + 47 同質股座位測。 → **adopted-as-convention**
- **angle_risk(座位是否切錯)**:低。這些是驗證/工程慣例,原生棲地=回測稽核,我們就在稽核座位上用=棲地匹配,v1.2 審查確認全部在原生座位使用。兩個被點名的角度修正:E1 (meta-labeling 的 lift = filtered vs full base-rate 是 de Prado 原意,但非『勝過同覆蓋率隨機濾網』的 edge,需補 precision-at-coverage);HRP 在我們小 N/同質宇宙 (5 sleeves + 47 同質股) 對它不利,TR-07 的『不換』只在此二座位有效。
- **reopen(重測觸發=資訊成本)**:HRP:取得 50+ 檔多資產異質宇宙後重測 (docs/19 標 HRP 錯置中-高,優勢隨 N 與異質性增長)。meta-labeling lift:補 precision-at-coverage 指標 (E1 修正,低成本)。其餘慣例:除非發現洩漏或 PBO 實作 bug 否則不需重開。
- **重測優先度**:⚪ 低 — low — 慣例已在正確座位確認;唯一有座位錯置的子項是 HRP (已在 TR-07 於不利小 N 座位測過判 PARTIAL『不換』,翻案需多資產大 N 異質宇宙),但那是 HRP 一項的事,不是整套 AFML 慣例的事。

---

## Part C — >500 引用經典深讀計畫(尚未深測)

從 8 個子領域挑出 **177 篇** 引用超過 500 的經典(去重後,含 2026-07 由 >2000 放寬後新增的 500-2000 中間帶)。皆與選股/交易相關。
分波原則見 Part A §A4。引用數為 agent 估計(canonical 地位),數字僅供排序,實際引用以 Google Scholar 為準。

> **已執行(2026-07-08)**:
> - **Newey-West (1987) + Politis-Romano (1994) → TR-18**:壓測旗艦唯一的 PASSED alpha,發現 **t=3.38 是日頻假象**(Dimson lagged-beta),月頻 t=2.64/2.95 不過 HLZ,旗艦降級 PASSED-borderline;順帶把 **Dimson (1979) 薄交易 beta** 加入佇列。詳見 [TR-18](tests/TR-18-inference-robustness.md)。
> - **Fama-French 2015 五因子 → TR-20**:把上面那個邊際 alpha 對 FF5(+RMW+CMA)/FF6 重測,alpha 幾乎不動、RMW/CMA 不顯著=**真殘值 alpha,非未建模因子 beta**(旗艦不變、強化)。詳見 [TR-20](tests/TR-20-ff5-attribution.md)。**Hou-Xue-Zhang q-factor**(ROE+I/A,需 EDGAR 自建)仍佇列為獨立交叉驗證。
> - **Kritzman-Li-Page-Rigobon 2010/2011 吸收比率 → TR-21**(創作者 reel 線索→主要來源→一天內判定):465 檔 S&P 座位上 **FAILED**——AR 不領先大跌(前月百分位中位 44,p=0.75)、與平均相關 +0.97 幾乎同物、閘門輸靜態與隨機安慰劑;棲地但書=原生為產業組合×含 GFC 內生危機。詳見 [TR-21](tests/TR-21-absorption-ratio.md) 與 [docs/23](23-creator-mechanisms.md)。
> - **新增 wave-1/2 深讀**:**Bun-Bouchaud-Potters 2017《Cleaning large correlation matrices》**(Physics Reports,~900 引用;RMT 清理 canonical 綜述,含特徵向量端的極限)——支撐 TR-03b 擴充(特徵值+特徵向量雙端清理競技場);實作參照 Bongiorno-Challet k-BAHC(<500 引用,掛此條之下)。

### C.0 候選索引(依波次、引用數排序)

| 波 | 論文 | 作者 | 年份 | ~引用 | 子領域 | 可用免費資料重建? |
|---|---|---|---|---|---|---|
| ① | engle-granger-1987-cointegration | Engle & Granger | 1987 | 40000 | Econometrics & metho | yes — 只需日線 OHLCV 價格對;無新資料;算力小;注意共整合關係可能不 |
| ① | newey-west-1987 | Newey & West | 1987 | 30000 | Econometrics & metho | yes — 純標準誤重算，只需既有免費日/月報酬序列，零新資料、point-in |
| ① | debondt_thaler_1985_overreaction | De Bondt & Thaler | 1985 | 9500 | Long-term reversal / | yes(有但書)。日線→月頻、36月形成/36月持有完全可算;point-in- |
| ① | lsv-1994-contrarian | Lakonishok, Shleifer & | 1994 | 9000 | value | yes — E/P、B/M、C/P(現金流/價)、sales growth 全部 |
| ① | daniel_hirshleifer_subrahmanyam_1998 | Daniel, Hirshleifer &  | 1998 | 7000 | Overconfidence + sel | YES/PARTIAL. Momentum (2-12m) + LT-rever |
| ① | pastor-stambaugh2003-liqrisk | Pastor & Stambaugh | 2003 | 6500 | Market microstructur | YES(核心可重建)。每股 γ:回歸 r_{i,t+1} = θ + φ·r_{ |
| ① | ang-hodrick-xing-zhang-2006-ivol | Ang, Hodrick, Xing & Z | 2006 | 6000 | Cross-sectional fact | yes — 只需免費日線報酬 + Ken French 日頻 FF3 因子(已接 |
| ① | ff88_divyield | Fama & French | 1988 | 5000 | Return predictabilit | yes — Shiller 免費長歷史月度資料(S&P 價格+股利,1871-) |
| ① | jegadeesh_titman_2001_evaluation | Jegadeesh & Titman | 2001 | 5000 | Momentum: out-of-sam | yes, fully. OOS momentum and post-format |
| ① | welch-goyal-2008 | Welch & Goyal | 2008 | 4500 | Econometrics & metho | yes — 論文附公開月度資料集(1926-present),與 TR-17/K |
| ① | grs-1989 | Gibbons, Ross & Shanke | 1989 | 4200 | Econometrics & metho | yes — 只需 sleeve/測試組合月報酬 + Ken French 因子（ |
| ① | clark-west-2007 | Clark & West | 2007 | 4000 | Econometrics & metho | yes — 只需長指數歷史(SPY/QQQ)+免費預測子(估值比/動量/波動)， |
| ① | frazzini-pedersen-2014-bab | Frazzini & Pedersen | 2014 | 3500 | low-risk anomaly / f | yes — beta 用日線 OHLCV 估(FP 的 correlation× |
| ① | cooper-gulen-schill-2008-asset-growth | Cooper, Gulen & Schill | 2008 | 3200 | investment | yes — 總資產 YoY from EDGAR，PIT 對齊申報日。 |
| ① | harvey-siddique-2000-coskewness | Harvey & Siddique | 2000 | 3200 | Derivatives, volatil | yes (fully). Coskewness = standardized E |
| ① | politis-romano-1994-stationary-bootstrap | Politis & Romano | 1994 | 3000 | Econometrics & metho | yes — 純重抽樣工具;套既有 F5/報酬序列;無新資料;需調 mean bl |
| ① | shanken-1992 | Shanken | 1992 | 2900 | Econometrics & metho | yes — 純標準誤重算，用 TR-06 既有月報酬+β 估計即可，零新資料；p |
| ① | bali-cakici-whitelaw-2011-max | Bali, Cakici & Whitela | 2011 | 2900 | Lottery demand / cra | YES, fully. MAX(k) = mean of the k large |
| ① | stambaugh99_bias | Stambaugh | 1999 | 2800 | Return predictabilit | yes — 純方法論,只需既有報酬+預測子序列;實作 Stambaugh/Ken |
| ① | bernard-thomas-1989-pead | Bernard & Thomas | 1989 | 2800 | PEAD | yes — EDGAR 提供季 EPS 與精確申報日(PIT 天然對齊，申報日= |
| ① | grinblatt_han_2005 | Grinblatt & Han | 2005 | 2600 | Disposition effect - | YES — the most cleanly buildable in this |
| ① | mclean_pontiff_2016_academic_research_destroys | McLean & Pontiff | 2016 | 2600 | Modern asset pricing | yes (methodologically) — we already have |
| ① | ct08_restrictions | Campbell & Thompson | 2008 | 2400 | Return predictabilit | yes — 沿用 TR-17 已有的 GW 預測子(公開資料)+ Shiller |
| ① | lee_swaminathan_2000_price_momentum_volume | Lee & Swaminathan | 2000 | 2300 | Momentum: volume-con | yes, fully. Both price momentum and trad |
| ① | george_hwang_2004_52wk | George & Hwang | 2004 | 2200 | 52-week-high momentu | yes。訊號=每檔 close / trailing-252日最高價,純免費日線 |
| ① | lns-2010-skeptical | Lewellen, Nagel & Shan | 2010 | 2200 | Econometrics & metho | yes — 方法論協定(GLS-R²、CI、測試資產多樣化);套既有橫斷面檢定; |
| ① | cooper_gutierrez_hameed_2004_market_states | Cooper, Gutierrez & Ha | 2004 | 2100 | Momentum: market-sta | yes, fully. Market state = sign of lagge |
| ① | lesmond-ogden-trzcinka1999-lot-zeroreturn | Lesmond, Ogden & Trzci | 1999 | 2000 | Market microstructur | yes (fully). Proportion of zero-return d |
| ① | nagel_2005_short_sales_institutional | Nagel | 2005 | 1900 | Behavioral finance & | YES/PARTIAL. Institutional ownership fro |
| ① | ang_bekaert_2007_predictability_there | Ang & Bekaert | 2007 | 1800 | Return predictabilit | yes(美國腿)— 指數長歷史 + D/P(Shiller)+ 3M T-bil |
| ① | fu-2009-egarch-ivol | Fu | 2009 | 1800 | Derivatives, volatil | yes. EGARCH(1,1) conditional idio-vol on |
| ① | pesaran-timmermann-1992 | Pesaran & Timmermann | 1992 | 1700 | Econometrics & metho | yes — 只需擇時訊號 + 指數報酬方向;無新資料;算力≈0。 |
| ① | stambaugh_yu_yuan_2015_arbitrage_asymmetry | Stambaugh, Yu & Yuan | 2015 | 1600 | Behavioral finance & | YES/PARTIAL. IVOL from OHLCV+FF3 residua |
| ① | dellavigna_pollet_2009_friday_inattention | DellaVigna & Pollet | 2009 | 1500 | Behavioral finance & | YES, fully (best-in-class fit). Earnings |
| ① | frazzini_2006_disposition_underreaction | Frazzini | 2006 | 1500 | Behavioral finance & | YES/PARTIAL. Frazzini's original referen |
| ① | campbell_yogo_2006_efficient_tests | Campbell & Yogo | 2006 | 1500 | Return predictabilit | yes — 純方法論,只需既有指數報酬+持續預測子序列。PIT 佳。成本 $0( |
| ① | datar-naik-radcliffe1998-turnover | Datar, Naik & Radcliff | 1998 | 1500 | Market microstructur | yes. Turnover = daily $ or share volume  |
| ① | hou-moskowitz2005-pricedelay | Hou & Moskowitz | 2005 | 1500 | Market microstructur | yes (fully). Weekly returns from daily O |
| ① | hxz-2020-replicating-anomalies | Hou, Xue & Zhang | 2020 | 1400 | composite/methodolog | yes — 複製協定(NYSE breakpoint、VW、去微型股)可直接套用 |
| ① | kelly-jiang-2014-tail-risk | Kelly & Jiang | 2014 | 1400 | Derivatives, volatil | yes. Monthly common tail index = Hill es |
| ① | baker-bradley-wurgler-2011-lowvol-limits | Baker, Bradley & Wurgl | 2011 | 1300 | low-vol | yes — 低波/低 beta 組合由 OHLCV 建。 |
| ① | barroso_santaclara_2015_momentum_moments | Barroso & Santa-Clara | 2015 | 1300 | Momentum: crashes /  | yes, fully. WML factor buildable from fr |
| ① | hirshleifer_lim_teoh_2009_distraction | Hirshleifer, Lim & Teo | 2009 | 1300 | Behavioral finance & | YES, fully. Same-day announcement count  |
| ① | brandt-santaclara-valkanov-2009-ppp | Brandt, Santa-Clara &  | 2009 | 1300 | characteristics-mana | yes — size/B-M/動量特徵皆日線+EDGAR 可得;效用最大化係數估 |
| ① | neely_rapach_tu_zhou_2014_technical | Neely, Rapach, Tu & Zh | 2014 | 1200 | Return predictabilit | yes — 技術指標全由指數 OHLCV(含量能)建;總經預測子用 Goyal  |
| ① | ledoit-wolf-2008-sharpe | Ledoit & Wolf | 2008 | 1200 | Econometrics & metho | yes — 純檢定,套既有策略/基準日報酬;無新資料;需自助抽樣(小算力)。 |
| ① | boyer-mitton-vorkink-2010-expected-idio-skewness | Boyer, Mitton & Vorkin | 2010 | 1200 | Derivatives, volatil | yes/partial. Realized idio-skewness = sk |
| ① | lewellen_2004_financial_ratios | Lewellen | 2004 | 1100 | Return predictabilit | yes — 指數長歷史(Shiller 免費 1871-)提供 D/P、E/P; |
| ① | ali_hwang_trombley_2003_arbitrage_risk_bm | Ali, Hwang & Trombley | 2003 | 1000 | Behavioral finance & | YES, fully. B/M from EDGAR book equity + |
| ① | pontiff-woodgate-2008-share-issuance | Pontiff & Woodgate | 2008 | 950 | net-issuance | yes — split-adjusted 流通股數 by EDGAR(封面/財報 |
| ① | novymarx_2012_intermediate_momentum | Novy-Marx | 2012 | 950 | Momentum: intermedia | yes, fully. Only needs price history to  |
| ① | nagel2012-evaporating-liquidity | Nagel | 2012 | 900 | Market microstructur | yes. Daily 5-day contrarian portfolios f |
| ① | ferreira_santaclara_2011_sum_of_parts | Ferreira & Santa-Clara | 2011 | 850 | Return predictabilit | yes — Shiller 免費資料含指數價格、股利、盈餘,可建三分量。PIT: |
| ① | da_gurun_warachka_2014_frog_in_pan | Da, Gurun & Warachka | 2014 | 800 | Momentum: informatio | yes, fully. Information discreteness = s |
| ① | bgln-2015-deflating-profitability | Ball, Gerakos, Linnain | 2015 | 750 | quality/profitabilit | yes — gross / operating / net 多種 profita |
| ① | israel_moskowitz_2013_shorting_size_time | Israel & Moskowitz | 2013 | 750 | Momentum / value / s | yes, fully. Long-only and long-short leg |
| ① | asness-frazzini-2013-devil-hml | Asness & Frazzini | 2013 | 700 | value | yes — 需月更價格 + 落後帳面權益(EDGAR)，皆免費。 |
| ① | heston_sadka_2008_seasonality | Heston & Sadka | 2008 | 700 | Seasonality in the c | yes, fully. Signal = average historical  |
| ① | faber_2007_tactical_asset_allocation | Faber | 2007 | 700 | Return predictabilit | yes — 只需指數/ETF 月末收盤與 200 日 SMA。PIT 完美。成本 |
| ① | blitz_huij_martens_2011_residual_momentum | Blitz, Huij & Martens | 2011 | 650 | Momentum: residual ( | yes, fully. Needs FF3 factors (free from |
| ② | hansen-gmm-1982 | Hansen | 1982 | 27000 | Econometrics & metho | partial→yes — 檢定本身只需免費因子+測試組合月報酬，statsmo |
| ② | diebold-mariano-1995 | Diebold & Mariano | 1995 | 15000 | Econometrics & metho | yes — 只需既有 OOS 預測序列(波動/報酬)+免費報酬；DM 統計量易實 |
| ② | shleifer_vishny_1997 | Shleifer & Vishny | 1997 | 9000 | Limits-to-arbitrage  | PARTIAL (indirect). Not a signal itself. |
| ② | baker_wurgler_2006 | Baker & Wurgler | 2006 | 8000 | Investor sentiment ( | PARTIAL/YES. Characteristics (size, age, |
| ② | amihud-mendelson1986-spread | Amihud & Mendelson | 1986 | 7000 | Market microstructur | PARTIAL。原文用『報價』價差,我們沒有(免費日線無 bid/ask)。只能 |
| ② | banz-1981-size | Banz | 1981 | 6500 | size | partial — EDGAR 基本面齊全但價格宇宙目前限大型股；需先 inge |
| ② | hong_stein_1999 | Hong & Stein | 1999 | 6500 | Gradual information  | PARTIAL. Momentum from price. Diffusion- |
| ② | roll1984-effspread | Roll | 1984 | 4800 | Market microstructur | YES,有 caveat。只需免費日線收盤變動。Point-in-time OK |
| ② | acharya-pedersen2005-lcapm | Acharya & Pedersen | 2005 | 4500 | Market microstructur | YES(可重建,較費工)。全部 4 個 beta 都由 Amihud 正規化 i |
| ② | basu-1977-ep | Basu | 1977 | 4500 | value | yes — E/P = TTM 盈餘(EDGAR)/市值，PIT 對齊申報日；全 |
| ② | cochrane11_discount | Cochrane | 2011 | 4200 | Return predictabilit | yes(就其可檢驗核心)— 用 Shiller 免費資料跑『D/P → 未來股利 |
| ② | ff89_business | Fama & French | 1989 | 3800 | Return predictabilit | yes — 期限利差(10Y-3M)、違約利差(Moody's Baa-Aaa) |
| ② | hou-xue-zhang-2015-qfactor | Hou, Xue & Zhang | 2015 | 3500 | Cross-sectional fact | partial→yes — I/A=年度總資產成長、ROE=季度淨利/權益,全在 |
| ② | ikenberry-lakonishok-vermaelen-1995-buybacks | Ikenberry, Lakonishok  | 1995 | 3500 | net-issuance | partial — 回購宣告日需事件資料(no)；但可用 EDGAR 流通股數『 |
| ② | jegadeesh_1990_predictable | Jegadeesh | 1990 | 3300 | Short-term reversal | partial。訊號(月頻排名)完全可用免費日線;但 1月短期反轉惡名昭彰地被  |
| ② | chan_jegadeesh_lakonishok_1996_momentum | Chan, Jegadeesh & Lako | 1996 | 3200 | Price + earnings mom | partial。價格動量 leg=yes(免費日線)。盈餘動量 leg:SUE  |
| ② | da_engelberg_gao_2011_search_attention | Da, Engelberg & Gao | 2011 | 3200 | Behavioral finance & | YES/PARTIAL. Google Trends SVI is free ( |
| ② | hong_lim_stein_2000_bad_news_slow | Hong, Lim & Stein | 2000 | 3000 | Momentum: informatio | partial. Size is free (price x shares);  |
| ② | daniel-titman-1997-characteristics-vs-covariances | Daniel & Titman | 1997 | 2900 | Cross-sectional fact | partial — 需個股報酬(有)+ FF 因子(有)+ 特徵(B/M 由 E |
| ② | moskowitz_grinblatt_1999_industry | Moskowitz & Grinblatt | 1999 | 2800 | Industry momentum | partial-yes。報酬=免費日線。產業分類:EDGAR filer met |
| ② | fama_french_2008_dissecting_anomalies | Fama & French | 2008 | 2600 | Fundamentals / cross | partial — needs EDGAR PIT fundamentals ( |
| ② | btz09_vrp | Bollerslev, Tauchen &  | 2009 | 2600 | Return predictabilit | partial→大致 yes — VIX(CBOE 免費,1990-;VXO 至 |
| ② | richardson-sloan-soliman-tuna-2005 | Richardson, Sloan, Sol | 2005 | 2600 | accruals anomaly (re | yes — 廣義應計需 EDGAR 完整資產負債表(營運/金融資產負債分類)，工 |
| ② | lo_mamaysky_wang_2000_foundations_ta | Lo, Mamaysky & Wang | 2000 | 2600 | Return predictabilit | yes — 核回歸型態辨識與條件分布檢定全由免費日線 OHLCV 實作。PIT  |
| ② | stambaugh_yu_yuan_2012 | Stambaugh, Yu & Yuan | 2012 | 2400 | Investor sentiment x | PARTIAL/YES. Anomaly L/S from EDGAR + pr |
| ② | daniel_moskowitz_2016_crashes | Daniel & Moskowitz | 2016 | 2300 | Momentum crashes / r | yes。WML 因子、崩盤事件描述(2009 動量崩盤)、動態加權都可在 503 |
| ② | cs98_cape | Campbell & Shiller | 1998 | 2300 | Return predictabilit | yes — Shiller 免費資料直接含 CAPE(1881-),traili |
| ② | rsz10_combination | Rapach, Strauss & Zhou | 2010 | 2300 | Return predictabilit | yes — 完全複用 TR-17 既有 GW 預測子(公開/免費),只加預測值簡 |
| ② | titman-wei-xie-2004-capex | Titman, Wei & Xie | 2004 | 2300 | investment | yes — capex/資產 by EDGAR 現金流量表，PIT。 |
| ② | lo_mackinlay_1990_contrarian_profits | Lo & MacKinlay | 1990 | 2300 | Reversal: contrarian | yes, fully. Own- and cross-autocovarianc |
| ② | kraus-litzenberger-1976-skewness-preference | Kraus & Litzenberger | 1976 | 2000 | Derivatives, volatil | yes. Identical construction to Harvey-Si |
| ② | goyenko-holden-trzcinka2009-proxyvalidation | Goyenko, Holden & Trzc | 2009 | 1900 | Market microstructur | partial. All the daily proxies are build |
| ② | lehmann_1990_fads_martingales | Lehmann | 1990 | 1800 | Reversal: short-term | yes, fully. Weekly returns from free dai |
| ② | brennan-chordia-subrahmanyam1998-dollarvolume | Brennan, Chordia & Sub | 1998 | 1800 | Market microstructur | yes. Dollar volume from OHLCV; FF/Carhar |
| ② | zhang_2006_information_uncertainty | Zhang | 2006 | 1700 | Behavioral finance & | PARTIAL. Free uncertainty proxies: firm  |
| ② | bsw-2010-fdr-alpha | Barras, Scaillet & Wer | 2010 | 1700 | Econometrics & metho | yes — 套既有 trial-registry 的 t 統計量集合;無新資料; |
| ② | cochrane_2008_dog_did_not_bark | Cochrane | 2008 | 1600 | Return predictabilit | yes — Shiller 免費長歷史含價格與股利,可建 D/P 與股利成長並跑 |
| ② | lev-thiagarajan-1993-fundamental-signals | Lev & Thiagarajan | 1993 | 1600 | fundamentals / signa | yes — 12 訊號幾乎全部 EDGAR 可算(存貨、應收、毛利、SG&A、c |
| ② | grundy_martin_2001_risks_rewards_momentum | Grundy & Martin | 2001 | 1500 | Momentum: risk decom | yes, fully. Needs FF factors (free, Ken  |
| ② | fairfield-whisenant-yohn-2003 | Fairfield, Whisenant & | 2003 | 1500 | accruals / investmen | yes — 淨營運資產成長全 EDGAR；PIT 可行；成本≈$0。 |
| ② | goyal-santaclara-2003-idio-risk-matters | Goyal & Santa-Clara | 2003 | 1400 | Derivatives, volatil | yes. Average stock variance = mean over  |
| ② | livnat-mendenhall-2006-sue | Livnat & Mendenhall | 2006 | 1400 | PEAD (measurement) | partial — 時序 SUE 分支 yes(EDGAR 全可)；分析師 SU |
| ② | chordia-subrahmanyam-anshuman2001-tradingactivity | Chordia, Subrahmanyam  | 2001 | 1300 | Market microstructur | yes. Dollar volume & turnover time serie |
| ② | sadka2006-liquidityrisk-momentum-pead | Sadka | 2006 | 1300 | Market microstructur | partial. Sadka's exact permanent/transit |
| ② | jobson-korkie-1981 | Jobson & Korkie | 1981 | 1300 | Econometrics & metho | yes — 閉式公式,套既有報酬;無新資料;算力≈0。 |
| ② | abarbanell-bushee-1998 | Abarbanell & Bushee | 1998 | 1300 | fundamentals / trada | yes — 訊號全 EDGAR；『後續公告日兌現』檢定需 EDGAR 申報日(本 |
| ② | lesmond_schill_zhou_2004_illusory_momentum | Lesmond, Schill & Zhou | 2004 | 1200 | Momentum: trading co | partial. Momentum legs from free daily O |
| ② | dittmar-2002-cokurtosis-pricing-kernel | Dittmar | 2002 | 1200 | Derivatives, volatil | yes. Cokurtosis = standardized E[ε_i · ε |
| ② | asness-frazzini-pedersen-2019-qmj | Asness, Frazzini & Ped | 2019 | 1200 | quality factor / fun | partial — 獲利/成長/安全支柱多數 EDGAR 可算;派息與部分安全指 |
| ② | hirshleifer-hou-teoh-zhang-2004-noa | Hirshleifer, Hou, Teoh | 2004 | 1100 | accruals | yes — NOA(營業資產−營業負債) by EDGAR。 |
| ② | stambaugh-yuan-2017-mispricing-factors | Stambaugh & Yuan | 2017 | 1100 | composite/methodolog | yes(大部分)— 11 個成分異常多由 EDGAR+OHLCV 建；聚合方法可 |
| ② | pontiff_2006_costly_arbitrage | Pontiff | 2006 | 1100 | Behavioral finance & | PARTIAL (framing paper, not a standalone |
| ② | kozak-nagel-santosh-2020-shrinking | Kozak, Nagel & Santosh | 2020 | 1100 | SDF / shrinkage ML a | partial — 方法(L2 收縮於 characteristic-manag |
| ② | kelly-pruitt-su-2019-ipca | Kelly, Pruitt & Su | 2019 | 1100 | IPCA / conditional f | partial — IPCA 演算法(交替最小平方)可自實作;但穩健估計需夠多特 |
| ② | mashruwala_rajgopal_shevlin_2006_accrual_arbitrage | Mashruwala, Rajgopal & | 2006 | 1000 | Behavioral finance & | YES/PARTIAL. Total accruals from EDGAR ( |
| ② | fss-2003-spurious | Ferson, Sarkissian & S | 2003 | 1000 | Econometrics & metho | yes — 模擬持續預測子 + 我們指數歷史;純方法/模擬;算力小。 |
| ② | feng-giglio-xiu-2020-taming | Feng, Giglio & Xiu | 2020 | 1000 | factor selection / S | yes — 只需一組因子報酬時序(可自建)跑 double-selection  |
| ② | daniel-titman-2006-intangible | Daniel & Titman | 2006 | 950 | net-issuance | partial/yes — 需 5 年報酬 + 帳面成長分解與複合發行，皆免費但 |
| ② | gervais_kaniel_mingelgrin_2001_high_volume | Gervais, Kaniel & Ming | 2001 | 950 | Momentum-adjacent: v | yes, fully. Abnormal-volume classificati |
| ② | mohanram-2005-gscore | Mohanram | 2005 | 950 | fundamentals / G-sco | partial — 多數訊號(ROA、現金流、盈餘變異)EDGAR yes；R& |
| ② | blitz-vanvliet-2007-vol-effect | Blitz & van Vliet | 2007 | 900 | low-vol | yes(美股部分)— vol-sorted deciles from OHLCV |
| ② | green-hand-zhang-2017-characteristics | Green, Hand & Zhang | 2017 | 900 | composite/methodolog | partial — 多數會計/量價特徵(EDGAR+OHLCV)可建，少數需 I |
| ② | korajczyk_sadka_2004_momentum_trading_costs | Korajczyk & Sadka | 2004 | 850 | Momentum: trading co | partial. Momentum legs from free daily O |
| ② | hou_2007_industry_information_diffusion | Hou | 2007 | 800 | Momentum: industry l | partial/yes. Returns from free daily OHL |
| ② | brw-2008-longhorizon | Boudoukh, Richardson & | 2008 | 800 | Econometrics & metho | yes — 指數長歷史即可複製重疊迴歸;純方法;算力小。 |
| ② | freyberger-neuhierl-weber-2020 | Freyberger, Neuhierl & | 2020 | 800 | characteristic selec | partial — 方法可實作;但穩健的變數選擇需夠廣宇宙×62 特徵，小宇宙結 |
| ② | bouman_jacobsen_2002_halloween | Bouman & Jacobsen | 2002 | 750 | Return predictabilit | yes — 只需指數月報酬。PIT 完美。成本 $0。 |
| ② | krs-2013-twopass | Kan, Robotti & Shanken | 2013 | 700 | Econometrics & metho | yes — 套既有因子/投組月報酬;無新資料;中等算力。 |
| ② | afimp-2018-size-junk | Asness, Frazzini, Isra | 2018 | 650 | size | partial — quality 腿(EDGAR)可建，但 size 腿需小盤 |
| ② | pettenuzzo_timmermann_valkanov_2014_constraints | Pettenuzzo, Timmermann | 2014 | 650 | Return predictabilit | yes — 只需指數報酬 + 免費預測子(D/P、CAPE、term sprea |
| ② | zhu_zhou_2009_moving_average_allocation | Zhu & Zhou | 2009 | 650 | Return predictabilit | yes — 只需指數月報酬 + MA;可實作其效用比較框架。PIT 佳。成本 $ |
| ② | kelly_pruitt_2013_present_values | Kelly & Pruitt | 2013 | 650 | Return predictabilit | partial→yes — 需建 size/BM 組合的橫斷面 B/M(EDGA |
| ② | abdi-ranaldo2017-chl-spread | Abdi & Ranaldo | 2017 | 650 | Market microstructur | yes (fully). Close/high/low from OHLCV;  |
| ② | han_yang_zhou_2013_ma_cross_section | Han, Yang & Zhou | 2013 | 600 | Return predictabilit | yes — 波動排序與 MA 訊號全由免費日線建。PIT 佳。成本 $0(需注意 |
| ② | bollerslev_marrone_xu_zhou_2014_vrp | Bollerslev, Marrone, X | 2014 | 600 | Return predictabilit | partial→大致 yes(美國腿)— 隱含變異數用 VIX(CBOE 免費, |
| ② | bali-demirtas-levy-2009-downside-var | Bali, Demirtas & Levy | 2009 | 600 | Derivatives, volatil | yes. VaR = empirical 1st/5th percentile  |
| ③ | ball-brown-1968 | Ball & Brown | 1968 | 11000 | earnings-return rela | partial — 概念可用 EDGAR 現代資料重現(即 PEAD TR 本身 |
| ③ | heston-1993-stochastic-vol | Heston | 1993 | 10000 | Stochastic volatilit | PARTIAL/NO. Pricing use = NO (needs a PI |
| ③ | delong_shleifer_summers_waldmann_1990 | De Long, Shleifer, Sum | 1990 | 9500 | Noise trader risk (l | PARTIAL/NO for the canonical test. The c |
| ③ | merton-1976-jump-diffusion | Merton | 1976 | 8500 | Jump risk / crash ri | PARTIAL->YES for the physical side. Jump |
| ③ | loughran-ritter-1995-new-issues | Loughran & Ritter | 1995 | 6000 | net-issuance | partial/no — 需 IPO/SEO 事件日；EDGAR 有 S-1/4 |
| ③ | french-schwert-stambaugh-1987 | French, Schwert & Stam | 1987 | 5500 | Volatility-return tr | YES. Only market index daily/monthly ret |
| ③ | lettau_ludvigson_2001_cay | Lettau & Ludvigson | 2001 | 3500 | Return predictabilit | partial — cay 需消費/財富/勞動所得季頻資料(FRED/BEA 免 |
| ③ | chordia-roll-subrahmanyam2000-commonality | Chordia, Roll & Subrah | 2000 | 3000 | Market microstructur | PARTIAL。原生度量=日內報價價差/深度,我們沒有。只能用日線 Amihud |
| ③ | francis-lafond-olsson-schipper-2005 | Francis, LaFond, Olsso | 2005 | 3000 | accruals quality / e | partial — 應計品質需估 Dechow-Dichev 迴歸(應計對前中後 |
| ③ | rouwenhorst_1998_international_momentum | Rouwenhorst | 1998 | 2600 | Momentum: internatio | no / partial. Requires international (12 |
| ③ | bakshi-kapadia-madan-2003-implied-moments | Bakshi, Kapadia & Mada | 2003 | 2600 | Derivatives, volatil | no for the implied side (needs the full  |
| ③ | rosenberg-reid-lanstein-1985-bm | Rosenberg, Reid & Lans | 1985 | 2500 | value | yes — B/M = 帳面權益(EDGAR)/市值，全免費。 |
| ③ | carr-wu-2009-variance-risk-premiums | Carr & Wu | 2009 | 2100 | Derivatives, volatil | partial. Market-level: synthetic index v |
| ③ | foster-olsen-shevlin-1984 | Foster, Olsen & Shevli | 1984 | 1900 | PEAD (origin) | yes — 純 EDGAR 季 EPS 時序建 UE；PIT 可行；成本≈$0。 |
| ③ | ou-penman-1989 | Ou & Penman | 1989 | 1900 | fundamentals / compo | yes — 財報比率全 EDGAR；但須注意其樣本內 logit 選變數的前視/ |
| ③ | cohen_frazzini_2008_economic_links | Cohen & Frazzini | 2008 | 1500 | Momentum: cross-firm | partial. Returns free; the customer-supp |
| ③ | asquith_pathak_ritter_2005_short_interest | Asquith, Pathak & Ritt | 2005 | 1300 | Behavioral finance & | PARTIAL. Short interest is published ~bi |
| ③ | xing-zhang-zhao-2010-vol-smirk | Xing, Zhang & Zhao | 2010 | 900 | Derivatives, volatil | no (for the native signal). Requires per |
| ③ | cremers-weinbaum-2010-putcall-parity | Cremers & Weinbaum | 2010 | 850 | Derivatives, volatil | no (native). Needs matched-strike call/p |
| ③ | an-ang-bali-cakici-2014-joint-cross-section | An, Ang, Bali & Cakici | 2014 | 750 | Derivatives, volatil | no (native). Needs per-stock call/put im |
| ③ | kozak-nagel-santosh-2018-interpreting | Kozak, Nagel & Santosh | 2018 | 750 | SDF / factor structu | partial — 命題可用本專案特徵組合的 PCA 譜檢驗(幾個主成分解釋 S |
| ③ | avramov-chordia-goyal2006-liquidity-reversals | Avramov, Chordia & Goy | 2006 | 700 | Market microstructur | yes. Weekly returns + turnover + Amihud  |
| ③ | elliott_gargano_timmermann_2013_complete_subset | Elliott, Gargano & Tim | 2013 | 600 | Return predictabilit | yes — 只需指數報酬 + Goyal 免費預測子集;子集迴歸平均易實作。PI |
| ③ | haddad-kozak-santosh-2020-factor-timing | Haddad, Kozak & Santos | 2020 | 550 | factor timing / SDF | partial — 需先建 characteristic-managed PC  |
| (已參照) | bollerslev-1986-garch | Bollerslev | 1986 | 45000 | Conditional volatili | YES, fully. GARCH(1,1)/EGARCH fit on fre |
| (已參照) | black-scholes-1973 | Black & Scholes | 1973 | 45000 | Option pricing (base | NO for pricing (no PIT options chain — b |
| (已參照) | carhart_1997_wml_factor | Carhart | 1997 | 23000 | Momentum factor cons | yes。WML 因子完全可由免費日線 OHLCV 建構(基金 leg 不需要); |
| (已參照) | johansen-1991 | Johansen | 1991 | 22000 | Econometrics & metho | yes — 只需免費日線 OHLCV(股票/ETF)；statsmodels 已 |
| (已參照) | jegadeesh_titman_1993_momentum | Jegadeesh & Titman | 1993 | 14000 | Cross-sectional mome | yes(已測)。完全可用免費日線;TR-11 已在 47 檔同產業與 503 檔 |
| (已參照) | kyle1985-lambda | Kyle | 1985 | 13000 | Market microstructur | PARTIAL/model。真 λ 需簽名成交(intraday/tick),我 |
| (已參照) | petersen-2009 | Petersen | 2009 | 12000 | Econometrics & metho | yes — 純標準誤重算，用既有 47/610 股票月報酬 panel 即可；零 |
| (已參照) | ff-2015-five-factor | Fama & French | 2015 | 11000 | quality/profitabilit | yes — RMW(營業利潤/帳面權益)、CMA(總資產成長)皆由 EDGAR  |
| (已參照) | amihud_2002 | Amihud | 2002 | 11000 | Limits-to-arbitrage  | YES (fully). ILLIQ = mean(|daily return| |
| (已參照) | sloan-1996-accruals | Sloan | 1996 | 7000 | accruals anomaly / f | yes — 需 EDGAR 資產負債表/現金流量表(流動資產、流動負債、現金、折 |
| (已參照) | gw08_oos | Goyal & Welch | 2008 | 3800 | Return predictabilit | yes(已具備)— GW 資料集公開免費,TR-17 已部分採用;協定即本專案  |
| (已參照) | moskowitz_ooi_pedersen_2012_tsmom | Moskowitz, Ooi & Peder | 2012 | 3600 | Time-series momentum | partial。原生棲地=roll-adjusted 連續期貨,免費資料到不了( |
| (已參照) | harvey_liu_zhu_2016_cross_section_expected_returns | Harvey, Liu & Zhu | 2016 | 3500 | Modern asset pricing | yes (methodological, no market data need |
| (已參照) | piotroski-2000-fscore | Piotroski | 2000 | 3000 | fundamentals / F-sco | yes — 9 訊號全來自 EDGAR 損益/資產負債/現金流；PIT 申報日對 |
| (已參照) | bernard-thomas-1990-underreaction | Bernard & Thomas | 1990 | 2300 | PEAD / earnings expe | yes — 只需 EDGAR 季 EPS 序列建自相關 SUE 與後續申報窗；P |
| (已參照) | corwin-schultz2012-highlow-spread | Corwin & Schultz | 2012 | 1600 | Market microstructur | yes (fully). Daily high/low from OHLCV;  |
| (已參照) | moreira_muir_2017_vol_managed | Moreira & Muir | 2017 | 1500 | Momentum: risk-manag | yes, fully. Vol-managed factor = factor  |

### C.1 第一波 — 高引用 × 免費資料可重建 × 高洞見(立即可排 TR)

這些可用現有日線 OHLCV + EDGAR 就能重建,是下一輪 TR 的首選。每篇附建議的 fabric TR 切入角度(含它必須先打敗的 Nagel 對照)。

#### engle-granger-1987-cointegration — Engle & Granger (1987) · ~40000 引用 · 「Co-integration and Error Correction: Representation, Estimation, and Testing」
- **主張 / 與我方關聯**:若兩個 I(1) 價格序列共整合,其線性組合是 I(0)(均值回歸),且存在誤差修正表述;以殘差單根檢定判定共整合。 → TR-01 統計套利配對目前用 distance/相關;Engle-Granger 給配對交易的『正確計量座位』——共整合 + ECM 半衰期,判斷價差是否真回歸而非偽相關。
- **可測性(免費資料)**:yes — 只需日線 OHLCV 價格對;無新資料;算力小;注意共整合關係可能不穩定(需滾動再估)。
- **TR 切入(含 Nagel 對照)**:TR-01b:用 Engle-Granger 共整合(而非 distance)選對 + ECM 建價差訊號,套 F1 成交時點/成本;Nagel 對照=隨機進場的假價差與靜態持有,確認共整合對的均值回歸淨利勝隨機控制且非樣本內假象。

#### newey-west-1987 — Newey & West (1987) · ~30000 引用 · 「A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix」
- **主張 / 與我方關聯**:當殘差有自相關/異質變異數（重疊報酬、波動叢聚），OLS 標準誤被低估、t 值灌水；NW 給出封閉式一致共變異估計。 → 我們唯一顯著 alpha=多 sleeve Carhart α t=2.64（docs/00 §E4）與 TR-06 Fama-MacBeth 斜率 t=2.69 都建立在報酬序列上；月度再平衡+動量重疊使殘差自相關，NW 是判斷這些 t 是否撐得住的第一道誠實檢查。
- **可測性(免費資料)**:yes — 純標準誤重算，只需既有免費日/月報酬序列，零新資料、point-in-time 不受影響；lag 選擇用 Andrews(1991)/4(T/100)^(2/9) 經驗式即可。
- **TR 切入(含 Nagel 對照)**:TR：把所有 headline t（多 sleeve α、TR-06 FM 斜率）以 NW HAC(lag=重疊期)重算，並列 OLS/NW/月度聚類/block-bootstrap 四種 t 對照。Nagel 對照=同一 NW 尺規下，策略 α 的 NW-t 必須顯著高於 (a) 1/σ² 波動管理 book 與 (b) 靜態曝險 book 各自對 VOO 的 α NW-t，且隨機進場 placebo book 的 NW-t≈0；若策略 t 在 NW 校正後跌破門檻或不勝控制，判 α 為推論假象。

#### debondt_thaler_1985_overreaction — De Bondt & Thaler (1985) · ~9500 引用 · 「Does the Stock Market Overreact?」
- **主張 / 與我方關聯**:以過去 3-5 年累積報酬排名,極端 loser 組合在後續 3-5 年顯著跑贏極端 winner 組合(反轉),幅度無法用 CAPM beta 解釋。 → 長期反轉是動量-反轉光譜的長端(與 JT 短中期動量正好相反),是選股的 contrarian 主軸;若在其 503 檔宇宙成立,可作為與動量 sleeve 對沖的低相關 sleeve。
- **可測性(免費資料)**:yes(有但書)。日線→月頻、36月形成/36月持有完全可算;point-in-time 用其 503 檔 S&P 宇宙可行。關鍵風險:原始效應集中在小型/低價股,且極度依賴 survivorship 與 delisting 報酬——必須掛 TR-13 Shumway 下市調整,否則 loser 反彈被倖存者偏誤灌水。成本低,無需日內/選擇權。預期:在現代大型股宇宙上效應大幅衰減。
- **TR 切入(含 Nagel 對照)**:在 503 檔 PIT 宇宙建 3年形成期十分位,long past-loser − short past-winner,月頻再平衡,強制 Shumway 下市報酬。Nagel 對照:反轉組合的『loser 溢酬』必須先擊敗 (a) Cederburg 靜態常波動 long-only、(b) 加入 size + 低價(1/price)控制後的殘餘——因為 loser=高 beta/小型/低價的複合;還要贏隨機進場 contrarian。預先承諾:若 loser 溢酬被 size+beta 控制吸收,判定=『長期反轉=小型/低價因子的重新包裝』。

#### lsv-1994-contrarian — Lakonishok, Shleifer & Vishny (1994) · ~9000 引用 · 「Contrarian Investment, Extrapolation, and Risk」
- **主張 / 與我方關聯**:value(高 B/M、高 C/P、高 E/P、低過去銷售成長)溢酬源於投資人對過去成長的外推錯誤定價，非風險補償；value 在壞狀態並不特別差。 → 提供 value 的行為機制與多維估值排序(C/P、GS 雙維 glamour-vs-value)，可判別我方『value 死』是外推機制失效還是座位/建構問題。
- **可測性(免費資料)**:yes — E/P、B/M、C/P(現金流/價)、sales growth 全部由 EDGAR+價格可建，PIT。
- **TR 切入(含 Nagel 對照)**:建 LSV glamour-vs-value 雙維排序(估值×過去成長)L/S，市場中性，對照 shuffle 隨機分位；檢驗『壞狀態不差』宣稱於我方 regime 面板，並 beat 1/σ² vol-managed 與靜態 beta（證非單純低 beta）。

#### daniel_hirshleifer_subrahmanyam_1998 — Daniel, Hirshleifer & Subrahmanyam (1998) · ~7000 引用 · 「Investor Psychology and Security Market Under- and Overreactions」
- **主張 / 與我方關聯**:Overconfident investors overreact to private information; self-attribution sustains momentum short-term, then arriving public information forces a long-run correction (reversal). Effects are largest where value is hard to pin down (high information ambiguity). → Predicts a specific time-signature (continuation -> reversal) AND a cross-sectional moderator (information ambiguity, proxyable by idio-vol / intangible intensity) — gives a testable 'where should momentum live' map that reframes our dead large-cap momentum as a mis-seated test.
- **可測性(免費資料)**:YES/PARTIAL. Momentum (2-12m) + LT-reversal (36-60m) legs from price. Ambiguity moderator: true proxy = analyst dispersion (I/B/E/S, NOT free); use idio-vol + intangible intensity (R&D/SG&A from EDGAR) as free surrogates -> partial. Point-in-time OK.
- **TR 切入(含 Nagel 對照)**:Build momentum and LT-reversal legs, interact with an information-ambiguity proxy (idio-vol, intangible intensity from EDGAR); DHS predicts stronger continuation-then-reversal in high-ambiguity names. Nagel controls it must beat: (1) static full-exposure baseline of the ambiguity-sorted basket; (2) 1/sigma^2 vol-managed momentum (Moreira-Muir vol-managed momentum is already strong — the DHS-conditioned spread must beat THIS, the hardest control); (3) placebo ambiguity ranking -> interaction vanishes. Subsume test vs plain momentum + FF. PASSED only if ambiguity-conditioned continuation/reversal beats vol-managed momentum and is not plain momentum repackaged.

#### pastor-stambaugh2003-liqrisk — Pastor & Stambaugh (2003) · ~6500 引用 · 「Liquidity Risk and Expected Stock Returns (Journal of Political Economy)」
- **主張 / 與我方關聯**:每股月度流動性 γ 來自『簽名成交量→次日反轉』回歸;市場整體 γ 的 innovation 是系統風險;對此 innovation 高 beta 的股票有更高期望報酬(年化 ~7.5% 高−低)。 → 選股用『流動性 beta』排序,而非流動性 level;是與 Amihud level 效應正交的第二維度。也給一個市場擇時信號(aggregate liquidity innovation)。**強項:P-S 度量是專為日線資料設計的**,不像多數微結構度量需要 tick。
- **可測性(免費資料)**:YES(核心可重建)。每股 γ:回歸 r_{i,t+1} = θ + φ·r_{i,t} + γ·sign(超額 r_{i,t})·(收盤×量)_{i,t}。全部來自免費日線 OHLCV。Aggregate innovation = 橫斷面平均 γ 的 AR innovation。流動性 beta = 時序回歸。Point-in-time OK(全 trailing)。成本 $0。
- **TR 切入(含 Nagel 對照)**:建每股 γ→aggregate innovation→時序回歸取每股流動性 beta,beta 五分位 L/S。Nagel 對照:(1) 靜態曝險——流動性 beta 是否只是 CAPM market beta 或 size 的偽裝?對 static beta/size-matched 組合中性化;(2) 1/σ² 波動管理——aggregate liquidity 崩塌 = 危機高波動,檢查溢酬不是 1/σ² 波動擇時的重貼標籤(用實現波動當 VIX 代理條件化);(3) 隨機進場 null。並把 aggregate liquidity innovation 當市場擇時信號,直接對打 Nagel 的 1/σ² 波動管理——這正是 Nagel 批評的核心戰場。

#### ang-hodrick-xing-zhang-2006-ivol — Ang, Hodrick, Xing & Zhang (2006) · ~6000 引用 · 「The Cross-Section of Volatility and Expected Returns」
- **主張 / 與我方關聯**:以 FF3 殘差算出的高特質波動股,未來報酬顯著偏低(月 −1%+),與『波動應被補償』相反 = IVOL puzzle。 → 直接可交易的選股訊號:多低 IVOL、避高 IVOL;是 low-vol 家族中最乾淨的橫斷面版本,可疊在已 PASSED 的 GP 品質 sleeve 上;與我們宇宙相性高(只需量價)。
- **可測性(免費資料)**:yes — 只需免費日線報酬 + Ken French 日頻 FF3 因子(已接 pandas_datareader);IVOL=過去 21-60 日 FF3 迴歸殘差之標準差,全量價、無 PIT 洩漏;零成本。限制:我們宇宙偏大型科技股,IVOL 分散度較窄,可能壓縮 spread。
- **TR 切入(含 Nagel 對照)**:503/610 宇宙月度依 IVOL 分 quintile,多低空高。判定前必打敗 Nagel 三件套,尤其 (1) 1/σ² 波動管理控制——IVOL 極可能只是把低波動股放大權重的複雜包裝(如 TR-17 KMZ 被 1/σ² 支配);(2) 靜態低波動 sleeve(常數曝險);(3) 隨機特徵 placebo。淨成本後仍勝 1/σ² 才算真 IVOL alpha,否則判 PARTIAL = vol-timing 重述。

#### ff88_divyield — Fama & French (1988) · ~5000 引用 · 「Dividend Yields and Expected Stock Returns (JFE 22:3-25)」
- **主張 / 與我方關聯**:股利殖利率 D/P 正向預測後續市場超額報酬,且 R² 隨持有期拉長而上升(1年期解釋力遠大於月頻),反映折現率的時變。 → 最乾淨、最少資料需求的市場擇時訊號;若連 D/P 都打不過波動旋鈕,等於替本專案『$0 資料選不出 alpha』的 G-S 論點再添一柱。可延伸到用個股/產業 D/P 做橫斷面選股偏誤檢驗。
- **可測性(免費資料)**:yes — Shiller 免費長歷史月度資料(S&P 價格+股利,1871-)可直接建 D/P;用 trailing-12m 股利即 point-in-time 乾淨;$0。個股層可用 EDGAR 申報股利對齊,但覆蓋較差。
- **TR 切入(含 Nagel 對照)**:SPY/大盤月頻,trailing D/P 做 OOS predictive regression(擴張窗 + Campbell-Thompson 式歷史均值基準),倉位 ∝ 預測超額報酬並截倉[0,2]、淨 5bps。Nagel 對照關卡:必須勝過 Moreira-Muir 1/σ² 波動管理與 Cederburg 靜態 B&H,且對波動管理 alpha 的 t≥2;同時必須套 Stambaugh 偏誤修正的 t 值,否則判『persistent-regressor artifact』。

#### jegadeesh_titman_2001_evaluation — Jegadeesh & Titman (2001) · ~5000 引用 · 「Profitability of Momentum Strategies: An Evaluation of Alternative Explanations」
- **主張 / 與我方關聯**:Momentum profits persist strongly in the post-1990 out-of-sample period, are not explained by cross-sectional risk (Conrad-Kaul), and reverse partially over months 13-60 after formation, favouring a behavioral (delayed-overreaction) interpretation. → The OOS confirmation and the explicit month-13-to-60 reversal give two directly testable predictions (does momentum survive OOS on our seat, and does it reverse long-run?) that frame whether our null is habitat-specific or a genuine death.
- **可測性(免費資料)**:yes, fully. OOS momentum and post-formation long-run reversal both from free daily OHLCV; PIT trivial; cost $0.
- **TR 切入(含 Nagel 對照)**:Replicate momentum in a held-out post-publication window and trace cumulative returns to month 60 for the reversal on the 503 universe. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso), (2) static exposure, (3) random-entry placebo. Also run the Conrad-Kaul cross-sectional-variance decomposition as the specific alternative it must beat. PASSED only if net-cost OOS momentum survives and the long-run reversal replicates.

#### welch-goyal-2008 — Welch & Goyal (2008) · ~4500 引用 · 「A Comprehensive Look at the Empirical Performance of Equity Premium Prediction」
- **主張 / 與我方關聯**:幾乎所有經典股權溢酬預測子在樣本外都輸給簡單歷史均值,樣本內顯著多為不穩定/資料窺探;OOS R² 是誠實標尺。 → 這是 fabric 已引用的 Goyal-Welch 資料集原論文,也是 Campbell-Thompson 與 KMZ(TR-17)的共同基準;是『免費資料上擇時難』的定海神針,且資料正要 ingest。
- **可測性(免費資料)**:yes — 論文附公開月度資料集(1926-present),與 TR-17/KMZ 翻案條件共享 ingest 成本;PIT 對齊良好;算力小。
- **TR 切入(含 Nagel 對照)**:TR:重建 GW 面板,對每個預測子報 OOS R²(vs 歷史均值),再接 Campbell-Thompson 符號約束;Nagel 對照必打敗=1/σ² 波動管理 + 靜態曝險 + 隨機進場——唯有 OOS 勝歷史均值且淨值勝波動管理,才算真擇時 alpha。

#### grs-1989 — Gibbons, Ross & Shanken (1989) · ~4200 引用 · 「A Test of the Efficiency of a Given Portfolio (the GRS test)」
- **主張 / 與我方關聯**:給定 K 個因子，N 個測試資產的 α 是否聯合為零有精確 F 分布檢定；單一資產 t 顯著不代表模型被拒，須看聯合統計量（含 α 的共變異結構）。 → docs/00 §9A 已自爆：long-only sleeve 抬 α-t 是 beta 不是訊號（零訊號籃子照抬到 2.89）。GRS 正是把 5 個 sleeve 的 α 做『正確的多變量聯合檢定』的工具——比目前逐一單 t 誠實一個量級，直接壓力測試那個 t=2.64。
- **可測性(免費資料)**:yes — 只需 sleeve/測試組合月報酬 + Ken French 因子（免費），構建測試組合用免費 OHLCV+EDGAR 排序即可；point-in-time 用申報日對齊排序變數；無需日內/選擇權。
- **TR 切入(含 Nagel 對照)**:TR：把 5 sleeve（或品質/動量分位組合）當測試資產，對 (i) CAPM/FF5+Carhart 與 (ii) 加入 Nagel 因子的擴充集跑 GRS。Nagel 對照直接進因子集：加入 Moreira-Muir 1/σ² 波動管理市場因子與靜態市場因子後，若 GRS 聯合 α 由顯著轉不顯著 → 判『多 sleeve α = 波動擇時/beta 包裝』；唯有在含波動管理+靜態因子的 spanning 下 GRS 仍拒絕 α=0，才升格為真 α。

#### clark-west-2007 — Clark & West (2007) · ~4000 引用 · 「Approximately Normal Tests for Equal Predictive Accuracy in Nested Models」
- **主張 / 與我方關聯**:比較巢狀模型（含預測子 vs 只有常數/歷史均值）的 OOS MSPE 時，即使真模型是常數，較大模型也會因估計噪音吃虧；CW 給出調整後、近似常態的檢定，正確判『預測子是否真的 OOS 勝常數』。 → 這是 Nagel『打敗常數/靜態』批評的統計正典化：TR-17(KMZ VoC) 與任何用 EDGAR 估值比預測報酬的擇時，都要先過『OOS 勝歷史均值』這關。CW 正是那個檢定，直接補強 F6/F7 的樣本外誠實層。
- **可測性(免費資料)**:yes — 只需長指數歷史(SPY/QQQ)+免費預測子(估值比/動量/波動)，擴張視窗 OOS 即可；point-in-time 用 EDGAR 申報日對齊；無需日內/選擇權。
- **TR 切入(含 Nagel 對照)**:TR：對每個候選預測子跑 CW 檢定 vs 歷史均值基準（=靜態/常數），報 OOS R² 與 CW-t。Nagel 對照本身就是虛無假設：常數基準=靜態曝險、1/σ² 波動管理視為第二基準；預測子必須 CW-顯著勝『常數』且勝『1/σ² 波動時序』兩者，才算真預測力。把此檢定接進 TR-17，直接裁決 VoC 曲線是否只是波動擇時。

#### frazzini-pedersen-2014-bab — Frazzini & Pedersen (2014) · ~3500 引用 · 「Betting Against Beta」
- **主張 / 與我方關聯**:槓桿與賣空受限使投資人追買高 beta，壓低其風險調整報酬;BAB 因子(beta-中性、做多低 beta 槓桿化)有顯著正 alpha，橫跨資產類別。 → 任務自己舉的範例論文，且直接對話本專案 TR-06 發現的『SML 反轉』(AI 牛市高 beta 大勝，=BAB 反向)。是檢驗低風險異常在本科技重倉座位是否失效的關鍵。
- **可測性(免費資料)**:yes — beta 用日線 OHLCV 估(FP 的 correlation×vol 分解法)；PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 用 FP 的 rank-weighted、beta-中性 BAB 建構在本宇宙重測，並跨 regime(AI 牛市 vs 一般)拆解，直接對照 TR-06 的 SML 反轉。必須打敗:(a) 靜態市場曝險，(b) 隨機進場，(c) 樸素低波動排序(證 FP 槓桿建構的增量)。

#### cooper-gulen-schill-2008-asset-growth — Cooper, Gulen & Schill (2008) · ~3200 引用 · 「Asset Growth and the Cross-Section of Stock Returns」
- **主張 / 與我方關聯**:總資產年成長率越高，後續報酬越低；控制 size/BM/動量後，asset growth 仍是最強的橫斷面預測子之一，且在大型股亦顯著。 → investment 因子的主力，且是少數在大型股(我方座位)仍強的異常；與 FF5 CMA、q-factor I/A 同源，可判別三者哪個在我方宇宙存活。
- **可測性(免費資料)**:yes — 總資產 YoY from EDGAR，PIT 對齊申報日。
- **TR 切入(含 Nagel 對照)**:asset-growth decile L/S(低成長−高成長)，市場中性，對照 shuffle 與 FF5(CMA 是否吸收)；檢驗投資因子在我方大型股是否比 value 存活得好，須 beat 隨機分位與靜態 beta。

#### harvey-siddique-2000-coskewness — Harvey & Siddique (2000) · ~3200 引用 · 「Conditional Skewness in Asset Pricing Tests」
- **主張 / 與我方關聯**:Stocks whose returns covary with market volatility / market squared returns (negative coskewness) command a premium (~3.6%/yr); adding systematic skewness helps price the cross-section and absorbs part of momentum. Skewness preference is priced beyond mean-variance. → The cleanest free-data higher-moment stock-selection signal and the missing >2000 classic underneath the already-listed Ang-Chen-Xing downside-beta entry. Directly instruments the project's tail-risk theme: negative-coskew names are the ones that crash with the market, so any 'premium' is a candidate risk-compensation the G-S framing predicts should survive on $0 data (it's a risk exposure, not an anomaly).
- **可測性(免費資料)**:yes (fully). Coskewness = standardized E[ε_i · ε_m^2] estimated from trailing ~12-60m daily stock + index excess returns; needs only free daily OHLCV + index. PIT trivial (all trailing). Cost ~$0. Weakest-habitat caveat: premium is stronger in small caps, so survivorship large-cap universe may compress it.
- **TR 切入(含 Nagel 對照)**:TR: estimate systematic coskewness (SKD) for 503/610 PIT universe from daily returns, quintile-sort, net-cost L/S long-negative-coskew minus long-positive-coskew. Nagel controls it must beat: (a) static exposure — coskew-sorted basket held at constant weight (is the 'premium' just a hidden beta/size tilt?); (b) 1/σ² vol-managed version of the same book; (c) random-coskew placebo (shuffle the ranking → spread must vanish). Also run FF3+UMD subsumption. Pre-commit: PASS only if net-of-cost L/S survives AND beats static exposure AND is not spanned by market beta + size; else verdict = 'coskewness = beta/size repackaging in this seat.'

#### politis-romano-1994-stationary-bootstrap — Politis & Romano (1994) · ~3000 引用 · 「The Stationary Bootstrap」
- **主張 / 與我方關聯**:以幾何分布隨機區塊長重抽樣,產生平穩自助樣本、保留時序相依;是 White reality-check、Hansen SPA、Ledoit-Wolf Sharpe 檢定的底層引擎。 → fabric F5 與 Sharpe 檢定都『默默用了』區塊自助,但我們從未把平穩自助當一級工具校準/對照 iid 自助——它是所有相依穩健推論的地基。
- **可測性(免費資料)**:yes — 純重抽樣工具;套既有 F5/報酬序列;無新資料;需調 mean block length。
- **TR 切入(含 Nagel 對照)**:TR:把平穩自助抽成一級模組,對 F5 檢定並列 iid vs 平穩自助分布;Nagel 對照=隨機進場策略,確認平穩自助在相依結構下正確地讓隨機控制不顯著(而 iid 自助可能過度自信),真策略需在平穩自助下仍過關。

#### shanken-1992 — Shanken (1992) · ~2900 引用 · 「On the Estimation of Beta-Pricing Models (errors-in-variables correction)」
- **主張 / 與我方關聯**:Fama-MacBeth 第二階段用的是估計出的 β（含測量誤差），未校正的 FM 標準誤系統性低估、風險價格 t 灌水；Shanken 給出 (1+市場 SR²) 膨脹因子的封閉修正。 → TR-06 的 A1 用 Fama-MacBeth 得市場風險價格 +1.899%/mo, t=2.69——這個 t 未做 Shanken 校正，可能高估。這是直接精修一個既有 TR 判定、且是本子領域點名的 Fama-MacBeth 家族核心缺口。
- **可測性(免費資料)**:yes — 純標準誤重算，用 TR-06 既有月報酬+β 估計即可，零新資料；point-in-time 不受影響。
- **TR 切入(含 Nagel 對照)**:TR-06b：對 TR-06 的 FM 斜率套 Shanken EIV 膨脹，報告校正前後 t（預期 t 由 2.69 下修）。Nagel 對照=把 FM 估到的風險價格拿去建『按估計 β 排序』的多空 book，須淨勝 (a) 隨機 β 指派 placebo 與 (b) 靜態 buy-and-hold；若 Shanken 校正後斜率 t 跌破 2.0 或 book 不勝控制，判市場-β 溢酬在本樣本為弱證據。

#### bali-cakici-whitelaw-2011-max — Bali, Cakici & Whitelaw (2011) · ~2900 引用 · 「Maxing Out: Stocks as Lotteries and the Cross-Section of Expected Returns」
- **主張 / 與我方關聯**:Stocks with the highest max daily returns last month (lottery-like) earn LOW subsequent returns; MAX subsumes much of the idio-vol puzzle — investors overpay for right-tail skew. → Trivially computable stock screen (max daily return) usable in selection today; and a direct explanation-competitor to AHXZ idio-vol — a joint test resolves which vol/skew mechanism, if any, survives in our universe.
- **可測性(免費資料)**:YES, fully. MAX(k) = mean of the k largest daily returns in the trailing month, straight from free daily OHLCV. Point-in-time trivial. No options/intraday.
- **TR 切入(含 Nagel 對照)**:Monthly decile sort on MAX(5) across the 610 universe; long low-MAX / short high-MAX; exSharpe + FF/Carhart alpha, 2x cost stress (F2), phase-averaged (F12). Nagel controls it MUST beat: (a) zero-signal random-decile basket (F6), (b) static EW-47 / B&H (F3); as a pure cross-sectional bet the 1/sigma^2 timing control is secondary, the random-entry/zero-signal control is primary. Double-sort MAX x idio-vol to see if either adds over the other or both collapse. Prior: given FAILED low-vol and dead XS-momentum, expect a small/insignificant net-of-cost MAX premium, but it is cheap and high-insight to confirm.

#### stambaugh99_bias — Stambaugh (1999) · ~2800 引用 · 「Predictive Regressions (JFE 54:375-421)」
- **主張 / 與我方關聯**:當回歸子高度持久且其創新與報酬創新相關時,OLS 斜率有系統性向上偏誤、標準 t 檢定嚴重高估顯著性;給出偏誤方向、量級與貝式後驗修正。 → 這是 fabric『誠實層』的直接彈藥:本專案所有用 D/P、CAPE、利差擇時的 TR 都踩在 Stambaugh 偏誤上;把它做成一個可複用的統計閘,能一次性下修多個擇時訊號的顯著性,呼應 3 次對抗 review 抓 in-sample artifact 的傳統。
- **可測性(免費資料)**:yes — 純方法論,只需既有報酬+預測子序列;實作 Stambaugh/Kendall 偏誤修正與 bootstrap;無新資料需求;$0。
- **TR 切入(含 Nagel 對照)**:不是策略而是閘:對 TR 的每個持久估值比擇時訊號,回報 OLS-t 與偏誤修正-t 的落差,及 bootstrap p 值。Nagel 對照關卡的補強件——先用它證明訊號係數在修偏後仍顯著,再進波動管理/靜態曝險對照;若修偏後 t 崩到 <2,則該擇時訊號在打 Nagel 對照前就已出局。

#### bernard-thomas-1989-pead — Bernard & Thomas (1989) · ~2800 引用 · 「Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium?」
- **主張 / 與我方關聯**:盈餘驚奇(SUE)最高十分位在申報後約 60 交易日持續向上漂移、最低向下，L/S 約 18%/年；漂移無法用 CAPM/size 風險解釋，屬延遲反應(under-reaction)。 → PEAD 是免費資料最可行的事件型 alpha 之一，只需 EDGAR 申報日 + 歷史盈餘算 SUE，日線算事件後累積報酬；既有名單有動量/反轉但無 PEAD 這條純基本面事件腿。
- **可測性(免費資料)**:yes — EDGAR 提供季 EPS 與精確申報日(PIT 天然對齊，申報日=可交易日)；SUE 用季節性隨機漫步或標準化驚奇；日線算 drift。成本≈$0。唯早年 EDGAR 前(<1994)資料缺。
- **TR 切入(含 Nagel 對照)**:TR 建 SUE decile，於 EDGAR 申報日 T+1 進場、持有 ~60 交易日的漂移 L/S，含 F1 成交時點與交易成本。必須打敗:(a) 隨機進場日(同持有期、破事件擇時假象)，(b) 靜態曝險，(c) 廣市場動量(證 PEAD 非動量重貼標籤)。

#### grinblatt_han_2005 — Grinblatt & Han (2005) · ~2600 引用 · 「Prospect Theory, Mental Accounting, and Momentum」
- **主張 / 與我方關聯**:Stocks with large unrealized capital GAINS (price above the turnover-weighted reference price) earn higher subsequent returns than those with large unrealized losses; when CGO is added as a regressor, conventional past-return momentum disappears. → THE free-data-testable manifestation of the disposition effect: Odean (1998) and Shefrin-Statman (1985) need individual brokerage records we can never get, whereas CGO is their market-level proxy, fully reconstructable from price + volume + shares. A genuinely novel-to-us signal that directly speaks to our dead-momentum result.
- **可測性(免費資料)**:YES — the most cleanly buildable in this set. CGO = f(historical prices, weekly turnover). Turnover needs shares outstanding (EDGAR, PIT) or a volume proxy. All from daily OHLCV + EDGAR shares. Point-in-time clean. Moderate turnover -> costs matter but tractable. Cost ~$0.
- **TR 切入(含 Nagel 對照)**:Construct a ~5yr turnover-weighted reference price, compute CGO, decile-sort broad universe, net-of-cost L/S; and run the horse-race regression CGO vs past-return momentum on our universe. Nagel controls it must beat: (1) static EW exposure to the high-CGO basket (Cederburg); (2) 1/sigma^2 vol-managed momentum as the benchmark it must ADD value over — is CGO a different trade or the same edge?; (3) placebo reference price (random weights) -> signal collapses. Key PASSED bar: net-cost CGO L/S beats BOTH vol-managed momentum and static exposure, AND the 'CGO subsumes momentum' regression replicates on our data.

#### mclean_pontiff_2016_academic_research_destroys — McLean & Pontiff (2016) · ~2600 引用 · 「Does Academic Research Destroy Stock Return Predictability? (Journal of Finance)」
- **主張 / 與我方關聯**:Predictor returns fall ~26% out-of-sample and ~58% post-publication; decay is larger for anomalies that are more arbitrageable (higher liquidity, more capital), consistent with arbitrageurs trading on the published signal. → Directly formalizes the corpus's most-repeated empirical finding ('post-2019 effect decay', G-S $0-info→$0-alpha). Gives a quantitative yardstick to judge whether OUR surviving factor (GP ICIR+0.30) is pre- or post-publication, and predicts which of our zoo entries should already be dead.
- **可測性(免費資料)**:yes (methodologically) — we already have a factor library + trial registry; needs each factor's publication date (public) and our own in-sample vs post-pub OOS returns. No new data. Caveat: our sample is short and large-cap, so we can only test the decay slope on the handful of factors we can rebuild, not their full 97. Cost $0.
- **TR 切入(含 Nagel 對照)**:For each rebuildable factor (GP, accruals, momentum, value, F-score) split return at the original publication date and measure in-sample vs post-pub OOS attenuation; compare to MP's ~58% benchmark. Nagel control it must beat: STATIC EXPOSURE — the honest post-pub baseline is a buy-and-hold of the factor with no timing; the test is whether any residual post-pub alpha survives net of static exposure and is NOT just a 1/sigma^2 (Moreira-Muir) vol-managed repackaging. Pre-commit: a factor whose post-pub alpha is fully explained by static exposure + vol timing is reclassified as decayed.

#### ct08_restrictions — Campbell & Thompson (2008) · ~2400 引用 · 「Predicting Excess Stock Returns Out of Sample: Can Anything Beat the Historical Average? (RFS 21:1509-1531)」
- **主張 / 與我方關聯**:對 Goyal-Welch 的悲觀結論回擊:只要施加簡單經濟約束(禁止負股權溢酬、係數符號合理),樣本外 R² 可轉正且小幅擇時可帶來實質效用增益;微小 OOS R²(~0.5%/月)已具經濟價值。 → 直接界定『免費宏觀/估值訊號能否擇時』的樂觀上界,是 Goyal-Welch 的辯方;本專案已有 GW 15 預測子(TR-17),此文是最省成本的加值層——測『加約束後是否真的翻案』。
- **可測性(免費資料)**:yes — 沿用 TR-17 已有的 GW 預測子(公開資料)+ Shiller/FRED 免費序列;僅新增 sign/理論值截斷邏輯與 OOS R²、效用增益計算;point-in-time 可行;$0。
- **TR 切入(含 Nagel 對照)**:在既有 GW 預測子上跑約束版 OOS 預測(截負、係數封頂),用 Campbell-Thompson 的 OOS R² 與 CER 效用增益量度;構造 1/σ² 目標倉位。Nagel 對照關卡:效用增益必須來自『訊號』而非隱含的波動縮放——與 Moreira-Muir 波動管理正交化後仍須留下正 alpha(t≥2),否則判 OOS 增益=波動擇時包裝。

#### lee_swaminathan_2000_price_momentum_volume — Lee & Swaminathan (2000) · ~2300 引用 · 「Price Momentum and Trading Volume」
- **主張 / 與我方關聯**:Past trading volume forecasts both the magnitude and persistence of momentum: high-volume winners and low-volume losers experience faster reversals, while low-volume winners/high-volume losers sustain momentum, defining a 'momentum life cycle'. → Adds a free volume dimension to momentum that could separate the transient (reversing) from the durable component on our seat, sharpening or reviving a signal we found dead unconditionally.
- **可測性(免費資料)**:yes, fully. Both price momentum and trading volume/turnover come from free daily OHLCV (volume field); PIT trivial; cost $0.
- **TR 切入(含 Nagel 對照)**:Double-sort momentum x lagged turnover on 503 universe, replicate the life-cycle (high-vol winners reverse). Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso), (2) static exposure to the low-volume-winner basket, (3) placebo volume ranking. PASSED only if the volume-conditioned momentum spread beats vol-managed plain momentum net of cost.

#### george_hwang_2004_52wk — George & Hwang (2004) · ~2200 引用 · 「The 52-Week High and Momentum Investing」
- **主張 / 與我方關聯**:股價/52週高點的比值(接近高點程度)預測後續報酬,且此訊號『支配』傳統 JT 個股動量與 Moskowitz-Grinblatt 產業動量——動量本質是對 52週高錨點的 underreaction。 → 52週高是最乾淨、最好算的動量訊號(只需日線 rolling max),且宣稱『打敗 JT 動量本身』——正好可在他們已測死 JT 動量的宇宙上,檢驗是否有一個更強的動量代理漏測了。高洞見×高可用性。
- **可測性(免費資料)**:yes。訊號=每檔 close / trailing-252日最高價,純免費日線 OHLCV 即可;point-in-time 無前視。成本低,無需任何付費資料。這是本批最無資料摩擦的一篇。
- **TR 切入(含 Nagel 對照)**:建 52wk-high proximity 分位,long 近高 − short 遠高,月頻;直接對照組=既有 TR-11 的 JT 動量(論文核心宣稱:52wk 打敗 JT)。Nagel 三件套:必須擊敗 (a) Moreira-Muir 1/σ² 波動管理市場、(b) Cederburg 靜態曝險、(c) 隨機進場。預先承諾:若 52wk 溢酬僅在 JT 動量已死的宇宙裡也是 ICIR≈0,則錨定假說在此棲地不成立;若它獨活而 JT 死,才算真正新增訊號。

#### lns-2010-skeptical — Lewellen, Nagel & Shanken (2010) · ~2200 引用 · 「A Skeptical Appraisal of Asset Pricing Tests」
- **主張 / 與我方關聯**:在強因子結構(size/BM 投組)下,幾乎任何與 SMB/HML 相關的因子都能得到高橫斷面 R²;應改報 GLS-R²、報 95% 信賴區間、用經濟上多樣的測試資產。 → TR-03 PCA(PC1=41.8%)與任何橫斷面因子檢定都受此警示:別被漂亮 R²/SML 騙;直接約束我們『如何判因子 PASS』。
- **可測性(免費資料)**:yes — 方法論協定(GLS-R²、CI、測試資產多樣化);套既有橫斷面檢定;無新資料;算力小。
- **TR 切入(含 Nagel 對照)**:把 LNS 三戒律寫進因子檢定 harness:報 GLS-R² + CI + 產業/特徵多樣化測試資產;Nagel 對照=注入隨機『假因子』,證明它在舊 OLS-R² 下也能假裝顯著,但在 LNS-GLS 協定 + 隨機進場控制下被打回原形。

#### cooper_gutierrez_hameed_2004_market_states — Cooper, Gutierrez & Hameed (2004) · ~2100 引用 · 「Market States and Momentum」
- **主張 / 與我方關聯**:Momentum profits are entirely conditional on the market state: following positive lagged 3-year (or 12-month) market returns momentum is strongly positive, but following negative market states momentum profits are zero or negative and later reverse. → Provides a fully free regime gate (index return sign) that could explain WHEN our large-cap momentum pays, and connects directly to the momentum-crash timing we already care about via Daniel-Moskowitz.
- **可測性(免費資料)**:yes, fully. Market state = sign of lagged 12/36-month index return, available from our long index history; momentum from free daily OHLCV; PIT trivial; cost $0.
- **TR 切入(含 Nagel 對照)**:Condition momentum L/S on lagged market state on the 503 universe and index history; replicate 'up-state momentum only.' Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso) - prove market-state timing != vol-timing, the hardest control, (2) static always-on momentum exposure (Cederburg), (3) placebo market-state labels. PASSED only if state-conditioned momentum beats vol-managed always-on momentum net of cost and phase-averaged (F12) to defuse timing-luck.

#### lesmond-ogden-trzcinka1999-lot-zeroreturn — Lesmond, Ogden & Trzcinka (1999) · ~2000 引用 · 「A New Estimate of Transaction Costs」
- **主張 / 與我方關聯**:A stock's price stays flat on a day when the information signal is smaller than its trading cost, so the incidence of zero-return days identifies round-trip transaction costs via a limited-dependent-variable (Tobit-style) model. The LOT cost estimate tracks quoted+impact costs and is a priced friction cross-sectionally. → Gives a second, quotes-free trading-cost characteristic orthogonal in construction to Amihud ILLIQ (counts flat days rather than |ret|/$vol), and directly instruments the G-S 'who pays the information cost' framing. Buildable purely from daily OHLCV; complements the illiquidity-premium sleeve.
- **可測性(免費資料)**:yes (fully). Proportion of zero-return days + a one-parameter LDV/Tobit fit from daily OHLCV; PIT trivial; cost ~$0. Honest caveat: zero-return incidence is near-zero in a survivorship large-cap universe, so like Amihud/PEAD our seat is its WEAKEST habitat (premium lives in micro/small caps) — mis-seat risk high.
- **TR 切入(含 Nagel 對照)**:Rank the 610-name PIT universe by LOT cost, decile L/S + long-only high-cost tilt. Must beat all three Nagel controls: (1) static exposure — does the LOT premium survive after neutralizing a static size + Amihud-level tilt (expect heavy collinearity, most absorbed)?; (2) 1/σ² Moreira-Muir vol-management — high-LOT names spike in illiquidity during stress, so the residual must carry alpha t≥2 after orthogonalizing to vol-managed returns; (3) random-entry null on the same names. Position as a robustness sleeve to the Amihud TR: do two independent cost estimators (LOT vs Amihud) agree on sign/rank?

#### nagel_2005_short_sales_institutional — Nagel (2005) · ~1900 引用 · 「Short Sales, Institutional Investors and the Cross-Section of Stock Returns」
- **主張 / 與我方關聯**:Overpricing anomalies (high market-to-book, dispersion, turnover, volatility underperformance) concentrate among LOW institutional-ownership stocks, where short-sale constraints bind — overpricing can't be arbitraged when few institutions hold/lend the stock. → Directly the 'short-sale constraints' keyword and supplies a FREE short-constraint proxy (residual IO from 13F) that gates every overpricing anomaly — lets us DIAGNOSE the short side that our long-only, $0-data book can't trade. Bonus: authored by Nagel, the namesake of our control battery.
- **可測性(免費資料)**:YES/PARTIAL. Institutional ownership from 13F filings (free via EDGAR, quarterly); residual IO = IO orthogonalized on size (Nagel's logit spec). Anomaly signals from EDGAR+price; PIT OK (align on 13F filing date given its lag); cost $0. Caveat: 13F covers only >$100M managers with a reporting lag, and our large-cap universe is HIGH-IO (constraints rarely bind) = weakest seat.
- **TR 切入(含 Nagel 對照)**:Compute residual IO, double-sort a candidate anomaly (B/M, IVOL, turnover) × IO; test underperformance concentrated in low-IO names. Nagel controls: (1) static exposure — is low-IO just a small/illiquid beta tilt? neutralize vs size + Amihud ILLIQ (already in list); (2) 1/σ² vol management; (3) placebo IO. Pre-commit: since the effect lives in low-IO hard-to-short names we can't short, durable value = a GATE flagging which of our long-only exposures are arbitrageable (safe) vs short-constrained overpricing (trap).

#### ang_bekaert_2007_predictability_there — Ang & Bekaert (2007) · ~1800 引用 · 「Stock Return Predictability: Is It There?」
- **主張 / 與我方關聯**:股利殖利率單獨的長期可預測性脆弱(不穩健、樣本相依);但在雙變量系統中,短期利率是更穩健的負向預測子,且可預測性主要集中在短期而非長期。多國證據削弱了『D/P 強預測長期報酬』的傳統敘事。 → 直接針對『估值比擇時到底有沒有用』的核心疑問,並指向短期利率(免費 T-bill)可能是比 D/P 更可靠的擇時輸入——這對我們設計 regime gate(目前 200-SMA/Markov 都 FAILED)是具體的替代訊號建議。
- **可測性(免費資料)**:yes(美國腿)— 指數長歷史 + D/P(Shiller)+ 3M T-bill(Goyal/FRED 免費)。國際腿=partial(需國際指數)。PIT 佳。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:比較三個擇時輸入(D/P 單變量 vs 短期利率 vs 雙變量)在 SPY 上的 OOS 預測與轉成部位後的績效;必須先打敗 buy-and-hold 靜態曝險、1/σ² 波動管理與隨機進場。重點診斷:利率型 gate 是否在我們宇宙也比估值型 gate 穩健,或如 docs/09 的擇時全數 FAILED。判 PASS 需三對照皆勝且 Campbell-Yogo/CT 檢定顯著。

#### fu-2009-egarch-ivol — Fu (2009) · ~1800 引用 · 「Idiosyncratic Risk and the Cross-Section of Expected Stock Returns」
- **主張 / 與我方關聯**:When idiosyncratic volatility is measured as a CONDITIONAL EGARCH forecast rather than lagged realized IVOL, the cross-sectional relation to returns flips POSITIVE — reversing the Ang-Hodrick-Xing-Zhang puzzle. Expected (not realized) idio-vol is compensated. → Directly pits two seats of the same signal against each other — realized IVOL (already listed as AHXZ) vs conditional-forecast IVOL — which is exactly the project's 'were we in the wrong seat?' methodology. Testable end-to-end on free data, and carries a famous adversarial trap (Guo-Kassa-Ferguson 2014 show Fu's in-sample EGARCH fit induces look-ahead bias) that the fabric's PIT discipline is built to catch.
- **可測性(免費資料)**:yes. EGARCH(1,1) conditional idio-vol on daily/monthly FF3 residuals; free. CRITICAL PIT caveat: must use a one-step-ahead EXPANDING-window EGARCH forecast, never the in-sample fitted value (the known bias). Cost ~$0 (arch package, CPU-cheap).
- **TR 切入(含 Nagel 對照)**:TR: build EGARCH conditional IVOL two ways — (i) in-sample fitted (the biased Fu construction) and (ii) strictly PIT one-step forecast — and show the sign of the IVOL premium flips between them. Nagel controls: (a) static exposure; (b) 1/σ² vol management (the whole signal IS a vol construct — the forecast-IVOL sort must beat a vol-managed book, otherwise it's vol timing); (c) placebo forecast. Pre-commit: report both the biased and PIT versions; if the positive relation exists only under in-sample fit, verdict = look-ahead artifact (documents the seat where a famous result dies under PIT discipline).

#### pesaran-timmermann-1992 — Pesaran & Timmermann (1992) · ~1700 引用 · 「A Simple Nonparametric Test of Predictive Performance」
- **主張 / 與我方關聯**:給預測與實現同號比率的非參數檢定(PT 統計量),直接檢驗市場擇時方向有無技能,不依賴報酬幅度。 → 我們的 regime gate / 擇時 overlay 本質是方向決策;PT 檢定直接量『進出場方向有無 edge』,比 Sharpe 更貼近 gate 的功能。
- **可測性(免費資料)**:yes — 只需擇時訊號 + 指數報酬方向;無新資料;算力≈0。
- **TR 切入(含 Nagel 對照)**:TR:對 200-SMA / Markov gate 的進出方向跑 PT 檢定;Nagel 對照=隨機進場(方向亂猜)與靜態曝險(永遠 in),證明 gate 方向命中率顯著高於隨機、且擇時淨值勝靜態,才算真擇時。

#### stambaugh_yu_yuan_2015_arbitrage_asymmetry — Stambaugh, Yu & Yuan (2015) · ~1600 引用 · 「Arbitrage Asymmetry and the Idiosyncratic Volatility Puzzle」
- **主張 / 與我方關聯**:IVOL predicts LOW returns among overpriced stocks but HIGH returns among underpriced; because buying is easier than shorting (arbitrage asymmetry), the overpriced/negative side dominates, so the overall IVOL-return relation is negative; high sentiment strengthens the negative (overpriced) side. → Directly names the subdomain keyword 'arbitrage asymmetry' and reframes the ALREADY-referenced Ang-Hodrick-Xing-Zhang (2006) IVOL puzzle as a limits-to-arb phenomenon rather than a risk factor. Yields a mispricing-conditioned selection rule (avoid high-IVOL overpriced names on the long book) and instruments the G-S 'who can't pay to arbitrage' story on the un-shortable short side.
- **可測性(免費資料)**:YES/PARTIAL. IVOL from OHLCV+FF3 residuals (free). Mispricing score = composite rank of 11 anomalies, many buildable from EDGAR+price (accruals, gross profitability, asset growth, momentum, NOA, O-score) but a few partial (net stock issuance, distress). BW sentiment index free (full-sample PCA look-ahead caveat, identical to the already-listed baker_wurgler_2006). PIT OK for IVOL and most anomaly legs; cost ~$0. Honest limit: our survivorship large-cap universe compresses IVOL dispersion, and the action is on the overpriced short leg we can't trade (effectively long-only) → weakest habitat.
- **TR 切入(含 Nagel 對照)**:Build the composite mispricing score, double-sort mispricing × IVOL, verify IVOL→low-return only among overpriced names and →high among underpriced. Nagel controls it MUST beat: (1) 1/σ² vol management — since the variable IS IVOL, the mispricing-CONDITIONED spread must beat a plain vol-managed / low-vol tilt or it is low-vol repackaged; (2) static exposure = a constantly-held low-IVOL basket; (3) placebo mispricing score. Pre-commit: because profit concentrates in the un-shortable overpriced leg, durable value = a GATE/moderator (which anomalies to trust, when) not a tradable L/S sleeve.

#### dellavigna_pollet_2009_friday_inattention — DellaVigna & Pollet (2009) · ~1500 引用 · 「Investor Inattention and Friday Earnings Announcements」
- **主張 / 與我方關聯**:Friday earnings announcements get a ~15% weaker immediate response, ~70% larger post-announcement drift, and 8% lower volume — weekend distraction delays incorporation of the news. → A free, clean, near-exogenous attention experiment: same PEAD signal but the DELAY is mechanically larger on Fridays. Gives an attention MODERATOR on PEAD (bernard_thomas_1990_pead already in the list) that says where drift-based selection should concentrate.
- **可測性(免費資料)**:YES, fully (best-in-class fit). Earnings-announcement dates + SUE from EDGAR PIT quarterly filings (8-K/10-Q dates); weekday is free; returns from OHLCV; PIT OK; cost $0. Caveat: EDGAR filing timestamp can lag the actual press release by hours/days — must reconcile announcement vs filing date; large-cap sample has relatively few Friday reporters.
- **TR 切入(含 Nagel 對照)**:Build SUE-sorted PEAD book; interact drift with Friday vs non-Friday announcements. Nagel controls: (1) static exposure = a constant SUE tilt — the Friday-conditioned INCREMENT must beat plain PEAD (itself weak in large caps); (2) 1/σ² vol management (drift ≠ vol timing); (3) placebo weekday relabeling → interaction vanishes. Pre-commit: if the Friday increment is insignificant in our large-cap PIT universe, verdict = inattention effect too small at our breadth/seat.

#### frazzini_2006_disposition_underreaction — Frazzini (2006) · ~1500 引用 · 「The Disposition Effect and Underreaction to News」
- **主張 / 與我方關聯**:The disposition effect creates underreaction: post-announcement drift is strongest when the capital-gains overhang and the news share the SAME sign (winners with good news / losers with bad news drift most); an event strategy earns ~200 bps/mo alpha. → Bridges two papers ALREADY in the ledger — grinblatt_han_2005 (capital-gains overhang) and bernard_thomas_1990_pead — into one conditional signal (CGO-conditioned PEAD). Says drift-based selection pays most where overhang and news align; free via the Grinblatt-Han CGO proxy.
- **可測性(免費資料)**:YES/PARTIAL. Frazzini's original reference price uses mutual-fund holdings (13F, quarterly, free via EDGAR but coarse). The cleaner free path = Grinblatt-Han turnover-weighted CGO from price+volume (already buildable in our stack) × SUE from EDGAR earnings. PIT OK; cost $0. Caveat: the CGO proxy differs from a holdings-based reference price; large-cap seat.
- **TR 切入(含 Nagel 對照)**:Compute CGO (Grinblatt-Han), interact with SUE-signed earnings surprise; test same-sign (CGO·news>0) drift >> opposite-sign. Nagel controls: (1) static exposure = plain PEAD and plain CGO/momentum tilts — the INTERACTION must beat BOTH parents (else it's just momentum+PEAD additivity); (2) 1/σ² vol management; (3) placebo CGO sign. Pre-commit: if same-sign drift is merely plain PEAD among past-winners, verdict = momentum×PEAD overlap, not incremental disposition alpha.

#### campbell_yogo_2006_efficient_tests — Campbell & Yogo (2006) · ~1500 引用 · 「Efficient Tests of Stock Return Predictability」
- **主張 / 與我方關聯**:當預測子高度持續且其創新與報酬創新相關時,標準 t 檢定 size 嚴重失真;作者用局部單根漸近建構 Bonferroni Q 檢定,得到 D/P、E/P 在正確 size 下對報酬仍具(較弱但顯著)預測力。 → 這是把估值比擇時做對的統計地基:我們一旦用 D/P、CAPE(cs98 已在名單)做市場迴歸,必須用它避免『假預測性』。與已在名單的 Stambaugh(1999)、Clark-West(2007)互補,是自我打臉防線的一環。
- **可測性(免費資料)**:yes — 純方法論,只需既有指數報酬+持續預測子序列。PIT 佳。成本 $0(需實作 Q-test,statsmodels 無現成但可寫)。
- **TR 切入(含 Nagel 對照)**:把 Campbell-Yogo Q-test 加入 fabric 的預測性檢定工具箱,對每個時序擇時訊號(D/P、CAPE、term spread)輸出『size 校正後是否顯著』;作為 gate:任何擇時 sleeve 若在 Q-test 下不顯著即不得升格。它本身非交易策略,而是給所有市場擇時 TR 的對照門檻(必須先通過它,才允許與 buy-and-hold / 1/σ² / 隨機進場比 Sharpe)。

#### datar-naik-radcliffe1998-turnover — Datar, Naik & Radcliffe (1998) · ~1500 引用 · 「Liquidity and Stock Returns: An Alternative Test」
- **主張 / 與我方關聯**:Cross-sectional expected returns decrease in turnover (low-turnover = illiquid = higher required return), robust to size, book-to-market and beta; turnover is a clean, continuously available liquidity proxy. → A liquidity premium built from a FLOW (turnover) rather than a COST (spread) or IMPACT (Amihud) measure — a third, distinct axis. Turnover = OHLCV volume / EDGAR shares outstanding, both free and PIT. Complements Amihud level and gives a natural moderator to overlay on momentum/quality.
- **可測性(免費資料)**:yes. Turnover = daily $ or share volume (OHLCV) / shares outstanding (EDGAR, PIT-aligned to filing date); monthly aggregation; cost ~$0. Caveat: Nasdaq double-counting of dealer volume distorts levels — use NYSE-consistent handling or rank within venue; large-cap survivorship universe compresses the turnover spread (mis-seat toward small caps).
- **TR 切入(含 Nagel 對照)**:Low-minus-high turnover decile L/S + low-turnover long-only tilt, PIT shares from EDGAR. Nagel gauntlet: (1) static exposure — is the turnover premium just an inverted size/Amihud tilt? Neutralize and check residual; (2) 1/σ² vol-management — turnover co-moves with volatility, require the tilt to beat Moreira-Muir with alpha t≥2 and beat Cederburg static B&H on Calmar; (3) random-entry null. Pre-commit: likely PARTIAL (largely subsumed by size/illiquidity level in a liquid mega-cap seat) — a 'right effect, wrong habitat' teaching case.

#### hou-moskowitz2005-pricedelay — Hou & Moskowitz (2005) · ~1500 引用 · 「Market Frictions, Price Delay, and the Cross-Section of Expected Returns」
- **主張 / 與我方關聯**:Stocks whose prices respond with a lag to market-wide information (high 'delay', measured by the incremental R² of lagged market returns in weekly regressions) earn a large premium (~5-12%/yr) not explained by size, liquidity, or standard microstructure controls; delay proxies for an under-arbitraged friction. → A friction premium constructed ENTIRELY from returns (weekly returns of a stock vs contemporaneous+lagged market) — no shares, no volume, no quotes needed. Cleanly buildable, and conceptually links our failed lead-lag/reversal intuitions to a priced friction rather than a tradable inefficiency.
- **可測性(免費資料)**:yes (fully). Weekly returns from daily OHLCV; regress r_i on contemporaneous + 4 lagged market returns; delay = 1 - R²(contemp-only)/R²(full); PIT clean; cost ~$0.
- **TR 切入(含 Nagel 對照)**:Sort on the D1 delay measure, high-delay-minus-low decile L/S + high-delay long-only tilt. Nagel gauntlet: (1) static exposure — high-delay names are typically small/illiquid, so neutralize a static size+Amihud tilt and test the delay residual; (2) 1/σ² Moreira-Muir vol-management control, require alpha t≥2; (3) random-entry null. Pre-commit: in a 610-name liquid universe delay dispersion is small, expect PARTIAL — but it is a pure-return friction we have literally never tested.

#### hxz-2020-replicating-anomalies — Hou, Xue & Zhang (2020) · ~1400 引用 · 「Replicating Anomalies」
- **主張 / 與我方關聯**:以 NYSE breakpoint + 市值加權 + 排除微型股的一致協定重測 452 個已發表異常，約 65% 無法複製顯著性——多數 zoo 是微型股/等權/data-mining 假象。 → 對一個以『打臉/負結果』為主軸的專案是黃金方法論：直接支撐我方『廣宇宙因子近死』(docs/10)與嚴謹 breakpoint 慣例，並提供一份『哪些異常是真的』的可信名單。
- **可測性(免費資料)**:yes — 複製協定(NYSE breakpoint、VW、去微型股)可直接套用為我方 factor gate 的正式版。
- **TR 切入(含 Nagel 對照)**:把 HXZ 複製協定(NYSE bp + VW + 去微型股)設為 factor_determination 閘門的正式版，重跑 docs/09 因子；對照『等權/全樣本 breakpoint』量化多少 edge 是方法論假象——這是強化 shuffle/隨機分位紀律的 meta 對照。

#### kelly-jiang-2014-tail-risk — Kelly & Jiang (2014) · ~1400 引用 · 「Tail Risk and Asset Prices」
- **主張 / 與我方關聯**:A common tail-risk index estimated from the cross-section of firms' extreme daily returns (Hill-type power-law tail) is persistent, spikes in crises, forecasts market returns, and its cross-sectional loading (tail beta) earns a large premium. → Uniquely suited to this project because the tail measure is built FROM the cross-section of free daily returns (not from options) — it converts the universe the project already has into a systematic crash-risk factor. Gives both a market-timing signal (tail index level) and a stock-selection sort (tail beta), squarely on the derivatives/tail subdomain but with $0 data.
- **可測性(免費資料)**:yes. Monthly common tail index = Hill estimator on pooled cross-sectional returns below a dynamic threshold; tail beta = time-series regression of each stock's excess return on tail-index innovations. All from free daily OHLCV cross-section + index. PIT OK (trailing). Cost ~$0. Caveat: estimator noisier on ~500-name universe than on CRSP thousands.
- **TR 切入(含 Nagel 對照)**:TR: build the Kelly-Jiang tail index from 610-name daily cross-section, estimate per-stock tail beta, quintile L/S. Nagel controls: (a) 1/σ² vol management — tail spikes ARE high-vol episodes, so the tail-beta premium must beat a vol-managed book (this is the hardest control, since tail risk and volatility timing coincide); (b) static exposure of the high-tail-beta basket; (c) placebo tail index from a shuffled cross-section. Also test the tail-index LEVEL as a market-timing overlay vs Moreira-Muir 1/σ². Pre-commit: real tail premium only if it beats vol-managed control with alpha-t≥2; else = vol-timing relabelled.

#### baker-bradley-wurgler-2011-lowvol-limits — Baker, Bradley & Wurgler (2011) · ~1300 引用 · 「Benchmarks as Limits to Arbitrage: Understanding the Low-Volatility Anomaly」
- **主張 / 與我方關聯**:低波動/低 beta 股風險調整後報酬較高；成因是『基準相對績效約束下的套利限制』——機構受託人不能用槓桿，只能追高 beta，使低波股長期被低估。 → 為 low-vol/BAB 提供機制，且直接預測『何時會反轉』：當宇宙全是高 beta 成長股時機制可能失效——正對應我方 TR-06 BAB 反轉與 docs/09 lowvol 反轉。
- **可測性(免費資料)**:yes — 低波/低 beta 組合由 OHLCV 建。
- **TR 切入(含 Nagel 對照)**:低波 L/S 與 BAB(TR-06 已測反轉 Sharpe −0.79)並跑，對照 shuffle 與 FF5 靜態 beta；檢驗『基準約束』敘事是否在我方 47 檔全高 beta 科技宇宙註定反轉，須 beat 隨機分位與 1/σ² vol-managed。

#### barroso_santaclara_2015_momentum_moments — Barroso & Santa-Clara (2015) · ~1300 引用 · 「Momentum Has Its Moments」
- **主張 / 與我方關聯**:Scaling the winners-minus-losers momentum portfolio by its trailing 6-month realized variance removes the fat left tail (2009 crash), stabilizes the strategy at constant volatility, and raises Sharpe from ~0.5 to ~0.9 without look-ahead. → This paper IS essentially the 1/sigma^2 Nagel control we already impose, so replicating it fixes the benchmark: every cross-sectional momentum TR must be shown to add value OVER constant-vol-scaled WML, not just over raw WML.
- **可測性(免費資料)**:yes, fully. WML factor buildable from free daily OHLCV (503+ universe); trailing realized variance from daily returns; PIT trivial (only past returns). Cost $0. This is the single most buildable risk-managed momentum spec in the set.
- **TR 切入(含 Nagel 對照)**:Build raw WML then variance-scaled WML on our 503-universe; the paper itself is the 1/sigma^2 control, so the TR frames it as the BENCHMARK: any candidate momentum variant (residual, intermediate, market-state-timed) must beat variance-scaled WML net-of-cost, and variance-scaling must beat both static full-exposure WML (Cederburg) and a random-entry placebo. Pre-commit: if scaling only rescales risk without net-cost Sharpe gain on our large-cap seat, momentum stays FAILED.

#### hirshleifer_lim_teoh_2009_distraction — Hirshleifer, Lim & Teoh (2009) · ~1300 引用 · 「Driven to Distraction: Extraneous Events and Underreaction to Earnings News」
- **主張 / 與我方關聯**:When many other firms announce earnings the same day, a firm's own surprise gets a weaker immediate reaction and much stronger post-announcement drift; industry-unrelated concurrent news distracts more than related news. → Like DellaVigna-Pollet but the attention scarcity is a market-level COUNT, fully reconstructable from filing dates — a second free moderator that pinpoints high-distraction days as where drift-based selection pays; bears directly on our dead-PEAD/momentum seat.
- **可測性(免費資料)**:YES, fully. Same-day announcement count from an EDGAR filing-date panel (count of daily 10-Q/8-K earnings filings market-wide); SUE + returns free; PIT OK; cost $0. Same filing-date-vs-press-release timing caveat as DP; large-cap breadth caveat.
- **TR 切入(含 Nagel 對照)**:Compute daily market-wide earnings-announcement counts, interact PEAD drift with the count (high-distraction days). Nagel controls: (1) static exposure = constant SUE tilt — distraction increment must beat plain PEAD; (2) 1/σ² vol management; (3) placebo distraction count (shuffle days). Pre-commit: PASSED only if high-distraction drift beats plain PEAD after costs; else = attention effect below our seat's breadth.

#### brandt-santaclara-valkanov-2009-ppp — Brandt, Santa-Clara & Valkanov (2009) · ~1300 引用 · 「Parametric Portfolio Policies: Exploiting Characteristics in the Cross-Section of Equity Returns」
- **主張 / 與我方關聯**:不預測個股報酬，而把組合權重直接參數化為(size、B/M、動量)特徵的線性函數，估少數係數即最大化投資人效用;樣本外勝 value-weight 與樸素因子組合，且天然含交易成本控制。 → characteristics-managed portfolio 的奠基方法，且參數極少(抗過擬合)——正是 $0 免費資料下把 EDGAR+價量特徵轉成組合的穩健框架，避開 GKX 式高維過擬合(本專案 TR-08 的教訓)。
- **可測性(免費資料)**:yes — size/B-M/動量特徵皆日線+EDGAR 可得;效用最大化係數估計計算量低;PIT walk-forward 可行;成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 實作 PPP(特徵=GP、應計、動量、size)於本宇宙 walk-forward。必須打敗:(a) 1/N 與 value-weight 靜態組合，(b) 樸素等權因子 tilt，(c) 隨機權重擾動;並用 PBO/CSCV 確認少參數是否真的抗過擬合。

#### neely_rapach_tu_zhou_2014_technical — Neely, Rapach, Tu & Zhou (2014) · ~1200 引用 · 「Forecasting the Equity Risk Premium: The Role of Technical Indicators」
- **主張 / 與我方關聯**:技術指標(MA 交叉、時序動量、量能 OBV)對股權溢酬的樣本外預測力,與 Goyal-Welch 型總經預測子相當且互補;把兩類訊號用主成分/組合結合,顯著提升 OOS R² 與擇時效用,尤其技術訊號在景氣衰退早期更敏感。 → 這是把我們既有的 OHLCV 技術訊號正式接進市場擇時預測框架的旗艦文獻,且明確與已在名單的 Rapach-Strauss-Zhou 2010(組合預測)、Campbell-Thompson 約束同源;正好測試『純價量技術能否為擇時貢獻增量』。
- **可測性(免費資料)**:yes — 技術指標全由指數 OHLCV(含量能)建;總經預測子用 Goyal 公開資料集。PIT 佳(月頻)。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:重建 14 技術 + 14 總經預測子,對 SPY 跑主成分組合預測(對照單純均值與 RSZ 等權組合),再轉成擇時部位;必須先打敗 buy-and-hold 靜態曝險、Moreira-Muir 1/σ² 波動管理與隨機進場。關鍵消融:技術訊號的增量是否只是變相的 1/σ²/趨勢曝險(用 Nagel 對照隔離),或真有正交資訊。

#### ledoit-wolf-2008-sharpe — Ledoit & Wolf (2008) · ~1200 引用 · 「Robust Performance Hypothesis Testing with the Sharpe Ratio」
- **主張 / 與我方關聯**:在肥尾與自相關下,用 HAC + 平穩自助(Politis-Romano)建兩策略 Sharpe 差的穩健檢定,取代失效的 Jobson-Korkie/Memmel 常態假設。 → 我們一天到晚宣稱『combo Sharpe > VOO』『多 sleeve > 單 sleeve』——LW08 是判斷這些 Sharpe 差是否只是噪音的正確工具,直接進 scorecard。
- **可測性(免費資料)**:yes — 純檢定,套既有策略/基準日報酬;無新資料;需自助抽樣(小算力)。
- **TR 切入(含 Nagel 對照)**:TR:對『旗艦 vs VOO』『多 sleeve vs 單 sleeve』跑 LW08 Sharpe 差檢定;Nagel 對照必打敗=1/σ² 波動管理與隨機進場——唯有旗艦 Sharpe 在自助檢定下顯著勝控制,才記為真績效差而非抽樣運氣。

#### boyer-mitton-vorkink-2010-expected-idio-skewness — Boyer, Mitton & Vorkink (2010) · ~1200 引用 · 「Expected Idiosyncratic Skewness」
- **主張 / 與我方關聯**:Stocks with high EXPECTED idiosyncratic skewness (forecast from a cross-sectional regression of realized idio-skewness on lagged firm characteristics) earn low subsequent returns — investors overpay for lottery-like positive skew. It is the forward-looking, tradable cousin of the MAX effect (already listed). → Directly buildable stock-selection signal in the skewness family, complementary to the already-listed Bali-Cakici-Whitelaw MAX. The characteristic-regression forecast avoids the look-ahead problem of realized skewness and is exactly the kind of $0-data cross-sectional predictor the project can test; also a clean test of whether 'lottery demand' survives in a large-cap survivorship universe.
- **可測性(免費資料)**:yes/partial. Realized idio-skewness = skew of daily FF3 residuals over ~60d (free; FF factors via pandas_datareader). Forecasting regression uses lagged momentum, turnover (volume/shares — shares from EDGAR PIT), idio-vol, industry — all free. PIT clean (expanding regression). Cost ~$0.
- **TR 切入(含 Nagel 對照)**:TR: replicate the expected-idio-skew forecast, decile-sort, short high / long low expected skew, net cost. Nagel controls: (a) static exposure of the low-skew basket (is it just a low-vol/low-beta tilt?); (b) 1/σ² vol management (expected idio-skew correlates with idio-vol → must beat a vol-managed control); (c) placebo — random skew forecast → spread vanishes. Subsume vs MAX, IVOL, size. Pre-commit: PASS only if the forecast adds L/S alpha beyond MAX + IVOL and beats vol-managed control; else = lottery/vol repackaging.

#### lewellen_2004_financial_ratios — Lewellen (2004) · ~1100 引用 · 「Predicting Returns with Financial Ratios」
- **主張 / 與我方關聯**:股利殖利率等高持續性估值比確實有樣本內預測力,但因回歸元近單根,Stambaugh 偏誤與有限樣本使 t 值虛高;作者提出以已知的高自相關結構為條件的偏誤校正檢定,結論是 D/P 的預測力比 Stambaugh(1999)悲觀結論所暗示的更穩健。 → 直接關乎我們是否該用 D/P、E/P、B/M 對 SPY/QQQ 擇時;它是 Stambaugh 偏誤(已在名單 stambaugh99_bias)與 Campbell-Thompson 約束之間缺的一環,提供一個具體、可實作的偏誤校正推論法。
- **可測性(免費資料)**:yes — 指數長歷史(Shiller 免費 1871-)提供 D/P、E/P;B/M 可由 EDGAR 總股權/市值近似。PIT:市場級估值比修正極小,月頻對齊乾淨。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:對 SPY 跑 D/P→未來 12M 超額報酬的擴張窗預測,同時報 (a) 原始 t、(b) Lewellen 偏誤校正 t、(c) Stambaugh/Kendall 校正 t 三者差距;再把符號正確的預測轉成擇時部位,對照組必須先打敗 buy-and-hold 靜態曝險(Cederburg)、1/σ² 波動管理(Moreira-Muir),以及同『在市時間比例』的隨機進場。判 PASS 需 OOS R²>0(Campbell-Thompson 基準)且淨成本後 Sharpe 勝三個對照。

#### ali_hwang_trombley_2003_arbitrage_risk_bm — Ali, Hwang & Trombley (2003) · ~1000 引用 · 「Arbitrage Risk and the Book-to-Market Anomaly」
- **主張 / 與我方關聯**:The value (B/M) premium is larger among stocks with higher idiosyncratic volatility, higher transaction costs, and lower investor sophistication — supporting the Shleifer-Vishny thesis that arbitrage-return volatility deters arbitrage and is why the anomaly survives. → Our value factor is FAILED (docs/09/10, the lost decade). AHT says the premium lives specifically in high-arbitrage-risk names, so our broad low-arb-risk large-cap seat is exactly where value should be weakest — re-seats the dead-value verdict and operationalizes limits-to-arb as a within-anomaly moderator. Fully free.
- **可測性(免費資料)**:YES, fully. B/M from EDGAR book equity + price; idio vol from OHLCV+FF3 residuals. PIT OK; cost $0. Caveat: the large-cap survivorship universe is a LOW-arbitrage-risk seat — precisely where AHT predicts the WEAKEST value premium (likely confirms 'dead value here, alive in high-idio-vol small caps').
- **TR 切入(含 Nagel 對照)**:Double-sort B/M × idio-vol; test the value premium rising monotonically in idio vol. Nagel controls: (1) static exposure — is 'high-idio-vol value' just small/distressed beta? neutralize vs size + a constant high-vol basket; (2) 1/σ² vol management; (3) placebo arb-risk rank. Pre-commit: if the high-arb-risk value premium is subsumed by size/distress beta, verdict = value = small/distress repackaged (consistent with our lost decade); durable use = a limits-to-arb gate on which anomalies to expect in our low-arb-risk seat.

#### pontiff-woodgate-2008-share-issuance — Pontiff & Woodgate (2008) · ~950 引用 · 「Share Issuance and Cross-Sectional Returns」
- **主張 / 與我方關聯**:淨股票發行(1-5 年 split-adjusted 股數變動)強力負向預測橫斷面報酬；1970 後其預測力可比甚至強於 size/BM/動量，且在大型股仍顯著。 → net-issuance 子領域的錨，且是少數在大型股(我方座位)仍強的異常——高潛在存活率；發行/回購是乾淨的公司行為訊號。
- **可測性(免費資料)**:yes — split-adjusted 流通股數 by EDGAR(封面/財報股數)，PIT。
- **TR 切入(含 Nagel 對照)**:net-issuance decile L/S(低發行−高發行)，市場中性，對照 shuffle 與 FF5 靜態 beta；檢驗發行因子在大型股是否存活、beat 隨機分位——若存活即為我方少數可入旗艦的新腿。

#### novymarx_2012_intermediate_momentum — Novy-Marx (2012) · ~950 引用 · 「Is Momentum Really Momentum?」
- **主張 / 與我方關聯**:Momentum profits come almost entirely from intermediate-horizon past performance (months t-12 to t-7); the recent-past (t-6 to t-2) leg has little independent predictive power, so standard 12-2 momentum is a blend dominated by its older half. → Directly changes the signal construction of every momentum sleeve we test, and offers a cheap horizon-decomposition that could reopen our dead large-cap momentum in a form we never tried (intermediate-only ranking).
- **可測性(免費資料)**:yes, fully. Only needs price history to form t-12..t-7 vs t-6..t-2 legs; pure free daily OHLCV; PIT trivial; cost $0.
- **TR 切入(含 Nagel 對照)**:Decompose momentum into intermediate and recent legs on the 503 universe, horse-race the two, and test the intermediate-only sort. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso) as the hardest control, (2) static exposure to the intermediate-winner basket, (3) random-decile placebo. PASSED only if intermediate-leg momentum beats variance-scaled plain momentum net of cost.

#### nagel2012-evaporating-liquidity — Nagel (2012) · ~900 引用 · 「Evaporating Liquidity」
- **主張 / 與我方關聯**:Returns to short-term reversal strategies are compensation for supplying liquidity; their expected returns are strongly time-varying and predictably high when the VIX is high (liquidity scarce), so the reversal premium 'evaporates' and spikes with volatility. → Directly connects the short-term-reversal factor (which our factor_search found is destroyed by costs at daily frequency) to a liquidity-provision RISK premium, and — critically — it is essentially a VOLATILITY-TIMED strategy, making it the perfect adversarial case for the Nagel-control lineage (this IS a Nagel paper). Tests whether reversal alpha is anything more than 1/σ² vol-timing wearing a microstructure costume.
- **可測性(免費資料)**:yes. Daily 5-day contrarian portfolios from OHLCV; VIX/realized-vol conditioning free from index history/FRED; PIT clean; cost ~$0. Honest caveat: reversal is turnover-heavy — the gross/net gap (our cost wall) is the whole story, so this is as much a cost TR as an alpha TR.
- **TR 切入(含 Nagel 對照)**:Build the daily reversal strategy on the liquid universe, condition expected returns on VIX/realized vol, report GROSS vs NET (10bps/side). Nagel gauntlet is native here: (1) the paper's own VIX-conditioning IS a vol-timing signal, so the acid test is whether VIX-timed reversal beats a plain Moreira-Muir 1/σ² overlay on the market — if not, judge 'reversal-liquidity premium = vol-timing in disguise'; (2) static B&H (Cederburg) on Calmar; (3) random-entry null on the reversal legs. Pre-commit: net-of-cost the reversal premium likely dies in mega-caps (cost wall), teaching that a real liquidity-provision premium is uncapturable at $0 execution — a G-S-consistent result.

#### ferreira_santaclara_2011_sum_of_parts — Ferreira & Santa-Clara (2011) · ~850 引用 · 「Forecasting Stock Market Returns: The Sum of the Parts Is More than the Whole」
- **主張 / 與我方關聯**:不要直接迴歸總報酬,而把它拆成 D/P + 盈餘成長 + P/E 成長三塊分別預測(P/E 成長設為 0 或均值回歸),相加後的 OOS R² 遠勝整體迴歸與歷史均值,擇時效用可觀且穩健。 → 提供一個低參數、抗過擬合的市場擇時法,直接對撞 Welch-Goyal 的 OOS 悲觀論;且輸入(D/P、盈餘)全在我們免費資料範圍。是『組合/分解預測』sub-area 中最實作友善的一篇。
- **可測性(免費資料)**:yes — Shiller 免費資料含指數價格、股利、盈餘,可建三分量。PIT:盈餘為已實現(需注意報告落差,用 trailing)。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:在 SPY 上實作 sum-of-the-parts 預測(D/P + 盈餘成長,P/E 成長=0),對照 (a) 歷史均值(Campbell-Thompson 基準)、(b) 整體報酬單迴歸;轉成擇時後須先打敗 buy-and-hold、1/σ² 波動管理與隨機進場。判 PASS 需 OOS R²>0 且 net-of-cost 擇時 Sharpe 勝三對照;檢驗其相對整體迴歸的優勢在我們樣本是否成立。

#### da_gurun_warachka_2014_frog_in_pan — Da, Gurun & Warachka (2014) · ~800 引用 · 「Frog in the Pan: Continuous Information and Momentum」
- **主張 / 與我方關聯**:Momentum is much stronger and does not reverse for stocks whose formation-period return accrued through continuous information (many small same-signed daily returns, low 'information discreteness'), because investors underreact to gradual news; jumpy stocks show weak, reversing momentum. → Gives a fully free, novel signal (information discreteness computed from daily return signs) that conditions momentum, and could resurrect large-cap momentum in the continuous-information subset - a habitat we never isolated.
- **可測性(免費資料)**:yes, fully. Information discreteness = sign(cumulative return) x (%neg days - %pos days) over the formation window, computed purely from free daily OHLCV; PIT trivial; cost $0. One of the cheapest high-insight tests in the set.
- **TR 切入(含 Nagel 對照)**:Compute information discreteness over the 12-1 window, double-sort momentum x ID on the 503 universe, test continuous-information momentum. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso) as hardest control, (2) static exposure to the continuous-winner basket, (3) placebo ID from shuffled daily-return signs -> conditioning must vanish. PASSED only if the continuous-info momentum spread beats vol-managed momentum net of cost.

#### bgln-2015-deflating-profitability — Ball, Gerakos, Linnainmaa & Nikolaev (2015) · ~750 引用 · 「Deflating Profitability」
- **主張 / 與我方關聯**:以『營業利潤 / 帳面權益』(deflate 掉非營業與財務項)比 Novy-Marx 的 gross profitability/資產更能預測橫斷面報酬；profitability 溢酬對『用哪個利潤定義與分母』高度敏感。 → 直接校準我方唯一存活因子(GP)——測『更乾淨的 profitability 定義是否再抬 ICIR』，是把 docs/10 GP 從 modest 推向更強的最低成本升級。
- **可測性(免費資料)**:yes — gross / operating / net 多種 profitability 變體(各種分母)皆 EDGAR 可建。
- **TR 切入(含 Nagel 對照)**:並排跑 gross / operating(book-equity deflated)/ net 三版 profitability L/S，對照現行 GP 基準與 shuffle；量哪個 deflator 在我方座位 ICIR 最高、是否 beat 隨機分位與 FF5 靜態 beta。

#### israel_moskowitz_2013_shorting_size_time — Israel & Moskowitz (2013) · ~750 引用 · 「The Role of Shorting, Firm Size, and Time on Market Anomalies」
- **主張 / 與我方關聯**:For size, value, and momentum, the premia are NOT concentrated in the short leg and are largely present in large-cap, long-only implementations; momentum in particular has a substantial long-side component and works across size groups, contrary to the 'it's all in hard-to-short small caps' view. → Directly speaks to our long-only, large-cap, $0 seat: it quantifies how much of the momentum premium is reachable long-only in big stocks, calibrating whether our null is a true failure or a leg/size artifact.
- **可測性(免費資料)**:yes, fully. Long-only and long-short leg returns across size terciles from free daily OHLCV; size from price x shares (EDGAR/free); PIT fine; cost $0.
- **TR 切入(含 Nagel 對照)**:Split momentum (and our GP-quality/value sleeves) into long-leg-only vs full L/S across size terciles on the 503 universe; measure how much premium is long-side/large-cap reachable. Nagel controls it must beat: (1) static long-only exposure to the winner basket (Cederburg) - is the 'long leg' anything beyond held beta?, (2) 1/sigma^2 vol management, (3) random-decile placebo. PASSED bar: a long-only large-cap momentum leg delivers net-cost alpha over static winner-basket exposure.

#### asness-frazzini-2013-devil-hml — Asness & Frazzini (2013) · ~700 引用 · 「The Devil in HML's Details」
- **主張 / 與我方關聯**:用『當期價格』而非年度落後價格建 book-to-market，HML 溢酬更大、與動量負相關更強——估值時點這個建構細節實質改變結論。 → 直接關係我方 value-death 判定：可能是用了落後價格的偽陰。是高槓桿、低成本的『建構是否害死 value』檢驗。
- **可測性(免費資料)**:yes — 需月更價格 + 落後帳面權益(EDGAR)，皆免費。
- **TR 切入(含 Nagel 對照)**:並排跑『落後價格 B/M』vs『當期價格 B/M』兩版 L/S，市場中性，對照 shuffle；若當期價格版在 2015-24 仍死則坐實 value 死，否則揭露 docs/09 的建構偽陰。須 beat 隨機分位與 FF5 靜態 beta。

#### heston_sadka_2008_seasonality — Heston & Sadka (2008) · ~700 引用 · 「Seasonality in the Cross-Section of Stock Returns」
- **主張 / 與我方關聯**:Stocks that historically outperformed in a given calendar month continue to outperform in that same month years later; this same-month seasonal effect is large, persists to 20 annual lags, and is distinct from size, momentum, and industry. → A completely orthogonal, free, cross-sectional signal we have never tested, and a natural diagnostic partner to momentum (seasonal continuation vs price continuation) that could add an uncorrelated sleeve to the flagship combo.
- **可測性(免費資料)**:yes, fully. Signal = average historical return in the target calendar month per stock, from free daily/monthly returns; PIT trivial (only past same-month returns); cost $0.
- **TR 切入(含 Nagel 對照)**:Build same-calendar-month average-return ranks, form monthly deciles on 503 universe, net-of-cost L/S. Nagel controls it must beat: (1) static exposure to the seasonal-winner basket (is it just a stable-industry tilt?), (2) 1/sigma^2 vol management, (3) random-month placebo -> reshuffle month labels and the seasonal spread must vanish. Also subsume-test vs momentum + FF + industry. PASSED only if net-cost seasonal L/S survives value-weighting and beats the placebo.

#### faber_2007_tactical_asset_allocation — Faber (2007) · ~700 引用 · 「A Quantitative Approach to Tactical Asset Allocation」
- **主張 / 與我方關聯**:一條極簡規則——收盤價高於 10 月 SMA 則持有、否則轉現金——能在幾乎不損報酬下大幅降低波動與最大回撤,尤其閃避大空頭;是被廣泛引用的趨勢擇時基準。 → 這是零工程、可立即重建的市場擇時規則,且與本專案已測的『200-SMA/HMM gate 皆 FAILED』(docs/09)正面對照——是檢驗『趨勢擇時到底是真降風險還是隨機進場也一樣』的乾淨測試場。
- **可測性(免費資料)**:yes — 只需指數/ETF 月末收盤與 200 日 SMA。PIT 完美。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:對 SPY(及股債商 ETF 籃)實作 10 月 SMA 擇時,嚴格比對三個 Nagel 對照:(1)buy-and-hold 靜態曝險(Cederburg,含成本)、(2)1/σ² 波動管理(Moreira-Muir),(3)同在市時間比例的隨機進場 1,000 次分布。判 PASS 需 SMA 規則的風險調整後(Sharpe/Calmar,淨換手成本)顯著落在隨機進場分布右尾且勝 buy-and-hold 與 1/σ²;否則歸類為『降 beta 曝險而非擇時 alpha』。

#### blitz_huij_martens_2011_residual_momentum — Blitz, Huij & Martens (2011) · ~650 引用 · 「Residual Momentum」
- **主張 / 與我方關聯**:Ranking stocks on the trailing 12-1 return of their Fama-French three-factor RESIDUALS (scaled by residual volatility) earns momentum-like premia with roughly half the volatility and far smaller crashes, because it strips out the dynamic factor bets that cause momentum's tail. → Offers a factor-neutral momentum that may survive where our raw large-cap momentum died, and its residualization is a different edge from vol-scaling, so it is a genuine test of whether momentum alpha exists once beta bets are removed.
- **可測性(免費資料)**:yes, fully. Needs FF3 factors (free from Ken French library) to compute residuals, then momentum on residuals; free daily OHLCV for stock returns; PIT fine (rolling regression on past window); cost $0.
- **TR 切入(含 Nagel 對照)**:Estimate rolling 36-month FF3 residuals, form 12-1 residual-momentum deciles, net-of-cost L/S on 503 universe. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled plain WML (Barroso) - is residualization anything more than vol-management?, (2) static exposure to the residual-winner basket, (3) placebo residuals from shuffled factor loadings. PASSED bar: residual momentum beats variance-scaled raw momentum AND is not subsumed by FF+quality.

### C.2 第二波 — 可測但需額外建構 / 部分資料

需要多做一點資料工程(建產業分類、指數長歷史、公開附錄資料集)或只能部分重建。

#### hansen-gmm-1982 — Hansen (1982) · ~27000 引用 · 「Large Sample Properties of Generalized Method of Moments Estimators」
- **主張 / 與我方關聯**:用矩條件 E[m·R]=1 可在不假設分布下估 SDF 參數；過度識別的 J 統計量檢定『因子是否共同定價測試資產』，是 GRS 在 SDF 語言下、對非常態/異質更穩健的推廣。 → 把因子模型檢定從 β-定價(GRS)升到 SDF/GMM 語言，可在不靠常態假設下檢定我們的因子/sleeve 是否定價截面，並自然容納條件矩(波動管理因子)。是 factor-model tests 與 GMM 兩個點名支柱的交集正典。
- **可測性(免費資料)**:partial→yes — 檢定本身只需免費因子+測試組合月報酬，statsmodels/linearmodels 或手刻 GMM 皆可；point-in-time 用 EDGAR 對齊。標 partial 僅因實作與最適加權矩陣估計比 GRS 重、樣本短時 J 檢定小樣本偏誤需 bootstrap；無需日內/選擇權。
- **TR 切入(含 Nagel 對照)**:TR：估線性 SDF m=1−b'f，對 5 sleeve/分位組合跑 GMM J 檢定，對照 GRS。Nagel 對照直接進矩條件：SDF 內含 Moreira-Muir 1/σ² 波動管理因子與靜態市場因子後，若 J 檢定無法拒絕(模型定價得了 sleeve) → 判 sleeve α = 波動管理/beta 可解釋；唯有含這些控制仍被 J 拒絕的殘差 α 才升格。

#### diebold-mariano-1995 — Diebold & Mariano (1995) · ~15000 引用 · 「Comparing Predictive Accuracy」
- **主張 / 與我方關聯**:給定任意損失函數，兩模型的 OOS 損失差序列做 HAC-穩健的均值為零檢定，即可判定預測力是否顯著不同——不需假設模型正確或巢狀。 → 當我們要說『模型 X 比波動管理/常數基準預測得更好』時，這是那句話的正式檢定。對波動預測(GARCH vs 已實現波動代理)與報酬擇時的模型選擇提供誠實裁決，補齊 forecast-evaluation 支柱的通用版(Clark-West 管巢狀，DM 管一般)。
- **可測性(免費資料)**:yes — 只需既有 OOS 預測序列(波動/報酬)+免費報酬；DM 統計量易實作(NW 標準誤)；point-in-time 不受影響；無需日內/選擇權。
- **TR 切入(含 Nagel 對照)**:TR：以 DM 檢定比較候選預測器 vs Nagel 基準的 OOS 損失。Nagel 對照即比較對象：候選波動/報酬預測必須 DM-顯著勝 (a) 1/σ² 波動管理隱含預測 與 (b) 常數/歷史均值(靜態)；巢狀情形改用 Clark-West。把 DM 接進 TR-04(VaR/波動)與 TR-17(擇時)，讓『我們的模型更準』永遠附一個 DM p 值而非目測。

#### shleifer_vishny_1997 — Shleifer & Vishny (1997) · ~9000 引用 · 「The Limits of Arbitrage」
- **主張 / 與我方關聯**:Real arbitrage is done by a few specialists deploying other people's capital; when mispricing widens they face redemptions precisely when the opportunity is best, so they cannot fully correct prices — arbitrage is weakest where fundamental/idiosyncratic risk and horizon mismatch are high. → The theoretical spine of this whole subdomain and a direct sibling of our G-S '$0 info cost -> $0 alpha' foundation. Reframes every behavioral anomaly as surviving only where arbitrage is costly, and supplies a cross-cutting moderator (idio-vol, illiquidity, horizon) to overlay on the other TRs.
- **可測性(免費資料)**:PARTIAL (indirect). Not a signal itself. Test its central prediction: anomaly magnitude increases in arbitrage-cost proxies (idiosyncratic vol per Pontiff, Amihud illiquidity, size) — all buildable from OHLCV + EDGAR, PIT OK. Cannot test the capital-flow/agency channel (needs fund-flow data -> no).
- **TR 切入(含 Nagel 對照)**:Meta-TR / conditioning study (not a standalone strategy): interact each buildable behavioral anomaly (De Bondt-Thaler reversal, CGO, sentiment-conditioned spread) with an arbitrage-cost composite (idio-vol + ILLIQ + size). Prediction: spreads monotonically larger in the high-arb-cost quintile. Nagel controls it must beat: (1) static exposure to the high-arb-cost basket alone — is the 'stronger anomaly' just the high-idio-vol / small-cap risk premium held long? (Cederburg); (2) 1/sigma^2 vol management (high-idio-vol names dominate — is it vol-timing?); (3) placebo arb-cost ranking. Honest verdict frame: likely confirms our only surviving alpha lives where costs eat it (G-S restated) -> value is explanatory, not tradable.

#### baker_wurgler_2006 — Baker & Wurgler (2006) · ~8000 引用 · 「Investor Sentiment and the Cross-Section of Stock Returns」
- **主張 / 與我方關聯**:Following high sentiment, speculative / hard-to-value stocks (small, young, high-vol, unprofitable, non-dividend, extreme growth or distress) earn LOW subsequent returns; low-sentiment periods reverse the pattern. → A regime/conditioning variable that could revive characteristics we found flat unconditionally (size, profitability); ties directly to our surviving GP-quality sleeve and to Markov/regime overlays — turns a dead unconditional sort into a conditional one.
- **可測性(免費資料)**:PARTIAL/YES. Characteristics (size, age, vol, profitability, dividend-payer, B/M) buildable from EDGAR + price. Sentiment index: Wurgler publishes the monthly BW index free (NYU site, ~through 2018) BUT it is FULL-SAMPLE PCA -> look-ahead baked into construction; a real point-in-time rebuild is hard (IPO first-day returns, equity share of issuance need extra data). Honest: descriptive test with published index = yes; clean PIT = partial.
- **TR 切入(含 Nagel 對照)**:Build a sentiment-sensitivity composite (size/age/vol/profitability/dividend), form L/S, and condition returns on lagged BW sentiment tercile. Nagel controls it must beat: (1) static unconditional exposure to the same characteristic — does sentiment-conditioning add over always-on holding? (Cederburg static); (2) 1/sigma^2 vol management — high-sentiment periods ~ high-vol periods, so prove the conditioning is not just inverse-vol timing (the SHARPEST control here); (3) placebo: random dates as fake sentiment states -> effect vanishes. Plus PIT honesty: re-run with a lag-only rebuilt proxy to see if look-ahead drove it. PASSED only if the sentiment-conditioned spread beats the vol-managed control and survives the PIT rebuild.

#### amihud-mendelson1986-spread — Amihud & Mendelson (1986) · ~7000 引用 · 「Asset Pricing and the Bid-Ask Spread (Journal of Financial Economics)」
- **主張 / 與我方關聯**:期望毛報酬隨相對買賣價差遞增且呈凹型(spread-return relation);高價差資產被長 holding-period 的 clientele 持有,攤銷交易成本。 → 選股用價差當 required-return 代理;凹型與 clientele 預測給『價差因子在長持有期組合更該被計入』的洞見。是 Amihud 2002 的理論母體。
- **可測性(免費資料)**:PARTIAL。原文用『報價』價差,我們沒有(免費日線無 bid/ask)。只能用估計價差(Roll / Corwin-Schultz / zero-return 比例)替代 → 測的是『估計價差-報酬關係』,非原始報價版本。Point-in-time OK。clientele/攤銷的凹型預測較難乾淨檢驗。
- **TR 切入(含 Nagel 對照)**:用估計價差(Corwin-Schultz 或 Roll)排序測 spread-return 關係與凹型。Nagel 對照:(1) 靜態曝險——價差溢酬扣掉靜態 size/Amihud level 傾斜後是否還在(高度共線,預期大半被吸收);(2) 隨機進場 null;(3) 凹型測試須對照『線性 size 傾斜』這個更簡單的形狀。因與 Amihud 2002 高度重疊,定位為 Amihud TR 的 robustness sleeve(不同估計器是否給同結論),而非獨立旗艦。

#### banz-1981-size — Banz (1981) · ~6500 引用 · 「The Relationship Between Return and Market Value of Common Stocks」
- **主張 / 與我方關聯**:小市值股橫斷面平均報酬顯著高於大市值，CAPM β 無法解釋——size effect 的原始證據，且效應集中在最小的市值分位。 → 所有 size tilt 的根源；但我方宇宙=大型股(47/503)，size 溢酬的原生棲地是小型股，直接檢驗需擴宇宙——是判斷『我方座位能否測 size』的基準文獻。
- **可測性(免費資料)**:partial — EDGAR 基本面齊全但價格宇宙目前限大型股；需先 ingest point-in-time 全市場（含下市）小型股宇宙才能在原生棲地測。資訊成本=髒指數成分史/CRSP 型下市面板。
- **TR 切入(含 Nagel 對照)**:以 NYSE 分位 breakpoint 建 size decile L/S（市值加權），市場中性後對照 (a) shuffle 隨機分位（隨機進場）(b) FF5 靜態 beta——須證 SMB 溢酬非小盤 beta 副產品。屬 T2 缺小盤資料，落地即測。

#### hong_stein_1999 — Hong & Stein (1999) · ~6500 引用 · 「A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets」
- **主張 / 與我方關聯**:Information diffuses gradually, so prices underreact -> momentum; momentum is stronger where information diffuses slowest (small, low-coverage firms); a later overreaction by momentum traders eventually reverses. → Provides a testable cross-sectional MODERATOR for momentum (coverage/size) that directly explains WHY our large-cap momentum died — mega-caps are the fast-diffusion, weakest habitat, consistent with our null. Predicts momentum should revive in low-coverage names.
- **可測性(免費資料)**:PARTIAL. Momentum from price. Diffusion-speed moderator: true proxy = analyst coverage (I/B/E/S, NOT free); use size + turnover + firm age (EDGAR/price) as free surrogates -> partial. Point-in-time OK.
- **TR 切入(含 Nagel 對照)**:Momentum L/S conditioned on a diffusion-speed proxy (size/turnover/age); Hong-Stein predicts monotonically stronger momentum in the slow-diffusion quintile. Nagel controls it must beat: (1) 1/sigma^2 vol-managed momentum (Moreira-Muir) — the coverage-conditioned momentum must beat vol-managed momentum, else it is the same edge (hardest control); (2) static exposure to the small/low-turnover basket (Cederburg); (3) placebo coverage proxy. Honesty note: our survivorship-large-cap universe IS Hong-Stein's weakest habitat, so a null here does NOT convict the mechanism (mis-seat) — reopening requires a small-cap PIT universe (an information cost).

#### roll1984-effspread — Roll (1984) · ~4800 引用 · 「A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market (Journal of Finance)」
- **主張 / 與我方關聯**:有效價差 = 2·√(−Cov(Δp_t, Δp_{t-1})),當一階自協方差為負時成立;價差造成的 bid-ask bounce 使相鄰價格變動負相關。 → 給我們一個『從免費日線反推交易成本』的估計器,可直接校準 TR-12 phase-cost 模型(目前用假設值),也可當流動性因子。是本子領域『effective-spread estimators』的定義性論文。
- **可測性(免費資料)**:YES,有 caveat。只需免費日線收盤變動。Point-in-time OK。已知限制:實務上約半數估計自協方差為正(估計無定義)——日線上噪音大,intraday 較穩(我們沒 tick)。故 partial-to-yes:當作『可建但需與 Corwin-Schultz/Amihud 交叉驗證』的成本估計器。
- **TR 切入(含 Nagel 對照)**:用 Roll 估計器算每股有效價差,雙用途:(a) 餵入成本模型(F2/TR-12)——測『Roll vs Corwin-Schultz vs Amihud 哪個最能預測我們回測裡的實現滑價』;(b) 當價差因子做 L/S 排序。Nagel 對照:(1) 靜態曝險——價差因子是否只是 size 靜態傾斜?size 中性化後還剩多少;(2) 隨機進場 null 產生價差-報酬 spread 的 null 分布;(3) 對成本用途,對照組=『常數成本假設』(這本身就是 Nagel 靜態控制的成本版:動態價差估計是否勝過一個常數?)。PASS=Roll 成本估計在樣本外顯著優於常數成本。

#### acharya-pedersen2005-lcapm — Acharya & Pedersen (2005) · ~4500 引用 · 「Asset Pricing with Liquidity Risk (Journal of Financial Economics)」
- **主張 / 與我方關聯**:期望報酬 = 無風險 + market beta + 淨流動性成本(level) + 3 個流動性 covariance beta(β2:流動性共動;β3:報酬對市場流動性;β4:流動性對市場報酬)。 → 把 Amihud 的 level 效應升級成有結構的風險分解;選股時可分辨『貴是因為 level 貴』還是『因為 flight-to-liquidity 曝險』。是 Amihud 2002 與 P-S 2003 的統一框架。
- **可測性(免費資料)**:YES(可重建,較費工)。全部 4 個 beta 都由 Amihud 正規化 illiquidity innovations + 報酬構成,皆源自免費日線;market cap 正規化常數需 shares outstanding(EDGAR)。Point-in-time OK。難點=innovation 建模(AR2)與短樣本 n_eff,非資料缺口。
- **TR 切入(含 Nagel 對照)**:在既有 Amihud ILLIQ 之上建 4 個 LCAPM beta,測『covariance betas 是否在 level(Amihud)與 size 之上還有增益』。Nagel 對照:(1) 靜態曝險——先扣掉永久 illiquidity level tilt(=Amihud TR 的結果)與 static CAPM beta,covariance betas 還剩多少?(2) 1/σ² 波動管理——flight-to-liquidity(β4)在高波動期爆發,須證明它不是 1/σ² 的複雜包裝;(3) 隨機組合 null。PASS 條件=4-beta 分解在 Amihud level + size + static beta 之上仍有顯著 t 且淨成本存活。預期:多半被 level + size 吸收(與本框架『複雜度多被最簡控制解釋』的先驗一致)。

#### basu-1977-ep — Basu (1977) · ~4500 引用 · 「Investment Performance of Common Stocks in Relation to Their Price-Earnings Ratios」
- **主張 / 與我方關聯**:低 P/E(高 E/P)股風險調整後報酬顯著高於高 P/E，CAPM 無法解釋——最早的估值比率異常，且獨立於 size。 → value 因子的 earnings-yield 版本；我方 value(B/M)在 2015-24 座位=死(docs/09)，E/P 版命運是否不同是乾淨的診斷。與 Greenblatt earnings-yield 直接相連。
- **可測性(免費資料)**:yes — E/P = TTM 盈餘(EDGAR)/市值，PIT 對齊申報日；全免費資料可建。
- **TR 切入(含 Nagel 對照)**:E/P decile L/S(NYSE breakpoint、VW、6 月再平衡)，市場中性後對照 shuffle 隨機分位與 FF5 靜態 beta；檢驗 E/P 版在失落十年是否也死，或 earnings-yield 與 B/M 命運分歧。

#### cochrane11_discount — Cochrane (2011) · ~4200 引用 · 「Presidential Address: Discount Rates (JF 66:1047-1108)」
- **主張 / 與我方關聯**:由 Campbell-Shiller 恆等式,D/P 的變動幾乎必然由『後續報酬可預測』吸收,因為股利成長本身不可預測(狗沒吠);長視窗回歸放大同一訊號,可預測性是折現率變動的普遍現象而非異常。 → 提供本專案擇時章節的理論骨架與『為何 D/P 一定預測某物』的識別論證;其可檢驗核心(股利成長不可預測 ⇒ 報酬可預測)是一個乾淨的、可用免費資料複現的診斷,能與 FF88 互為驗證。
- **可測性(免費資料)**:yes(就其可檢驗核心)— 用 Shiller 免費資料跑『D/P → 未來股利成長』與『D/P → 未來報酬』對照回歸,複現『狗沒吠』;綜述本身非單一測試,但核心恆等式分解完全 $0 可重建;point-in-time 可行。
- **TR 切入(含 Nagel 對照)**:診斷型 TR:分解 D/P 的變異——回歸未來報酬 vs 未來股利成長,展示預測力集中在報酬側(複現 Cochrane/‘Dog’)。這一步不打 Nagel 對照(是識別診斷,非策略);其產出(D/P 確實編碼報酬預測)才餵給 FF88/CT08 的可交易性測試,那裡才由 Moreira-Muir 波動管理 + Cederburg 靜態當關卡。

#### ff89_business — Fama & French (1989) · ~3800 引用 · 「Business Conditions and Expected Returns on Stocks and Bonds (JFE 25:23-49)」
- **主張 / 與我方關聯**:違約利差(Baa-Aaa)與 D/P 捕捉長波景氣風險溢酬、期限利差捕捉短波,三者共同使預期報酬在衰退低谷高、擴張高峰低——可預測性是理性時變風險溢酬而非無效率。 → 把擇時訊號從估值比擴到宏觀利差,且棲地是本專案 FRED 免費資料完全覆蓋的;違約利差是少數與波動旋鈕不高度共線的訊號,適合檢驗 Nagel 批評是否對『宏觀型』訊號同樣成立。
- **可測性(免費資料)**:yes — 期限利差(10Y-3M)、違約利差(Moody's Baa-Aaa)皆 FRED 免費、point-in-time 可行;D/P 用 Shiller;月頻;$0。
- **TR 切入(含 Nagel 對照)**:月頻多預測子 OOS 回歸(違約利差 + 期限利差 + D/P),倉位 ∝ 預測超額報酬。Nagel 對照關卡:違約利差在衰退飆升,天然與波動相關——須對 Moreira-Muir 1/σ² 正交化後違約利差殘差仍帶正 alpha(t≥2);與 Cederburg 靜態比 Calmar。並附 Stambaugh/Newey-West 修正 t。

#### hou-xue-zhang-2015-qfactor — Hou, Xue & Zhang (2015) · ~3500 引用 · 「Digesting Anomalies: An Investment Approach (q-factor model)」
- **主張 / 與我方關聯**:以投資(資產成長 I/A)與獲利(ROE)兩因子 + 市場 + size,可吸收 ~80 個異象中的多數,表現不輸/勝 FF 模型。 → 投資與 ROE 兩腿皆可由 EDGAR PIT 重建,直接給選股評分;是 GP 之外第二條基本面 alpha 線,並提供比 Carhart 更貼題、更嚴的歸因基準(可檢驗 GP 是否被 ROE 吃掉)。
- **可測性(免費資料)**:partial→yes — I/A=年度總資產成長、ROE=季度淨利/權益,全在 EDGAR companyfacts(filed 即 PIT);零成本。缺口:原文用 NYSE breakpoints + 全市場宇宙,我們只有 503/610,無法完全複刻因子權重,只能建 our-universe 版做歸因。
- **TR 切入(含 Nagel 對照)**:(A) 建 our-universe I/A 與 ROE quintile L/S;(B) 以 {Mkt, ME, I/A, ROE} 對旗艦 combo 與 GP sleeve 做 spanning/歸因。Nagel 對照:每條因子腿須打敗靜態常數曝險版(F6 靜態控制),整體擇股不得被 1/σ² 波動管理解釋。預先承諾:若 I/A 腿在大型股宇宙 ICIR≈0(docs/10 asset_growth 已見 −0.22 弱),判定=投資因子棲地錯置(原生=小型股/全市場),FAILED 只關閉大型股座位。

#### ikenberry-lakonishok-vermaelen-1995-buybacks — Ikenberry, Lakonishok & Vermaelen (1995) · ~3500 引用 · 「Market Underreaction to Open Market Share Repurchases」
- **主張 / 與我方關聯**:公開市場庫藏股回購宣告後四年有顯著正異常報酬，尤其 value 股——市場對回購訊號反應不足。 → net-issuance 因子的對稱另一半(負發行=回購)；可用 EDGAR 股數淨減少代理，與 Pontiff-Woodgate 拼成完整發行光譜。
- **可測性(免費資料)**:partial — 回購宣告日需事件資料(no)；但可用 EDGAR 流通股數『淨減少』代理回購(yes)。
- **TR 切入(含 Nagel 對照)**:用股數淨減少(negative net issuance)代理回購，建 L/S，對照 Pontiff-Woodgate 連續版與 shuffle；檢驗回購腿是否為 net-issuance 因子的對稱另一半、beat 隨機分位與 FF5 靜態 beta。

#### jegadeesh_1990_predictable — Jegadeesh (1990) · ~3300 引用 · 「Evidence of Predictable Behavior of Security Returns」
- **主張 / 與我方關聯**:以上月報酬排名,買 loser 賣 winner 的 1月 contrarian 組合有顯著正報酬(短期反轉),與 3-12月動量方向相反。 → 短期反轉是他們已在 mega-cap 上測死的方向(docs/06:1日/5日反轉淨值破產),但月頻+風控+廣宇宙版尚未在 fabric 正式審判;是判斷『反轉 alpha 是真訊號還是點差 bounce』的教科書案例。
- **可測性(免費資料)**:partial。訊號(月頻排名)完全可用免費日線;但 1月短期反轉惡名昭彰地被 bid-ask bounce/微結構污染——用收盤價會高估毛報酬,淨點差後(TR-12 成本)極可能歸零。point-in-time 可行。無需 tick,但無 tick 就無法乾淨地把 bounce 從真訊號分離,故標 partial。
- **TR 切入(含 Nagel 對照)**:月頻 loser-minus-winner，加 skip-1-day 微結構衛生,同一 book 跑 same-close vs next-close 成交敏感度(F1),掛 TR-12 點差。Nagel 對照:反轉毛報酬必須擊敗隨機進場 + 靜態曝險;真正的殺手對照是『點差成本+skip-day 後殘餘』——若淨值<0(如 docs/06),判定=微結構假象非 alpha。預期 FAILED-net,與既有 mega-cap 結論一致但補上廣宇宙月頻座位。

#### chan_jegadeesh_lakonishok_1996_momentum — Chan, Jegadeesh & Lakonishok (1996) · ~3200 引用 · 「Momentum Strategies」
- **主張 / 與我方關聯**:價格動量與盈餘動量(SUE、盈餘公告報酬、分析師預測修正)各自獨立預測後續報酬,兩者互不完全包含;動量主要來自市場對盈餘資訊的緩慢反應。 → 唯一能把他們手上的 EDGAR 基本面(PIT 申報日對齊)真正用進動量的一篇——用 EDGAR 季度 EPS 自建 SUE,測『EDGAR 盈餘動量是否對價格動量有增量』,是一個他們尚未觸及的資料角度。
- **可測性(免費資料)**:partial。價格動量 leg=yes(免費日線)。盈餘動量 leg:SUE 可用 EDGAR 季度 EPS 序列以申報日對齊重建(真 PIT),可行;但『分析師預測修正』leg 需 I/B/E/S → no(付費)。故測 price + EDGAR-SUE 雙 leg,誠實丟掉 revisions leg。重建成本=EDGAR 解析(已具備)。
- **TR 切入(含 Nagel 對照)**:兩個正交 sleeve:6月價格動量 vs EDGAR-SUE 盈餘動量;測邊際貢獻(SUE 對已知動量是否加分)。Nagel 對照:每個 leg 都要先擊敗 Moreira-Muir 波動管理 + Cederburg 靜態;關鍵增量檢定=SUE leg 在控制價格動量後是否仍有殘餘 ICIR。注意 docs/19 已記 PEAD 在大型股宇宙=其最弱棲地(無漂移),故預期 SUE leg 在 S&P 大型股弱;翻案座位=小型股宇宙。

#### da_engelberg_gao_2011_search_attention — Da, Engelberg & Gao (2011) · ~3200 引用 · 「In Search of Attention」
- **主張 / 與我方關聯**:A spike in Google SVI (direct retail-attention proxy) predicts higher prices over the next ~2 weeks and a reversal within the year, plus stronger IPO first-day pops — attention induces temporary overpricing. → The 'attention' keyword's cleanest FREE signal — Google Trends is genuinely $0 and PIT-clean from 2004, a rare alt-data source inside our budget. Attention-spike → short-horizon overpricing → reversal is a directly tradable, novel-to-us behavioral signal that also stress-tests our G-S 'you must pay for information' thesis (here the info is nearly free).
- **可測性(免費資料)**:YES/PARTIAL. Google Trends SVI is free (weekly, 2004+), PIT-clean (as-released). Returns from OHLCV; cost $0. Caveats: Trends is sampled/normalized (rounded, noisy, sampling changes over time), ticker-name ambiguity, weekly frequency, and retail-attention effects are strongest in small caps (our large-cap seat weaker).
- **TR 切入(含 Nagel 對照)**:Pull abnormal SVI, cross-sectionally sort, test 1-2 week continuation then multi-month reversal. Nagel controls: (1) static exposure — is high-SVI just a high-turnover/high-vol basket? neutralize vs turnover and a constant high-attention basket; (2) 1/σ² vol management; (3) placebo SVI (random ticker series). Pre-commit: after net costs the short-horizon attention trade likely dies (high turnover) → durable value = SVI as a reversal/risk overlay, and check the reversal is not just short-term reversal (jegadeesh_1990, already in list) relabeled.

#### hong_lim_stein_2000_bad_news_slow — Hong, Lim & Stein (2000) · ~3000 引用 · 「Bad News Travels Slowly: Size, Analyst Coverage, and the Profitability of Momentum Strategies」
- **主張 / 與我方關聯**:Holding size fixed, momentum is much stronger among stocks with LOW analyst coverage, and the effect is driven mainly by the slow diffusion of BAD news among losers - direct empirical support for the Hong-Stein gradual-information-diffusion mechanism. → Sharpens the diffusion moderator behind our dead large-cap momentum (mega-caps = fastest diffusion = weakest habitat) and identifies coverage/size as the free-ish conditioning variable to reopen momentum in the right seat.
- **可測性(免費資料)**:partial. Size is free (price x shares); true analyst coverage is I/B/E/S (paid) - use size, firm age (EDGAR first-filing), and turnover as free coverage surrogates -> partial; PIT fine; cost $0 for surrogates.
- **TR 切入(含 Nagel 對照)**:Condition momentum on a free diffusion-speed proxy (size x age x turnover) on the 503 universe; predict monotonically stronger momentum in slow-diffusion names. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso, hardest), (2) static exposure to the small/low-turnover basket (Cederburg), (3) placebo coverage proxy. Honesty caveat: our survivorship large-cap universe is the weakest habitat, so a null does NOT convict the mechanism (mis-seat); reopening needs a small-cap PIT universe (info cost).

#### daniel-titman-1997-characteristics-vs-covariances — Daniel & Titman (1997) · ~2900 引用 · 「Evidence on the Characteristics of Cross-Sectional Variation in Stock Returns」
- **主張 / 與我方關聯**:報酬由公司特徵(B/M、size)本身預測,而非其對 HML/SMB 的因子載荷;控制特徵後因子 beta 無溢酬 = 挑戰風險基礎的因子模型。 → 這是整個 anomaly zoo 的元問題,且直接對映本框架 Nagel-control 哲學:一個異象到底是『特徵 alpha』還是『可被靜態因子曝險複製』。提供現成的識別檢定範式,可直接升級 F6 控制組方法論。
- **可測性(免費資料)**:partial — 需個股報酬(有)+ FF 因子(有)+ 特徵(B/M 由 EDGAR 權益/市值、size 由價格×股數,PIT 可行);零成本。原文用 characteristic-balanced portfolios,我們宇宙 N 較小、因子載荷估計雜訊大,只能做簡化 double-sort(特徵×載荷)。
- **TR 切入(含 Nagel 對照)**:對已 PASSED 的 GP sleeve 與旗艦 combo 做 Daniel-Titman 式雙分類:固定特徵(GP 分位)後看因子 beta 是否仍有溢酬,反之亦然——即 F6『哪個最簡單的控制能解釋它』的嚴格化。Nagel 對照:特徵中性化後殘餘報酬若消失,判定=因子曝險(靜態 beta),非特徵 alpha;唯有特徵固定後 beta 溢酬消失、特徵溢酬存活,才支持特徵 alpha。

#### moskowitz_grinblatt_1999_industry — Moskowitz & Grinblatt (1999) · ~2800 引用 · 「Do Industries Explain Momentum?」
- **主張 / 與我方關聯**:產業動量(買贏家產業組合)強勁,且在很大程度上『解釋掉』個股動量——控制產業後個股動量顯著減弱;動量有實質的產業成分。 → 他們的個股 JT 動量已死(TR-11),但從未測產業層聚合是否還活;產業動量也是既有 5-sleeve combo 裡『科技動量/防禦輪動』sleeve 的學理根;可用 EDGAR SIC 直接落地。
- **可測性(免費資料)**:partial-yes。報酬=免費日線。產業分類:EDGAR filer metadata 帶 SIC 碼(可近似 PIT,但 SIC 由 SEC 指派、非嚴格歷史快照),或用靜態 GICS 代理;兩者都有 vintage 誤差但可做。無需付費資料。標 partial 僅因產業對映品質。
- **TR 切入(含 Nagel 對照)**:以 SIC/GICS 建產業組合,產業動量 long 贏家產業;直接對照=個股 JT 動量(論文宣稱產業吸收個股動量)。Nagel 三件套:產業動量必須擊敗 Moreira-Muir 1/σ² 波動管理 + Cederburg 靜態 + 隨機產業輪動。預先承諾:若產業動量 ≈ 隨機輪動或被靜態科技曝險解釋(2015-26 科技牛),判定=產業動量在此樣本=偽裝的科技 beta,與 docs/10 的 regime-rotation 教訓一致。

#### fama_french_2008_dissecting_anomalies — Fama & French (2008) · ~2600 引用 · 「Dissecting Anomalies (Journal of Finance)」
- **主張 / 與我方關聯**:Most anomalies (accruals, net share issues, asset growth, momentum, profitability) are strong in microcaps and weak/absent in the value-weighted big-cap universe; sorts vs regressions disagree because tiny stocks dominate equal-weight sorts. → This is the exact intellectual backbone of our docs/19 'habitat' argument (PEAD/accruals live in small caps; large-cap FAILED only closes the large-cap seat). Testing it directly turns our qualitative habitat claim into a measured size-interaction across our whole factor library.
- **可測性(免費資料)**:partial — needs EDGAR PIT fundamentals (accruals/asset growth/profitability, XBRL ~2009+) + free daily OHLCV extended to small caps. Point-in-time OK via filed-date. Binding gaps: (a) microcap universe with survivorship/delisting returns is not clean on free data (yfinance/stooq drop dead tickers), (b) pre-2009 structured fundamentals thin. Feasible as a large+small-cap post-2009 slice; the true microcap tail is not. Cost $0.
- **TR 切入(含 Nagel 對照)**:Rebuild each anomaly's long-short spread separately within micro/small/big size groups, value-weighted vs equal-weighted, on our EDGAR+price panel. Nagel control it must beat: STATIC EXPOSURE — a value-weighted buy-and-hold of the same characteristic-sorted portfolio is the honest baseline, and the anomaly must add over it AND survive value-weighting (which kills most microcap effects); random-entry placebo on the sort ranks confirms the spread isn't a sorting artifact. Pre-commit: if spreads survive only equal-weighted-microcap, verdict = 'real but in an unreachable seat' (reconverges to docs/11 data-dimension bind).

#### btz09_vrp — Bollerslev, Tauchen & Zhou (2009) · ~2600 引用 · 「Expected Stock Returns and Variance Risk Premia (RFS 22:4463-4492)」
- **主張 / 與我方關聯**:VRP(風險中性期望變異數減物理已實現變異數)顯著正向預測 1-6 個月市場超額報酬,其可預測性在季度視窗達峰值,遠強於 D/P 等傳統估值比,反映時變風險趨避。 → 與本專案既有訊號正交的『新訊號家族』,且棲地是本專案能觸及的近代高頻期(1990-);是少數可能真正打敗波動旋鈕的候選,因為 VRP 本身就編碼了『非波動』的風險溢酬資訊——正好用來壓力測 Nagel 批評的邊界。
- **可測性(免費資料)**:partial→大致 yes — VIX(CBOE 免費,1990-;VXO 至 1986)提供隱含變異;已實現變異可由日線指數報酬估(理想用日內,但日線月度 RV 可近似)。point-in-time 可行。限制:原文用高頻 RV,免費日線版是近似;1990 前需重建 → 該段標 partial。$0。
- **TR 切入(含 Nagel 對照)**:月頻:VRP = VIX²(月末)− trailing 已實現變異(日線)→ OOS predictive regression;倉位 ∝ 預測超額報酬。關鍵 Nagel 對照:因 VRP 與波動高度相關,必須把倉位對 Moreira-Muir 1/σ² 與『純 VIX 水位擇時』雙重正交化後,VRP 殘差仍須帶正 alpha(t≥2);否則判『VRP 只是波動管理的另一參數化』。淨 5bps + 截倉。

#### richardson-sloan-soliman-tuna-2005 — Richardson, Sloan, Soliman & Tuna (2005) · ~2600 引用 · 「Accrual Reliability, Earnings Persistence and Stock Prices」
- **主張 / 與我方關聯**:擴大應計定義(含非流動營運資產與淨金融資產)並依『會計可靠度』分層:低可靠度應計持續性最低、被市場高估最嚴重，異常報酬主要來自這些成分。 → 是 Sloan(1996)的升級——告訴我們用 EDGAR 建應計時該用哪個更廣的定義、哪個成分最 alpha-rich。直接改良應計 TR 的訊號建構。
- **可測性(免費資料)**:yes — 廣義應計需 EDGAR 完整資產負債表(營運/金融資產負債分類)，工程量中等但 PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 比較 Sloan 窄應計 vs RSST 廣義應計的 decile L/S ICIR，並拆低可靠度成分的增量貢獻。必須打敗:(a) 零訊號基本面籃子，(b) Sloan 窄應計(證增量)，(c) 靜態曝險。

#### lo_mamaysky_wang_2000_foundations_ta — Lo, Mamaysky & Wang (2000) · ~2600 引用 · 「Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation」
- **主張 / 與我方關聯**:用核回歸(kernel smoothing)把主觀的技術型態(頭肩、雙頂、旗形等)演算法化後,若干型態出現後的條件報酬分布與無條件分布有統計顯著差異,顯示技術分析含有非零的增量資訊(雖經濟量值溫和)。 → 技術/趨勢 sub-area 的方法論奠基之作,把『圖形型態』變成可重現、可統計檢定的訊號,完全用我們的日線 OHLCV;它教的是『條件分布檢定』而非買賣規則,是避免技術訊號 data-snooping 的嚴謹範式。
- **可測性(免費資料)**:yes — 核回歸型態辨識與條件分布檢定全由免費日線 OHLCV 實作。PIT 佳。成本 $0 但工程量較重(平滑 + 型態偵測 + 分布檢定)。
- **TR 切入(含 Nagel 對照)**:TR:在 503 檔宇宙實作核回歸型態辨識,檢驗型態後條件報酬分布 vs 無條件分布(Kolmogorov-Smirnov / 分位數);關鍵對照=對『隨機打亂日期的安慰劑型態』做同檢定,證明訊號非資料窺探。若轉成交易,須先打敗隨機進場與 buy-and-hold 並扣本專案成本。判定重點=條件資訊是否在扣成本後仍具經濟意義,或僅統計上可偵測。

#### stambaugh_yu_yuan_2012 — Stambaugh, Yu & Yuan (2012) · ~2400 引用 · 「The Short of It: Investor Sentiment and Anomalies」
- **主張 / 與我方關聯**:Each of 11 anomalies is stronger following HIGH sentiment, and the effect is concentrated in the SHORT (overpriced) leg because short-sale constraints prevent correction; low-sentiment periods yield weak anomalies. → A direct, actionable timing overlay for the anomalies we can build (GP-quality survivor, LT-reversal, CGO): explains WHEN a behavioral spread pays. Also a sober caution — profits sit in the short leg our long-only $0 seat cannot easily trade, tempering expectations.
- **可測性(免費資料)**:PARTIAL/YES. Anomaly L/S from EDGAR + price. BW sentiment index free (same look-ahead caveat as Baker-Wurgler). Short-leg feasibility caveat: our free-data project is effectively long-only, and the paper predicts most of the profit is short-side (unreachable) -> honest partial. PIT caveat on sentiment construction.
- **TR 切入(含 Nagel 對照)**:Take our buildable anomalies (GP-quality, LT-reversal, CGO), split returns by lagged BW sentiment tercile AND by leg; replicate 'high sentiment -> wider spread, short-leg-driven'. Nagel controls it must beat: (1) 1/sigma^2 vol management — high sentiment correlates with the vol cycle, so prove sentiment-timing != vol-timing (hardest control); (2) static unconditional always-on anomaly exposure (Cederburg) — does sentiment-timing beat always-on?; (3) placebo sentiment dates. Long-only honesty: report long-leg-only vs full spread to quantify how much our $0 seat can actually capture. PASSED bar: the sentiment-conditioned LONG leg (reachable) still adds over a vol-managed always-on anomaly.

#### daniel_moskowitz_2016_crashes — Daniel & Moskowitz (2016) · ~2300 引用 · 「Momentum Crashes」
- **主張 / 與我方關聯**:動量在恐慌後反彈期(熊市底部、市場高波動、past-loser 呈高 beta)發生罕見但巨大的崩盤;以動態縮放(依預測期望報酬/預測變異數加權)可大幅改善動量的 Sharpe。 → 這是 fabric『Nagel 對照』的正面戰場:動態/風險管理動量 vs 純 1/σ² 波動擇時。既有旗艦 combo 的價值全在風險塑形(Carhart t=3.38),而 DM 的動態動量正是『用狀態縮放賺風險塑形』的最強學術宣稱——直接檢驗它是否勝過最簡單的波動管理控制。(附註:residual momentum 是崩盤緩解的近親,但 Blitz-Huij-Martens 2011 僅 ~500 引用,低於門檻,故不單列。)
- **可測性(免費資料)**:yes。WML 因子、崩盤事件描述(2009 動量崩盤)、動態加權都可在 503 宇宙+指數長歷史上重建;預測變異數用 GARCH(`arch`,docs/03 已規劃),預測期望報酬用滾動估計。無需選擇權/日內。2009 崩盤需該年代在樣本內——用其長指數歷史涵蓋。
- **TR 切入(含 Nagel 對照)**:建 WML,刻畫其 drawdown 條件於(熊市+高波動+loser 高 beta);建 DM 動態動量=WML×(forecast μ / forecast σ²)。核心 Nagel 對決:動態動量必須加分於 (a) Moreira-Muir 純 1/σ² 波動管理 WML、(b) Barroso 常波動 WML、(c) Cederburg 靜態。預先承諾(照 TR-17 KMZ 前例):若動態加權的 Sharpe 增益塌回波動管理控制,判定=『崩盤擇時=波動擇時的重新包裝』;唯有淨成本+截倉後仍勝波動控制,才算真正的崩盤 alpha。

#### cs98_cape — Campbell & Shiller (1998) · ~2300 引用 · 「Valuation Ratios and the Long-Run Stock Market Outlook (JPM 24:11-26)」
- **主張 / 與我方關聯**:高 CAPE 與高 D/P 偏離歷史均值後傾向均值回歸,主要透過『價格向下修正』而非盈餘/股利上升實現;CAPE 對後續 10 年實質報酬有可觀負向解釋力。 → 散戶最常引用的擇時訊號,也是最容易被過度信任的;本專案該給它一個誠實裁決——CAPE 的長視窗可預測性 vs 其 OOS/實務不可交易性(重疊視窗、極少獨立觀測、Stambaugh 偏誤)。直接服務『50-100% 不可達』與期望管理敘事。
- **可測性(免費資料)**:yes — Shiller 免費資料直接含 CAPE(1881-),trailing 10 年實質盈餘即 point-in-time 乾淨;$0。注意:重疊 10 年視窗使有效樣本 n_eff 極小,須誠實標註。
- **TR 切入(含 Nagel 對照)**:月頻 CAPE 的 OOS 擇時(倉位隨 CAPE 相對其擴張窗均值升降),同時報告長視窗回歸的 n_eff 與 Stambaugh/Hodrick 修正後 t。Nagel 對照關卡:與 Moreira-Muir 波動管理及 Cederburg 靜態 B&H 比淨值與 Calmar;預先承諾——極可能判 PARTIAL/FAILED(統計上真、可交易 alpha 上不勝靜態曝險),作為『真訊號 ≠ 可交易 alpha』的教材案例。

#### rsz10_combination — Rapach, Strauss & Zhou (2010) · ~2300 引用 · 「Out-of-Sample Equity Premium Prediction: Combination Forecasts and Links to the Real Economy (RFS 23:821-862)」
- **主張 / 與我方關聯**:單一預測子 OOS 不穩,但對眾多預測子的預測值做簡單平均(組合預測)可顯著降低變異、產生穩健正 OOS R²,且其擇時報酬集中在衰退期,連結實體經濟。 → 本專案已有 GW 15 預測子(TR-17)且信奉集成穩健(ensemble robustness 已是 README 賣點);此文是把它們從『單獨都被波動旋鈕打爆』升級為『組合是否翻案』的最直接、最省成本延伸,測試集成能否跨越 Nagel 門檻。
- **可測性(免費資料)**:yes — 完全複用 TR-17 既有 GW 預測子(公開/免費),只加預測值簡單平均與 OOS R²、衰退期分解;point-in-time 可行;$0。
- **TR 切入(含 Nagel 對照)**:對 15 個 GW 預測子各自 OOS 預測後取簡單平均,構 1/σ² 目標倉位。Nagel 對照關卡:組合預測的擇時淨值須勝 Moreira-Muir 波動管理與 Cederburg 靜態,且對波動管理殘差 alpha t≥2;預先承諾——若組合增益仍被波動旋鈕吸收(呼應 TR-17 對 KMZ 的判定),判『集成穩健為真但 alpha=波動擇時』,強化本專案既有結論。

#### titman-wei-xie-2004-capex — Titman, Wei & Xie (2004) · ~2300 引用 · 「Capital Investments and Stock Returns」
- **主張 / 與我方關聯**:資本支出異常增加的公司後續報酬顯著較低(過度投資/帝國建造)，效應在現金充裕、低槓桿(治理弱)公司最強。 → investment 因子的『capex 存量』版，與 asset-growth(總資產)互補；治理交互提供更細的訊號切法。
- **可測性(免費資料)**:yes — capex/資產 by EDGAR 現金流量表，PIT。
- **TR 切入(含 Nagel 對照)**:異常 capex decile L/S，對照 asset-growth 版與 shuffle；檢驗 capex 版是 asset-growth 的乾淨子集或獨立訊號，須 beat 隨機分位與 FF5 靜態 beta。

#### lo_mackinlay_1990_contrarian_profits — Lo & MacKinlay (1990) · ~2300 引用 · 「When Are Contrarian Profits Due to Stock Market Overreaction?」
- **主張 / 與我方關聯**:Most short-horizon contrarian profits come NOT from own-stock overreaction but from positive cross-serial correlations (large stocks lead small stocks); own-autocorrelation is actually often positive, so 'overreaction' is largely a lead-lag phenomenon. → A rigorous diagnostic that tells us whether any reversal/contrarian sleeve we build is genuine mean-reversion or a lead-lag artifact we cannot trade long-only, preventing mis-attribution of short-term reversal profits.
- **可測性(免費資料)**:yes, fully. Own- and cross-autocovariance matrices computed from the free daily/weekly return panel; PIT fine; cost $0; purely diagnostic (no trading needed to run the decomposition).
- **TR 切入(含 Nagel 對照)**:Compute the Lo-MacKinlay decomposition of any contrarian sleeve on the 503 return panel, splitting profit into own-autocovariance vs cross-serial. Nagel control framing: the cross-serial (lead-lag) component is untradable long-only, so the tradable residual must still beat static exposure and a random-entry placebo. Verdict use: reclassify any reversal 'alpha' that is mostly cross-serial as a non-implementable artifact.

#### kraus-litzenberger-1976-skewness-preference — Kraus & Litzenberger (1976) · ~2000 引用 · 「Skewness Preference and the Valuation of Risk Assets」
- **主張 / 與我方關聯**:Extending the CAPM to a third moment, investors prefer positive skewness, so assets that reduce portfolio skewness (negative coskewness with the market) must offer higher expected returns. Systematic skewness carries its own risk price alongside beta. → The theoretical foundation the project should cite to justify why any coskewness TR (Harvey-Siddique) is testing a RISK premium, not an anomaly — key for the G-S 'who pays the information cost' verdict language. Same free data as Harvey-Siddique, so it costs nothing extra to ground the empirical test in its original theory. Borderline >2000; included as a possibly-missed classic that anchors the whole higher-moment subdomain.
- **可測性(免費資料)**:yes. Identical construction to Harvey-Siddique (systematic skewness from daily stock + index returns); free OHLCV + index; PIT trivial; ~$0. The paper's contribution is theoretical, so the empirical TR is shared with harvey-siddique-2000.
- **TR 切入(含 Nagel 對照)**:TR: fold into the harvey-siddique-2000 TR as its theoretical prior — estimate the three-moment SML (price of beta AND price of coskewness) via Fama-MacBeth, report both risk prices with Shanken (ledger-queued) EIV correction. Nagel controls: the coskewness risk price must survive against (a) a random-coskew placebo cross-section (FM slope → 0), (b) a book sorted on estimated coskew held statically, and (c) show the premium is not a 1/σ² vol-timing relabel. Pre-commit: treat as PASSED-as-risk only if the coskewness price is significant net of Shanken correction AND the sort beats static+vol controls; else the three-moment CAPM adds no priced dimension in this seat.

#### goyenko-holden-trzcinka2009-proxyvalidation — Goyenko, Holden & Trzcinka (2009) · ~1900 引用 · 「Do Liquidity Measures Measure Liquidity?」
- **主張 / 與我方關聯**:In a monthly/annual horse-race, daily-data proxies (effective tick, LOT, Holden, Amihud) match high-frequency TAQ benchmarks well; for percent-cost (spread) the tick-based measures win, and for price impact Amihud's ILLIQ is the best low-frequency proxy. → Not a signal — a meta-tool that tells us WHICH of the cheap estimators (Amihud, LOT, Roll, CS, effective tick) we should trust in a $0/mo free-data regime, so we do not build a whole liquidity sleeve on a proxy that is actually noise. Directly de-risks every other liquidity TR in this list.
- **可測性(免費資料)**:partial. All the daily proxies are buildable from OHLCV at ~$0; but the TAQ 'ground truth' to re-validate them needs intraday (T2 information cost). Practical use: adopt their published ranking to pick our proxy, and internally replicate the CHEAP half (cross-proxy correlation matrix on our universe) as a consistency check.
- **TR 切入(含 Nagel 對照)**:A measurement-QA TR, not a trading TR: compute Amihud, LOT, Roll, CS, Abdi-Ranaldo, zero-return and effective-tick on the 610 universe, report the cross-proxy correlation/rank-agreement matrix, and pre-register 'trust Amihud for impact, effective-tick/CS for spread' per GHT. No Nagel control needed (no return claim); instead it FEEDS the Nagel-gated liquidity TRs by fixing which proxy each uses, preventing proxy-shopping (a Sullivan-Timmermann-White data-snooping leak).

#### lehmann_1990_fads_martingales — Lehmann (1990) · ~1800 引用 · 「Fads, Martingales, and Market Efficiency」
- **主張 / 與我方關聯**:A zero-cost portfolio that buys prior-week losers and sells prior-week winners earns large positive returns the following week, implying strong short-horizon return reversals inconsistent with a random walk. → The canonical short-term reversal signal (complement to our long-horizon reversal work and to Jegadeesh 1990), fully buildable on free data and directly testable against the cost wall that usually eats weekly strategies.
- **可測性(免費資料)**:yes, fully. Weekly returns from free daily OHLCV; contrarian weights from prior-week returns; PIT trivial; cost $0 gross - but weekly turnover makes the cost stress the whole story.
- **TR 切入(含 Nagel 對照)**:Build the weekly loser-minus-winner portfolio on the 503 universe, gross then net under costs.py. Nagel controls it must beat: (1) RANDOM-ENTRY / zero-signal placebo (primary for a pure XS reversal), (2) static exposure baseline, (3) 1/sigma^2 vol management (secondary). Pre-commit (G-S): weekly reversal is notoriously a bid-ask-bounce and liquidity-provision artifact - expect net-of-cost collapse, so its durable value is as a microstructure/limits-to-arb diagnostic, not a long-only sleeve.

#### brennan-chordia-subrahmanyam1998-dollarvolume — Brennan, Chordia & Subrahmanyam (1998) · ~1800 引用 · 「Alternative Factor Specifications, Security Characteristics, and the Cross-Section of Expected Stock Returns」
- **主張 / 與我方關聯**:Regressing Fama-French-risk-adjusted returns directly on characteristics, dollar trading volume enters significantly and NEGATIVELY (more liquid = lower return), and characteristics dominate covariances — establishing both a dollar-volume liquidity premium and the risk-adjusted-characteristic testing methodology. → Provides the standard methodology (risk-adjusted return on characteristics) our factor validation already echoes, plus a fourth liquidity proxy (dollar volume) to horse-race against Amihud/turnover/LOT. The methodological contribution alone (how to test a characteristic net of FF loadings) is reusable across every TR.
- **可測性(免費資料)**:yes. Dollar volume from OHLCV; FF/Carhart factors already built in-repo; run the risk-adjusted-return-on-characteristic regression; PIT clean; cost ~$0. Caveat: dollar volume is highly collinear with size & Amihud — expect the marginal premium to be small in our universe.
- **TR 切入(含 Nagel 對照)**:Implement the BCS two-pass: risk-adjust returns by our FF/Carhart model, regress on log dollar-volume (+ size, BM, momentum). Nagel gauntlet on the implied tilt: (1) static exposure — is the dollar-volume coefficient just size? Orthogonalize; (2) 1/σ² Moreira-Muir control; (3) random-entry null. Also use it as a METHOD-adoption candidate (F-layer): standardize 'characteristic significance = risk-adjusted-return regression, not raw quantile spread' across the liquidity TRs.

#### zhang_2006_information_uncertainty — Zhang (2006) · ~1700 引用 · 「Information Uncertainty and Stock Returns」
- **主張 / 與我方關聯**:Greater information uncertainty amplifies price CONTINUATION following news — momentum and PEAD are stronger among high-uncertainty firms (young, small, volatile, low-coverage), consistent with overconfidence/psychology (DHS). → Operationalizes the cross-sectional moderator that DHS (already in the ledger) predicts but doesn't build. Our large-cap universe is large/old/well-covered = LOW uncertainty = exactly where Zhang says momentum is weakest — a direct re-seat of our dead large-cap momentum verdict.
- **可測性(免費資料)**:PARTIAL. Free uncertainty proxies: firm age (first EDGAR filing / listing date), size (price×shares), return volatility (OHLCV). Non-free: analyst coverage & dispersion (I/B/E/S) → use the age/size/vol surrogates. PIT OK; cost $0. Caveat: large-cap universe is uniformly low-uncertainty, compressing the spread (confirms the dead-momentum seat).
- **TR 切入(含 Nagel 對照)**:Build momentum & PEAD, interact with a composite free uncertainty index (small + young + high-vol); Zhang predicts stronger continuation in high-uncertainty names. Nagel controls: (1) 1/σ² vol management — the uncertainty proxy loads on volatility, so the uncertainty-conditioned continuation must beat a vol-managed momentum book; (2) static exposure = a constant small/young tilt; (3) placebo uncertainty. Pre-commit: if high-uncertainty momentum is just small-cap/high-vol beta, verdict = uncertainty = size/vol repackaged.

#### bsw-2010-fdr-alpha — Barras, Scaillet & Wermers (2010) · ~1700 引用 · 「False Discoveries in Mutual Fund Performance: Measuring Luck in Estimated Alphas」
- **主張 / 與我方關聯**:對大量估計 α 的 t 分布套 FDR,估出真正 α>0、α=0、α<0 的比例;多數看似 skilled 的基金其實是運氣。 → 我們掃 200+ OSAP 訊號 / 因子 zoo 時,BSW 給『這批訊號裡有多少是真的』的 FDR 估計——比逐一 Bonferroni 更貼近『一堆候選裡挑真 alpha』的問題。
- **可測性(免費資料)**:yes — 套既有 trial-registry 的 t 統計量集合;無新資料;算力小。
- **TR 切入(含 Nagel 對照)**:TR:對 factor-zoo / OSAP 掃描的 t 值集合套 BSW-FDR,估真陽性比例並與 HLZ Bonferroni 對照;Nagel 對照=把候選全換成隨機進場/波動管理訊號,確認 FDR 對隨機控制估出≈0 真陽性,校準我們的發現率。

#### cochrane_2008_dog_did_not_bark — Cochrane (2008) · ~1600 引用 · 「The Dog That Did Not Bark: A Defense of Return Predictability」
- **主張 / 與我方關聯**:即便 D/P→報酬的迴歸 t 值不顯著,D/P→未來股利成長的『不可預測性』本身就是報酬可預測的強證據(VAR 恆等式下兩者互補);因此傳統以單一迴歸 t 值否定可預測性的作法低估了實際證據強度。 → 提供一個與 Welch-Goyal(gw08,已在名單,OOS 悲觀)正面對撞的視角,教我們用 present-value 分解而非單一 OOS R² 來判斷擇時訊號是否真有內容——對我們『擇時幾乎全 FAILED』的結論是必要的對立面壓力測試。
- **可測性(免費資料)**:yes — Shiller 免費長歷史含價格與股利,可建 D/P 與股利成長並跑 VAR 恆等式。PIT 佳(年頻已實現股利)。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:在 SPY/指數上同時估計 D/P→報酬 與 D/P→股利成長兩條迴歸,檢驗 Cochrane 的『係數必須相加到恆等式約束』;把約束後的隱含報酬可預測性轉成擇時,對照組須先打敗 buy-and-hold、1/σ² 與隨機進場。診斷價值:區分『真無可預測性』與『單迴歸檢定力不足』——正是本專案 T1(座位/檢定錯置)判準的教科書案例。

#### lev-thiagarajan-1993-fundamental-signals — Lev & Thiagarajan (1993) · ~1600 引用 · 「Fundamental Information Analysis」
- **主張 / 與我方關聯**:12 項基本面訊號(存貨、應收、毛利、銷管費、資本支出、有效稅率、存貨計價等)與同期盈餘反應係數及未來報酬相關；訊號在高通膨/特定總經狀態下加權不同。 → F-score/G-score 的直系祖先與訊號詞典;提供一套 EDGAR 可算的基本面『增量資訊』特徵，可作 ML 因子面板的基本面欄位來源(補本專案特徵多為價量的弱點)。
- **可測性(免費資料)**:yes — 12 訊號幾乎全部 EDGAR 可算(存貨、應收、毛利、SG&A、capex、稅率)；PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 把 12 訊號組成複合 score 的 L/S decile，並拆解哪幾項貢獻 IC。必須打敗:(a) 零訊號基本面籃子，(b) 純 GP 品質(證增量)，(c) 靜態曝險。亦可作為 GKX 式 ML 面板的基本面特徵注入實驗。

#### grundy_martin_2001_risks_rewards_momentum — Grundy & Martin (2001) · ~1500 引用 · 「Understanding the Nature of the Risks and the Source of the Rewards to Momentum Investing」
- **主張 / 與我方關聯**:Momentum loads with large, time-varying betas on market and size/value factors (it goes long past-winners that carry the recent factor direction); after hedging these dynamic factor bets, a stock-specific residual momentum remains, and the raw strategy's risk is dominated by its shifting factor exposures. → Explains momentum crashes as a dynamic-beta phenomenon and is the intellectual precursor to residual/factor-hedged momentum, giving a hedged variant that could survive on our seat where raw momentum failed.
- **可測性(免費資料)**:yes, fully. Needs FF factors (free, Ken French) to estimate momentum's rolling betas and build a factor-hedged momentum; free daily OHLCV for stocks; PIT fine; cost $0.
- **TR 切入(含 Nagel 對照)**:Estimate momentum's rolling market/size/value betas, build the factor-hedged momentum on the 503 universe, and compare crash behaviour vs raw. Nagel controls it must beat: (1) 1/sigma^2 variance-scaled WML (Barroso) - is hedging just vol-management?, (2) static exposure, (3) placebo (hedge on shuffled betas). PASSED only if factor-hedged momentum's net-cost alpha beats vol-managed raw momentum.

#### fairfield-whisenant-yohn-2003 — Fairfield, Whisenant & Yohn (2003) · ~1500 引用 · 「Accrued Earnings and Growth: Implications for Future Profitability and Market Mispricing」
- **主張 / 與我方關聯**:應計異常是更廣『資產成長/淨營運資產成長』異常的特例;應計與長期營運資產成長對未來 ROA 有相同的負向意涵，市場對兩者皆過度樂觀。 → 連結應計(Sloan)與資產成長(名單已有 Cooper-Gulen-Schill 2008)兩條腿——顯示可能是同一機制。對本專案是『避免重複因子』的關鍵診斷:應計與資產成長是否該併為一個訊號。
- **可測性(免費資料)**:yes — 淨營運資產成長全 EDGAR；PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 做應計 vs 資產成長 vs 淨營運資產成長的橫斷面正交化與 spanning 檢定(誰吸收誰的 alpha)，避免因子動物園重複計數。必須打敗零訊號籃子與靜態曝險;並回報與既有 Cooper-Gulen-Schill 座位的關係。

#### goyal-santaclara-2003-idio-risk-matters — Goyal & Santa-Clara (2003) · ~1400 引用 · 「Idiosyncratic Risk Matters!」
- **主張 / 與我方關聯**:The equal-weighted cross-sectional average of individual stock variances (a measure of average idiosyncratic risk) positively predicts next-month aggregate market return — idiosyncratic risk is priced at the market level over time. → A free-data market-timing signal built from the cross-section the project already owns, and a textbook cautionary tale: Bali, Cakici, Yan & Zhang (2005) showed the result is fragile to equal- vs value-weighting, small-cap/liquidity effects, and the sample end-point. It is a ready-made TR where the project's job is to reproduce AND break a famous predictability claim — exactly its comparative advantage.
- **可測性(免費資料)**:yes. Average stock variance = mean over names of within-month sum of squared daily returns; regress next-month market excess return on it. Free OHLCV + index. PIT OK (expanding OOS). Cost ~$0.
- **TR 切入(含 Nagel 對照)**:TR: reproduce the predictive regression, then stress it — value- vs equal-weight, drop micro-caps, expanding OOS (Clark-West already queued in the ledger for exactly this nested-model test). Nagel controls: the historical-mean benchmark IS the static/constant baseline; the predictor must beat (a) constant expected return AND (b) a 1/σ² vol-managed market book — because average variance and market variance are near-collinear, so any 'idio-risk timing' must beat plain vol timing. Pre-commit: signal is real only if OOS R²>0 with Clark-West significance AND it beats the 1/σ² book; expectation = collapses under value-weighting (Bali et al. replication), reinforcing the project's timing-is-hard prior.

#### livnat-mendenhall-2006-sue — Livnat & Mendenhall (2006) · ~1400 引用 · 「Comparing the Post-Earnings Announcement Drift for Surprises Calculated from Analyst and Time Series Forecasts」
- **主張 / 與我方關聯**:用『分析師預測』算的 SUE 比時序模型 SUE 的 PEAD 更大、更穩健；但即使純時序/Compustat 資料的 SUE 仍捕捉顯著可交易漂移；並校準價格、市值、財報延遲等實作細節。 → 是 PEAD 實作的操作手冊——告訴我們免費(時序、無分析師)SUE 能保留多少 drift，以及要控制哪些會計陷阱(preliminary vs 最終、財報延遲)。直接指引本專案的 PEAD TR 設計。
- **可測性(免費資料)**:partial — 時序 SUE 分支 yes(EDGAR 全可)；分析師 SUE 分支 no(需 IBES 付費)。可只做時序分支並誠實標注上限。成本:時序≈$0。
- **TR 切入(含 Nagel 對照)**:TR 復現其時序-SUE 分支於 EDGAR，量化免費 SUE 的 drift(對照文獻中分析師 SUE 的上限)；納入財報延遲/preliminary 陷阱控制。必須打敗隨機進場與靜態曝險，並記錄『分析師資料=一筆資訊成本』的翻案條件。

#### chordia-subrahmanyam-anshuman2001-tradingactivity — Chordia, Subrahmanyam & Anshuman (2001) · ~1300 引用 · 「Trading Activity and Expected Stock Returns」
- **主張 / 與我方關聯**:Expected returns are NEGATIVELY related to the volatility (coefficient of variation) of dollar trading volume and turnover, even after controlling for the level of liquidity, size, BM and momentum — a counterintuitive sign that the second moment of trading activity is priced. → Moves beyond liquidity LEVEL to liquidity VARIABILITY — a distinct, easily-built characteristic (time-series vol of turnover) and a rare case where the empirical sign contradicts naive risk intuition, which makes it a sharp test of whether our pipeline can honestly reproduce a surprising priced second moment.
- **可測性(免費資料)**:yes. Dollar volume & turnover time series from OHLCV + EDGAR shares; compute rolling mean & CV; PIT clean; cost ~$0. Caveat: Nasdaq volume double-counting; the negative-sign result is fragile and later literature disputes it — good stress test for our data-snooping controls.
- **TR 切入(含 Nagel 對照)**:Sort on CV-of-turnover (and CV-of-$volume), decile L/S controlling for the turnover level. Nagel gauntlet: (1) static exposure — is CV-of-turnover just a repackaged size or idio-vol tilt? Neutralize both; (2) 1/σ² Moreira-Muir control (turnover-vol correlates with return-vol), require residual alpha t≥2; (3) random-entry null. Apply Harvey-Liu-Zhu t≥3 threshold given the sign is contested — pre-commit to FAILED unless the surprising negative sign survives both level-control and vol-management.

#### sadka2006-liquidityrisk-momentum-pead — Sadka (2006) · ~1300 引用 · 「Momentum and Post-Earnings-Announcement Drift Anomalies: The Role of Liquidity Risk」
- **主張 / 與我方關聯**:Firm-level price impact decomposes into a fixed (transitory) and a variable (permanent, information-driven) component; the variable component has a systematic, priced factor that explains a large share of momentum and post-earnings-announcement-drift returns — these anomalies are partly liquidity-risk premia. → Speaks directly to WHY our momentum failed as stock-selection alpha (ICIR≈0): if momentum profits are compensation for a liquidity-risk factor, then in a liquid mega-cap seat with no liquidity-risk dispersion the premium should vanish — exactly what we observed. Reframes a FAILED anomaly as a mis-seated risk premium (T1 mis-seat candidate).
- **可測性(免費資料)**:partial. Sadka's exact permanent/transitory decomposition needs intraday transaction/order-flow data (T2 information cost). BUT the priced liquidity-risk FACTOR can be proxied from daily data via Pastor-Stambaugh / Amihud innovations, then used as a control/beta. Proxy path cost ~$0; exact decomposition needs intraday.
- **TR 切入(含 Nagel 對照)**:Diagnostic (not new signal): build a daily-data liquidity-risk factor (Amihud-innovation or P-S traded factor), then regress our momentum & (later, when earnings dates land) PEAD returns on it — does liquidity-risk beta absorb the (already ≈0) momentum alpha? Nagel framing: show the momentum book's residual after liquidity-risk AND 1/σ² vol-management is indistinguishable from zero (t<2), confirming momentum here = beta, not selection alpha. No standalone tilt; positions as the 'why momentum is a liquidity-risk premium, not alpha' explainer for docs/19.

#### jobson-korkie-1981 — Jobson & Korkie (1981) · ~1300 引用 · 「Performance Hypothesis Testing with the Sharpe and Treynor Measures」
- **主張 / 與我方關聯**:給兩 Sharpe(及 Treynor)差的漸近常態檢定;原式有代數錯誤,Memmel(2003)修正——常態假設下有效,肥尾下失真(故需 LW08)。 → 是 Sharpe 比較檢定的原始出處與教學基準;先用 JK/Memmel 得快速漸近 p,再用 LW08 做肥尾穩健複核,兩者對照即知常態假設影響多大。
- **可測性(免費資料)**:yes — 閉式公式,套既有報酬;無新資料;算力≈0。
- **TR 切入(含 Nagel 對照)**:TR:對關鍵 Sharpe 比較同時報 JK/Memmel 漸近 p 與 LW08 自助 p;Nagel 對照=隨機進場,確認真策略在兩法下皆顯著勝控制,並量化常態假設在我們肥尾日報酬上的偏差。

#### abarbanell-bushee-1998 — Abarbanell & Bushee (1998) · ~1300 引用 · 「Abnormal Returns to a Fundamental Analysis Strategy」
- **主張 / 與我方關聯**:用 Lev-Thiagarajan 基本面訊號建構的交易策略年超額報酬約 13%，部分在後續盈餘公告日實現，證訊號捕捉市場對未來盈餘的低估。 → 把基本面訊號從『解釋』推進到『可交易組合 + 事件實現』，並連結到 PEAD(報酬在後續公告日兌現)。是基本面訊號 lineage 中最直接的回測藍本，EDGAR 可測。
- **可測性(免費資料)**:yes — 訊號全 EDGAR；『後續公告日兌現』檢定需 EDGAR 申報日(本專案已有)；PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 復現其基本面 L/S，並加做『報酬是否聚集於後續 4 個財報公告窗』的兌現檢定(連結 PEAD TR)。必須打敗:(a) 隨機進場，(b) 靜態曝險，(c) GP/價值對照。

#### lesmond_schill_zhou_2004_illusory_momentum — Lesmond, Schill & Zhou (2004) · ~1200 引用 · 「The Illusory Nature of Momentum Profits」
- **主張 / 與我方關聯**:Momentum's paper profits are 'illusory' because winners and losers are disproportionately small, low-priced, high-bid-ask-spread stocks; once realistic round-trip trading costs are charged, the strategy's net return collapses toward zero. → This is the academic backbone of our own cost-wall / F2 discipline and long-only $0 constraint; it predicts exactly why our net-of-cost momentum died and sets the honest bar any momentum TR must clear.
- **可測性(免費資料)**:partial. Momentum legs from free daily OHLCV (yes); the realistic-cost overlay needs a spread/impact model - we have costs.py and can approximate spreads from price level + volume, but true historical bid-ask is not in the free stack, so cost realism is approximate -> partial.
- **TR 切入(含 Nagel 對照)**:Re-run momentum deciles on 503 universe charging costs.py spreads that scale with 1/price and inverse-volume (their key mechanism), and report gross vs net decay by cost quintile. Nagel control it must beat: STATIC EXPOSURE - the honest baseline is buy-and-hold; the test is whether ANY net-of-cost momentum survives, and whether the residual is just 1/sigma^2 vol-managed repackaging. Pre-commit: confirms momentum's value is diagnostic (cost-gate calibration), not a tradable long-only sleeve.

#### dittmar-2002-cokurtosis-pricing-kernel — Dittmar (2002) · ~1200 引用 · 「Nonlinear Pricing Kernels, Kurtosis Preference, and Evidence from the Cross-Section of Equity Returns」
- **主張 / 與我方關聯**:A pricing kernel nonlinear in the market return (embedding kurtosis preference) prices the cross-section better than mean-variance; cokurtosis (comovement with market cubed / extreme co-movement) is priced beyond beta and coskewness. Investors demand compensation for assets that add fat-tail comovement. → Completes the higher-co-moment ladder alongside Harvey-Siddique (coskewness): together they let the project test whether ANY free-data higher-moment exposure is a durable premium or just a beta/size tilt — a systematic sweep of the 'is it risk or is it noise' question the whole project is organized around.
- **可測性(免費資料)**:yes. Cokurtosis = standardized E[ε_i · ε_m^3] from trailing daily stock + index returns; free OHLCV + index. PIT OK (trailing). Cost ~$0. Caveat: higher co-moments are noisily estimated on ~500 names and correlate mechanically with beta/coskewness — needs orthogonalization.
- **TR 切入(含 Nagel 對照)**:TR: estimate coskewness and cokurtosis jointly, quintile-sort on cokurtosis orthogonalized to beta+coskew, net-cost L/S. Nagel controls: (a) static exposure of the high-cokurt basket; (b) 1/σ² vol management (extreme-comovement names are high-vol → must beat vol-managed control); (c) placebo co-moment. Run alongside harvey-siddique-2000 in one TR so both higher moments share the estimation harness. Pre-commit: a co-moment is 'priced' only if its orthogonalized L/S survives net cost and beats static+vol-managed controls; expectation (given the project's prior) = mostly absorbed by beta/size, adding a pillar to the '$0 data → risk-shaping only' thesis.

#### asness-frazzini-pedersen-2019-qmj — Asness, Frazzini & Pedersen (2019) · ~1200 引用 · 「Quality Minus Junk」
- **主張 / 與我方關聯**:以獲利力、成長、安全性、派息四支柱合成品質分數，QMJ L/S 在美股及國際皆有顯著風險調整報酬;高品質股『應該』更貴但溢價不足，故可預測報酬。 → 本專案唯一 PASSED 因子是 Novy-Marx GP(獲利);QMJ 是其自然擴張(把品質從單一 GP 擴成四支柱複合)。直接測『更豐富的品質定義能否再加 alpha』。
- **可測性(免費資料)**:partial — 獲利/成長/安全支柱多數 EDGAR 可算;派息與部分安全指標(如 beta、bankruptcy score)需價量+EDGAR 組合。國際分支 no。美股分支 yes；PIT 可行;成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 在美股宇宙建四支柱 QMJ L/S，做與既有 GP sleeve 的 spanning(QMJ 是否吸收 GP、是否增量)。必須打敗:(a) 單一 GP 品質(證複合增量)，(b) 零訊號品質籃子，(c) 靜態曝險。長只 sleeve 須 L/S 隔離(docs/00 §E9A)。

#### hirshleifer-hou-teoh-zhang-2004-noa — Hirshleifer, Hou, Teoh & Zhang (2004) · ~1100 引用 · 「Do Investors Overvalue Firms with Bloated Balance Sheets? (Net Operating Assets)」
- **主張 / 與我方關聯**:淨營業資產(NOA=累積應計的存量版)/落後總資產越高，後續長期報酬越低——資產負債表『膨脹』是比流量應計更持久的過度樂觀訊號。 → accruals 的存量對應，且是 Sloan 流量版的強力補強；提供『存量 vs 流量哪個在我方座位存活』的判別。
- **可測性(免費資料)**:yes — NOA(營業資產−營業負債) by EDGAR。
- **TR 切入(含 Nagel 對照)**:NOA decile L/S，對照 Sloan 流量應計版與 shuffle；檢驗存量 vs 流量應計哪個在我方座位存活、beat 隨機分位與 FF5 靜態 beta。

#### stambaugh-yuan-2017-mispricing-factors — Stambaugh & Yuan (2017) · ~1100 引用 · 「Mispricing Factors」
- **主張 / 與我方關聯**:把 11 個異常聚成兩個複合 mispricing 因子(MGMT 管理面、PERF 表現面)，加市場與 size 的四因子模型，橫斷面解釋力優於 FF5 與 q-factor。 → 『複合因子』的建構範本——如何把 zoo 壓成少數穩健複合，直接對應我方 multi-sleeve(唯一顯著 α，t=2.64)的組合邏輯。
- **可測性(免費資料)**:yes(大部分)— 11 個成分異常多由 EDGAR+OHLCV 建；聚合方法可複現。
- **TR 切入(含 Nagel 對照)**:建 MGMT+PERF 複合排序 L/S，對照個別異常與 shuffle；檢驗複合是否比單因子更 beat 隨機分位，並以市場中性 L/S 隔離 beta(呼應 docs/00 多 sleeve)。須 beat FF5 靜態曝險。

#### pontiff_2006_costly_arbitrage — Pontiff (2006) · ~1100 引用 · 「Costly Arbitrage and the Myth of Idiosyncratic Risk」
- **主張 / 與我方關聯**:Idiosyncratic risk is the largest arbitrage cost — a HOLDING cost borne every period (unlike one-time transaction costs) — so for a focused arbitrageur it is binding, not diversifiable; this is why anomalies survive. → The theoretical backbone for the whole 'idio-vol moderates anomalies' cluster (Ali-Hwang-Trombley, Mashruwala, SYY-2015) and directly instruments our G-S 'information/holding cost' framing — idio risk IS the cost that pays surviving mispricing. Guides WHERE (high-idio-vol) our long-only anomalies should still work.
- **可測性(免費資料)**:PARTIAL (framing paper, not a standalone signal). Its testable core = anomaly magnitude rises in idio vol (holding cost), buildable free (idio vol from OHLCV × any anomaly from EDGAR+price). PIT OK; cost $0. Best adopted as the meta-framework that motivates the AHT/Mashruwala/SYY TRs rather than a separate sleeve.
- **TR 切入(含 Nagel 對照)**:Meta-test: regress each of our anomaly spreads' magnitude on the idio-vol quintile; Pontiff predicts a monotone increase, and that idio vol dominates transaction-cost proxies. Nagel controls: the incremental anomaly return in high-idio-vol names must beat (1) 1/σ² vol management (high idio vol ≠ total-vol timing) and (2) a static high-idio-vol basket; (3) placebo idio-vol rank. Pre-commit: adopt as the F2/limits-to-arb 'holding-cost' CONVENTION, not a tradable sleeve; framework confirmed if idio vol > transaction cost as the dominant anomaly moderator.

#### kozak-nagel-santosh-2020-shrinking — Kozak, Nagel & Santosh (2020) · ~1100 引用 · 「Shrinking the Cross-Section」
- **主張 / 與我方關聯**:用 characteristics-managed portfolios 建 SDF，並以貝式/L2 收縮於主成分空間估係數;少數穩健主成分即解釋橫斷面，純稀疏(few-characteristic)模型反而較差——關鍵是收縮而非選變數。 → 這是 Nagel 本人的 SDF-ML 框架;既是本專案 Nagel 對照的思想源頭，也是把多個 EDGAR/價量特徵合成為單一穩健 SDF 的現代方法。測『收縮 SDF 能否在小宇宙勝樸素因子加總』直接對話本專案 Ledoit-Wolf/PCA 慣例。
- **可測性(免費資料)**:partial — 方法(L2 收縮於 characteristic-managed PC 空間)完全可實作;但『數十特徵 × 廣宇宙』的原生棲地在 610 檔小宇宙會受廣度限制(docs/11 綁定約束)。特徵子集 yes;完整棲地 partial;PIT 可行;成本≈$0(算力)。
- **TR 切入(含 Nagel 對照)**:TR 用本專案可得特徵(GP、應計、動量、size、投資…)建 characteristic-managed portfolios，跑 KNS 收縮 SDF，對照(a) 樸素等權因子 SDF、(b) Ledoit-Wolf/PCA(TR-03)、(c) 隨機特徵 SDF。檢驗收縮是否在小宇宙仍勝;並記錄『廣宇宙/多特徵=一筆資訊成本』翻案條件。

#### kelly-pruitt-su-2019-ipca — Kelly, Pruitt & Su (2019) · ~1100 引用 · 「Characteristics Are Covariances: A Unified Model of Risk and Return (IPCA)」
- **主張 / 與我方關聯**:IPCA 讓特徵決定時變因子暴露(而非直接是 alpha)，少數潛在因子即解釋橫斷面與時序;多數特徵的『anomaly alpha』在 IPCA 下消失，代表它們是 beta 而非 alpha。 → 直接對話本專案反覆的發現『動量=beta 非 alpha』(TR-11)。IPCA 給出可檢定框架:哪些 EDGAR/價量特徵是真 alpha、哪些只是時變 beta。是 GKX 之外另一條 ML 資產定價主線。
- **可測性(免費資料)**:partial — IPCA 演算法(交替最小平方)可自實作;但穩健估計需夠多特徵×夠廣宇宙，本專案小宇宙會受限。特徵子集 yes;完整棲地 partial;PIT 可行;成本≈$0(算力)。
- **TR 切入(含 Nagel 對照)**:TR 用 IPCA 把本專案特徵拆成『時變 beta 載荷 vs 殘差 alpha』，正式檢定 GP/應計/動量是 alpha 還 beta(對照 TR-06/TR-11 的 beta 結論)。必須打敗靜態因子模型(FF5)的截距檢定;並回報特徵數不足時的估計不穩定。

#### mashruwala_rajgopal_shevlin_2006_accrual_arbitrage — Mashruwala, Rajgopal & Shevlin (2006) · ~1000 引用 · 「Why is the Accrual Anomaly Not Arbitraged Away? The Role of Idiosyncratic Risk and Transaction Costs」
- **主張 / 與我方關聯**:The accrual anomaly (Sloan 1996) persists because arbitrage is costly: extreme-accrual firms have high idiosyncratic volatility (no close substitute → arbitrage risk) AND low price / low volume (high transaction costs), so arbitrageurs can't profitably correct the mispricing. → Pairs with the already-listed sloan-1996-accruals to show WHY the anomaly survives; a concrete limits-to-arb test on an anomaly we can fully build from EDGAR, operationalizing the G-S 'who pays the cost' logic — and it warns that accrual alpha sits exactly where WE also can't cheaply harvest it.
- **可測性(免費資料)**:YES/PARTIAL. Total accruals from EDGAR (balance-sheet or cash-flow method — already noted buildable in the ledger); idio vol from OHLCV; transaction-cost proxies = price level, dollar volume, Amihud ILLIQ (all free, amihud already in list). PIT OK; cost $0. Caveat: large-cap universe = low-arb-cost seat → predicts a weak accrual anomaly here.
- **TR 切入(含 Nagel 對照)**:Build an accrual-decile L/S, then partition by idio vol and Amihud; test that the anomaly concentrates in high-arb-cost names. Nagel controls: (1) static exposure = a constant low-accrual tilt; (2) 1/σ² vol management; (3) placebo accrual / arb-cost rank. Pre-commit: after charging realistic bid-ask + size-dependent impact (costs.py) on the high-arb-cost leg, the tradable accrual L/S should collapse precisely where the anomaly is largest → durable value = confirming the limits-to-arb gate, not a sleeve.

#### fss-2003-spurious — Ferson, Sarkissian & Simin (2003) · ~1000 引用 · 「Spurious Regressions in Financial Economics?」
- **主張 / 與我方關聯**:若真實期望報酬具持續性,一個獨立的持續變數會與之偽相關,產生 Yule 型偽迴歸;疊加資料窺探後,已發表的預測子多半站不住。 → 為我們對 valuation/情緒/regime 預測子的懷疑論提供正式引用;直接支撐 fabric『免費資料上可預測性≈0』先驗,並給偽迴歸診斷。
- **可測性(免費資料)**:yes — 模擬持續預測子 + 我們指數歷史;純方法/模擬;算力小。
- **TR 切入(含 Nagel 對照)**:TR:對任一時序預測子做 FSS 偽迴歸診斷(模擬持續 null 下的 t 分布)判其顯著是否超出偽迴歸帶;Nagel 對照=隨機進場 + 靜態曝險,確認只有非偽的預測子在偽迴歸校正後仍能擇時勝控制。

#### feng-giglio-xiu-2020-taming — Feng, Giglio & Xiu (2020) · ~1000 引用 · 「Taming the Factor Zoo: A Test for the Number of Factors」
- **主張 / 與我方關聯**:用 double-selection LASSO 控制既有因子後，檢定新因子是否有增量定價貢獻，修正『因子動物園』中大量因子在控制其他因子後失去顯著性的問題。 → 本專案的核心紀律是『這個因子是真增量還是重貼標籤』(反覆用 spanning/Harvey-Liu-Zhu 門檻)。FGX 提供正規的增量因子檢定，可制度化進 fabric 的因子閘。
- **可測性(免費資料)**:yes — 只需一組因子報酬時序(可自建)跑 double-selection LASSO;PIT 對因子層次不太綁;成本≈$0。
- **TR 切入(含 Nagel 對照)**:把 FGX double-selection 檢定制度化為 fabric 因子閘的一環:每個新候選因子(GP、應計、BAB…)須通過『控制既有因子後仍有增量 SDF 貢獻』。作為方法論工具而非策略;對照現有 Harvey-Liu-Zhu t 門檻，檢驗哪個更嚴。無須打敗 Nagel 對照(非策略)，但輸出用於 gating 所有策略 TR。

#### daniel-titman-2006-intangible — Daniel & Titman (2006) · ~950 引用 · 「Market Reactions to Tangible and Intangible Information」
- **主張 / 與我方關聯**:未來報酬由『無形資訊』(過去 5 年報酬中無法由基本面成長解釋的部分)反向預測，而非帳面/價值比率本身；複合股權發行變數捕捉之，B/M 的預測力其實來自過去表現反轉。 → 把 value 溢酬重新詮釋為『過去表現反轉/無形資訊』，對我方 value-death 診斷提供替代機制；連結 net-issuance 與 value 兩子領域。
- **可測性(免費資料)**:partial/yes — 需 5 年報酬 + 帳面成長分解與複合發行，皆免費但需較長歷史。
- **TR 切入(含 Nagel 對照)**:建 intangible-return 殘差 L/S(過去 5 年報酬中基本面無法解釋的部分)，對照 B/M 與 net-issuance；檢驗 value 溢酬是否實為無形資訊反轉，須 beat shuffle 隨機分位與 FF5 靜態 beta。

#### gervais_kaniel_mingelgrin_2001_high_volume — Gervais, Kaniel & Mingelgrin (2001) · ~950 引用 · 「The High-Volume Return Premium」
- **主張 / 與我方關聯**:Stocks experiencing abnormally high trading volume over a day or week subsequently earn higher returns over the next 1-4 weeks (and abnormally low volume, lower returns), a 'high-volume return premium' attributed to a visibility/attention shift in investor demand. → A free, volume-only signal orthogonal to price momentum that could form a distinct sleeve or a conditioning variable, and tests whether attention shocks add over the price-based signals we already ran.
- **可測性(免費資料)**:yes, fully. Abnormal-volume classification and forward returns from free daily OHLCV (volume field) vs a trailing volume reference; PIT trivial; cost $0.
- **TR 切入(含 Nagel 對照)**:Classify high/low abnormal-volume names weekly on the 503 universe, hold 1-4 weeks, net-of-cost L/S and long-only. Nagel controls it must beat: (1) random-entry / zero-signal placebo (primary), (2) static exposure, (3) 1/sigma^2 vol management. Also horse-race vs price momentum and Lee-Swaminathan turnover to check it is not the same edge. PASSED only if net-cost high-volume premium survives weekly turnover costs.

#### mohanram-2005-gscore — Mohanram (2005) · ~950 引用 · 「Separating Winners from Losers Among Low Book-to-Market Stocks Using Financial Statement Analysis」
- **主張 / 與我方關聯**:Piotroski F-score 對低 B/M 成長股無效；改用 8 項成長導向訊號(盈餘/現金流穩定度、R&D、廣告、資本支出強度)組 G-score，在成長股內做多高分年報酬顯著較高。 → 補 F-score 的鏡像:本專案宇宙(S&P500/科技偏重)以成長股為主，F-score 反而不適用；G-score 才是這個座位對的基本面複合訊號。EDGAR 可複製。
- **可測性(免費資料)**:partial — 多數訊號(ROA、現金流、盈餘變異)EDGAR yes；R&D/廣告強度需 EDGAR XBRL 標記(部分公司缺、標記不一致)→ 中等工程。PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 在低 B/M 子集建 G-score L/S。必須打敗:(a) 同子集隨機/零訊號籃子，(b) 純成長(低 B/M)持有，(c) 靜態 VOO。與 Piotroski F-score TR 並列，檢驗『座位=成長 vs 價值』決定哪個計分有效。

#### blitz-vanvliet-2007-vol-effect — Blitz & van Vliet (2007) · ~900 引用 · 「The Volatility Effect: Lower Risk Without Lower Return」
- **主張 / 與我方關聯**:全球低波動股 Sharpe 顯著高於高波動股，且低波不犧牲絕對報酬——低波投資的實務奠基，效應獨立於 value/size。 → low-vol 因子的實務建構範本(可投資、低換手)；與 docs/09 lowvol 反轉直接對照，測效應是否在我方年代/宇宙消失。
- **可測性(免費資料)**:yes(美股部分)— vol-sorted deciles from OHLCV。
- **TR 切入(含 Nagel 對照)**:vol decile L/S，對照 shuffle 與 1/σ² vol-managed overlay；檢驗低波效應在 2015-24 科技牛市是否消失/反轉(對照 docs/09)，須 beat 隨機分位與靜態 beta。

#### green-hand-zhang-2017-characteristics — Green, Hand & Zhang (2017) · ~900 引用 · 「The Characteristics that Provide Independent Information About Average U.S. Monthly Stock Returns」
- **主張 / 與我方關聯**:在 94 個公司特徵中，多變量 Fama-MacBeth 下僅約 12 個在 2003 後仍提供『獨立』的橫斷面報酬資訊，且獨立特徵數逐年下降——大半 zoo 在聯合下冗餘。 → 直接回答『zoo 這麼大，哪些聯合下仍有增量』——指引我方不浪費算力重測冗餘因子，並與 docs/00『唯一穩健=GP』的稀疏結論呼應。
- **可測性(免費資料)**:partial — 多數會計/量價特徵(EDGAR+OHLCV)可建，少數需 IBES 分析師/機構持股(no)。
- **TR 切入(含 Nagel 對照)**:在我方可建的特徵子集跑多變量 Fama-MacBeth，找『聯合顯著』殘存特徵；對照單變量顯著性量化冗餘，並 beat shuffle 隨機分位——把結果當我方因子清單的剪枝依據。

#### korajczyk_sadka_2004_momentum_trading_costs — Korajczyk & Sadka (2004) · ~850 引用 · 「Are Momentum Profits Robust to Trading Costs?」
- **主張 / 與我方關聯**:Momentum survives proportional (spread) costs for equal- and value-weighted and liquidity-weighted implementations, but non-proportional PRICE-IMPACT costs cap capacity: beyond roughly a few billion dollars of long-side capital, momentum's abnormal returns are eliminated. → Complements Lesmond et al with a capacity/impact angle that maps onto our F2 cost stress and impact model, telling us the size beyond which any momentum sleeve is uninvestable even before our large-cap null.
- **可測性(免費資料)**:partial. Momentum legs from free daily OHLCV; the price-impact model (they use Glosten-Harris/effective spreads) must be approximated from size+volume in costs.py rather than estimated from tick data -> partial, cost realism is our impact-model assumption.
- **TR 切入(含 Nagel 對照)**:Re-run momentum on 503 universe under an increasing-AUM price-impact schedule (impact ~ trade-size/ADV) and find the capacity where net alpha hits zero. Nagel control it must beat: STATIC EXPOSURE at the same AUM (does a passive winner basket degrade less?), plus confirm the residual is not 1/sigma^2 vol-managed repackaging. Diagnostic verdict: calibrates our impact model and the capacity ceiling, not a standalone sleeve.

#### hou_2007_industry_information_diffusion — Hou (2007) · ~800 引用 · 「Industry Information Diffusion and the Lead-Lag Effect in Stock Returns」
- **主張 / 與我方關聯**:Within an industry, the returns of large firms lead those of small firms, and a big-firm industry-return signal predicts small-firm returns; much of the well-known size lead-lag effect is intra-industry information diffusion rather than a market-wide phenomenon. → Connects industry momentum (Moskowitz-Grinblatt, already in ledger) to a testable, free intra-industry lead-lag signal, and offers a cross-predictive overlay (big-firm industry moves) for selecting small names.
- **可測性(免費資料)**:partial/yes. Returns from free daily OHLCV; industry grouping from EDGAR SIC codes (free); size from price x shares; PIT fine; cost $0 - only limitation is our large-cap survivor universe has thin small-firm coverage (mis-seat risk).
- **TR 切入(含 Nagel 對照)**:Group the 503 universe by SIC, build a lagged big-firm industry-return signal, predict small-firm returns intra-industry. Nagel controls it must beat: (1) static exposure to the industry basket (is it just industry beta?), (2) 1/sigma^2 vol management, (3) placebo industry assignment. Habitat caveat: our universe is large-cap-heavy (the followers are thin), so a null is a mis-seat, not a refutation; reopening needs a small-cap PIT universe.

#### brw-2008-longhorizon — Boudoukh, Richardson & Whitelaw (2008) · ~800 引用 · 「The Myth of Long-Horizon Predictability」
- **主張 / 與我方關聯**:長期重疊迴歸的斜率與 R² 隨視窗上升幾乎是機械性上升(係數在 null 下高度相關),不代表真可預測性增強;正確標準誤下長短期證據一致地弱。 → 凡想用『長期報酬更好預測』做低頻擇時的念頭都被此打預防針;對 horizon-framework(docs/14)的重疊視窗設計是直接約束。
- **可測性(免費資料)**:yes — 指數長歷史即可複製重疊迴歸;純方法;算力小。
- **TR 切入(含 Nagel 對照)**:TR:用指數歷史重跑 1/3/5 年重疊預測迴歸,套 BRW 正確 null 分布;Nagel 對照=隨機進場的長期擇時,證明長視窗『看起來可預測』在隨機控制上同樣出現,故非真訊號。

#### freyberger-neuhierl-weber-2020 — Freyberger, Neuhierl & Weber (2020) · ~800 引用 · 「Dissecting Characteristics Nonparametrically」
- **主張 / 與我方關聯**:用 adaptive group LASSO + 樣條非參數估計，62 個特徵中只有約 15 個穩健有增量預測力(含動量、獲利、B/M、應計相關);許多特徵關係高度非線性。 → 回答本專案『哪些特徵值得放進 ML 面板』的實證問題，且方法比 GKX 神經網路更可解釋、更適合小資料/小宇宙。給出 EDGAR/價量特徵的精選短名單。
- **可測性(免費資料)**:partial — 方法可實作;但穩健的變數選擇需夠廣宇宙×62 特徵，小宇宙結果易不穩。特徵子集 yes;完整 partial;PIT 可行;成本≈$0(算力)。
- **TR 切入(含 Nagel 對照)**:TR 用 adaptive group LASSO 在本專案特徵集做非參數選擇 + 邊際形狀估計，對照 GKX(TR-08 FAILED)的高維黑箱:少而可解釋的特徵是否在小宇宙更穩。必須打敗零訊號/隨機特徵基準與靜態曝險;回報選中特徵的 OOS ICIR。

#### bouman_jacobsen_2002_halloween — Bouman & Jacobsen (2002) · ~750 引用 · 「The Halloween Indicator, 'Sell in May and Go Away': Another Puzzle」
- **主張 / 與我方關聯**:在絕大多數國家,11 月至 4 月的股市報酬顯著高於 5 月至 10 月;基於此的『Sell in May』日曆擇時規則在許多市場勝過 buy-and-hold,且此季節性穩健跨國、跨長歷史存在。 → 是最簡單的純日曆市場擇時異常,零工程可測,且是資料窺探/多重測試(Sullivan-Timmermann-White,已在名單)的經典警示對象——正好用本專案的 trial-registry 與 SPA 檢定它是否為 data-snooping 產物。
- **可測性(免費資料)**:yes — 只需指數月報酬。PIT 完美。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:在 SPY + 長指數歷史重建 Halloween 擇時,對照 buy-and-hold 靜態曝險與同在市比例的隨機進場;關鍵不是毛績效而是把它丟進本專案 SPA / trial-registry,檢驗在『所有日曆切分』的多重測試家族中它是否仍顯著(White 2000 / Sullivan-Timmermann-White data-snooping bias)。判 FAILED 若 SPA p 值在校正後失去顯著,判 PARTIAL 若季節性存活但擇時淨值不勝 buy-and-hold。

#### krs-2013-twopass — Kan, Robotti & Shanken (2013) · ~700 引用 · 「Pricing Model Performance and the Two-Pass Cross-Sectional Regression Methodology」
- **主張 / 與我方關聯**:提供在『模型誤設』下仍有效的 t 與橫斷面 R² 標準誤,並給兩個非嵌套模型 R² 是否顯著不同的檢定;Shanken(1992) 的 SE 在誤設下仍偏。 → 當我們宣稱『GP 品質模型 > CAPM』或『多因子 > 單因子』時,KRS 給誠實的模型比較檢定,避免宣稱一模型贏而差異其實在噪音內。
- **可測性(免費資料)**:yes — 套既有因子/投組月報酬;無新資料;中等算力。
- **TR 切入(含 Nagel 對照)**:TR:用 KRS 誤設穩健 R² 檢定比較『GP-augmented 模型 vs FF3』;Nagel 對照=把候選因子換成 1/σ² 波動管理因子與隨機因子,確認 R² 提升在誤設穩健檢定下對真因子顯著、對波動/隨機控制不顯著。

#### afimp-2018-size-junk — Asness, Frazzini, Israel, Moskowitz & Pedersen (2018) · ~650 引用 · 「Size Matters, If You Control Your Junk」
- **主張 / 與我方關聯**:裸 size 溢酬弱且不穩，但控制 quality/junk(QMJ)後 size 溢酬變大、單調、跨時跨國跨產業穩健——size 效應被『垃圾股偏誤』掩蓋。 → 直接接我方唯一存活因子 GP/品質(docs/10 ICIR+0.30)——size×quality 交互可能是把 SMB 從 FAILED 救活的關鍵，且機制與我方已有 EDGAR quality 面同源。
- **可測性(免費資料)**:partial — quality 腿(EDGAR)可建，但 size 腿需小盤宇宙；可先在現有大型股內做『品質中性化 size 殘差』縮小版檢驗，完整版待小盤 ingest。
- **TR 切入(含 Nagel 對照)**:建 QMJ-中性化 size L/S，對照裸 size L/S 與 shuffle 隨機分位；檢驗控制 junk 後 SMB 是否翻正，並以市場中性 L/S 隔離（避免 long-only beta 抬 t，docs/00 §E9A），須 beat FF5 靜態曝險。

#### pettenuzzo_timmermann_valkanov_2014_constraints — Pettenuzzo, Timmermann & Valkanov (2014) · ~650 引用 · 「Forecasting Stock Returns under Economic Constraints」
- **主張 / 與我方關聯**:在標準預測迴歸上施加兩個經濟約束(預測溢酬非負、隱含條件 Sharpe 落在合理上界內),能大幅穩定估計、提升 OOS R² 與資產配置效用,勝過無約束迴歸與歷史均值。 → 是 Campbell-Thompson(已在名單)符號約束的貝式強化版,直接可操作化進我們的擇時 overlay(docs/03 O8);對『無約束迴歸幾乎必敗』提供一個免資料成本、純規則的救援方案。
- **可測性(免費資料)**:yes — 只需指數報酬 + 免費預測子(D/P、CAPE、term spread)。PIT 佳。成本 $0(需實作貝式約束估計)。
- **TR 切入(含 Nagel 對照)**:TR:對同一組預測子跑三版本(無約束 / CT 符號約束 / PTV Sharpe-bound + 非負約束),比較 OOS R² 與轉成部位後的績效;所有版本仍須先打敗 buy-and-hold、1/σ² 與隨機進場。焦點:經濟約束能否把我們一貫 FAILED 的擇時 gate 拉過對照線,或只是縮小 downside 而不產生 alpha。

#### zhu_zhou_2009_moving_average_allocation — Zhu & Zhou (2009) · ~650 引用 · 「Technical Analysis: An Asset Allocation Perspective on the Use of Moving Averages」
- **主張 / 與我方關聯**:當存在報酬可預測性但估計參數不確定時,移動平均擇時規則能作為固定配置的有價值補充,理論上可提升期望效用;MA 的價值來自它對趨勢/不確定性的穩健反應,而非單純的曲線配適。 → 為 Faber 型 SMA 擇時提供理論基礎(何時、為何 MA 規則能勝固定配置),讓我們能從『學習/參數不確定』角度理解本專案擇時失敗——若我們宇宙的可預測性太弱,理論就預測 MA 無增益,與 docs/09 一致。
- **可測性(免費資料)**:yes — 只需指數月報酬 + MA;可實作其效用比較框架。PIT 佳。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:在 SPY 上比較固定配置 vs MA-augmented 配置的實現效用(CRRA),並掃描『假設的可預測性強度』參數,定位 MA 開始勝出的門檻;對照組仍是 buy-and-hold 靜態曝險、1/σ² 與隨機進場。診斷:把我們宇宙估到的可預測性代入,理論是否預測 MA 應該失敗(佐證擇時 FAILED 的根因是廣度/IC 而非規則型式)。

#### kelly_pruitt_2013_present_values — Kelly & Pruitt (2013) · ~650 引用 · 「Market Expectations in the Cross-Section of Present Values」
- **主張 / 與我方關聯**:把橫斷面的組合估值比(如各 size/BM 組合的 B/M)用偏最小平方萃取單一預測因子,能穩健地預測整體市場報酬與股利成長,OOS 表現勝傳統單一估值比迴歸,顯示市場預期藏在橫斷面估值的離散度裡。 → 把『橫斷面 → 時序擇時』橋接起來,且是降維/正則化(對抗過擬合)在市場擇時上的實作樣板;輸入(組合 B/M)全在我們 EDGAR+價格能力範圍,是 KMZ 複雜度主題(已在名單)在低維、可解釋端的對照。
- **可測性(免費資料)**:partial→yes — 需建 size/BM 組合的橫斷面 B/M(EDGAR 帳面權益 PIT + 價格);PLS 三通道可實作。PIT:靠 EDGAR 申報日對齊。成本 $0 但工程量中等。
- **TR 切入(含 Nagel 對照)**:TR:用 25 個 size×BM 組合的 B/M 跑 Kelly-Pruitt PLS 濾波預測 SPY 未來報酬,對照 (a) 單一總體 B/M 迴歸、(b) 歷史均值(Campbell-Thompson 基準);轉成擇時後須先打敗 buy-and-hold、1/σ² 與隨機進場。焦點:橫斷面離散度是否在我們宇宙提供單一 B/M 沒有的增量 OOS R²,或如多數擇時般衰退為零。

#### abdi-ranaldo2017-chl-spread — Abdi & Ranaldo (2017) · ~650 引用 · 「A Simple Estimation of Bid-Ask Spreads from Close, High, and Low Prices」
- **主張 / 與我方關聯**:Using the mid-range (average of daily high and low) as a proxy for the efficient price, the covariance of close-to-mid-range deviations yields a simple, closed-form bid-ask spread estimate ('CHL') that is less biased and more accurate than Roll (1984) and Corwin-Schultz (2012) against TAQ benchmarks. → The current best free-data spread estimator — a direct upgrade to the Roll/CS tools already used in-repo. Lets the spread-premium sleeve rest on the most accurate available $0 proxy, and provides a third independent estimator for the GHT-style estimator-agreement audit.
- **可測性(免費資料)**:yes (fully). Close/high/low from OHLCV; closed-form; PIT clean; cost ~$0. Caveat: still noisy for very liquid names where the true spread is a penny (near estimator resolution) — aggregate to monthly and rank rather than level.
- **TR 切入(含 Nagel 對照)**:Adopt CHL as the primary spread estimator; TR = does the CHL-spread carry a cross-sectional premium beyond Amihud level, and do CHL/CS/Roll/LOT agree on rank (feeds the GHT audit TR)? Nagel gauntlet on the spread tilt: (1) static exposure — residualize against static size + Amihud level (heavy overlap expected); (2) 1/σ² Moreira-Muir control (spread estimate scales with range/vol), require alpha t≥2; (3) random-entry null. Position primarily as a measurement upgrade feeding the Amihud/spread flagship, secondarily as its own priced-spread test.

#### han_yang_zhou_2013_ma_cross_section — Han, Yang & Zhou (2013) · ~600 引用 · 「A New Anomaly: The Cross-Sectional Profitability of Technical Analysis」
- **主張 / 與我方關聯**:把移動平均擇時套在波動度排序組合上,高波動組合的 MA 擇時獲利最大;由此構造的 MA 時序組合產生顯著的橫斷面 alpha,無法被市場/規模/價值/動量因子解釋,且主要來自成功規避高波動組合的下行。 → 把『技術擇時』從市場層帶到橫斷面層,且訊號完全是我們有的日線 OHLCV;它同時觸及技術/趨勢擇時與波動風險管理兩個 sub-area,是檢驗『MA 擇時是否只是隱性 1/σ² 波動管理』的理想案例。
- **可測性(免費資料)**:yes — 波動排序與 MA 訊號全由免費日線建。PIT 佳。成本 $0(需注意高換手成本,正是本專案 F1 成交時點/成本慣例的用武之地)。
- **TR 切入(含 Nagel 對照)**:TR:重建波動十分位 + MA(如 10/50/200 日)擇時組合,檢驗其 alpha 是否在扣除本專案成本模型與 1/σ² 波動管理對照後仍存活;核心消融=把 MA 訊號替換成『同等在市時間的隨機進場』與『純 1/σ² 縮放』,若 alpha 消失即證明它是波動擇時的重新包裝而非獨立訊號。判 PASS 需勝三 Nagel 對照且淨成本後顯著。

#### bollerslev_marrone_xu_zhou_2014_vrp — Bollerslev, Marrone, Xu & Zhou (2014) · ~600 引用 · 「Stock Return Predictability and Variance Risk Premia: Statistical Inference and International Evidence」
- **主張 / 與我方關聯**:變異數風險溢酬(VRP=隱含變異數−預期已實現變異數)在多國都對短期(1-3 月)股權溢酬有顯著預測力,且在修正重疊樣本推論偏誤後仍穩健,預測力集中在短期並隨國別經濟連結而共動。 → 把 VRP 擇時從美國(BTZ 2009,已在名單)擴到國際並補上正確的重疊樣本推論,是 VRP sub-area 的自然加厚;VIX 是免費長指數,讓這條擇時線在我們資料內大致可測。
- **可測性(免費資料)**:partial→大致 yes(美國腿)— 隱含變異數用 VIX(CBOE 免費,1990-;VXO 至 1986),已實現變異數由指數日報酬算。國際腿=需外國波動指數(partial)。PIT 佳但歷史較短(~1990 起)。成本 $0。
- **TR 切入(含 Nagel 對照)**:TR:建美國 VRP=VIX²−近月已實現變異數,對 SPY 跑 1/3/6 月預測(重疊樣本用 Hodrick/Newey-West 校正,佐以已在名單的 Diebold-Mariano/Clark-West);轉成擇時後須先打敗 buy-and-hold、1/σ² 波動管理與隨機進場。焦點:VRP 的擇時增量是否獨立於單純的 1/σ² 波動曝險(用 Nagel 對照隔離),以及在 1990 後短樣本是否夠力。

#### bali-demirtas-levy-2009-downside-var — Bali, Demirtas & Levy (2009) · ~600 引用 · 「Is There an Intertemporal Relation between Downside Risk and Expected Returns?」
- **主張 / 與我方關聯**:Downside risk measured by Value-at-Risk (and expected shortfall) is positively priced in the cross-section and over time, beyond ordinary variance — the left-tail, not total volatility, is what earns compensation. → A distinct free-data tail measure (empirical VaR from the return distribution) that complements the already-listed Ang-Chen-Xing downside beta: ACX measures downside COMOVEMENT, this measures each stock's own left-tail. Lets the project test whether standalone tail risk (VaR) is priced separately from vol and beta — directly on the project's data, no options.
- **可測性(免費資料)**:yes. VaR = empirical 1st/5th percentile of trailing daily returns per stock; expected shortfall = mean beyond it. Free OHLCV. PIT OK (trailing). Cost ~$0. Lower citation count than the marquee names but a clean, distinct tail construct.
- **TR 切入(含 Nagel 對照)**:TR: compute rolling empirical VaR/ES per name, quintile-sort, net-cost L/S high-VaR minus low-VaR; also test market-VaR as a timing signal. Nagel controls: (a) static exposure of the high-VaR basket (is VaR just beta/vol?); (b) 1/σ² vol management (VaR and vol are near-collinear → the VaR sort must beat a vol-managed book, the binding hurdle); (c) placebo VaR ranking. Orthogonalize VaR to total vol and beta before sorting. Pre-commit: VaR is a separately-priced tail dimension only if the orthogonalized L/S survives net cost and beats vol-managed control; expectation = largely subsumed by volatility, another '$0 data can't separate tail from vol' data point.

### C.3 第三波 — 需付資訊成本(新資料維度)

需要日內 / 選擇權 / tick / 國際 / 小型股等我們目前沒有的資料。先寫下『翻案條件=哪筆資料』,待資料維度打開再排(G-S 紀律)。

#### ball-brown-1968 — Ball & Brown (1968) · ~11000 引用 · 「An Empirical Evaluation of Accounting Income Numbers」
- **主張 / 與我方關聯**:盈餘意外的符號與同期異常報酬同向;且相當部分價格反應在盈餘公告『後』才發生——PEAD 現象的最早文獻證據。 → PEAD/盈餘漂移整條腿的思想源頭與 null 框架;深讀價值在於理解為何『延遲反應』是 EDGAR 事件型 alpha 的物理基礎，供 PEAD TR 立論。
- **可測性(免費資料)**:partial — 概念可用 EDGAR 現代資料重現(即 PEAD TR 本身)，但原論文年代(1946-66)資料不可及;作為背景/立論而非獨立回測。成本≈$0(併入 PEAD TR)。
- **TR 切入(含 Nagel 對照)**:不單獨開 TR;作為 PEAD TR(Bernard-Thomas)的理論母體與 null 說明。若要驗證『延遲反應』普遍性，即以現代 EDGAR 事件研究做公告日 vs 公告後的報酬分解——必須顯示公告後仍有可交易漂移(打敗隨機進場)。

#### heston-1993-stochastic-vol — Heston (1993) · ~10000 引用 · 「A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options」
- **主張 / 與我方關聯**:Options under a mean-reverting square-root variance process with leverage correlation admit a semi-closed-form price, capturing the smile/skew that Black-Scholes cannot. → Mostly a pricing model whose native habitat (options) is unreachable on $0, BUT its physical-side ingredients — mean-reverting variance, vol-of-vol, negative return-vol correlation — are testable stylized facts that upgrade our risk model and drawdown dynamics beyond GBM (TR-05).
- **可測性(免費資料)**:PARTIAL/NO. Pricing use = NO (needs a PIT options chain we do not have; budget). The PHYSICAL variance dynamics (mean-reversion speed, vol-of-vol, corr(return, delta-var)) ARE estimable from free daily index/stock realized vol. Risk-neutral / VRP calibration would need options -> NO.
- **TR 切入(含 Nagel 對照)**:Not a pricing TR. Estimate the physical Heston-style variance process from daily realized vol on our indices and feed it into the Monte-Carlo risk model as a stochastic-vol upgrade to TR-05's GBM, benchmarked against the assumption-free block-bootstrap 'honest MC'. This is risk measurement, not an alpha claim, so the relevant control is the risk-matched static / block-bootstrap baseline (not the Nagel timing triple). Prior: stoch-vol MC narrows the GBM tail gap (TR-05 showed GBM understates tails by orders of magnitude) but still trails the block bootstrap; option-pricing use stays N/A on budget.

#### delong_shleifer_summers_waldmann_1990 — De Long, Shleifer, Summers & Waldmann (1990) · ~9500 引用 · 「Noise Trader Risk in Financial Markets」
- **主張 / 與我方關聯**:Short-horizon arbitrageurs face the risk that noise-trader mispricing worsens before it corrects (noise-trader risk); this risk is systematic, deters arbitrage, and earns a premium, so assets more exposed to sentiment risk are riskier and cheaper. → The theoretical origin of 'sentiment as priced risk' that underpins Baker-Wurgler and Stambaugh-Yu-Yuan; supplies the noise-trader-risk framing for why our sentiment overlays should be treated as a risk premium, not a free lunch. Names the explicitly-requested 'noise trader risk' theme and closes the subdomain's theory quartet.
- **可測性(免費資料)**:PARTIAL/NO for the canonical test. The classic closed-end-fund-discount test (Lee-Shleifer-Thaler) needs CEF discount data — not in our free stack. Free surrogate: a sentiment-risk beta (rolling loading on delta-BW-sentiment) as a priced characteristic, buildable from price + free sentiment index (with the look-ahead caveat). PIT weak. Primarily a framing/foundation paper.
- **TR 切入(含 Nagel 對照)**:Estimate each stock's sentiment-risk beta (rolling loading on delta-BW-sentiment), sort, and test whether high-sentiment-beta stocks carry a return premium (noise-trader-risk compensation). Nagel controls it must beat: (1) static exposure — is high-sentiment-beta just high market-beta / high-vol held long? (Cederburg); (2) 1/sigma^2 vol management — sentiment beta ~ vol exposure, the decisive control; (3) placebo sentiment series. Honest pre-commit: the premium is likely subsumed by market-beta/idio-vol -> verdict = foundational framing confirmed, no separable tradable premium on our seat; its primary role is to justify treating the Baker-Wurgler / SYY overlays as risk premia (G-S consistent), not alpha.

#### merton-1976-jump-diffusion — Merton (1976) · ~8500 引用 · 「Option Pricing When Underlying Stock Returns Are Discontinuous」
- **主張 / 與我方關聯**:Adding lognormal Poisson jumps to geometric Brownian motion produces fat tails/skew and prices the discontinuous crash risk that Black-Scholes omits. → The jump/crash channel is exactly the tail our GBM (TR-05) and normal VaR (TR-04) mispriced; realized jump intensity can also serve as a cross-sectional crash-risk characteristic for selection (avoid high-jump-risk names).
- **可測性(免費資料)**:PARTIAL->YES for the physical side. Jumps are detectable in free daily returns (threshold filters on large |returns| — cruder than intraday bipower but workable); per-name jump intensity/size is estimable from daily OHLCV. Option-pricing calibration = NO (no chain). Point-in-time OK for realized-jump features.
- **TR 切入(含 Nagel 對照)**:Two-pronged. (a) Risk-model TR: add a jump component to the TR-05 Monte-Carlo and test whether jump-diffusion closes the tail/MDD gap vs the block bootstrap (control = risk-matched baseline, not Nagel timing). (b) Selection TR: build a per-name realized-jump-intensity characteristic (count/size of extreme daily moves) and sort the 610 universe — do high-jump-risk stocks underperform risk-adjusted? Must beat zero-signal/random basket (F6) and static EW (F3); double-sort with MAX since extreme daily moves overlap. Prior: jump feature ~ MAX/idio-vol proxy — adds tail realism to the risk model (measurement value) but no clean alpha.

#### loughran-ritter-1995-new-issues — Loughran & Ritter (1995) · ~6000 引用 · 「The New Issues Puzzle」
- **主張 / 與我方關聯**:IPO 與 SEO 後五年顯著跑輸配對非發行公司——『新發行之謎』；發行公司在高估值窗口擇時發行，長期弱勢。 → net-issuance 的事件版與機制(擇時發行)；是 Pontiff-Woodgate 連續版的離散事件對照。
- **可測性(免費資料)**:partial/no — 需 IPO/SEO 事件日；EDGAR 有 S-1/424B/S-3 申報日可近似，但配對與清洗成本高、資料髒。屬 T2 缺乾淨發行事件資料。
- **TR 切入(含 Nagel 對照)**:以 EDGAR 發行申報日近似事件，建發行後日曆時間組合 vs size/BM 配對對照；成本牆=事件日清洗。若落地，對照 shuffle 隨機事件日檢驗弱勢非日曆巧合。

#### french-schwert-stambaugh-1987 — French, Schwert & Stambaugh (1987) · ~5500 引用 · 「Expected Stock Returns and Volatility」
- **主張 / 與我方關聯**:The expected market risk premium rises with predictable (ex-ante) volatility, while unexpected volatility shocks are negatively related to returns — the vol-feedback / leverage asymmetry. → Underwrites whether vol should scale exposure up or down, and the negative-shock channel is the crash/vol-feedback mechanism behind our drawdown overlays; a diagnostic anchor for our regime.
- **可測性(免費資料)**:YES. Only market index daily/monthly returns are needed to build monthly realized vol and test vol-in-mean and the return-vol asymmetry. Free long index history (SPY/QQQ + FF market series back to 1926). Point-in-time OK.
- **TR 切入(含 Nagel 對照)**:Rebuild the ex-ante-vol-in-mean regression and the unexpected-vol asymmetry on our long index history, then a tradable vol-in-mean exposure rule. Nagel controls it MUST beat: 1/sigma^2 vol management (Moreira-Muir), static exposure, random entry (full triple). Prior: the sign/asymmetry replicates as a diagnostic (PARTIAL, vol-feedback confirmed) but as a timing rule collapses into the inverse-variance control — documents the risk-return relation for our era rather than standalone alpha.

#### lettau_ludvigson_2001_cay — Lettau & Ludvigson (2001) · ~3500 引用 · 「Consumption, Aggregate Wealth, and Expected Stock Returns」
- **主張 / 與我方關聯**:消費對總財富與勞動所得的共整合偏離(cay)是股權溢酬的強力短期預測子,樣本內外皆勝股利殖利率等傳統比率,反映跨期消費平滑下的時變風險溢酬。 → macro-predictor sub-area 的旗艦經典(目前名單此區偏薄),且是本專案 PIT 紀律最重要的反面教材:cay 的共整合向量用全樣本估計,惡名昭彰地含 look-ahead,樣本外實時表現大幅衰退——正是我們『座位/資料對齊』判準的活體案例。
- **可測性(免費資料)**:partial — cay 需消費/財富/勞動所得季頻資料(FRED/BEA 免費但在我們核心 OHLCV+EDGAR 之外);且共整合向量的實時估計是主要 PIT 陷阱。指數報酬端 yes。成本 $0(FRED)但屬新資料維度且 PIT 風險高。
- **TR 切入(含 Nagel 對照)**:TR:重建 cay 並跑兩版——(a)全樣本共整合向量(重現原文,示範 look-ahead)、(b)僅用 t 時點前資訊的遞迴估計(誠實 PIT);比較兩版 OOS R² 落差以量化 look-ahead 溢價。擇時部位須先打敗 buy-and-hold、1/σ² 與隨機進場。預期結論=實時 cay 的擇時增益大幅衰退,佐證 McLean-Pontiff 型發表後/樣本外衰退。

#### chordia-roll-subrahmanyam2000-commonality — Chordia, Roll & Subrahmanyam (2000) · ~3000 引用 · 「Commonality in Liquidity (Journal of Financial Economics)」
- **主張 / 與我方關聯**:個股流動性(價差、深度)變動顯著載於市場與產業層流動性變動 → 流動性有系統成分,無法分散,支撐 P-S / Acharya-Pedersen 的 priced liquidity risk。 → 為『流動性風險為何被定價』提供微觀證據(共同成分不可分散);對選股是 P-S/Acharya-Pedersen 的機制解釋,而非直接信號。選股直接適用性較弱。
- **可測性(免費資料)**:PARTIAL。原生度量=日內報價價差/深度,我們沒有。只能用日線 Amihud ΔILLIQ 做 commonality 代理(regress 個股日 ΔILLIQ on 市場日 ΔILLIQ)——是 proxy,非原始報價版本。Point-in-time OK。
- **TR 切入(含 Nagel 對照)**:用日線 Amihud-based commonality beta(個股 ΔILLIQ 對市場 ΔILLIQ 的載荷)當系統流動性風險排序。Nagel 對照:(1) 靜態曝險——commonality beta 是否只是 market beta / size?中性化後檢查;(2) 隨機組合 null;(3) 高 commonality 在危機爆發 → 對照 1/σ² 波動管理。定位=P-S TR 的 supporting sleeve(驗證共同成分存在並被定價),非旗艦。

#### francis-lafond-olsson-schipper-2005 — Francis, LaFond, Olsson & Schipper (2005) · ~3000 引用 · 「The Market Pricing of Accruals Quality」
- **主張 / 與我方關聯**:以應計品質(應計對現金流的映射穩定度)衡量資訊風險，較差品質公司有較高權益資金成本與較高預期報酬;應計品質是被定價的資訊風險維度。 → 把應計從『mispricing』延伸到『被定價的資訊風險』，提供另一個 EDGAR 可算的品質/風險維度，並與本專案 GP 品質、Sloan 應計形成可比較的三方 spanning。
- **可測性(免費資料)**:partial — 應計品質需估 Dechow-Dichev 迴歸(應計對前中後期現金流)，需多年時序 per firm;EDGAR 可算但工程量中等;PIT 需 rolling 估計。yes-但工程;成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 建應計品質分位 L/S，並與 Sloan 應計、GP 品質做三方 spanning(誰是增量)。檢驗它究竟是 mispricing(可套利消失)還定價風險(持續)。必須打敗零訊號基本面籃子與靜態曝險。

#### rouwenhorst_1998_international_momentum — Rouwenhorst (1998) · ~2600 引用 · 「International Momentum Strategies」
- **主張 / 與我方關聯**:Medium-term momentum (3-12 month) is present and significant in 12 European countries, works across all size groups (strongest in small firms), and is correlated with US momentum - establishing momentum as a robust non-US-specific phenomenon. → The geographic OOS test that inoculates momentum against data-mining claims; relevant as theory backing even though we cannot rebuild it, and a benchmark for how strong momentum 'should' be if our large-cap null is a habitat artifact.
- **可測性(免費資料)**:no / partial. Requires international (12-country) equity price data not in our free US-only stack; the mechanism is theory-backing only, not rebuildable; a US-only re-derivation adds nothing new beyond JT-type tests already run -> effectively not testable on our seat.
- **TR 切入(含 Nagel 對照)**:Not a standalone TR on our seat (no international data); use as theory-backing to interpret our US null - if momentum is globally robust yet dead in our large-cap survivor universe, that argues mis-seat (habitat) rather than non-existence. Any US re-test still faces the same Nagel controls (variance-scaled WML, static exposure, random entry). Reopen trigger: acquiring an international PIT universe = a clear G-S information cost.

#### bakshi-kapadia-madan-2003-implied-moments — Bakshi, Kapadia & Madan (2003) · ~2600 引用 · 「Stock Return Characteristics, Skew Laws, and the Differential Pricing of Individual Equity Options」
- **主張 / 與我方關聯**:Given a strip of out-of-the-money options across strikes, one can compute the risk-neutral variance, skewness, and kurtosis model-free via spanning/replication; individual equity risk-neutral distributions are much less negatively skewed than the index, explaining the differential pricing (skew) of individual vs index options. → The >2000 methodological classic that MANUFACTURES the implied-moment predictors the rest of this batch uses (Xing's smirk, Conrad-Dittmar-Ghysels ex-ante skew, the VIX itself). Including it documents the single largest locked capability behind the options paywall: the whole risk-neutral-moment toolkit. It also connects to the already-listed btz09_vrp / heston entries by supplying the measurement layer.
- **可測性(免費資料)**:no for the implied side (needs the full OTM option strike cross-section — paid). One free exception: the INDEX risk-neutral variance is exactly the VIX² construction (VIX free from CBOE, 1990-), so market-level BKM variance is partially testable; per-stock and skew/kurt are options-gated. Mark T2 (reopen on options feed) / partial at index level. Cost: paid options chains.
- **TR 切入(含 Nagel 對照)**:TR (mostly data-gated, T2): (i) free slice — reconstruct index risk-neutral variance from VIX and compare to realized (a BKM-consistent view of the VRP already partly covered by btz09_vrp); (ii) gated slice — once options exist, compute per-stock risk-neutral skew and sort. Nagel controls for any tradable use: risk-neutral-skew L/S must beat (a) static exposure, (b) 1/σ² vol management, and (c) the FREE realized-skew/coskew signals (Harvey-Siddique, Boyer-Mitton-Vorkink) — the acid test of whether risk-neutral (forward-looking) moments add anything over physical ones. Pre-commit: this is the master reopen-condition for the entire implied-moment family; fund it only if the index-VIX slice already shows the implied moment carries information the free realized moment lacks.

#### rosenberg-reid-lanstein-1985-bm — Rosenberg, Reid & Lanstein (1985) · ~2500 引用 · 「Persuasive Evidence of Market Inefficiency」
- **主張 / 與我方關聯**:高 book-to-market 股有正 α(book/price 異常的原始證據)，並記錄短期(月)反轉——『市場無效』的說服性證據，早於 FF1992。 → B/M 溢酬的原始出處(FF1992 的前身)；對追溯 value-death 的建構細節有基準價值。
- **可測性(免費資料)**:yes — B/M = 帳面權益(EDGAR)/市值，全免費。
- **TR 切入(含 Nagel 對照)**:B/M decile L/S，市場中性後對照 shuffle 與 FF5 靜態 beta；與 Asness-Frazzini『devil in HML』的估值時點版並跑(當期 vs 落後價格)，診斷 value 死是機制失效或建構偽陰。

#### carr-wu-2009-variance-risk-premiums — Carr & Wu (2009) · ~2100 引用 · 「Variance Risk Premiums」
- **主張 / 與我方關聯**:The variance risk premium (realized variance minus the model-free synthetic variance-swap rate) is large and negative for the index (sellers of variance earn a premium) and varies across individual stocks; it is not spanned by the market return, implying an independent priced volatility factor. → The measurement-methodology classic behind the already-listed btz09_vrp entry, and the source of the individual-stock VRP that could become a cross-sectional selection signal. At the market level the index VRP is a well-known return predictor (timing), directly on the project's Nagel battleground of vol-based timing; the per-stock VRP is the options-gated extension.
- **可測性(免費資料)**:partial. Market-level: synthetic index variance swap ≈ VIX² (free, CBOE 1990-), realized variance from index daily returns → the index VRP is buildable and overlaps btz09_vrp — usable NOW as a timing signal. Per-stock VRP needs individual option chains (paid) → T2. PIT OK for the index slice. Cost: $0 index / paid per-stock.
- **TR 切入(含 Nagel 對照)**:TR: (i) free slice — build the market VRP as VIX²−RV and test it as a market-timing overlay; (ii) gated slice — per-stock VRP sort when options exist. Nagel controls for the timing slice (this is the core Nagel fight): the VRP-timed market book must beat (a) constant/static exposure and (b) a 1/σ² vol-managed market book with alpha-t≥2 — because VRP timing and vol timing are deeply entangled, this is the decisive control; (c) random-entry placebo → Sharpe≈0. Pre-commit: index VRP earns 'real timing signal' status only if it beats the 1/σ² control net of cost; expectation given the project's Moreira-Muir/Cederburg results = largely a vol-timing relabel, making the per-stock (paid) extension the only place genuinely new alpha could hide.

#### foster-olsen-shevlin-1984 — Foster, Olsen & Shevlin (1984) · ~1900 引用 · 「Earnings Releases, Anomalies, and the Behavior of Security Returns」
- **主張 / 與我方關聯**:以時序模型的未預期盈餘(UE)排序，申報後 60 天存在單調漂移；驚奇型度量(analyst-free 時序)即足以捕捉，且與 size 效應交互。 → PEAD 的原始建構論文，給出 analyst-free 的時序盈餘期望模型——正是 $0 免費資料唯一可行的 SUE 建法(無分析師預測)。是 B&T 之前的方法藍本。
- **可測性(免費資料)**:yes — 純 EDGAR 季 EPS 時序建 UE；PIT 可行；成本≈$0。
- **TR 切入(含 Nagel 對照)**:作為 PEAD TR 的 SUE 建構對照:比較『時序 UE(FOS)』vs『季節隨機漫步 SUE(B&T)』兩種免費建法哪個 drift 訊號更強。必須打敗隨機進場與靜態曝險，並回報兩種 UE 定義的 ICIR 穩健度。

#### ou-penman-1989 — Ou & Penman (1989) · ~1900 引用 · 「Financial Statement Analysis and the Prediction of Stock Returns」
- **主張 / 與我方關聯**:以大量財報比率用邏輯迴歸合成單一『Pr』分數預測未來盈餘變動方向，據以建構的 L/S 兩年累積約 12.5% 異常報酬——早期『用整份財報做量化預測』的先驅。 → 是複合基本面預測(現代 ML 資產定價的會計版前身)的起點，示範如何從整份財報壓縮成單一交易分數——與本專案 ML 因子面板的動機同源，且純 EDGAR。
- **可測性(免費資料)**:yes — 財報比率全 EDGAR；但須注意其樣本內 logit 選變數的前視/過擬合(正是本專案 rigor 強項可審)。PIT 需嚴格 walk-forward 重估係數。成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR 用 walk-forward logit(僅用當期可得財報)重建 Pr 分數 L/S，並以本專案 PBO/CSCV 與 walk-forward 檢查『Ou-Penman 的原始樣本內選變數』是否過擬合 artifact。必須打敗零訊號基本面籃子與靜態曝險。

#### cohen_frazzini_2008_economic_links — Cohen & Frazzini (2008) · ~1500 引用 · 「Economic Links and Predictable Returns」
- **主張 / 與我方關聯**:Stock prices do not promptly incorporate news about economically linked firms: a portfolio long firms whose major customers had high returns and short those with low-return customers earns large monthly alpha, evidence of attention-limited slow cross-firm diffusion. → A cross-firm momentum mechanism distinct from own-price momentum that, if the links can be built from EDGAR customer disclosures, offers a genuinely novel and largely uncrowded signal for stock selection.
- **可測性(免費資料)**:partial. Returns free; the customer-supplier links come from principal-customer disclosures (SFAS 131) in 10-K filings on EDGAR - present but require text parsing + entity matching to build the link graph (nontrivial engineering); PIT feasible from filing dates -> partial, an engineering/info cost.
- **TR 切入(含 Nagel 對照)**:Parse principal-customer disclosures from EDGAR 10-Ks to build the customer link graph, form a customer-return-momentum signal, monthly L/S on the 503 universe. Nagel controls it must beat: (1) own-stock 1/sigma^2 vol-managed momentum (is it just repackaged own-momentum?), (2) static exposure, (3) placebo (random customer links) -> alpha must vanish. Pre-commit: value is a novel cross-firm signal only if it survives net-cost AND is not subsumed by own-momentum + industry.

#### asquith_pathak_ritter_2005_short_interest — Asquith, Pathak & Ritter (2005) · ~1300 引用 · 「Short Interest, Institutional Ownership, and Stock Returns」
- **主張 / 與我方關聯**:Stocks that are simultaneously high short interest AND low institutional ownership (most short-constrained) significantly underperform, with the effect strongest in the most-constrained quintile — overpricing persists when shorting is impeded. → The most DIRECT short-sale-constraint measure (short-interest ratio), complementing Nagel-2005's IO proxy; identifies overpriced names our long-only book should AVOID (a screen, not a short) — squarely the 'short-sale constraints' subdomain keyword.
- **可測性(免費資料)**:PARTIAL. Short interest is published ~bi-monthly by exchanges/FINRA (semi-free, downloadable) but is NOT in our core OHLCV+EDGAR stack → needs an ingest; IO from 13F (free via EDGAR). PIT OK with care for the short-interest report/settlement lag; cost ~$0 plus engineering to ingest the short-interest feed. Caveat: our large-cap high-IO universe rarely binds.
- **TR 切入(含 Nagel 對照)**:Ingest the short-interest ratio, double-sort SIR × IO; test underperformance in the high-SIR/low-IO cell, used as an AVOID screen on the long book. Nagel controls: (1) static exposure — is the underperformance just a small/high-vol tilt? neutralize vs size + vol; (2) 1/σ² vol management; (3) placebo SIR. Pre-commit: value is as a long-only EXCLUSION screen (drop flagged high-SIR/low-IO overpriced names) since the tradable profit is on the un-shortable short side; verdict = measured as the long book's alpha improvement after exclusion.

#### xing-zhang-zhao-2010-vol-smirk — Xing, Zhang & Zhao (2010) · ~900 引用 · 「What Does the Individual Option Volatility Smirk Tell Us About Future Equity Returns?」
- **主張 / 與我方關聯**:The steepness of an individual stock's implied-volatility smirk (OTM-put IV minus ATM-call IV) negatively predicts next-month stock returns by ~10.9%/yr — informed traders' crash fears show up in put skew before they show up in the stock. → The flagship 'option-implied predictor' of the subdomain and a paradigm case of the project's data-dimension thesis: the signal is a leading crash-fear indicator that CANNOT be built from OHLCV, so it maps a concrete reopen condition — 'buy an options chain, unlock this alpha.' Exactly the G-S 'pay the information cost' story made tradable.
- **可測性(免費資料)**:no (for the native signal). Requires per-stock option chains (IV across strikes/maturities) — no free PIT source under the $0 budget (OptionMetrics/IvyDB is paid). Mark T2: reopen when an options-chain feed is acquired. Weak free surrogate: realized-return left-tail / downside semivariance from daily data — but that is a different (backward-looking) construct and will not replicate the informed-trading channel.
- **TR 切入(含 Nagel 對照)**:TR (data-gated, T2): once an options feed exists, compute the smirk, decile-sort, net-cost L/S short high-smirk. Nagel controls: (a) static exposure; (b) 1/σ² vol management — smirk co-moves with vol, so the smirk sort must beat a vol-managed book AND (c) subsume vs the free realized-skew/IVOL predictors above (the whole point is that IMPLIED skew beats REALIZED skew). Placebo = randomized smirk. Pre-commit: the information cost of options data is justified only if the smirk L/S beats BOTH the vol-managed control AND every free skewness signal (Harvey-Siddique, Boyer-Mitton-Vorkink) net of realistic option-driven transaction costs; else the paid data bought nothing over $0 data.

#### cremers-weinbaum-2010-putcall-parity — Cremers & Weinbaum (2010) · ~850 引用 · 「Deviations from Put-Call Parity and Stock Return Predictability」
- **主張 / 與我方關聯**:Stocks whose call implied volatilities exceed their put implied volatilities (positive deviation from put-call parity) outperform stocks with the reverse by ~50 bps/week; the IV spread reflects informed order flow migrating to the options market before it hits the stock. → A second, distinct option-implied cross-sectional predictor (informed-trading channel, orthogonal to Xing's crash-fear smirk), reinforcing the reopen-condition map for options data. Together with Xing and An-Ang-Bali-Cakici it defines the tier-1 wish-list for whatever the project would test first if/when it ever pays the options information cost.
- **可測性(免費資料)**:no (native). Needs matched-strike call/put implied vols → option chains, no free PIT source. Mark T2 (reopen on options feed). No adequate OHLCV surrogate — the signal is defined in implied-vol space.
- **TR 切入(含 Nagel 對照)**:TR (data-gated, T2): compute the call-minus-put IV spread, form weekly L/S long positive-deviation. Nagel controls: (a) static exposure; (b) 1/σ² vol management; (c) subsumption vs short-term reversal and the free skewness/IVOL signals (does the IV spread predict beyond what price already tells us?). Placebo = shuffled IV spread. Pre-commit: the weekly signal must survive weekly-rebalance option/stock transaction costs (F2) — notoriously the killer for a 50 bps/week edge — AND beat the vol-managed control; verdict likely PARTIAL as a diagnostic of informed flow rather than a net-tradable sleeve, again pricing the options information cost.

#### an-ang-bali-cakici-2014-joint-cross-section — An, Ang, Bali & Cakici (2014) · ~750 引用 · 「The Joint Cross Section of Stocks and Options」
- **主張 / 與我方關聯**:Increases in a stock's call implied volatility predict higher future stock returns and increases in put implied volatility predict lower returns; information flows from the options market to the stock market, so IV changes lead stock returns in the cross-section. → A third option-implied cross-sectional predictor (IV-change / lead-lag channel), completing the trio with Xing (smirk) and Cremers-Weinbaum (parity deviation). Ang is a co-author, tying it to the already-listed downside-risk work. Reinforces the concrete, ranked reopen list for options data and the G-S information-cost accounting.
- **可測性(免費資料)**:no (native). Needs per-stock call/put implied vol time series → option chains, no free PIT source. Mark T2 (reopen on options feed). No OHLCV surrogate captures the option-to-stock lead-lag.
- **TR 切入(含 Nagel 對照)**:TR (data-gated, T2): sort on monthly change in call IV (long) and put IV (short). Nagel controls: (a) static exposure; (b) 1/σ² vol management (IV changes are vol-space moves → must beat a vol-managed book); (c) subsumption vs momentum/reversal and vs the other two option signals (does IV-change add beyond smirk + parity?). Placebo = shuffled IV change. Pre-commit: as one of three option-implied signals, prioritize whichever single one best beats free realized signals per unit of options-data cost; treat the trio as a bundled information-cost decision, not three separate purchases.

#### kozak-nagel-santosh-2018-interpreting — Kozak, Nagel & Santosh (2018) · ~750 引用 · 「Interpreting Factor Models」
- **主張 / 與我方關聯**:只要不存在近似無套利機會，橫斷面平均報酬必由少數主成分(SDF)近似張成;行為與理性解釋在因子結構上觀測等價——重點是『少數共同成分』而非因子的來源故事。 → 為本專案的 PCA/SDF 取徑(TR-03)提供理論正當性，也解釋為何『廣度鎖死』:免費資料的橫斷面被少數大主成分主宰(TR-03 PC1=41.8%)。深化 KNS 2020 的動機。
- **可測性(免費資料)**:partial — 命題可用本專案特徵組合的 PCA 譜檢驗(幾個主成分解釋 SDF);小宇宙可做但廣度受限。yes-描述性;成本≈$0。
- **TR 切入(含 Nagel 對照)**:TR-03b 延伸:畫 characteristic-managed portfolios 的主成分譜，檢驗『少數 PC 是否張成本宇宙 SDF』，並連結 KNS 2020 收縮。屬理論/診斷(非策略)，用以解釋廣度天花板;若要交易化則須打敗樸素因子加總與靜態曝險。

#### avramov-chordia-goyal2006-liquidity-reversals — Avramov, Chordia & Goyal (2006) · ~700 引用 · 「Liquidity and Autocorrelations in Individual Stock Returns」
- **主張 / 與我方關聯**:Weekly return reversals are concentrated in high-turnover and illiquid stocks; the negative short-horizon autocorrelation is a manifestation of liquidity provision / inventory effects, not fundamental information — reversal profits are compensation to liquidity suppliers. → Complements Nagel (2012): together they pin short-term reversal as a liquidity-provision premium living in illiquid, high-turnover names — which tells us exactly why reversal is uncapturable in our liquid mega-cap seat. A clean, purely OHLCV conditioning test that reframes reversal as habitat-specific.
- **可測性(免費資料)**:yes. Weekly returns + turnover + Amihud illiquidity from OHLCV/EDGAR; double-sort reversal by illiquidity/turnover; PIT clean; cost ~$0. Caveat: turnover-heavy at weekly horizon — net-of-cost survival is the binding question, and the effect is strongest exactly where we do not trade (illiquid names).
- **TR 切入(含 Nagel 對照)**:Condition the weekly reversal strategy on Amihud/turnover terciles; test whether reversal profit rises monotonically with illiquidity. Nagel gauntlet: (1) static exposure — is the illiquid-reversal leg just a size/illiquidity level tilt? Neutralize; (2) 1/σ² Moreira-Muir control (reversal profits spike with vol, per Nagel 2012), require residual alpha t≥2; (3) random-entry null. Pre-commit: in a liquid universe the illiquid tercile is nearly empty ⇒ PARTIAL/FAILED, confirming the 'reversal = liquidity provision in illiquid habitat' seat argument.

#### elliott_gargano_timmermann_2013_complete_subset — Elliott, Gargano & Timmermann (2013) · ~600 引用 · 「Complete Subset Regressions」
- **主張 / 與我方關聯**:把所有含 k 個預測子的迴歸全數估計後取簡單平均(complete subset regression),能在多預測子環境下有效降低估計變異、改善股權溢酬的 OOS 預測,勝過單一大迴歸、forward selection 與若干收縮法。 → 是『組合預測』sub-area 中與已在名單的 Rapach-Strauss-Zhou 2010(等權組合)不同的一支方法論;提供一個介於單迴歸與 KMZ 高維複雜度之間的中間路線,且完全用免費預測子。
- **可測性(免費資料)**:yes — 只需指數報酬 + Goyal 免費預測子集;子集迴歸平均易實作。PIT 佳。成本 $0(組合數隨 k 增長,算力可控)。
- **TR 切入(含 Nagel 對照)**:TR:對 Goyal 14 預測子跑 complete subset regression(掃 k=1..5),對照 (a) 全變數大迴歸、(b) RSZ 等權組合、(c) 歷史均值(Campbell-Thompson);轉成擇時後須先打敗 buy-and-hold、1/σ² 與隨機進場。焦點:子集平均的 OOS R² 是否在我們樣本勝其他組合法,或全部組合法一起衰退為零(佐證廣度/IC 天花板而非方法問題)。

#### haddad-kozak-santosh-2020-factor-timing — Haddad, Kozak & Santosh (2020) · ~550 引用 · 「Factor Timing」
- **主張 / 與我方關聯**:主成分因子的可預測性集中在『最高變異的少數 PC』——用其估值 spread 擇時，最優 factor-timing 組合的收益遠大於靜態因子暴露，且擇時貢獻主要來自前幾個 PC。 → 『factor timing』子領域的現代 SDF 版正典;直接檢驗本專案反覆失敗的擇時腿(TR-02 gate FAILED、Markov gate)是否因『在錯的維度擇時』——HKS 說該在 PC 估值 spread 上擇時而非市場層。
- **可測性(免費資料)**:partial — 需先建 characteristic-managed PC 並算各 PC 的 book-to-price(EDGAR+價量可得);小宇宙 PC 估計不穩。方法 yes;穩健棲地 partial;PIT 可行;成本≈$0(算力)。
- **TR 切入(含 Nagel 對照)**:TR 建本宇宙特徵 PC，用各 PC 的估值 spread 做 factor timing，直接對照 Nagel 1/σ² 波動管理與靜態 PC 曝險:估值 spread 擇時是否勝純波動 scaling 與恆定曝險。必須同時打敗隨機進場;連結本專案擇時全敗的座位診斷。

### C.4 排程(接 docs/21 Paper-to-TR 管線)

- **第一波(60 篇)**:免費資料可重建,直接進 [docs/21](21-paper-to-tr-pipeline.md) 的 TR 執行階段。每篇 F0 預先承諾 + builder/auditor 雙軌 + 強制 Nagel 三重對照。建議每輪挑 2-3 篇,先做引用最高且洞見最新的。
- **第二波(76 篇)**:先補資料工程(產業分類表、指數長歷史、論文公開附錄),再進 TR。
- **第三波(24 篇)**:掛在 [docs/19](19-mechanism-taxonomy.md) 的翻案條件下,標明『資訊成本=哪筆資料』;待日內/選擇權/國際資料 ingest 後啟動(對應 docs/00 §E7 的資料維度路線)。
- **與 Part B 的回饋迴圈**:任何一波做完,若判定與某篇 Part B 台帳論文的座位重疊,依 F10 級聯回頭更新該論文的 angle_risk 與優先度。

---
*生成:2026-07-08(v2:表格加年份/作者欄、選書門檻由 >2000 放寬到 >500)。台帳 52 篇 + 前瞻 177 篇(其中 >2000 帶 64 篇 + 500-2000 帶擴充)。由 workflow 結構化輸出彙整,引用數為估計,深讀時以原文與 Google Scholar 覆核。*