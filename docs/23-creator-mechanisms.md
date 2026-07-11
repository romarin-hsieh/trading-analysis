# 內容創作者機制評估 — 四支 reel 的深入審視與行動(2026-07)

> 使用者供稿:四支 Instagram reel(特徵向量清理、量化迭代迴圈、選擇權流/訂單流看盤、吸收比率)。
> 紀律(同 [docs/21](21-paper-to-tr-pipeline.md) 管線精神):**創作者內容=機制線索,不是證據**。每個線索必須
> 對回主要來源(論文),經 F0 預先承諾進 fabric,判定寫入 [docs/18](18-strategy-registry.md)。
> 先前案例:Falak Khan/LSE(docs/13 §10)、Serenity(docs/16)。

## 總覽:四支 reel 的判讀與行動

| # | Reel 主題 | 主要來源 | 我們已有 | 真缺口? | 行動 |
|---|---|---|---|---|---|
| 1 | 特徵向量(方向)清理:LW 只修特徵值,錢其實流向雜訊特徵向量 | Bongiorno-Challet 2021 (k-BAHC);canonical 綜述=Bun-Bouchaud-Potters 2017(~900 引用) | LW 全域強制、TR-03 PCA、TR-03b(MP 譜+clipping)佇列、HRP(TR-07) | **是** — 我們的清理全在特徵值端 | **TR-03b 已執行(2026-07-09)**:BAHC PARTIAL——贏 naive 沒贏 LW,特徵向量清理在 vol 通道無增值;LW 慣例確認(見 TR-03b) |
| 2 | 量化迭代迴圈:生成→回測→ICIR 評分→讀失敗→再生成;訊號衰退檢查;OOS 閘門 | de Prado(CSCV/PBO)、White/Hansen(SPA)、HLZ | **幾乎全部已內建且更嚴**:trial-registry 記帳、DSR 吃真實 N、SPA、PBO、F9、凍結 holdout | 只有一小塊 | **IC 衰退半衰期**納入因子閘門(佇列,見 §2) |
| 3 | 選擇權流看盤(GEX 熱圖、net gamma、footprint、量/delta profile) | 無單一論文;GEX=從鏈上 OI×gamma 聚合 | TR-09 N/A(無 PIT 選擇權資料)、backlog「快照自建=時間敏感」 | **是** — 資料維度缺口 | **已啟動**:`scripts/collect/options_snapshot.py` + Actions cron(SPY/QQQ 每日,$0) |
| 4 | 吸收比率:top 特徵值吸收的變異占比=脆弱度,領先大跌 | Kritzman-Li-Page-Rigobon 2010/2011(JPM,>500 引用) | 無 | 可立即測 | **TR-21 已執行 → FAILED(本座位)**,見 §4 |

---

## §1 Reel 1:特徵向量清理 — 真缺口,TR-03b 擴充

**Reel 主張**(對回文獻後成立):最小變異組合要反轉共變異矩陣;反轉把特徵值變 1/λ,**最小的特徵值爆炸主導權重**;而那些小特徵值對應的**特徵向量**在原始矩陣裡與隨機洗牌無異(Bongiorno-Challet 的量測)。**Ledoit-Wolf 與所有標準收縮只重新縮放特徵值(修數字),不動特徵向量(不修方向)**——錢實際流向的方向沒被清理。他們的解法:資產聚類成區塊、塊內壓到平均相關、遞迴處理殘餘、拔靴平均(k-BAHC)。

**對照我們的現況**:LW 全域強制(對)、TR-03 PCA 因子共變異(特徵值端)、TR-03b 佇列(MP 譜+clipping——還是特徵值端)、HRP(TR-07,聚類但用於配置不是清理)。**確認:我們的清理工具箱全在特徵值端,特徵向量端是真空白。**

**誠實座位註記**:旗艦是 5 sleeve 風險平價(小 N),矩陣反轉的雜訊問題不 binding;這個機制的原生棲地是**大 N(數百檔)最小變異/最大分散組合**。我們的可測座位=47/465 檔股票面板的 min-var。

**行動(已執行 → TR-03b,2026-07-09)**:463 檔 min-var 競技場實測——**BAHC-lite PARTIAL**(14.1-15.5%,贏 naive/sample、沒贏 LW 13.2-14.2%;三個 lite 實作嫌疑被稽核反事實排除=真輸,結構原因是塊狀均勻化縮槓桿);clip≈LW 同族平手;**LW 全域慣例確認正確**。翻案=BAHC 的 max-Sharpe/均值通道(其原生 headline)、k>1 完整遞迴、GICS 先驗塊狀。詳見 [TR-03b](tests/TR-03b-covariance-cleaning.md)。

## §2 Reel 2:迭代迴圈 — 我們已有更嚴版本;唯一可取=IC 衰退半衰期

**Reel 主張**:單次回測=一次猜測;要迴圈(生成→回測→評分→讀失敗→再生成),用 ICIR 評分,檢查訊號衰退(2 天=噪音、50 天=可追蹤),最後 OOS 閘門。

