# 萃取待辦清單（Extraction Backlog）

> 日期：2026-06-14。把已研讀的 gap-filling ref repo → 對映到 trading-analysis 要建的模組（萃取＝理解後乾淨重寫）。
> 授權：MIT/Apache 可帶 attribution 採用；**jo-cho 無 LICENSE → 僅參考，從 de Prado/mlfinlab/ta 上游重寫**。完整評估見 [repo-evaluation.md](repo-evaluation.md)、[refs/repos.md](refs/repos.md)。

## regime/（市場 regime，CANSLIM 的「M」）
| 萃取 | 來源 | 備註 |
|---|---|---|
| **200 日 SMA 趨勢 gate（主）** | QuantResearch `mebane_faber_taa.py:52` | 最簡單可辯護的「M」；對齊 Minervini「大盤確認上升」 |
| GaussianHMM + MarkovRegression 2-state（機率 overlay）| QuantResearch `hidden_markov_chain.py:79`、`gaussian_mixture_markov_switching.ipynb` | **必加**狀態標籤對齊（HMM state index 隨機）+ VIX/SMA 驗證（repo 沒做）；輸出 high-vol 機率當連續 risk-off |
| GARCH 條件波動 | QuantResearch `arima_garch.ipynb`（`arch`）| 第二 regime 特徵；AIC grid 要快取非 live 跑 |

## features/ + factors/
| 萃取 | 來源 | 備註 |
|---|---|---|
| **均值回歸包：Hurst / variance-ratio / half-life** | QuantResearch `mean_reversion.py:30-102` | 純 NumPy、零依賴、最易 lift |
| **Alphalens 因子驗證 harness（IC decay / 分位）** | QuantResearch `volume_factor_alphalens.ipynb` | 任何因子進回測前先過 IC 驗證 |
| 指標廣度（Donchian/Keltner/Ulcer/ADX/Vortex/CCI/Aroon/MFI/CMF/TSI/Williams%R/PPO…）+ **ADF stationarity 篩選** | jo-cho `tautil.py`（用 `ta` 庫）| 直接加 `ta`/pandas-ta 依賴，別手刻；只留 ADF 穩態者當 ML 輸入 |
| 微結構特徵（Corwin-Schultz spread、Amihud/Kyle λ、VPIN）| jo-cho `microstructure_features.py`（AFML Ch19）| OHLCV 衍生流動性因子；從 AFML 重寫 |
| MDI/MDA 特徵重要性 + >0.8 相關性剔除 | jo-cho（plain sklearn `feature_importances_`）| 加 per-tree mean±std + MDA(permutation) 更穩 |
| Fama-MacBeth 2-step 因子暴露 | QuantResearch `fama_french.ipynb` | 需基本面因子歸因時 |
| PCA eigen-factor / 統計風險因子 | ML_Finance `PCA-SP500.ipynb`、QuantResearch `ch1_pca` | 風險因子層 |

## labeling/（新模組 — ML/meta-labeling，我們完全沒有）
| 萃取 | 來源 | 備註 |
|---|---|---|
| **Triple-barrier 標記** | 從 de Prado AFML Ch3 / mlfinlab 重寫（jo-cho 只討論未實作）| **最高優先**：pt/sl + 垂直 barrier |
| **Trend-scanning 標記**（t-value = 樣本權重）| jo-cho `trend_scanning.py:32-99`（可移植）| 第二 labeler |
| **Purged + embargoed / Combinatorial Purged CV** | jo-cho `cross_validation.py`（優先用上游 mlfinlab/timeseriescv）| **必要**：重疊標記訓練防洩漏，配 vectorbt |

## strategy/rules/（新規則）
| 萃取 | 來源 | 備註 |
|---|---|---|
| **配對/共整合均值回歸**（EG 2-step + 滾動 z-score + 每步重檢共整合）| quant-trading `Pair trading backtest.py:64,108,157` | **最高價值**，我們沒有；移植數學、用滾動向量化取代迴圈 |
| Parabolic SAR 趨勢停損 | quant-trading `Parabolic SAR backtest.py:30,98` | ~30 行遞迴 |
| RSI 超買超賣 | quant-trading `RSI…backtest.py:60,86` | 可完全向量化 |
| Dual Thrust / opening-range 突破 | quant-trading `Dual Thrust backtest.py:43,128` | intraday |

