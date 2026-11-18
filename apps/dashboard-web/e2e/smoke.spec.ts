import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { recordedCalls } from "./support/recorder";
import { apiPython, currentRun, resetStore } from "./support/store";

test.beforeAll(() => resetStore());

test("首頁顯示側欄", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "總覽" })).toBeVisible();
});

test("Token 頁面可載入", async ({ page }) => {
  await page.goto("/tokens");
  await expect(page.getByRole("heading", { name: "Token 用量" })).toBeVisible();
  await expect(page.getByText(/^錯誤：/)).toHaveCount(0);
});

test("Agent 頁面顯示種子 agent 且沒有錯誤", async ({ page }) => {
  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "Agent 管理", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /sample\/tester/ })).toBeVisible();
  await expect(page.getByText(/^(Error|錯誤)[:：]/)).toHaveCount(0);
});

test("執行資料庫包含 agent_runs 資料表", () => {
  const code = "import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); print(c.execute(\"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='agent_runs'\").fetchone()[0])";
  const output = execFileSync(apiPython, ["-c", code, currentRun().database], { encoding: "utf8" });
  expect(output.trim()).toBe("1");
});

test("沒有錯誤資料時顯示空狀態", async ({ page }) => {
  await page.goto("/health/errors");
  await expect(page.getByText(/近 14 天無 agent 錯誤輸出/)).toBeVisible();
});

test("排程更新只修改 fixture 並記錄 launchctl", async ({ request }) => {
  const run = currentRun();
  const plist = path.join(run.home, "Library", "LaunchAgents", "com.sk.agent.sample.tester.plist");
  const before = fs.readFileSync(plist);
  const response = await request.post("/api/agents/schedule", {
    data: { label: "com.sk.agent.sample.tester", entries: [{ Hour: 10, Minute: 30 }] },
  });
  expect(response.ok()).toBeTruthy();
  expect(fs.readFileSync(plist).equals(before)).toBeFalsy();
  expect(recordedCalls()).toEqual(expect.arrayContaining([
    expect.objectContaining({ cmd: "launchctl", argv: ["unload", plist] }),
    expect.objectContaining({ cmd: "launchctl", argv: ["load", plist] }),
  ]));
});
