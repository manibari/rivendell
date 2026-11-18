葉子 826 片：通過 0、失敗 0、沒有測試 239、未執行 0、不適用 587。紅燈 319 項，黃燈 21 項。

## 1 樹的檢查

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| UNKNOWN_PURPOSE | $.modules[0].screens[0].controls[0].does | 控制項用途尚未釐清 |

`UNKNOWN_PURPOSE`：沒人說得出這個控制項做什麼，要決定它的用途或拿掉它。

## 2 樹和資料夾

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| MIXED_FOLDER | apps/dashboard-api/routes | 同層檔案屬於模組：harvest、home、ports、projects、shell、skills |
| MIXED_FOLDER | apps/dashboard-api/routes/monitoring | 同層檔案屬於模組：health、tokens |
| MIXED_FOLDER | apps/dashboard-web/src/app | 同層檔案屬於模組：home、shell |
| MIXED_FOLDER | apps/dashboard-web/src/components | 同層檔案屬於模組：agents、health、home、projects、shell、skills |
| MIXED_FOLDER | apps/dashboard-web/src/lib | 同層檔案屬於模組：ports、shell |

`MIXED_FOLDER`：同一資料夾有不同模組的直接檔案。

## 3 樹和路由

沒有問題


## 4 樹和畫面

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| UNLABELED | agents.label.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | agents.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | avatar.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | avatar.main.default.controls[14] | 控制項沒有可存取名稱 |
| NOT_REACHED | avatar.main.key-entered.save-key | 畫面或狀態未到達 |
| UNLABELED | docs.slug.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | harvest.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.agents.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.disk.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.errors.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.git.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.sensors.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | health.ssot.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | home.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | ports.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | projects.name.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | projects.name-workflow-flow.default.controls[0] | 控制項沒有可存取名稱 |
| NOT_REACHED | projects.name-workflow-flow.skill-detail.close-detail | 畫面或狀態未到達 |
| UNLABELED | projects.name-workflow.default.controls[0] | 控制項沒有可存取名稱 |
| ORPHAN | projects.name-workflow.default.controls[17] | 樹上找不到 button：rivendell |
| ORPHAN | projects.name-workflow.default.controls[18] | 樹上找不到 button：/requirement |
| ORPHAN | projects.name-workflow.default.controls[19] | 樹上找不到 button：/gstack-office-hours |
| ORPHAN | projects.name-workflow.default.controls[20] | 樹上找不到 button：/user-flow |
| ORPHAN | projects.name-workflow.default.controls[21] | 樹上找不到 button：/gstack-design-consultation |
| ORPHAN | projects.name-workflow.default.controls[22] | 樹上找不到 button：/gstack-design-shotgun |
| ORPHAN | projects.name-workflow.default.controls[23] | 樹上找不到 button：/mockup |
| ORPHAN | projects.name-workflow.default.controls[24] | 樹上找不到 button：/gstack-design-html |
| ORPHAN | projects.name-workflow.default.controls[25] | 樹上找不到 button：/planning-with-files |
| ORPHAN | projects.name-workflow.default.controls[26] | 樹上找不到 button：/gstack-plan-eng-review |
| ORPHAN | projects.name-workflow.default.controls[27] | 樹上找不到 button：/gstack-plan-design-review |
| ORPHAN | projects.name-workflow.default.controls[28] | 樹上找不到 button：/gstack-plan-ceo-review |
| ORPHAN | projects.name-workflow.default.controls[29] | 樹上找不到 button：/gstack-autoplan |
| ORPHAN | projects.name-workflow.default.controls[30] | 樹上找不到 button：/agent-code-dispatch |
| ORPHAN | projects.name-workflow.default.controls[31] | 樹上找不到 button：/gstack-investigate |
| ORPHAN | projects.name-workflow.default.controls[32] | 樹上找不到 button：/gstack-freeze |
| ORPHAN | projects.name-workflow.default.controls[33] | 樹上找不到 button：/gstack-unfreeze |
| ORPHAN | projects.name-workflow.default.controls[34] | 樹上找不到 button：/gstack-careful |
| ORPHAN | projects.name-workflow.default.controls[35] | 樹上找不到 button：/gstack-codex |
| ORPHAN | projects.name-workflow.default.controls[36] | 樹上找不到 button：/gstack-review |
| ORPHAN | projects.name-workflow.default.controls[37] | 樹上找不到 button：/gstack-qa |
| ORPHAN | projects.name-workflow.default.controls[38] | 樹上找不到 button：/gstack-qa-only |
| ORPHAN | projects.name-workflow.default.controls[39] | 樹上找不到 button：/gstack-design-review |
| ORPHAN | projects.name-workflow.default.controls[40] | 樹上找不到 button：/gstack-land-and-deploy |
| ORPHAN | projects.name-workflow.default.controls[41] | 樹上找不到 button：/gstack-ship |
| ORPHAN | projects.name-workflow.default.controls[42] | 樹上找不到 button：/gstack-canary |
| ORPHAN | projects.name-workflow.default.controls[43] | 樹上找不到 button：/gstack-document-release |
| UNLABELED | projects.main.default.controls[0] | 控制項沒有可存取名稱 |
| NOT_REACHED | projects.main.new-project.project-name | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.new-project.repo-path | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.new-project.description | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.new-project.agents | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.new-project.create | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.new-project.cancel | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.edit-project.edit-description | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.edit-project.edit-agents | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.edit-project.save | 畫面或狀態未到達 |
| NOT_REACHED | projects.main.edit-project.cancel-edit | 畫面或狀態未到達 |
| UNLABELED | skills.name.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | skills.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | skills.main.default.controls[23] | 控制項沒有可存取名稱 |
| UNLABELED | skills.main.default.controls[24] | 控制項沒有可存取名稱 |
| NOT_REACHED | skills.main.roles-view.raw-document | 畫面或狀態未到達 |
| NOT_REACHED | skills.main.roles-view.role-choice | 畫面或狀態未到達 |
| NOT_REACHED | skills.main.roles-view.job-anchor | 畫面或狀態未到達 |
| NOT_REACHED | skills.main.roles-view.skill-link | 畫面或狀態未到達 |
| UNLABELED | skills.roles.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | tokens.main.default.controls[0] | 控制項沒有可存取名稱 |
| UNLABELED | workflow.main.default.controls[0] | 控制項沒有可存取名稱 |
| ORPHAN | workflow.main.default.controls[17] | 樹上找不到 button：rivendell |
| ORPHAN | workflow.main.default.controls[18] | 樹上找不到 button：/requirement |
| ORPHAN | workflow.main.default.controls[19] | 樹上找不到 button：/gstack-office-hours |
| ORPHAN | workflow.main.default.controls[20] | 樹上找不到 button：/user-flow |
| ORPHAN | workflow.main.default.controls[21] | 樹上找不到 button：/gstack-design-consultation |
| ORPHAN | workflow.main.default.controls[22] | 樹上找不到 button：/gstack-design-shotgun |
| ORPHAN | workflow.main.default.controls[23] | 樹上找不到 button：/mockup |
| ORPHAN | workflow.main.default.controls[24] | 樹上找不到 button：/gstack-design-html |
| ORPHAN | workflow.main.default.controls[25] | 樹上找不到 button：/planning-with-files |
| ORPHAN | workflow.main.default.controls[26] | 樹上找不到 button：/gstack-plan-eng-review |
| ORPHAN | workflow.main.default.controls[27] | 樹上找不到 button：/gstack-plan-design-review |
| ORPHAN | workflow.main.default.controls[28] | 樹上找不到 button：/gstack-plan-ceo-review |
| ORPHAN | workflow.main.default.controls[29] | 樹上找不到 button：/gstack-autoplan |
| ORPHAN | workflow.main.default.controls[30] | 樹上找不到 button：/agent-code-dispatch |
| ORPHAN | workflow.main.default.controls[31] | 樹上找不到 button：/gstack-investigate |
| ORPHAN | workflow.main.default.controls[32] | 樹上找不到 button：/gstack-freeze |
| ORPHAN | workflow.main.default.controls[33] | 樹上找不到 button：/gstack-unfreeze |
| ORPHAN | workflow.main.default.controls[34] | 樹上找不到 button：/gstack-careful |
| ORPHAN | workflow.main.default.controls[35] | 樹上找不到 button：/gstack-codex |
| ORPHAN | workflow.main.default.controls[36] | 樹上找不到 button：/gstack-review |
| ORPHAN | workflow.main.default.controls[37] | 樹上找不到 button：/gstack-qa |
| ORPHAN | workflow.main.default.controls[38] | 樹上找不到 button：/gstack-qa-only |
| ORPHAN | workflow.main.default.controls[39] | 樹上找不到 button：/gstack-design-review |
| ORPHAN | workflow.main.default.controls[40] | 樹上找不到 button：/gstack-land-and-deploy |
| ORPHAN | workflow.main.default.controls[41] | 樹上找不到 button：/gstack-ship |
| ORPHAN | workflow.main.default.controls[42] | 樹上找不到 button：/gstack-canary |
| ORPHAN | workflow.main.default.controls[43] | 樹上找不到 button：/gstack-document-release |

