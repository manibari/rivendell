#!/usr/bin/env node
// Mechanical checks for an HTML figure / slide / diagram page.
// Turns the "screenshot and eyeball it" rule into diagnostics with evidence,
// the way archify's validate does (code / subject / evidence / suggestion).
//
// Usage:
//   node check-html-figure.mjs <file.html> [--width 1600] [--height 900|auto]
//        [--min-font 12] [--screenshot out.png] [--annotate] [--json]
//   --annotate draws each diagnostic's box on the screenshot (red = error, amber = warning).
//
// Checks (R1 canvas rule + the three eyeball questions from CLAUDE.md):
//   figure/overflow      page scrolls beyond the viewport (切版 / 溢出)
//   figure/text-wrap     a text element wrapped onto 2+ lines
//   figure/small-font    computed font-size below --min-font
//   figure/text-overlap  two text boxes intersect
//   figure/canvas-fill   content bbox fills < 80% of the viewport, or a side has > 8% padding
//   figure/empty-band    a horizontal band taller than 8% of the viewport has no content
//
// Exit 1 when any error-level diagnostic exists. Uses the system Chrome via
// Playwright (channel "chrome"), so no browser download is needed.

import { pathToFileURL } from "node:url";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const args = process.argv.slice(2);
if (!args.length || args.includes("--help")) {
  console.error("usage: check-html-figure.mjs <file.html> [--width N] [--height N|auto] [--min-font N] [--screenshot out.png] [--json]");
  process.exit(2);
}
const file = resolve(args[0]);
const opt = (name, def) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : def;
};
const width = Number(opt("--width", 1600));
const heightArg = opt("--height", 900);
const minFont = Number(opt("--min-font", 12));
const screenshot = opt("--screenshot", null);
const annotate = args.includes("--annotate");
const asJson = args.includes("--json");

// Playwright is resolved from rivendell's node_modules or any ancestor.
const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  console.error("playwright not found. Run from the rivendell repo (it is in node_modules) or `npm i playwright`.");
  process.exit(2);
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width, height: heightArg === "auto" ? 900 : Number(heightArg) } });
await page.goto(pathToFileURL(file).href, { waitUntil: "load" });
await page.evaluate(() => document.fonts?.ready);

if (heightArg === "auto") {
  const h = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.setViewportSize({ width, height: h });
}

