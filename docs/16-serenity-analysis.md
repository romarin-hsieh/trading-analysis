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

## 4. ✅ 已回測:他的 dated calls 前向報酬(事件研究,多代理對抗驗證)

`scripts/serenity_calls_backtest.py`:167 檔有價格的事件標的,「首次轉多」事件 → 美東時間**嚴格次一交易日收盤**進場 → +5/21/63 交易日報酬,**超額 = 減同視窗 QQQ**。決定性控制 = **隨機擇時 placebo**(同樣的股票、每檔 20 個隨機日期):

| 視窗 | n | 他的超額(均值/中位) | 勝率 | **placebo 超額** | **擇時差** | 真實值在隨機分布位置 |
|---|---|---|---|---|---|---|
| +5d | 166 | +0.3% / −0.8% | 46% | +1.8% | −1.5% | 第 14 百分位 |
| +21d | 166 | +5.2% / −1.0% | 46% | +6.1% | −0.9% | 第 47 百分位 |
| +63d | 156 | +10.7% / +1.4% | 52% | **+18.7%** | **−8.0%** | **第 4.6 百分位** |

**四個誠實結論**:
1. **正超額全來自「宇宙」,不是「擇時」**:隨機日期買進他的股票池,63 天贏 QQQ +18.7%——他的真實 call 時點反而只有 +10.7%,**顯著低於隨機**(部分因誤判產生的「遲到進場」,見 3)。跟單的價值=**他的選股宇宙**(光子/neocloud/記憶體鏈),不是他喊單的時機。
2. **顯著性經不起校正**:plain t=2.49 好看,但事件擠在同段牛市(29% 在 2026-01),**月度聚類校正後 t≈1.0-1.4、bootstrap P=0.06-0.17 → 與零無法區分**;且**前 5 個事件(AXTI +297%/SNDK +276%/AEHR +216%…)貢獻了 ~70-100% 的全部超額**,拿掉後均值 ≈0-2.6%、**中位數為負、勝率 46-52%——超過一半的 call 輸給 QQQ**,彩券型分布。
3. **關鍵字分類噪音大到不能歸因於「他」**:人工抽查 ~60% 的「轉多」標籤是誤判(「Never long though」被標多、清單文誤植、勝利回顧文比真 call 晚 2 個月→機械性壓低他的前向報酬)。已修一個真 bug(`tp` 匹配到 `http`,16.8% 含連結推文永遠不能標多);深層修復需 LLM 逐則分類(Haiku batch ~$1/月,已列升級路徑)。
4. **本研究測的是「次日收盤跟單買股」**——無法證實或證偽他自報的 +3,612%(那依賴選擇權/槓桿/盤中,不可觀測)。輸家名單提醒風險:SPRB −61%、BMNR −55%、MSTR −55%、KTOS −53%(即使在瘋牛期)。

> **一句話:跟單=買到一個(這一年)很強的宇宙清單,不是買到擇時能力;而且一半以上的個別 call 輸大盤,賺的錢集中在少數 moonshot。**⚠️ 他發文時已有倉位;你看到 thesis 時是他的 exit liquidity 候選人。追蹤=情報,不是訊號。

---
*Sources: [Substack 深析](https://singularityresearchfund.substack.com/p/inside-the-mind-of-serenity-aleabitoreddit) · [bearsavings 檔案](https://www.bearsavings.com/blog/who-is-serenity-aleabitoreddit/) · [檔案庫 repo](https://github.com/yan-labs/serenity-aleabitoreddit) · [semiconstocks tracker](https://semiconstocks.com/)。2026-06-19。*