`UNLABELED`：控制項沒有可存取名稱。
`NOT_REACHED`：掃描未到達畫面或狀態。
`ORPHAN`：畫面上有、樹上沒有，控制項用途尚未記錄。

## 5 樹和測試

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | shell.sidebar.project-switcher.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.project-switcher.empty | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-overview.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-avatar.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-workflow.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-projects.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-agents.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-agents.side-effect | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-tokens.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-deployment.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-deployment.side-effect | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-sensors.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-disk.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-schedule-health.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-schedule-health.side-effect | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-recent-errors.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-git-health.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-git-health.side-effect | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-ssot-drift.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-ssot-drift.side-effect | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-workflow-ui.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-workflow-backend.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-workflow-slide.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-workflow-maintenance.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-skills-overview.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-skills-by-role.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.nav-harvest.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.health-group.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.health-group.empty | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.skills-group.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.skills-group.empty | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.group-chevron.happy | 葉子沒有端到端測試 |
| NO_TEST | shell.sidebar.group-chevron.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.label.back-to-project.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-load.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-load.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-load.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-load.repeat | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-load.side-effect | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-run-now.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-run-now.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-run-now.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-run-now.repeat | 葉子沒有端到端測試 |
| NO_TEST | agents.label.agent-run-now.side-effect | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-load.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-load.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-load.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-load.repeat | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-load.side-effect | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-run-now.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-run-now.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-run-now.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-run-now.repeat | 葉子沒有端到端測試 |
| NO_TEST | agents.main.agent-run-now.side-effect | 葉子沒有端到端測試 |
| NO_TEST | agents.main.run-history.happy | 葉子沒有端到端測試 |
| NO_TEST | agents.main.run-history.empty | 葉子沒有端到端測試 |
| NO_TEST | agents.main.run-history.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.refresh.happy | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.refresh.empty | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.refresh.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.api-key.happy | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.api-key.empty | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.api-key.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.api-key.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.save-key.happy | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.save-key.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.save-key.repeat | 葉子沒有端到端測試 |
| NO_TEST | avatar.main.engine.happy | 葉子沒有端到端測試 |
| NO_TEST | docs.slug.roles-back.happy | 葉子沒有端到端測試 |
| NO_TEST | docs.slug.role-link.happy | 葉子沒有端到端測試 |
| NO_TEST | docs.slug.document-link.happy | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.pending.happy | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.pending.empty | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.accepted.happy | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.accepted.empty | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.dismissed.happy | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.dismissed.empty | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.all.happy | 葉子沒有端到端測試 |
| NO_TEST | harvest.main.all.empty | 葉子沒有端到端測試 |
| NO_TEST | health.disk.refresh.happy | 葉子沒有端到端測試 |
| NO_TEST | health.disk.refresh.empty | 葉子沒有端到端測試 |
| NO_TEST | health.disk.refresh.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | health.disk.refresh.side-effect | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-minute.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-minute.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.five-minutes.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.five-minutes.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.fifteen-minutes.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.fifteen-minutes.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-hour.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-hour.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.six-hours.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.six-hours.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-day.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-day.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.seven-days.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.seven-days.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.thirty-days.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.thirty-days.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.ninety-days.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.ninety-days.empty | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-year.happy | 葉子沒有端到端測試 |
| NO_TEST | health.sensors.one-year.empty | 葉子沒有端到端測試 |
| NO_TEST | home.main.ssot-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | home.main.ssot-detail.side-effect | 葉子沒有端到端測試 |
| NO_TEST | home.main.schedule-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | home.main.schedule-detail.side-effect | 葉子沒有端到端測試 |
| NO_TEST | home.main.errors-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | home.main.cost-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | home.main.git-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | home.main.git-detail.side-effect | 葉子沒有端到端測試 |
| NO_TEST | ports.main.related-deployments.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.related-deployments.empty | 葉子沒有端到端測試 |
| NO_TEST | ports.main.refresh.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.refresh.empty | 葉子沒有端到端測試 |
| NO_TEST | ports.main.refresh.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | ports.main.refresh.side-effect | 葉子沒有端到端測試 |
| NO_TEST | ports.main.all.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.all.empty | 葉子沒有端到端測試 |
| NO_TEST | ports.main.frontend.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.frontend.empty | 葉子沒有端到端測試 |
| NO_TEST | ports.main.backend.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.backend.empty | 葉子沒有端到端測試 |
| NO_TEST | ports.main.database.happy | 葉子沒有端到端測試 |
| NO_TEST | ports.main.database.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.name.back-to-projects.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.name.agent-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.back-to-project.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.back-to-project.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.skill-chip.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.skill-chip.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.close-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.name-workflow-flow.close-detail.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.new-project.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.new-project.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.project-detail.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.mission.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.mission.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.delete.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.delete.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.delete.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | projects.main.delete.repeat | 葉子沒有端到端測試 |
| NO_TEST | projects.main.project-name.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.project-name.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.project-name.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.repo-path.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.repo-path.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.repo-path.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.description.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.description.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.description.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.agents.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.agents.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.agents.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.create.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.create.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.create.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | projects.main.create.repeat | 葉子沒有端到端測試 |
| NO_TEST | projects.main.cancel.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.cancel.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-description.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-description.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-description.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-agents.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-agents.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.edit-agents.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | projects.main.save.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.save.empty | 葉子沒有端到端測試 |
| NO_TEST | projects.main.save.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | projects.main.save.repeat | 葉子沒有端到端測試 |
| NO_TEST | projects.main.cancel-edit.happy | 葉子沒有端到端測試 |
| NO_TEST | projects.main.cancel-edit.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.name.back-to-skills.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.loop-view.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.loop-view.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.role-view.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.role-view.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.other-filter.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.other-filter.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.built-in-filter.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.built-in-filter.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.all-filter.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.all-filter.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.expand-all.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.expand-all.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.search.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.search.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.main.search.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | skills.main.folder-filter.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.loop-filter.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.raw-document.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.role-choice.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.job-anchor.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.main.skill-link.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.back-to-skills.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.raw-document.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.role-choice.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.role-choice.empty | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.job-anchor.happy | 葉子沒有端到端測試 |
| NO_TEST | skills.roles.skill-link.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-from.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-from.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-from.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-from.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-to.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-to.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-to.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.date-to.dependency-down | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.clear-dates.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.clear-dates.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.by-account.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.by-account.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.by-model.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.by-model.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.per-minute.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.per-minute.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.per-hour.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.per-hour.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.one-hour.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.one-hour.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.three-hours.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.three-hours.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.six-hours.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.six-hours.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.total.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.total.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.output.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.output.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.context-cache.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.context-cache.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.pause.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.pause.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.report-select.happy | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.report-select.empty | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.report-select.invalid-input | 葉子沒有端到端測試 |
| NO_TEST | tokens.main.report-select.dependency-down | 葉子沒有端到端測試 |

