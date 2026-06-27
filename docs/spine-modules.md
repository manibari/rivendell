# Spine Modules — fleet 共用 infra 脊椎登錄表

> Living index. 每識別到一個「跨產品常重用」的模組就加一列,別讓它住在腦袋裡。
> 配套:office-hours design doc `~/.gstack/projects/manibari-rivendell/manibari-chore-skill-quality-design-20260627-233134.md`
> + memory `fleet-infra-spine`。
>
> **紀律**:入脊椎前先**審計**(跨 ≥2 個成熟產品 chimesflow/family-fiscal/mops 看形狀是否收斂);
> 收斂的才抽成 recipe-skill。greenfield(tukey-*/pti-ares/ic-yms)是**消費者**,不是定義者。
> 每支 recipe-skill 要有**鋭利的 TRIGGER**,這樣下次描述需求時 Claude 自動把它拉出來 —— 你不用記得,skill 記得。

| # | 模組 | 做什麼 | 狀態 | recipe-skill (規劃名) |
|---|------|--------|------|----------------------|
| 1 | 帳密 auth | 登入 / 憑證 / token | candidate | `spine-auth` |
| 2 | rbac | 角色權限,給多人用 | candidate | `spine-rbac` |
| 3 | logs + admin API | 後台看 logs 跟資料 | candidate | `spine-admin-observability` |
| 4 | roadmap | 開發 roadmap 呈現 | candidate | `spine-roadmap` |
| 5 | 版本 versioning | 開發版本號 / changelog | candidate | `spine-versioning` |
| 6 | cloudflare / deploy | tunnel + prod 部署(WSL deploy 工具已建) | candidate | `spine-deploy` |
| 7 | DB schema sync | alembic + dev↔prod schema 同步 | candidate | `spine-schema-sync` |
| 8 | 表單回饋 feedback | 使用者回饋表單系統 | candidate | `spine-feedback` |
| 9 | 通知小鈴鐺 | in-app notification bell | candidate | `spine-notifications` |
| 10 | audit 稽核軌跡 | 誰改了什麼的 audit log | candidate | `spine-audit` |
| 11 | api-keys 金鑰管理 | 對外 API key 發放/撤銷 | candidate | `spine-api-keys` |
| 12 | settings 設定中心 | 系統/租戶設定頁 | candidate | `spine-settings` |
| 13 | email/mail 寄信 | 寄信子系統(通知/邀請/回饋) | candidate | `spine-email` |
| 14 | file upload/storage | 附件上傳/儲存 | candidate | `spine-file-storage` |

> 條件性(只有特定產品要):multi-tenant、SSO allowlist、admin snapshot/backup。需要時再加列。
> #10–14 來自 2026-06-27 盤點 chimesflow code(routers + 跨檔引用數),非憑記憶。

狀態:`candidate`(候選,未審計) → `audited`(已比對成熟產品交集) → `skill`(已捕捉成 recipe-skill,可自動觸發)

第一個要跑通迴圈的:**#1 帳密 auth**(design doc 的「第一刀」+ 是其他多數的前置)。跑通 = 證明「系統會替你記」。
