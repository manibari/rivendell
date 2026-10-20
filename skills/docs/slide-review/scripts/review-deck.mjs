#!/usr/bin/env node
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { formatLines, markRepeats, minFontFor, naturalSort, parseCanvas, slideStatus, summarize } from "./review-lib.mjs";

const usage = "用法：node review-deck.mjs <slides-dir | slide.html ...> [--out <dir>] [--iter <n>] [--canvas <W>x<H>] [--min-font-ratio <r>]";
const checker = resolve(dirname(fileURLToPath(import.meta.url)), "../../chart-design/references/check-html-figure.mjs");

function parseArgs(args) {
  const options = { iter: 1, ratio: 0.0075, inputs: [] };
  for (let index = 0; index < args.length; index++) {
    const arg = args[index];
    if (["--out", "--iter", "--canvas", "--min-font-ratio"].includes(arg)) {
      const value = args[++index];
      if (!value || value.startsWith("--")) throw new Error(`缺少 ${arg} 的值`);
      if (arg === "--out") options.out = resolve(value);
      if (arg === "--iter") options.iter = Number(value);
      if (arg === "--canvas") options.canvas = parseCanvas(value);
      if (arg === "--min-font-ratio") options.ratio = Number(value);
    } else if (arg.startsWith("-")) {
      throw new Error(`不認得的參數：${arg}`);
    } else {
      options.inputs.push(resolve(arg));
    }
  }
  if (!options.inputs.length) throw new Error(usage);
  if (!Number.isSafeInteger(options.iter) || options.iter < 1) throw new Error("--iter 須為正整數");
  if (!Number.isFinite(options.ratio) || options.ratio <= 0) throw new Error("--min-font-ratio 須為正數");
  return options;
}

async function inputFiles(inputs) {
  const info = await Promise.all(inputs.map((input) => stat(input)));
  if (inputs.length === 1 && info[0].isDirectory()) {
    const entries = await readdir(inputs[0], { withFileTypes: true });
    return naturalSort(entries.filter((entry) => entry.isFile() && extname(entry.name).toLowerCase() === ".html")
      .map((entry) => entry.name)).map((name) => join(inputs[0], name));
  }
  if (info.some((item) => !item.isFile()) || inputs.some((input) => extname(input).toLowerCase() !== ".html")) {
    throw new Error("輸入須為一個資料夾或 HTML 檔案");
  }
  return inputs;
}

function unreadDiagnostic(code, message) {
  return { code, severity: "error", subject: {}, evidence: {}, suggestion: message, message, repeat: false };
}

function unreadSlide(file, canvas, minFont, code, message) {
  return {
    file, name: basename(file), canvas, min_font: minFont, screenshot: null,
    status: "unread", errors: 1, warnings: 0, diagnostics: [unreadDiagnostic(code, message)],
  };
}

async function measureCanvases(files) {
  const result = new Map();
  let browser;
  try {
    const require = createRequire(import.meta.url);
    const { chromium } = require("playwright");
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const page = await browser.newPage({ viewport: { width: 2400, height: 2400 } });
    for (const file of files) {
      try {
        await page.goto(pathToFileURL(file).href, { waitUntil: "load" });
        await page.evaluate(() => document.fonts?.ready);
        const size = await page.evaluate(() => {
          const rect = document.body.getBoundingClientRect();
          return [Math.round(rect.width), Math.round(rect.height)];
        });
        result.set(file, size.every((value) => value > 0 && value < 2400) ? size : null);
      } catch (error) {
        result.set(file, { error: String(error) });
      }
    }
  } catch (error) {
    for (const file of files) result.set(file, { error: String(error) });
  } finally {
    if (browser) await browser.close();
  }
  return result;
}

function runChecker(file, canvas, minFont, screenshot) {
  return new Promise((done) => {
    const args = [checker, file, "--width", String(canvas[0]), "--height", String(canvas[1]),
      "--min-font", String(minFont), "--screenshot", screenshot, "--annotate", "--json"];
    const child = spawn(process.execPath, args);
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8").on("data", (chunk) => { stdout += chunk; });
    child.stderr.setEncoding("utf8").on("data", (chunk) => { stderr += chunk; });
    child.on("error", (error) => { stderr += String(error); });
    child.on("close", (exitCode) => {
      if (exitCode === 0 || exitCode === 1) {
        try {
          const report = JSON.parse(stdout);
          if (Array.isArray(report.diagnostics)) return done({ report });
        } catch { /* Invalid checker output is reported below. */ }
      }
      done({ error: stderr.trim() });
    });
  });
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const files = await inputFiles(options.inputs);
  if (!files.length) throw new Error("找不到 HTML 投影片");
  const out = options.out ?? join(options.inputs.length === 1 && (await stat(options.inputs[0])).isDirectory()
    ? options.inputs[0] : dirname(files[0]), "review");
  const reportPath = join(out, `iter-${options.iter}`, "report.json");
  let previous;
  if (options.iter > 1) {
    try {
      previous = JSON.parse(await readFile(join(out, `iter-${options.iter - 1}`, "report.json"), "utf8"));
    } catch (error) {
      if (error.code === "ENOENT") throw new Error(`找不到上一輪的 report.json（iter-${options.iter - 1}），無法判斷重複問題`);
      throw error;
    }
  }
  await mkdir(dirname(reportPath), { recursive: true });
  const sizes = options.canvas ? new Map(files.map((file) => [file, options.canvas])) : await measureCanvases(files);
  const slides = [];
  for (const file of files) {
    const canvas = sizes.get(file);
    if (!canvas) {
      slides.push(unreadSlide(file, null, null, "review/canvas-unknown", "未判讀：量不到畫布大小，請用 --canvas 指定"));
      continue;
    }
    if (canvas.error) {
      slides.push(unreadSlide(file, null, null, "review/check-failed", canvas.error));
      continue;
    }
    const minFont = minFontFor(canvas[0], options.ratio);
    const screenshot = join(dirname(reportPath), `${basename(file, extname(file))}.png`);
    const checked = await runChecker(file, canvas, minFont, screenshot);
    if (checked.error !== undefined) {
      slides.push(unreadSlide(file, canvas, minFont, "review/check-failed", checked.error));
      continue;
    }
    const diagnostics = checked.report.diagnostics.map((diagnostic) => ({ ...diagnostic, repeat: false }));
    const slide = {
      file, name: basename(file), canvas, min_font: minFont, screenshot,
      errors: diagnostics.filter((diagnostic) => diagnostic.severity === "error").length,
      warnings: diagnostics.filter((diagnostic) => diagnostic.severity === "warning").length,
      diagnostics,
    };
    slide.status = slideStatus(slide);
    slides.push(slide);
  }
  const marked = previous ? markRepeats(previous, slides) : slides;
  const report = {
    iter: options.iter, created_at: new Date().toISOString(), inputs: files,
    min_font_ratio: options.ratio, slides: marked, summary: summarize(marked),
  };
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  for (const line of formatLines(report)) console.log(line);
  console.log(reportPath);
  process.exitCode = report.summary.fail || report.summary.unread ? 1 : 0;
}

try {
  await main();
} catch (error) {
  console.error(error.message);
  process.exitCode = 2;
}