`NO_TEST`：葉子沒有端到端測試。

## 6 還沒有測試的葉子（依模組）

### 外框與側欄

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | shell.sidebar.project-switcher.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.project-switcher.empty | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-overview.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-avatar.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-workflow.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-projects.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-agents.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-agents.side-effect | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-tokens.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-deployment.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-deployment.side-effect | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-sensors.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-disk.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-schedule-health.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-schedule-health.side-effect | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-recent-errors.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-git-health.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-git-health.side-effect | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-ssot-drift.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-ssot-drift.side-effect | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-workflow-ui.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-workflow-backend.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-workflow-slide.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-workflow-maintenance.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-skills-overview.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-skills-by-role.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.nav-harvest.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.health-group.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.health-group.empty | 尚未通過測試 |
| NO_TEST | shell.sidebar.skills-group.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.skills-group.empty | 尚未通過測試 |
| NO_TEST | shell.sidebar.group-chevron.happy | 尚未通過測試 |
| NO_TEST | shell.sidebar.group-chevron.empty | 尚未通過測試 |


### Agent

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | agents.label.back-to-project.happy | 尚未通過測試 |
| NO_TEST | agents.label.agent-load.happy | 尚未通過測試 |
| NO_TEST | agents.label.agent-load.empty | 尚未通過測試 |
| NO_TEST | agents.label.agent-load.dependency-down | 尚未通過測試 |
| NO_TEST | agents.label.agent-load.repeat | 尚未通過測試 |
| NO_TEST | agents.label.agent-load.side-effect | 尚未通過測試 |
| NO_TEST | agents.label.agent-run-now.happy | 尚未通過測試 |
| NO_TEST | agents.label.agent-run-now.empty | 尚未通過測試 |
| NO_TEST | agents.label.agent-run-now.dependency-down | 尚未通過測試 |
| NO_TEST | agents.label.agent-run-now.repeat | 尚未通過測試 |
| NO_TEST | agents.label.agent-run-now.side-effect | 尚未通過測試 |
| NO_TEST | agents.main.agent-detail.happy | 尚未通過測試 |
| NO_TEST | agents.main.agent-load.happy | 尚未通過測試 |
| NO_TEST | agents.main.agent-load.empty | 尚未通過測試 |
| NO_TEST | agents.main.agent-load.dependency-down | 尚未通過測試 |
| NO_TEST | agents.main.agent-load.repeat | 尚未通過測試 |
| NO_TEST | agents.main.agent-load.side-effect | 尚未通過測試 |
| NO_TEST | agents.main.agent-run-now.happy | 尚未通過測試 |
| NO_TEST | agents.main.agent-run-now.empty | 尚未通過測試 |
| NO_TEST | agents.main.agent-run-now.dependency-down | 尚未通過測試 |
| NO_TEST | agents.main.agent-run-now.repeat | 尚未通過測試 |
| NO_TEST | agents.main.agent-run-now.side-effect | 尚未通過測試 |
| NO_TEST | agents.main.run-history.happy | 尚未通過測試 |
| NO_TEST | agents.main.run-history.empty | 尚未通過測試 |
| NO_TEST | agents.main.run-history.dependency-down | 尚未通過測試 |