## portfolio/（組合層，補 PyPortfolioOpt）
| 萃取 | 來源 | 備註 |
|---|---|---|
| SciPy 目標：GMV / max-Sharpe / max-diversification / **risk-parity** | QuantResearch `portfolio_optimization.py:43-58` | framework 無關，直接接 vectorbt sizing |

## backtest/ 嚴謹度
| 萃取 | 來源 | 備註 |
|---|---|---|
| **Walk-forward 最佳化迴圈**（每月重訓 + OLS baseline）| ML_Finance `Deep-Factor-Models.ipynb` `training()` | 時序 CV 嚴謹度 |
| NN 因子敏感度（解析 Jacobian → 可解釋 β）| 同上 `sensitivities()` | 可解釋因子暴露 |
| Omega/Sortino/MDD 指標參考 | quant-trading `Heikin-Ashi backtest.py:280,296,315` | vectorbt 外的 fallback |

## opinion/ + alt-data（insider / PEAD / events / 法說）— 三者皆 MIT
| 層 | 來源（重用度）| DuckDB 表 | 訊號 | `as_of` |
|---|---|---|---|---|
| **insider** | **edgartools 幾乎直接可用**：`Company(t).get_filings(form="4").obj().get_ownership_summary().to_dataframe(detailed=True, include_metadata=True)` → 每筆 txn（`Code` P=買/S=賣、Shares、Price、Date=txn、+`filing.filing_date`）| `insider_txns(ticker,insider,position,code,shares,price,txn_date,accession,as_of)` | **cluster buy**：滾動 30d 內 ≥N 位不同 insider 的 `Code='P'`，依 net_value 加權 | `filing.filing_date`（非 txn date）|
| **events** | edgartools `get_filings(form="8-K").obj()` → `CurrentReport.items`（item codes）、`.has_earnings_release` | `events(ticker,accession,item_code,has_press_release,as_of)` | 8-K item flag 當特徵/過濾（2.02 財報、5.02 高管異動）| `filing.filing_date` |
| **PEAD** | PEAD-Strategy 借**公式+漂移結構**，丟掉其 backtester（用 vectorbt）與付費分析師資料 | `earnings_surprise(ticker,fiscal_period,eps_actual,sue,as_of)` | SUE>上界做多/<下界做空、持有 ~60-85d 漂移。**SUE 改用時序版**（無付費）：`(EPS_q−EPS_{q-4})/σ(ΔEPS 近~8q)`，EPS 取自 edgartools XBRL `by_concept("EarningsPerShareDiluted")`、報酬取 yfinance | 8-K Item 2.02 `filing_date` |
| **opinion（法說）** | earningscall client 可用：`get_transcript(year,quarter,level)`，auth `ECALL_API_KEY`（預設 "demo"）。⚠️ **level-1 全文免費；level 2-4 speaker/Q&A 需付費** | `call_distill(ticker,year,quarter,tone,guidance_delta,risk_flags,as_of)` | Haiku 蒸餾語氣/guidance 變化當 overlay | `event.conference_date` |

**重用判決**：edgartools 最強（直接驅動 insider+events+PEAD 的 EPS，只缺 DuckDB upsert 包裝 + `set_identity(email)`）。PEAD-Strategy 只取 SUE 公式與漂移窗，backtester 丟棄、付費分母換時序 SUE。earningscall client 乾淨但只 level-1 全文免費（pipeline 要能降級到 level-1）。已 clone（共 23 ref repos）。

---

## 優先順序（建議實作序，全部只用現有 OHLCV/EDGAR/yfinance，零新成本）
1. `regime/` 200-SMA gate +（overlay）HMM — 解鎖 CANSLIM「M」
2. `labeling/` triple-barrier + purged CV — ML 基礎建設（沒有就別碰 ML）
3. `features/` 指標廣度 + 均值回歸包 + ADF 篩選
4. `strategy/rules/` 配對共整合 + Parabolic SAR + RSI
5. `factors/` Alphalens 驗證 harness（+ 既有 qlib Alpha158 移植）
6. `portfolio/` risk-parity 目標
7. alt-data：insider Form4 + PEAD（見 ⏳ 區）
