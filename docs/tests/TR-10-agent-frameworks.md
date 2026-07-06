# TR-10 LLM Agent 交易框架(TradingAgents / hermes / OpenBB / bullgpt / hyperliquid-agent)— 質性評測

## 1. 機制定義與理論
「多代理投研桌」:用 LLM 代理分飾分析師/多空研究員/交易員/風控/基金經理,對單一標的辯論後產出裁決(如圖示的 gobi_automates 流程:7 analysts → bull vs bear debate → trader → risk → verdict)。理論依據是**任務分解+對抗性辯論降低單模型幻覺**;無定價理論基礎。出處:[TradingAgents](https://tradingagents-ai.github.io/)(TauricResearch)、[hermes](https://github.com/schnetzlerjoe/hermes)、[OpenBB](https://github.com/OpenBB-finance/OpenBB)(資料平台非策略)、bullgpt.io(商用包裝)、[hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent)(加密永續)。

## 2. 相關既有機制
docs/repo-evaluation.md 已評 ai-hedge-fund/TradingAgents/Kronos(結論:**headline 數字全部禁不起嚴格回測**);docs/16 Serenity(人肉版供應鏈代理);我們的多代理**用法差異**:本專案把 agent 用在「對抗式驗證」而非「產生訊號」——這正是這類框架缺的那一半。

## 3. 預期目標
框架宣稱:辯論後的裁決比單模型/買進持有有更好的風險調整報酬(TradingAgents 論文自報 Sharpe 提升)。

## 4. 測試設計
質性評測 + 依 fabric 判斷可測性:這類框架的輸出**不可重現**(同 prompt 不同次輸出不同、模型版本漂移、資料快照非 PIT),違反 F1(不可凍結的訊號)與 F4(無法生成 3000 個獨立可重播事件)。要合規需:凍結模型+凍結資料快照+數千次成本高昂的重播——超出預算。故以架構審查+文獻/自報數字檢核代替。

## 5. 結果(質性)
| 框架 | 定位 | 判讀 |
|---|---|---|
| TradingAgents | 學術多代理辯論 | 自報回測期短(數月)、無成本/滑價敏感度、無 PIT 保證;**展示≠edge** |
| hermes | 個人投研 agent | 工程 scaffold,無驗證層 |
| OpenBB | **資料/終端平台** | 非策略;是唯一直接可用的——當免費資料源與 CLI(工程價值高) |
| bullgpt.io | 商用訂閱 | 無可稽核 track record;行銷面大於證據面 |
| hyperliquid-agent | 加密永續執行 bot | 市場外(加密+槓桿永續),超出本專案範圍 |

## 6. 判定:**PARTIAL(工程價值)/ FAILED(alpha 宣稱)**
作為**流程自動化**(資料彙整、報告生成、對抗驗證)PARTIAL-有價值——本專案 60+ commits 的多代理驗證就是證明;作為 **alpha 來源** FAILED——LLM 讀的是公開資訊(價格/新聞/財報),資訊集合不優於市場,且輸出不可重現、不可通過 F1/F4/F6。與 docs/12 結論一致:**瓶頸是資料不是方法**,換成「會說話的方法」不改變資訊集合。

## 7. 衰退評估
無「衰退」可言——從未有可稽核的正 alpha 基線。TradingAgents 類自報數字屬 in-sample 展示(與 Kronos headline 同類,docs/repo-evaluation 已證偽同型宣稱)。

## 8. 失敗/侷限歸因
(a) 資訊集合不變,包裝改變;(b) 不可重現→不可驗證→不可信任;(c) 成本:每裁決數萬 token,對日頻組合是真實費用;(d) 幻覺風險在長鏈條辯論中放大。

## 9. 可組合性
**正確用法(本專案已在做)**:LLM agent 做「驗證者/稽核者/報告員」——對抗式攻擊回測(抓了 30+ 真錯誤)、Serenity 推文分類升級(docs/16 的 LLM 分類路徑)、dashboard 敘事層(V1 LLM 規劃)。**不要用**:讓 agent 直接產生買賣訊號進 combo。OpenBB 可納入資料層擴充候選。