### 助理

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | avatar.main.refresh.happy | 尚未通過測試 |
| NO_TEST | avatar.main.refresh.empty | 尚未通過測試 |
| NO_TEST | avatar.main.refresh.dependency-down | 尚未通過測試 |
| NO_TEST | avatar.main.api-key.happy | 尚未通過測試 |
| NO_TEST | avatar.main.api-key.empty | 尚未通過測試 |
| NO_TEST | avatar.main.api-key.invalid-input | 尚未通過測試 |
| NO_TEST | avatar.main.api-key.dependency-down | 尚未通過測試 |
| NO_TEST | avatar.main.save-key.happy | 尚未通過測試 |
| NO_TEST | avatar.main.save-key.dependency-down | 尚未通過測試 |
| NO_TEST | avatar.main.save-key.repeat | 尚未通過測試 |
| NO_TEST | avatar.main.engine.happy | 尚未通過測試 |


### 文件

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | docs.slug.roles-back.happy | 尚未通過測試 |
| NO_TEST | docs.slug.role-link.happy | 尚未通過測試 |
| NO_TEST | docs.slug.document-link.happy | 尚未通過測試 |


### Skill Harvest

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | harvest.main.pending.happy | 尚未通過測試 |
| NO_TEST | harvest.main.pending.empty | 尚未通過測試 |
| NO_TEST | harvest.main.accepted.happy | 尚未通過測試 |
| NO_TEST | harvest.main.accepted.empty | 尚未通過測試 |
| NO_TEST | harvest.main.dismissed.happy | 尚未通過測試 |
| NO_TEST | harvest.main.dismissed.empty | 尚未通過測試 |
| NO_TEST | harvest.main.all.happy | 尚未通過測試 |
| NO_TEST | harvest.main.all.empty | 尚未通過測試 |


