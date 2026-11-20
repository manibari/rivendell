import { createRequire } from 'node:module';
import { statSync } from 'node:fs';
import { mkdir, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const CALLOUT_COLOR = '#D13438';
const BADGE_TEXT_COLOR = '#FFFFFF';
const BADGE_SIZE = 24;
const BADGE_GAP = 4;
const OUTLINE_PADDING = 4;
const CLIP_PADDING = 16;
const SPEC_FIELDS = new Set([
  'url', 'out', 'viewport', 'deviceScaleFactor', 'storageState',
  'waitFor', 'clip', 'fullPage', 'mask', 'callouts',
]);

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

function nonemptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

export function parseSpec(raw, specPath) {
  const problems = [];
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    throw new Error('規格必須是 JSON 物件');
  }
  for (const field of Object.keys(raw)) {
    if (!SPEC_FIELDS.has(field)) problems.push(`未知欄位：${field}`);
  }

  if (!nonemptyString(raw.url)) {
    problems.push('url 必須是 http 或 https 網址');
  } else {
    try {
      const url = new URL(raw.url);
      if (!['http:', 'https:'].includes(url.protocol)) problems.push('url 必須是 http 或 https 網址');
    } catch {
      problems.push('url 必須是 http 或 https 網址');
    }
  }
  if (!nonemptyString(raw.out) || !raw.out.endsWith('.png')) {
    problems.push('out 必須是 .png 路徑');
  }

  const viewport = raw.viewport === undefined ? { width: 1440, height: 900 } : raw.viewport;
  if (viewport === null || typeof viewport !== 'object' || Array.isArray(viewport)) {
    problems.push('viewport 必須包含正整數 width 和 height');
  } else {
    for (const field of Object.keys(viewport)) {
      if (!['width', 'height'].includes(field)) problems.push(`viewport 未知欄位：${field}`);
    }
    for (const field of ['width', 'height']) {
      if (!Number.isSafeInteger(viewport[field]) || viewport[field] <= 0) {
        problems.push(`viewport.${field} 必須是正整數`);
      }
    }
  }

  const deviceScaleFactor = raw.deviceScaleFactor === undefined ? 2 : raw.deviceScaleFactor;
  if (![1, 2, 3].includes(deviceScaleFactor)) problems.push('deviceScaleFactor 必須是 1、2 或 3');
  if (raw.storageState !== undefined) {
    if (!nonemptyString(raw.storageState)) {
      problems.push('storageState 必須是檔案路徑');
    } else {
      try {
        if (!statSync(path.resolve(process.cwd(), raw.storageState)).isFile()) {
          problems.push(`storageState 不是檔案：${raw.storageState}`);
        }
      } catch {
        problems.push(`storageState 檔案不存在：${raw.storageState}`);
      }
    }
  }
  for (const field of ['waitFor', 'clip']) {
    if (raw[field] !== undefined && !nonemptyString(raw[field])) problems.push(`${field} 必須是選擇器字串`);
  }
  const fullPage = raw.fullPage === undefined ? false : raw.fullPage;
  if (typeof fullPage !== 'boolean') problems.push('fullPage 必須是布林值');
  if (raw.clip !== undefined && fullPage === true) problems.push('clip 與 fullPage: true 不能同時使用');

  const mask = raw.mask === undefined ? [] : raw.mask;
  if (!Array.isArray(mask)) {
    problems.push('mask 必須是選擇器陣列');
  } else {
    mask.forEach((selector, index) => {
      if (!nonemptyString(selector)) problems.push(`mask[${index}] 必須是選擇器字串`);
    });
  }
  const callouts = raw.callouts === undefined ? [] : raw.callouts;
  if (!Array.isArray(callouts)) {
    problems.push('callouts 必須是陣列');
  } else {
    const numbers = new Set();
    callouts.forEach((callout, index) => {
      if (callout === null || typeof callout !== 'object' || Array.isArray(callout)) {
        problems.push(`callouts[${index}] 必須是物件`);
        return;
      }
      for (const field of Object.keys(callout)) {
        if (!['n', 'selector'].includes(field)) problems.push(`callouts[${index}] 未知欄位：${field}`);
      }
      if (!Number.isSafeInteger(callout.n) || callout.n <= 0) {
        problems.push(`callouts[${index}].n 必須是正整數`);
      } else if (numbers.has(callout.n)) {
        problems.push(`callouts[${index}].n 重複：${callout.n}`);
      } else {
        numbers.add(callout.n);
      }
      if (!nonemptyString(callout.selector)) problems.push(`callouts[${index}].selector 必須是選擇器字串`);
    });
  }

  if (problems.length) throw new Error(problems.join('；'));
  return {
    url: raw.url,
    out: path.resolve(process.cwd(), raw.out),
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor,
    ...(raw.storageState === undefined ? {} : { storageState: path.resolve(process.cwd(), raw.storageState) }),
    ...(raw.waitFor === undefined ? {} : { waitFor: raw.waitFor }),
    ...(raw.clip === undefined ? {} : { clip: raw.clip }),
    fullPage,
    mask,
    callouts,
  };
}