const report = await page.evaluate(({ minFont, heightAuto }) => {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const diags = [];
  const push = (code, severity, subject, evidence, suggestion) =>
    diags.push({ code, severity, subject, evidence, suggestion });

  const sw = document.documentElement.scrollWidth;
  const sh = document.documentElement.scrollHeight;
  if (sw > vw || (!heightAuto && sh > vh)) {
    push("figure/overflow", "error", { viewport: [vw, vh] },
      { scrollWidth: sw, scrollHeight: sh, overflowX: sw > vw, overflowY: sh > vh },
      "reduce content or spacing; never fix with overflow:hidden or smaller type");
  }

  const isVisible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || Number(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const snippet = (el) => (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 40);
  const selector = (el) => {
    const parts = [];
    let cur = el;
    while (cur && cur !== document.body && parts.length < 3) {
      let s = cur.tagName.toLowerCase();
      if (cur.id) s += "#" + cur.id;
      else if (cur.classList.length) s += "." + [...cur.classList].slice(0, 2).join(".");
      parts.unshift(s);
      cur = cur.parentElement;
    }
    return parts.join(" > ");
  };

  // Text leaves: elements whose own text nodes carry visible text.
  const textLeaves = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  for (let el = walker.nextNode(); el; el = walker.nextNode()) {
    if (["SCRIPT", "STYLE", "NOSCRIPT"].includes(el.tagName)) continue;
    const ownText = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(" ");
    if (!ownText) continue;
    if (!isVisible(el)) continue;
    textLeaves.push({ el, ownText });
  }

  const boxes = [];
  for (const { el, ownText } of textLeaves) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const fs = parseFloat(cs.fontSize);
    let lh = parseFloat(cs.lineHeight);
    if (!Number.isFinite(lh)) lh = fs * 1.4;
    boxes.push({ el, r, fs });
    const rectOf = (q) => [Math.round(q.left), Math.round(q.top), Math.round(q.width), Math.round(q.height)];
    if (fs < minFont) {
      push("figure/small-font", "warning", { selector: selector(el), text: snippet(el) },
        { fontSizePx: Math.round(fs * 10) / 10, minFontPx: minFont, rect: rectOf(r) },
        "raise the size or justify why this element is allowed below the floor");
    }
    // A single-line element is roughly one line-height tall; 1.8× means it wrapped.
    const inlineOnly = [...el.children].every(c => getComputedStyle(c).display.startsWith("inline") || c.tagName === "BR");
    const hasBr = el.querySelector("br") !== null;
    if (inlineOnly && !hasBr && r.height >= lh * 1.8 && ownText.length > 1) {
      push("figure/text-wrap", "warning", { selector: selector(el), text: snippet(el) },
        { heightPx: Math.round(r.height), lineHeightPx: Math.round(lh), widthPx: Math.round(r.width), rect: rectOf(r) },
        "widen the container, shorten the text, or break it deliberately");
    }
  }

  // Overlap between text boxes that are not ancestor/descendant of each other.
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const ix = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
      const iy = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
      if (ix > 2 && iy > 2) {
        push("figure/text-overlap", "error",
          { a: { selector: selector(a.el), text: snippet(a.el) }, b: { selector: selector(b.el), text: snippet(b.el) } },
          { overlapPx: [Math.round(ix), Math.round(iy)], rect: [Math.round(Math.max(a.r.left, b.r.left)), Math.round(Math.max(a.r.top, b.r.top)), Math.round(ix), Math.round(iy)] },
          "move one label (offset / different anchor) or shorten it; do not shrink the font");
      }
    }
  }

  // Canvas fill (R1): union bbox of content-bearing elements vs viewport.
  const contentEls = [...document.body.querySelectorAll("*")].filter(el => {
    if (["SCRIPT", "STYLE", "NOSCRIPT", "HTML", "BODY"].includes(el.tagName)) return false;
    if (!isVisible(el)) return false;
    const cs = getComputedStyle(el);
    const hasBg = cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== "transparent";
    const hasBorder = ["Top", "Right", "Bottom", "Left"].some(s => parseFloat(cs["border" + s + "Width"]) > 0 && cs["border" + s + "Style"] !== "none");
    const isMedia = ["IMG", "SVG", "CANVAS", "VIDEO"].includes(el.tagName);
    const ownText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    return hasBg || hasBorder || isMedia || ownText;
  });
  const rects = contentEls.map(el => el.getBoundingClientRect())
    .filter(r => r.width < vw * 0.98 || r.height < vh * 0.98); // ignore full-page wrappers
  let left = vw, top = vh, right = 0, bottom = 0;
  for (const r of rects) {
    left = Math.min(left, Math.max(0, r.left));
    top = Math.min(top, Math.max(0, r.top));
    right = Math.max(right, Math.min(vw, r.right));
    bottom = Math.max(bottom, Math.min(vh, r.bottom));
  }
  const metrics = { viewport: [vw, vh], scrollSize: [sw, sh], textElements: textLeaves.length };
  if (rects.length) {
    const fill = ((right - left) * (bottom - top)) / (vw * vh);
    const pad = { left: left / vw, right: (vw - right) / vw, top: top / vh, bottom: (vh - bottom) / vh };
    metrics.canvasFill = Math.round(fill * 100) / 100;
    metrics.edgePadding = Object.fromEntries(Object.entries(pad).map(([k, v]) => [k, Math.round(v * 100) / 100]));
    const badSides = Object.entries(pad).filter(([, v]) => v > 0.08).map(([k]) => k);
    if (fill < 0.8 || badSides.length) {
      push("figure/canvas-fill", "warning", { rule: "R1" },
        { fill: metrics.canvasFill, edgePadding: metrics.edgePadding, sidesOver8pct: badSides },
        "spread content to fill >= 80% of the canvas; if it cannot, the page is the wrong size for the content");
    }
    // Empty horizontal bands inside the content area.
    const step = Math.max(4, Math.round(vh / 100));
    const occupied = new Array(Math.ceil(vh / step)).fill(false);
    for (const r of rects) {
      const y0 = Math.max(0, Math.floor(r.top / step)), y1 = Math.min(occupied.length - 1, Math.floor(r.bottom / step));
      for (let y = y0; y <= y1; y++) occupied[y] = true;
    }
    let runStart = null;
    const bands = [];
    for (let y = 0; y <= occupied.length; y++) {
      const empty = y < occupied.length && !occupied[y];
      if (empty && runStart === null) runStart = y;
      if (!empty && runStart !== null) { bands.push([runStart * step, y * step]); runStart = null; }
    }
    for (const [y0, y1] of bands) {
      if (y0 <= top + 1 || y1 >= bottom - 1) continue; // edges are covered by padding above
      if ((y1 - y0) / vh > 0.08) {
        push("figure/empty-band", "warning", { rule: "R1" },
          { fromY: y0, toY: y1, heightPct: Math.round(((y1 - y0) / vh) * 100), rect: [0, y0, vw, y1 - y0] },
          "close the gap or move content into it; a blank stripe reads as a layout mistake");
      }
    }
  }
  return { diagnostics: diags, metrics };
}, { minFont, heightAuto: heightArg === "auto" });