### 系統健康

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | health.disk.refresh.happy | 尚未通過測試 |
| NO_TEST | health.disk.refresh.empty | 尚未通過測試 |
| NO_TEST | health.disk.refresh.dependency-down | 尚未通過測試 |
| NO_TEST | health.disk.refresh.side-effect | 尚未通過測試 |
| NO_TEST | health.sensors.one-minute.happy | 尚未通過測試 |
| NO_TEST | health.sensors.one-minute.empty | 尚未通過測試 |
| NO_TEST | health.sensors.five-minutes.happy | 尚未通過測試 |
| NO_TEST | health.sensors.five-minutes.empty | 尚未通過測試 |
| NO_TEST | health.sensors.fifteen-minutes.happy | 尚未通過測試 |
| NO_TEST | health.sensors.fifteen-minutes.empty | 尚未通過測試 |
| NO_TEST | health.sensors.one-hour.happy | 尚未通過測試 |
| NO_TEST | health.sensors.one-hour.empty | 尚未通過測試 |
| NO_TEST | health.sensors.six-hours.happy | 尚未通過測試 |
| NO_TEST | health.sensors.six-hours.empty | 尚未通過測試 |
| NO_TEST | health.sensors.one-day.happy | 尚未通過測試 |
| NO_TEST | health.sensors.one-day.empty | 尚未通過測試 |
| NO_TEST | health.sensors.seven-days.happy | 尚未通過測試 |
| NO_TEST | health.sensors.seven-days.empty | 尚未通過測試 |
| NO_TEST | health.sensors.thirty-days.happy | 尚未通過測試 |
| NO_TEST | health.sensors.thirty-days.empty | 尚未通過測試 |
| NO_TEST | health.sensors.ninety-days.happy | 尚未通過測試 |
| NO_TEST | health.sensors.ninety-days.empty | 尚未通過測試 |
| NO_TEST | health.sensors.one-year.happy | 尚未通過測試 |
| NO_TEST | health.sensors.one-year.empty | 尚未通過測試 |


### 總覽

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | home.main.ssot-detail.happy | 尚未通過測試 |
| NO_TEST | home.main.ssot-detail.side-effect | 尚未通過測試 |
| NO_TEST | home.main.schedule-detail.happy | 尚未通過測試 |
| NO_TEST | home.main.schedule-detail.side-effect | 尚未通過測試 |
| NO_TEST | home.main.errors-detail.happy | 尚未通過測試 |
| NO_TEST | home.main.cost-detail.happy | 尚未通過測試 |
| NO_TEST | home.main.git-detail.happy | 尚未通過測試 |
| NO_TEST | home.main.git-detail.side-effect | 尚未通過測試 |


