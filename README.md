# trading-analysis

**A side project that set out to find a money-printing trading strategy — and instead built a machine for honestly killing bad ones.**

這是一個個人研究專案。起點是一個樸素的問題:「網路上/論文裡/大師書裡那些交易策略,到底哪些今天還真的能持續套利?」我們用 $0/月的免費資料(yfinance、SEC EDGAR、FRED、公開檔案庫),在 60+ 次提交、120+ 個機制/策略的系統性測試之後,得到的答案比預期更有價值——**因為它把「什麼是知道的、什麼是不知道的、如何判斷可行與不可行」變成了可重跑的程式與文件**。

## 我們做了什麼

1. **建了一套驗收標準(fabric)**,把每一次踩坑法典化成規則([docs/17](docs/17-fabric-acceptance.md)):無洩漏(F1)、淨成本(F2)、可投資基準(F3)、有效樣本量(F4)、多重測試(F5)、控制組(F6)、子期+聚類校正(F7)、校準判定(F8)、**路徑隨機化——假設你不知道未來**(F9)、標準變更即複測(F10)。並用經濟學文獻與量化公司白皮書(Harvey-Liu、AQR、Arnott-Harvey-Markowitz、de Prado、Frazzini-Israel-Moskowitz、Shumway、Lo)對這套標準本身做了**對抗性審查**(v1.2 修訂案在 §5——包括抓到我們自己旗艦結論的兩個弱點)。
2. **測了 120+ 個機制**:從 Minervini/CAN SLIM、Vegas 通道、動量突破、均線×成交量、季節性、統計套利 pairs、Markov regime、PCA 因子、VaR、Monte Carlo、CAPM、HRP、機器學習預測(GBM/RF)、到 LLM agent 框架——每個新機制一份標準化測試報告([docs/tests/TR-01~11](docs/tests/)),含定義/假設/論文出處、結果表、圖表、PASSED/PARTIAL/FAILED、衰退估計、失敗歸因、可組合性。
3. **建了可持續運轉的基礎設施**:point-in-time 資料層(DuckDB+Parquet;EDGAR 以揭露日對齊)、order-independent 回測引擎(vectorbt)、嚴謹度模組(PSR/DSR/PBO/SPA)、每日 Telegram 監控(五維出場投票 + Serenity 追蹤,GitHub Actions 免費排程)。

## 我們現在「知道」的(可重跑的證據)

- **選股 alpha 在免費日線資料上幾乎不存在**。廣市場動量已死(ICIR≈0)、價值失落十年、PEAD/內部人/本業因子全滅;唯一穩健的橫斷訊號是**毛利/資產品質因子**(ICIR +0.30)。ML(GBM/RF)預測器的 OOS IC≈0,shuffled 控制甚至比真模型高。
- **擇時到現金幾乎總是減損**。從 200 日線到 Hamilton Markov 濾波(最有理論根據的版本),每一個現金 gate 都輸給買進持有——V 型反彈的結構讓「賣在低點、錯過回升」成為常態。regime 辨識是**真的**(波動聚類存在),但波動預測≠報酬預測。
- **可交付的價值全在「風險塑形」**:5-sleeve 風險平價組合(Carhart alpha t=2.64,**v1.2 改標 PASSED-borderline**,因 t<3.0)、回撤預算/槓桿刻度(選你能忍的 MDD 讀出配置)、規則投票 ensemble(holdout 勝樣本內最佳單規則 0.99 vs 0.63)。2025 樣本外:組合 +27.9%、MDD −5.7%(vs VOO +17.8%、−18.7%)——**行為如設計,但別把單年當證據**。
- **點估計會說謊**:300 個隨機 3 年視窗下,zoo 榜首的動量選股 P(beat 等權)=23%(降級 FAILED),IBS 均值回歸 66%(唯一 robust-PASS 的技術規則)。**單一起點的回測=抽一張路徑運氣牌。**
- **絕大多數網路策略的「有效」= beta + 事後清單 + 忽略成本**。手挑飆股清單等權持有 2025 +62.8%——那是選股偏誤,不是策略;隔夜效應毛 Sharpe 0.89 → 淨 **−0.97**(成本牆)。

## 我們現在「知道自己不知道」的

- **選擇權維度**(BSM/VRP/gamma):無 PIT 免費資料,拒測(TR-09 N/A)。
- **日內維度**(ORB 等):同上。這兩個是「可能還有真 alpha」但我們觀測不到的地方。
- **長熊市/利率衝擊 regime**:2015-2026 只有 V 型崩跌;防禦機制的普遍性宣稱須以長歷史重放佐證(F7 v2)。
- **他人的不可稽核績效**(Serenity +3612%、agent 框架 demo):無法證實也無法證偽——我們能測的是「凡人可複製的部分」,結論是宇宙情報有價值、擇時跟單無 edge。

## 我們如何判斷「可行 vs 不可行」(方法論本身即產出)

`新想法 → 先寫可證偽宣稱(F0)→ fabric 十條規則 → TR 報告 → 判定入註冊表(負結果也入)→ 任何 PASSED 觸發對抗性多代理驗證 → 標準演進即複測`。詳見 [docs/18 註冊表](docs/18-strategy-registry.md)(PASSED 5 / PARTIAL 11 / FAILED 10 族)與其 §4 持續迴圈。這套流程在本專案抓出 **30+ 個真幻覺**(排序相依 artifact、CV 洩漏、倖存者 +126bps、t 值灌水 3.7×、beta 假裝 alpha……)。

## 收束:值得繼續前進的方向

1. **風險塑形產品化**:組合 + L 刻度 + 監控管線已可日常使用;接 dashboard 的 LLM 敘事層(agent 當分析員/驗證員,不當訊號源)。
2. **資料維度擴張**(唯一可能解鎖新 alpha 的路):日內、選擇權鏈、分析師修正——任一有免費/低價 PIT 來源出現即重啟對應 TR。
3. **fabric v1.2 backlog**:rf=BIL 全面重算 Sharpe、成本曲線/2× 壓力欄、再平衡相位平均、下市終端報酬——標準先行,重跑在後。
4. **年度儀式**:每年重跑 OOS 年檢 + 出手審計 + 閘門測量,讓結論隨資料自動更新。

## Quickstart

```bash
uv sync --extra dev
uv run trading-analysis ingest --config configs/mvp.yaml   # ingest daily bars
uv run python scripts/validate_recommendation.py           # the flagship combo, full rigor gates
uv run python scripts/tests/tr11_bagged_backtest.py        # path-randomized evaluation demo
uv run python scripts/gate_3x_voo.py                       # the goal-gate measurement
```

架構:UI(Streamlit)→ CLI(Typer)→ `trading_analysis.api`(唯一公開介面)→ core(data / models / strategy / backtest / portfolio / regime / factors / ml)。文件入口:[docs/00-executive-summary.md](docs/00-executive-summary.md)。

## License

Apache-2.0. See [LICENSE](LICENSE). Reference repos(僅設計參考,未複製程式碼):Kronos、TradingAgents、ai-hedge-fund、OpenBB。

> **Disclaimer**: research/education only, not financial advice. 所有回測皆有其假設與侷限;本 repo 的一半價值正是把這些侷限寫成白紙黑字。
