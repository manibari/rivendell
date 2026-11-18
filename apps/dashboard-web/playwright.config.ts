import path from "node:path";
import { defineConfig } from "@playwright/test";
import { apiPython, createRun, e2eRoot, repoRoot, webRoot } from "./e2e/support/store";

const webPort = Number(process.env.E2E_WEB_PORT ?? 3005);
const apiPort = Number(process.env.E2E_API_PORT ?? 8005);
const run = createRun(webPort, apiPort);
const recorderBin = path.join(e2eRoot, "recorders", "bin");

export default defineConfig({
  testDir: "./e2e",
  testMatch: "*.spec.ts",
  workers: 1,
  fullyParallel: false,
  globalSetup: "./e2e/global-setup.ts",
  use: { baseURL: `http://127.0.0.1:${webPort}` },
  reporter: [
    ["list"],
    ["json", { outputFile: "e2e/.results/report.json" }],
  ],
  webServer: [
    {
      command: `"${apiPython}" -m uvicorn server:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: path.join(repoRoot, "apps", "dashboard-api"),
      url: `http://127.0.0.1:${apiPort}/openapi.json`,
      reuseExistingServer: false,
      timeout: 300_000,
      env: {
        HOME: run.home,
        PATH: `${recorderBin}${path.delimiter}${process.env.PATH ?? ""}`,
        E2E_RECORDER_LOG: run.recorderLog,
        REPORTS_DIR: run.reports,
        WORKFLOW_MAP_FILE: run.workflow,
        RIVENDELL_LEGACY_DB_PATH: run.database,
        RIVENDELL_DB_PATH: run.database,
        RIVENDELL_DB_DIR: path.join(run.root, "data"),
        RIVENDELL_SESSION_LOGS: path.join(run.home, ".claude", "session-logs"),
        RIVENDELL_SKILLS_DIR: path.join(run.root, "skills"),
        RIVENDELL_SKILL_SUMMARIES: path.join(run.root, "skills", "summaries.tsv"),
        RIVENDELL_PORTS_CONF: path.join(run.root, "data", "ports.conf"),
        HARVEST_SKILLS_ROOT: run.root,
        DISK_TREE_FILE: path.join(run.root, "data", "disk-tree.json"),
        DISK_SNAPSHOT_COMMAND: path.join(recorderBin, "disk-snapshot"),
        SK_CHECK_COMMAND: path.join(recorderBin, "sk-check"),
        GIT_HEALTH_ROOT: path.join(run.root, "projects"),
        ISSUES_PROJECTS_DIR: path.join(run.root, "projects"),
        COMPOSE_FILE: path.join(run.root, "data", "docker-compose.yml"),
      },
    },
    {
      command: `npm run build:e2e && npx next start -H 127.0.0.1 -p ${webPort}`,
      cwd: webRoot,
      url: `http://127.0.0.1:${webPort}/`,
      reuseExistingServer: false,
      timeout: 300_000,
      env: { NEXT_DIST_DIR: ".next-e2e", API_PROXY_TARGET: `http://127.0.0.1:${apiPort}` },
    },
  ],
});