### 部署

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | ports.main.related-deployments.happy | 尚未通過測試 |
| NO_TEST | ports.main.related-deployments.empty | 尚未通過測試 |
| NO_TEST | ports.main.refresh.happy | 尚未通過測試 |
| NO_TEST | ports.main.refresh.empty | 尚未通過測試 |
| NO_TEST | ports.main.refresh.dependency-down | 尚未通過測試 |
| NO_TEST | ports.main.refresh.side-effect | 尚未通過測試 |
| NO_TEST | ports.main.all.happy | 尚未通過測試 |
| NO_TEST | ports.main.all.empty | 尚未通過測試 |
| NO_TEST | ports.main.frontend.happy | 尚未通過測試 |
| NO_TEST | ports.main.frontend.empty | 尚未通過測試 |
| NO_TEST | ports.main.backend.happy | 尚未通過測試 |
| NO_TEST | ports.main.backend.empty | 尚未通過測試 |
| NO_TEST | ports.main.database.happy | 尚未通過測試 |
| NO_TEST | ports.main.database.empty | 尚未通過測試 |


### 專案

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | projects.name.back-to-projects.happy | 尚未通過測試 |
| NO_TEST | projects.name.agent-detail.happy | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.back-to-project.happy | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.back-to-project.empty | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.skill-chip.happy | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.skill-chip.empty | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.close-detail.happy | 尚未通過測試 |
| NO_TEST | projects.name-workflow-flow.close-detail.empty | 尚未通過測試 |
| NO_TEST | projects.main.new-project.happy | 尚未通過測試 |
| NO_TEST | projects.main.new-project.empty | 尚未通過測試 |
| NO_TEST | projects.main.project-detail.happy | 尚未通過測試 |
| NO_TEST | projects.main.mission.happy | 尚未通過測試 |
| NO_TEST | projects.main.mission.empty | 尚未通過測試 |
| NO_TEST | projects.main.edit.happy | 尚未通過測試 |
| NO_TEST | projects.main.edit.empty | 尚未通過測試 |
| NO_TEST | projects.main.delete.happy | 尚未通過測試 |
| NO_TEST | projects.main.delete.empty | 尚未通過測試 |
| NO_TEST | projects.main.delete.dependency-down | 尚未通過測試 |
| NO_TEST | projects.main.delete.repeat | 尚未通過測試 |
| NO_TEST | projects.main.project-name.happy | 尚未通過測試 |
| NO_TEST | projects.main.project-name.empty | 尚未通過測試 |
| NO_TEST | projects.main.project-name.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.repo-path.happy | 尚未通過測試 |
| NO_TEST | projects.main.repo-path.empty | 尚未通過測試 |
| NO_TEST | projects.main.repo-path.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.description.happy | 尚未通過測試 |
| NO_TEST | projects.main.description.empty | 尚未通過測試 |
| NO_TEST | projects.main.description.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.agents.happy | 尚未通過測試 |
| NO_TEST | projects.main.agents.empty | 尚未通過測試 |
| NO_TEST | projects.main.agents.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.create.happy | 尚未通過測試 |
| NO_TEST | projects.main.create.empty | 尚未通過測試 |
| NO_TEST | projects.main.create.dependency-down | 尚未通過測試 |
| NO_TEST | projects.main.create.repeat | 尚未通過測試 |
| NO_TEST | projects.main.cancel.happy | 尚未通過測試 |
| NO_TEST | projects.main.cancel.empty | 尚未通過測試 |
| NO_TEST | projects.main.edit-description.happy | 尚未通過測試 |
| NO_TEST | projects.main.edit-description.empty | 尚未通過測試 |
| NO_TEST | projects.main.edit-description.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.edit-agents.happy | 尚未通過測試 |
| NO_TEST | projects.main.edit-agents.empty | 尚未通過測試 |
| NO_TEST | projects.main.edit-agents.invalid-input | 尚未通過測試 |
| NO_TEST | projects.main.save.happy | 尚未通過測試 |
| NO_TEST | projects.main.save.empty | 尚未通過測試 |
| NO_TEST | projects.main.save.dependency-down | 尚未通過測試 |
| NO_TEST | projects.main.save.repeat | 尚未通過測試 |
| NO_TEST | projects.main.cancel-edit.happy | 尚未通過測試 |
| NO_TEST | projects.main.cancel-edit.empty | 尚未通過測試 |