if (screenshot && annotate) {
  await page.evaluate((diags) => {
    const layer = document.createElement("div");
    layer.style.cssText = "position:absolute;left:0;top:0;width:0;height:0;z-index:2147483647;pointer-events:none;font:11px/1.2 -apple-system,Helvetica,sans-serif";
    for (const d of diags) {
      const r = d.evidence && d.evidence.rect;
      if (!r) continue;
      const color = d.severity === "error" ? "#d62828" : "#e08a00";
      const box = document.createElement("div");
      const pad = d.code === "figure/empty-band" ? 0 : 3;
      box.style.cssText = `position:absolute;left:${r[0] - pad + window.scrollX}px;top:${r[1] - pad + window.scrollY}px;width:${r[2] + pad * 2}px;height:${r[3] + pad * 2}px;border:2px ${d.code === "figure/empty-band" ? "dashed" : "solid"} ${color};background:${color}14;box-sizing:border-box`;
      const tag = document.createElement("span");
      tag.textContent = d.code.replace("figure/", "");
      tag.style.cssText = `position:absolute;left:-2px;top:-16px;background:${color};color:#fff;padding:1px 5px;border-radius:3px;white-space:nowrap`;
      box.appendChild(tag);
      layer.appendChild(box);
    }
    document.body.appendChild(layer);
  }, report.diagnostics);
}
if (screenshot) await page.screenshot({ path: resolve(screenshot), fullPage: heightArg === "auto" });
await browser.close();

const errors = report.diagnostics.filter(d => d.severity === "error").length;
const warnings = report.diagnostics.length - errors;
const out = {
  ok: errors === 0,
  file,
  viewport: report.metrics.viewport,
  summary: { errors, warnings },
  metrics: report.metrics,
  diagnostics: report.diagnostics,
  screenshot: screenshot ? resolve(screenshot) : null,
};
if (asJson) {
  console.log(JSON.stringify(out, null, 2));
} else {
  console.log(`${out.ok ? "PASS" : "FAIL"} ${file} @${out.viewport.join("x")} — ${errors} errors, ${warnings} warnings`);
  console.log(`  fill=${report.metrics.canvasFill ?? "n/a"} padding=${JSON.stringify(report.metrics.edgePadding ?? {})} text=${report.metrics.textElements}`);
  for (const d of report.diagnostics) {
    console.log(`  [${d.severity}] ${d.code} ${JSON.stringify(d.subject)} ${JSON.stringify(d.evidence)}`);
    console.log(`      → ${d.suggestion}`);
  }
  if (screenshot) console.log(`  screenshot: ${out.screenshot}`);
}
process.exit(out.ok ? 0 : 1);
