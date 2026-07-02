# Serenity (@aleabitoreddit) 剖析 + 追蹤機制

> /goal part 3(2026-06-19):剖析其可能的進出場與選股策略,設計追蹤發文/進出場的機制與通知。
> 工具:`scripts/notify/serenity_tracker.py`(已跑通,live 資料)+ `.github/workflows/monitor.yml`(Telegram 排程)。

## 1. 身分與可信度(誠實檔案)

- **身分**:前 Reddit WSB 交易員(u/AleaBito),自稱前 AI research scientist / RISC-V 基金會成員 / 光子學背景、拒絕 NVIDIA offer;X 追蹤 ~90 萬。**完全匿名**。
- **績效**:自報 2026 YTD +3,612%(槓桿、選擇權)。**全部自報、無第三方審計**。他有一點值得肯定:**事前給明確倉位**(non-retroactive),留下可稽核的 paper-trail。
- ⚠️ **誠實警告**:匿名+自報+高槓桿+選擇權=不可驗證的 track record。**追蹤他的價值在「資訊速度與供應鏈視角」,絕不在「複製倉位」。**

## 2. 策略解剖(從 5,959 則推文檔案 + 公開分析)

**核心方法 = Chokepoint Theory(供應鏈瓶頸理論)**:不買明星股,而是往上游追,找「hyperscaler 不計代價也要維持供應」的**獨佔/寡佔節點**,在機構輪動之前建立不對稱倉位。

**實際宇宙(檔案庫 673 個 ticker,前 30 名 mention)**:

| 鏈環 | 代表標的(mention 數) |
|---|---|
| Neocloud/算力租賃 | **NBIS(865,第一名)**、IREN(554)、CIFR(202)、CRWV(227) |
| 光學/光子(他的本業) | LITE(643)、AAOI(501)、COHR(260)、POET(170)、AXTI(612)、IQE(203)、SOI(171)、TSEM(128) |
| 記憶體/儲存 | MU(168)、SNDK(142)、WDC |
| 大盤錨 | NVDA(498)、GOOGL/MSFT/META/AMZN/TSM |
| 其他高 beta | RKLB(161)、HIMS(171)、HOOD(168)、RDDT(140) |

**進出場模式(從發文行為推斷)**:
- **進場**:供應鏈調研先行(產能/交期/單一供應商認證)→ 在「還沒有 narrative」時建倉 → 公開 thesis(此時他已有倉位——注意這個利益結構)。分批加碼於回檔。
- **出場**:thesis 實現(機構輪動進來、估值 catch-up)或 thesis 破壞(供應瓶頸解除/第二供應商認證)。也做**選擇權賣方 swing**(他發過 $1M 帳戶 5 天 $20k 的 sell-side 策略)。
- **風格標籤**:中線(1-6 個月)事件/基本面驅動 + 高集中 + 槓桿;**不是**技術指標交易者。

**與你的關聯**:你的 137 檔清單與他的宇宙高度重疊(RKLB/ASTS/OKLO/IONQ/CIFR/IREN/WULF/HUT/CRWV/LEU/SMR/MU/SNDK/HIMS/HOOD…)——你實際上已在追蹤他的影響圈。docs/13 §11 的教訓直接適用:**他的清單=高波動火箭池,規則疊加只會減分,分散+倉位控制才是正解。**

## 3. 追蹤機制(已建成,$0)

**資料源**:X API 要 $200+/月(超預算)、nitter 鏡像不穩 → 用**公開檔案庫** [yan-labs/serenity-aleabitoreddit](https://github.com/yan-labs/serenity-aleabitoreddit)(5,959 則推文 CSV,含 id/時間/全文/互動數,持續更新)。代價:**通知延遲取決於檔案庫刷新頻率**(非即時)。

**管線**(`scripts/notify/serenity_tracker.py`):
```
fetch 檔案庫 CSV → diff 上次已見 id(data/_serenity_seen.txt)
→ 新推文抽取 $TICKER + 方向詞(long/buy/adding/calls vs sold/trim/exit/puts/short)
→ Telegram 推播(--analyze 模式:全檔案 ticker 統計/首末見/方向計數)
```

**通知**:`.github/workflows/monitor.yml` 每交易日收盤後跑(同時跑五維止損監控),推 Telegram。Cowork 對比:claude.ai 排程任務可做同樣分析但非 $0 且不適合無人值守推播;**GitHub Actions cron + Telegram Bot 是免費穩定解**。設定只需三步:BotFather 建 bot → repo secrets 放 `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` → variables 放 `PORTFOLIO`。

## 4. 後續(誠實優先序)

1. **回測他的 calls**(檔案庫有帶日期的 track-record + 每則推文時間戳):抽「首次轉多」事件 → 事件後 21/63d 前向報酬 vs 同期 QQQ——把「跟單有沒有用」變成可量測的數字。這是最有價值的下一步。
2. 方向詞抽取可升級 LLM 分類(Haiku batch,~$1/月),誤判率會顯著下降。
3. ⚠️ 永遠記住:他發文時**已有倉位**;你看到 thesis 時是他的 exit liquidity 候選人。追蹤=情報,不是訊號。

---
*Sources: [Substack 深析](https://singularityresearchfund.substack.com/p/inside-the-mind-of-serenity-aleabitoreddit) · [bearsavings 檔案](https://www.bearsavings.com/blog/who-is-serenity-aleabitoreddit/) · [檔案庫 repo](https://github.com/yan-labs/serenity-aleabitoreddit) · [semiconstocks tracker](https://semiconstocks.com/)。2026-06-19。*
