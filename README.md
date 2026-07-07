# trading-analysis

**A side project that set out to find a money-printing trading strategy — and instead built a machine for honestly killing bad ones.**

*(English first; 繁體中文在下半部。)*

---

## English

### What this is

A personal research project. The naive starting question: *"Of all the trading strategies floating around the internet, papers, and guru books — which ones can still be arbitraged today?"* Using $0/month of free data (yfinance, SEC EDGAR, public archives), across 70+ commits and **~130 mechanisms/strategies tested**, the answer turned out to be more valuable than the question — because it turned *"what do we know, what don't we know, and how do we decide what's feasible"* into reproducible code and documents.

### What we built

1. **An acceptance framework ("fabric", [docs/17](docs/17-fabric-acceptance.md))** that codifies every mistake we made into rules: leak-free (F1), net costs (F2), investable benchmarks (F3), effective sample size (F4), multiple-testing (F5), control experiments (F6), sub-period stability with clustered t-stats (F7), calibrated verdicts (F8), **path randomization — assume you don't know the future** (F9), re-test policy on standard changes (F10). The framework itself was then **adversarially reviewed against the literature** (Harvey-Liu-Zhu, Arnott-Harvey-Markowitz protocol, de Prado, AQR/FIM trading costs, Cederburg, Lo, Shumway, Hoffstein) — producing v1.2 amendments that caught two critical flaws in *our own* flagship numbers, all since fixed and re-run.
2. **Fifteen standardized test reports** ([docs/tests/TR-01..15](docs/tests/)) covering statistical arbitrage, Markov regime-switching, PCA factor models, VaR, GBM Monte Carlo, CAPM, HRP, ML forecasting (GBM & Random Forest), Black-Scholes (N/A: no options data), LLM agent frameworks, bagged backtesting, rebalance-phase luck, delisting bias, effective samples, and cost stress — each with theory, assumptions, charts, PASSED/PARTIAL/FAILED verdict, decay estimate, failure attribution, and a **native-habitat declaration** ([docs/19](docs/19-mechanism-taxonomy.md)) so a FAILED verdict never over-claims beyond the seat it was tested in.
3. **Working infrastructure**: point-in-time data layer (DuckDB+Parquet; EDGAR aligned to filing dates), order-independent backtest engine (vectorbt), rigor modules (PSR/DSR/PBO/SPA), and daily Telegram monitors (multi-indicator exit votes + a social-signal tracker) on free GitHub Actions cron.

### What we now KNOW (reproducible evidence)

- **Selection alpha barely exists in free daily data.** Broad-market momentum is dead (ICIR≈0); value has been lost for a decade; PEAD/insider/operating-fundamental factors all failed; ML forecasters (GBM and RF) score OOS IC≈0 — the shuffled-label control actually beat the real model. The one robust cross-sectional signal: **gross profitability** (ICIR +0.30).
- **Timing to cash almost always subtracts.** Every cash gate — from the 200-day SMA to a walk-forward Hamilton Markov filter — lost to buy-and-hold, and the Markov gate's celebrated "MDD halving" was **fully reproduced by a constant 57% static exposure with zero model and zero trades** (Cederburg replicated).
- **The deliverable value is all in risk-shaping.** The 5-sleeve risk-parity combo is the one alpha claim that survived everything: **full-cost Carhart t=3.38 (2015-2026), above the Harvey-Liu-Zhu t≥3.0 bar, and t=3.14 even at 2× costs on every channel**; phase-immune (30bps timing-luck band); 2025 out-of-sample +27.9% with −5.7% MDD vs VOO's −18.7%. Honest caveats stay attached: the t-stat improved because the sample lengthened, and campaign-wide Bonferroni remains unresolved (trial registry lists both endpoints).
- **Point estimates lie.** Over 300 randomized 3-year windows the zoo's momentum table-topper beat equal-weight only 23% of the time (demoted to FAILED), while IBS mean-reversion survived at 66% (the only robust technical rule). Quarterly momentum's rebalance-phase luck spans **1,753 bps/yr** — the flagship's is 30 bps.
- **Most "it works" demos on the internet = beta + hindsight lists + ignored costs.** A hand-picked hot-stock list returned +62.8% in 2025 by itself; the overnight effect's gross Sharpe 0.89 became **−0.97** net. Survivorship inflation on our universe is an honest interval: **[+1.26%, +2.02%]/yr** (Shumway-bounded).

### What we know we DON'T know

