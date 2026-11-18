#!/usr/bin/env node
import { createRequire } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { parseAriaSnapshot } from './aria_parse.mjs';

const NETWORK_IDLE_CAP_MS = 1000;

function argumentsForRun(args) {
  const options = { timeoutMs: 15000 };
  const flags = { '--tree': 'tree', '--out': 'out', '--base-url': 'baseUrl', '--only': 'only', '--timeout-ms': 'timeoutMs' };
  for (let index = 0; index < args.length; index += 2) {
    const key = flags[args[index]];
    if (!key || index + 1 >= args.length || args[index + 1].startsWith('--')) {
      throw new Error(`參數錯誤：${args[index] ?? '缺少參數'}`);
    }
    options[key] = args[index + 1];
  }
  if (!options.tree || !options.out) throw new Error('缺少 --tree 或 --out');
  options.timeoutMs = Number(options.timeoutMs);
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1) {
    throw new Error('--timeout-ms 必須是正整數');
  }
  return options;
}

function resolveRoute(route, sample = {}) {
  let missing;
  const resolved = route.replace(/\[\[\.\.\.([^\]]+)\]\]|\[\.\.\.([^\]]+)\]|\[([^\]]+)\]/g, (_, optional, catchall, single) => {
    const name = optional ?? catchall ?? single;
    const value = sample[name];
    if (value === undefined || value === null) {
      missing ??= name;
      return '';
    }
    const segments = String(value).split('/');
    if (single && segments.length !== 1) {
      missing ??= name;
      return '';
    }
    return segments.map(encodeURIComponent).join('/');
  });
  return { resolved, missing };
}

function absoluteUrl(baseUrl, route) {
  return new URL(route.replace(/^\/+/, ''), `${baseUrl.replace(/\/+$/, '')}/`).href;
}

function playwrightChromium() {
  const require = createRequire(path.join(process.cwd(), 'package.json'));
  for (const packageName of ['playwright', '@playwright/test']) {
    try {
      const { chromium } = require(packageName);
      if (chromium) return chromium;
    } catch (error) {
      if (error.code !== 'MODULE_NOT_FOUND') throw error;
    }
  }
  throw new Error('找不到 Playwright：請在目標專案安裝 @playwright/test，並在該專案目錄執行');
}

async function idle(page) {
  try {
    await page.waitForLoadState('networkidle', { timeout: NETWORK_IDLE_CAP_MS });
  } catch { /* A busy page can still be scanned. */ }
}

async function pressWithTimeout(page, key, timeout) {
  let timer;
  try {
    await Promise.race([
      page.keyboard.press(key),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`按鍵逾時（${timeout} ms）`)), timeout);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function performStep(page, step, baseUrl, timeout) {
  const [[action, value]] = Object.entries(step);
  switch (action) {
    case 'click':
      await page.getByRole(value.role, { name: value.name, exact: true }).click({ timeout });
      break;
    case 'fill':
      await page.getByRole(value.role, { name: value.name, exact: true }).fill(value.value, { timeout });
      break;
    case 'press':
      await pressWithTimeout(page, value.key, timeout);
      break;
    case 'goto': {
      const response = await page.goto(absoluteUrl(baseUrl, value), { waitUntil: 'load', timeout });
      if (response && response.status() >= 400) throw new Error(`HTTP ${response.status()}`);
      break;
    }
    case 'wait_for':
      await page.getByRole(value.role, { name: value.name, exact: true }).waitFor({ state: 'visible', timeout });
      break;
    default:
      throw new Error(`不支援的步驟：${action}`);
  }
}

async function scanEntry(browser, baseUrl, moduleId, screen, state, timeout) {
  const { resolved, missing } = resolveRoute(screen.route, screen.sample);
  const entry = {
    module: moduleId, screen: screen.id, state: state.id,
    url: absoluteUrl(baseUrl, missing ? screen.route : resolved),
    reached: false, error: null, controls: [],
  };
  if (missing) {
    entry.error = `缺少 sample：${missing}`;
    return entry;
  }

  let context;
  try {
    context = await browser.newContext();
    const page = await context.newPage();
    try {
      const response = await page.goto(entry.url, { waitUntil: 'load', timeout });
      if (response && response.status() >= 400) throw new Error(`HTTP ${response.status()}`);
    } catch (error) {
      entry.error = `步驟 0（載入頁面）失敗：${error.message}`;
      return entry;
    }
    await idle(page);
    for (const [index, step] of state.steps.entries()) {
      try {
        await performStep(page, step, baseUrl, timeout);
      } catch (error) {
        entry.error = `步驟 ${index + 1} 失敗：${error.message}`;
        return entry;
      }
    }
    await idle(page);
    try {
      entry.controls = parseAriaSnapshot(await page.locator('body').ariaSnapshot({ timeout }));
      entry.reached = true;
    } catch (error) {
      entry.error = `讀取無障礙快照失敗：${error.message}`;
    }
  } catch (error) {
    entry.error ??= `開啟頁面失敗：${error.message}`;
  } finally {
    if (context) await context.close();
  }
  return entry;
}

function timestampWithOffset() {
  const now = new Date();
  const offsetMinutes = -now.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? '+' : '-';
  const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, '0');
  const minutes = String(Math.abs(offsetMinutes) % 60).padStart(2, '0');
  const local = new Date(now.getTime() + offsetMinutes * 60_000);
  return `${local.toISOString().slice(0, -1)}${sign}${hours}:${minutes}`;
}

async function main() {
  const options = argumentsForRun(process.argv.slice(2));
  let tree;
  try {
    tree = JSON.parse(await readFile(options.tree, 'utf8'));
  } catch (error) {
    throw new Error(`無法讀取 feature tree：${error.message}`);
  }
  const baseUrl = options.baseUrl ?? tree.config?.base_url;
  if (!baseUrl) throw new Error('缺少 base_url');
  try { new URL(baseUrl); } catch { throw new Error(`base_url 無效：${baseUrl}`); }
  if (!Array.isArray(tree.modules)) throw new Error('feature tree 缺少 modules');
  const chromium = playwrightChromium();
  const browser = await chromium.launch({ headless: true });
  const screens = [];
  try {
    for (const module of tree.modules) {
      for (const screen of module.screens ?? []) {
        if (screen.layout || (options.only && options.only !== `${module.id}.${screen.id}`)) continue;
        for (const state of [{ id: 'default', steps: [] }, ...(screen.states ?? [])]) {
          screens.push(await scanEntry(browser, baseUrl, module.id, screen, state, options.timeoutMs));
        }
      }
    }
  } finally {
    await browser.close();
  }
  await writeFile(options.out, `${JSON.stringify({ schema: 1, base_url: baseUrl, scanned_at: timestampWithOffset(), screens }, null, 2)}\n`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 2;
});
