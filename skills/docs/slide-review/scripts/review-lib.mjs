const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

export function naturalSort(names) {
  return [...names].sort((a, b) => collator.compare(a, b) || a.localeCompare(b));
}

export function parseCanvas(text) {
  const match = /^(\d+)x(\d+)$/i.exec(text ?? "");
  if (!match) throw new Error("畫布格式須為 WxH，且寬高須為正整數");
  const canvas = match.slice(1).map(Number);
  if (canvas.some((value) => !Number.isSafeInteger(value) || value <= 0)) {
    throw new Error("畫布格式須為 WxH，且寬高須為正整數");
  }
  return canvas;
}

export function minFontFor(width, ratio) {
  return Math.round(width * ratio * 10) / 10;
}

export function slideStatus(slide) {
  if (slide.status === "unread") return "unread";
  return slide.diagnostics.some((diagnostic) => diagnostic.severity === "error") ? "fail" : "pass";
}

export function markRepeats(prevReport, slides) {
  const prior = new Map(prevReport.slides.map((slide) => [slide.name,
    new Set(slide.diagnostics.filter((diagnostic) => diagnostic.severity === "error")
      .map((diagnostic) => diagnostic.code))]));
  return slides.map((slide) => ({
    ...slide,
    diagnostics: slide.diagnostics.map((diagnostic) => ({
      ...diagnostic,
      repeat: diagnostic.severity === "error" && (prior.get(slide.name)?.has(diagnostic.code) ?? false),
    })),
  }));
}

export function summarize(slides) {
  return {
    slides: slides.length,
    pass: slides.filter((slide) => slide.status === "pass").length,
    fail: slides.filter((slide) => slide.status === "fail").length,
    unread: slides.filter((slide) => slide.status === "unread").length,
    repeats: slides.reduce((sum, slide) => sum + slide.diagnostics.filter((diagnostic) => diagnostic.repeat).length, 0),
  };
}

export function formatLines(report) {
  const labels = { pass: "通過", fail: "未通過", unread: "未判讀" };
  const lines = report.slides.map((slide) => {
    const canvas = slide.canvas ? slide.canvas.join("x") : "未知";
    const repeats = slide.diagnostics.filter((diagnostic) => diagnostic.repeat).length;
    return `${slide.name} ${canvas} 錯誤 ${slide.errors} 警告 ${slide.warnings} ${labels[slide.status]}`
      + (repeats ? `（重複 ${repeats}）` : "");
  });
  const { slides, pass, fail, unread, repeats } = report.summary;
  lines.push(`共 ${slides} 頁：通過 ${pass}、未通過 ${fail}、未判讀 ${unread}、重複問題 ${repeats}`);
  return lines;
}