Options (BSM/VRP) and intraday dimensions — no point-in-time free data, refused to fabricate; long-bear/rate-shock regimes (2015-2026 only had V-shaped crashes); unauditable track records (what we *can* test: copying a famous account's calls at next-day close has **no timing edge over random entries into the same names** — the universe intel is the value, not the timing).

### How we decide feasible vs. not

`idea → falsifiable claim first (F0) → the ten fabric rules → standardized TR → verdict into the registry (negative results kept) → any PASSED triggers adversarial multi-agent verification → standard changes trigger re-tests`. This loop caught **30+ genuine illusions** in our own work. See the [strategy registry (docs/18)](docs/18-strategy-registry.md) — PASSED 5 / PARTIAL 11 / FAILED 10 families.

### Directions that remain worth pursuing

1. **Productize risk-shaping** — the combo + leverage dial + monitors are daily-usable; wire the LLM layer as analyst/auditor (never as signal source).
2. **Data-dimension expansion** — the only path that could unlock new alpha: intraday, options chains, analyst revisions; any free PIT source re-opens the corresponding TR.
3. **Annual rituals** — re-run the OOS year-check, trade audit, and goal gates every January so conclusions update with data.

### Quickstart

```bash
uv sync --extra dev
uv run trading-analysis ingest --config configs/mvp.yaml   # ingest daily bars
uv run python scripts/validate_recommendation.py           # flagship combo, full rigor gates
uv run python scripts/tests/tr15_combo_cost.py             # cost-stressed flagship (t=3.38/3.14)
uv run python scripts/tests/tr11_bagged_backtest.py        # path-randomized evaluation demo
```

Architecture: UI (Streamlit) → CLI (Typer) → `trading_analysis.api` (only public surface) → core (data / models / strategy / backtest / portfolio / regime / factors / ml). Docs entry point: [docs/00-executive-summary.md](docs/00-executive-summary.md).

**License**: Apache-2.0 ([LICENSE](LICENSE)). Reference repos (design inspiration only, no code copied): Kronos, TradingAgents, ai-hedge-fund, OpenBB.

> **Disclaimer**: research/education only, not financial advice. Every backtest carries assumptions and limits; half this repo's value is writing those limits down.

---

## 繁體中文

### 這是什麼

一個個人研究專案。起點是一個樸素的問題:「網路上、論文裡、大師書裡那些交易策略,到底哪些今天還真的能持續套利?」我們用 $0/月的免費資料(yfinance、SEC EDGAR、公開檔案庫),在 70+ 次提交、**~130 個機制/策略的系統性測試**之後,答案比問題更有價值——因為它把「什麼是知道的、什麼是不知道的、如何判斷可行與不可行」變成了可重跑的程式與文件。

### 我們做了什麼

1. **建了一套驗收標準(fabric,[docs/17](docs/17-fabric-acceptance.md))**,把每一次踩坑法典化:無洩漏(F1)、淨成本(F2)、可投資基準(F3)、有效樣本量(F4)、多重測試(F5)、控制組(F6)、子期穩定+聚類 t(F7)、校準判定(F8)、**路徑隨機化——假設你不知道未來**(F9)、標準變更即複測(F10)。並用經濟學文獻與量化公司白皮書(Harvey-Liu-Zhu、AHM 回測協定、de Prado、AQR/FIM 交易成本、Cederburg、Lo、Shumway、Hoffstein)**對這套標準本身做對抗性審查**——v1.2 修訂案抓到我們自家旗艦數字的兩個 critical 缺陷,全部已修復並重跑。
2. **十五份標準化測試報告**([docs/tests/TR-01..15](docs/tests/)):統計套利、Markov 變異變遷、PCA 因子模型、VaR、GBM 蒙地卡羅、CAPM、HRP、機器學習預測(GBM 與隨機森林)、Black-Scholes(N/A:無選擇權資料)、LLM agent 框架、bagged 回測、再平衡相位運氣、下市偏誤、有效樣本、成本壓力——每份含理論、假設、圖表、PASSED/PARTIAL/FAILED 判定、衰退估計、失敗歸因,以及**原生棲地聲明**([docs/19](docs/19-mechanism-taxonomy.md)),讓 FAILED 判定永遠不會越過「被測座位」過度宣稱。
3. **能運轉的基礎設施**:point-in-time 資料層(DuckDB+Parquet;EDGAR 以揭露日對齊)、order-independent 回測引擎(vectorbt)、嚴謹度模組(PSR/DSR/PBO/SPA)、每日 Telegram 監控(五維出場投票+社群訊號追蹤),跑在免費 GitHub Actions cron 上。

### 我們現在「知道」的(可重跑的證據)

- **免費日線資料上幾乎不存在選股 alpha。** 廣市場動量已死(ICIR≈0)、價值失落十年、PEAD/內部人/本業因子全滅;ML 預測器(GBM 與 RF)的 OOS IC≈0——shuffled 控制甚至比真模型高。唯一穩健的橫斷訊號:**毛利/資產品質因子**(ICIR +0.30)。
- **擇時到現金幾乎總是減損。** 從 200 日線到 walk-forward Hamilton Markov 濾波,每一個現金 gate 都輸給買進持有;Markov gate 引以為傲的「MDD 減半」被**一個 57% 恆定曝險(零模型、零交易)完整複製**(Cederburg 重現)。
- **可交付的價值全在風險塑形。** 5-sleeve 風險平價組合是唯一全部存活的 alpha 宣稱:**全成本 Carhart t=3.38(2015-2026),越過 Harvey-Liu-Zhu 的 t≥3.0 標準;所有通道 2× 成本壓力下仍 t=3.14**;相位免疫(timing-luck 帶寬僅 30bps);2025 樣本外 +27.9%、MDD −5.7%(VOO 同期 −18.7%)。誠實 caveat 保留:t 值提升主因是樣本延長;全 campaign Bonferroni 仍未解(試驗登記簿兩端點皆列)。
- **點估計會說謊。** 300 個隨機 3 年視窗下,zoo 榜首的動量選股只有 23% 的時間贏等權(降級 FAILED),IBS 均值回歸以 66% 存活(唯一 robust 的技術規則);季度動量的再平衡相位運氣高達 **1,753 bps/年**——旗艦只有 30 bps。
- **網路上大多數「有效」示範 = beta + 事後清單 + 忽略成本。** 手挑飆股清單 2025 自己就 +62.8%;隔夜效應毛 Sharpe 0.89 → 淨 **−0.97**。倖存者膨脹的誠實區間:**[+1.26%, +2.02%]/年**(Shumway 定界)。

### 我們「知道自己不知道」的

選擇權(BSM/VRP)與日內維度——無 PIT 免費資料,拒絕編造;長熊/利率衝擊 regime(2015-2026 只有 V 型崩跌);不可稽核的他人績效(我們能測的部分:次日收盤跟單名人喊單,**對同一批股票的隨機進場沒有任何擇時優勢**——宇宙情報才是價值,擇時不是)。

### 我們如何判斷「可行 vs 不可行」

`想法 → 先寫可證偽宣稱(F0)→ fabric 十條規則 → 標準化 TR → 判定入註冊表(負結果也保留)→ 任何 PASSED 觸發對抗性多代理驗證 → 標準演進即複測`。這個迴圈在我們自己的工作裡抓出 **30+ 個真幻覺**。見[策略總註冊表(docs/18)](docs/18-strategy-registry.md)——PASSED 5 / PARTIAL 11 / FAILED 10 族。

### 值得繼續前進的方向

1. **風險塑形產品化**——組合+槓桿刻度+監控已可日常使用;LLM 層當分析員/稽核員接入(絕不當訊號源)。
2. **資料維度擴張**——唯一可能解鎖新 alpha 的路:日內、選擇權鏈、分析師修正;任一免費 PIT 來源出現即重開對應 TR。
3. **年度儀式**——每年一月重跑 OOS 年檢、出手審計與目標閘門,讓結論隨資料自動更新。

### 快速開始

```bash
uv sync --extra dev
uv run trading-analysis ingest --config configs/mvp.yaml   # 攝取日線
uv run python scripts/validate_recommendation.py           # 旗艦組合(完整嚴謹閘門)
uv run python scripts/tests/tr15_combo_cost.py             # 成本壓力後的旗艦(t=3.38/3.14)
uv run python scripts/tests/tr11_bagged_backtest.py        # 路徑隨機化評估示範
```

架構:UI(Streamlit)→ CLI(Typer)→ `trading_analysis.api`(唯一公開介面)→ core(data / models / strategy / backtest / portfolio / regime / factors / ml)。文件入口:[docs/00-executive-summary.md](docs/00-executive-summary.md)。

**授權**:Apache-2.0([LICENSE](LICENSE))。參考 repo(僅設計參考,未複製程式碼):Kronos、TradingAgents、ai-hedge-fund、OpenBB。

> **免責聲明**:僅供研究/教育,非投資建議。所有回測皆有其假設與侷限;本 repo 的一半價值正是把這些侷限寫成白紙黑字。