**對照**:這正是本專案的核心主題——但 reel 版本**有毒的那一半**它自己也承認:「迴圈在同一份資料上優化=更快找到更漂亮的雜訊」。我們的 fabric 就是這個問題的完整解:**試驗登記簿把每次迭代計入 N**(DSR 吃真實 N)、SPA 全家族檢定、PBO/CSCV、F9 路徑隨機化、凍結 holdout。**ICIR 我們本來就是主要度量**(factors/validation.py)。結論:此 reel 對我們無新增,反而佐證 fabric 的設計動機。

**唯一可取的一小塊:訊號衰退半衰期作為正式閘門**。我們的因子閘門測多 horizon IC,但沒有正式的「**IC 半衰期 ≥ 成本回收 horizon**」判準(訊號衰退比成本回收快=付手續費追雜訊,呼應隔夜策略的成本牆教訓)。**行動(佇列)**:factor gate 加 IC(h) 衰退曲線擬合半衰期,與該 horizon 的來回成本比較;先跑 GP 品質因子與動量當示範。

## §3 Reel 3:選擇權流看盤 — 資料維度提醒,收集已啟動

**Reel 內容**是一個 orderflow 交易者的看盤配置(net GEX 熱圖、NDX/QQQ gamma exposure levels、footprint、量/delta profile),不是可證偽的機制宣稱。**對我們的價值=再次確認選擇權維度的資訊成本值得付**。

- **盤中 footprint/orderflow**:tick 級資料,$0 預算不可達 → 誠實維持 N/A(docs/19 翻案條件)。
- **GEX(dealer gamma exposure)**:可從**每日選擇權鏈快照**建(OI×gamma 按 strike 聚合);yfinance 免費(延遲)鏈完全夠日頻研究。**問題是歷史買不到、只能從今天開始存。**
- **行動(本輪已執行)**:`scripts/collect/options_snapshot.py` — SPY/QQQ 前 6 個到期日、每日收盤後 GitHub Actions 快照(~60KB/天,gzip CSV 進 repo `collected/options/`)。**這是一筆用時間支付的資訊成本**(G-S 紀律)。6-12 個月後的首批候選 TR:net-GEX 作為波動/釘住 regime 訊號(對 Nagel 三重對照)、VRP(隱含−實現)。

## §4 Reel 4:吸收比率 — 立即可測 → TR-21 已執行,FAILED(本座位)

**Reel 主張**(對回 KLPR 2010/2011 成立):AR=前 n/5 特徵值吸收的總變異占比;高 AR=市場緊耦合、一個衝擊會傳播;**AR 領先大跌**(最差月回撤都在 AR 尖峰後);且 AR≠平均相關(KLPR 案例:平均相關 0.36→0.32 下降、AR 0.55→0.80 飆升)。

**TR-21 實測**(465 檔現任 S&P、500 天窗、top 20%、2017-2025;F0 預先承諾三分規則,照字面執行):
- **C1 診斷 FAIL**:最差 10 個 SPY 月份**前一個月**的 AR 百分位中位數=44(置換 p=0.75)——AR 在本座位**不領先**大跌。
- **C2**:corr(AR, 平均成對相關)=+0.97——在個股面板上兩者幾乎是同一件事,reel 引的「相關看不到的它看得到」在本座位不成立。
- **C3 閘門 FAIL**:dAR>1 退場閘門 exSharpe 0.40/MDD −24.5%,**輸給恆定 69% 曝險(0.65/−24.2%)**與隨機閘門安慰劑 p95(0.90)——Cederburg/鐵律第三度重演(Markov、IBS 之後)。
- **判定:FAILED(本座位)**。棲地但書:KLPR 原生=~51 個**產業組合**×1998-2010(含 GFC 這種**內生槓桿累積**危機);我們的樣本只有外生衝擊(COVID)與利率衝擊,AR 的理論機制(內生耦合累積)在樣本裡沒有對應事件。**翻案條件=產業組合面板+含 2008 的長歷史(PIT 宇宙資訊成本)**。詳見 [TR-21](tests/TR-21-absorption-ratio.md)。
- **→ 翻案已執行(2026-07-11,TR-21b)**:KF 49 產業日頻 1970-2026 原生座位重測,稽核分裂判定——水位宣稱反轉(中位 37 百分位)、dAR>1 尖峰弱複製(7/10 vs 33%,suggestive p=0.02-0.034)、閘門第 5 次輸靜態(0.28 vs 0.46)。診斷具棲地特異性,AR 永不作閘門。詳見 [TR-21b](tests/TR-21b-absorption-native.md)。

## §5 元教訓

1. **Reel→主要來源→F0→TR 的管線在一天內、$0 成本下把一個「聽起來很有道理」的機制判成 FAILED**——這正是 fabric 存在的目的。四支 reel 只有一支(特徵向量清理)指到我們工具箱的真空白。
2. 創作者內容的系統性價值排序:**指出資料維度缺口(reel 3)> 指出方法論空白(reel 1)> 可立即證偽的機制宣稱(reel 4)> 流程勵志文(reel 2)**。
3. 與 [docs/22](22-paper-ledger-and-plan.md) 的整合:KLPR(TR-21 已執行)、Bun-Bouchaud-Potters 2017(wave-1/2 深讀)已入讀計畫;Bongiorno-Challet(引用 <500)以「TR-03b 擴充的實作參照」掛在 canonical 綜述之下,不單獨立項。

*2026-07-09。*