export function clipRect(box, padding, pageSize) {
  const left = Math.max(0, box.x - padding);
  const top = Math.max(0, box.y - padding);
  const right = Math.min(pageSize.width, box.x + box.width + padding);
  const bottom = Math.min(pageSize.height, box.y + box.height + padding);
  if (right <= left || bottom <= top) throw new Error('裁切範圍不在頁面內');
  return { x: left, y: top, width: right - left, height: bottom - top };
}

export function placeBadges(boxes, bounds, size) {
  const step = size + BADGE_GAP;
  const maxX = bounds.x + bounds.width - size;
  const maxY = bounds.y + bounds.height - size;
  if (maxX < bounds.x || maxY < bounds.y) throw new Error('擷取範圍太小，無法放置標號');
  const positions = [];
  for (const box of boxes) {
    const startX = Math.min(maxX, Math.max(bounds.x, box.x - OUTLINE_PADDING - size));
    const startY = Math.min(maxY, Math.max(bounds.y, box.y - OUTLINE_PADDING - size));
    let placed = false;
    const rows = [];
    for (let y = startY; y <= maxY; y += step) rows.push(y);
    for (let y = bounds.y; y < startY; y += step) rows.push(y);
    rows.push(startY);
    for (const [row, y] of rows.entries()) {
      const firstX = row === 0 ? startX : bounds.x;
      const lastX = row === rows.length - 1 ? startX - step : maxX;
      for (let x = firstX; x <= lastX; x += step) {
        if (positions.every((badge) => x + size <= badge.x || badge.x + size <= x || y + size <= badge.y || badge.y + size <= y)) {
          positions.push({ n: box.n, x, y });
          placed = true;
          break;
        }
      }
      if (placed) break;
    }
    if (!placed) throw new Error(`標號 ${box.n} 無法放入擷取範圍`);
  }
  return positions;
}

