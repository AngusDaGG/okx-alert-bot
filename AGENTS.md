# Agent 操作入口

## 共用開發流程

此段為遠端也可讀取的核心契約；保留上方專案特定限制。

- 使用 Codex 與 GitHub 原生功能；不依賴 Dispatcher／Runner、codex-ready、自製 AI Risk／Merge Gate 或獨立 Reviewer 服務。Issue 依規模決定，可多次 Commit；每項開發任務先完整 Diff、相關測試及自我 Code Review，再交付 Draft PR，低風險也不能省略 Draft。
- Draft 階段跑必要 CI，失敗自主修復；核對最新 HEAD／有效測試版本與可信 workflow／App，不使用空測試、略過失敗或降低保護。一般 UI／低影響修錯／文件，在充分驗證且風險可接受時自主轉正式 PR，啟用個別 PR 的原生 auto-merge。
- 按行為、範圍及後果判斷，不只看檔名。安全／權限／憑證／隱私資料、真實交易／資金／風控／重要商業邏輯、破壞性正式 DB、重大架構／外部整合、實機驗收、重大或不可逆部署、AGENTS 安全規範／CI／合併部署政策，以及不明風險，預設需人工確認；不得拆 PR／移檔／改規則規避。
- 需人工時保留 Draft、不得 auto-merge；用現有互動提問提供摘要、風險、PR、Commit SHA，選「核准該版本／暫停查看或驗收／不核准請修改」。核准僅限呈現的 SHA，不取代 Frozen、產品授權、Stop／hold、CI、簽章與實機 Gate；無提問工具則直接詢問並等待。
- 審查後新增 Commit 要重新測試與評估，不沿用舊人工核准。修改已排隊 PR 前先原生撤銷 auto-merge、讀回確認；無法可靠撤銷就停止該 PR 自動化。主要分支只經 PR／required CI，不直接 Push、force push、admin bypass 或新增 Actions Merge Bot；保留必要的既有人工保護。
- 首次正式開發主動檢查 Git／GitHub／技術棧／CI／保護／原生 auto-merge／AGENTS／部署需要，依已有授權補缺項並接續原任務；冪等重用設定。不得未授權建立 repo／公開或上傳私人碼；只問缺少的帳號／owner／Secrets／費用／發布等決策，不重問是否初始化。遠端不假設繼承本機 global。
- CD 僅限安全、明確且已授權的實際目標，依政策執行健康檢查；研究／工具無目標只需 CI。保留高影響發布、簽章與實機核准；CI／Merge／部署／實機分別驗證，不做假 CD。權限／方案或證據不足保持 BLOCKED。
