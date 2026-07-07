# Paper-to-TR 管線 — 持續探索高品質論文並反饋複測的 agentic flow 設計

> 緣起(2026-07-08):docs/20 那輪七篇論文的人工審思產出了 G-S 經濟學地基、Nagel 控制模式、TR-17 等高價值成果——本檔把那次「人肉執行」固化成可持續運轉的五階段管線。設計原則:**論文的價值主要是新控制組與新測量方式,不是新策略;論文必須進 fabric 才算數。**

## 0. 啟發總結(為什麼要有這條管線)

1. 這輪七篇的實際產出:1 個經濟學地基(G-S:$0 資訊成本→$0 alpha 均衡)、1 個標準攻擊武器(Nagel 控制)、1 個新診斷維度(LPS 隔夜/日內)、3 個測量修正(MP/Shumway/Lo 系)、1 個 PARTIAL 判定+明確翻案條件(KMZ)。**武器庫 > 彈藥。**
2. 讀論文 ≠ 測論文:KMZ 頂刊+0.47 Sharpe 宣稱,進 fabric 出來是「機制形狀微弱、被 1/σ² 控制支配」。
3. 座位思維保護雙向:不被 headline 帶走,也不冤枉好機制(定理未破,棲地不可及)。

## 1. 五階段管線

```
[0 發現] 週cron → [1 分診] LLM → [2 深讀映射] agent → [3 TR執行] builder+auditor → [4 反饋] 註冊表+F10級聯
```

### 階段 0 — 發現(全自動,$0)
- **來源**:SSRN FEN 熱門下載、arXiv q-fin(每日 RSS)、NBER 新 working papers、JF/JFE/RFS 期刊目錄 RSS、AQR/Man Institute/Research Affiliates 白皮書頁、Alpha Architect/Quantpedia 新條目。
- **機制**:GitHub Actions 週頻 cron(復用 `monitor.yml` 模式);去重用 seen-list state 檔(復用 `serenity_tracker` 模式);輸出候選清單 JSON。

### 階段 1 — 分診(廉價 LLM,~$1-2/月)
對每篇 title+abstract 打標(對齊 [docs/19 分類軸](19-mechanism-taxonomy.md)):
- 功能分類(α/風險測量/塑形/估計/執行/驗證方法)
- 原生棲地(資產×頻率×廣度×年代)與**棲地可及性**(我們的免費資料到得了嗎)
- **親緣**:最近的既有 TR 編號
- **challenge map**:是否挑戰 docs/18 的某個既有判定(挑戰 PASSED > 挑戰 FAILED)
- 可信度(期刊層級/作者/引用)
評分 = 相關性(挑戰判定 / 新控制組或方法 / 棲地可及)× 可信度 → **Telegram 週報**(前 N 篇+一句話理由)。

### 階段 2 — 深讀映射(agent,按需)
過門檻或使用者點名的論文:
- 抓 PDF(SSRN/NBER 免費;`pypdf` 已裝)、**核對原文關鍵頁**——分診可用摘要,深讀必須抽原文(本輪教訓:KMZ 的 T=12 滾動、fill 慣例這類生死細節只在原文)。
- 產出 docs/20 式對帳條目:`我們的覆蓋 / 論文真正主張(含樣本×成本×限制)/ 缺口 / 行動`,行動四選一:**(a) 已覆蓋豁免(記理由)(b) 開新 TR (c) 修 fabric 規則(v1.x 修訂案)(d) 挑戰既有判定 → 觸發 F10 複測**。

### 階段 3 — TR 執行(既有 workflow 模式)
- **F0 預先承諾先寫**(可證偽宣稱+PASSED/PARTIAL 判準+棲地/座位/錯置自評+翻案條件)→ builder agent 寫 `scripts/tests/tr_XX.py`(F1-F12 全合規)→ auditor agent 重跑核數。
- TR-01~08 的 8+1 代理工作流即此階段的既有實作。

### 階段 4 — 反饋
- 判定 → [docs/18 註冊表](18-strategy-registry.md) + [docs/19 分類學](19-mechanism-taxonomy.md) 新列 + [trial-registry](trial-registry.md) 變體計數。
- **推翻既有判定 → F10 級聯複測**(先例:TR-16 反轉 TR-11)。
- 季度儀式:當季映射條目彙整成 docs/20 式總覽;年度儀式(docs/18 §4)不變。

## 2. 護欄(全部來自 docs/20 那輪的教訓)

1. **Nagel 三件套強制**:進 TR 的每篇必答「波動管理 / 靜態曝險 / 隨機進場——哪個最簡單的控制能解釋它?」(F6 v2 的論文版)。
2. **原文核對強制**:禁止只憑摘要/推文轉述開 TR。
3. **翻案條件=資訊成本**(G-S 紀律):必須寫「需要什麼資料、大約多少錢」,不許寫「未來再看」。
4. **人在迴路閘門**:階段 0-1 全自動;**階段 2-4 由使用者從週報點名觸發**(成本控制+品味判斷)。
5. 每篇的變體家族計入 trial-registry(F5 v2)。

## 3. 實作順序與成本

| Phase | 內容 | 成本 | 狀態 |
|---|---|---|---|
| 1 | 發現 cron + seen-list + Telegram 週報(`scripts/notify/paper_scout.py` + monitor.yml 加一步) | $0 | 待建(小) |
| 2 | 分診 LLM(Haiku batch;需 API key 決策——或先人工從週報分診) | ~$1-2/月 | 待決 |
| 3-4 | 深讀→TR→反饋 | 本地算力 | **已存在**(本 session 即證明) |

---
*先例:docs/20(七篇人工執行)、TR-17(KMZ 全流程示範:原文核對→F0→實測→Nagel 控制→PARTIAL+翻案條件)。2026-07-08。*
