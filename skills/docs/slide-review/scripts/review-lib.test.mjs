import test from "node:test";
import assert from "node:assert/strict";
import {
  formatLines, markRepeats, minFontFor, naturalSort, parseCanvas, slideStatus, summarize,
} from "./review-lib.mjs";

const diagnostic = (code, severity = "error") => ({ code, severity, subject: {}, evidence: {}, suggestion: "fix" });
const slide = (name, diagnostics = [], status = "pass") => ({
  name, canvas: [960, 540], errors: diagnostics.filter((item) => item.severity === "error").length,
  warnings: diagnostics.filter((item) => item.severity === "warning").length,
  status, diagnostics,
});

test("natural sort keeps numeric order and suffix order", () => {
  const names = ["s10.html", "s05b.html", "s2.html", "s05.html"];
  assert.deepEqual(naturalSort(names), ["s2.html", "s05.html", "s05b.html", "s10.html"]);
  assert.equal(names[0], "s10.html");
});

test("canvas parsing accepts positive dimensions and rejects bad input", () => {
  assert.deepEqual(parseCanvas("960x540"), [960, 540]);
  assert.deepEqual(parseCanvas("720X405"), [720, 405]);
  for (const value of ["", "960", "960x0", "-1x405", "960.5x540", "960x540x2"]) {
    assert.throws(() => parseCanvas(value));
  }
});

test("minimum font uses width and rounds to a tenth", () => {
  assert.equal(minFontFor(960, 0.0075), 7.2);
  assert.equal(minFontFor(1600, 0.0075), 12);
});

test("status handles errors, warnings, and unread slides", () => {
  assert.equal(slideStatus(slide("a", [diagnostic("bad")])) , "fail");
  assert.equal(slideStatus(slide("a", [diagnostic("note", "warning")])), "pass");
  assert.equal(slideStatus(slide("a", [diagnostic("review/canvas-unknown")], "unread")), "unread");
});

test("repeats require the same slide, code, and error severity", () => {
  const previous = { slides: [slide("s1.html", [diagnostic("old"), diagnostic("warn", "warning")], "fail")] };
  const current = [
    slide("s1.html", [diagnostic("old"), diagnostic("new"), diagnostic("old", "warning"), diagnostic("warn")], "fail"),
    slide("s2.html", [diagnostic("old")], "fail"),
  ];
  const marked = markRepeats(previous, current);
  assert.deepEqual(marked[0].diagnostics.map((item) => item.repeat), [true, false, false, false]);
  assert.deepEqual(marked[1].diagnostics.map((item) => item.repeat), [false]);
  assert.equal(current[0].diagnostics[0].repeat, undefined);
});

test("summary counts slides and repeated diagnostics", () => {
  const slides = [
    slide("s1.html", [], "pass"),
    slide("s2.html", [{ ...diagnostic("bad"), repeat: true }], "fail"),
    slide("s3.html", [{ ...diagnostic("review/check-failed"), repeat: false }], "unread"),
  ];
  assert.deepEqual(summarize(slides), { slides: 3, pass: 1, fail: 1, unread: 1, repeats: 1 });
});

test("formatLines prints Chinese slide and summary lines", () => {
  const slides = [
    slide("s1.html", [], "pass"),
    slide("s2.html", [{ ...diagnostic("bad"), repeat: true }], "fail"),
    { ...slide("s3.html", [diagnostic("review/canvas-unknown")], "unread"), canvas: null },
  ];
  const lines = formatLines({ slides, summary: summarize(slides) });
  assert.deepEqual(lines, [
    "s1.html 960x540 錯誤 0 警告 0 通過",
    "s2.html 960x540 錯誤 1 警告 0 未通過（重複 1）",
    "s3.html 未知 錯誤 1 警告 0 未判讀",
    "共 3 頁：通過 1、未通過 1、未判讀 1、重複問題 1",
  ]);
});