async function capture(spec) {
  const browser = await playwrightChromium().launch();
  let context;
  try {
    context = await browser.newContext({
      viewport: spec.viewport,
      deviceScaleFactor: spec.deviceScaleFactor,
      ...(spec.storageState ? { storageState: spec.storageState } : {}),
    });
    const page = await context.newPage();
    await page.goto(spec.url, { waitUntil: 'load' });
    try {
      await page.waitForLoadState('networkidle', { timeout: 5000 });
    } catch (error) {
      if (error.name !== 'TimeoutError') throw error;
    }
    if (spec.waitFor) await page.locator(spec.waitFor).waitFor({ state: 'visible', timeout: 10000 });

    const scroll = await page.evaluate(() => ({ x: window.scrollX, y: window.scrollY }));
    const boxes = [];
    const missing = [];
    for (const callout of spec.callouts) {
      const locator = page.locator(callout.selector);
      const count = await locator.count();
      const visible = [];
      for (let index = 0; index < count; index++) {
        if (await locator.nth(index).isVisible()) visible.push(locator.nth(index));
      }
      if (visible.length !== 1) {
        missing.push(`標號 ${callout.n}，選擇器 ${JSON.stringify(callout.selector)}：找到 ${visible.length} 個可見元素`);
        continue;
      }
      const box = await visible[0].boundingBox();
      if (!box) {
        missing.push(`標號 ${callout.n}，選擇器 ${JSON.stringify(callout.selector)}：找到 0 個可見元素`);
        continue;
      }
      boxes.push({ n: callout.n, x: box.x + scroll.x, y: box.y + scroll.y, width: box.width, height: box.height });
    }
    if (missing.length) throw new Error(missing.join('；'));

    const pageSize = await page.evaluate(() => ({
      width: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth ?? 0),
      height: Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight ?? 0),
    }));
    let clip;
    if (spec.clip) {
      const target = page.locator(spec.clip).first();
      const box = await target.boundingBox();
      if (!box) throw new Error(`clip 選擇器找不到可見元素：${spec.clip}`);
      clip = clipRect({ ...box, x: box.x + scroll.x, y: box.y + scroll.y }, CLIP_PADDING, pageSize);
    }
    const bounds = clip ?? (spec.fullPage
      ? { x: 0, y: 0, ...pageSize }
      : { x: scroll.x, y: scroll.y, ...spec.viewport });
    const badges = placeBadges(boxes, bounds, BADGE_SIZE);
    await page.evaluate(({ boxes: entries, badges: labels, color, textColor, size, outlinePadding }) => {
      const overlay = document.createElement('div');
      overlay.id = 'manual-writer-annotation-overlay';
      Object.assign(overlay.style, {
        position: 'absolute', left: '0', top: '0', width: '0', height: '0',
        zIndex: '2147483647', pointerEvents: 'none', overflow: 'visible',
      });
      for (const box of entries) {
        const outline = document.createElement('div');
        Object.assign(outline.style, {
          position: 'absolute', boxSizing: 'border-box',
          left: `${box.x - outlinePadding}px`, top: `${box.y - outlinePadding}px`,
          width: `${box.width + 2 * outlinePadding}px`, height: `${box.height + 2 * outlinePadding}px`,
          border: `2px solid ${color}`, borderRadius: '3px',
        });
        overlay.append(outline);
      }
      for (const badge of labels) {
        const element = document.createElement('div');
        element.textContent = String(badge.n);
        Object.assign(element.style, {
          position: 'absolute', boxSizing: 'border-box',
          left: `${badge.x}px`, top: `${badge.y}px`,
          width: `${size}px`, height: `${size}px`, borderRadius: '50%',
          background: color, color: textColor, font: 'bold 14px/24px Arial, sans-serif',
          textAlign: 'center', whiteSpace: 'nowrap',
        });
        overlay.append(element);
      }
      document.body.append(overlay);
    }, { boxes, badges, color: CALLOUT_COLOR, textColor: BADGE_TEXT_COLOR, size: BADGE_SIZE, outlinePadding: OUTLINE_PADDING });
    try {
      await mkdir(path.dirname(spec.out), { recursive: true });
      await page.screenshot({ path: spec.out, fullPage: spec.fullPage, ...(clip ? { clip } : {}), mask: spec.mask.map((selector) => page.locator(selector)) });
    } finally {
      await page.locator('#manual-writer-annotation-overlay').evaluate((element) => element.remove()).catch(() => {});
    }
  } finally {
    await context?.close();
    await browser.close();
  }
}

async function specPaths(args) {
  const files = [];
  for (let index = 0; index < args.length; index++) {
    const option = args[index];
    if (!['--spec', '--spec-dir'].includes(option) || !args[index + 1]) {
      throw new Error(`無效參數：${option}`);
    }
    const value = args[++index];
    if (option === '--spec') files.push(value);
    else {
      const names = (await readdir(value)).filter((name) => name.endsWith('.json')).sort();
      files.push(...names.map((name) => path.join(value, name)));
    }
  }
  if (!files.length) throw new Error('請提供 --spec <檔案> 或 --spec-dir <目錄>');
  return files;
}

async function main() {
  let files;
  try {
    files = await specPaths(process.argv.slice(2));
  } catch (error) {
    console.error(`錯誤：${error.message}`);
    process.exitCode = 1;
    return;
  }
  for (const file of files) {
    try {
      let raw;
      try {
        raw = JSON.parse(await readFile(file, 'utf8'));
      } catch (error) {
        if (error instanceof SyntaxError) throw new Error('JSON 格式錯誤');
        throw new Error('無法讀取規格檔');
      }
      const spec = parseSpec(raw, file);
      await capture(spec);
      console.log(`ok ${spec.out} (${spec.callouts.length} 個標註)`);
    } catch (error) {
      console.error(`錯誤 ${file}: ${String(error.message).replace(/\s*\r?\n\s*/g, ' ')}`);
      process.exitCode = 1;
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