### 技能庫

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | skills.name.back-to-skills.happy | 尚未通過測試 |
| NO_TEST | skills.main.loop-view.happy | 尚未通過測試 |
| NO_TEST | skills.main.loop-view.empty | 尚未通過測試 |
| NO_TEST | skills.main.role-view.happy | 尚未通過測試 |
| NO_TEST | skills.main.role-view.empty | 尚未通過測試 |
| NO_TEST | skills.main.other-filter.happy | 尚未通過測試 |
| NO_TEST | skills.main.other-filter.empty | 尚未通過測試 |
| NO_TEST | skills.main.built-in-filter.happy | 尚未通過測試 |
| NO_TEST | skills.main.built-in-filter.empty | 尚未通過測試 |
| NO_TEST | skills.main.all-filter.happy | 尚未通過測試 |
| NO_TEST | skills.main.all-filter.empty | 尚未通過測試 |
| NO_TEST | skills.main.expand-all.happy | 尚未通過測試 |
| NO_TEST | skills.main.expand-all.empty | 尚未通過測試 |
| NO_TEST | skills.main.search.happy | 尚未通過測試 |
| NO_TEST | skills.main.search.empty | 尚未通過測試 |
| NO_TEST | skills.main.search.invalid-input | 尚未通過測試 |
| NO_TEST | skills.main.folder-filter.happy | 尚未通過測試 |
| NO_TEST | skills.main.loop-filter.happy | 尚未通過測試 |
| NO_TEST | skills.main.raw-document.happy | 尚未通過測試 |
| NO_TEST | skills.main.role-choice.happy | 尚未通過測試 |
| NO_TEST | skills.main.job-anchor.happy | 尚未通過測試 |
| NO_TEST | skills.main.skill-link.happy | 尚未通過測試 |
| NO_TEST | skills.roles.back-to-skills.happy | 尚未通過測試 |
| NO_TEST | skills.roles.raw-document.happy | 尚未通過測試 |
| NO_TEST | skills.roles.role-choice.happy | 尚未通過測試 |
| NO_TEST | skills.roles.role-choice.empty | 尚未通過測試 |
| NO_TEST | skills.roles.job-anchor.happy | 尚未通過測試 |
| NO_TEST | skills.roles.skill-link.happy | 尚未通過測試 |


### Token 用量

| 代碼 | 位置 | 說明 |
| --- | --- | --- |
| NO_TEST | tokens.main.date-from.happy | 尚未通過測試 |
| NO_TEST | tokens.main.date-from.empty | 尚未通過測試 |
| NO_TEST | tokens.main.date-from.invalid-input | 尚未通過測試 |
| NO_TEST | tokens.main.date-from.dependency-down | 尚未通過測試 |
| NO_TEST | tokens.main.date-to.happy | 尚未通過測試 |
| NO_TEST | tokens.main.date-to.empty | 尚未通過測試 |
| NO_TEST | tokens.main.date-to.invalid-input | 尚未通過測試 |
| NO_TEST | tokens.main.date-to.dependency-down | 尚未通過測試 |
| NO_TEST | tokens.main.clear-dates.happy | 尚未通過測試 |
| NO_TEST | tokens.main.clear-dates.empty | 尚未通過測試 |
| NO_TEST | tokens.main.by-account.happy | 尚未通過測試 |
| NO_TEST | tokens.main.by-account.empty | 尚未通過測試 |
| NO_TEST | tokens.main.by-model.happy | 尚未通過測試 |
| NO_TEST | tokens.main.by-model.empty | 尚未通過測試 |
| NO_TEST | tokens.main.per-minute.happy | 尚未通過測試 |
| NO_TEST | tokens.main.per-minute.empty | 尚未通過測試 |
| NO_TEST | tokens.main.per-hour.happy | 尚未通過測試 |
| NO_TEST | tokens.main.per-hour.empty | 尚未通過測試 |
| NO_TEST | tokens.main.one-hour.happy | 尚未通過測試 |
| NO_TEST | tokens.main.one-hour.empty | 尚未通過測試 |
| NO_TEST | tokens.main.three-hours.happy | 尚未通過測試 |
| NO_TEST | tokens.main.three-hours.empty | 尚未通過測試 |
| NO_TEST | tokens.main.six-hours.happy | 尚未通過測試 |
| NO_TEST | tokens.main.six-hours.empty | 尚未通過測試 |
| NO_TEST | tokens.main.total.happy | 尚未通過測試 |
| NO_TEST | tokens.main.total.empty | 尚未通過測試 |
| NO_TEST | tokens.main.output.happy | 尚未通過測試 |
| NO_TEST | tokens.main.output.empty | 尚未通過測試 |
| NO_TEST | tokens.main.context-cache.happy | 尚未通過測試 |
| NO_TEST | tokens.main.context-cache.empty | 尚未通過測試 |
| NO_TEST | tokens.main.pause.happy | 尚未通過測試 |
| NO_TEST | tokens.main.pause.empty | 尚未通過測試 |
| NO_TEST | tokens.main.report-select.happy | 尚未通過測試 |
| NO_TEST | tokens.main.report-select.empty | 尚未通過測試 |
| NO_TEST | tokens.main.report-select.invalid-input | 尚未通過測試 |
| NO_TEST | tokens.main.report-select.dependency-down | 尚未通過測試 |

