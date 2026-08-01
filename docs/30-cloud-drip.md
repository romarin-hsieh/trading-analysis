# 每日滴灌上雲評估:GitHub Actions × 免費資源(docs/29 u10 的結構性解法)

> 2026-08-01。觸發:使用者問「每日跑的內容是否可整合到 GitHub Actions,用免費資源完成?」
> 背景:本機滴灌無 OS 排程=會話停則滴灌停(7 月曾沉默停擺 10 天,損失 ~250 檔 AV 額度)。
> 結論:**核心每日額度捕捉(AV、Tiingo)可以、也應該上雲;關鍵約束不是算力(公開 repo
> Actions 免費無上限)而是「資料落點」的授權紅線——解法=私有資料 repo,順帶把 u9 備份
> 補成全綠、把 docs/27 §4 的 trading-data 中間層一併蓋掉。**

## 一、每日跑的內容 × 可搬性判定

| 項 | 頻率/額度 | 可搬? | 理由 |
|---|---|---|---|
| **AV earnings 滴灌** | 25 檔/日(當日不用即作廢) | ✅✅ **最高價值** | 時間敏感額度;跑一次 ~3 分鐘;資料增量 ~KB/日 |
| **Tiingo 小型股價格(p3)** | 45 檔/時、500 唯一檔/月 | ✅ | 每日 1 批(~3 分鐘)→ 11-12 天耗盡月額度=p3 兩個月無人職守收齊 |
| 選擇權 SPY/QQQ 快照、分析師、8-K、GDELT | 日/週 | ✅ 已在雲上 | 現有 monitor/weekly workflow,commit 到 `collected/`(git=異地備份) |
| FinMind 台股面板新鮮度 | 面板已收齊;未來週頻補新 | ✅ 選配 | 週頻 job 幾分鐘;非急 |
| **Theta 個股鏈** | — | ❌ 不可 | 需本機桌面終端+登入;雲上無解(docs/27 §2 的待決策項不變) |
| 重型 TR 執行 | 事件驅動 | 不需要 | 留在會話內(本來就是互動研究) |

## 二、兩個關鍵約束

1. **算力免費額度:非約束。** 本 repo 是 **public** → Actions 標準 runner **分鐘數免費無上限**。
   新增工作量 ≈ 6-8 分鐘/日,遠低於任何限制;現有兩個 workflow 已用同一額度跑一個月。
2. **資料落點=授權紅線(真正的設計約束)。** Tiingo/AV 條款禁止再散布其資料——**價格與財報
   面板不可 commit 進公開 repo**(現有 `collected/` 快照是小型衍生摘要,面板是另一回事)。
   解法:**私有資料 repo `trading-data`**(免費、僅本人可讀=個人使用非散布):
   - workflow 跑在**公開 repo**(分鐘無上限),用 fine-grained PAT 把私有 repo checkout 到
     `data/` → collector **一行不改**直接寫入 → commit+push 回私有 repo。
   - 副作用一:**u9 備份全綠**——`data/` 的雲端副本每日自動增長(本機碟損只損失未 push 的部分)。
   - 副作用二:docs/27 §4 的「trading-data 三層架構中間層」就此建成(架構文件的第 4 步)。
   - 副作用三:本機同步 = `git -C data pull`(data/ 種子化為私有 repo 的 clone 之後)。
   - 容量:種子 ~540MB+日增 KB 級,多年內遠低於 GitHub 建議上限;**不用 LFS**(避開其
     1GB/月頻寬帽,檔案本來就小)。

## 三、已建好的東西(未設 secrets 前為惰性 no-op,不會失敗轟炸)

- `.github/workflows/daily-drip.yml`:每日 09:10 UTC(台灣 17:10)——gate 檢查 secrets →
  checkout 公開 repo + 私有 data repo → AV 批 + Tiingo 小型股批(各自 `|| true` 容錯)→
  commit/push 私有 repo → 狀態摘要。
- `scripts/ops/sync_data.ps1`:本機一鍵拉下雲端最新 data(`git -C data pull --rebase --autostash`,
  含未種子化時的說明)。

## 四、一次性設定(需要你的帳號動作,~10 分鐘)

```
# 1. 建私有資料 repo
gh repo create romarin-hsieh/trading-data --private

# 2. 把本機 data/ 種子化為它的 clone(在 trading-analysis 目錄下)
cd data
git init -b main
git add -A
git commit -m "seed: local data layer 2026-08-01"
git remote add origin https://github.com/romarin-hsieh/trading-data.git
git push -u origin main
cd ..

# 3. 三個 secrets 加到「公開 repo」的 Actions secrets(stdin 輸入,不落任何檔案/畫面)
gh secret set DATA_REPO_TOKEN        # fine-grained PAT:僅 trading-data、僅 Contents RW
gh secret set ALPHA_VANTAGE_API_KEY
gh secret set TIINGO_API_KEY
```

註記:(a) PAT 用 fine-grained、單 repo、僅 Contents 讀寫,最小權限;(b) `data/` 本已被主
repo gitignore,巢狀 git 無衝突——唯 6 個被主 repo 追蹤的 `data/_*state*.json` 建議在遷移後
從主 repo `git rm --cached`(雲端狀態成為唯一事實來源,也順帶消除 monitor-bot rebase 時的
autostash 摩擦);(c) secrets 永不進程式碼、永不 echo——與現行 .env 紀律相同。

## 五、上雲後的分工

| 在雲上(無人職守) | 在本機(會話內) |
|---|---|
| AV 每日 25 檔、Tiingo 小型股每日 45 檔、快照四線、(選配)FinMind 週頻補新 | TR 執行、面板組裝、重型回測 |
| 私有 repo=data 的活備份 | `scripts/ops/sync_data.ps1` 拉最新再開工 |

## 六、為何不是 `investment-dashboard-data`(2026-08-01 深入評估,使用者提問)

實查事實:該 repo **PUBLIC**、已 **763MB**、根目錄 `.nojekyll` = **GitHub Pages 對外供檔**
(dashboard 的公開資料 CDN)、ETL 活躍。三個獨立否決:

1. **授權紅線(決定性)**:public+Pages 供檔=把 Tiingo/AV 授權資料架成公開 API;改私有
   則瀏覽器端 fetch 失效=弄壞現有 dashboard。
2. **容量與部署耦合**:763MB+540MB+每日二進位增長 → 逼近軟上限、拖慢 Pages 部署與 ETL;
   展示層 CDN(輕/快/穩)與原始庫(日增/偶爾重寫)生命週期相反。
3. **爆炸半徑**:drip bot 的 RW token 不應觸及公開展示內容——分倉=隔離故障域。

**正確的整併方向(使用者直覺的正確一半)**:沿「原始 vs 衍生」切——
`investment-dashboard-data` 是**衍生層 CDN**,應接收的是我們自產的 `exports/dashboard/*.json`
(無授權問題;即 docs/27 §4 dashboard 面板的資料端接線,可日後在 daily-drip 加一發佈步);
原始面板進**私有** `trading-data`。workflow 的目標 repo 已參數化(repo variable `DATA_REPO`,
預設 `romarin-hsieh/trading-data`)——選擇是設定,不是改碼。

*本文件為 u10 的結構性半解(額度捕捉線的心跳=workflow 失敗通知);完整心跳(所有資料源
新鮮度斷言)仍列 docs/29 u10。*
