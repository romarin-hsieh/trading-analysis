# 參考資料索引（REF Index）

> 目的：記錄我們**索引過什麼、參考過什麼、參考程度、以及採用/不採用的原因**，並帶**版本戳記**以便日後快速比對版本內容。擴大參考來源時不必每次從頭開始。

## 檔案分類
| 檔案 | 類型 | 內容 |
|---|---|---|
| [repos.md](repos.md) | GitHub repos | 已 clone 研讀的開源 repo（含 git SHA 版本） |
| [articles.md](articles.md) | 文章/網頁/論文/文件 | 研究引用的網路來源（含存取日期） |
| [data-sources.md](data-sources.md) | 資料源目錄 | **70 個資料源 × 7 類的盡職調查全文**(2026-07 站上驗證;免費/<$5 判定、PIT 品質、解鎖對照)——docs/24 的完整附錄 |
| [scraping-and-apis.md](scraping-and-apis.md) | 工具選型 | **Dataroma/13F 路徑判定(EDGAR 直取+edgartools)、6 個 adopt 的 API wrapper、反爬蟲工具階梯(curl_cffi→patchright→nodriver)+ GHA datacenter-IP 警告** |
| [videos.md](videos.md) | 影片/逐字稿 | YouTube 影片摘要、財經創作者逐字稿萃取（未來 pipeline 落點） |

## 版本戳記慣例（version stamp）
- **GitHub repos**：用 **git commit SHA**（精確、權威）。記 `short_sha` + `commit_date` + clone 日期。要比對是否更新：`git -C <repo> fetch && git -C <repo> rev-parse origin/HEAD` 與記錄的 SHA 比對。
- **文章/網頁**：用 **存取日期（accessed）** 當版本；若有存檔快照（保存全文），加 **sha256(內容)** 以偵測內容變動。格式 `accessed:YYYY-MM-DD | sha256:<hash 或 n/a>`。
- **影片**：用 **videoId**（不變）+ **summary_captured 日期**；逐字稿存檔時加 sha256。

## 欄位語意（critical-thinking 列法）
每筆至少記：
- **裡面有什麼**（What's inside）：一句到數句，指名關鍵內容/可萃取物。
- **參考程度**（Reference degree）：以下分級
  - 🟢 **採用-核心**：直接成為我們架構/策略的核心（如 vectorbt、Minervini 8 條）
  - 🟡 **採用-萃取**：萃取其邏輯/公式/門檻後乾淨重寫（如 Magic Formula 公式、PKScreener VCP）
  - 🔵 **參考-架構**：參考其設計模式/思路，不取碼（如 ai-hedge-fund persona、TradingAgents 辯論）
  - ⚪ **僅情報**：知道它存在、評估過，暫不用（如 OpenBB、freqtrade）
  - 🔴 **不採用**：評估後排除（含原因，如 AI-Trader、pandas-ta）
- **採用/不採用原因**：為何。

## 搜尋框架（broad sweep 用）
排名訊號：⭐stars · 🍴forks · 📈star velocity（近期建立卻高星=上升）· 🔧維護(last push) · ⚖️寬鬆授權 · 🎯補缺口。Tier S=clone 研讀 / A=知道 / B=僅記錄。掃描法：未認證 GitHub Search API 按 topic + `sort=stars`／`created:>日期`（velocity proxy）。完整套用見 [repos.md](repos.md) §C。

## 相關工具文件
- 爬蟲技術選型：[../tech-selection-scraping-tools.md](../tech-selection-scraping-tools.md)（最大缺口＝文章正文抽取→trafilatura；Playwright 已裝）。
- 攝取/輿論 pipeline：[../ingestion-pipeline.md](../ingestion-pipeline.md)。

## 我們的 repo 位置
- 參考 repo clone 於專案外：`C:\Users\Romarin\Documents\Software Projects\_ref_repos\`（**20 個**，shallow，不在 git 內，研究完可刪）。新增 4 個 Tier-S：QuantResearch、Technical_Analysis_and_Feature_Engineering、ML_Finance_Codes、quant-trading。
- 各 repo 的**深度 code-level 評估**在 [../repo-evaluation.md](../repo-evaluation.md)；策略/投資者面在 [../research-inventory.md](../research-inventory.md)；資料源在 [../data-and-backtest-rigor.md](../data-and-backtest-rigor.md)、[../sentiment-and-market-analysis.md](../sentiment-and-market-analysis.md)；總報告在 [../00-executive-summary.md](../00-executive-summary.md)。

_最後更新：2026-06-14_