## 6 負責人審核摘要

模組 12 個、畫面 23 個、狀態 5 個、控制項 118 個（重複項計一次）、葉子 826 片、不適用葉子 587 片。

### 清單 A：用途不明的控制項

| 畫面 | 角色 | 名稱 | 查過的地方 |
| --- | --- | --- | --- |
| shell.sidebar | combobox | 無可存取名稱 | `Sidebar.tsx:574-588` 有選項與專案清單，但找不到 `onChange`、提交或依選值更新畫面的程式；掃描只回報空名稱。 |

### 清單 B：模組名稱

| ID | 名稱 |
| --- | --- |
| shell | 外框與側欄 |
| agents | Agent |
| avatar | 助理 |
| docs | 文件 |
| harvest | Skill Harvest |
| health | 系統健康 |
| home | 總覽 |
| ports | 部署 |
| projects | 專案 |
| skills | 技能庫 |
| tokens | Token 用量 |
| workflow | 工作流程 |

### 清單 C：不適用原因

| 原因 | 葉子數 |
| --- | ---: |
| 固定導覽連結，與資料筆數無關 | 38 |
| 固定畫面控制項，與資料筆數無關 | 5 |
| 此控制項不呼叫服務 | 102 |
| 此控制項不接受文字輸入 | 107 |
| 此操作不呼叫外部系統 | 104 |
| 此操作只讀取或切換畫面 | 110 |
| 沒有登入，只有一位本機使用者 | 118 |
| 畫面資料由目前狀態提供 | 3 |

### 介面發現

- **沒有可存取名稱：** 掃描出 25 列：側欄專案下拉選單在 22 個畫面重複出現，助理頁的引擎選單 1 列，技能總覽的兩個篩選選單 2 列。後三者雖已列在樹中，掃描仍會回報 `UNLABELED`。
- **中文畫面上的英文標籤：** 側欄 `Agent`、`Token 用量`、`UI Feature`、`Backend`、`Slide`、`Maintenance`、`Skill Harvest`；部署頁 `Refresh`；技能頁 `Skills`、`Skill 總覽`、`Repo 路徑` 等混用英文；技能說明視窗的 `close`。
- **沒有作用的控制項：** 側欄專案下拉選單有 `select` 與選項，但沒有選值處理程式。
- **指向不存在頁面的連結：** 在本次檢查的固定連結中未確認到；`docs/loops/gov-tender.md` 原檔存在，動態路由也存在。

### 取捨與未完成的比對

- `shell.sidebar` 收納所有側欄連結與群組按鈕，包含僅在目前路由或展開時顯示的子連結。這些項目從各頁草稿移除，原因是共用版面重複。
- `skills.roles` 的角色按鈕、工作定位連結、技能連結，以及流程頁的技能按鈕，按來源元件各合併為一個重複控制項。助理頁兩個金鑰欄位共用同一個列表處理程式，也合併為一個重複控制項。
- `/workflow` 和 `/projects/[name]/workflow` 的頁面程式都是轉址，故清空草稿控制項；原掃描把轉址後目標頁的按鈕記在這兩個來源畫面。依目前 checker 契約，這造成 54 列 `ORPHAN`；若要同時保留轉址事實並消除這些列，需由下一次掃描或 checker 正確標記轉址，不能把目標頁按鈕誤寫成來源頁控制項。
- `projects.main` 的新增與編輯表單、流程頁的技能說明視窗、助理頁輸入金鑰後的儲存按鈕、技能頁角色視角已寫為狀態。原掃描沒有這些狀態，所以 16 列 `NOT_REACHED` 等待重掃。助理頁兩個金鑰欄位同名，現有步驟只用角色與名稱，可能無法指定其中一欄；此限制需由重掃確認。
- 同一資料夾的直接檔案分屬不同模組，保留 5 個 `MIXED_FOLDER`。每個來源檔仍恰有一個模組負責。API 路由依畫面用途歸屬，通用樣式、字型、側欄和共用 API helper 歸 `shell`。
- 無側欄項目的 `docs`、`workflow` 模組保留獨立名稱：前者為文件頁，後者為舊書籤轉址。沒有新增模組。

### Checker 最終輸出

- `validate`：1 列；最後一行：`UNKNOWN_PURPOSE $.modules[0].screens[0].controls[0].does：控制項用途尚未釐清`
- `folders`：5 列；最後一行：`MIXED_FOLDER apps/dashboard-web/src/lib：同層檔案屬於模組：ports、shell`
- `routes`：1 列；最後一行：`沒有問題`
- `screens`：95 列；最後一行：`ORPHAN workflow.main.default.controls[43]：樹上找不到 button：/gstack-document-release`
