# REF：文章 / 網頁 / 論文 / 文件

> 版本＝存取日期（accessed）；有存檔快照才加 sha256。非窮舉每個 URL，記載**承重來源**與其用途。
> 程度分級見 [README.md](README.md)。

## A. 學術論文（策略量化基礎）
| 來源 | URL | accessed | 程度 | 用途/裡面有什麼 |
|---|---|---|---|---|
| Buffett's Alpha (Frazzini/Kabiller/Pedersen) | SSRN 3197185 | 2026-06-14 | 🔵 | 把 Buffett 拆解成 QMJ+BAB+槓桿 |
| Quality Minus Junk (Asness/Frazzini/Pedersen) | SSRN 2312432 | 2026-06-14 | 🟡 | QMJ 因子定義（獲利/成長/安全/配息）→ 我們自建 |
| Fama-French 5-factor | tevgeniou.github.io/.../FiveFactor.pdf | 2026-06-14 | 🟡 | 因子定義（Mkt/SMB/HML/RMW/CMA）+Carhart 動能 |
| Deflated Sharpe Ratio (Bailey/López de Prado) | SSRN 2460551 | 2026-06-14 | 🟢 | 回測 scorecard #5：多重檢定調整 |
| Kronos | arXiv 2508.02739 | 2026-06-14 | 🔵 | 基礎模型；headline 數字存疑 |

## B. 資料源文件
| 來源 | URL | accessed | 程度 | 用途 |
|---|---|---|---|---|
| SEC EDGAR companyfacts/frames API | sec.gov/search-filings/edgar-application-programming-interfaces | 2026-06-14 | 🟢 | **美股基本面主源**（point-in-time，filed 日） |
| Alpha Vantage NEWS_SENTIMENT | alphavantage.co/documentation | 2026-06-14 | 🟢 | 情緒主源（內建分數+時戳，25/日） |
| FinMind | github.com/FinMind/FinMind | 2026-06-14 | 🟢 | 台股價格+基本面+籌碼 |
| Financial Modeling Prep (FMP) | site.financialmodelingprep.com/pricing-plans | 2026-06-14 | ⚪ | 基本面便利 fallback（非 point-in-time） |
| Ken French Data Library | (Dartmouth) | 2026-06-14 | 🟡 | Fama-French 因子歷史資料 |
| Shiller CAPE 資料 | shillerdata.com | 2026-06-14 | 🟡 | 市場估值 overlay |

## C. 策略 / 指標參考
| 來源 | accessed | 程度 | 用途 |
|---|---|---|---|
| Minervini Trend Template（8 條）/ SEPA / VCP | 2026-06-14 | 🟢 | 第一個要實作的策略 |
| Greenblatt Magic Formula（magicformulainvesting.com / AAII #46）| 2026-06-14 | 🟡 | 價值對照組 |
| CAN SLIM（AAII screen / IBD）| 2026-06-14 | 🟡 | C/A/L/S/I 門檻 |
| McClellan / Zweig / %-above-MA（StockCharts ChartSchool）| 2026-06-14 | 🟡 | 市場廣度公式 |
| Follow-through / Distribution day（QuantifiedStrategies/TraderLion）| 2026-06-14 | 🟡 | regime「M」引擎 |
| Graham（Graham Number/NCAV/防禦型 7 條）| 2026-06-14 | 🟡 | 價值篩選 |
| 獨立評論：Kinlay 對 Kronos 的批評 | 2026-06-14 | 🔵 | 佐證 Kronos 當選配 |

## D. USIC 冠軍（真實對帳報酬）
| 來源 | accessed | 程度 | 用途 |
|---|---|---|---|
| BusinessWire/PRNewswire USIC 年度新聞稿（2021-2025）| 2026-06-14 | 🔵 | 冠軍報酬/策略；佐證 Minervini/CANSLIM 收斂 |

