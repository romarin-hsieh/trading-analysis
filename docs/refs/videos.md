# REF：影片 / 逐字稿

> 版本＝videoId（不變）+ summary_captured 日期；逐字稿存檔時加 sha256(transcript)。
> 這裡也是未來**財經 YouTuber 逐字稿萃取 pipeline** 的落點（見下方 §C schema）。

## A. 已摘要的影片（研究來源）
| videoId | 標題（推定）| 語言 | summary_captured | 程度 | 裡面有什麼 / 用途 |
|---|---|---|---|---|---|
| `WJClXWVUyUw` | 從零打造 AI 投資團隊！ai-hedge-fund 專案解析，本地 LLM 也能跑 | zh | 2026-06-14 | 🔵參考-架構 | 多代理 LLM 投資、19 persona、本地 Ollama → 餵入 ai-hedge-fund 評估 |
| `9ZrX-fcVXrM` | Kronos：專為 K 線設計的金融大模型，實測 A 股回測績效 | zh | 2026-06-14 | 🔵參考-選配 | Kronos 介紹、OHLCV 專用基礎模型 → 餵入 Kronos 評估 |

## B. 概念參考（非單一影片）
- **finfluencertracker.com**（邀請碼 BETA-ZAQ995）：追蹤財經創作者 calls + 回測勝率（WLO/LO/LS 報酬、Win Rate、Sharpe、Beta、MDD、Volatility、Positive-Bias、YOLO/heating stocks）。**我們要復刻此概念**成自己的 YouTuber pipeline（見 §C）。詳見 [articles.md](articles.md) E 區。

## C. 財經 YouTuber 逐字稿 pipeline（落點 schema，⏳ 由 workflow 設計中）
> 目標：每日 1-2 次掃描追蹤頻道是否有新片 → 抓逐字稿 → LLM 萃取關鍵段落與其市場看法、買賣點位 → 加入「專業投資人觀點」層 → 餵 dashboard。這正是可高速回測的內容（像 finfluencertracker 那樣算勝率）。

**每部影片預計記錄欄位**（待 pipeline 落地後自動寫入）：
```
video_id, channel_id, channel_name, creator_type,        # 創作者類型（短線/長線/價值/動能…）
published_at, captured_at, transcript_sha256,
calls: [ { ticker, stance(buy/sell/hold/trim),
           entry_zone, exit_zone, stop, conviction(0-1),
           timeframe(short/swing/long), rationale_excerpt } ],
market_view_summary,                                      # 對大盤/板塊的看法
backtest: { wlo_return, lo_return, ls_return, win_rate, sharpe, mdd }  # finfluencer 式回測
```

**追蹤的創作者清單**（待使用者提供；先放結構）：
| channel | type | 追蹤 RSS | 備註 |
|---|---|---|---|
| （待填）| | `youtube.com/feeds/videos.xml?channel_id=…` | |

> 註：技術選型（新片偵測 RSS vs API、逐字稿 youtube-transcript-api/Whisper、LLM 萃取成本、finfluencer 式回測法）由背景 workflow 回來後補進 [../ingestion-pipeline.md](../ingestion-pipeline.md)（待建）。

_最後更新：2026-06-14_
