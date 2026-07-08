# TR-22 — 旗艦 combo 家族的 CSCV/PBO(docs/20 點名的缺口)

> 腳本:`scripts/tests/tr22_combo_pbo.py` · 對抗稽核:兩個 CONFIRMED-BUG 已修(inverse_vol
> 零波動處理、稻草人組成),分層 PBO 已實作。

## 判定:**F0 家族 PBO = 24.5%(<30%,CREDIBLE)——但分層檢視後的誠實操作結論:配置器不是 edge,RP/IV/EW-of-sleeves 近乎可互換(DGU)。**

**問題**:從配置器×sleeve 集家族裡挑出「risk-parity 5-sleeve」當旗艦,是不是過擬合的選擇?
**家族**:{equal-weight, risk-parity, inverse-vol, min-variance} × {5s, 4s-無槓桿, 4s-無黃金}
= 12 configs,日報酬 2015–2026,CSCV S=16(C(16,8)=12,870 個對稱分割)。

## 分層 PBO(稽核修正後)

| 層 | PBO(IV=renorm) | PBO(IV=limit) |
|---|---|---|
| L1 宣告家族(12,F0 headline) | **24.5%** | 30.6% |
| L2 剔除 min-variance 稻草人(9) | 41.8% | 47.8% |
| L3 決賽圈 RP/IV/EW × 5-sleeve(3) | 27.4% | 88.8% |

- **L1 24.5% < 30%**:照 F0 預先承諾規則=CREDIBLE。但稽核證明這個數字**一半在測「min-variance
  一直很爛」**(它只在 19/12,870 個分割裡是 IS 最佳)——稻草人壓低 PBO。
- **L2(認真候選人)41.8–47.8%**:配置器的選擇**部分是運氣**;與 DGU(優化器很難贏 1/N)一致。
- **L3 對 IV 慣例極敏感(27%→89%)**:RP 對 IV 的全樣本 Sharpe 差距僅 0.01,在一天訊號延遲的
  慣例雜訊之內(稽核:給 IV 同樣延遲會翻轉排名)。**不再報「第一名 config」。**

## 兩個 CONFIRMED-BUG(已修)

1. **inverse_vol 零波動處理**:原 fillna 讓零波動(死)sleeve 拿 1/N 權重、活 sleeve 全歸零
   (inf/inf=NaN 假象),205 天變相持現金——未宣告的規則值 ~0.12 Sharpe(比 RP-IV 差距大一個
   量級)。已改為明文規則(死 sleeve 剔除、活 sleeve 重正規化)+ 權重和斷言,limit 慣例列為敏感度。
2. **家族組成**:分層報告取代單一數字(見上表)。

## Alpha 宣稱不受影響(稽核確認)

Carhart alpha 對**每個**配置器都存在:EW-5s t=2.92、IV 3.32、RP 3.44、連 MV 都 2.16(日頻;
TR-18 月頻 caveat 全部適用)——alpha 是 sleeve 組合的性質,不是配置器的性質。**EW-of-sleeves
是配置器無關的誠實地板。**

*2026-07-09。F5 經驗法則(<30% 可信/>50% 雜訊)首次正式應用於旗艦家族。*