## E. 爬蟲/自動化工具（已由 workflow 摘要；詳見 [../ingestion-pipeline.md](../ingestion-pipeline.md) §4）
| 來源 | URL | 程度 | 裡面有什麼 / 結論 |
|---|---|---|---|
| Medium GraphQL + 突破 Cloudflare（zhgchg.li）| zhgchg.li/.../medium-api-...graphql...88f0fb935120 | 🟡採用-萃取 | Medium 私有 GraphQL `medium.com/_/graphql`；雲端 IP 會被 Cloudflare 403 → **經 Cloudflare Worker proxy** 解。**採用為 Tier 2 Medium 爬法** |
| browse.sh / Browserbase CLI（blocktempo）| blocktempo.com/browse-sh-browserbase-cli-... | ⚪僅情報 | AI agent 驅動瀏覽器 + 500+ skill；Browserbase 免費 1hr/月。當 Tier 3 緊急 fallback |
| 工具清單（beebag）| beebag.com.tw/good.html | ⚪僅情報 | 推 **Playwright**(>Selenium，~95% 成功) + 從 Playwright 取 cookie 後用 requests 輕量下載 |
| **finfluencertracker.com**（概念，邀請碼 BETA-ZAQ995）| finfluencertracker.com | 🟡概念採用 | 創作者 call 追蹤+回測勝率（WLO/LO/LS/Win/Sharpe/MDD/Beta/YOLO/heating）。**復刻此概念**到 YouTuber pipeline（[../ingestion-pipeline.md](../ingestion-pipeline.md) §3） |

### E-2 爬蟲/工具 landscape（workflow 盤點）
| 工具 | 模式 | 費用 | 程度 | 一句話 |
|---|---|---|---|---|
| **r.jina.ai (Jina Reader)** | SaaS+OSS | 免費無 key | 🟡採用 | URL 前綴得乾淨 Markdown，從自身 IP 抓繞過封鎖 → **Tier 1 主抓取** |
| **Crawl4AI** | OSS 自架 | 免費(MIT) | 🟡採用 | 乾淨 Markdown for RAG，Actions 原生 → Tier 1 |
| **Cloudflare Worker proxy** | 自架 | 免費 100k/日 | 🟡採用 | Medium/Cloudflare 繞 403 → Tier 2 |
| **feedparser (RSS)** | OSS | 免費 | 🟢採用-核心 | Tier 0：新聞/Medium/YouTube RSS 偵測 |
| Apify | SaaS | $5 credits/月免費 | ⚪→Tier3 | 現成 actors |
| Camoufox / agent-browser | OSS 自架 | 免費 | ⚪→Tier3 | 最佳免費 stealth / 本地 fallback |
| FlareSolverr | OSS 自架 | 免費 | ⚪僅情報 | Cloudflare JS 挑戰；對 Turnstile 失效、漸沒落 |
| Playwright(+stealth)/Camoufox | OSS 自架 | 免費 | ⚪僅情報 | JS-heavy 站工作馬 |
| Firecrawl / ScrapingBee / Bright Data | SaaS | $16 / $49 / $499 | 🔴不採用 | **超預算** |

### E-3 排程/自動化（workflow 盤點）
| 選項 | 程度 | 結論 |
|---|---|---|
| **GitHub Actions cron** | 🟢採用-核心 | 編排器；public repo 免費無上限；觸發 best-effort（避 `:00`，加 `workflow_dispatch` fallback） |
| 家機/Pi（Whisper/Ollama）| 🟢採用 | 持久工作的免費溢位 worker |
| Cloudflare Workers Cron | ⚪僅情報 | 10ms CPU 只能當 pinger |
| Claude Code Routines(雲)/排程 | ⚪僅情報 | 機器可關但綁訂閱用量；當分析 brain 非排程器 |
| **Obsidian / NotebookLM 自動化** | 🔴不採用(當手動輔助) | NotebookLM 無穩定 API、Obsidian 外掛需 app 開著 → **不能當 cron 引擎**，只當研究輔助/知識庫 |

_最後更新：2026-06-14_
