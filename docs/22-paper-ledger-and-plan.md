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
1. **引用 >2000**(canonical,經同儕大量驗證,值得投入);
2. **與股票交易/選股邏輯相關**(不只是純理論);
3. **可用我們的免費資料重建**(日線 OHLCV + EDGAR 基本面 + 指數長歷史);需日內/選擇權/tick 的標 T2(排程但等資料維度);
4. **尚未在正確座位深測**(已參照且已在正確棲地測過的→不重排)。
排波原則:**第一波 = 高引用 × 免費資料可重建 × 高洞見潛力**;需付資訊成本(新資料)的順延為後波,但先寫下「翻案條件=哪筆資料」。

---

## Part B — 已參照論文台帳(52 篇)

六大主題、52 篇論文,每篇含分類、summary/結論、我們的洞見與用途、結果,以及重測中繼資料(angle_risk / reopen / 優先度)。
先給**重測優先度索引**(依優先度排序,快速看『先重測誰』),再按主題列完整記錄。

### B.0 重測優先度索引

| 優先度 | 論文 | 我們的結果 | 重測觸發(reopen 濃縮) |
|---|---|---|---|
| 🔴 高 | Hurst-Ooi-Pedersen 2017 | PARTIAL/mixed (理論背書採納;我們測的動量座位=衰退/FAILED;T | 取得多資產期貨資料(股指/債/商品/FX 期貨,數十個低相關市場)→建構 HOP 原生的 vol-target TSMOM 組合書,檢驗 crisis-alpha smile。這是… |
| 🔴 高 | Lou-Polk-Skouras 2019 (Overnight/Intraday) | queued | 用已有 OHLC 的 open/close 近似 (收→開 = prev-close→open、開→收 = open→close),對 47/503 檔動量 top-K book … |
| 🟡 中 | Bailey-Borwein-Lopez de Prado (PBO/CSCV) | adopted-as-convention(已用於 Minervini);旗艦 co | 對旗艦 combo 家族(8 配置)跑 CSCV-PBO 並在 F5 加門檻註記 → 資訊成本≈$0(既有回測,小算力)。 |
| 🟡 中 | Bollerslev 1986 | not-yet-tested (建議採納方向但從未實作、從未跑;現行以 traili | 當波動預測品質成為 binding(vol-target sizing 或 Kelly 部位在 regime 轉折被打臉,或要正式比較 forecast-σ vs realized… |
| 🟡 中 | Brown-Goetzmann-Ibbotson-Ross 1992 | adopted-as-convention(倖存者紀律已採納;經 TR-13 部分處 | ingest 點對點指數成分史(Wikipedia 版本史=免費但髒 / iShares-SPDR 歷史持股 / CRSP=付費學術)+ 下市報酬 → 資訊成本:從免費髒資料到付費… |
| 🟡 中 | Campbell-Thompson 2005 | adopted-as-convention(擇時層約束)——但 C-T 的符號約束溢 | ingest Goyal-Welch 總經預測子資料集(與 TR-17/KMZ 翻案條件共享的資訊成本)→ 在其原生單資產擇時座位跑符號約束股權溢酬迴歸。 |
| 🟡 中 | Fama-French 1992 | 混合:value 因子 FAILED(docs/09/10 失落十年、價值死);橫斷 | 取得中小型股 + 國際 PIT 宇宙(資訊成本:全市場/國際下市-aware 資料),或延長歷史回 1990s 涵蓋價值友善年代 → 在價值原生棲地重測 BE/ME 溢酬。 |
| 🟡 中 | GISW (Sharpe manipulation) | not-yet-tested(全專案未引用;為候選採納項) | 當任一策略具選擇權式/負偏態 payoff(現有 L≥1.5 槓桿 combo、防禦 overlay,或未來 covered-call/short-vol sleeve)→ 加算 … |
| 🟡 中 | Gatev-Goetzmann-Rouwenhorst 2006 | FAILED (OOS +1.96%/yr < 現金 BIL +2.70%;對現金超 | (a) 便宜且該先做:用 GGR 原生 distance 選對(而非共整合)+更廣宇宙(跨 ETF/ADR/全市場)以現有日線重測——資訊成本=工程;(b) 真正救活需日內資料(O… |
| 🟡 中 | Gu-Kelly-Xiu 2020 | FAILED(TR-08/11)——但 docs/19 標錯置風險=高:FAILED | 610 檔倖存者-aware 宇宙 + 基本面/另類資料特徵(資訊成本=ingest 94 式豐富特徵面板 × 數千檔)。注:部分已做——docs/10 廣宇宙因子≈死,此證據『支… |
| 🟡 中 | KMZ 2024 (Virtue of Complexity) | PARTIAL | Ingest 公開的 Goyal-Welch 月度總經預測子資料集 (1926-present),在 95 年長樣本 × 15 個總經序列的原生棲地上完整復現並重跑 TR-17 腳… |
| 🟡 中 | Kelly 1956 | adopted/implemented(half-Kelly 已實作)並作為『回撤預 | 任何 sleeve 產出穩健 OOS edge (p,b) 時,Kelly-by-probability 座位重開——但那 gated on 先突破 alpha 牆(付資訊成本:日… |
| 🟡 中 | Lopez de Prado HRP | PARTIAL(TR-07:機制如設計降波動 −3.9pp,permuted-HRP | 取得 50+ 檔真異質多資產宇宙(跨股/債/商品/國際/另類)即重測 HRP 於其原生棲地。資訊成本=多資產 PIT 資料 ingest(收斂回 docs/11『資料維度是綁定約束… |
| 🟡 中 | Moreira-Muir 2017 (Volatility-Managed Portfolios) | PARTIAL | 把 1/σ² 波動管理升級為 F6 v2 正式 sleeve 時,需加:(a) 交易成本 (換手高);(b) Cederburg 靜態恆定曝險二階控制;(c) 高波動宇宙反傷檢查。… |
| 🟡 中 | Nagel 2025 / Buncic 2025 (VoC critique) | PARTIAL | 同 KMZ 條:取得 Goyal-Welch 長歷史總經資料集後,在原生棲地上重跑,才能檢驗 Nagel 批評是否在 KMZ 自己的座位也成立 (而非只在我們的座位)。資訊成本=G… |
| 🟡 中 | Sharpe 1964 (CAPM) | PARTIAL(TR-06)——作為定價模型在本宇宙被拒(SML 反轉),作為風險中 | 廣/全市場 PIT 宇宙(610 檔倖存者-aware + 含非科技產業 + 跨多年代/regime)重測 SML 斜率——資訊成本=擴宇宙+更長歷史。 |
| 🟡 中 | Shumway 1997 (delisting) | PASSED(方法;TR-13 區間化完成) | ingest CRSP 型下市代碼面板(WRDS 學術付費)→ 把 [+1.26%,+2.02%] 區間收成點估計;資訊成本=付費 CRSP/WRDS。 |
| 🟡 中低 | Lakonishok-Lee (Insider) | FAILED | 擴充 insider 宇宙到小型股 PIT (Form 4 電子申報始於 ~2003,無法回補更早年代,唯一可及擴充=小型股廣度 + cluster-buy/高階主管加權等更細訊號… |
| 🟡 中低 | Ledoit-Wolf 2004 | adopted-as-convention(全域強制);間接於 TR-03/TR-0 | 執行 TR-03b:47/610 宇宙特徵值譜 vs MP 帶(幾個真訊號特徵值?),把 MP-clipping 加入 TR-03 競技場(vs LW vs PCA vs samp… |
| 🟡 中低 | Marcenko-Pastur 1967 | adopted-as-convention (經 LW shrinkage + TR | TR-03b:畫 47/610 宇宙樣本共變異特徵值譜 vs MP 帶(幾個真訊號特徵值?預期 3-5),把 MP-clipping 加入 TR-03 競技場(vs LW vs P… |
| ⚪ 低 | Almgren-Chriss 2000 | adopted-as-convention（設計採納為容量檢查；因規模不符誠實跳過、 | 資本規模達機構級或交易流動性差宇宙，使參與率>0、市場衝擊變一階；具體觸發=某部位使 AC 交易半衰期 τ=1/κ > 再平衡視窗（docs/19：F2 v2 容量曲線引用 cos… |
| ⚪ 低 | Arnott-Harvey-Markowitz 2019 (AHM) | adopted-as-convention(F0 檢查表即其操作化) | n/a — meta 協定不需重測;若協定更新版發布可增修 F0 → 資訊成本≈$0。 |
| ⚪ 低 | Bailey-Lopez de Prado 2014 (DSR) | adopted-as-convention(scorecard 核心工具) | 若返回分布嚴重非常態、需更新 PSR 的 skew/kurt 動差估計,或 N 定義有爭議 → 資訊成本≈$0(既有 trial-registry)。 |
| ⚪ 低 | Bertsimas-Lo 1998 | adopted-as-convention（TWAP 基線 + IS 會計原則；TR | ① 當 execution/ 真正動工、需要 implementation-shortfall 帳本（arrival price vs 實際成交）時。② 資本規模使單筆單>數% A… |
| ⚪ 低 | Brock-Lakonishok-LeBaron 1992 | adopted-as-convention (資料窺探防線採納為 fabric 慣例 | (a) 若要正式引用 BLB 量化結論→需 OCR 或取得可抽取文字版做 spot-verify;(b) 若要原座位復現→需長歷史單指數日線(DJIA 1897-)。兩者皆低優先:… |
| ⚪ 低 | Carhart 1997 | adopted-as-convention(作為 alpha 標尺/歸因基準)。注: | 若懷疑我方 UMD 建構偏離 Carhart 定義、或需國際動量因子;或若某配方數字變 load-bearing → OCR 原始 PDF。實務上隨宇宙擴充重建 UMD。 |
| ⚪ 低 | Cederburg-ODoherty-Wang-Yan 2020 | adopted-as-convention(TR-02b/TR-17 的控制組;F6 | n/a — 控制工具已採納入 F6;無翻案概念。若未來要把 1/σ² 波動管理當策略而非控制,才需重評其穩健性 → 資訊成本≈$0。 |
| ⚪ 低 | Cover 1991 | not-yet-tested(刻意延後為 optional benchmark;未建 | 想要一個 μ/Σ-free 的穩健對照時(例如質疑 risk-parity 的估計依賴),花小成本實作 UP / online-Newton-step 當 benchmark。資訊… |
| ⚪ 低 | DeMiguel-Garlappi-Uppal 2009 | adopted-as-convention(強制 1/N benchmark)+ 於 | 宇宙擴到大 N 異質(50+ 跨資產)且有長歷史時,optimizer 才有機會勝 1/N。資訊成本=多資產 PIT 資料 ingest + 長歷史。 |
| ⚪ 低 | Engle 1982 | adopted-as-convention (波動叢聚⇒block bootstra | 若要正式報告我們宇宙的條件異質性強度、或把 heteroskedasticity-robust 標準誤自動化進 rigor→加 ARCH-LM 為 scorecard 診斷(現有日… |
| ⚪ 低 | Fama 1970 | adopted-as-convention(認識論框架;聯合假設紀律)——非可測策略 | 非直接可重測;每次採用新基準模型(如加 QMJ/q-factor 到歸因)聯合假設 caveat 就重現、alpha 判定可能位移。具體=基準變更時重跑全部歸因。 |
| ⚪ 低 | Fama-French 1993 | adopted-as-convention(作為風險調整/歸因基準,非被測策略) | 若換更廣/更長宇宙 → 需在該宇宙重建 SMB/HML;或若加入 QMJ/q-factor 基準,alpha 判定可能位移(資訊成本=擴宇宙 PIT 財報)。 |
| ⚪ 低 | Grinold (fundamental law / breadth) | adopted-as-convention(天花板/組織定律)+ 經驗確認:擴廣度  | 定律本身是數學不可測;但『廣度天花板』判定隨換資料維度而重開——ingest 數千低相關名(多資產/期貨/全球)或高 IC alt-data(每項皆 docs/11 的一筆資訊成本… |
| ⚪ 低 | Grossman-Stiglitz 1980 | adopted-as-convention（框架哲學/元理論；非可測策略，無 TR） | 非策略、無單一重開事件；它是為所有其他翻案條件『定價』的元條件。實務觸發=任何一次付出新的資訊成本（ingest 日內資料、選擇權鏈、另類資料、小型股 PIT 基本面）——每一筆都… |
| ⚪ 低 | Hansen 2005 | adopted-as-convention(F5 主要工具) | 若子期/資產顯示強 block 相依(ARCH/GARCH-M),需改用 block/wild-bootstrap 版 SPA 而非 iid 版 → 資訊成本≈$0(既有資料,計算… |
| ⚪ 低 | Harvey-Liu-Zhu 2016 | adopted-as-convention(alpha 門檻;旗艦以 t=3.38  | 收緊到 campaign 級 FWER(Bonferroni t≈3.66)或全面改用 BHY-FDR 1% → 資訊成本≈$0(既有 trial-registry 重算)。 |
| ⚪ 低 | Hoffstein (rebalance timing luck) | PASSED(方法;TR-12 揭露 timing luck,3 修正生效) | n/a — 已於原生棲地窮舉相位測完;若新增其他日曆錨定策略,F12 直接套用 → 資訊成本≈$0。 |
| ⚪ 低 | Jegadeesh-Titman 1993 | FAILED(TR-11,作為『選股增量』;動量=beta)——已在兩個座位(47  | 國際/小型股宇宙(需國際或中小型 PIT 資料);或 TR-19 隔夜/日內歸因拆解(診斷角度,非交易——成本牆仍立)。 |
| ⚪ 低 | Kyle 1985 | adopted-as-convention（成本模型設計；costs.py 已實作但 | ① 立即工程觸發：把 backtest/costs.py 的 size_dependent_cost 接線進回測（目前實作但未接線，v1.2 審查點名）。② 機制重開：資本規模放大… |
| ⚪ 低 | Lo 2002 | adopted-as-convention(已實作於 restate_rf_shar | n/a(已實作);若要擴充到完整 IID/GMM 的 Sharpe 推論或多期重疊校正 → 資訊成本≈$0。 |
| ⚪ 低 | Lo-MacKinlay 1988 | adopted-as-convention (作為特徵採納;從未作為策略跑 TR) | 當 VR 要從『描述性特徵』升格為『trend-vs-revert 交易 gate』時——升級為 Lo-MacKinlay 異質穩健 z*(q)、per-asset 計算、輸出符號… |
| ⚪ 低 | Markowitz 1952 | adopted-as-convention(基礎框架公理,未單獨跑 TR;covar | 公理層,不需『重測』。唯一會改變用法的事件:取得夠長且穩定的 μ 估計(DGU:25 資產需 ~3000 月)——現實不可及,故 E-V 的 max-return 版永遠讓位給只用… |
| ⚪ 低 | McLean-Pontiff 2013 | adopted-as-convention(衰退 haircut/先驗)+ 被我方自 | 僅當我方累積的發表後衰退量測系統性偏離~35% 時才修訂 haircut 量級;具體=對 200 個 OSAP 訊號做系統性發表後 walk-forward(需 ingest OS… |
| ⚪ 低 | Michaud 1989 | adopted-as-convention(建構約束;塑造『不建 naked MVO | 若取得穩健的 robust/resampled-MVO 實作 + 顯著更長的估計窗,可測『約束後 MVO 是否勝 risk-parity』——但 DGU 已預示於我們的資產數不太可… |
| ⚪ 低 | Novy-Marx (gross profitability) | PASSED / adopted(ICIR +0.30;docs/18 PASSED | 它 PASSED,故『翻案』=強化而非推翻:延長歷史(1990s)+更多真熊市確認 flight-to-quality 的 regime-universality;且任何 long… |
| ⚪ 低 | Obizhaeva-Wang 2013 | not-yet-tested / queued（韌性壓力旋鈕設計，資料閘控未建） | 取得日內 LOB / 訂單簿韌性資料（G-S 意義下的資訊成本；<$15/mo 下目前受阻）+ 交易規模達到 ≥ 簿深度。具體觸發=ingest 日內 LOB 資料後，把『回補半衰… |
| ⚪ 低 | Petersen 2009 (clustered SE) | adopted-as-convention(已實作 n_eff + 聚類 t) | n/a(已實作);若要從 by-time 聚類擴到雙向聚類(firm×time)或 Driscoll-Kraay → 資訊成本≈$0(既有資料重算)。 |
| ⚪ 低 | Rahimi-Recht 2007 (Random Fourier Features) | adopted-as-convention | 僅在 TR-17 重跑 (見 KMZ 條) 或懷疑 RFF 數值正確性時才回看;無獨立重測意義。 |
| ⚪ 低 | Ross 1976 (APT) | adopted-as-convention(架構授權)。注:image-only 掃 | 非可測策略;只有在我們加入超越 TR-03 PCA 的正式 APT 載荷迴歸/統計因子步驟時才『重開』。具體:在更大更異質宇宙擴展 TR-03 PCA。 |
| ⚪ 低 | Sullivan-Timmermann-White 1999 | adopted-as-convention(操作化為 trial-registry  | 新增任何未登記的大型規則家族(如新的通道/濾網族)時,重跑 SPA + 更新 trial-registry → 資訊成本≈$0(既有資料重算)。 |
| ⚪ 低 | White 2000 | adopted-as-convention(F5 地基;SPA 為實作首選,未單獨跑 | 若需要 max-statistic 的完整 bootstrap 分布做 SPA 的交叉檢核,或 SPA 對我們 GARCH/block 相依結構失準時 → 資訊成本≈$0(既有資料… |
| ⚪ 低 | de Prado AFML | adopted-as-convention | HRP:取得 50+ 檔多資產異質宇宙後重測 (docs/19 標 HRP 錯置中-高,優勢隨 N 與異質性增長)。meta-labeling lift:補 precision-a… |

### B.1 A. 資產定價與因子 (docs/03 附錄A)

#### Fama-French 1992 — asset pricing / cross-section (size, value, beta)
- **分類**:機制族=α 產生(價值/規模橫斷面特徵)+ 方法慣例(decile 排序 harness)。原生棲地:資產=美股全市場、頻率=月頻、廣度=廣橫斷面(數百~數千)、年代=1963-1990、用途=橫斷面定價檢定。docs/19『價值(Fama-French)』列:座位=503 檔、錯置風險=低-中(價值溢酬本源於小型股)。
- **Summary / 結論**:size(ME)與 book-to-market(BE/ME)吸收橫斷面平均報酬;控制 size 後市場 β 與報酬『無關』(SML 平坦)。用 NYSE breakpoints、decile 排序——正是我們 quantile-spread 設計的原型。 結論:β 單獨不是報酬預測子;size+value 才是。全交易所 breakpoints 會讓組合在 NASDAQ 進入後全變小型股 → 必須用 NYSE breakpoints。
- **我們的洞見**:兩件事:(1)不要讓 CAPM β 以『alpha』洩入 factors/,β 只作風險中和/風險調整分母;(2)橫斷面特徵 decile 排序 + NYSE breakpoints 採為 rank-IC/ICIR harness 慣例。價值因子在我們 2015-24 座位=失落十年(FAILED)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1 VALIDATES + 附錄A;docs/09/10(value FAIL);docs/00 §E2;factors/validation.py;O3 SMB/HML 建構配方 — 橫斷面 rank-IC / quantile-spread harness 的設計原型(factors/validation.py);驅動 O3 建 SMB/HML(EDGAR book equity 依賴)。價值(earnings yield / B-M)當因子實測。 → **混合:value 因子 FAILED(docs/09/10 失落十年、價值死);橫斷面 decile+NYSE breakpoint harness = adopted-as-convention**
- **angle_risk(座位是否切錯)**:中(對 value 這條腿):我們在 S&P500 大型股 × 2015-24(公認的價值失落十年)測價值,而價值溢酬的原生棲地是小型股 × 含價值友善年代的長歷史。β-平坦結論則低風險(與我們一致、只當風險中和用)。
- **reopen(重測觸發=資訊成本)**:取得中小型股 + 國際 PIT 宇宙(資訊成本:全市場/國際下市-aware 資料),或延長歷史回 1990s 涵蓋價值友善年代 → 在價值原生棲地重測 BE/ME 溢酬。
- **重測優先度**:🟡 中 — medium — 價值的原生棲地(小型股+長歷史)尚未在我們資料測到;但失落十年是全行業共識,急迫度不高。β-中和用法與 harness 慣例=不需重測。

#### Fama-French 1993 — asset pricing / 因子模型與歸因基準
- **分類**:機制族=估計工程·描述歸因(風險調整基準,非賺錢策略)。原生棲地:資產=美股(+債)、頻率=月頻、廣度=廣橫斷面、年代=1963-1991、用途=共同風險因子/把 alpha 壓到 0 的基準。屬 docs/19 §4『歸因/估計工程』家族。
- **Summary / 結論**:3 因子(Mkt/SMB/HML)+2 債券因子;模仿組合捕捉 size/value 的共同變異、把截距(alpha)驅近 0。給出 2×3 size×BE/ME 排序、價值加權、每年 6 月再平衡、BE 取 t-1 的精確配方。 結論:判斷 edge 的正確標尺是『alpha net of Mkt/SMB/HML』而非原始/超額 Sharpe——因為動量/趨勢策略重載於這些因子。
- **我們的洞見**:把 raw Sharpe 換成因子調整後 alpha 當作驗收門檻;FF3→Carhart-4 迴歸步驟寫進 backtest/歸因層,每個策略都報 alpha 而非只報 Sharpe。配方直接移植。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O3 + 附錄A;TR-15(旗艦 Carhart alpha t=3.38 的建構基礎);factors/;backtest/ 歸因 — 建 SMB/HML(2×3 排序、VW、6 月再平衡、BE t-1);FF3(→+動量)迴歸步驟成為所有策略的歸因引擎。TR-15 順手修復 FF loader 上游格式 break。 → **adopted-as-convention(作為風險調整/歸因基準,非被測策略)**
- **angle_risk(座位是否切錯)**:低 — 完全按原意當歸因基準使用,座位正確。唯一 caveat=Fama-1970 聯合假設問題:alpha 判定只與此基準模型一樣好。
- **reopen(重測觸發=資訊成本)**:若換更廣/更長宇宙 → 需在該宇宙重建 SMB/HML;或若加入 QMJ/q-factor 基準,alpha 判定可能位移(資訊成本=擴宇宙 PIT 財報)。
- **重測優先度**:⚪ 低 — low — 基礎設施/慣例,座位正確;隨宇宙變更才需重建,不需推翻。

#### Jegadeesh-Titman 1993 — asset pricing / cross-sectional momentum
- **分類**:機制族=α 產生(XS 動量)。原生棲地:資產=美股全市場、頻率=月頻、廣度=廣橫斷面(數百~數千)、年代=1965-1989、用途=相對強弱選股。docs/19『XS 動量(Jegadeesh-Titman)』:座位=47 檔同產業(高相關)+503 檔 S&P500,錯置風險=低(兩棲地皆測)。
- **Summary / 結論**:3-12 月相對強弱動量 ~1%/月;12 月形成/3 月持有最佳 1.31%/月(加 1 週 skip 1.49%),非系統風險可解釋,約半在後 24 個月反轉。背書我們的 1-bar lag(=skip-week 微結構衛生)與 RS 特徵。 結論:動量是真效應(JT+Rouwenhorst+AMP 背書),但其 IR 天花板被廣度鎖死~1;需 skip-period 與持有期上限(24 月反轉)。
- **我們的洞見**:動量真、但在我們座位=beta 不是選股 alpha:廣市場 ICIR≈0、47 檔 top-K P(beat EW)=23%(TR-11 F9 降級 FAILED)。1-bar lag=誠實最小 skip(HOP 證延遲會侵蝕報酬,別加更多)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1+附錄A;docs/06(因子搜尋湧現最佳=純多頭 6-1 動量);docs/09;TR-11;TR-12;docs/19 — 背書 minervini_trend、RS/動量特徵、1-bar lag、reversal guardrail;XS 動量當策略實測;TR-12 相位平均證單相位不可信(季動量 timing-luck 1,753bps/yr)。 → **FAILED(TR-11,作為『選股增量』;動量=beta)——已在兩個座位(47 高相關 + 503 廣市場)皆測皆死**
- **angle_risk(座位是否切錯)**:低(docs/19 明列雙棲地皆測)。殘餘角度風險=(a)原生棲地也含國際/小型股,未測;(b)LPS(2019)診斷角度:動量溢酬可能全住在隔夜——我們從未做隔夜/日內拆解(TR-19 佇列)。
- **reopen(重測觸發=資訊成本)**:國際/小型股宇宙(需國際或中小型 PIT 資料);或 TR-19 隔夜/日內歸因拆解(診斷角度,非交易——成本牆仍立)。
- **重測優先度**:⚪ 低 — low — 已在正確廣棲地測過且輸(ICIR≈0),效應真但 IR 被廣度鎖死。唯一 medium 的子項是 LPS 隔夜診斷(TR-19),屬歸因非翻案。

#### Carhart 1997 — asset pricing / 4 因子模型 · 基金績效歸因
- **分類**:機制族=估計工程·描述歸因(動量因子基準)。原生棲地:資產=美國共同基金/股票、頻率=月頻、廣度=廣橫斷面、年代=1962-1993、用途=把績效持續性歸因到 UMD+費用。屬 docs/19 §4 歸因家族。
- **Summary / 結論**:在 FF3 上加動量因子(UMD/WML)=4 因子;基金『持續性』大多是動量因子+費用,不是技能。(image-only 掃描,由既有知識覆蓋並已標注) 結論:趨勢/動量系統的 edge 若只是 UMD 載荷,就不是技能——必須報 alpha net of Carhart-4。這是趨勢系統最重要的單一基準。
- **我們的洞見**:動量該對『被定價的動量因子』基準化,不能當免費 alpha。UMD 加入 factors/ 迴歸面板,minervini_trend/旗艦 alpha 一律報 Carhart-4 淨值。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O3+附錄A;TR-15(旗艦 t=3.38≥HLZ 3.0 判 PASSED);factors/ 歸因面板 — UMD 當第 4 因子;TR-15 旗艦的 Carhart alpha t-stat 就是 HLZ(t≥3.0)門檻的度量;所有策略歸因。 → **adopted-as-convention(作為 alpha 標尺/歸因基準)。注:原文 image-only 掃描,配方細節依既有知識**
- **angle_risk(座位是否切錯)**:低 — 當歸因基準按原意使用。唯一 caveat=image-only 掃描,若某數值細節成為 load-bearing,需 OCR 原文核對。
- **reopen(重測觸發=資訊成本)**:若懷疑我方 UMD 建構偏離 Carhart 定義、或需國際動量因子;或若某配方數字變 load-bearing → OCR 原始 PDF。實務上隨宇宙擴充重建 UMD。
- **重測優先度**:⚪ 低 — low — 慣例/基準,座位正確,按設計運作。

#### Sharpe 1964 (CAPM) — asset pricing / 均衡定價(單因子 β)
- **分類**:機制族=估計工程·描述歸因(市場因子/風險中和)。原生棲地:資產=全市場、頻率=不限、廣度=全市場、年代=1960s、用途=均衡下期望報酬線性於 β(SML)。docs/19『CAPM』:座位=47 檔科技(極窄棲地),錯置風險=中。
- **Summary / 結論**:均衡下期望報酬只線性於市場 β(SML),β 是唯一被定價的風險。TR-06 在我們宇宙實測 CAPM。 結論:FF1992 實證殺死 β-報酬關係 → 不可加 raw β 當 alpha 因子;β 只作風險中和與風險調整分母。
- **我們的洞見**:β 純作風險中和(portfolio 的 beta-neutral/beta-target)。TR-06 發現本宇宙 SML『反轉陡升』(FM 斜率 +1.9%/mo t=2.69,高 beta 大勝=BAB 在 AI 牛市反向)、截距 −1.02%/mo 違反 CAPM;歸因工具價值保留。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;TR-06(PARTIAL);docs/19 CAPM 列;portfolio/ beta 中和 — 市場因子概念 + regime-gate 到市場狀態(200-SMA/HMM 粗版);β 風險中和;TR-06 Fama-MacBeth SML 檢定。 → **PARTIAL(TR-06)——作為定價模型在本宇宙被拒(SML 反轉),作為風險中和/歸因工具保留**
- **angle_risk(座位是否切錯)**:中-高 — docs/19 明列座位極窄(47 檔科技)。SML 反轉是『此棲地』現象(AI 牛市高 beta 補償),非對 CAPM 的普遍反駁;我們從一個極窄科技座位切入。原生棲地=全市場定價。
- **reopen(重測觸發=資訊成本)**:廣/全市場 PIT 宇宙(610 檔倖存者-aware + 含非科技產業 + 跨多年代/regime)重測 SML 斜率——資訊成本=擴宇宙+更長歷史。
- **重測優先度**:🟡 中 — medium — PARTIAL 判定明顯棲地特定(窄科技座位),SML 反轉大概不普遍化;但 CAPM 定價非我方 alpha 目標,故非 high。切入角度窄=值得標記。

#### Ross 1976 (APT) — asset pricing / 多因子無套利定價
- **分類**:機制族=估計工程·描述歸因(多因子架構授權)。原生棲地:資產=不限、頻率=不限、廣度=廣橫斷面(共同因子結構)、年代=1976、用途=報酬由少數共同因子驅動、無套利釘價、對『哪些因子』不可知論。屬 docs/19 §4 因子/歸因家族。
- **Summary / 結論**:報酬由一組共同因子驅動,期望報酬線性於因子載荷,無套利釘住價格——多因子、對因子身分理論中立。(image-only 掃描,由既有知識覆蓋並已標注) 結論:APT 是『不需 CAPM 推導即可用經驗動機因子(動量/價值/品質)』的執照——授權整個多因子 factors/ 方向與 IC/quantile-spread 機制。
- **我們的洞見**:把 factors/ 結構化為 APT 式多因子面板 + 明確因子載荷迴歸(Mkt/SMB/HML/UMD/QMJ),使任何策略報酬可做因子風險分解。TR-03 的 PCA 統計因子是其經驗對應。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;TR-03(PCA);factors/ 架構;歸因分解 — factors/ 架構授權;IC/quantile-spread 機制的理論正當性;TR-03(PCA 統計因子=APT 風味的經驗版,PC1=41.8% 一個大 beta)。 → **adopted-as-convention(架構授權)。注:image-only 掃描,由既有知識覆蓋;TR-03 PCA 是其經驗近親**
- **angle_risk(座位是否切錯)**:低 — 當架構授權使用,正確。APT 不指定『哪些因子』→ 沒有具體座位可切錯,它是 meta-執照。caveat=image-only 掃描。
- **reopen(重測觸發=資訊成本)**:非可測策略;只有在我們加入超越 TR-03 PCA 的正式 APT 載荷迴歸/統計因子步驟時才『重開』。具體:在更大更異質宇宙擴展 TR-03 PCA。
- **重測優先度**:⚪ 低 — low — 基礎架構慣例,無獨立可重測的策略面。

#### Gu-Kelly-Xiu 2020 — asset pricing / ML 橫斷面預測
- **分類**:機制族=α 產生(ML 橫斷面預測)。原生棲地:資產=全美股 ~3 萬檔、頻率=月頻、廣度=巨量橫斷面 × 60 年 × 94 特徵、年代=1957-2016、用途=非線性 ML 選股。docs/19『ML 預測(GKX 2020)』:座位=47 檔×8 年×11 特徵(≈原生棲地 0.1%),錯置風險=高。
- **Summary / 結論**:樹/神經網路約『雙倍』線性模型的 L/S Sharpe(NN VW decile Sharpe 1.35 vs OLS 0.61);900+ 預測子的裸 OLS OOS 轉負;跨方法 top 預測子=價格趨勢、流動性、波動。 結論:ML 勝線性『但那是在豐富特徵上』(docs/12);用弱特徵(純價量)再炫的方法也變不出 alpha;股票級 R²~0.3% → 須在組合層評估。
- **我們的洞見**:背書 LightGBM(淺樹>深網)、我方特徵屬其 top-3 類、須正則化+組合層評估。但在我方座位:TR-08 OOS IC −0.0013、R² −4.8%、Sharpe≈shuffled 控制——GKX 效應在此宇宙完全衰退。
- **用在哪 · 怎麼用 · 結果**:docs/03 §1+附錄A;TR-08(FAILED);TR-11(RF 預測器 FAILED);docs/12;docs/19 ML 列 — 驗證 LightGBM 選型與特徵面板;ML 混合預測實測 TR-08(LightGBM)、TR-11(RF 預測器)。 → **FAILED(TR-08/11)——但 docs/19 標錯置風險=高:FAILED 只證『小而相關宇宙+價量特徵』無效,與 GKX 主張不衝突**
- **angle_risk(座位是否切錯)**:高 — 這是使用者點名的旗艦『切錯座位』案例(如 KMZ)。我方座位=其原生棲地 ~0.1%(47 檔 vs 3 萬檔、11 特徵 vs 94)。FAILED 不觸及 GKX 的座位。
- **reopen(重測觸發=資訊成本)**:610 檔倖存者-aware 宇宙 + 基本面/另類資料特徵(資訊成本=ingest 94 式豐富特徵面板 × 數千檔)。注:部分已做——docs/10 廣宇宙因子≈死,此證據『支持不翻案』。
- **重測優先度**:🟡 中 — medium — 角度明顯錯(高錯置),但已有緩解證據(docs/10 廣宇宙因子近死)傾向不翻案;僅在同時 ingest 豐富特徵+廣宇宙時才值得正確規模重測,故非 high。

#### McLean-Pontiff 2013 — asset pricing / 異常衰退元研究
- **分類**:機制族=驗證方法·描述(異常衰退元發現/先驗)。原生棲地:資產=82 個已發表異常、頻率=月頻、廣度=跨異常元研究、年代=1970s-2010s、用途=量化樣本外+發表後衰退。用作 rigor scorecard 的 haircut 先驗——座位正確。
- **Summary / 結論**:82 個已發表異常:樣本外衰退~10%(統計偏誤、不顯著)、發表後衰退~35%(套利)。衰退對高特異波動/流動性差/小型股最小。 結論:已發表異常回測高估活體 alpha ~35-50% → 須 haircut;並偏好較少被套利的角落 + 發表後起算的 walk-forward 窗。
- **我們的洞見**:把~35% 衰退 haircut 與『發表後起算窗』寫進 rigor scorecard;作為 OSAP 212/200 個未測訊號的先驗(docs/15:發表後平均衰退 58%)。我方自身結果反覆佐證(TR-01 pairs GGR +11%衰退>100%、TR-16 IBS Connors 時代衰退、動量 ICIR≈0)。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O4+附錄A;docs/15(OSAP 先驗);rigor scorecard;TR-01/TR-16(自身衰退佐證) — rigor scorecard 的衰退 haircut 線(O4);OSAP 未測訊號的先驗;偏好 illiquid/小型/高特異波動角落。 → **adopted-as-convention(衰退 haircut/先驗)+ 被我方自身衰退發現反覆佐證**
- **angle_risk(座位是否切錯)**:低 — 當 meta-先驗/haircut 按設計使用,未切錯座位;我方自身衰退觀察(pairs、IBS、動量)正好佐證其量級。
- **reopen(重測觸發=資訊成本)**:僅當我方累積的發表後衰退量測系統性偏離~35% 時才修訂 haircut 量級;具體=對 200 個 OSAP 訊號做系統性發表後 walk-forward(需 ingest OSAP 資料+PIT)。
- **重測優先度**:⚪ 低 — low — 慣例、已被佐證、座位正確。

#### Campbell-Thompson 2005 — asset pricing / 股權溢酬 OOS 擇時預測
- **分類**:機制族=估計工程·風險塑形(擇時層約束)。原生棲地:資產=單一大盤(股權溢酬)、頻率=月頻、廣度=單資產時序、年代=1927-2005、用途=用 Goyal-Welch 型預測子做市場擇時、加符號限制。座位=擇時,類 KMZ 的單資產月頻總經預測子棲地。
- **Summary / 結論**:股權溢酬預測子只有在加『係數符號限制 + 非負溢酬下限』後才 OOS 勝歷史均值;OOS R² 很小(<0.5%/月)但有經濟意義。 結論:無限制 OLS 時序預測子 OOS 幾乎必敗,除非加經濟符號約束——對 regime/擇時層是廉價高值的規則。
- **我們的洞見**:在任何擇時/regime overlay 上強制加符號限制+非負溢酬下限(O8)。我方擇時/gate 一律 FAILED(TR-02、docs/09 gate-to-cash)與 C-T 警告一致——但那是不同建構(Markov/200-SMA gate),非 C-T 的符號約束 OLS 溢酬預測子本身。
- **用在哪 · 怎麼用 · 結果**:docs/03 §O8+附錄A;TR-02(Markov gate);docs/19 Markov gate 列;擇時 overlay 慣例 — regime/擇時 overlay 的約束慣例(O8);與 TR-02(Markov gate FAILED)、200-SMA/HMM gate 的擇時失敗互相呼應。 → **adopted-as-convention(擇時層約束)——但 C-T 的符號約束溢酬預測子『從未在其原生單資產擇時座位跑過』**
- **angle_risk(座位是否切錯)**:中 — C-T 原生座位=市場級月頻股權溢酬擇時(Goyal-Welch 總經預測子 + 符號約束),與 KMZ 同棲地。我們只把它當慣例/約束採納,我方擇時 FAILED(TR-02)是不同建構(Markov/200-SMA gate)非 C-T 的約束 OLS 溢酬預測子。
- **reopen(重測觸發=資訊成本)**:ingest Goyal-Welch 總經預測子資料集(與 TR-17/KMZ 翻案條件共享的資訊成本)→ 在其原生單資產擇時座位跑符號約束股權溢酬迴歸。
- **重測優先度**:🟡 中 — medium — 採為規則卻從未在原生座位測;翻案與 TR-17(KMZ)共享 Goyal-Welch 資料成本,一旦該資料落地即為廉價 add-on。

#### Fama 1970 — market efficiency / 認識論(聯合假設)
- **分類**:機制族=驗證方法·描述(市場效率認識論)。原生棲地:資產=全市場、頻率=不限、廣度=全市場資訊效率、年代=1970、用途=弱/半強/強式分類 + 聯合假設問題。作為 rigor scorecard 與整個負結果專案的認識論框架——座位正確。
- **Summary / 結論**:弱/半強/強式效率分類;價格『充分反映』資訊,故任何可預測性檢定=效率+假設報酬模型的『聯合檢定』。 結論:聯合假設問題:我方 IC/alpha 結果只與基準模型一樣好——強化 FF3/Carhart-4 風險調整的必要。
- **我們的洞見**:整個負結果專案=EMH 的經驗面;結合 Grossman-Stiglitz(docs/20 §6):免費資料上 alpha≈0 正是 EMH/G-S 均衡預言。alpha 判定的謙遜(不能完全分離『無 alpha』與『錯基準』)寫進 scorecard 哲學。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄A;docs/00 §E;docs/20 §6(G-S 均衡);rigor scorecard 哲學 — rigor scorecard 的認識論框架;docs/00 §E 的判斷哲學;與 docs/20 Grossman-Stiglitz 段落連結。 → **adopted-as-convention(認識論框架;聯合假設紀律)——非可測策略,是我方全專案量測所對的 null**
- **angle_risk(座位是否切錯)**:低 — 當認識論框架使用,正確;無座位被切錯。唯一『風險』是哲學性的:永遠無法完全分離『無 alpha』與『錯基準』(這就是聯合假設問題本身=永久 caveat,非可修的座位)。
- **reopen(重測觸發=資訊成本)**:非直接可重測;每次採用新基準模型(如加 QMJ/q-factor 到歸因)聯合假設 caveat 就重現、alpha 判定可能位移。具體=基準變更時重跑全部歸因。
- **重測優先度**:⚪ 低 — low — 基礎認識論慣例,非策略。

#### Novy-Marx (gross profitability) — asset pricing / 基本面品質因子
- **分類**:機制族=α 產生(基本面品質)。原生棲地:資產=美股全市場、頻率=年頻財報、廣度=廣橫斷面、年代=1963-2010、用途=毛利/資產橫斷面選股。docs/19『品質 GP(Novy-Marx)』:座位=503 檔 PIT EDGAR ✓,錯置風險=低,『已在正確棲地確認』。
- **Summary / 結論**:gross profitability = 毛利/總資產,是穩健的品質因子。我方以 EDGAR PIT 對齊實作,是 alt-data pipeline 的示範因子,現已進旗艦當 +15% 品質 tilt。 結論:全 session 唯一穩健的新 alpha:廣有效率宇宙上 GP(基本面品質)勝價量動量——ICIR +0.30、跨期同號、regime-universal(bear/壓力最強=flight-to-quality)。
- **我們的洞見**:這是『對照組的正例』:在正確棲地測、而且贏了。GP L/S 單獨 Sharpe +0.45(modest 但真)。與集中動量低相關(+0.16)可加性。caveat:long-only sleeve 抬 alpha-t 是 beta 不是訊號(docs/00 §E9A,零訊號籃子一樣抬),須用 L/S 隔離。
- **用在哪 · 怎麼用 · 結果**:docs/10 §4b/4e;docs/00 §E2;docs/18 PASSED;docs/19 GP 列(低錯置);scripts/fundamental_factors.py、quality_research.py — gross_profitability=GrossProfit/Assets、PIT EDGAR;實測因子;旗艦 +15% 品質 tilt / 品質 sleeve;深掘 regime 適用地圖。 → **PASSED / adopted(ICIR +0.30;docs/18 PASSED)——已在正確廣橫斷面年頻財報棲地確認**
- **angle_risk(座位是否切錯)**:低 — docs/19 明列『已在正確棲地確認』(503 檔 PIT EDGAR、廣橫斷面、年頻財報)。這是反例:座位對、且贏。唯一 live 方法論再查=long-only 增量-α 須以 L/S 重驗(docs/00 §E9A)。
- **reopen(重測觸發=資訊成本)**:它 PASSED,故『翻案』=強化而非推翻:延長歷史(1990s)+更多真熊市確認 flight-to-quality 的 regime-universality;且任何 long-only 併入須以市場中性 L/S 重驗隔離訊號。
- **重測優先度**:⚪ 低 — low — 唯一在正確座位 PASSED 的因子;僅為強化(更長歷史/更多熊市/L-S 隔離複驗)而重測,非為推翻。

#### Grinold (fundamental law / breadth) — portfolio / 主動管理 IR 預算
- **分類**:機制族=驗證方法·描述(主動管理基本定律 IR=IC×√Breadth)。原生棲地:資產=不限、頻率=不限、廣度=IR 預算之核心變數、年代=1989、用途=把可達 IR 拆成 IC×獨立賭注數。作為我方全部負結果的組織性天花板——座位正確,且被 51→503 廣度實驗直接佐證。
- **Summary / 結論**:IR = IC × √Breadth。可達 Sharpe≈IR 被廣度與 IC 鎖死~1。是解釋我方全部負結果的物理上限。 結論:免費日線資料的 IC×廣度把可達 Sharpe 鎖在~1:0/56 配置達 Sharpe 2;三條件(≥5 策略 ∧ 低風險 ∧ 50-100%)數學互斥,根因是 Calmar≈f(Sharpe)、Sharpe 被廣度鎖死。突破只有換資料維度(廣度×16、或高 IC alt-data、或更高頻)。
- **我們的洞見**:演算法到頂;瓶頸是資料不是方法複雜度。唯一出路=換資料維度(docs/11 四條路)。並被 TR-14 深化:√breadth 假設獨立賭注,而我方 47 同產業高相關(zoo 59 變體有效試驗僅 1.8,ρ=0.54)→ 有效廣度≪名目。
- **用在哪 · 怎麼用 · 結果**:docs/06 §1;docs/11(四條路);docs/14 §75;docs/00 §E1;docs/08;TR-14(有效廣度 n_eff) — 因子搜尋前沿的物理上限(docs/06);換資料維度清單的組織原則(docs/11);解釋 Calmar 牆/Sharpe 天花板(docs/14、docs/00 §E1)。 → **adopted-as-convention(天花板/組織定律)+ 經驗確認:擴廣度 51→503 沒幫助(IC 隨 universe 變廣而降,docs/09)、0/56 配置達 Sharpe 2**
- **angle_risk(座位是否切錯)**:低 — 當正確組織定律使用,51→503 廣度實驗直接佐證。微妙點:√breadth 假設獨立賭注,我方高相關名使有效廣度≪名目(TR-14)——若有偏差是『低估廣度懲罰』而非切錯座位。
- **reopen(重測觸發=資訊成本)**:定律本身是數學不可測;但『廣度天花板』判定隨換資料維度而重開——ingest 數千低相關名(多資產/期貨/全球)或高 IC alt-data(每項皆 docs/11 的一筆資訊成本)。
- **重測優先度**:⚪ 低 — low — 已經驗確認的數學定律(擴廣度沒幫助);無可推翻,僅 docs/11 的資料維度變更會移動可達前沿。

### B.2 B. 資料窺探·過擬合·倖存者 (docs/03 附錄B)

#### White 2000 — 回測嚴謹性 / 資料窺探多重測試
- **分類**:功能=驗證方法;原生棲地=規格搜尋下的交易規則資料窺探檢定(資產無關×任意頻率×規則家族選擇×用途=挑出贏家後的族群層 p 值)。docs/19 §5 歸為 fabric 自身工具、原生座位=回測稽核。
- **Summary / 結論**:用平穩 bootstrap 對「規格搜尋出的最佳模型相對基準無優越預測力」的虛無做檢定,產出考慮到全部 L 個被搜尋模型(而非只有贏家)的漸近有效 p 值。Example 2.2 本身就是一個多空交易訊號 vs buy&hold。 結論:單一策略的樣本內 Sharpe 在做過參數掃描後系統性樂觀;正解是對整族參數化取 max-statistic 的族群層 p 值。
- **我們的洞見**:我們選鉤子時(minervini 的 8 門檻、RS/ATR 掃描)必須有族群層 p 值;但實作首選 Hansen SPA(見下),White RC 只當概念基礎與保守篩。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B(逐篇);F5 多重測試 v2;docs/19 §5;O1 backtest/spa.py 設計 — 作為 F5 多重測試門檻的理論地基;closed-form E[max] Sharpe 當保守篩,SPA 當主要檢定。 → **adopted-as-convention(F5 地基;SPA 為實作首選,未單獨跑純 White RC)**
- **angle_risk(座位是否切錯)**:低。原生棲地就是交易規則的規格搜尋,與我們的座位完全一致;唯一刻意偏離=改用 Hansen SPA 因 RC 的檢定力會被垃圾策略稀釋到零(已在 docs/03 附錄B 記錄)。
- **reopen(重測觸發=資訊成本)**:若需要 max-statistic 的完整 bootstrap 分布做 SPA 的交叉檢核,或 SPA 對我們 GARCH/block 相依結構失準時 → 資訊成本≈$0(既有資料,純算力)。無外部觸發需求。
- **重測優先度**:⚪ 低 — low — 正確棲地、且被 Hansen 依設計取代;是工具非策略,無翻案動機

#### Hansen 2005 — 回測嚴謹性 / 多重測試
- **分類**:功能=驗證方法;原生棲地=策略族群選擇的多重測試(資產無關×任意頻率×用途=回測稽核)。docs/19 §5 原生座位=回測稽核。
- **Summary / 結論**:White RC 的嚴格改良版:studentize 損失差、採 sample-dependent 虛無以降權「差且無關」的替代策略。只要往候選集塞垃圾策略,RC 的檢定力可被打到零;SPA 免疫此問題。 結論:SPA 是我們選擇閘門的最佳多重測試工具——用每個策略自身 bootstrap 標準差 studentize,給出一致的 p 值。
- **我們的洞見**:把整個 gridded 規則族丟進一個檢定時,壞策略不會稀釋 SPA;定為 F5 的主要工具而非 plain RC。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;F5 多重測試 v2(主要工具);docs/19 §5;O1 backtest/spa.py — F5 變體家族的主要多重測試工具(closed-form E[max] 僅作保守篩)。 → **adopted-as-convention(F5 主要工具)**
- **angle_risk(座位是否切錯)**:低。原生棲地=策略選擇多重測試,與我們用途一致;無錯置。
- **reopen(重測觸發=資訊成本)**:若子期/資產顯示強 block 相依(ARCH/GARCH-M),需改用 block/wild-bootstrap 版 SPA 而非 iid 版 → 資訊成本≈$0(既有資料,計算成本)。
- **重測優先度**:⚪ 低 — low — 在原生座位、如設計運作的核心工具

#### Sullivan-Timmermann-White 1999 — 回測嚴謹性 / 技術交易規則資料窺探
- **分類**:功能=驗證方法;原生棲地=股指、日頻、~100 年 DJIA、~7,846 條交易規則家族的窺探校正——這是本專案座位的最直接鏡像。
- **Summary / 結論**:把 White RC 套到 100 年 DJIA 上 ~7,846 條交易規則:最佳規則樣本內(1897–1986)撐過窺探校正,但樣本外(1987–1996)p≈0.12=無顯著經濟價值;S&P 期貨含實際成本後無一勝基準。 結論:從規則家族挑出的技術規則,樣本內漂亮但很可能是窺探驅動;必須以整個 grid 為宇宙報告被選 config 的 SPA 校正 p 值 + 硬性樣本外保留期。
- **我們的洞見**:把 Minervini/RS/ATR 全部變體視為宇宙;zoo 家族的有效變體數要計(TR-14 證 59 變體=1.8 個獨立賭注);設凍結的 post-2010 holdout 讓 optimizer 永不見。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B + 附錄E(BLB 警世案例);trial-registry(≈226);TR-14(zoo 59→1.8);F5 + 凍結 post-2010 holdout — 作為 zoo/變體家族窺探會計(trial-registry)與凍結 holdout 紀律的直接依據。 → **adopted-as-convention(操作化為 trial-registry + TR-14 有效變體計數 + 凍結 holdout)**
- **angle_risk(座位是否切錯)**:低-中。座位本身高度吻合(技術規則家族選擇);殘留風險=我們是否真的窮舉登記了完整試驗數 N——trial-registry 是我們的答案,但新增未登記家族會破功。
- **reopen(重測觸發=資訊成本)**:新增任何未登記的大型規則家族(如新的通道/濾網族)時,重跑 SPA + 更新 trial-registry → 資訊成本≈$0(既有資料重算)。
- **重測優先度**:⚪ 低 — low — 已操作化;只在未登記新家族時觸發

#### Bailey-Lopez de Prado 2014 (DSR) — 回測嚴謹性 / 過擬合校正
- **分類**:功能=驗證方法;原生棲地=回測稽核(試驗數 N × 非常態 × 軌跡長度校正;資產無關)。docs/19 §5 原生座位=回測稽核。
- **Summary / 結論**:DSR 依 (a) 試驗數、(b) 偏態/峰態(經 PSR)、(c) 軌跡長度校正觀測 Sharpe。明言 holdout/k-fold 不能防過擬合(「跑 20 次 holdout,偽陽性是預期內的」)。 結論:未控制搜尋規模的回測毫無價值;PurgedKFold 只擋洩漏、不擋選擇偏誤,必須在 CV 之上加 DSR 層,吃真實試驗數 N。
- **我們的洞見**:scorecard 的『Deflated Sharpe』點必須引用 trial-registry 的實際 N;時序宣稱另加 MinTRL(F4 時間維)。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;F4(MinTRL)/F5;docs/05(抓 Minervini);docs/19 §5;O1 backtest/deflated_sharpe.py — O1 backtest/deflated_sharpe.py(PSR+DSR)核心工具;F4 的 MinTRL 判準。 → **adopted-as-convention(scorecard 核心工具)**
- **angle_risk(座位是否切錯)**:低。原生棲地=回測稽核,與用途一致;無錯置。
- **reopen(重測觸發=資訊成本)**:若返回分布嚴重非常態、需更新 PSR 的 skew/kurt 動差估計,或 N 定義有爭議 → 資訊成本≈$0(既有 trial-registry)。
- **重測優先度**:⚪ 低 — low — 在原生座位的核心工具,如設計運作

#### Bailey-Borwein-Lopez de Prado (PBO/CSCV) — 回測嚴謹性 / 過擬合機率診斷
- **分類**:功能=驗證方法;原生棲地=回測稽核(組合對稱交叉驗證 CSCV 估 IS-best 在 OOS 低於中位的機率;自由度隨 N 升、隨 T 降)。
- **Summary / 結論**:CSCV 估計『樣本內最佳策略在樣本外低於中位』的機率。全過擬合虛無(N 策略真 Sharpe 皆 0)下 PBO≈1;它給出 DSR 給不了的『選擇程序本身是否脆弱』診斷。 結論:PBO 是選擇程序的脆弱度診斷;經驗法則 <30% 可信、>50% 雜訊;策略晉升應 gate 在 PBO<0.5。
- **我們的洞見**:用 CSCV 抓過我們自己的 Minervini(docs/05 PBO=0.93=嚴重過擬合);把 <30%/>50% 經驗法則寫進 F5。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B;docs/05(Minervini PBO=0.93);docs/20 §4(旗艦 combo 缺口);F5;O1 backtest/pbo.py — O1 backtest/pbo.py;抓 Minervini 過擬合;F5 的 PBO 門檻註記。 → **adopted-as-convention(已用於 Minervini);旗艦 combo 8 配置的 PBO=queued(docs/20 §4 明列缺口)**
- **angle_risk(座位是否切錯)**:低。工具在原生座位;唯一缺口是覆蓋範圍——旗艦 combo 家族從未正式跑 PBO,不是切入角度錯而是尚未套用。
- **reopen(重測觸發=資訊成本)**:對旗艦 combo 家族(8 配置)跑 CSCV-PBO 並在 F5 加門檻註記 → 資訊成本≈$0(既有回測,小算力)。
- **重測優先度**:🟡 中 — medium — 工具正確,但『旗艦 combo 從未跑 PBO』是具體且已登記的缺口,值得清掉

#### Brown-Goetzmann-Ibbotson-Ross 1992 — 資料完整性 / 倖存者偏誤
- **分類**:功能=資料完整性/驗證;原生棲地=基金績效樣本因存活截斷(廣宇宙×多年×用途=證明存活製造虛假持續性)。
- **Summary / 結論**:以存活截斷樣本會讓『波動-報酬』關係偽裝成績效持續性——單靠倖存者就能從純雜訊製造出『hot hands』,強到足以解釋已發表的可預測性。 結論:由當前上市代碼建的橫斷面 RS 排名與任何宇宙都是倖存者偏誤;下市/已死名必須在每個日期在冊,否則橫斷面因子可信度全毀。
- **我們的洞見**:點對點 universe 成分(含下市)是廉價現在做、昂貴事後補的硬前提(R3);TR-13 已給出倖存者膨脹的誠實區間 [+1.26%,+2.02%]/yr。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄B(§1 VALIDATES + R3);docs/11(#1 倖存者);TR-13(區間化);F11/F13 — 驗證 scorecard 的倖存者線;F11 宇宙合法性 + F13 資料層下市注入的依據。 → **adopted-as-convention(倖存者紀律已採納;經 TR-13 部分處理);完整 PIT 宇宙=queued/受阻於資料**
- **angle_risk(座位是否切錯)**:低-中。論文主張已正確採納,但我們的宇宙仍非完整 PIT——610 union 無下市代碼、以價格行為分類。BGIR 的完整防護需要真正的逐日成分史,這是尚未買到的資料維度,不是切入角度錯。
- **reopen(重測觸發=資訊成本)**:ingest 點對點指數成分史(Wikipedia 版本史=免費但髒 / iShares-SPDR 歷史持股 / CRSP=付費學術)+ 下市報酬 → 資訊成本:從免費髒資料到付費 CRSP。
- **重測優先度**:🟡 中 — medium — 論文已採納,但底層 PIT 成分/下市資料缺口未解、且 gate 住所有橫斷面因子的可信度;是缺關鍵資料型的重測

#### Harvey-Liu-Zhu 2016 — 回測嚴謹性 / 因子多重測試門檻
- **分類**:功能=驗證方法;原生棲地=因子動物園的領域級多重測試(數百因子×橫斷面×用途=校正後的顯著性門檻)。
- **Summary / 結論**:考量整個學界因子搜尋後,新因子的 t 門檻應提高到 ~3.0(而非 2.0);領域級多重測試把大量『發現』重新歸類為偽陽性。 結論:alpha 的 PASSED 門檻設 t≥3.0(或 BHY-FDR 1%)——這是領域級多重測試後的 alpha 標準。
- **我們的洞見**:把 t≥3.0 定為 F5/F8 的 alpha 硬門檻;旗艦多 sleeve 組合全成本 Carhart t=3.38 恰過此門檻(2× 成本壓力仍 t=3.14)。
- **用在哪 · 怎麼用 · 結果**:F5/F8(t≥3.0);docs/18 TR-15(t=3.38);docs/00 E9;README 核心公式表 — F5/F8 的 alpha PASSED 門檻;旗艦升級判定(TR-15)的達標線。 → **adopted-as-convention(alpha 門檻;旗艦以 t=3.38 過線)**
- **angle_risk(座位是否切錯)**:低。作為領域級門檻使用,棲地一致;殘留註記=旗艦過 HLZ 3.0 但未過全 campaign Bonferroni(需 t≈3.66),已誠實記錄。
- **reopen(重測觸發=資訊成本)**:收緊到 campaign 級 FWER(Bonferroni t≈3.66)或全面改用 BHY-FDR 1% → 資訊成本≈$0(既有 trial-registry 重算)。
- **重測優先度**:⚪ 低 — low — 慣例如設計運作;只有『收緊到 campaign 級』這一個已知且已記錄的開放項

#### Arnott-Harvey-Markowitz 2019 (AHM) — 回測嚴謹性 / 回測協定與研究紀律
- **分類**:功能=驗證方法(meta 協定);原生棲地=ML 時代的回測紀律檢查表(資產無關×用途=動工前的預先承諾)。
- **Summary / 結論**:提出 ML 時代回測的協定/檢查表:預先承諾研究計畫、避免多重測試與過擬合、要求樣本外與經濟合理性、對成本與資料窺探誠實。 結論:每個 TR 動工前應先寫可證偽宣稱、判準、原生棲地/座位、錯置風險與翻案條件——即 AHM 檢查表的操作化。
- **我們的洞見**:F0『預先承諾聲明』就是 AHM 檢查表的落地;並作為 v1.2 對抗性框架審查的基點之一。
- **用在哪 · 怎麼用 · 結果**:F0(預先承諾檢查表);docs/17 v1.2 審查基點;docs/00 E9 — F0 動工前預先承諾聲明的模板;fabric v1.2 審查基點。 → **adopted-as-convention(F0 檢查表即其操作化)**
- **angle_risk(座位是否切錯)**:低。作為 meta 協定/檢查表使用,原生用途就是 ML 時代回測紀律,與我們一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a — meta 協定不需重測;若協定更新版發布可增修 F0 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 流程紀律,已內化為 F0

#### Lo 2002 — 績效統計 / Sharpe 推論
- **分類**:功能=風險測量/統計;原生棲地=任何報酬序列的 Sharpe 統計推論(自相關校正的年化調整)。
- **Summary / 結論**:Sharpe 的年化與其標準誤受報酬序列相關性影響;有正自相關時 naive √252 年化會高估,需以自相關校正的除子調整。 結論:|lag-1 自相關|>0.05 時,Sharpe 年化須做 Lo (2002) 自相關校正,否則平滑/相依報酬的 Sharpe 灌水。
- **我們的洞見**:F3 規定超額-over-BIL Sharpe 且在自相關顯著時附 Lo 校正;已在 restate_rf_sharpe.py 實作 lo_factor 除子。
- **用在哪 · 怎麼用 · 結果**:F3;scripts/restate_rf_sharpe.py(lo_factor,lag-1..5);README 核心公式表 — F3 rf/基準慣例的一部分;restate 每個絕對 Sharpe。 → **adopted-as-convention(已實作於 restate_rf_sharpe.py)**
- **angle_risk(座位是否切錯)**:低。原生棲地=Sharpe 的自相關統計校正,與用途完全一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a(已實作);若要擴充到完整 IID/GMM 的 Sharpe 推論或多期重疊校正 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 已實作、在原生座位

#### Shumway 1997 (delisting) — 資料完整性 / 下市偏誤
- **分類**:功能=資料層/驗證;原生棲地=含下市代碼的 CRSP 型面板(NYSE/AMEX 績效型下市 ~−30%、Nasdaq ~−55%)。被測座位=無下市代碼的 610 檔 union、以價格行為分類。
- **Summary / 結論**:CRSP 遺漏的績效型下市報酬平均約 −30%(Nasdaq ~−55%);忽略它=以最後觀測價出場=系統性樂觀高估報酬。 結論:下市須注入終端報酬(併購型不注),否則凍結在最後價=教科書級倖存者高估。
- **我們的洞見**:TR-13:9 個窗內下市全為併購型(注 −30% 幾乎不動);真偏誤在 151 個被清除名,合成上界給出倖存者膨脹誠實區間 [+1.26%,+2.02%]/yr;凡引 610 union 絕對數字自此標區間。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-13;F13 資料層;docs/11(下市報酬);trial-registry — TR-13 跑實測並產出區間;F13 資料層下市注入規則(併購不注)。 → **PASSED(方法;TR-13 區間化完成)**
- **angle_risk(座位是否切錯)**:中。原生棲地=含下市代碼的 CRSP 面板;我們的座位無代碼、只能以價格行為分類——核心紀律=併購絕不能注 −30%(TR-13 自評錯置=中)。這是真實的錯置風險,但已被規則吸收;殘留=區間非點估計。
- **reopen(重測觸發=資訊成本)**:ingest CRSP 型下市代碼面板(WRDS 學術付費)→ 把 [+1.26%,+2.02%] 區間收成點估計;資訊成本=付費 CRSP/WRDS。
- **重測優先度**:🟡 中 — medium — 方法已過,但誠實數字只是區間;收緊需付費下市資料(明碼標價的資訊成本)

#### Hoffstein (rebalance timing luck) — 回測嚴謹性 / 再平衡時點運氣
- **分類**:功能=驗證方法/風險塑形診斷;原生棲地=任何日曆再平衡策略(棲地無關)。TR-12 F0 自評錯置=低。
- **Summary / 結論**:同一策略在不同再平衡錨定日之間的績效差是非技能雜訊,量級常超過策略間的比較差;正解=K 分批(每相位 1/K)或以相位平均序列作判定。 結論:單相位錨定的數字不可獨立採信;判定須用相位平均(tranche)序列。
- **我們的洞見**:TR-12:季動量 timing-luck 帶寬 1,753bps/yr(單相位數字自此不足採信)、月動量 746bps;旗艦 combo 相位免疫(30bps)無需改;實盤動量應 K=4 分批;定為 F12。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-12;F12;docs/18 TR-12(1,753bps) — TR-12 量化各家族帶寬 + 相位-0 位置檢驗;F12 再平衡相位規則。 → **PASSED(方法;TR-12 揭露 timing luck,3 修正生效)**
- **angle_risk(座位是否切錯)**:低。原生棲地=日曆再平衡策略(棲地無關),我們就在此座位窮舉全部相位測試;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a — 已於原生棲地窮舉相位測完;若新增其他日曆錨定策略,F12 直接套用 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 完全在原生座位、方法已過並已成 F12 強制關卡

#### Cederburg-ODoherty-Wang-Yan 2020 — 回測嚴謹性 / 波動管理的懷疑性控制
- **分類**:功能=驗證方法/控制組;原生棲地=股票波動管理組合、月頻——作為 Moreira-Muir(1/σ² 波動管理)宣稱的懷疑性靜態控制。
- **Summary / 結論**:對 Moreira-Muir 的波動管理組合做樣本外檢驗:風險匹配的靜態/恆定曝險常能複製甚至勝過波動管理的表現,顯示其樣本外優勢不穩健。 結論:任何『MDD 減半 / 風控增益』宣稱都要配風險匹配的靜態(常數曝險)控制;能被一個常數旋鈕複製的就不算增值。
- **我們的洞見**:TR-02b:靜態 57% 恆定曝險同 MDD、更高 exSharpe、零交易——Markov regime gate 對曝險決策零增值;TR-17:1/σ² 波動管理支配 KMZ 全部 18 變體但 Cederburg 警告其對靜態的優勢不穩健、勿直接當策略;定為 F6 v2 靜態控制 + Nagel 三件套之一。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-02(§Cederburg 補跑);F6 v2 靜態控制;TR-17(波動管理控制);docs/18 TR-02 — TR-02b/TR-17 的靜態控制組;F6 v2『擇時/複雜度類必答:哪個最簡單的控制能解釋它』。 → **adopted-as-convention(TR-02b/TR-17 的控制組;F6 標準攻擊武器)**
- **angle_risk(座位是否切錯)**:低。作為懷疑性控制工具使用,原生用途就是檢驗波動管理宣稱,與我們一致;控制『贏了』正是它該做的事。
- **reopen(重測觸發=資訊成本)**:n/a — 控制工具已採納入 F6;無翻案概念。若未來要把 1/σ² 波動管理當策略而非控制,才需重評其穩健性 → 資訊成本≈$0。
- **重測優先度**:⚪ 低 — low — 控制工具在原生座位正確使用,v1.2 審查已確認

#### GISW (Sharpe manipulation) — 績效測量 / 操縱防護度量
- **分類**:功能=風險測量;原生棲地=任何具選擇權式/凹型 payoff 的策略——Sharpe 等常見度量可被賣選擇權/動態策略人為拉高,MPPM 是不可操縱的替代度量。
- **Summary / 結論**:標準績效度量(含 Sharpe)可被具凹型/選擇權式報酬的策略系統性拉高(如賣尾部保險);作者提出理論上不可操縱的 MPPM(冪效用型)。 結論:當策略有負偏態/選擇權式 payoff 時,Sharpe/t 值會被操縱式高估,需以 MPPM 做操縱防護交叉檢核。
- **我們的洞見**:(尚未採納)——本專案整條評估鏈重度依賴超額-over-BIL Sharpe、Lo 校正 Sharpe 與 t 值,但從未套用 MPPM;而 L≥1.5 槓桿 combo 與防禦 overlay 正是 GISW 針對的偏態 profile。
- **用在哪 · 怎麼用 · 結果**:(無——repo 未引用);候選落點=F3/F8 的 Sharpe 評估層 — 未使用。repo 全域 grep Ingersoll/Spiegel/manipulat/MPPM 皆無命中(僅 Goyal-Welch 與一處 Welch t-test)。 → **not-yet-tested(全專案未引用;為候選採納項)**
- **angle_risk(座位是否切錯)**:尚未切入,故無『切錯座位』——但這正是盲點:我們用 Sharpe/t 評估的槓桿與防禦 sleeve 具凹型/負偏 payoff,恰是 GISW 警告 Sharpe 會被高估之處。等於我們一直用一把可被這些 payoff 操縱的尺。
- **reopen(重測觸發=資訊成本)**:當任一策略具選擇權式/負偏態 payoff(現有 L≥1.5 槓桿 combo、防禦 overlay,或未來 covered-call/short-vol sleeve)→ 加算 MPPM 作操縱防護交叉檢核;資訊成本≈$0(純度量、免費資料,唯一成本是實作)。
- **重測優先度**:🟡 中 — medium — 真實盲點(整條評估鏈依賴 Sharpe,且已有偏態 sleeve 落在 GISW 靶心),但採納極廉價;適合開一個小 TR / F3 增修

#### Petersen 2009 (clustered SE) — 計量統計 / 面板標準誤
- **分類**:功能=風險測量/統計;原生棲地=面板資料標準誤(跨時間/跨個體相依→需聚類校正)。docs/19 §5 原生座位=fabric 工具。
- **Summary / 結論**:面板迴歸的 OLS 標準誤在存在跨時間或跨個體相依時嚴重低估;比較 Fama-MacBeth、聚類(by firm / by time)等方法,指出應依相依結構選擇聚類維度。 結論:跨相依的變體/事件不是獨立樣本;有效樣本數與 t 值須做聚類校正(n_eff、月度 CR1 或 block bootstrap)。
- **我們的洞見**:TR-14:n_eff = k·n/(1+(k−1)·ρ̄) 套回各 TR 的 F4 宣稱(zoo 59 變體實為 1.8 個獨立賭注、QQQ+SPY ρ=0.94→n_eff 2,206 FAIL);Serenity(docs/16)月度聚類把 t=2.49 打回 ~1.0-1.4;定為 F4/F7 的聚類 t。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-14(tr14_neff.py);F4/F7(聚類 t);docs/16 Serenity(t 2.49→1.0-1.4) — scripts/tests/tr14_neff.py 實作 n_eff 聚類邏輯;F7 子期聚類校正 t。 → **adopted-as-convention(已實作 n_eff + 聚類 t)**
- **angle_risk(座位是否切錯)**:低。原生棲地=面板標準誤,與我們用途(跨相依變體/事件的聚類校正)完全一致;無錯置。
- **reopen(重測觸發=資訊成本)**:n/a(已實作);若要從 by-time 聚類擴到雙向聚類(firm×time)或 Driscoll-Kraay → 資訊成本≈$0(既有資料重算)。
- **重測優先度**:⚪ 低 — low — 已實作、在原生座位、v1.2 審查確認

### B.3 C. 組合與部位 (docs/03 附錄C)

#### Markowitz 1952 — 組合理論 / capital allocation (portfolio construction)
- **分類**:機制族=風險塑形·配置(mean-variance 框架公理)。原生棲地:資產=任意(需 N≥2)、頻率=任意(靜態單期)、廣度=需 μ 與 Σ 兩組輸入、年代=1950s 前指數化時代、用途=單期組合選擇。
- **Summary / 結論**:拒絕『最大化折現期望報酬』(該準則不蘊含分散),改以 E-V 規則:效率集在均值對變異數間取捨,且是共變異數(不是個別變異數)驅動分散效益。純理論/公理層論文,非可證偽的實證假設。 結論:選到好名字 ≠ 好組合;決定組合風險的是被選名單的 covariance structure,不是個別資產的優劣。
- **我們的洞見**:portfolio/ 必須消費一個 Σ 而非只吃 expected-return scores;相關性高的 Minervini winners(常同產業/同因子)不做 covariance-aware sizing 就會集中風險。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C；src/trading_analysis/portfolio/covariance.py 與 allocators.py(covariance-aware 配置的前提)；docs/18 §3 rulebook(組合層再平衡) — 作為 portfolio 模組的框架公理:所有配置器都建立在『吃 Σ』之上,而非另做一個實證測試去驗證 E-V 本身。 → **adopted-as-convention(基礎框架公理,未單獨跑 TR;covariance-aware sizing 的地基)**
- **angle_risk(座位是否切錯)**:低。E-V 是公理不是我們去證偽的假設,無『錯座位』問題。唯一潛在錯置:把它當『max-Sharpe MVO 藍圖』照做——我們刻意沒有(見 Michaud/DGU),改用 risk-parity。因此真正被實證檢驗到的其實是它的 naive 實作(MVO),而非 E-V 原則;不要把 MVO 的失敗記在 Markowitz 頭上。
- **reopen(重測觸發=資訊成本)**:公理層,不需『重測』。唯一會改變用法的事件:取得夠長且穩定的 μ 估計(DGU:25 資產需 ~3000 月)——現實不可及,故 E-V 的 max-return 版永遠讓位給只用 Σ 的 risk-only 版。資訊成本=極長且 PIT 乾淨的歷史。
- **重測優先度**:⚪ 低 — low — 公理層框架,已內建於 portfolio 模組;本身不是可證偽的座位。

#### Michaud 1989 — 組合最佳化 / estimation risk
- **分類**:機制族=估計工程(對 MVO 的批判/警示)。原生棲地:資產=任意、頻率=任意、廣度=估計誤差顯著的 N、年代=1980s、用途=警示 naive optimizer、界定 robust/resampled MVO 為 baseline。
- **Summary / 結論**:MV 最佳化是『estimation-error maximizer』——系統性 overweight 報酬被高估、變異被低估、負相關為假象的資產,因此 unconstrained MV 樣本外可劣於等權。 結論:絕不上 naked/unconstrained MVO;要 box/turnover 約束,並以 resampling/robust MVO 為 baseline 而非 vanilla MVO。
- **我們的洞見**:O5 建構約束:never ship unconstrained MVO;把 max-Sharpe MVO 降為必須自證的 also-ran(R8),portfolio/ 改以 risk-parity/min-var 為主。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §1 VALIDATES + §2 O5;docs/18 §3(demote MVO);portfolio/allocators.py(改用 risk_parity/min_variance 的決策依據) — 作為負面設計約束寫死在 roadmap:攔截『PyPortfolioOpt MVO』roadmap 線的字面照做;塑造了『不建 naked MVO』的決策,而非跑一張 TR。 → **adopted-as-convention(建構約束;塑造『不建 naked MVO』的架構決策)**
- **angle_risk(座位是否切錯)**:低。Michaud 的主張=『naive MVO 壞』,我們正是在這座位上採納它(從不建 naked MVO),無錯置。它是負面約束不是我們去證偽的 alpha 機制;不會有『機制未定罪但座位錯』的疑慮。
- **reopen(重測觸發=資訊成本)**:若取得穩健的 robust/resampled-MVO 實作 + 顯著更長的估計窗,可測『約束後 MVO 是否勝 risk-parity』——但 DGU 已預示於我們的資產數不太可能。資訊成本=更長歷史 + 更多(異質)資產的 PIT 資料。
- **重測優先度**:⚪ 低 — low — 已在正確座位採納為約束;非決策路徑上的可證偽機制。

#### DeMiguel-Garlappi-Uppal 2009 — 組合配置 / optimizer benchmark
- **分類**:機制族=風險塑形·配置的 hurdle/benchmark(naive 1/N)。原生棲地:資產=股票組合、頻率=月頻、廣度=各資料集約 10-25 資產、年代=1970-2004、用途=作為任何 optimizer 的樣本外門檻。
- **Summary / 結論**:14 個模型 × 7 個資料集,無一在 Sharpe、CEQ、換手上穩定勝 naive 1/N;sample-MVO 要勝 1/N 所需估計窗約 3,000 月(25 資產)、6,000 月(50 資產)——實務不可及。 結論:1/N 是 mandatory benchmark;任何 optimizer 必須在 walk-forward 上『淨換手』勝等權才准 size 實盤部位。
- **我們的洞見**:把等權設為硬性 scorecard 線(新增一條);start with risk-parity/min-var(避開 DGU 證明無望的 μ 估計),max-Sharpe MVO 必須自證。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §1;src/.../portfolio/allocators.py::equal_weight;TR-07 兩 Arena 皆列『等權(DGU 門檻)』;scripts/gate_3x_voo.py 的年度等權對照 — 在每個組合類 TR 都放『等權(DGU 門檻)』作對照;gate_3x_voo 也放年度等權 47 作 beta 對照。 → **adopted-as-convention(強制 1/N benchmark)+ 於我們座位 empirically CONFIRMED — TR-07 中 1/N 勝或平所有 optimizer(Arena A 等權 sleeves +24.95%/Sh 1.26;Arena B 月度等權 Sh 1.26 ≥ HRP 1.22 ≥ min-var(LW) 1.12)**
- **angle_risk(座位是否切錯)**:低-中。我們座位(5 sleeves N=5;47 同質高相關股)N 比 DGU 更小、相關更高,對 1/N 更有利,故 1/N 勝出是 DGU 的直接預言而非錯置。唯一 caveat:sleeves 是先前研究的樣本內產物(繼承偏誤),但那只影響絕對水準,不影響 1/N vs optimizer 的相對比較。
- **reopen(重測觸發=資訊成本)**:宇宙擴到大 N 異質(50+ 跨資產)且有長歷史時,optimizer 才有機會勝 1/N。資訊成本=多資產 PIT 資料 ingest + 長歷史。
- **重測優先度**:⚪ 低 — low — 已在正確(甚至更有利)座位確認;1/N 作為門檻是常態運作,不是待翻案項。

#### Ledoit-Wolf 2004 — 共變異數估計 / estimation engineering
- **分類**:機制族=估計工程(covariance shrinkage)。原生棲地:資產=廣橫斷面、頻率=任意、廣度=N 接近/超過 T 的樣本共變異、年代=2000s、用途=為任何 Σ-based 步驟提供穩健輸入。
- **Summary / 結論**:sample Σ 在 N→T 時充滿估計誤差;向結構化目標(此處 constant-correlation 模型)以解析最適強度 δ* 收縮;所有測試情境給最高 information ratio、最低實現波動。 結論:任何 Σ-based 步驟(MVO/min-var/risk-parity)都必須用 LW 收縮,絕不用 raw sample Σ。
- **我們的洞見**:全域強制的建構約束(一個 sklearn import、CPU-trivial、zero infra cost),讓 risk-parity/min-var 從第一天就吃收縮後的 Σ。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + §2 O5;src/.../portfolio/covariance.py::shrunk_covariance(LedoitWolf/OAS);TR-03(PCA vs LW)、TR-07(min-var 用 LW)、docs/08 combo build(validate_recommendation.build_combo) — shrunk_covariance() 包住 sklearn 的 LedoitWolf/OAS,是所有配置器與因子共變異的預設輸入。 → **adopted-as-convention(全域強制);間接於 TR-03/TR-07 驗證有效 —— TR-07 中 LW 收縮讓 min-var 波動(18.17%)反而低於 HRP,先行解決了 HRP 想解的病態矩陣問題**
- **angle_risk(座位是否切錯)**:低。LW 用在其原生用途(共變異估計清理),座位正確。唯一『未做』不是錯置而是同族第三方法未橫評:尚未畫我們宇宙的特徵值譜 vs Marčenko-Pastur 帶、未比 LW vs eigenvalue-clipping vs 非線性 LW2020(docs/20 §2 的 TR-03b 佇列)。
- **reopen(重測觸發=資訊成本)**:執行 TR-03b:47/610 宇宙特徵值譜 vs MP 帶(幾個真訊號特徵值?),把 MP-clipping 加入 TR-03 競技場(vs LW vs PCA vs sample)。觸發=想在更大 N 宇宙做共變異估計時;資訊成本低(現有資料即可跑)。
- **重測優先度**:🟡 中低 — low-medium — 已全域採納且有效;medium 僅在於『LW vs MP-clipping vs LW2020』估計器 horse-race 尚未跑(TR-03b 佇列,便宜、可隨時執行)。

#### Kelly 1956 — 部位 sizing / growth-optimal capital allocation
- **分類**:機制族=風險塑形·配置(growth-optimal sizing)。原生棲地:資產=任意、頻率=任意、廣度=需已知且穩定的 edge/odds (p,b)、年代=1956、用途=把二元 side 轉成 sized position。
- **Summary / 結論**:以最大化 G=E[log(wealth)] 下注(二元賭注 fraction=edge/odds)使資本以最大指數率成長,且在非終止賽局以機率 1 支配任何其他策略;押全資本雖最大化期望財富但幾乎必破產。 結論:用 fractional/half-Kelly(full Kelly 給定估計誤差太激進)由 meta-label 機率 p 與 triple-barrier payoff ratio b 來 size,而非固定比例或 raw signal strength。
- **我們的洞見**:sizing 應由機率驅動;half-Kelly 是 Michaud/DGU『估計誤差』教訓在 sizing 層的對應。真正存活並產生價值的用法是回撤預算 / 雙向槓桿 L 刻度。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C + R2;src/.../portfolio/sizing.py::kelly_leverage(fraction=0.5, cap);docs/18 PASSED『回撤預算/雙向槓桿刻度』+ scripts/defensive_overlay.py;docs/19 §3(Kelly/回撤預算/L 刻度=如設計運作) — kelly_leverage(expected_return, variance, fraction=0.5, cap) 實作 half-Kelly;在防禦 overlay 以回撤預算/L 刻度落地(L≥1.5 combo 支配 VOO)。 → **adopted/implemented(half-Kelly 已實作)並作為『回撤預算/L 刻度』屬 PASSED 風險塑形(L≥1.5 支配 VOO)。但 R2 原案『Kelly 由 ML 機率驅動』因餵它的 meta-label edge(TR-08/11)FAILED 而未 productive 部署——存活的是 drawdown-budget/L-scale 這支。**
- **angle_risk(座位是否切錯)**:中。原生 Kelly 需要『已知且穩定的 edge (p,b)』。我們的 ML p(TR-08/11)FAILED,所以『Kelly 由 ML 機率驅動』這座位其實從未有可靠 edge 可 size——不是 Kelly 機制錯,是上游 alpha 缺席(G-S:$0 資訊成本 → $0 edge → 無可 size 之物)。因此『Kelly 有沒有幫助』的判定被上游 alpha 缺席污染;存活座位(drawdown-budget/L-scale on beta 曝險)是 Kelly 另一種、可運作的用法。
- **reopen(重測觸發=資訊成本)**:任何 sleeve 產出穩健 OOS edge (p,b) 時,Kelly-by-probability 座位重開——但那 gated on 先突破 alpha 牆(付資訊成本:日內/選擇權/另類資料)。否則維持 drawdown-budget/L 刻度用法。
- **重測優先度**:🟡 中 — medium — 機制本身如設計運作(已實作、L-scale PASSED);待重測的是『有真 edge 時的機率驅動 Kelly』,但它 gated on 先有 alpha,故非獨立高優先。

#### Cover 1991 — online 配置 / regret-minimizing allocation
- **分類**:機制族=風險塑形·配置(assumption-free online allocation)。原生棲地:資產=多資產、頻率=(隱含)長 horizon 再平衡、廣度=CRP 家族、年代=1991、用途=無統計假設下追平事後最佳 CRP 的 regret benchmark;關鍵:無交易成本。
- **Summary / 結論**:對所有 constant-rebalanced portfolios 做表現加權平均即為『universal』:不需任何市場統計假設(明確允許 1929/1987 崩盤),漸近成長率追平事後選定的最佳 CRP,(1/n)·ln(S*_n/S_n)→0。 結論:一個 no-estimation、no-Σ、no-μ 的 online 配置 baseline;定位為 research benchmark,而非核心依賴。
- **我們的洞見**:regret/robustness 心態支撐我們的 walk-forward 紀律;可作 assumption-free 對照,但明確標為低優先(R8),不進核心。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C(明列 optional low-priority benchmark)+ §3 R8 demote 段;docs/18(未見於任何 TR);未實作於 src/ — 僅作為觀念上的『無假設對照』寫入 roadmap;未寫任何程式。 → **not-yet-tested(刻意延後為 optional benchmark;未建 module)**
- **angle_risk(座位是否切錯)**:中-高(潛在)。Cover 原生棲地=長 horizon、**無交易成本**、CRP 家族,且 regret bound 是漸近的(需極長 n 才收斂)。若在我們日線、含成本、少資產、~10 年樣本座位測它,幾乎必因『無成本假設 + regret 未收斂』看似失敗——那會是錯置而非機制被駁。務必先想清楚座位再測。
- **reopen(重測觸發=資訊成本)**:想要一個 μ/Σ-free 的穩健對照時(例如質疑 risk-parity 的估計依賴),花小成本實作 UP / online-Newton-step 當 benchmark。資訊成本低(現有日線即可),但必須在誠實層下:含成本 + 標註『漸近保證、短樣本 regret 未收斂』。
- **重測優先度**:⚪ 低 — low — 刻意延後的 optional benchmark,非決策路徑;若實作,重點在避免錯置誤判(含成本 + 短樣本註記),而非搶跑。

#### Lopez de Prado HRP — 組合配置 / hierarchical (graph-based) allocation
- **分類**:機制族=風險塑形·配置(hierarchical/graph-based allocation)。原生棲地:資產=大 N 異質宇宙(數十~百資產)、頻率=任意、廣度=越大 N 越異質越有利、年代=2016、用途=不需反矩陣、避開 Markowitz 之咒的樣本外穩健配置。明示為風險配置器,不宣稱選股 alpha。
- **Summary / 結論**:相關矩陣→距離 d=√(0.5(1-ρ))→single-linkage 樹→準對角化→遞迴二分,兩半各以叢集內反變異數算變異、按 α=1-v0/(v0+v1) 分配。不需反矩陣;MC 中樣本外變異比 CLA min-var 低約 31%、優於天真反變異數(IVP)。 結論:(我們的)於兩個被測座位 HRP 輸現役 log-barrier risk-parity(5 sleeves 上 Sharpe 1.44 vs 1.04,HRP 把 69.9% 塞進債券);LdP 的 −31% 變異優勢在真實資料縮到 −8%;字面『勝 1/N』不成立(Sh 1.22 vs 等權 1.26)→ 不換權重引擎。
- **我們的洞見**:不換配置引擎;但保留 HRP 的樹/dendrogram 當『約束』——47 檔選股設『每叢集最多 k 檔』防單一叢集(半導體/軟體/國防)集中,F6 permuted-HRP 控制組證明此結構資訊有真增量。純降波動則反波動以 1/7 換手拿到多數效果、更划算。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄C(R8);docs/tests/TR-07-hrp.md(PARTIAL);docs/18 TR-07;docs/19 §3(錯置中-高);scripts/tests/tr07_hrp.py;src/.../portfolio/allocators.py — TR-07 兩 Arena(5 sleeves 13,045 bar×asset;47 檔 119,863 bar×asset),月頻 walk-forward、10bps/腿、permuted-HRP 20-seed 控制組;scipy 重寫 HRP 對打現役 risk_parity/min-var/等權/反波動。 → **PARTIAL(TR-07:機制如設計降波動 −3.9pp,permuted-HRP 控制證明來自叢集結構而非權重分布;但決策問題輸現役 risk_parity → 不換)**
- **angle_risk(座位是否切錯)**:中-高 —— 本批最需注意錯置的一篇。HRP 原生棲地=大 N 異質;我們兩座位都對它不利(N=5 太小,single-linkage 在小 N 鏈化、切點不穩;47 檔同質高 beta 叢集 2022 一起跌)。TR-07 的 PARTIAL/輸只關閉『小 N』與『同質』兩座位,**不定罪 HRP 於其原生大 N 異質宇宙**。此外 LW 收縮已先替我們解掉 HRP 想解的病態矩陣問題,削弱了它相對 min-var 的原始賣點。
- **reopen(重測觸發=資訊成本)**:取得 50+ 檔真異質多資產宇宙(跨股/債/商品/國際/另類)即重測 HRP 於其原生棲地。資訊成本=多資產 PIT 資料 ingest(收斂回 docs/11『資料維度是綁定約束』)。
- **重測優先度**:🟡 中 — medium — 錯置風險中-高(座位明顯偏離原生棲地),但『要不要換(決策問題)』已在我們實際使用的座位穩固回答、且 LW 已解掉其核心賣點,故 HRP 本身重測是 medium(待有大 N 異質宇宙資料時),不是 high。

### B.4 D. 執行與微結構 (docs/03 附錄D)

#### Kyle 1985 — 市場微結構 / 最適執行（price impact）
- **分類**:機制族=執行·流程類（價格衝擊/市場微結構）。原生棲地：資產=單一風險資產；頻率=連續拍賣/tick；廣度=單資產；年代=1985；用途=策略性知情下單下的價格發現。座位對照：docs/19 執行類。錯置風險=中——我們從未在其原生『策略性知情下單』座位使用，只借 λ 當 Amihud 成本代理。
- **Summary / 結論**:Kyle 1985 建立線性均衡：知情交易者的淨訂單流以單一常數 λ 推動價格，市場深度=1/λ，衝擊永久且線性、λ∝√(雜訊變異/私有資訊變異)。我們沒在其原生的『策略性知情下單/價格發現』座位使用，只借 λ 當 Amihud 成本代理，把回測的固定 bps 成本升級為 size-dependent。在 $100k 零售規模衝擊項近乎零，spread 才是一階成本。 結論:價格衝擊由單一常數 Kyle-λ 治理（市場深度=1/λ），衝擊永久且線性、與訂單/ADV 成比例——固定 bps 成本假設在結構上錯誤。
- **我們的洞見**:採納 Kyle-λ≈(每日σ)/(每日$成交)=Amihud 流動性代理，把回測成本改成 size-dependent cost = spread/2 + λ·(trade_$/ADV)；但誠實記錄：$100k 零售書參與率≈0→衝擊項≈0、spread 才是一階，故 λ 項在我們的座位近乎惰性。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Kyle + §2 O2；backtest/costs.py（size_dependent_cost，已實作未接線）；docs/19 §1 執行類（Almgren-Chriss 列引用 costs.py） — docs/03 附錄D §Kyle + O2：設計 size-dependent 成本模型（backtest/costs.py 的 size_dependent_cost，λ=Amihud 代理）；docs/19 執行類引用。狀態：已實作、v1.2 審查（docs/20 §3）指出『從未接線』進回測。 → **adopted-as-convention（成本模型設計；costs.py 已實作但未接線進回測，非跑過 TR）**
- **angle_risk(座位是否切錯)**:中。我們從未在 Kyle 的原生座位（策略性知情下單、價格發現、機構/內線規模）使用它——只借了 λ 價格衝擊常數當 Amihud 每日流動性成本代理，套在 $100k 零售書上。此規模參與率≈0、衝擊項→0，等於把 Kyle 描述的核心機制（訂單流推動價格）用在它幾乎失效的座位；spread 才是一階。這不是誤判 Kyle（沒跑 TR），而是借來的機制在我們的座位近乎惰性——若日後規模放大或交易流動性差的小型股，λ 才會變成一階。
- **reopen(重測觸發=資訊成本)**:① 立即工程觸發：把 backtest/costs.py 的 size_dependent_cost 接線進回測（目前實作但未接線，v1.2 審查點名）。② 機制重開：資本規模放大到在所交易標的參與率>0，或改交易流動性差的小型股，使 λ·(trade_$/ADV) 變一階。③ 取得日內/tick 資料以直接估 λ（而非 Amihud 每日代理）——此為 G-S 意義下的一筆資訊成本。
- **重測優先度**:⚪ 低 — low — 已採納為成本慣例；零售規模衝擊項≈0（spread 一階），唯一待辦是工程接線 costs.py 而非重測

#### Bertsimas-Lo 1998 — 最適執行 / 交易成本分析
- **分類**:機制族=執行·流程類（區塊最適執行/實施落差）。原生棲地：資產=機構區塊單；頻率=日內 N 期分批；廣度=單標的區塊；年代=1998；用途=最小化期望執行成本。錯置風險=低——採納的是 implementation-shortfall 會計原則與 TWAP 基線，非在零售規模硬套 DP。
- **Summary / 結論**:Bertsimas-Lo 1998 把最佳執行寫成動態規劃（Bellman），證明在算術隨機漫步+線性永久衝擊的最簡假設下等量分批（TWAP）最適，資訊態加一個線性 shifting 修正。並以 Perold 實施落差（紙上 20%/yr→實盤 2.5%/yr）點出執行成本就是紙上-實盤缺口。我們採納 TWAP 基線與 implementation-shortfall 會計原則，TR-12 的 K=4 分批即此直覺。 結論:最適執行=Bellman 動態規劃；在算術隨機漫步+線性永久衝擊下最適解=等量分批（TWAP）；Perold 實施落差（紙上 20%/yr→實盤 2.5%/yr）證明紙上-實盤差距就是執行成本。
- **我們的洞見**:採納兩件事：(a) TWAP/等量分批為 execution/ 預設基線（最簡假設下可證最適、零調參）；(b) 以 implementation shortfall（arrival vs 實際成交）取代無摩擦 Sharpe 當頭條成本指標——直接對治 Perold 紙上-實盤缺口。TR-12 的 K=4 分批即 TWAP 直覺的體現。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Bertsimas-Lo + §3 R5 + §2 O2；TR-12（K=4 分批=TWAP 直覺）；rigor scorecard 的 implementation-shortfall 行（規劃中） — docs/03 附錄D §Bertsimas-Lo + R5：TWAP 為 execution/ 預設基線 + implementation-shortfall 頭條成本指標；TR-12 K=4 分批體現 TWAP 直覺對抗 timing-luck。 → **adopted-as-convention（TWAP 基線 + IS 會計原則；TR-12 K=4 體現，非獨立跑過 TR）**
- **angle_risk(座位是否切錯)**:低。採納的是正確高度的教訓（implementation shortfall 會計 > 無摩擦 Sharpe，Perold 20%→2.5% 例）與 TWAP 基線，而非在零售規模硬套區塊執行 DP。零售 $100k 幾乎不存在『單一大單需跨期分批』的問題，所以我們沒把 DP 誤置；TR-12 的 K=4 分批只是借用 TWAP 直覺對抗 timing-luck，座位相符。
- **reopen(重測觸發=資訊成本)**:① 當 execution/ 真正動工、需要 implementation-shortfall 帳本（arrival price vs 實際成交）時。② 資本規模使單筆單>數% ADV、必須跨期分批時，BL 的 TWAP-最適與 shifting 修正才有可測內容。零售規模下無此觸發。
- **重測優先度**:⚪ 低 — low — 原則已採納、TR-12 已體現 TWAP；零售規模無區塊分批問題可測

#### Almgren-Chriss 2000 — 最適執行 / 清算軌跡與風險
- **分類**:機制族=執行·流程類（風險趨避最適清算/交易半衰期）。原生棲地：資產=機構清算部位；頻率=日內排程；廣度=可組合層；年代=2000；用途=成本-風險效率前沿。docs/19 §1 已收錄：原生棲地=機構規模（參與率>0 的市場衝擊）。錯置風險=低——已辨識規模不符、誠實跳過，未誤測。
- **Summary / 結論**:Almgren-Chriss 2000 在 Bertsimas-Lo 上加入風險罰項，得成本期望-變異數效率前沿與封閉解交易半衰期 τ=1/κ（波動越高/流動性越差交易越快，τ 與外加期限 T 無關）。我們採納 τ 當容量檢查，但辨識原生棲地=機構規模、在 $100k 零售大型股座位衝擊項→0，故誠實跳過未開 TR，costs.py 留給 F2 v2 容量曲線。 結論:在 BL 上加風險罰項→成本期望-變異數效率前沿與封閉解交易半衰期 τ=1/κ；波動越高/流動性越差→交易越快；τ 是波動·流動性·趨避決定的內在時間尺度、與外加期限 T 無關。
- **我們的洞見**:採納『交易速度應為 σ 與流動性的函數』與 τ=1/κ 容量檢查（部位若 AC 半衰期>再平衡視窗即過大）；但誠實判定我們的規模不符其原生棲地（參與率≈0、衝擊項→0、spread 一階），故 costs.py 已實作但不另開 TR，留給 F2 v2 容量曲線引用。
- **用在哪 · 怎麼用 · 結果**:docs/20 §3；docs/19 §1 執行類（誠實跳過列）；docs/03 附錄D §Almgren-Chriss + §3 R5；backtest/costs.py（F2 v2 容量曲線待用） — docs/03 附錄D §Almgren-Chriss + R5 + docs/20 §3 + docs/19 §1 執行類：τ=1/κ 容量檢查納入路線圖；因規模不符誠實跳過未開 TR；costs.py 已實作留 F2 v2 容量曲線。 → **adopted-as-convention（設計採納為容量檢查；因規模不符誠實跳過、未開 TR；costs.py 已實作未接線）**
- **angle_risk(座位是否切錯)**:低（座位錯置已被正確辨識並規避）。docs/19 明確標註原生棲地=機構規模（參與率>0 的市場衝擊）；在 $100k 零售大型股座位參與率≈0、衝擊項→0，AC 的交易排程是二階問題、spread 是一階，因此誠實跳過未開 TR——即沒有把機構級清算模型誤測在零售座位上。殘餘角度風險純為『規模』：一旦資本放大或交易流動性差標的，AC 半衰期>再平衡視窗的容量檢查就變成一階。
- **reopen(重測觸發=資訊成本)**:資本規模達機構級或交易流動性差宇宙，使參與率>0、市場衝擊變一階；具體觸發=某部位使 AC 交易半衰期 τ=1/κ > 再平衡視窗（docs/19：F2 v2 容量曲線引用 costs.py 的 size_dependent_cost 時）。此為需要更大資金/更差流動性座位的重開。
- **重測優先度**:⚪ 低 — low — 已辨識規模不符、誠實跳過（未誤測）；僅機構規模/流動性差宇宙才重開

#### Obizhaeva-Wang 2013 — 市場微結構 / LOB 韌性最適執行
- **分類**:機制族=執行·流程類（LOB 韌性/供需動態）。原生棲地：資產=限價簿；頻率=日內訂單簿回補；廣度=單標的大單（20× 深度）；年代=2013；用途=韌性感知最適排程。錯置風險=低——未測、資料閘控（需日內 LOB），刻意只收斂成單一壓力旋鈕，非誤測。
- **Summary / 結論**:Obizhaeva-Wang 2013 證明最適排程取決於 LOB 韌性（訂單簿回補速度）而非靜態深度/點差，最適形狀是大初始單+小連續單+末端區塊（非等量），相對 TWAP 的節省隨回補時間增長（0.33%→1.88%→7.41%，20× 深度單）。我們決定不建 LOB 模擬器，只把韌性收斂成單一『回補半衰期』壓力旋鈕；因缺日內 LOB 資料，此旋鈕仍為設計未建。 結論:最適排程取決於韌性（LOB 回補速度）而非靜態深度/點差；最適形狀=大初始單+小連續單+末端區塊（非等量）；相對 TWAP 的成本節省隨回補時間增長（0.33%→1.88%→7.41%，20× 深度單）——挑戰 BL/AC 的 TWAP-最適結論。
- **我們的洞見**:採納『不建 LOB 模擬器，改把韌性收斂成單一回補半衰期敏感度旋鈕』，在成本模型/rigor scorecard 上以快/慢回補帶寬壓力測試淨 Sharpe——避免容量宣稱被樂觀日內流動性綁架。但因缺日內 LOB 資料，此旋鈕仍為設計、尚未建置。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄D §Obizhaeva-Wang + §3 R5；rigor scorecard 的 resilience-sensitivity 行（規劃中，未建） — docs/03 附錄D §Obizhaeva-Wang + R5：韌性=單一壓力旋鈕（回補半衰期）寫入 execution/ 成本模型與 rigor scorecard 設計；未建（需日內 LOB）。 → **not-yet-tested / queued（韌性壓力旋鈕設計，資料閘控未建）**
- **angle_risk(座位是否切錯)**:低（尚未測、資料閘控）。從未在任何座位套用，故無誤置；唯一角度風險是它的原生棲地（日內 LOB 韌性、訂單簿回補動態、機構單 20× 深度）需要我們在 <$15/mo 下沒有的日內 LOB 資料。我們刻意不建 LOB 模擬器、只把韌性收斂成單一『回補半衰期』敏感度旋鈕——這是正確的規避，不是誤測。
- **reopen(重測觸發=資訊成本)**:取得日內 LOB / 訂單簿韌性資料（G-S 意義下的資訊成本；<$15/mo 下目前受阻）+ 交易規模達到 ≥ 簿深度。具體觸發=ingest 日內 LOB 資料後，把『回補半衰期』從單一壓力旋鈕升級為真實估計。
- **重測優先度**:⚪ 低 — low — 資料閘控（需日內 LOB），現有資料維度無法測；正確延後

#### Grossman-Stiglitz 1980 — 資訊經濟學 / 市場效率（元理論）
- **分類**:機制族=描述·歸因 / 元理論（資訊經濟學均衡）。原生棲地：資產=理性預期資產市場均衡；頻率=跨頻率通用；廣度=市場整體、知情 vs 未知情交易者；年代=1980；用途=解釋為何完全效率不可能。錯置風險=中——作為框架哲學採納、非可測策略；風險=過度外推成『免費資料 alpha 全不可能』。
- **Summary / 結論**:Grossman-Stiglitz 1980 證明資訊有成本則完全效率不可能，均衡下知情交易的期望毛利恰等於資訊成本，alpha 被競爭到資訊成本線（永不歸零也永不免費）。這是本專案全部負結果的經濟學基礎：免費日線=$0 資訊成本→均衡 $0 alpha，能留下的只有風險溢酬與組合層風險塑形；每個翻案條件都是一筆資訊成本。 結論:資訊有成本→完全效率市場不可能；均衡=部分無效率，知情交易的期望毛利恰好等於資訊成本；alpha 被競爭到資訊成本線，永不歸零也永不免費。
- **我們的洞見**:把 G-S 定為全專案負結果的經濟學基礎：我們 130+ 機制實證收斂（免費日線上選股 alpha≈0、唯一 PASSED=組合層風險塑形）正是 G-S 均衡的直接預言——資訊成本=$0→均衡 $0 alpha。並據此重寫 alpha 判定哲學：任何 PASSED 的 alpha 必須能講出『誰在付我們資訊成本的補償』；每個翻案條件都是一筆資訊成本。
- **用在哪 · 怎麼用 · 結果**:docs/20 §6；README『我們如何判斷』；fabric F8 alpha 判定哲學註記；docs/11（資料維度=綁定約束）；作為全專案負結果的經濟學基礎 — docs/20 §6（本輪寫入）+ README『我們如何判斷』段 + fabric F8 alpha 判定哲學註記：定為全專案負結果的經濟學基礎與 alpha 判定哲學；docs/11『資料維度是綁定約束』的更深表述（要買 alpha 先付資訊成本）。 → **adopted-as-convention（框架哲學/元理論；非可測策略，無 TR）**
- **angle_risk(座位是否切錯)**:中（框架哲學採納，非可測機制）。角度風險不在『測錯座位』而在『過度外推』：我們把資訊成本=$0（免費日線）→均衡 alpha=$0 當作全專案負結果的解釋。但 G-S 本身預言 alpha 存活於資訊成本高、套利者少之處（小型股、被忽略角落）——若拿 G-S 當『免費資料上 alpha 一律不可能』的萬用擋箭牌，反而違背其精神。正確用法：它是為每一個『翻案條件』標價的透鏡（每筆資訊成本=一次潛在買回 alpha 的機會），而非否證一切的封口令。
- **reopen(重測觸發=資訊成本)**:非策略、無單一重開事件；它是為所有其他翻案條件『定價』的元條件。實務觸發=任何一次付出新的資訊成本（ingest 日內資料、選擇權鏈、另類資料、小型股 PIT 基本面）——每一筆都是 G-S 的資訊成本，付了就應重新檢查對應座位是否浮現超額報酬。
- **重測優先度**:⚪ 低 — low（作為重測目標）/ 但作為框架透鏡=高重要性常駐 — 非可測策略，每次付資訊成本時被重新援引以檢查 alpha 是否浮現

### B.5 E. 時序·均值回歸·波動 (docs/03 附錄E)

#### Lo-MacKinlay 1988 — time-series econometrics / random-walk test (trending vs mean-reverting structure)
- **分類**:機制族=估計工程·描述診斷(隨機漫步檢定,非α產生)。原生棲地:資產=美股 CRSP 指數與個股／頻率=週報酬／廣度=廣橫斷面(EW 指數的 VR>1 由小型股驅動)／年代=1962-1985／用途=統計檢定。本框架被測座位=日線滾動 VR 特徵(features/timeseries),用途正確但實作為簡化版。
- **Summary / 結論**:變異比(VR)檢定拒絕週報酬的隨機漫步:EW CRSP 指數 VR 隨 q 單調升破 1(q=2 的 1.30 到 q=16 的~2.0)、指數一階自相關 +30%(指數層動量,小型股驅動),但個股呈負自相關。對非同步交易與時變波動穩健。 結論:VR 是正典的無洩漏隨機漫步檢定;關鍵限定:指數層 VR>1 但單股 VR<1 ⇒ VR 依 regime／橫斷面座位而變,單一全域 VR 會誤標結構。
- **我們的洞見**:採納 VR 為 features/ 均值回歸包(Hurst/half-life/VR)的正典無洩漏工具;並內化『VR 符號依座位而變、單一全域 VR 會誤標』的限定。
- **用在哪 · 怎麼用 · 結果**:src/trading_analysis/features/timeseries.py (variance_ratio / rolling_variance_ratio, 預設 q=2);docs/03 附錄E + VALIDATES 表 line 17;docs/12 — 實作為 causal rolling feature 餵給趨勢／均值回歸辨識;從未單獨跑 TR。目前用同質性(homoskedastic)版本、固定 q=2、未報告 per-asset 符號分佈。 → **adopted-as-convention (作為特徵採納;從未作為策略跑 TR)**
- **angle_risk(座位是否切錯)**:低-中。棲地方向正確——它本就是診斷工具而非α來源,我們也用在對的地方。缺口在實作:用了會 over-reject 的同質性版本、固定 q=2、只算全域/單股卻未輸出符號分佈,而論文明確要求 heteroskedasticity-robust z*(q)、per-asset、多 q(2/4/8/16)+符號分佈。這是實作缺角,不是機制錯置。
- **reopen(重測觸發=資訊成本)**:當 VR 要從『描述性特徵』升格為『trend-vs-revert 交易 gate』時——升級為 Lo-MacKinlay 異質穩健 z*(q)、per-asset 計算、輸出符號分佈、q 參數化。無需新資料(現有日線即可),資訊成本=工程時間。
- **重測優先度**:⚪ 低 — low。目前僅描述性特徵,誤標成本尚未實現;一旦要拿 VR 當交易 gate 才升 medium。

#### Brock-Lakonishok-LeBaron 1992 — technical trading rules / 資料窺探警示的正典案例
- **分類**:機制族=α產生(技術規則:MA 關係 VMA + 區間突破 TRB)+驗證方法(bootstrap null)。原生棲地:資產=DJIA 指數／頻率=日／廣度=單指數／年代=1897-1986／用途=技術訊號可預測性。注意:掃描版影像 PDF、由既有知識摘要,確切數字需 spot-verify。
- **Summary / 結論**:DJIA 1897-1986,簡單移動平均(VMA)與區間突破(TRB)規則具預測力:買訊~12%年化 vs 賣訊為負,買日報酬變異低於賣日——與常數風險隨機漫步不一致;經 AR(1)/GARCH-M bootstrap null 顯著。 結論:MA/突破規則帶資訊——但它是資料窺探的正典警示:Sullivan-Timmermann-White 後續證明 BLB 的特定規則過不了全宇宙資料窺探校正。
- **我們的洞見**:兩件:(a) validates minervini_trend 前提(MA 關係規則帶資訊);(b) 更重要——它是反資料窺探的教科書,直接催生把 White Reality Check / Hansen SPA / DSR / PBO 加進 rigor scorecard,且 bootstrap null 應用 AR(1)/GARCH-M 而非 iid。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 263-266 + VALIDATES 表 line 13 + Theme Takeaway #1;催生 backtest/spa.py (Hansen SPA)、DSR、PBO(O1 模組);規則前提實測落在 docs/05/07(Minervini Sharpe 1.17→0.64)、TR-16(技術規則章節全關) — 作為方法論錨(反資料窺探)而非跑過的策略;其『技術規則帶資訊』前提體現在 Minervini/Vegas/ensemble 的實測(全數衰退/關閉)。 → **adopted-as-convention (資料窺探防線採納為 fabric 慣例;規則前提在我們座位實測=衰退/FAILED,但未以 BLB 原座位單獨跑 TR)**
- **angle_risk(座位是否切錯)**:中。我們從未在 BLB 原生座位(單一指數 DJIA、百年日線、VMA/TRB 精確規則)復現;而是把『技術規則帶資訊』搬到個股橫斷面(Minervini/Vegas)測,得衰退/FAILED。BLB 的正面結論本身已被 STW 全域窺探校正推翻,故我們的負結果與『校正後共識』一致——真正的殘餘風險是:掃描版摘要的確切數字(12%/yr 等)尚未 spot-verify。
- **reopen(重測觸發=資訊成本)**:(a) 若要正式引用 BLB 量化結論→需 OCR 或取得可抽取文字版做 spot-verify;(b) 若要原座位復現→需長歷史單指數日線(DJIA 1897-)。兩者皆低優先:方法論教訓已內化、正面結論已被文獻校正。
- **重測優先度**:⚪ 低 — low。方法論教訓已內化為 fabric 慣例,正面結論已被 STW 校正;僅摘要數字待 spot-verify。

#### Gatev-Goetzmann-Rouwenhorst 2006 — 統計套利 / 市場中性相對價值
- **分類**:機制族=α產生(統計套利·均值回歸)。原生棲地:資產=全市場股票配對／頻率=日線(部分日內調整)／廣度=廣橫斷面 distance-match(全 CRSP)／年代=1962-2002／成本=機構級／用途=市場中性套利。docs/19 §1 錯置=中。
- **Summary / 結論**:距離法配對(正規化價格差平方和最小配對,2σ 發散進場、收斂出場)在 1962-2002 賺~11%年化超額,超過保守交易成本、與單純反轉獲利有別,獲利載於一個未識別的共同潛在因子。 結論:~11%/yr 市場中性超額,但作者自陳 post-2002 因容量/擁擠而衰退;Do-Faff(2010/2012)證實 post-2010 淨成本後趨近 0。
- **我們的洞見**:2σ/0σ 進出=天然 triple-barrier;實測後結論=日線棲地衰退>100%,連現金都輸;共整合篩選本身有微弱訊號(勝 90% 隨機非共整合對)但絕對報酬不及格;『不相關∧不賺錢』sleeve 入組合反拖累 alpha t(2.66→1.79)。殘值=|z|>4 結構斷裂偵測可當個股異常警報。
- **用在哪 · 怎麼用 · 結果**:docs/tests/TR-01-stat-arb-pairs.md;scripts/tests/tr01_stat_arb_pairs.py;docs/18 註冊表 TR-01 列;docs/19 §1 pairs 列;docs/03 附錄E line 268-271 + Theme Takeaway #3 — TR-01 完整審判:47 檔同產業對、Engle-Granger 共整合選對(訓練 2015-19)、OOS 2020-2026(1,633 日)、10bps/腿、含 20 組隨機非共整合控制。 → **FAILED (OOS +1.96%/yr < 現金 BIL +2.70%;對現金超額 −0.7%/yr,衰退>100%,與 Do-Faff 一致)**
- **angle_risk(座位是否切錯)**:中-高——本批最需注意的錯置。(1) 選對方法錯位:GGR 用 distance(正規化價格 SSD 最小)選對,我們用 Engle-Granger 共整合檢定——不同座位,且共整合更嚴格、『訓練期最共整合的對往往後來結構斷裂最猛』(Type-II,SMCI/INTC −75% MDD);(2) 宇宙錯位:GGR 是全 CRSP 廣配對,我們只配 47 檔同產業高相關名字(9/10 對 AI_semis、6 對含 SMCI),集中度風險把 sleeve 綁在單一醜聞股;(3) 日線收盤 vs GGR 部分日內。文獻(Do-Faff)證實日線棲地整體衰退,故 FAILED 方向大致可信,但我們測的是 GGR 一個窄且非原生的切片。
- **reopen(重測觸發=資訊成本)**:(a) 便宜且該先做:用 GGR 原生 distance 選對(而非共整合)+更廣宇宙(跨 ETF/ADR/全市場)以現有日線重測——資訊成本=工程;(b) 真正救活需日內資料(ORB 級)+動態對池輪換(docs/11 ④)。各為一筆 G-S 資訊成本。
- **重測優先度**:🟡 中 — medium。原座位(distance+廣宇宙)未測,且我們用了非原生的共整合選法+極窄集中宇宙=真錯置;但文獻已示日線 pairs 整體衰退,故非 high。優先做便宜的 (a) distance+廣宇宙日線重測。

#### Engle 1982 — 波動計量 / 條件異質變異(ARCH)
- **分類**:機制族=風險測量·估計工程(條件變異數建模,非α產生)。原生棲地:資產=總經時間序列(UK 通膨)／頻率=不限／廣度=單序列／年代=1982／用途=條件變異數估計 + ARCH-LM 檢定。注意:掃描版影像 PDF、由既有知識摘要。
- **Summary / 結論**:提出 ARCH:條件變異數為過去平方誤差的函數,附 ARCH 效應的 LM 檢定,應用於 UK 通膨不確定性(2003 諾貝爾)。波動叢聚且可預測,即使報酬本身不可預測。 結論:報酬波動叢聚 ⇒ 任何假設同質 iid 報酬的顯著性/bootstrap 檢定皆設定錯誤;需 block/wild bootstrap 與 GARCH/AR(1) null。
- **我們的洞見**:核心教訓被採納:波動叢聚⇒拒絕 iid null⇒改用 block/wild bootstrap 與 GARCH/AR(1) null。但論文建議的 ARCH-LM 診斷本身未建入 rigor scorecard。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 273-276 + Theme Takeaway #1 flag;實踐 scripts/tests/tr05_gbm_mc.py(block bootstrap)、TR-11;ARCH-LM 未見於 src(grep 無) — 作為方法論約束(拒絕 iid null)。實踐落在 TR-05 用 stationary block bootstrap(Politis-Romano, b=21)當誠實 MC、TR-11 bagged/區塊重抽。ARCH-LM 檢定=建議未實作。 → **adopted-as-convention (波動叢聚⇒block bootstrap 教訓已採納;ARCH-LM 診斷=not-yet-implemented,GARCH 亦未建)**
- **angle_risk(座位是否切錯)**:低。我們沒有『測』ARCH 這個機制(它是計量工具非策略),而是採納其推論且用對了地方(block bootstrap)。殘餘風險僅在:未把 ARCH-LM 正式列為 scorecard 診斷、未量化我們資料的 ARCH 效應強度;加上掃描版摘要數字待 spot-verify。
- **reopen(重測觸發=資訊成本)**:若要正式報告我們宇宙的條件異質性強度、或把 heteroskedasticity-robust 標準誤自動化進 rigor→加 ARCH-LM 為 scorecard 診斷(現有日線即可,資訊成本=工程)。
- **重測優先度**:⚪ 低 — low。核心教訓已內化;ARCH-LM 僅把已知異質性顯性化,邊際價值低。

#### Bollerslev 1986 — 波動預測 / 條件σ 模型
- **分類**:機制族=風險測量·估計工程(前瞻條件σ 預測)。原生棲地:資產=金融時間序列／頻率=日／廣度=單序列／年代=1986／用途=波動預測(GARCH(1,1)=現代波動預測工作馬)。
- **Summary / 結論**:推廣 ARCH,讓當期條件變異數依賴過去的條件變異數(GARCH(1,1)),得到簡約的長記憶波動模型——現代波動預測的工作馬。 結論:GARCH(1,1) 預測 σ 用於『前瞻』風險遠優於滾動窗 std;部位規模應以『預測』波動(而非已實現波動)縮放。
- **我們的洞見**:認知採納(GARCH σ 優於滾動 std 用於前瞻風險、應以預測波動 size 部位),但從未實作。我們實際的波動估計仍是 trailing-window std / rvol / ATR;vol-target sizing 用已實現波動而非 GARCH。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 278-281 + Theme Takeaway #2;src 內無 garch 實作(grep 無);portfolio/sizing.py 現用已實現波動代理 — 建議 features/garch_vol(GARCH(1,1) 一步預測 σ,PIT/expanding fit)餵 portfolio/ risk-parity sizing 與 ml/ meta-label sizing——建議未建。 → **not-yet-tested (建議採納方向但從未實作、從未跑;現行以 trailing-std/rvol 代理前瞻風險)**
- **angle_risk(座位是否切錯)**:中。我們從未在任何座位測過 GARCH——既非採納也非否證,是純缺口。錯置風險=我們用 realized-vol 代理『前瞻風險』,而 GARCH 的整個賣點正是前瞻;若 vol-target/Kelly/MDD 門檻對前瞻 σ 敏感,realized 代理可能在 regime 轉折點系統性錯估(呼應 TR-05:平靜期校準外推到高波動必失真)。
- **reopen(重測觸發=資訊成本)**:當波動預測品質成為 binding(vol-target sizing 或 Kelly 部位在 regime 轉折被打臉,或要正式比較 forecast-σ vs realized-σ 的部位規模差異)→加 features/garch_vol(arch 套件, PIT fit, CPU 便宜合 <$15/mo, 現有日線即可)。純工程成本、無新資料。
- **重測優先度**:🟡 中 — medium。從未測=真缺口且便宜(現有資料+CPU 便宜);但現行 realized-vol sizing 已『如設計運作』(vol-target PARTIAL),GARCH 增量價值未證,故非 high。做一次 forecast-vs-realized σ 的 sizing 對照即可定案。

#### Hurst-Ooi-Pedersen 2017 — 時序動量 TSMOM / managed futures / 趨勢跟隨
- **分類**:機制族=α產生(時序動量 TSMOM)+風險塑形(vol-target)。原生棲地:資產=**67 個市場多資產(股/債/商品/FX 期貨)**／頻率=日-月／廣度=**跨資產低相關的組合書**／年代=1880-2016／用途=10% 波動目標的趨勢書。docs/19 §1 對應 Donchian/TAA 家族(原生多市場期貨)。
- **Summary / 結論**:波動縮放的 TSMOM(等權 1/3/12 月訊號、10% 年化波動目標、67 市場)在 1880-2016 每個十年皆獲利(前~100 年純 OOS),於股熊/回撤期賺最多(TSMOM smile),過 2-and-20 費用,但訊號延遲(尤其短視窗)顯著侵蝕報酬。 結論:趨勢跟隨是真實、非資料探勘的溢酬;兩個設計教訓:(1) vol-target 部位規模(書層 10% 波動);(2) 訊號延遲顯著侵蝕報酬——我們的 1-bar lag 是誠實最小值,別再加。
- **我們的洞見**:validates 趨勢跟隨為真溢酬 + 200-SMA/HMM regime gate + 1-bar lag=誠實最小值;vol-target sizing=最高槓桿的組合改動。但我們自己的動量實測=衰退:廣市場動量 ICIR≈0、XS 動量 P(beat EW)=23% FAILED、TAA/雙動量 crisis 保險真但 Sharpe 增強假。
- **用在哪 · 怎麼用 · 結果**:docs/03 附錄E line 283-286 + VALIDATES 表 line 13-15 + Theme Takeaway #2;實測 docs/09、TR-11、docs/13 §8;docs/19 §1 Donchian/TAA 列 — 作為趨勢引擎+regime gate 的理論背書;動量的實測散落 docs/09(廣宇宙 ICIR≈0)、TR-11(XS 動量 FAILED)、docs/13 §8(TAA PARTIAL)。TSMOM 原生形式(67 市場多資產 vol-target 書)從未建構。 → **PARTIAL/mixed (理論背書採納;我們測的動量座位=衰退/FAILED;TAA 版=PARTIAL(crisis 保險真、Sharpe 增強假);HOP 原生 67 市場 TSMOM=not-yet-tested)**
- **angle_risk(座位是否切錯)**:高——本批第二大錯置。HOP 主張是**跨 67 個低相關市場多資產(股/債/商品/FX 期貨)的時序動量+10% vol-target 組合書**,其 alpha 與 TSMOM smile(危機賺錢)本質來自跨資產分散。我們測的是**單一資產類(47-503 檔美股)的橫斷面動量**——既非時序動量、無多資產分散、無 67 市場廣度。我們的動量 FAILED 只關閉『窄同質股票 XS 動量』座位,完全不觸及 HOP 原生座位。docs/19 已明列為 Donchian/TAA 家族(單一股指座位失敗不能外推)。
- **reopen(重測觸發=資訊成本)**:取得多資產期貨資料(股指/債/商品/FX 期貨,數十個低相關市場)→建構 HOP 原生的 vol-target TSMOM 組合書,檢驗 crisis-alpha smile。這是整個新資料維度(期貨連續合約)=明確的 G-S 資訊成本。TAA 版已用 ETF proxy 部分覆蓋(docs/13 §8)但無法複製 67 市場廣度。
- **重測優先度**:🔴 高 — high。角度明顯錯(我們用單資產 XS 測、HOP 是多資產 TSMOM)且缺關鍵資料(期貨宇宙)=docs/19 明列高錯置。但需新資料維度,屬『high 優先但被資料成本 gated』——取得期貨資料前無法在正確座位測。

#### Marcenko-Pastur 1967 — 隨機矩陣理論 / 共變異矩陣的雜訊底
- **分類**:機制族=估計工程(共變異矩陣去雜訊,非α產生)。原生棲地:資產=不限／頻率=不限／廣度=**大 N(P/N 比為關鍵,漸近性需大 N)**／年代=1967／用途=共變異清理(RMT 雜訊底)。
- **Summary / 結論**:純雜訊樣本共變異的特徵值有封閉形式分布,支撐區間 [(1±√(P/N))²σ²];將 MP 帶疊在真實資料的特徵值譜上即可分離訊號與雜訊特徵值。 結論:MP 帶給出雜訊底:帶內特徵值=雜訊、帶上=訊號——據此可做 eigenvalue clipping(第三種共變異清理法,對比 shrinkage 與 sample)。
- **我們的洞見**:LW shrinkage(全域強制)+ TR-03 PCA 因子共變異是同一去雜訊問題的解;MP 視角預測 47/610 宇宙除少數(TR-03 量到 PC1=41.8% 一個大 beta)外多落雜訊帶內。但從未畫過我們宇宙的特徵值譜 vs MP 帶、也沒測過 eigenvalue clipping。
- **用在哪 · 怎麼用 · 結果**:docs/20 §2(理論再審思,含 TR-03b 佇列行動);概念上等同 LW shrinkage 全域 + TR-03 PCA(docs/18 TR-03 列、scripts)。注意:docs/03 VALIDATES 表 line 22 的『MP』是 McLean-Pontiff,非本篇。 — 作為為何做共變異 shrinkage 的理論底(採納同族解 LW/PCA);MP 特有的譜圖+clipping 診斷=佇列 TR-03b 未跑。 → **adopted-as-convention (經 LW shrinkage + TR-03 PCA 採納同族解) + queued (TR-03b:MP 譜圖 vs 帶 + eigenvalue clipping 對照,未跑)**
- **angle_risk(座位是否切錯)**:低。棲地方向正確——共變異估計就是它的原生座位,我們也確實在做共變異清理(LW/PCA)。唯一缺口:採納了『族』(shrinkage)卻沒跑 MP 的『特定診斷』(譜圖分離訊號/雜訊 + clipping 對照)。是診斷完整度缺口,非機制錯置。附註:我們宇宙 N 小(47-610),MP 的 P/N 漸近性在小 N 下較弱。
- **reopen(重測觸發=資訊成本)**:TR-03b:畫 47/610 宇宙樣本共變異特徵值譜 vs MP 帶(幾個真訊號特徵值?預期 3-5),把 MP-clipping 加入 TR-03 競技場(vs LW vs PCA vs sample)。現有日線即可,純工程成本,已在佇列。
- **重測優先度**:🟡 中低 — low-medium。已在正確棲地用同族方法(LW/PCA 皆『如設計運作』);MP 特定診斷是錦上添花且便宜、已佇列;預期 clipping≈LW(同族),增量價值可能小,故不急。

### B.6 F. 複雜度·近期 (docs/20)

#### KMZ 2024 (Virtue of Complexity) — 資產定價 / 單資產市場擇時 (high-dimensional return prediction, ML)
- **分類**:α 產生類 — 機制族=單資產市場擇時 (RFF + ridge(less) 超參數化高維回歸)。原生棲地:資產=美股大盤指數;頻率=月;廣度=1 (單資產,非橫斷面);年代=1926-2020 (95 年,含多次衰退);用途=return-timing。docs/19 §1 標記錯置風險=中-高。
- **Summary / 結論**:在 P>T 的超參數化 ridgeless 回歸下,單資產擇時的 OOS 期望表現隨特徵數 P 嚴格遞增,最適 shrinkage 再增益。15 個 Goyal-Welch 總經預測子經 Rahimi-Recht 隨機傅立葉特徵展開到 P=12,000、T=12 月滾動窗,1926-2020 擇時 Sharpe 增益約 0.47 (t≈3);R² 大幅為負但被論文論證為無經濟意義。 結論:複雜度(更多參數)在低訊噪的金融擇時裡是美德而非詛咒:負 R² 與高 Sharpe 並存,倉位自發學會近 long-only 並在 15 次衰退前撤出 14 次。
- **我們的洞見**:「keep it simple」在本框架應是實證結論而非教條;我們的 ML FAILED (TR-08/11) 是在 47 檔橫斷面樹模型的座位得到,從未在 KMZ 的座位 (單資產 + RFF + ridge + T=12 滾動) 上測過,必須實測而非援引。
- **用在哪 · 怎麼用 · 結果**:TR-17 (docs/tests/TR-17-virtue-of-complexity.md);docs/20 §1;docs/18 註冊表 TR-17 列;docs/19 §1 α 產生表 KMZ 列 — 在我們的資料上復現機制形狀:SPY 1993-2026 (~389 OOS 月) + QQQ,15 個可建構的價格/利率預測子,RFF + kernel-form ridge,T=12 滾動,P 從 2 掃到 12,000 畫 VoC 曲線;加 fabric 誠實層 (Nagel 控制 + 淨成本 + 截倉 + n_eff 註記)。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:中-高。配方對、棲地錯:我們用了正確的 RFF+ridge+T=12 機制,但切入的是 33 年 vs 論文 95 年、純價格/利率訊號 vs Goyal-Welch 總經預測子、有成本+截倉 vs 無成本+無限倉。TR-17 承認這是「機制形狀」復現而非 alpha 宣稱 (n_eff<3000)。VoC 乾淨階梯沒出現 (SPY 曲線嘈雜非單調、QQQ 甚至 P=12 最佳),且被 1/σ² 波動管理控制決定性支配。結論=棲地差異,非機制證偽——KMZ 定理未被推翻。
- **reopen(重測觸發=資訊成本)**:Ingest 公開的 Goyal-Welch 月度總經預測子資料集 (1926-present),在 95 年長樣本 × 15 個總經序列的原生棲地上完整復現並重跑 TR-17 腳本。資訊成本=取得+對齊 GW 資料集 (公開、成本低)。
- **重測優先度**:🟡 中 — medium — 屬「配方對但缺關鍵資料 (長歷史+總經預測子)」,GW 資料集公開使成本低;但 TR-17 已在可及座位判 PARTIAL 且 Nagel 控制決定性獲勝,原生棲地重測的邊際資訊有限。

#### Rahimi-Recht 2007 (Random Fourier Features) — 機器學習 / 核方法近似 (kernel approximation)
- **分類**:估計工程類 (工具組件,非交易機制) — 機制族=隨機特徵映射逼近 shift-invariant kernel。原生棲地=通用監督式 ML,不綁定任何資產/頻率/廣度;在本專案僅作為 KMZ 高維特徵生成器的數值組件。
- **Summary / 結論**:以隨機取樣的正弦/餘弦特徵逼近 shift-invariant (如 RBF) kernel,把 kernel 回歸轉成 P 個隨機特徵上的線性回歸;P 越大逼近越準,大幅降低算力。 結論:可用有限 P 個隨機傅立葉特徵近似無限維 kernel,使高維非線性回歸在計算上可行——KMZ 正是靠這個把 15 個預測子展開到 P=12,000。
- **我們的洞見**:採納為 TR-17 的實作組件:RFF 生成高維特徵,配合 kernel-form ridge (T=12 使 12,000 特徵的解只需 12×12 線性系統);它不是被測的 alpha 機制,而是復現 KMZ 的必要工具。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 F0 + 實作 (RFF 特徵生成、kernel 形式 ridge);docs/19 §1 KMZ 列括號註記「RFF+ridge」 — TR-17 特徵生成層:γ=1、seed=3、特徵權重按 P 固定、訊號視窗內標準化,登記為 18 變體試驗的基礎映射。 → **adopted-as-convention**
- **angle_risk(座位是否切錯)**:低 / 不適用。它是數值方法組件,沒有交易「棲地」,我們未把它當 alpha 測,故無錯置風險。唯一間接風險:若 RFF 實作 (特徵權重/標準化) 有 bug 會污染 TR-17 結論——但 seed/γ/特徵權重已固定並登記。
- **reopen(重測觸發=資訊成本)**:僅在 TR-17 重跑 (見 KMZ 條) 或懷疑 RFF 數值正確性時才回看;無獨立重測意義。
- **重測優先度**:⚪ 低 — low — 工具而非機制,沒有 alpha 宣稱要平反;只有 KMZ 重測時才會連帶用到。

#### Moreira-Muir 2017 (Volatility-Managed Portfolios) — 資產定價 / 因子擇時 (volatility timing)
- **分類**:風險塑形·配置類 — 機制族=波動管理 (以 1/σ² 逆向縮放曝險)。原生棲地:資產=股市因子組合 (市場/動量/價值等);頻率=月;廣度=不限;年代=戰後美股;用途=提升因子 Sharpe。在本專案作為擇時複雜度的對照控制 (Nagel 批評的化身);與 docs/19 §3 vol-target 列同族。
- **Summary / 結論**:按上月已實現變異數的倒數 (1/σ²) 縮放因子曝險,可在不擇報酬方向下顯著提升多數股市因子的 Sharpe 與 alpha:波動可預測但報酬不可預測,故低波期加倉、高波期減倉即賺。 結論:一個簡單的波動旋鈕 (1/σ²) 就能大幅提升風險調整報酬——正是 Nagel 用來質疑 KMZ「複雜度增益其實是偽裝的波動擇時」的基準。
- **我們的洞見**:作為 TR-17 的決定性控制:任何 KMZ 複雜度變體必須勝過 1/σ² 波動管理且對其 alpha-t≥2 才算真增益。結果 1/σ² 控制 (SPY +0.67 / QQQ +0.73) 決定性支配全部 18 個複雜度變體 → 複雜度在本座位=波動擇時的複雜包裝。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 R2 + §5 (Moreira-Muir 1/σ² = 決勝控制);docs/20 §1 (F6 v2 控制);docs/19 §3 vol-target 列;docs/13 §12 (vol-target 實測) — TR-17 §5 R2 判準的基準控制;registry 內另有 vol-target 家族 (strategy_zoo/highvol_ruleset) 獨立測過,判 PARTIAL:降 MDD 真、alpha 假、高波動宇宙反傷。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:中。用在正確的功能座位 (風險塑形控制) 且它贏了;但有未平角度:Cederburg (TR-02b) 已警告 1/σ² 對「靜態恆定曝險」的優勢通常不穩健,TR-17 也承認波動管理控制本身未扣成本、未對靜態曝險做二階控制。故「贏 KMZ」穩,「值得當獨立策略」尚未在扣成本+靜態控制下確立。
- **reopen(重測觸發=資訊成本)**:把 1/σ² 波動管理升級為 F6 v2 正式 sleeve 時,需加:(a) 交易成本 (換手高);(b) Cederburg 靜態恆定曝險二階控制;(c) 高波動宇宙反傷檢查。觸發事件=想把 TR-17 的控制轉成獨立配置策略。資訊成本=低 (資料已在手,只是加控制)。
- **重測優先度**:🟡 中 — medium — 作為控制的角色已確立且穩健;作為獨立 alpha 的座位 (扣成本+靜態控制) 未測,但 vol-target 家族已 PARTIAL 提示 alpha 大概為假,故非高優先。

#### Nagel 2025 / Buncic 2025 (VoC critique) — 資產定價 / 方法論批評 (ML market-timing critique)
- **分類**:驗證方法類 / α 產生類的反命題 — 機制族=對 KMZ VoC 的證偽 (主張複雜度增益=波動擇時 artifact)。原生棲地=與 KMZ 相同 (單資產月頻擇時),但立場=歸因/證偽;在本專案作為 TR-17 預先承諾判準 R2 的來源。
- **Summary / 結論**:Nagel/Buncic 質疑 KMZ 的複雜度 Sharpe 增益並非來自高維非線性學習,而是被複雜模型偶然重現的波動擇時 (1/σ²) artifact;控制掉波動擇時成分後複雜度的邊際貢獻消失。KM (2025) 有回應辯護。 結論:KMZ 的增益可能是波動管理的偽裝;正確檢驗是加入 Moreira-Muir 波動管理控制,看複雜度是否還有增量 alpha。
- **我們的洞見**:直接寫進 TR-17 預先承諾判準 R2:策略須勝波動管理控制且對其 alpha-t≥2,否則判定=波動擇時 artifact。這把誠實層建進復現裡,避免我們自己重蹈 KMZ 被批評的坑。
- **用在哪 · 怎麼用 · 結果**:TR-17 §0 R2 + §6;docs/20 §1 (直接檢驗 Nagel 批評);docs/19 §1 KMZ 列 (被 1/σ² 支配) — TR-17 §0 R2 判準 + §6 判定;結果站在 Nagel/Buncic 一側 (複雜度被 1/σ² 決定性支配),但明確聲明不推翻 KMZ 定理。 → **PARTIAL**
- **angle_risk(座位是否切錯)**:低-中。批評本身是歸因/證偽立場,我們用它當控制判準=正確用法。角度風險在於:我們只在可及的短樣本×技術訊號集上驗證了 Nagel 一側,無法在 KMZ 原生棲地 (95 年×總經) 上裁決 Nagel vs KM 的真正學術爭論——我們的 PARTIAL 不是對這場爭論的最終票。
- **reopen(重測觸發=資訊成本)**:同 KMZ 條:取得 Goyal-Welch 長歷史總經資料集後,在原生棲地上重跑,才能檢驗 Nagel 批評是否在 KMZ 自己的座位也成立 (而非只在我們的座位)。資訊成本=GW 資料集 (公開、低)。
- **重測優先度**:🟡 中 — medium — 與 KMZ 綁定;在我們的座位證據已足 (Nagel 側決定性獲勝),進一步裁決學術爭論需 GW 資料集,邊際價值中等。

#### Lou-Polk-Skouras 2019 (Overnight/Intraday) — 資產定價 / 報酬時段拆解 (return decomposition, clientele effects)
- **分類**:描述·歸因類 (診斷座位,非賺錢座位) — 機制族=隔夜 (收→開) vs 日內 (開→收) 報酬拆解。原生棲地:資產=美股大型股;頻率=日頻拆時段;廣度=廣橫斷面;年代=1993-2013;用途=歸因診斷 (溢酬住哪個時段、散戶近開盤 vs 機構近收盤的客群效應)。docs/19 §1 季節性/隔夜列。
- **Summary / 結論**:把日報酬拆成隔夜與日內兩段:大型股風險溢酬幾乎全在隔夜,動量溢酬約 +0.98%/月全在隔夜 (隔夜 Sharpe 0.77 vs 全日 0.31),低波動/價值反在日內賺;散戶近開盤、機構近收盤交易,形成時段客群效應。 結論:同一因子的報酬有強烈時段結構;動量的錢在隔夜,這改變再平衡成本假設與成交慣例的含義 (即使不拿來交易)。
- **我們的洞見**:值得做「診斷性拆解」而非交易:我們宇宙的動量/GP 溢酬住在哪個時段?若動量 book 報酬全在隔夜,月度收盤再平衡的成本與成交假設含義不同。我們只測過 QQQ 隔夜『作為策略』(毛 0.89/淨 −0.97 撞成本牆),從未做歸因拆解。
- **用在哪 · 怎麼用 · 結果**:docs/20 §7 (行動 → TR-19 佇列);docs/18 §行動總表隱含;docs/13 §4/§15 (隔夜『作為策略』=FAILED 成本牆);docs/19 §1 季節性/隔夜列 — 尚未執行;規劃為 TR-19 (佇列):47/503 檔動量 top-K book 與 GP 品質做隔夜/日內報酬拆解,預期動量偏隔夜 (LPS 複製) 但幅度衰退。 → **queued**
- **angle_risk(座位是否切錯)**:中-高。作為策略,我們在正確棲地 (SPY/QQQ 隔夜) 測過並撞成本牆=誠實負結果;但作為診斷歸因 (LPS 的原生用途),我們根本還沒切入,缺開/收盤分離資料。目前等於用錯座位 (整日報酬) 看一個時段性現象——動量歸因診斷的正確座位需要開盤價/收盤價分離。
- **reopen(重測觸發=資訊成本)**:用已有 OHLC 的 open/close 近似 (收→開 = prev-close→open、開→收 = open→close),對 47/503 檔動量 top-K book 與 GP 品質做時段拆解;若要精確再 ingest 日內資料。資訊成本=低 (OHLC 已在手,可低成本近似;精確版才需日內資料=中)。
- **重測優先度**:🔴 高 — high — 屬「診斷座位從未切入 + 資料 (open/close) 已可低成本近似」;不是為了交易 (成本牆仍立),而是為了修正動量 book 的成本/成交假設,是本批中最該優先做的小型診斷 (TR-19)。

#### Lakonishok-Lee (Insider) — 資產定價 / 另類資料因子 (insider trading signals)
- **分類**:α 產生類 — 機制族=內部人淨買入因子 (Form 4 open-market P/S 的橫斷面選股)。原生棲地:資產=美股廣橫斷面 (含小型股,小公司訊號最強);頻率=月/季;廣度=全市場;年代=1975-1995 (訊號廣為人知前);用途=選股 alpha。在本專案座位大致對,但廣度受限於 494 檔大中型股 + 2015-2024。
- **Summary / 結論**:內部人交易可預測報酬,尤其小公司內部人買入;內部人是逆向投資者,淨買入預示正報酬。訊號自 2001 公開後已廣為人知。 結論:內部人淨買入是方向正確的選股訊號,但屬已被廣泛知曉、易衰退的 alpha。
- **我們的洞見**:實測確認:方向對 (IC +0.011、hit 57%、與 Lakonishok-Lee 同號) 但因子弱且跨期不穩 (2016-19 約 0/負、2020-24 才轉正),過不了穩定性閘門,沒贏過 gross profitability (ICIR +0.30)。又一個 alpha decay 案例——唯一穩健的新 alpha 是基本面品質。
- **用在哪 · 怎麼用 · 結果**:docs/10 §4d (insider Form 4 因子實測);docs/13 §10 (FAILED 因子);docs/18 FAILED 表 (insider);docs/19 §1 需補列 (現以文字散見) — 接入 SEC bulk 季度 Form 4 (data/connectors/insider.py),ingest 2015-2024 共 65,503 筆 / 494 檔,建 net-purchase-ratio 因子 (trailing 6/12mo、以 filed 申報日 point-in-time snap 次交易日),過 factor_determination 閘門;value-weighted 與 count-based 結果幾乎相同 (訊號本身弱,非 outlier)。 → **FAILED**
- **angle_risk(座位是否切錯)**:中。座位大致對 (橫斷面選股、Form 4 filed PIT、open-market P/S)=棲地匹配良好;但廣度受限:只 2015-2024 × 494 檔大中型股,缺了 Lakonishok-Lee 最強的小型股 + 資訊未擴散的 1975-1995 年代。FAILED 誠實但可能低估——我們測的是訊號公開衰退後 (2001+) 的大中型股殘值,正是其最弱棲地。
- **reopen(重測觸發=資訊成本)**:擴充 insider 宇宙到小型股 PIT (Form 4 電子申報始於 ~2003,無法回補更早年代,唯一可及擴充=小型股廣度 + cluster-buy/高階主管加權等更細訊號結構)。資訊成本=取得小型股 PIT Form 4 + 小型股價格 (中)。
- **重測優先度**:🟡 中低 — low-medium — 已在大致正確的座位測過且輸 (符合『正確棲地輸=低』);但小型股廣度缺口使它非純低,若日後建小型股宇宙可順帶重測,否則 alpha decay 共識使重測價值有限。

#### de Prado AFML — 量化方法論 / 回測與 ML 工程 (financial ML methodology)
- **分類**:驗證方法類 + 估計工程/執行類 — 機制族=金融 ML 工程慣例 (triple-barrier labeling、trend-scanning、PurgedKFold+embargo、meta-labeling、CSCV/PBO、HRP)。原生棲地=通用量化回測稽核,不綁定資產;在本專案多數採納為 convention,HRP 例外=跑過 TR-07。docs/19 §5 驗證方法類。
- **Summary / 結論**:AFML 提供一整套對抗過擬合與洩漏的金融 ML 工程慣例:triple-barrier 標記、purged K-fold + embargo 交叉驗證、meta-labeling、CSCV/PBO 過擬合機率、HRP 階層風險平價。 結論:在低訊噪的金融資料上,正確的洩漏控制 (purge+embargo)、過擬合稽核 (PBO/DSR) 與淺樹/meta-labeling,比追求模型複雜度更重要。
- **我們的洞見**:大量採納為 fabric 慣例:triple-barrier/trend-scanning 標記 (σ-band=水平障礙,直接對應 pairs 2σ/0σ 進出場)、PurgedKFold 嚴格 purge+embargo (洩漏控制)、meta-labeling 淺樹、CSCV/PBO 當過擬合閘門 (O1)。也修正一條:purge 修的是洩漏不是選擇偏誤 (PBO/DSR 才管 selection),不能把 PurgedKFold OOS 機率當過擬合保護。HRP 我們實際跑了 TR-07。
- **用在哪 · 怎麼用 · 結果**:labeling/、labeling/cv.py、ml/meta_labeling.py、O1 (DSR/PBO/SPA);docs/03 §meta-labeling 對抗審查 (E1 修正);TR-07 (HRP);docs/19 §5 驗證方法類 — labeling/ (triple-barrier, cv.py PurgedKFold)、ml/meta_labeling.py (淺樹 meta-label)、O1 DSR/PBO/SPA 模組全域用於 docs/05-17;HRP 在 TR-07 於 5 sleeves + 47 同質股座位測。 → **adopted-as-convention**
- **angle_risk(座位是否切錯)**:低。這些是驗證/工程慣例,原生棲地=回測稽核,我們就在稽核座位上用=棲地匹配,v1.2 審查確認全部在原生座位使用。兩個被點名的角度修正:E1 (meta-labeling 的 lift = filtered vs full base-rate 是 de Prado 原意,但非『勝過同覆蓋率隨機濾網』的 edge,需補 precision-at-coverage);HRP 在我們小 N/同質宇宙 (5 sleeves + 47 同質股) 對它不利,TR-07 的『不換』只在此二座位有效。
- **reopen(重測觸發=資訊成本)**:HRP:取得 50+ 檔多資產異質宇宙後重測 (docs/19 標 HRP 錯置中-高,優勢隨 N 與異質性增長)。meta-labeling lift:補 precision-at-coverage 指標 (E1 修正,低成本)。其餘慣例:除非發現洩漏或 PBO 實作 bug 否則不需重開。
- **重測優先度**:⚪ 低 — low — 慣例已在正確座位確認;唯一有座位錯置的子項是 HRP (已在 TR-07 於不利小 N 座位測過判 PARTIAL『不換』,翻案需多資產大 N 異質宇宙),但那是 HRP 一項的事,不是整套 AFML 慣例的事。

---

## Part C — >2000 引用經典深讀計畫(尚未深測)

從 8 個子領域挑出 **64 篇** 引用超過 2000 的經典(去重後),皆與選股/交易相關。
分波原則見 Part A §A4。引用數為 agent 估計(canonical 地位),數字僅供排序,實際引用以 Google Scholar 為準。

### C.0 候選索引(依波次、引用數排序)

| 波 | 論文 | ~引用 | 子領域 | 可用免費資料重建? |
|---|---|---|---|---|
| ① | newey-west-1987 | 30000 | Econometrics & methodo | yes — 純標準誤重算，只需既有免費日/月報酬序列，零新資料、point-in-time  |
| ① | amihud_2002 | 11000 | Limits-to-arbitrage fr | YES (fully). ILLIQ = mean(|daily return|/daily |
| ① | debondt_thaler_1985_overreaction | 9500 | Long-term reversal / o | yes(有但書)。日線→月頻、36月形成/36月持有完全可算;point-in-time 用 |
| ① | daniel_hirshleifer_subrahmanyam_1998 | 7000 | Overconfidence + self- | YES/PARTIAL. Momentum (2-12m) + LT-reversal (3 |
| ① | pastor-stambaugh2003-liqrisk | 6500 | Market microstructure  | YES(核心可重建)。每股 γ:回歸 r_{i,t+1} = θ + φ·r_{i,t} + |
| ① | ang-hodrick-xing-zhang-2006-ivol | 6000 | Cross-sectional factor | yes — 只需免費日線報酬 + Ken French 日頻 FF3 因子(已接 panda |
| ① | ff88_divyield | 5000 | Return predictability  | yes — Shiller 免費長歷史月度資料(S&P 價格+股利,1871-)可直接建 D |
| ① | grs-1989 | 4200 | Econometrics & methodo | yes — 只需 sleeve/測試組合月報酬 + Ken French 因子（免費），構建 |
| ① | clark-west-2007 | 4000 | Econometrics & methodo | yes — 只需長指數歷史(SPY/QQQ)+免費預測子(估值比/動量/波動)，擴張視窗 O |
| ① | shanken-1992 | 2900 | Econometrics & methodo | yes — 純標準誤重算，用 TR-06 既有月報酬+β 估計即可，零新資料；point-i |
| ① | bali-cakici-whitelaw-2011-max | 2900 | Lottery demand / crash | YES, fully. MAX(k) = mean of the k largest dai |
| ① | stambaugh99_bias | 2800 | Return predictability  | yes — 純方法論,只需既有報酬+預測子序列;實作 Stambaugh/Kendall 偏 |
| ① | stambaugh-1999 | 2800 | Econometrics & methodo | yes — 用 EDGAR 估值/品質比(申報日對齊, point-in-time)+長報酬 |
| ① | grinblatt_han_2005 | 2600 | Disposition effect ->  | YES — the most cleanly buildable in this set.  |
| ① | mclean_pontiff_2016_academic_research_destroys | 2600 | Modern asset pricing — | yes (methodologically) — we already have a fac |
| ① | ct08_restrictions | 2400 | Return predictability  | yes — 沿用 TR-17 已有的 GW 預測子(公開資料)+ Shiller/FRED  |
| ① | george_hwang_2004_52wk | 2200 | 52-week-high momentum | yes。訊號=每檔 close / trailing-252日最高價,純免費日線 OHLCV |
| ② | bollerslev-1986-garch | 45000 | Conditional volatility | YES, fully. GARCH(1,1)/EGARCH fit on free dail |
| ② | hansen-gmm-1982 | 27000 | Econometrics & methodo | partial→yes — 檢定本身只需免費因子+測試組合月報酬，statsmodels/l |
| ② | diebold-mariano-1995 | 15000 | Econometrics & methodo | yes — 只需既有 OOS 預測序列(波動/報酬)+免費報酬；DM 統計量易實作(NW 標 |
| ② | petersen-2009 | 12000 | Econometrics & methodo | yes — 純標準誤重算，用既有 47/610 股票月報酬 panel 即可；零新資料；po |
| ② | shleifer_vishny_1997 | 9000 | Limits-to-arbitrage (t | PARTIAL (indirect). Not a signal itself. Test  |
| ② | lakonishok-shleifer-vishny-1994-contrarian | 8000 | Cross-sectional factor | yes — B/M、C/P(現金流/價)、E/P 由 EDGAR + 價格,過去銷售成長由  |
| ② | baker_wurgler_2006 | 8000 | Investor sentiment (ti | PARTIAL/YES. Characteristics (size, age, vol,  |
| ② | amihud-mendelson1986-spread | 7000 | Market microstructure  | PARTIAL。原文用『報價』價差,我們沒有(免費日線無 bid/ask)。只能用估計價差( |
| ② | hong_stein_1999 | 6500 | Gradual information di | PARTIAL. Momentum from price. Diffusion-speed  |
| ② | roll1984-effspread | 4800 | Market microstructure  | YES,有 caveat。只需免費日線收盤變動。Point-in-time OK。已知限制: |
| ② | acharya-pedersen2005-lcapm | 4500 | Market microstructure  | YES(可重建,較費工)。全部 4 個 beta 都由 Amihud 正規化 illiqui |
| ② | cochrane11_discount | 4200 | Return predictability  | yes(就其可檢驗核心)— 用 Shiller 免費資料跑『D/P → 未來股利成長』與『D |
| ② | chan_jegadeesh_lakonishok_1996_momentum_strategies | 4200 | PEAD / earnings moment | partial — SUE leg is testable: build (EPS_q -  |
| ② | ff89_business | 3800 | Return predictability  | yes — 期限利差(10Y-3M)、違約利差(Moody's Baa-Aaa)皆 FRED |
| ② | hou-xue-zhang-2015-qfactor | 3500 | Cross-sectional factor | partial→yes — I/A=年度總資產成長、ROE=季度淨利/權益,全在 EDGAR |
| ② | harvey_liu_zhu_2016_cross_section_expected_returns | 3500 | Modern asset pricing — | yes (methodological, no market data needed bey |
| ② | jegadeesh_1990_predictable | 3300 | Short-term reversal | partial。訊號(月頻排名)完全可用免費日線;但 1月短期反轉惡名昭彰地被 bid-as |
| ② | chan_jegadeesh_lakonishok_1996_momentum | 3200 | Price + earnings momen | partial。價格動量 leg=yes(免費日線)。盈餘動量 leg:SUE 可用 EDG |
| ② | cooper-gulen-schill-2008-asset-growth | 3000 | Cross-sectional factor | yes — 資產成長=Assets_t/Assets_{t-1}−1,EDGAR compa |
| ② | fama-french-2008-dissecting-anomalies | 3000 | Cross-sectional factor | partial — 方法(size 分層 + sort vs FM 對照)可直接採用,但完整 |
| ② | daniel-titman-1997-characteristics-vs-covariances | 2900 | Cross-sectional factor | partial — 需個股報酬(有)+ FF 因子(有)+ 特徵(B/M 由 EDGAR 權 |
| ② | moskowitz_grinblatt_1999_industry | 2800 | Industry momentum | partial-yes。報酬=免費日線。產業分類:EDGAR filer metadata  |
| ② | btz09_vrp | 2600 | Return predictability  | partial→大致 yes — VIX(CBOE 免費,1990-;VXO 至 1986) |
| ② | fama_french_2008_dissecting_anomalies | 2600 | Fundamentals / cross-s | partial — needs EDGAR PIT fundamentals (accrua |
| ② | stambaugh_yu_yuan_2012 | 2400 | Investor sentiment x a | PARTIAL/YES. Anomaly L/S from EDGAR + price. B |
| ② | ang-chen-xing-2006-downside-risk | 2400 | Downside / tail-beta p | YES. Downside beta = slope of stock excess ret |
| ② | daniel_moskowitz_2016_crashes | 2300 | Momentum crashes / ris | yes。WML 因子、崩盤事件描述(2009 動量崩盤)、動態加權都可在 503 宇宙+指數 |
| ② | cs98_cape | 2300 | Return predictability  | yes — Shiller 免費資料直接含 CAPE(1881-),trailing 10  |
| ② | rsz10_combination | 2300 | Return predictability  | yes — 完全複用 TR-17 既有 GW 預測子(公開/免費),只加預測值簡單平均與 O |
| ③ | heston-1993-stochastic-vol | 10000 | Stochastic volatility  | PARTIAL/NO. Pricing use = NO (needs a PIT opti |
| ③ | delong_shleifer_summers_waldmann_1990 | 9500 | Noise trader risk (lim | PARTIAL/NO for the canonical test. The classic |
| ③ | merton-1976-jump-diffusion | 8500 | Jump risk / crash risk | PARTIAL->YES for the physical side. Jumps are  |
| ③ | banz-1981-size-effect | 7000 | Cross-sectional factor | no/partial — 市值=價格×股數(EDGAR 股數 PIT 可行),但 size  |
| ③ | french-schwert-stambaugh-1987 | 5500 | Volatility-return trad | YES. Only market index daily/monthly returns a |
| ③ | chordia-roll-subrahmanyam2000-commonality | 3000 | Market microstructure  | PARTIAL。原生度量=日內報價價差/深度,我們沒有。只能用日線 Amihud ΔILLI |
| (已參照) | black-scholes-1973 | 45000 | Option pricing (baseli | NO for pricing (no PIT options chain — budget; |
| (已參照) | carhart_1997_wml_factor | 23000 | Momentum factor constr | yes。WML 因子完全可由免費日線 OHLCV 建構(基金 leg 不需要);point- |
| (已參照) | johansen-1991 | 22000 | Econometrics & methodo | yes — 只需免費日線 OHLCV(股票/ETF)；statsmodels 已有 Joha |
| (已參照) | fama-french-2015-five-factor | 14000 | Cross-sectional factor | yes(歸因)/ partial(自建因子)— Ken French 已提供 FF5 月頻因 |
| (已參照) | jegadeesh_titman_1993_momentum | 14000 | Cross-sectional moment | yes(已測)。完全可用免費日線;TR-11 已在 47 檔同產業與 503 檔 S&P 兩 |
| (已參照) | kyle1985-lambda | 13000 | Market microstructure  | PARTIAL/model。真 λ 需簽名成交(intraday/tick),我們沒有 →  |
| (已參照) | sloan-1996-accruals | 6500 | Cross-sectional factor | yes — 總應計=(ΔCA−ΔCash)−(ΔCL−ΔSTD−ΔTax)−Dep,科目全在 |
| (已參照) | gw08_oos | 3800 | Return predictability  | yes(已具備)— GW 資料集公開免費,TR-17 已部分採用;協定即本專案 OOS 評估 |
| (已參照) | piotroski_2000_fscore | 3800 | Fundamentals — account | yes (best fit of the batch) — all 9 signals co |
| (已參照) | moskowitz_ooi_pedersen_2012_tsmom | 3600 | Time-series momentum ( | partial。原生棲地=roll-adjusted 連續期貨,免費資料到不了(需 Nasd |
| (已參照) | bernard_thomas_1990_pead | 2800 | PEAD (post-earnings-an | partial — SUE from EDGAR PIT quarterly EPS + d |
| (已參照) | corwin-schultz2012-highlow | 2100 | Market microstructure  | YES。只需免費日線 high/low(OHLC)。Point-in-time OK。成本  |

### C.1 第一波 — 高引用 × 免費資料可重建 × 高洞見(立即可排 TR)

這些可用現有日線 OHLCV + EDGAR 就能重建,是下一輪 TR 的首選。每篇附建議的 fabric TR 切入角度(含它必須先打敗的 Nagel 對照)。

#### newey-west-1987 — Newey & West (1987) · ~30000 引用
- **標題**:A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix
- **機制族 · 原生棲地**:估計/推論方法：異質變異數+自相關一致標準誤（HAC） · 資產=通用時間序列；頻率=任意（金融常用月/日）；廣度=單一序列的均值/斜率檢定；年代=1987 計量核心；用途=把過度樂觀的 OLS t 值降到誠實水準，非產生訊號
- **核心主張**:當殘差有自相關/異質變異數（重疊報酬、波動叢聚），OLS 標準誤被低估、t 值灌水；NW 給出封閉式一致共變異估計。
- **與選股/交易的關聯**:我們唯一顯著 alpha=多 sleeve Carhart α t=2.64（docs/00 §E4）與 TR-06 Fama-MacBeth 斜率 t=2.69 都建立在報酬序列上；月度再平衡+動量重疊使殘差自相關，NW 是判斷這些 t 是否撐得住的第一道誠實檢查。
- **可測性(免費資料)**:yes — 純標準誤重算，只需既有免費日/月報酬序列，零新資料、point-in-time 不受影響；lag 選擇用 Andrews(1991)/4(T/100)^(2/9) 經驗式即可。
- **建議 TR 切入(含 Nagel 對照)**:TR：把所有 headline t（多 sleeve α、TR-06 FM 斜率）以 NW HAC(lag=重疊期)重算，並列 OLS/NW/月度聚類/block-bootstrap 四種 t 對照。Nagel 對照=同一 NW 尺規下，策略 α 的 NW-t 必須顯著高於 (a) 1/σ² 波動管理 book 與 (b) 靜態曝險 book 各自對 VOO 的 α NW-t，且隨機進場 placebo book 的 NW-t≈0；若策略 t 在 NW 校正後跌破門檻或不勝控制，判 α 為推論假象。

#### amihud_2002 — Amihud (2002) · ~11000 引用
- **標題**:Illiquidity and Stock Returns: Cross-Section and Time-Series Effects
- **機制族 · 原生棲地**:Illiquidity as an arbitrage cost and priced risk -> illiquidity premium (risk-measurement + friction-driven alpha; also the operative gate on all other behavioral anomalies) · US equities, daily->monthly aggregation, broad NYSE cross-section, 1963-1997; ILLIQ = mean(|daily return| / daily dollar volume); purpose = price illiquidity and show frictions sustain mispricing
- **核心主張**:Expected returns increase in illiquidity (ILLIQ) cross-sectionally, and expected market return rises with market illiquidity over time; illiquidity is a priced characteristic/risk.
- **與選股/交易的關聯**:Two-for-one: (a) a priced characteristic buildable purely from OHLCV, and (b) the operational limits-to-arbitrage proxy that gates EVERY other anomaly in this subdomain — the friction that lets behavioral mispricing survive. Directly instruments our G-S 'who pays the information cost' framing (illiquidity IS the cost).
- **可測性(免費資料)**:YES (fully). ILLIQ = mean(|daily return|/daily dollar volume) — pure OHLCV, point-in-time trivial. Caveat (honest): the illiquidity premium concentrates in micro/small caps, so our survivorship-large-cap universe is its WEAKEST habitat (mis-seat risk high, like PEAD). Cost ~$0.
- **建議 TR 切入(含 Nagel 對照)**:Compute ILLIQ, decile-sort, net-cost L/S illiquidity premium; AND use ILLIQ as an arbitrage-cost MODERATOR overlaid on the other TRs (does De Bondt-Thaler reversal / CGO live in high-ILLIQ names?). Nagel controls it must beat: (1) static exposure — illiquid basket held constantly (is the 'premium' just small-cap beta?); (2) 1/sigma^2 vol management; (3) placebo ILLIQ. Critical pre-commit (G-S / F2 discipline): once realistic bid-ask + size-dependent impact (costs.py) is charged on the illiquid leg, the tradable L/S likely collapses -> its real, durable value is as a limits-to-arb GATE variable, not a standalone sleeve.

#### debondt_thaler_1985_overreaction — De Bondt & Thaler (1985) · ~9500 引用
- **標題**:Does the Stock Market Overreact?
- **機制族 · 原生棲地**:行為過度反應 → 多年期均值回歸(3-5年 loser 反彈) · 美股 NYSE 普通股、月頻聚合、廣橫斷面(全市場排名)、1926-1982 年代、用途=檢驗弱式效率/過度反應
- **核心主張**:以過去 3-5 年累積報酬排名,極端 loser 組合在後續 3-5 年顯著跑贏極端 winner 組合(反轉),幅度無法用 CAPM beta 解釋。
- **與選股/交易的關聯**:長期反轉是動量-反轉光譜的長端(與 JT 短中期動量正好相反),是選股的 contrarian 主軸;若在其 503 檔宇宙成立,可作為與動量 sleeve 對沖的低相關 sleeve。
- **可測性(免費資料)**:yes(有但書)。日線→月頻、36月形成/36月持有完全可算;point-in-time 用其 503 檔 S&P 宇宙可行。關鍵風險:原始效應集中在小型/低價股,且極度依賴 survivorship 與 delisting 報酬——必須掛 TR-13 Shumway 下市調整,否則 loser 反彈被倖存者偏誤灌水。成本低,無需日內/選擇權。預期:在現代大型股宇宙上效應大幅衰減。
- **建議 TR 切入(含 Nagel 對照)**:在 503 檔 PIT 宇宙建 3年形成期十分位,long past-loser − short past-winner,月頻再平衡,強制 Shumway 下市報酬。Nagel 對照:反轉組合的『loser 溢酬』必須先擊敗 (a) Cederburg 靜態常波動 long-only、(b) 加入 size + 低價(1/price)控制後的殘餘——因為 loser=高 beta/小型/低價的複合;還要贏隨機進場 contrarian。預先承諾:若 loser 溢酬被 size+beta 控制吸收,判定=『長期反轉=小型/低價因子的重新包裝』。

#### daniel_hirshleifer_subrahmanyam_1998 — Daniel, Hirshleifer & Subrahmanyam (1998) · ~7000 引用
- **標題**:Investor Psychology and Security Market Under- and Overreactions
- **機制族 · 原生棲地**:Overconfidence in private signals + biased self-attribution -> short-run continuation (momentum) then long-run reversal; predicts stronger effects where valuation is subjective/ambiguous (behavioral alpha) · US equities, monthly, broad cross-section; theory calibrated to 1990s momentum + long-term reversal; purpose = jointly explain momentum and reversal from one psychology
- **核心主張**:Overconfident investors overreact to private information; self-attribution sustains momentum short-term, then arriving public information forces a long-run correction (reversal). Effects are largest where value is hard to pin down (high information ambiguity).
- **與選股/交易的關聯**:Predicts a specific time-signature (continuation -> reversal) AND a cross-sectional moderator (information ambiguity, proxyable by idio-vol / intangible intensity) — gives a testable 'where should momentum live' map that reframes our dead large-cap momentum as a mis-seated test.
- **可測性(免費資料)**:YES/PARTIAL. Momentum (2-12m) + LT-reversal (36-60m) legs from price. Ambiguity moderator: true proxy = analyst dispersion (I/B/E/S, NOT free); use idio-vol + intangible intensity (R&D/SG&A from EDGAR) as free surrogates -> partial. Point-in-time OK.
- **建議 TR 切入(含 Nagel 對照)**:Build momentum and LT-reversal legs, interact with an information-ambiguity proxy (idio-vol, intangible intensity from EDGAR); DHS predicts stronger continuation-then-reversal in high-ambiguity names. Nagel controls it must beat: (1) static full-exposure baseline of the ambiguity-sorted basket; (2) 1/sigma^2 vol-managed momentum (Moreira-Muir vol-managed momentum is already strong — the DHS-conditioned spread must beat THIS, the hardest control); (3) placebo ambiguity ranking -> interaction vanishes. Subsume test vs plain momentum + FF. PASSED only if ambiguity-conditioned continuation/reversal beats vol-managed momentum and is not plain momentum repackaged.

#### pastor-stambaugh2003-liqrisk — Pastor & Stambaugh (2003) · ~6500 引用
- **標題**:Liquidity Risk and Expected Stock Returns (Journal of Political Economy)
- **機制族 · 原生棲地**:liquidity-risk-factor(市場整體流動性 innovation 作為 priced risk;流動性 beta) · US equities,日線→月頻聚合,市場整體 aggregate 度量,1966-1999,用途=衡量『對市場流動性衝擊的暴露』是否被定價(流動性 beta 橫斷面溢酬)。度量本身就是設計給日線 CRSP,非 tick。
- **核心主張**:每股月度流動性 γ 來自『簽名成交量→次日反轉』回歸;市場整體 γ 的 innovation 是系統風險;對此 innovation 高 beta 的股票有更高期望報酬(年化 ~7.5% 高−低)。
- **與選股/交易的關聯**:選股用『流動性 beta』排序,而非流動性 level;是與 Amihud level 效應正交的第二維度。也給一個市場擇時信號(aggregate liquidity innovation)。**強項:P-S 度量是專為日線資料設計的**,不像多數微結構度量需要 tick。
- **可測性(免費資料)**:YES(核心可重建)。每股 γ:回歸 r_{i,t+1} = θ + φ·r_{i,t} + γ·sign(超額 r_{i,t})·(收盤×量)_{i,t}。全部來自免費日線 OHLCV。Aggregate innovation = 橫斷面平均 γ 的 AR innovation。流動性 beta = 時序回歸。Point-in-time OK(全 trailing)。成本 $0。
- **建議 TR 切入(含 Nagel 對照)**:建每股 γ→aggregate innovation→時序回歸取每股流動性 beta,beta 五分位 L/S。Nagel 對照:(1) 靜態曝險——流動性 beta 是否只是 CAPM market beta 或 size 的偽裝?對 static beta/size-matched 組合中性化;(2) 1/σ² 波動管理——aggregate liquidity 崩塌 = 危機高波動,檢查溢酬不是 1/σ² 波動擇時的重貼標籤(用實現波動當 VIX 代理條件化);(3) 隨機進場 null。並把 aggregate liquidity innovation 當市場擇時信號,直接對打 Nagel 的 1/σ² 波動管理——這正是 Nagel 批評的核心戰場。

#### ang-hodrick-xing-zhang-2006-ivol — Ang, Hodrick, Xing & Zhang (2006) · ~6000 引用
- **標題**:The Cross-Section of Volatility and Expected Returns
- **機制族 · 原生棲地**:α 產生 / 橫斷面特徵排序 — 特質波動(IVOL)異象 · 美股全市場(NYSE/AMEX/NASDAQ 數千檔)× 日頻算 IVOL、月頻再平衡 × 廣橫斷面 × 1963-2000 年代 × 選股排序
- **核心主張**:以 FF3 殘差算出的高特質波動股,未來報酬顯著偏低(月 −1%+),與『波動應被補償』相反 = IVOL puzzle。
- **與選股/交易的關聯**:直接可交易的選股訊號:多低 IVOL、避高 IVOL;是 low-vol 家族中最乾淨的橫斷面版本,可疊在已 PASSED 的 GP 品質 sleeve 上;與我們宇宙相性高(只需量價)。
- **可測性(免費資料)**:yes — 只需免費日線報酬 + Ken French 日頻 FF3 因子(已接 pandas_datareader);IVOL=過去 21-60 日 FF3 迴歸殘差之標準差,全量價、無 PIT 洩漏;零成本。限制:我們宇宙偏大型科技股,IVOL 分散度較窄,可能壓縮 spread。
- **建議 TR 切入(含 Nagel 對照)**:503/610 宇宙月度依 IVOL 分 quintile,多低空高。判定前必打敗 Nagel 三件套,尤其 (1) 1/σ² 波動管理控制——IVOL 極可能只是把低波動股放大權重的複雜包裝(如 TR-17 KMZ 被 1/σ² 支配);(2) 靜態低波動 sleeve(常數曝險);(3) 隨機特徵 placebo。淨成本後仍勝 1/σ² 才算真 IVOL alpha,否則判 PARTIAL = vol-timing 重述。

#### ff88_divyield — Fama & French (1988) · ~5000 引用
- **標題**:Dividend Yields and Expected Stock Returns (JFE 22:3-25)
- **機制族 · 原生棲地**:valuation-ratio 擇時 / 單變量 predictive regression(D/P → 未來報酬) · 資產=美股大盤(NYSE 綜合)/ 頻率=月與 1-4 年疊加 / 廣度=單一市場指數 / 年代=1927-1986 / 用途=股權溢酬長期擇時
- **核心主張**:股利殖利率 D/P 正向預測後續市場超額報酬,且 R² 隨持有期拉長而上升(1年期解釋力遠大於月頻),反映折現率的時變。
- **與選股/交易的關聯**:最乾淨、最少資料需求的市場擇時訊號;若連 D/P 都打不過波動旋鈕,等於替本專案『$0 資料選不出 alpha』的 G-S 論點再添一柱。可延伸到用個股/產業 D/P 做橫斷面選股偏誤檢驗。
- **可測性(免費資料)**:yes — Shiller 免費長歷史月度資料(S&P 價格+股利,1871-)可直接建 D/P;用 trailing-12m 股利即 point-in-time 乾淨;$0。個股層可用 EDGAR 申報股利對齊,但覆蓋較差。
- **建議 TR 切入(含 Nagel 對照)**:SPY/大盤月頻,trailing D/P 做 OOS predictive regression(擴張窗 + Campbell-Thompson 式歷史均值基準),倉位 ∝ 預測超額報酬並截倉[0,2]、淨 5bps。Nagel 對照關卡:必須勝過 Moreira-Muir 1/σ² 波動管理與 Cederburg 靜態 B&H,且對波動管理 alpha 的 t≥2;同時必須套 Stambaugh 偏誤修正的 t 值,否則判『persistent-regressor artifact』。

#### grs-1989 — Gibbons, Ross & Shanken (1989) · ~4200 引用
- **標題**:A Test of the Efficiency of a Given Portfolio (the GRS test)
- **機制族 · 原生棲地**:因子模型檢定：多資產截距聯合檢定（F/Wald，multivariate α=0） · 資產=美股月頻測試組合（characteristic-sorted portfolios）；頻率=月；廣度=N 個測試組合 × K 因子的聯合；年代=1989 因子檢定經典；用途=判定一組因子是否『定價』一組測試資產，非選股
- **核心主張**:給定 K 個因子，N 個測試資產的 α 是否聯合為零有精確 F 分布檢定；單一資產 t 顯著不代表模型被拒，須看聯合統計量（含 α 的共變異結構）。
- **與選股/交易的關聯**:docs/00 §9A 已自爆：long-only sleeve 抬 α-t 是 beta 不是訊號（零訊號籃子照抬到 2.89）。GRS 正是把 5 個 sleeve 的 α 做『正確的多變量聯合檢定』的工具——比目前逐一單 t 誠實一個量級，直接壓力測試那個 t=2.64。
- **可測性(免費資料)**:yes — 只需 sleeve/測試組合月報酬 + Ken French 因子（免費），構建測試組合用免費 OHLCV+EDGAR 排序即可；point-in-time 用申報日對齊排序變數；無需日內/選擇權。
- **建議 TR 切入(含 Nagel 對照)**:TR：把 5 sleeve（或品質/動量分位組合）當測試資產，對 (i) CAPM/FF5+Carhart 與 (ii) 加入 Nagel 因子的擴充集跑 GRS。Nagel 對照直接進因子集：加入 Moreira-Muir 1/σ² 波動管理市場因子與靜態市場因子後，若 GRS 聯合 α 由顯著轉不顯著 → 判『多 sleeve α = 波動擇時/beta 包裝』；唯有在含波動管理+靜態因子的 spanning 下 GRS 仍拒絕 α=0，才升格為真 α。

#### clark-west-2007 — Clark & West (2007) · ~4000 引用
- **標題**:Approximately Normal Tests for Equal Predictive Accuracy in Nested Models
- **機制族 · 原生棲地**:預測評估：巢狀模型 OOS 等預測力檢定（MSPE-adjusted） · 資產=股指/單資產報酬預測；頻率=月(擇時)；廣度=一個預測子 vs 歷史均值基準；年代=2007 預測計量；用途=判定預測子是否 OOS 勝『常數基準』，非直接選股
- **核心主張**:比較巢狀模型（含預測子 vs 只有常數/歷史均值）的 OOS MSPE 時，即使真模型是常數，較大模型也會因估計噪音吃虧；CW 給出調整後、近似常態的檢定，正確判『預測子是否真的 OOS 勝常數』。
- **與選股/交易的關聯**:這是 Nagel『打敗常數/靜態』批評的統計正典化：TR-17(KMZ VoC) 與任何用 EDGAR 估值比預測報酬的擇時，都要先過『OOS 勝歷史均值』這關。CW 正是那個檢定，直接補強 F6/F7 的樣本外誠實層。
- **可測性(免費資料)**:yes — 只需長指數歷史(SPY/QQQ)+免費預測子(估值比/動量/波動)，擴張視窗 OOS 即可；point-in-time 用 EDGAR 申報日對齊；無需日內/選擇權。
- **建議 TR 切入(含 Nagel 對照)**:TR：對每個候選預測子跑 CW 檢定 vs 歷史均值基準（=靜態/常數），報 OOS R² 與 CW-t。Nagel 對照本身就是虛無假設：常數基準=靜態曝險、1/σ² 波動管理視為第二基準；預測子必須 CW-顯著勝『常數』且勝『1/σ² 波動時序』兩者，才算真預測力。把此檢定接進 TR-17，直接裁決 VoC 曲線是否只是波動擇時。

#### shanken-1992 — Shanken (1992) · ~2900 引用
- **標題**:On the Estimation of Beta-Pricing Models (errors-in-variables correction)
- **機制族 · 原生棲地**:橫斷面迴歸推論：估計誤差變數(EIV)校正的 FM 標準誤 · 資產=美股月頻橫斷面；頻率=月(兩階段)；廣度=N 資產 × 風險價格斜率；年代=1992 定價計量；用途=修正 FM 斜率被低估的標準誤，非產生訊號
- **核心主張**:Fama-MacBeth 第二階段用的是估計出的 β（含測量誤差），未校正的 FM 標準誤系統性低估、風險價格 t 灌水；Shanken 給出 (1+市場 SR²) 膨脹因子的封閉修正。
- **與選股/交易的關聯**:TR-06 的 A1 用 Fama-MacBeth 得市場風險價格 +1.899%/mo, t=2.69——這個 t 未做 Shanken 校正，可能高估。這是直接精修一個既有 TR 判定、且是本子領域點名的 Fama-MacBeth 家族核心缺口。
- **可測性(免費資料)**:yes — 純標準誤重算，用 TR-06 既有月報酬+β 估計即可，零新資料；point-in-time 不受影響。
- **建議 TR 切入(含 Nagel 對照)**:TR-06b：對 TR-06 的 FM 斜率套 Shanken EIV 膨脹，報告校正前後 t（預期 t 由 2.69 下修）。Nagel 對照=把 FM 估到的風險價格拿去建『按估計 β 排序』的多空 book，須淨勝 (a) 隨機 β 指派 placebo 與 (b) 靜態 buy-and-hold；若 Shanken 校正後斜率 t 跌破 2.0 或 book 不勝控制，判市場-β 溢酬在本樣本為弱證據。

#### bali-cakici-whitelaw-2011-max — Bali, Cakici & Whitelaw (2011) · ~2900 引用
- **標題**:Maxing Out: Stocks as Lotteries and the Cross-Section of Expected Returns
- **機制族 · 原生棲地**:Cross-sectional sort on extreme upside: MAX = average of the k highest daily returns over the prior month · US equity cross-section / monthly rebalance / broad CRSP / 1962-2005 / stock selection
- **核心主張**:Stocks with the highest max daily returns last month (lottery-like) earn LOW subsequent returns; MAX subsumes much of the idio-vol puzzle — investors overpay for right-tail skew.
- **與選股/交易的關聯**:Trivially computable stock screen (max daily return) usable in selection today; and a direct explanation-competitor to AHXZ idio-vol — a joint test resolves which vol/skew mechanism, if any, survives in our universe.
- **可測性(免費資料)**:YES, fully. MAX(k) = mean of the k largest daily returns in the trailing month, straight from free daily OHLCV. Point-in-time trivial. No options/intraday.
- **建議 TR 切入(含 Nagel 對照)**:Monthly decile sort on MAX(5) across the 610 universe; long low-MAX / short high-MAX; exSharpe + FF/Carhart alpha, 2x cost stress (F2), phase-averaged (F12). Nagel controls it MUST beat: (a) zero-signal random-decile basket (F6), (b) static EW-47 / B&H (F3); as a pure cross-sectional bet the 1/sigma^2 timing control is secondary, the random-entry/zero-signal control is primary. Double-sort MAX x idio-vol to see if either adds over the other or both collapse. Prior: given FAILED low-vol and dead XS-momentum, expect a small/insignificant net-of-cost MAX premium, but it is cheap and high-insight to confirm.

#### stambaugh99_bias — Stambaugh (1999) · ~2800 引用
- **標題**:Predictive Regressions (JFE 54:375-421)
- **機制族 · 原生棲地**:predictive-regression 計量 / 持久回歸子的有限樣本偏誤與貝式修正 · 資產=美股大盤 / 頻率=月 / 廣度=單預測子(D/P 等 AR(1) 高持久序列)/ 年代=方法論(套 1927-1996)/ 用途=修正擇時係數的統計顯著性
- **核心主張**:當回歸子高度持久且其創新與報酬創新相關時,OLS 斜率有系統性向上偏誤、標準 t 檢定嚴重高估顯著性;給出偏誤方向、量級與貝式後驗修正。
- **與選股/交易的關聯**:這是 fabric『誠實層』的直接彈藥:本專案所有用 D/P、CAPE、利差擇時的 TR 都踩在 Stambaugh 偏誤上;把它做成一個可複用的統計閘,能一次性下修多個擇時訊號的顯著性,呼應 3 次對抗 review 抓 in-sample artifact 的傳統。
- **可測性(免費資料)**:yes — 純方法論,只需既有報酬+預測子序列;實作 Stambaugh/Kendall 偏誤修正與 bootstrap;無新資料需求;$0。
- **建議 TR 切入(含 Nagel 對照)**:不是策略而是閘:對 TR 的每個持久估值比擇時訊號,回報 OLS-t 與偏誤修正-t 的落差,及 bootstrap p 值。Nagel 對照關卡的補強件——先用它證明訊號係數在修偏後仍顯著,再進波動管理/靜態曝險對照;若修偏後 t 崩到 <2,則該擇時訊號在打 Nagel 對照前就已出局。

#### stambaugh-1999 — Stambaugh (1999) · ~2800 引用
- **標題**:Predictive Regressions
- **機制族 · 原生棲地**:預測回歸推論：持續性回歸子造成的 Stambaugh 偏誤校正 · 資產=股指/個股報酬 on 估值比；頻率=月/季；廣度=單一持續性預測子；年代=1999 預測計量；用途=修正估值比預測報酬的係數偏誤，非產生訊號
- **核心主張**:當回歸子高度持續（E/P、B/M、D/P）且其創新與報酬創新相關時，OLS 預測係數在小樣本有系統性偏誤、t 被高估；須用偏誤校正/bootstrap 推論。
- **與選股/交易的關聯**:我們的 EDGAR 基本面（估值比、品質比）天生高持續性；任何『估值比預測未來報酬』的選股/擇時回歸都吃這個偏誤。這是把免費 EDGAR 因子做誠實的必修校正，且與唯一穩健因子=基本面品質 ICIR+0.30 的推論直接相關。
- **可測性(免費資料)**:yes — 用 EDGAR 估值/品質比(申報日對齊, point-in-time)+長報酬歷史，bootstrap 校正即可；無需日內/選擇權；成本=零。
- **建議 TR 切入(含 Nagel 對照)**:TR：對『估值比/品質比 → 未來報酬』預測回歸套 Stambaugh 偏誤校正+bootstrap 分布，報校正前後係數與 t。Nagel 對照=校正後的預測子建的 tilt book 須淨勝靜態基準與 1/σ² 波動管理，且用 Clark-West 過 OOS-勝常數關；若偏誤校正後 t 塌陷，判該基本面預測子為小樣本假象。

#### grinblatt_han_2005 — Grinblatt & Han (2005) · ~2600 引用
- **標題**:Prospect Theory, Mental Accounting, and Momentum
- **機制族 · 原生棲地**:Disposition effect (reluctance to realize gains/losses) -> unrealized-gain overhang relative to a reference price predicts returns; behavioral alpha that subsumes momentum · US equities, weekly/monthly, broad cross-section, 1962-1996; signal = turnover-weighted reference price -> CGO = (P - RefP)/P; purpose = explain momentum via the disposition effect
- **核心主張**:Stocks with large unrealized capital GAINS (price above the turnover-weighted reference price) earn higher subsequent returns than those with large unrealized losses; when CGO is added as a regressor, conventional past-return momentum disappears.
- **與選股/交易的關聯**:THE free-data-testable manifestation of the disposition effect: Odean (1998) and Shefrin-Statman (1985) need individual brokerage records we can never get, whereas CGO is their market-level proxy, fully reconstructable from price + volume + shares. A genuinely novel-to-us signal that directly speaks to our dead-momentum result.
- **可測性(免費資料)**:YES — the most cleanly buildable in this set. CGO = f(historical prices, weekly turnover). Turnover needs shares outstanding (EDGAR, PIT) or a volume proxy. All from daily OHLCV + EDGAR shares. Point-in-time clean. Moderate turnover -> costs matter but tractable. Cost ~$0.
- **建議 TR 切入(含 Nagel 對照)**:Construct a ~5yr turnover-weighted reference price, compute CGO, decile-sort broad universe, net-of-cost L/S; and run the horse-race regression CGO vs past-return momentum on our universe. Nagel controls it must beat: (1) static EW exposure to the high-CGO basket (Cederburg); (2) 1/sigma^2 vol-managed momentum as the benchmark it must ADD value over — is CGO a different trade or the same edge?; (3) placebo reference price (random weights) -> signal collapses. Key PASSED bar: net-cost CGO L/S beats BOTH vol-managed momentum and static exposure, AND the 'CGO subsumes momentum' regression replicates on our data.

#### mclean_pontiff_2016_academic_research_destroys — McLean & Pontiff (2016) · ~2600 引用
- **標題**:Does Academic Research Destroy Stock Return Predictability? (Journal of Finance)
- **機制族 · 原生棲地**:anomaly-decay / out-of-sample & post-publication attenuation · US equities / monthly / 97 published cross-sectional predictors / 1926-2013 / meta-study — measures how much predictability shrinks post-sample and post-publication
- **核心主張**:Predictor returns fall ~26% out-of-sample and ~58% post-publication; decay is larger for anomalies that are more arbitrageable (higher liquidity, more capital), consistent with arbitrageurs trading on the published signal.
- **與選股/交易的關聯**:Directly formalizes the corpus's most-repeated empirical finding ('post-2019 effect decay', G-S $0-info→$0-alpha). Gives a quantitative yardstick to judge whether OUR surviving factor (GP ICIR+0.30) is pre- or post-publication, and predicts which of our zoo entries should already be dead.
- **可測性(免費資料)**:yes (methodologically) — we already have a factor library + trial registry; needs each factor's publication date (public) and our own in-sample vs post-pub OOS returns. No new data. Caveat: our sample is short and large-cap, so we can only test the decay slope on the handful of factors we can rebuild, not their full 97. Cost $0.
- **建議 TR 切入(含 Nagel 對照)**:For each rebuildable factor (GP, accruals, momentum, value, F-score) split return at the original publication date and measure in-sample vs post-pub OOS attenuation; compare to MP's ~58% benchmark. Nagel control it must beat: STATIC EXPOSURE — the honest post-pub baseline is a buy-and-hold of the factor with no timing; the test is whether any residual post-pub alpha survives net of static exposure and is NOT just a 1/sigma^2 (Moreira-Muir) vol-managed repackaging. Pre-commit: a factor whose post-pub alpha is fully explained by static exposure + vol timing is reclassified as decayed.

#### ct08_restrictions — Campbell & Thompson (2008) · ~2400 引用
- **標題**:Predicting Excess Stock Returns Out of Sample: Can Anything Beat the Historical Average? (RFS 21:1509-1531)
- **機制族 · 原生棲地**:OOS 預測評估 / 經濟約束(sign & 理論係數限制)提升 OOS R² · 資產=美股大盤 / 頻率=月與年 / 廣度=單指數多預測子(D/P、E/P、利率、通膨等)/ 年代=1927-2005 / 用途=股權溢酬 OOS 擇時
- **核心主張**:對 Goyal-Welch 的悲觀結論回擊:只要施加簡單經濟約束(禁止負股權溢酬、係數符號合理),樣本外 R² 可轉正且小幅擇時可帶來實質效用增益;微小 OOS R²(~0.5%/月)已具經濟價值。
- **與選股/交易的關聯**:直接界定『免費宏觀/估值訊號能否擇時』的樂觀上界,是 Goyal-Welch 的辯方;本專案已有 GW 15 預測子(TR-17),此文是最省成本的加值層——測『加約束後是否真的翻案』。
- **可測性(免費資料)**:yes — 沿用 TR-17 已有的 GW 預測子(公開資料)+ Shiller/FRED 免費序列;僅新增 sign/理論值截斷邏輯與 OOS R²、效用增益計算;point-in-time 可行;$0。
- **建議 TR 切入(含 Nagel 對照)**:在既有 GW 預測子上跑約束版 OOS 預測(截負、係數封頂),用 Campbell-Thompson 的 OOS R² 與 CER 效用增益量度;構造 1/σ² 目標倉位。Nagel 對照關卡:效用增益必須來自『訊號』而非隱含的波動縮放——與 Moreira-Muir 波動管理正交化後仍須留下正 alpha(t≥2),否則判 OOS 增益=波動擇時包裝。

#### george_hwang_2004_52wk — George & Hwang (2004) · ~2200 引用
- **標題**:The 52-Week High and Momentum Investing
- **機制族 · 原生棲地**:錨定/對參考點的 underreaction(近 52週高 → 續漲) · 美股、月頻訊號(源自日線 252日 rolling max)、廣橫斷面、1963-2001 年代、用途=動量的行為錨定解釋
- **核心主張**:股價/52週高點的比值(接近高點程度)預測後續報酬,且此訊號『支配』傳統 JT 個股動量與 Moskowitz-Grinblatt 產業動量——動量本質是對 52週高錨點的 underreaction。
- **與選股/交易的關聯**:52週高是最乾淨、最好算的動量訊號(只需日線 rolling max),且宣稱『打敗 JT 動量本身』——正好可在他們已測死 JT 動量的宇宙上,檢驗是否有一個更強的動量代理漏測了。高洞見×高可用性。
- **可測性(免費資料)**:yes。訊號=每檔 close / trailing-252日最高價,純免費日線 OHLCV 即可;point-in-time 無前視。成本低,無需任何付費資料。這是本批最無資料摩擦的一篇。
- **建議 TR 切入(含 Nagel 對照)**:建 52wk-high proximity 分位,long 近高 − short 遠高,月頻;直接對照組=既有 TR-11 的 JT 動量(論文核心宣稱:52wk 打敗 JT)。Nagel 三件套:必須擊敗 (a) Moreira-Muir 1/σ² 波動管理市場、(b) Cederburg 靜態曝險、(c) 隨機進場。預先承諾:若 52wk 溢酬僅在 JT 動量已死的宇宙裡也是 ICIR≈0,則錨定假說在此棲地不成立;若它獨活而 JT 死,才算真正新增訊號。

### C.2 第二波 — 可測但需額外建構 / 部分資料

需要多做一點資料工程(建產業分類、指數長歷史、公開附錄資料集)或只能部分重建。

#### bollerslev-1986-garch — Bollerslev (1986); Engle (1982) · ~45000 引用
- **標題**:Generalized Autoregressive Conditional Heteroskedasticity (GARCH); ARCH
- **機制族 · 原生棲地**:Time-series conditional-variance recursion (volatility clustering, mean reversion); EGARCH adds leverage asymmetry · Any liquid return series (equity index, single stock, FX) / daily or lower / single-series / 1980s- / volatility forecasting & risk sizing
- **核心主張**:Conditional variance follows an ARMA-like recursion in past squared shocks and past variances; captures volatility clustering and yields superior short-horizon vol forecasts vs constant variance (EGARCH adds the negative-return leverage effect).
- **與選股/交易的關聯**:The conditional-vol forecast is the engine behind vol-targeting, VaR (TR-04) and position sizing across the whole book; testing whether GARCH sizing actually beats naive 1/sigma^2 is directly decision-relevant and un-done.
- **可測性(免費資料)**:YES, fully. GARCH(1,1)/EGARCH fit on free daily index & stock returns; no options/intraday. Point-in-time via expanding-window refit (register refit frequency under F5 design params).
- **建議 TR 切入(含 Nagel 對照)**:Use GARCH(1,1) conditional vol as the scaler for a vol-targeted market/book exposure; grade forecast accuracy (QLIKE/MZ) AND the risk-adjusted outcome. Nagel controls it MUST beat: (a) 1/sigma^2 using trailing realized vol (Moreira-Muir) — the core question is whether conditional variance beats naive inverse realized variance, (b) static exposure (F3), (c) random entry. Route the EGARCH leverage term into a downside-risk tilt. Prior (consistent with TR-04/TR-17): GARCH wins on vol-forecast accuracy (measurement PASS) but the sizing outcome ~ 1/sigma^2 (economic value PARTIAL) — fancy vol machinery keeps collapsing to inverse-variance.

#### hansen-gmm-1982 — Hansen (1982) · ~27000 引用
- **標題**:Large Sample Properties of Generalized Method of Moments Estimators
- **機制族 · 原生棲地**:估計/檢定：GMM 隨機折現因子(SDF)估計 + 過度識別 J 檢定 · 資產=通用（金融常用月頻因子+測試組合）；頻率=月；廣度=矩條件數 > 參數數的過度識別；年代=1982 計量核心；用途=估定價核並檢定其是否定價一組資產，非選股
- **核心主張**:用矩條件 E[m·R]=1 可在不假設分布下估 SDF 參數；過度識別的 J 統計量檢定『因子是否共同定價測試資產』，是 GRS 在 SDF 語言下、對非常態/異質更穩健的推廣。
- **與選股/交易的關聯**:把因子模型檢定從 β-定價(GRS)升到 SDF/GMM 語言，可在不靠常態假設下檢定我們的因子/sleeve 是否定價截面，並自然容納條件矩(波動管理因子)。是 factor-model tests 與 GMM 兩個點名支柱的交集正典。
- **可測性(免費資料)**:partial→yes — 檢定本身只需免費因子+測試組合月報酬，statsmodels/linearmodels 或手刻 GMM 皆可；point-in-time 用 EDGAR 對齊。標 partial 僅因實作與最適加權矩陣估計比 GRS 重、樣本短時 J 檢定小樣本偏誤需 bootstrap；無需日內/選擇權。
- **建議 TR 切入(含 Nagel 對照)**:TR：估線性 SDF m=1−b'f，對 5 sleeve/分位組合跑 GMM J 檢定，對照 GRS。Nagel 對照直接進矩條件：SDF 內含 Moreira-Muir 1/σ² 波動管理因子與靜態市場因子後，若 J 檢定無法拒絕(模型定價得了 sleeve) → 判 sleeve α = 波動管理/beta 可解釋；唯有含這些控制仍被 J 拒絕的殘差 α 才升格。

#### diebold-mariano-1995 — Diebold & Mariano (1995) · ~15000 引用
- **標題**:Comparing Predictive Accuracy
- **機制族 · 原生棲地**:預測評估：兩模型 OOS 損失差之等預測力檢定(可選損失函數) · 資產=通用(報酬/波動預測)；頻率=任意；廣度=兩競爭預測模型；年代=1995 預測計量；用途=在指定損失下判兩預測何者較準，非選股
- **核心主張**:給定任意損失函數，兩模型的 OOS 損失差序列做 HAC-穩健的均值為零檢定，即可判定預測力是否顯著不同——不需假設模型正確或巢狀。
- **與選股/交易的關聯**:當我們要說『模型 X 比波動管理/常數基準預測得更好』時，這是那句話的正式檢定。對波動預測(GARCH vs 已實現波動代理)與報酬擇時的模型選擇提供誠實裁決，補齊 forecast-evaluation 支柱的通用版(Clark-West 管巢狀，DM 管一般)。
- **可測性(免費資料)**:yes — 只需既有 OOS 預測序列(波動/報酬)+免費報酬；DM 統計量易實作(NW 標準誤)；point-in-time 不受影響；無需日內/選擇權。
- **建議 TR 切入(含 Nagel 對照)**:TR：以 DM 檢定比較候選預測器 vs Nagel 基準的 OOS 損失。Nagel 對照即比較對象：候選波動/報酬預測必須 DM-顯著勝 (a) 1/σ² 波動管理隱含預測 與 (b) 常數/歷史均值(靜態)；巢狀情形改用 Clark-West。把 DM 接進 TR-04(VaR/波動)與 TR-17(擇時)，讓『我們的模型更準』永遠附一個 DM p 值而非目測。

#### petersen-2009 — Petersen (2009) · ~12000 引用
- **標題**:Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches
- **機制族 · 原生棲地**:面板推論：雙向聚類(firm×time)標準誤與 FM/聚類/NW 對照 · 資產=股票 panel(firm×month)；頻率=月；廣度=大截面×時間；年代=2009 實證金融方法；用途=在有 firm 效應與 time 效應時給正確標準誤，非選股
- **核心主張**:金融 panel 同時有 firm 效應(截面相關)與 time 效應(序列相關)；只單向處理(或裸 OLS)會嚴重低估標準誤；須雙向聚類，且 FM 只吸收 time 效應、對 firm 效應無能。
- **與選股/交易的關聯**:我們 F7 用『月度 CR1 聚類 t』但只單向(time)；Petersen 是判斷是否還需 firm 向聚類、以及 FM/聚類/NW 三法差多少的權威。直接校準 F7 規則與所有因子 IC / sleeve α 的 panel t。
- **可測性(免費資料)**:yes — 純標準誤重算，用既有 47/610 股票月報酬 panel 即可；零新資料；point-in-time 不受影響。
- **建議 TR 切入(含 Nagel 對照)**:TR：對因子 IC 與 sleeve α 面板同時報 OLS / FM / 單向聚類 / 雙向聚類(firm×time) / NW 五種 t，量化 F7 現行單向聚類漏掉多少。Nagel 對照=在最保守(雙向聚類)標準誤下，α 仍須顯著勝 1/σ² 波動管理與靜態曝險控制、且隨機進場 placebo 不顯著；若雙向聚類把 t 打回不顯著，回饋 F7 v3 修訂。

#### shleifer_vishny_1997 — Shleifer & Vishny (1997) · ~9000 引用
- **標題**:The Limits of Arbitrage
- **機制族 · 原生棲地**:Agency + capital constraints on professional arbitrageurs -> arbitrage is limited exactly when opportunities are largest -> mispricing persists (economic foundation, not a tradable signal) · Conceptual/theory; motivated by professional (delegated) arbitrage — hedge funds, any asset/frequency; purpose = explain why mispricing survives despite smart money
- **核心主張**:Real arbitrage is done by a few specialists deploying other people's capital; when mispricing widens they face redemptions precisely when the opportunity is best, so they cannot fully correct prices — arbitrage is weakest where fundamental/idiosyncratic risk and horizon mismatch are high.
- **與選股/交易的關聯**:The theoretical spine of this whole subdomain and a direct sibling of our G-S '$0 info cost -> $0 alpha' foundation. Reframes every behavioral anomaly as surviving only where arbitrage is costly, and supplies a cross-cutting moderator (idio-vol, illiquidity, horizon) to overlay on the other TRs.
- **可測性(免費資料)**:PARTIAL (indirect). Not a signal itself. Test its central prediction: anomaly magnitude increases in arbitrage-cost proxies (idiosyncratic vol per Pontiff, Amihud illiquidity, size) — all buildable from OHLCV + EDGAR, PIT OK. Cannot test the capital-flow/agency channel (needs fund-flow data -> no).
- **建議 TR 切入(含 Nagel 對照)**:Meta-TR / conditioning study (not a standalone strategy): interact each buildable behavioral anomaly (De Bondt-Thaler reversal, CGO, sentiment-conditioned spread) with an arbitrage-cost composite (idio-vol + ILLIQ + size). Prediction: spreads monotonically larger in the high-arb-cost quintile. Nagel controls it must beat: (1) static exposure to the high-arb-cost basket alone — is the 'stronger anomaly' just the high-idio-vol / small-cap risk premium held long? (Cederburg); (2) 1/sigma^2 vol management (high-idio-vol names dominate — is it vol-timing?); (3) placebo arb-cost ranking. Honest verdict frame: likely confirms our only surviving alpha lives where costs eat it (G-S restated) -> value is explanatory, not tradable.

#### lakonishok-shleifer-vishny-1994-contrarian — Lakonishok, Shleifer & Vishny (1994) · ~8000 引用
- **標題**:Contrarian Investment, Extrapolation, and Risk
- **機制族 · 原生棲地**:α 產生 / 基本面特徵排序 — 價值(glamour vs value 外推)異象 · 美股全市場 × 年頻 × 廣橫斷面 × 1963-1990 × 價值選股 + 行為解釋
- **核心主張**:低 B/M、低 C/P、高過去成長的 glamour 股未來低報酬;價值溢酬源於投資者對成長過度外推,非承擔更高風險(下行期價值不更差)。
- **與選股/交易的關聯**:給價值一個可證偽的行為機制與多維定義(B/M、C/P、E/P、過去銷售成長四維),比單一 B/M 更細;可診斷『價值失落十年』是溢酬消失,還是 glamour 端擁擠擴大。
- **可測性(免費資料)**:yes — B/M、C/P(現金流/價)、E/P 由 EDGAR + 價格,過去銷售成長由 EDGAR 營收,全 PIT;年頻;零成本。docs/10 已見 value(earnings yield/BM)2015-24 失效,LSV 多維版可切開 glamour vs value 兩端。
- **建議 TR 切入(含 Nagel 對照)**:雙分類:價值(高 B/M)× 低過去成長 = 深度價值 vs glamour;比較兩端 forward return 與下行 beta(檢驗『價值非更高風險』)。Nagel 對照:靜態價值 sleeve 常數曝險(F6)+ 隨機特徵 placebo;LSV 核心宣稱『下行期價值不更差』本身即對『價值=風險補償』的反面控制,天然契合 F6 哲學。F7 子期必做(價值失落十年 regime)。

#### baker_wurgler_2006 — Baker & Wurgler (2006) · ~8000 引用
- **標題**:Investor Sentiment and the Cross-Section of Stock Returns
- **機制族 · 原生棲地**:Market-wide sentiment + limits-to-arbitrage -> conditional mispricing of hard-to-value / hard-to-arbitrage stocks (conditioning variable, not a standalone alpha) · US equities, monthly, broad cross-section, 1962-2001; top-down 6-proxy PCA sentiment index interacted with firm characteristics; purpose = identify which stocks are sentiment-sensitive and when
- **核心主張**:Following high sentiment, speculative / hard-to-value stocks (small, young, high-vol, unprofitable, non-dividend, extreme growth or distress) earn LOW subsequent returns; low-sentiment periods reverse the pattern.
- **與選股/交易的關聯**:A regime/conditioning variable that could revive characteristics we found flat unconditionally (size, profitability); ties directly to our surviving GP-quality sleeve and to Markov/regime overlays — turns a dead unconditional sort into a conditional one.
- **可測性(免費資料)**:PARTIAL/YES. Characteristics (size, age, vol, profitability, dividend-payer, B/M) buildable from EDGAR + price. Sentiment index: Wurgler publishes the monthly BW index free (NYU site, ~through 2018) BUT it is FULL-SAMPLE PCA -> look-ahead baked into construction; a real point-in-time rebuild is hard (IPO first-day returns, equity share of issuance need extra data). Honest: descriptive test with published index = yes; clean PIT = partial.
- **建議 TR 切入(含 Nagel 對照)**:Build a sentiment-sensitivity composite (size/age/vol/profitability/dividend), form L/S, and condition returns on lagged BW sentiment tercile. Nagel controls it must beat: (1) static unconditional exposure to the same characteristic — does sentiment-conditioning add over always-on holding? (Cederburg static); (2) 1/sigma^2 vol management — high-sentiment periods ~ high-vol periods, so prove the conditioning is not just inverse-vol timing (the SHARPEST control here); (3) placebo: random dates as fake sentiment states -> effect vanishes. Plus PIT honesty: re-run with a lag-only rebuilt proxy to see if look-ahead drove it. PASSED only if the sentiment-conditioned spread beats the vol-managed control and survives the PIT rebuild.

#### amihud-mendelson1986-spread — Amihud & Mendelson (1986) · ~7000 引用
- **標題**:Asset Pricing and the Bid-Ask Spread (Journal of Financial Economics)
- **機制族 · 原生棲地**:spread-premium / clientele(價差 → 要求報酬,凹型 holding-period 攤銷) · US equities(NYSE/AMEX),月頻報酬 × 期初報價價差,1961-1980,用途=證明報價價差正向定價、且長持有期投資人自我選擇高價差資產(clientele)。原生需『報價』價差。
- **核心主張**:期望毛報酬隨相對買賣價差遞增且呈凹型(spread-return relation);高價差資產被長 holding-period 的 clientele 持有,攤銷交易成本。
- **與選股/交易的關聯**:選股用價差當 required-return 代理;凹型與 clientele 預測給『價差因子在長持有期組合更該被計入』的洞見。是 Amihud 2002 的理論母體。
- **可測性(免費資料)**:PARTIAL。原文用『報價』價差,我們沒有(免費日線無 bid/ask)。只能用估計價差(Roll / Corwin-Schultz / zero-return 比例)替代 → 測的是『估計價差-報酬關係』,非原始報價版本。Point-in-time OK。clientele/攤銷的凹型預測較難乾淨檢驗。
- **建議 TR 切入(含 Nagel 對照)**:用估計價差(Corwin-Schultz 或 Roll)排序測 spread-return 關係與凹型。Nagel 對照:(1) 靜態曝險——價差溢酬扣掉靜態 size/Amihud level 傾斜後是否還在(高度共線,預期大半被吸收);(2) 隨機進場 null;(3) 凹型測試須對照『線性 size 傾斜』這個更簡單的形狀。因與 Amihud 2002 高度重疊,定位為 Amihud TR 的 robustness sleeve(不同估計器是否給同結論),而非獨立旗艦。

#### hong_stein_1999 — Hong & Stein (1999) · ~6500 引用
- **標題**:A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets
- **機制族 · 原生棲地**:Heterogeneous agents (newswatchers + momentum traders) + slow information diffusion -> initial underreaction (momentum) then momentum-driven overreaction (behavioral alpha with a cross-sectional moderator) · US equities, monthly, broad cross-section; theory predicts momentum stronger in slow-diffusion stocks (small, low analyst coverage); purpose = explain the cross-sectional variation of momentum
- **核心主張**:Information diffuses gradually, so prices underreact -> momentum; momentum is stronger where information diffuses slowest (small, low-coverage firms); a later overreaction by momentum traders eventually reverses.
- **與選股/交易的關聯**:Provides a testable cross-sectional MODERATOR for momentum (coverage/size) that directly explains WHY our large-cap momentum died — mega-caps are the fast-diffusion, weakest habitat, consistent with our null. Predicts momentum should revive in low-coverage names.
- **可測性(免費資料)**:PARTIAL. Momentum from price. Diffusion-speed moderator: true proxy = analyst coverage (I/B/E/S, NOT free); use size + turnover + firm age (EDGAR/price) as free surrogates -> partial. Point-in-time OK.
- **建議 TR 切入(含 Nagel 對照)**:Momentum L/S conditioned on a diffusion-speed proxy (size/turnover/age); Hong-Stein predicts monotonically stronger momentum in the slow-diffusion quintile. Nagel controls it must beat: (1) 1/sigma^2 vol-managed momentum (Moreira-Muir) — the coverage-conditioned momentum must beat vol-managed momentum, else it is the same edge (hardest control); (2) static exposure to the small/low-turnover basket (Cederburg); (3) placebo coverage proxy. Honesty note: our survivorship-large-cap universe IS Hong-Stein's weakest habitat, so a null here does NOT convict the mechanism (mis-seat) — reopening requires a small-cap PIT universe (an information cost).

#### roll1984-effspread — Roll (1984) · ~4800 引用
- **標題**:A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market (Journal of Finance)
- **機制族 · 原生棲地**:effective-spread-estimator(價格變動一階自協方差 → 隱含有效價差) · US equities/期貨,日線收盤序列,1963-1982,用途=在無報價資料時,僅用成交價的負自協方差反推有效買賣價差。天生為日線設計(不需報價/tick)。
- **核心主張**:有效價差 = 2·√(−Cov(Δp_t, Δp_{t-1})),當一階自協方差為負時成立;價差造成的 bid-ask bounce 使相鄰價格變動負相關。
- **與選股/交易的關聯**:給我們一個『從免費日線反推交易成本』的估計器,可直接校準 TR-12 phase-cost 模型(目前用假設值),也可當流動性因子。是本子領域『effective-spread estimators』的定義性論文。
- **可測性(免費資料)**:YES,有 caveat。只需免費日線收盤變動。Point-in-time OK。已知限制:實務上約半數估計自協方差為正(估計無定義)——日線上噪音大,intraday 較穩(我們沒 tick)。故 partial-to-yes:當作『可建但需與 Corwin-Schultz/Amihud 交叉驗證』的成本估計器。
- **建議 TR 切入(含 Nagel 對照)**:用 Roll 估計器算每股有效價差,雙用途:(a) 餵入成本模型(F2/TR-12)——測『Roll vs Corwin-Schultz vs Amihud 哪個最能預測我們回測裡的實現滑價』;(b) 當價差因子做 L/S 排序。Nagel 對照:(1) 靜態曝險——價差因子是否只是 size 靜態傾斜?size 中性化後還剩多少;(2) 隨機進場 null 產生價差-報酬 spread 的 null 分布;(3) 對成本用途,對照組=『常數成本假設』(這本身就是 Nagel 靜態控制的成本版:動態價差估計是否勝過一個常數?)。PASS=Roll 成本估計在樣本外顯著優於常數成本。

#### acharya-pedersen2005-lcapm — Acharya & Pedersen (2005) · ~4500 引用
- **標題**:Asset Pricing with Liquidity Risk (Journal of Financial Economics)
- **機制族 · 原生棲地**:liquidity-risk-factor(LCAPM:level + 三個 covariance 流動性 beta) · US equities,日線(建於 Amihud 正規化 illiquidity),寬橫斷面,1962-1999,用途=把流動性 level 溢酬與三種系統流動性風險(流動性共動、報酬-流動性 cross-covariance、flight-to-liquidity)拆開定價。
- **核心主張**:期望報酬 = 無風險 + market beta + 淨流動性成本(level) + 3 個流動性 covariance beta(β2:流動性共動;β3:報酬對市場流動性;β4:流動性對市場報酬)。
- **與選股/交易的關聯**:把 Amihud 的 level 效應升級成有結構的風險分解;選股時可分辨『貴是因為 level 貴』還是『因為 flight-to-liquidity 曝險』。是 Amihud 2002 與 P-S 2003 的統一框架。
- **可測性(免費資料)**:YES(可重建,較費工)。全部 4 個 beta 都由 Amihud 正規化 illiquidity innovations + 報酬構成,皆源自免費日線;market cap 正規化常數需 shares outstanding(EDGAR)。Point-in-time OK。難點=innovation 建模(AR2)與短樣本 n_eff,非資料缺口。
- **建議 TR 切入(含 Nagel 對照)**:在既有 Amihud ILLIQ 之上建 4 個 LCAPM beta,測『covariance betas 是否在 level(Amihud)與 size 之上還有增益』。Nagel 對照:(1) 靜態曝險——先扣掉永久 illiquidity level tilt(=Amihud TR 的結果)與 static CAPM beta,covariance betas 還剩多少?(2) 1/σ² 波動管理——flight-to-liquidity(β4)在高波動期爆發,須證明它不是 1/σ² 的複雜包裝;(3) 隨機組合 null。PASS 條件=4-beta 分解在 Amihud level + size + static beta 之上仍有顯著 t 且淨成本存活。預期:多半被 level + size 吸收(與本框架『複雜度多被最簡控制解釋』的先驗一致)。

#### cochrane11_discount — Cochrane (2011) · ~4200 引用
- **標題**:Presidential Address: Discount Rates (JF 66:1047-1108)
- **機制族 · 原生棲地**:present-value 恆等式 / 折現率變動=D/P 幾乎全部預測報酬(而非股利成長)——『沒吠的狗』論證 · 資產=股/債/信用/外匯全類(綜述)/ 頻率=月至多年 / 廣度=跨資產可預測性統整 / 年代=1930s-2010 / 用途=框定『可預測性=折現率時變』的理論觀點
- **核心主張**:由 Campbell-Shiller 恆等式,D/P 的變動幾乎必然由『後續報酬可預測』吸收,因為股利成長本身不可預測(狗沒吠);長視窗回歸放大同一訊號,可預測性是折現率變動的普遍現象而非異常。
- **與選股/交易的關聯**:提供本專案擇時章節的理論骨架與『為何 D/P 一定預測某物』的識別論證;其可檢驗核心(股利成長不可預測 ⇒ 報酬可預測)是一個乾淨的、可用免費資料複現的診斷,能與 FF88 互為驗證。
- **可測性(免費資料)**:yes(就其可檢驗核心)— 用 Shiller 免費資料跑『D/P → 未來股利成長』與『D/P → 未來報酬』對照回歸,複現『狗沒吠』;綜述本身非單一測試,但核心恆等式分解完全 $0 可重建;point-in-time 可行。
- **建議 TR 切入(含 Nagel 對照)**:診斷型 TR:分解 D/P 的變異——回歸未來報酬 vs 未來股利成長,展示預測力集中在報酬側(複現 Cochrane/‘Dog’)。這一步不打 Nagel 對照(是識別診斷,非策略);其產出(D/P 確實編碼報酬預測)才餵給 FF88/CT08 的可交易性測試,那裡才由 Moreira-Muir 波動管理 + Cederburg 靜態當關卡。

#### chan_jegadeesh_lakonishok_1996_momentum_strategies — Chan, Jegadeesh & Lakonishok (1996) · ~4200 引用
- **標題**:Momentum Strategies (Journal of Finance)
- **機制族 · 原生棲地**:earnings-surprise drift + revision momentum vs price momentum · US equities / monthly, event-anchored / broad cross-section / 1977-1993 / decomposes the drift into price-momentum, SUE-momentum, and analyst-revision-momentum legs
- **核心主張**:Past returns, standardized earnings surprise (SUE), and analyst-estimate revisions each independently predict returns for 6-12 months; earnings momentum and price momentum are distinct and only partially overlapping — markets underreact to earnings news.
- **與選股/交易的關聯**:This is the PEAD variant most likely to survive on our seat: docs/11 flags estimate-revision/SUE momentum as 'the most promising free-ish factor', low-correlated with quality/momentum. It also tells us WHICH leg (SUE vs revisions) carries the drift so we don't mis-attribute.
- **可測性(免費資料)**:partial — SUE leg is testable: build (EPS_q - EPS_{q-4})/sigma(dEPS) from EDGAR XBRL quarterly EPS, event-anchor to the 8-K/10-Q filed date (true PIT, the docs/02 as_of discipline). The REVISION leg is NOT free historically (IBES paid; Finnhub/FMP free tier is current-only, no history) -> that leg = no. Price-momentum leg = yes. Cost $0 for SUE+price legs.
- **建議 TR 切入(含 Nagel 對照)**:Build SUE from EDGAR PIT, form earnings-momentum deciles anchored to filing date, measure 1/5/20/60d drift; contrast with price-momentum deciles. Nagel control it must beat: RANDOM-ENTRY placebo — reshuffle announcement dates and the drift must vanish (this is the acid test the corpus already mandates for event signals); the SUE spread must also beat STATIC EXPOSURE and survive value-weighting. Explicitly flag the revision leg as untestable on free data (a G-S info-cost / 翻案 condition: paid IBES history). Habitat caveat: drift is strongest in small, low-coverage stocks.

#### ff89_business — Fama & French (1989) · ~3800 引用
- **標題**:Business Conditions and Expected Returns on Stocks and Bonds (JFE 25:23-49)
- **機制族 · 原生棲地**:宏觀 predictor 擇時 / 期限利差 + 違約利差 + D/P → 隨景氣循環的時變預期報酬 · 資產=美股+美債 / 頻率=月與多年 / 廣度=跨資產(股/債同一折現率驅動)/ 年代=1927-1987 / 用途=景氣循環股權溢酬擇時
- **核心主張**:違約利差(Baa-Aaa)與 D/P 捕捉長波景氣風險溢酬、期限利差捕捉短波,三者共同使預期報酬在衰退低谷高、擴張高峰低——可預測性是理性時變風險溢酬而非無效率。
- **與選股/交易的關聯**:把擇時訊號從估值比擴到宏觀利差,且棲地是本專案 FRED 免費資料完全覆蓋的;違約利差是少數與波動旋鈕不高度共線的訊號,適合檢驗 Nagel 批評是否對『宏觀型』訊號同樣成立。
- **可測性(免費資料)**:yes — 期限利差(10Y-3M)、違約利差(Moody's Baa-Aaa)皆 FRED 免費、point-in-time 可行;D/P 用 Shiller;月頻;$0。
- **建議 TR 切入(含 Nagel 對照)**:月頻多預測子 OOS 回歸(違約利差 + 期限利差 + D/P),倉位 ∝ 預測超額報酬。Nagel 對照關卡:違約利差在衰退飆升,天然與波動相關——須對 Moreira-Muir 1/σ² 正交化後違約利差殘差仍帶正 alpha(t≥2);與 Cederburg 靜態比 Calmar。並附 Stambaugh/Newey-West 修正 t。

#### hou-xue-zhang-2015-qfactor — Hou, Xue & Zhang (2015) · ~3500 引用
- **標題**:Digesting Anomalies: An Investment Approach (q-factor model)
- **機制族 · 原生棲地**:風險定價·α 產生 / 橫斷面特徵排序 — 投資(I/A)+ 獲利(ROE)因子模型 · 美股全市場 × 月頻再平衡(年度投資、季度 ROE)× 廣橫斷面(數千檔)× 1967-2014 × 多因子定價與異象吸收
- **核心主張**:以投資(資產成長 I/A)與獲利(ROE)兩因子 + 市場 + size,可吸收 ~80 個異象中的多數,表現不輸/勝 FF 模型。
- **與選股/交易的關聯**:投資與 ROE 兩腿皆可由 EDGAR PIT 重建,直接給選股評分;是 GP 之外第二條基本面 alpha 線,並提供比 Carhart 更貼題、更嚴的歸因基準(可檢驗 GP 是否被 ROE 吃掉)。
- **可測性(免費資料)**:partial→yes — I/A=年度總資產成長、ROE=季度淨利/權益,全在 EDGAR companyfacts(filed 即 PIT);零成本。缺口:原文用 NYSE breakpoints + 全市場宇宙,我們只有 503/610,無法完全複刻因子權重,只能建 our-universe 版做歸因。
- **建議 TR 切入(含 Nagel 對照)**:(A) 建 our-universe I/A 與 ROE quintile L/S;(B) 以 {Mkt, ME, I/A, ROE} 對旗艦 combo 與 GP sleeve 做 spanning/歸因。Nagel 對照:每條因子腿須打敗靜態常數曝險版(F6 靜態控制),整體擇股不得被 1/σ² 波動管理解釋。預先承諾:若 I/A 腿在大型股宇宙 ICIR≈0(docs/10 asset_growth 已見 −0.22 弱),判定=投資因子棲地錯置(原生=小型股/全市場),FAILED 只關閉大型股座位。

#### harvey_liu_zhu_2016_cross_section_expected_returns — Harvey, Liu & Zhu (2016) · ~3500 引用
- **標題**:…and the Cross-Section of Expected Returns (Review of Financial Studies)
- **機制族 · 原生棲地**:multiple-testing discipline / significance-hurdle correction (validation method, not an alpha) · US equities / cross-sectional factor tests / meta-catalog of 300+ published factors / 1967-2012 / a methodology that raises the t-stat bar for 'discovery' under multiplicity
- **核心主張**:Given the hundreds of factors tested, the conventional t>2 bar is far too lax; a multiple-testing-adjusted hurdle of about t>3.0 (Bonferroni/BHY/Holm) is required, and most published factors fail it.
- **與選股/交易的關聯**:This is validation-machinery, the natural companion to our existing DSR (Bailey-LdP deflated Sharpe) and PBO. It arms F5 / the trial-registry with a principled cross-factor hurdle so our own 130+ mechanism zoo is judged under multiplicity, not one-at-a-time — exactly the discipline the corpus is built on.
- **可測性(免費資料)**:yes (methodological, no market data needed beyond what we have) — apply the t>3 / BHY haircut to our existing trial-registry of factor variants and re-report which survive. Reconcile with our DSR usage. Cost $0. Not a data question at all; it's an accounting of how many bets we took (F5 v2 territory).
- **建議 TR 切入(含 Nagel 對照)**:Feed our full trial-registry (every factor/variant we have tested) through the HLZ multiplicity haircut and re-report which factors clear the adjusted bar; cross-check against DSR on the same items. Nagel-control mapping: this is NOT a timing strategy, so the 'control it must beat' is the multiple-testing NULL itself — the deflated/haircut t-stat is the adversary. Deliverable: an F5 rule note (user's <30% credible / >50% noise heuristic) plus a corrected significance table; likely demotes several borderline zoo entries.

#### jegadeesh_1990_predictable — Jegadeesh (1990) · ~3300 引用
- **標題**:Evidence of Predictable Behavior of Security Returns
- **機制族 · 原生棲地**:短視窗過度反應/微結構(1個月 loser 反彈) · 美股 NYSE/AMEX、月頻(1月形成/1月持有)、廣橫斷面、1934-1987 年代、用途=可預測性/contrarian 獲利
- **核心主張**:以上月報酬排名,買 loser 賣 winner 的 1月 contrarian 組合有顯著正報酬(短期反轉),與 3-12月動量方向相反。
- **與選股/交易的關聯**:短期反轉是他們已在 mega-cap 上測死的方向(docs/06:1日/5日反轉淨值破產),但月頻+風控+廣宇宙版尚未在 fabric 正式審判;是判斷『反轉 alpha 是真訊號還是點差 bounce』的教科書案例。
- **可測性(免費資料)**:partial。訊號(月頻排名)完全可用免費日線;但 1月短期反轉惡名昭彰地被 bid-ask bounce/微結構污染——用收盤價會高估毛報酬,淨點差後(TR-12 成本)極可能歸零。point-in-time 可行。無需 tick,但無 tick 就無法乾淨地把 bounce 從真訊號分離,故標 partial。
- **建議 TR 切入(含 Nagel 對照)**:月頻 loser-minus-winner，加 skip-1-day 微結構衛生,同一 book 跑 same-close vs next-close 成交敏感度(F1),掛 TR-12 點差。Nagel 對照:反轉毛報酬必須擊敗隨機進場 + 靜態曝險;真正的殺手對照是『點差成本+skip-day 後殘餘』——若淨值<0(如 docs/06),判定=微結構假象非 alpha。預期 FAILED-net,與既有 mega-cap 結論一致但補上廣宇宙月頻座位。

#### chan_jegadeesh_lakonishok_1996_momentum — Chan, Jegadeesh & Lakonishok (1996) · ~3200 引用
- **標題**:Momentum Strategies
- **機制族 · 原生棲地**:對資訊(尤其盈餘)的漸進擴散/underreaction · 美股 NYSE/AMEX/NASDAQ、月頻、廣橫斷面、1977-1993 年代、用途=區分價格動量與盈餘動量的來源
- **核心主張**:價格動量與盈餘動量(SUE、盈餘公告報酬、分析師預測修正)各自獨立預測後續報酬,兩者互不完全包含;動量主要來自市場對盈餘資訊的緩慢反應。
- **與選股/交易的關聯**:唯一能把他們手上的 EDGAR 基本面(PIT 申報日對齊)真正用進動量的一篇——用 EDGAR 季度 EPS 自建 SUE,測『EDGAR 盈餘動量是否對價格動量有增量』,是一個他們尚未觸及的資料角度。
- **可測性(免費資料)**:partial。價格動量 leg=yes(免費日線)。盈餘動量 leg:SUE 可用 EDGAR 季度 EPS 序列以申報日對齊重建(真 PIT),可行;但『分析師預測修正』leg 需 I/B/E/S → no(付費)。故測 price + EDGAR-SUE 雙 leg,誠實丟掉 revisions leg。重建成本=EDGAR 解析(已具備)。
- **建議 TR 切入(含 Nagel 對照)**:兩個正交 sleeve:6月價格動量 vs EDGAR-SUE 盈餘動量;測邊際貢獻(SUE 對已知動量是否加分)。Nagel 對照:每個 leg 都要先擊敗 Moreira-Muir 波動管理 + Cederburg 靜態;關鍵增量檢定=SUE leg 在控制價格動量後是否仍有殘餘 ICIR。注意 docs/19 已記 PEAD 在大型股宇宙=其最弱棲地(無漂移),故預期 SUE leg 在 S&P 大型股弱;翻案座位=小型股宇宙。

#### cooper-gulen-schill-2008-asset-growth — Cooper, Gulen & Schill (2008) · ~3000 引用
- **標題**:Asset Growth and the Cross-Section of Stock Returns
- **機制族 · 原生棲地**:α 產生 / 基本面特徵排序 — 資產成長(投資)異象 · 美股全市場 × 年度總資產→年頻 × 廣橫斷面 × 1968-2003 × 投資基礎選股
- **核心主張**:過去一年總資產成長最高的公司,未來報酬顯著最低(spread 年 −8% 級別);過度投資 = 未來低報酬。
- **與選股/交易的關聯**:單一 EDGAR 欄位(總資產)即可算的投資因子,直接選股;是 q-factor I/A 腿與 FF5 CMA 的可獨立測試代理,能把『投資因子在大型股是否有效』單獨釘死。
- **可測性(免費資料)**:yes — 資產成長=Assets_t/Assets_{t-1}−1,EDGAR companyfacts 單欄位,PIT(filed)乾淨;年頻低換手;零成本。docs/10 asset_growth ICIR −0.22(弱、方向對),概念已觸及但未正式 decile-hedge 化。
- **建議 TR 切入(含 Nagel 對照)**:年度資產成長 decile L/S(多低成長、空高成長),F1/F2 齊備。Nagel 對照:靜態常數曝險投資 sleeve(F6)+ 隨機特徵 placebo。與 q-factor 合判:若 I/A 與 asset growth 兩者在大型宇宙皆 ICIR≈0,收斂到『投資因子原生棲地=小型股/全市場』的棲地錯置結論(docs/19)。

#### fama-french-2008-dissecting-anomalies — Fama & French (2008) · ~3000 引用
- **標題**:Dissecting Anomalies
- **機制族 · 原生棲地**:描述·歸因 / 跨異象在 microcap-small-big 分層的存活性稽核 · 美股全市場 × 月頻 sort × 廣橫斷面(依 size 分 microcap/small/big)× 1963-2005 × 異象普遍性稽核
- **核心主張**:多數異象(動量以外)集中在 microcap,在大型股大幅減弱或消失;sort 法與 Fama-MacBeth 迴歸給出不同強度。
- **與選股/交易的關聯**:直接對映本專案痛點:我們宇宙=大型股,而多數異象原生棲地=小型股(docs/19 棲地錯置主題)。這篇是『為何你在大型股測不到』的權威背書,也是決定要測哪些因子的先驗地圖。
- **可測性(免費資料)**:partial — 方法(size 分層 + sort vs FM 對照)可直接採用,但完整複刻需 microcap 宇宙,我們沒有(僅 503/610 大中型)。價值=方法論與先驗,非新策略(符合 docs/20:好論文=新對照+新量測);零成本(用既有資料做 size 分層)。
- **建議 TR 切入(含 Nagel 對照)**:非建新策略,而是把已測因子(GP、accruals、asset growth、value)在 503/610 內做 size 三分層 + sort-vs-FM 雙法對照,量化每個因子的『大型股衰減幅度』並寫回 docs/19 棲地表。Nagel 對照:診斷型 TR,控制=同因子最小 size 分層 vs 最大分層的 spread 差;若 alpha 全集中在最小分層,證實棲地錯置。非擇時故不需 1/σ²。

#### daniel-titman-1997-characteristics-vs-covariances — Daniel & Titman (1997) · ~2900 引用
- **標題**:Evidence on the Characteristics of Cross-Sectional Variation in Stock Returns
- **機制族 · 原生棲地**:驗證方法·α 歸因 / 特徵 vs 因子暴露的識別檢定 · 美股全市場 × 月頻 × 廣橫斷面 × 1973-1993 × 判別『是特徵還是共變異在定價』
- **核心主張**:報酬由公司特徵(B/M、size)本身預測,而非其對 HML/SMB 的因子載荷;控制特徵後因子 beta 無溢酬 = 挑戰風險基礎的因子模型。
- **與選股/交易的關聯**:這是整個 anomaly zoo 的元問題,且直接對映本框架 Nagel-control 哲學:一個異象到底是『特徵 alpha』還是『可被靜態因子曝險複製』。提供現成的識別檢定範式,可直接升級 F6 控制組方法論。
- **可測性(免費資料)**:partial — 需個股報酬(有)+ FF 因子(有)+ 特徵(B/M 由 EDGAR 權益/市值、size 由價格×股數,PIT 可行);零成本。原文用 characteristic-balanced portfolios,我們宇宙 N 較小、因子載荷估計雜訊大,只能做簡化 double-sort(特徵×載荷)。
- **建議 TR 切入(含 Nagel 對照)**:對已 PASSED 的 GP sleeve 與旗艦 combo 做 Daniel-Titman 式雙分類:固定特徵(GP 分位)後看因子 beta 是否仍有溢酬,反之亦然——即 F6『哪個最簡單的控制能解釋它』的嚴格化。Nagel 對照:特徵中性化後殘餘報酬若消失,判定=因子曝險(靜態 beta),非特徵 alpha;唯有特徵固定後 beta 溢酬消失、特徵溢酬存活,才支持特徵 alpha。

#### moskowitz_grinblatt_1999_industry — Moskowitz & Grinblatt (1999) · ~2800 引用
- **標題**:Do Industries Explain Momentum?
- **機制族 · 原生棲地**:產業層報酬續延/類股輪動(個股動量的產業聚合) · 美股按產業聚合、月頻、產業層廣度(~20 產業)、1963-1995 年代、用途=檢驗動量是否為產業效應
- **核心主張**:產業動量(買贏家產業組合)強勁,且在很大程度上『解釋掉』個股動量——控制產業後個股動量顯著減弱;動量有實質的產業成分。
- **與選股/交易的關聯**:他們的個股 JT 動量已死(TR-11),但從未測產業層聚合是否還活;產業動量也是既有 5-sleeve combo 裡『科技動量/防禦輪動』sleeve 的學理根;可用 EDGAR SIC 直接落地。
- **可測性(免費資料)**:partial-yes。報酬=免費日線。產業分類:EDGAR filer metadata 帶 SIC 碼(可近似 PIT,但 SIC 由 SEC 指派、非嚴格歷史快照),或用靜態 GICS 代理;兩者都有 vintage 誤差但可做。無需付費資料。標 partial 僅因產業對映品質。
- **建議 TR 切入(含 Nagel 對照)**:以 SIC/GICS 建產業組合,產業動量 long 贏家產業;直接對照=個股 JT 動量(論文宣稱產業吸收個股動量)。Nagel 三件套:產業動量必須擊敗 Moreira-Muir 1/σ² 波動管理 + Cederburg 靜態 + 隨機產業輪動。預先承諾:若產業動量 ≈ 隨機輪動或被靜態科技曝險解釋(2015-26 科技牛),判定=產業動量在此樣本=偽裝的科技 beta,與 docs/10 的 regime-rotation 教訓一致。

#### btz09_vrp — Bollerslev, Tauchen & Zhou (2009) · ~2600 引用
- **標題**:Expected Stock Returns and Variance Risk Premia (RFS 22:4463-4492)
- **機制族 · 原生棲地**:variance risk premium 擇時 / VRP = 隱含變異數(VIX²)− 已實現變異數 → 短期報酬 · 資產=美股大盤(S&P500)/ 頻率=月(訊號源含日內已實現變異)/ 廣度=單指數 / 年代=1990-2007 / 用途=1-6 月股權溢酬擇時
- **核心主張**:VRP(風險中性期望變異數減物理已實現變異數)顯著正向預測 1-6 個月市場超額報酬,其可預測性在季度視窗達峰值,遠強於 D/P 等傳統估值比,反映時變風險趨避。
- **與選股/交易的關聯**:與本專案既有訊號正交的『新訊號家族』,且棲地是本專案能觸及的近代高頻期(1990-);是少數可能真正打敗波動旋鈕的候選,因為 VRP 本身就編碼了『非波動』的風險溢酬資訊——正好用來壓力測 Nagel 批評的邊界。
- **可測性(免費資料)**:partial→大致 yes — VIX(CBOE 免費,1990-;VXO 至 1986)提供隱含變異;已實現變異可由日線指數報酬估(理想用日內,但日線月度 RV 可近似)。point-in-time 可行。限制:原文用高頻 RV,免費日線版是近似;1990 前需重建 → 該段標 partial。$0。
- **建議 TR 切入(含 Nagel 對照)**:月頻:VRP = VIX²(月末)− trailing 已實現變異(日線)→ OOS predictive regression;倉位 ∝ 預測超額報酬。關鍵 Nagel 對照:因 VRP 與波動高度相關,必須把倉位對 Moreira-Muir 1/σ² 與『純 VIX 水位擇時』雙重正交化後,VRP 殘差仍須帶正 alpha(t≥2);否則判『VRP 只是波動管理的另一參數化』。淨 5bps + 截倉。

#### fama_french_2008_dissecting_anomalies — Fama & French (2008) · ~2600 引用
- **標題**:Dissecting Anomalies (Journal of Finance)
- **機制族 · 原生棲地**:cross-sectional fundamental anomaly, size-group habitat mapping · US equities / monthly / broad cross-section split into micro-small-big / 1963-2005 / diagnostic — which anomalies survive value-weighting vs live only in microcaps
- **核心主張**:Most anomalies (accruals, net share issues, asset growth, momentum, profitability) are strong in microcaps and weak/absent in the value-weighted big-cap universe; sorts vs regressions disagree because tiny stocks dominate equal-weight sorts.
- **與選股/交易的關聯**:This is the exact intellectual backbone of our docs/19 'habitat' argument (PEAD/accruals live in small caps; large-cap FAILED only closes the large-cap seat). Testing it directly turns our qualitative habitat claim into a measured size-interaction across our whole factor library.
- **可測性(免費資料)**:partial — needs EDGAR PIT fundamentals (accruals/asset growth/profitability, XBRL ~2009+) + free daily OHLCV extended to small caps. Point-in-time OK via filed-date. Binding gaps: (a) microcap universe with survivorship/delisting returns is not clean on free data (yfinance/stooq drop dead tickers), (b) pre-2009 structured fundamentals thin. Feasible as a large+small-cap post-2009 slice; the true microcap tail is not. Cost $0.
- **建議 TR 切入(含 Nagel 對照)**:Rebuild each anomaly's long-short spread separately within micro/small/big size groups, value-weighted vs equal-weighted, on our EDGAR+price panel. Nagel control it must beat: STATIC EXPOSURE — a value-weighted buy-and-hold of the same characteristic-sorted portfolio is the honest baseline, and the anomaly must add over it AND survive value-weighting (which kills most microcap effects); random-entry placebo on the sort ranks confirms the spread isn't a sorting artifact. Pre-commit: if spreads survive only equal-weighted-microcap, verdict = 'real but in an unreachable seat' (reconverges to docs/11 data-dimension bind).

#### stambaugh_yu_yuan_2012 — Stambaugh, Yu & Yuan (2012) · ~2400 引用
- **標題**:The Short of It: Investor Sentiment and Anomalies
- **機制族 · 原生棲地**:Market-wide sentiment + short-sale impediments -> overpricing dominates underpricing; anomaly short legs strong after high sentiment (behavioral alpha timing) · US equities, monthly, 11 anomaly long-shorts, 1965-2008; conditions anomaly returns on the BW sentiment index; purpose = time anomalies via sentiment and locate the profit in the short leg
- **核心主張**:Each of 11 anomalies is stronger following HIGH sentiment, and the effect is concentrated in the SHORT (overpriced) leg because short-sale constraints prevent correction; low-sentiment periods yield weak anomalies.
- **與選股/交易的關聯**:A direct, actionable timing overlay for the anomalies we can build (GP-quality survivor, LT-reversal, CGO): explains WHEN a behavioral spread pays. Also a sober caution — profits sit in the short leg our long-only $0 seat cannot easily trade, tempering expectations.
- **可測性(免費資料)**:PARTIAL/YES. Anomaly L/S from EDGAR + price. BW sentiment index free (same look-ahead caveat as Baker-Wurgler). Short-leg feasibility caveat: our free-data project is effectively long-only, and the paper predicts most of the profit is short-side (unreachable) -> honest partial. PIT caveat on sentiment construction.
- **建議 TR 切入(含 Nagel 對照)**:Take our buildable anomalies (GP-quality, LT-reversal, CGO), split returns by lagged BW sentiment tercile AND by leg; replicate 'high sentiment -> wider spread, short-leg-driven'. Nagel controls it must beat: (1) 1/sigma^2 vol management — high sentiment correlates with the vol cycle, so prove sentiment-timing != vol-timing (hardest control); (2) static unconditional always-on anomaly exposure (Cederburg) — does sentiment-timing beat always-on?; (3) placebo sentiment dates. Long-only honesty: report long-leg-only vs full spread to quantify how much our $0 seat can actually capture. PASSED bar: the sentiment-conditioned LONG leg (reachable) still adds over a vol-managed always-on anomaly.

#### ang-chen-xing-2006-downside-risk — Ang, Chen & Xing (2006) · ~2400 引用
- **標題**:Downside Risk
- **機制族 · 原生棲地**:Conditional (down-market) market beta priced separately from ordinary beta + coskewness / semivariance · US equity cross-section / monthly / broad NYSE / 1963-2001 / risk pricing + selection
- **核心主張**:Stocks with high downside beta (covariance with the market conditional on down markets) earn ~6%/yr higher returns; downside risk is priced beyond ordinary beta and coskewness.
- **與選股/交易的關聯**:A tail-aware refinement of beta for weighting/selection, and a direct test of whether our TR-06 SML-reversal (high-beta won in the AI bull) is actually a downside-beta compensation story rather than a CAPM anomaly.
- **可測性(免費資料)**:YES. Downside beta = slope of stock excess return on market excess return over down-market days only, trailing ~12m daily; coskewness likewise — free daily OHLCV + index. Point-in-time fine.
- **建議 TR 切入(含 Nagel 對照)**:Estimate realized relative downside-beta (beta^minus - beta) monthly; Fama-MacBeth price it in the 610 universe and compare to plain-beta pricing from TR-06. Nagel controls it MUST beat: zero-signal/random-beta basket (F6) and static EW exposure (F3); as a risk premium it must show the return is not merely the same high-beta-wins tilt TR-06 already documented (beat a plain-beta long-short). Prior: in an AI melt-up downside-beta ~ beta, so premium likely = beta compensation -> PARTIAL / attribution value, not clean alpha.

#### daniel_moskowitz_2016_crashes — Daniel & Moskowitz (2016) · ~2300 引用
- **標題**:Momentum Crashes
- **機制族 · 原生棲地**:動量的崩盤/選擇權性(熊市反彈時 past-loser 高 beta)+ 動態波動/狀態縮放 · 美股(及國際/跨資產)WML 因子、月頻、廣橫斷面、1927-2013 年代、用途=刻畫動量尾部風險並做動態風險管理
- **核心主張**:動量在恐慌後反彈期(熊市底部、市場高波動、past-loser 呈高 beta)發生罕見但巨大的崩盤;以動態縮放(依預測期望報酬/預測變異數加權)可大幅改善動量的 Sharpe。
- **與選股/交易的關聯**:這是 fabric『Nagel 對照』的正面戰場:動態/風險管理動量 vs 純 1/σ² 波動擇時。既有旗艦 combo 的價值全在風險塑形(Carhart t=3.38),而 DM 的動態動量正是『用狀態縮放賺風險塑形』的最強學術宣稱——直接檢驗它是否勝過最簡單的波動管理控制。(附註:residual momentum 是崩盤緩解的近親,但 Blitz-Huij-Martens 2011 僅 ~500 引用,低於門檻,故不單列。)
- **可測性(免費資料)**:yes。WML 因子、崩盤事件描述(2009 動量崩盤)、動態加權都可在 503 宇宙+指數長歷史上重建;預測變異數用 GARCH(`arch`,docs/03 已規劃),預測期望報酬用滾動估計。無需選擇權/日內。2009 崩盤需該年代在樣本內——用其長指數歷史涵蓋。
- **建議 TR 切入(含 Nagel 對照)**:建 WML,刻畫其 drawdown 條件於(熊市+高波動+loser 高 beta);建 DM 動態動量=WML×(forecast μ / forecast σ²)。核心 Nagel 對決:動態動量必須加分於 (a) Moreira-Muir 純 1/σ² 波動管理 WML、(b) Barroso 常波動 WML、(c) Cederburg 靜態。預先承諾(照 TR-17 KMZ 前例):若動態加權的 Sharpe 增益塌回波動管理控制,判定=『崩盤擇時=波動擇時的重新包裝』;唯有淨成本+截倉後仍勝波動控制,才算真正的崩盤 alpha。

#### cs98_cape — Campbell & Shiller (1998) · ~2300 引用
- **標題**:Valuation Ratios and the Long-Run Stock Market Outlook (JPM 24:11-26)
- **機制族 · 原生棲地**:valuation-ratio 均值回歸 / CAPE(10 年平滑實質盈餘 P/E)→ 長期報酬 · 資產=美股大盤 / 頻率=月、10 年疊加 / 廣度=單指數 / 年代=1881-1997 / 用途=長期(十年級)報酬與均值回歸展望
- **核心主張**:高 CAPE 與高 D/P 偏離歷史均值後傾向均值回歸,主要透過『價格向下修正』而非盈餘/股利上升實現;CAPE 對後續 10 年實質報酬有可觀負向解釋力。
- **與選股/交易的關聯**:散戶最常引用的擇時訊號,也是最容易被過度信任的;本專案該給它一個誠實裁決——CAPE 的長視窗可預測性 vs 其 OOS/實務不可交易性(重疊視窗、極少獨立觀測、Stambaugh 偏誤)。直接服務『50-100% 不可達』與期望管理敘事。
- **可測性(免費資料)**:yes — Shiller 免費資料直接含 CAPE(1881-),trailing 10 年實質盈餘即 point-in-time 乾淨;$0。注意:重疊 10 年視窗使有效樣本 n_eff 極小,須誠實標註。
- **建議 TR 切入(含 Nagel 對照)**:月頻 CAPE 的 OOS 擇時(倉位隨 CAPE 相對其擴張窗均值升降),同時報告長視窗回歸的 n_eff 與 Stambaugh/Hodrick 修正後 t。Nagel 對照關卡:與 Moreira-Muir 波動管理及 Cederburg 靜態 B&H 比淨值與 Calmar;預先承諾——極可能判 PARTIAL/FAILED(統計上真、可交易 alpha 上不勝靜態曝險),作為『真訊號 ≠ 可交易 alpha』的教材案例。

#### rsz10_combination — Rapach, Strauss & Zhou (2010) · ~2300 引用
- **標題**:Out-of-Sample Equity Premium Prediction: Combination Forecasts and Links to the Real Economy (RFS 23:821-862)
- **機制族 · 原生棲地**:forecast combination / 多預測子簡單平均 → 穩健正 OOS R²,與景氣循環連動 · 資產=美股大盤 / 頻率=月 / 廣度=15 個 GW 預測子的組合 / 年代=1947-2005 / 用途=穩健化股權溢酬 OOS 擇時
- **核心主張**:單一預測子 OOS 不穩,但對眾多預測子的預測值做簡單平均(組合預測)可顯著降低變異、產生穩健正 OOS R²,且其擇時報酬集中在衰退期,連結實體經濟。
- **與選股/交易的關聯**:本專案已有 GW 15 預測子(TR-17)且信奉集成穩健(ensemble robustness 已是 README 賣點);此文是把它們從『單獨都被波動旋鈕打爆』升級為『組合是否翻案』的最直接、最省成本延伸,測試集成能否跨越 Nagel 門檻。
- **可測性(免費資料)**:yes — 完全複用 TR-17 既有 GW 預測子(公開/免費),只加預測值簡單平均與 OOS R²、衰退期分解;point-in-time 可行;$0。
- **建議 TR 切入(含 Nagel 對照)**:對 15 個 GW 預測子各自 OOS 預測後取簡單平均,構 1/σ² 目標倉位。Nagel 對照關卡:組合預測的擇時淨值須勝 Moreira-Muir 波動管理與 Cederburg 靜態,且對波動管理殘差 alpha t≥2;預先承諾——若組合增益仍被波動旋鈕吸收(呼應 TR-17 對 KMZ 的判定),判『集成穩健為真但 alpha=波動擇時』,強化本專案既有結論。

### C.3 第三波 — 需付資訊成本(新資料維度)

需要日內 / 選擇權 / tick / 國際 / 小型股等我們目前沒有的資料。先寫下『翻案條件=哪筆資料』,待資料維度打開再排(G-S 紀律)。

#### heston-1993-stochastic-vol — Heston (1993) · ~10000 引用
- **標題**:A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options
- **機制族 · 原生棲地**:Continuous-time mean-reverting (CIR/square-root) variance with vol-of-vol and price-vol (leverage) correlation · Options / continuous-time / single-underlying / 1990s- / derivatives pricing & vol-surface calibration
- **核心主張**:Options under a mean-reverting square-root variance process with leverage correlation admit a semi-closed-form price, capturing the smile/skew that Black-Scholes cannot.
- **與選股/交易的關聯**:Mostly a pricing model whose native habitat (options) is unreachable on $0, BUT its physical-side ingredients — mean-reverting variance, vol-of-vol, negative return-vol correlation — are testable stylized facts that upgrade our risk model and drawdown dynamics beyond GBM (TR-05).
- **可測性(免費資料)**:PARTIAL/NO. Pricing use = NO (needs a PIT options chain we do not have; budget). The PHYSICAL variance dynamics (mean-reversion speed, vol-of-vol, corr(return, delta-var)) ARE estimable from free daily index/stock realized vol. Risk-neutral / VRP calibration would need options -> NO.
- **建議 TR 切入(含 Nagel 對照)**:Not a pricing TR. Estimate the physical Heston-style variance process from daily realized vol on our indices and feed it into the Monte-Carlo risk model as a stochastic-vol upgrade to TR-05's GBM, benchmarked against the assumption-free block-bootstrap 'honest MC'. This is risk measurement, not an alpha claim, so the relevant control is the risk-matched static / block-bootstrap baseline (not the Nagel timing triple). Prior: stoch-vol MC narrows the GBM tail gap (TR-05 showed GBM understates tails by orders of magnitude) but still trails the block bootstrap; option-pricing use stays N/A on budget.

#### delong_shleifer_summers_waldmann_1990 — De Long, Shleifer, Summers & Waldmann (1990) · ~9500 引用
- **標題**:Noise Trader Risk in Financial Markets
- **機制族 · 原生棲地**:Unpredictable noise-trader sentiment creates systematic risk that deters arbitrage -> mispricing persists and sentiment risk is priced (theory / economic foundation, not a tradable signal) · Conceptual/theory; motivated by closed-end funds and broad markets, any frequency; purpose = show noise-trader sentiment is a priced, non-diversifiable risk that limits arbitrage
- **核心主張**:Short-horizon arbitrageurs face the risk that noise-trader mispricing worsens before it corrects (noise-trader risk); this risk is systematic, deters arbitrage, and earns a premium, so assets more exposed to sentiment risk are riskier and cheaper.
- **與選股/交易的關聯**:The theoretical origin of 'sentiment as priced risk' that underpins Baker-Wurgler and Stambaugh-Yu-Yuan; supplies the noise-trader-risk framing for why our sentiment overlays should be treated as a risk premium, not a free lunch. Names the explicitly-requested 'noise trader risk' theme and closes the subdomain's theory quartet.
- **可測性(免費資料)**:PARTIAL/NO for the canonical test. The classic closed-end-fund-discount test (Lee-Shleifer-Thaler) needs CEF discount data — not in our free stack. Free surrogate: a sentiment-risk beta (rolling loading on delta-BW-sentiment) as a priced characteristic, buildable from price + free sentiment index (with the look-ahead caveat). PIT weak. Primarily a framing/foundation paper.
- **建議 TR 切入(含 Nagel 對照)**:Estimate each stock's sentiment-risk beta (rolling loading on delta-BW-sentiment), sort, and test whether high-sentiment-beta stocks carry a return premium (noise-trader-risk compensation). Nagel controls it must beat: (1) static exposure — is high-sentiment-beta just high market-beta / high-vol held long? (Cederburg); (2) 1/sigma^2 vol management — sentiment beta ~ vol exposure, the decisive control; (3) placebo sentiment series. Honest pre-commit: the premium is likely subsumed by market-beta/idio-vol -> verdict = foundational framing confirmed, no separable tradable premium on our seat; its primary role is to justify treating the Baker-Wurgler / SYY overlays as risk premia (G-S consistent), not alpha.

#### merton-1976-jump-diffusion — Merton (1976) · ~8500 引用
- **標題**:Option Pricing When Underlying Stock Returns Are Discontinuous
- **機制族 · 原生棲地**:Jump-diffusion: Poisson (lognormal) jumps superimposed on Brownian diffusion — discontinuous price paths · Options / continuous-time / single-underlying / 1970s- / derivatives pricing, but the jump component is observable in physical returns
- **核心主張**:Adding lognormal Poisson jumps to geometric Brownian motion produces fat tails/skew and prices the discontinuous crash risk that Black-Scholes omits.
- **與選股/交易的關聯**:The jump/crash channel is exactly the tail our GBM (TR-05) and normal VaR (TR-04) mispriced; realized jump intensity can also serve as a cross-sectional crash-risk characteristic for selection (avoid high-jump-risk names).
- **可測性(免費資料)**:PARTIAL->YES for the physical side. Jumps are detectable in free daily returns (threshold filters on large |returns| — cruder than intraday bipower but workable); per-name jump intensity/size is estimable from daily OHLCV. Option-pricing calibration = NO (no chain). Point-in-time OK for realized-jump features.
- **建議 TR 切入(含 Nagel 對照)**:Two-pronged. (a) Risk-model TR: add a jump component to the TR-05 Monte-Carlo and test whether jump-diffusion closes the tail/MDD gap vs the block bootstrap (control = risk-matched baseline, not Nagel timing). (b) Selection TR: build a per-name realized-jump-intensity characteristic (count/size of extreme daily moves) and sort the 610 universe — do high-jump-risk stocks underperform risk-adjusted? Must beat zero-signal/random basket (F6) and static EW (F3); double-sort with MAX since extreme daily moves overlap. Prior: jump feature ~ MAX/idio-vol proxy — adds tail realism to the risk model (measurement value) but no clean alpha.

#### banz-1981-size-effect — Banz (1981) · ~7000 引用
- **標題**:The Relationship Between Return and Market Value of Common Stocks
- **機制族 · 原生棲地**:α 產生 / 橫斷面特徵排序 — 規模(市值)異象 · 美股全市場(含 NYSE 微型股)× 月頻 × 廣橫斷面 × 1936-1975 × 規模選股
- **核心主張**:小市值股經 CAPM beta 調整後仍有顯著正超額報酬;size 是 beta 之外的橫斷面預測子。
- **與選股/交易的關聯**:SMB 源頭、FF/q 模型的 size 腿;但也是最受棲地限制的因子——我們宇宙無真微型股,是誠實記錄『資料維度=綁定約束』(docs/11)的教科書範例。
- **可測性(免費資料)**:no/partial — 市值=價格×股數(EDGAR 股數 PIT 可行),但 size 溢酬原生棲地=微型股/NYSE 底部 decile,我們宇宙(47 科技 + 503 S&P500 + 610 倖存者)全是大中型,分散度不足以重現。翻案需小型股 PIT 宇宙(新資料維度)。零成本但低效力。
- **建議 TR 切入(含 Nagel 對照)**:在 610 倖存者-aware 宇宙做 size quintile,誠實標『curated/大型偏誤』;主要價值=量化我們宇宙的 size 效力上限。Nagel 對照:靜態 size 曝險(F6);但因分散不足,預期判定=N/A 或 PARTIAL『棲地不可及』,不編造正結果(F8)。與 FF 2008 Dissecting 合看:size 是多數異象的載體維度,缺它=多數異象在此測不到的根因。

#### french-schwert-stambaugh-1987 — French, Schwert & Stambaugh (1987) · ~5500 引用
- **標題**:Expected Stock Returns and Volatility
- **機制族 · 原生棲地**:Aggregate risk-return relation: positive ex-ante vol-in-mean, negative contemporaneous vol-shock (vol feedback / leverage asymmetry) · Aggregate US stock market / monthly & daily / single-series / 1928-1984 / risk premium + vol dynamics
- **核心主張**:The expected market risk premium rises with predictable (ex-ante) volatility, while unexpected volatility shocks are negatively related to returns — the vol-feedback / leverage asymmetry.
- **與選股/交易的關聯**:Underwrites whether vol should scale exposure up or down, and the negative-shock channel is the crash/vol-feedback mechanism behind our drawdown overlays; a diagnostic anchor for our regime.
- **可測性(免費資料)**:YES. Only market index daily/monthly returns are needed to build monthly realized vol and test vol-in-mean and the return-vol asymmetry. Free long index history (SPY/QQQ + FF market series back to 1926). Point-in-time OK.
- **建議 TR 切入(含 Nagel 對照)**:Rebuild the ex-ante-vol-in-mean regression and the unexpected-vol asymmetry on our long index history, then a tradable vol-in-mean exposure rule. Nagel controls it MUST beat: 1/sigma^2 vol management (Moreira-Muir), static exposure, random entry (full triple). Prior: the sign/asymmetry replicates as a diagnostic (PARTIAL, vol-feedback confirmed) but as a timing rule collapses into the inverse-variance control — documents the risk-return relation for our era rather than standalone alpha.

#### chordia-roll-subrahmanyam2000-commonality — Chordia, Roll & Subrahmanyam (2000) · ~3000 引用
- **標題**:Commonality in Liquidity (Journal of Financial Economics)
- **機制族 · 原生棲地**:liquidity-commonality(個股流動性隨市場整體流動性共同波動) · US equities,日內報價價差/深度變動,1992,用途=證明個股流動性有共同因子(市場層流動性衝擊)。原生需『日內報價價差/深度』。
- **核心主張**:個股流動性(價差、深度)變動顯著載於市場與產業層流動性變動 → 流動性有系統成分,無法分散,支撐 P-S / Acharya-Pedersen 的 priced liquidity risk。
- **與選股/交易的關聯**:為『流動性風險為何被定價』提供微觀證據(共同成分不可分散);對選股是 P-S/Acharya-Pedersen 的機制解釋,而非直接信號。選股直接適用性較弱。
- **可測性(免費資料)**:PARTIAL。原生度量=日內報價價差/深度,我們沒有。只能用日線 Amihud ΔILLIQ 做 commonality 代理(regress 個股日 ΔILLIQ on 市場日 ΔILLIQ)——是 proxy,非原始報價版本。Point-in-time OK。
- **建議 TR 切入(含 Nagel 對照)**:用日線 Amihud-based commonality beta(個股 ΔILLIQ 對市場 ΔILLIQ 的載荷)當系統流動性風險排序。Nagel 對照:(1) 靜態曝險——commonality beta 是否只是 market beta / size?中性化後檢查;(2) 隨機組合 null;(3) 高 commonality 在危機爆發 → 對照 1/σ² 波動管理。定位=P-S TR 的 supporting sleeve(驗證共同成分存在並被定價),非旗艦。

### C.4 排程(接 docs/21 Paper-to-TR 管線)

- **第一波(17 篇)**:免費資料可重建,直接進 [docs/21](21-paper-to-tr-pipeline.md) 的 TR 執行階段。每篇 F0 預先承諾 + builder/auditor 雙軌 + 強制 Nagel 三重對照。建議每輪挑 2-3 篇,先做引用最高且洞見最新的。
- **第二波(29 篇)**:先補資料工程(產業分類表、指數長歷史、論文公開附錄),再進 TR。
- **第三波(6 篇)**:掛在 [docs/19](19-mechanism-taxonomy.md) 的翻案條件下,標明『資訊成本=哪筆資料』;待日內/選擇權/國際資料 ingest 後啟動(對應 docs/00 §E7 的資料維度路線)。
- **與 Part B 的回饋迴圈**:任何一波做完,若判定與某篇 Part B 台帳論文的座位重疊,依 F10 級聯回頭更新該論文的 angle_risk 與優先度。

---
*生成:2026-07-08。台帳 52 篇 + 前瞻 64 篇,由 14-agent workflow(6 主題台帳 + 8 子領域選書)結構化輸出彙整。引用數為估計,深讀時以原文與 Google Scholar 覆核。*