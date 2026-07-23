// 計畫書 docx build template — copy into cache/YYYYMMDD-計畫書docx/build.js
// and fill the content section from the md SoT (計畫書內文_vN.md).
// Run: NODE_PATH=$(npm root -g) node build.js   (requires global `docx` package)
//
// Conventions baked in:
//   warn()  → 紅字▲ pending-item marker (C00000) — the user flips pages scanning red
//   NI/list → fresh 1,2,3… numbered sequence per work-item block (rule 3)
//   claim+DET → bold one-liner + indented detail paragraph (rule 4)
//   fig()   → document-illustration ratio: source PNG 1600px wide, 620–740px tall,
//             inserted at 6.5in — NOT slide ratio 1600×900
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, PageNumber, PageBreak, LevelFormat } = require("docx");

const F = "Microsoft JhengHei";
const FIGDIR = path.join(__dirname, "..", "figures"); // adjust to your 圖檔 dir

// ---------- helpers ----------
const t = (text, o = {}) => new TextRun({ text, font: F, size: o.size ?? 22, bold: o.bold, color: o.color });
const warn = (text) => t("▲" + text, { color: "C00000", bold: true }); // 待補/待確認
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(s, { size: 32, bold: true })] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(s, { size: 28, bold: true })] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [t(s, { size: 24, bold: true })] });
const P = (runs, o = {}) => new Paragraph({ spacing: { after: o.after ?? 120, line: 320 }, alignment: o.align, indent: o.indent ? { left: o.indent } : undefined, children: Array.isArray(runs) ? runs : [t(runs)] });
const brk = () => new Paragraph({ children: [new PageBreak()] });

// numbered lists: each call to list() opens a fresh 1,2,3… sequence
let LID = -1;
const list = () => { LID++; return `n${LID}`; };
const NI = (ref, runs) => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 320 }, children: Array.isArray(runs) ? runs : [t(runs)] });
// detail paragraph under a numbered claim (indented, softer color)
const DET = (runs) => P(Array.isArray(runs) ? runs : [t(runs, { color: "404040" })], { indent: 480, after: 140 });

const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(content, { w, bold, fill, align } = {}) {
  const runs = Array.isArray(content) ? content : [t(String(content), { size: 20, bold })];
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ alignment: align, spacing: { line: 300 }, children: runs })] });
}
function tbl(widths, rows) {
  return new Table({ columnWidths: widths, margins: { top: 60, bottom: 60, left: 120, right: 120 },
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => (c && c.__cell) ? c.node(widths[ci]) : cell(c, { w: widths[ci], bold: ri === 0, fill: ri === 0 ? "DCE6F1" : undefined, align: ri === 0 ? AlignmentType.CENTER : undefined })) })) });
}
const wc = (content, opts = {}) => ({ __cell: true, node: (w) => cell(content, { w, ...opts }) });
function fig(file, hpx, caption) {
  const wIn = 6.5, hIn = wIn * hpx / 1600;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: "png",
      data: fs.readFileSync(path.join(FIGDIR, file)), transformation: { width: Math.round(wIn * 96), height: Math.round(hIn * 96) },
      altText: { title: caption, description: caption, name: caption } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t(caption, { size: 20, bold: true })] })
  ];
}

// ---------- content ----------
const children = [];
let r; // current list ref

// Example — claim + detail work item (rule 4):
// r = list();
// children.push(
//   H3("（一）A1 CAD 解析引擎建置"),
//   NI(r, [t("讀入 DWG/DXF 圖檔，自動整理出圖面上的元件、線路、尺寸與標註。", { bold: true })]),
//   DET("工程師目前逐層人工看圖……本項目將這一步自動化，輸出結構化的圖面清單。"),
//   NI(r, [t("……", { bold: true }), warn("（試點數據待補）")]),
// );

// ---------- document ----------
const numbering = { config: Array.from({ length: LID + 1 }, (_, i) => ({
  reference: `n${i}`,
  levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START,
             style: { paragraph: { indent: { left: 360, hanging: 360 } } } }] })) };

const doc = new Document({
  numbering,
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1418, right: 1418 } } }, // A4, 2/2.5cm
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ font: F, size: 18, children: [PageNumber.CURRENT] })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "計畫書_草案.docx");
  fs.writeFileSync(out, buf);
  console.log("written:", out);
});
