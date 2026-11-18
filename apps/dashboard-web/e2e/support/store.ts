import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { assertSafeServers } from "./guard";

export const webRoot = path.resolve(__dirname, "../..");
export const repoRoot = path.resolve(webRoot, "../..");
export const e2eRoot = path.join(webRoot, "e2e");
export const seedRoot = path.join(e2eRoot, "fixtures", "seed");
export const currentFile = path.join(e2eRoot, ".tmp", "current.json");
export const apiPython = process.env.DASHBOARD_API_PYTHON ?? path.join(repoRoot, "apps", "dashboard-api", ".venv", "bin", "python");
const legacyLib = path.join(repoRoot, "apps", "dashboard-legacy");
const seedCode = [
  "import sqlite3, sys",
  "sys.path.insert(0, sys.argv[1])",
  "from lib.db import init_db",
  "init_db()",
  "with sqlite3.connect(sys.argv[2]) as conn:",
  "    conn.execute('INSERT INTO agent_runs (agent_name, project, started_at, finished_at, exit_code, tokens_used, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?)', ('tester', 'sample', '2026-11-19T09:00:00', '2026-11-19T09:01:00', 0, 42, 0.01))",
].join("\n");

function initializeDatabase(run: RunPaths): void {
  const args = ["-c", seedCode, legacyLib, run.database];
  try {
    execFileSync(apiPython, args, {
      env: { ...process.env, RIVENDELL_LEGACY_DB_PATH: run.database },
      stdio: "pipe",
    });
  } catch (error) {
    throw new Error(`無法建立 E2E 資料庫；指令：${apiPython} -c <初始化程式> ${legacyLib} ${run.database}`, { cause: error });
  }
}

function pruneRuns(): void {
  const temporaryRoot = path.dirname(currentFile);
  const runs = fs.readdirSync(temporaryRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^run-\d+-\d+$/.test(entry.name))
    .map((entry) => {
      const folder = path.join(temporaryRoot, entry.name);
      return { folder, created: Number(entry.name.split("-")[1]) };
    })
    .sort((a, b) => b.created - a.created);
  for (const run of runs.slice(3)) fs.rmSync(run.folder, { recursive: true });
}

export interface RunPaths {
  root: string;
  home: string;
  reports: string;
  database: string;
  workflow: string;
  recorderLog: string;
}

// Playwright loads the config again in each worker. Only the first load (the
// main process, which starts the servers) makes a run; it exports the root, and
// workers inherit it. Without this, a worker made a second run and the test read
// files that the servers never wrote (2026-11-19).
const RUN_ENV = "E2E_RUN_ROOT";

export function createRun(webPort: number, apiPort: number): RunPaths {
  if (process.env[RUN_ENV]) {
    const run = currentRun();
    assertSafeServers(webPort, apiPort, run.home, os.userInfo().homedir);
    return run;
  }
  const root = path.join(e2eRoot, ".tmp", `run-${Date.now()}-${process.pid}`);
  const home = path.join(root, "home");
  assertSafeServers(webPort, apiPort, home, os.userInfo().homedir);
  fs.mkdirSync(root, { recursive: true });
  fs.cpSync(seedRoot, root, { recursive: true, force: true });
  const run: RunPaths = {
    root, home, reports: path.join(root, "reports"),
    database: path.join(root, "data", "rivendell.db"),
    workflow: path.join(root, "workflows", "workflow-map.json"),
    recorderLog: path.join(root, "recorder.jsonl"),
  };
  initializeDatabase(run);
  fs.writeFileSync(run.recorderLog, "");
  fs.writeFileSync(currentFile, JSON.stringify(run));
  pruneRuns();
  process.env[RUN_ENV] = root;
  return run;
}

export function currentRun(): RunPaths {
  return JSON.parse(fs.readFileSync(currentFile, "utf8")) as RunPaths;
}

export function resetStore(): void {
  const run = currentRun();
  for (const entry of ["home", "reports", "data", "workflows", "projects", "skills"]) {
    const target = path.join(run.root, entry);
    fs.rmSync(target, { recursive: true, force: true });
    const source = path.join(seedRoot, entry);
    if (fs.existsSync(source)) fs.cpSync(source, target, { recursive: true });
  }
  initializeDatabase(run);
  fs.writeFileSync(run.recorderLog, "");
}
