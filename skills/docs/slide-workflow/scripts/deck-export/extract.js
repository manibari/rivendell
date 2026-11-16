// Render an HTML deck and write its layout as data: boxes, images, rasters and text runs.
// Also writes one 2x screenshot per slide (ref-NN.png) for the image deck and for checks.
//
// Usage: node extract.js <deck.html> <outDir> [--selector .slide] [--keep-font]
//
// By default the page is laid out with the font that the PPTX uses (Microsoft JhengHei,
// taken from the PowerPoint app bundle), so line breaks in HTML and PPTX agree.
// --keep-font measures with the deck's own fonts instead.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const deck = path.resolve(args[0]);
const out = path.resolve(args[1]);
const selector = opt('--selector', '.slide');
const keepFont = args.includes('--keep-font');
fs.mkdirSync(path.join(out, 'r'), { recursive: true });

const FONT_DIRS = [
  '/Applications/Microsoft PowerPoint.app/Contents/Resources/Fonts',
  '/Applications/Microsoft Word.app/Contents/Resources/Fonts',
];
const fontDir = FONT_DIRS.find(d => fs.existsSync(path.join(d, 'MSJH.ttf')));
const fontCss = d => `
@font-face { font-family: 'MSJHX'; src: url('file://${encodeURI(d)}/MSJH.ttf'); font-weight: 100 600; }
@font-face { font-family: 'MSJHX'; src: url('file://${encodeURI(d)}/MSJHBD.ttf'); font-weight: 601 900; }
body, body * { font-family: 'MSJHX', sans-serif !important; }
`;

async function launch() {
  try { return await chromium.launch(); } catch (e) {
    const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    if (!fs.existsSync(chrome)) throw e;
    return chromium.launch({ executablePath: chrome });
  }
}

(async () => {
  const browser = await launch();
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.goto('file://' + deck, { waitUntil: 'networkidle' });
  let measuredWith = 'deck fonts';
  if (!keepFont && fontDir) {
    await page.addStyleTag({ content: fontCss(fontDir) });
    measuredWith = 'Microsoft JhengHei';
  } else if (!keepFont) {
    console.error('warn: Microsoft JhengHei not found; line breaks are measured with the deck fonts');
  }
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.waitForTimeout(800);

  const slides = await page.evaluate(sel => {
    const px = v => parseFloat(v) || 0;
    const parse = c => {
      const m = c && c.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
      return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
    };
    const mix = (c, under, a) => ({ r: c.r * a + under.r * (1 - a), g: c.g * a + under.g * (1 - a), b: c.b * a + under.b * (1 - a), a: 1 });
    const hex = c => [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
    const WHITE = { r: 255, g: 255, b: 255, a: 1 };
    const isInline = el => ['inline', 'contents'].includes(getComputedStyle(el).display) && el.tagName !== 'svg' && el.tagName !== 'IMG';
    const SIDES = ['Top', 'Right', 'Bottom', 'Left'];

    let rx = 0;
    const result = [];
    document.querySelectorAll(sel).forEach(slide => {
      const S = slide.getBoundingClientRect();
      const items = [];
      let order = 0;
      const rel = r => ({ x: r.left - S.left, y: r.top - S.top, w: r.width, h: r.height });

      // ctx: layer (paint layer), under (opaque color behind), op (opacity product),
      //      clip (overflow clip box), rclip (rounded clip box)
      function walk(el, ctx) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const op = ctx.op * (cs.opacity === '' ? 1 : px(cs.opacity));
        if (op <= 0.01) return;
        let layer = ctx.layer;
        if (cs.position !== 'static') {
          const z = parseInt(cs.zIndex);
          layer = Math.max(layer, isNaN(z) ? 1 : 1 + z);
        }
        const r = rel(el.getBoundingClientRect());
        let under = ctx.under;

        // 1. images: keep the original file, crop to the visible part
        if (el.tagName === 'IMG') {
          const c = ctx.clip;
          const x0 = Math.max(r.x, c.x), y0 = Math.max(r.y, c.y);
          const x1 = Math.min(r.x + r.w, c.x + c.w), y1 = Math.min(r.y + r.h, c.y + c.h);
          if (x1 - x0 > 1 && y1 - y0 > 1) {
            const u = new URL(el.src);
            items.push({ t: 'img', layer, o: order++, src: u.protocol === 'file:' ? decodeURI(u.pathname) : null, url: el.src,
              x: x0, y: y0, w: x1 - x0, h: y1 - y0,
              crop: { l: (x0 - r.x) / r.w, t: (y0 - r.y) / r.h, r: (r.x + r.w - x1) / r.w, b: (r.y + r.h - y1) / r.h } });
          }
          return;
        }
        // 2. inline svg: raster without its <text>; the text is written as native text
        if (el.tagName === 'svg') {
          const id = 'rx' + (rx++);
          el.setAttribute('data-rx', id);
          items.push({ t: 'raster', layer, o: order++, id, mode: 'svg', ...r });
          el.querySelectorAll('text').forEach(tx => {
            const tr = rel(tx.getBoundingClientRect());
            const ts = getComputedStyle(tx);
            const fill = parse(ts.fill) || { r: 0, g: 0, b: 0, a: 1 };
            const anchor = ts.textAnchor;
            items.push({ t: 'text', layer, o: order++, x: tr.x, y: tr.y, w: tr.w, h: tr.h, wrap: false,
              align: anchor === 'middle' ? 'c' : anchor === 'end' ? 'r' : 'l', lh: tr.h,
              paras: [[{ s: tx.textContent, size: px(ts.fontSize), color: hex(mix(fill, under, fill.a * op)), bold: px(ts.fontWeight) >= 600, ls: px(ts.letterSpacing) }]] });
          });
          return;
        }

        // 3. own box: background and borders become a shape; gradients, background
        //    images, pseudo-elements and transforms become a raster of this element only
        const bg = parse(cs.backgroundColor);
        const pseudo = ['::before', '::after'].some(p => {
          const s = getComputedStyle(el, p);
          return s.content && s.content !== 'none' && s.content !== 'normal';
        });
        let boxItem = null;
        if (cs.backgroundImage !== 'none' || pseudo || (cs.transform !== 'none' && !isInline(el))) {
          const id = 'rx' + (rx++);
          el.setAttribute('data-rx', id);
          items.push({ t: 'raster', layer, o: order++, id, mode: 'self', ...r });
        } else if (!isInline(el)) {
          const bw = SIDES.map(s => cs['border' + s + 'Style'] === 'none' ? 0 : px(cs['border' + s + 'Width']));
          const bc = SIDES.map(s => parse(cs['border' + s + 'Color']));
          const fill = bg && bg.a > 0 ? mix(bg, under, bg.a * op) : null;
          const rad = Math.min(px(cs.borderTopLeftRadius), r.w / 2, r.h / 2);
          const any = bw.some(w => w > 0);
          if (fill || any) {
            const uni = bw.every(w => w === bw[0]) && bc.every(c => c && hex(c) === hex(bc[0]) && c.a === bc[0].a)
              && SIDES.every(s => cs['border' + s + 'Style'] === cs.borderTopStyle);
            boxItem = { t: 'rect', layer, o: order++, ...r, fill: fill ? hex(fill) : null, rad, line: null, dash: false };
            const rc = ctx.rclip;  // header strip at the top of a rounded card
            if (rc && !rad && Math.abs(r.y - rc.y) < 1.5 && Math.abs(r.x - rc.x) < 1.5 && Math.abs(r.w - rc.w) < 1.5) {
              boxItem.rad = rc.rad;
              boxItem.topOnly = Math.abs(r.h - rc.h) > 1.5;
            }
            if (any && uni) {
              boxItem.line = { color: hex(mix(bc[0], under, bc[0].a * op)), w: bw[0] };
              boxItem.dash = cs.borderTopStyle === 'dashed';
            }
            items.push(boxItem);
            if (any && !uni) {
              const sides = [[r.x, r.y, r.w, bw[0]], [r.x + r.w - bw[1], r.y, bw[1], r.h],
                [r.x, r.y + r.h - bw[2], r.w, bw[2]], [r.x, r.y, bw[3], r.h]];
              sides.forEach((s, i) => {
                if (bw[i] > 0 && bc[i] && bc[i].a > 0)
                  items.push({ t: 'rect', layer, o: order++, x: s[0], y: s[1], w: s[2], h: s[3], fill: hex(mix(bc[i], under, bc[i].a * op)), rad: 0, line: null });
              });
            }
          }
          if (fill) under = fill;
        }

        // 4. text block: the inline content of a non-inline element
        if (!isInline(el)) {
          const runs = [];
          const rects = [];
          const collect = (node, owner) => {
            for (const n of node.childNodes) {
              if (n.nodeType === 3) {
                if (!n.textContent.trim() && !runs.length) continue;
                const s = getComputedStyle(owner);
                const range = document.createRange();
                range.selectNodeContents(n);
                for (const cr of range.getClientRects()) if (cr.width > 0) rects.push(cr);
                const col = parse(s.color) || { r: 0, g: 0, b: 0, a: 1 };
                let ownerOp = 1;
                for (let a = owner; a && a !== el; a = a.parentElement) ownerOp *= px(getComputedStyle(a).opacity);
                let txt = n.textContent;
                if (s.textTransform === 'uppercase') txt = txt.toUpperCase();
                runs.push({ s: txt, size: px(s.fontSize), color: hex(mix(col, under, col.a * op * ownerOp)),
                  bold: px(s.fontWeight) >= 600, ls: px(s.letterSpacing), italic: s.fontStyle === 'italic', ws: s.whiteSpace });
              } else if (n.nodeType === 1) {
                if (n.tagName === 'BR') { runs.push({ br: true }); continue; }
                if (getComputedStyle(n).display === 'none') continue;
                if (isInline(n)) {
                  // a margin or padding between inline spans becomes one space
                  const ns = getComputedStyle(n);
                  const gapL = px(ns.marginLeft) + px(ns.paddingLeft), gapR = px(ns.marginRight) + px(ns.paddingRight);
                  const sp = () => { const c = parse(ns.color) || { r: 0, g: 0, b: 0, a: 1 }; return { s: ' ', keep: true, size: px(ns.fontSize), color: hex(mix(c, under, c.a * op)), bold: false, ls: 0, ws: 'pre' }; };
                  if (gapL >= 3 && runs.length) runs.push(sp());
                  collect(n, n);
                  if (gapR >= 3) runs.push(sp());
                }
              }
            }
          };
          collect(el, el);
          let prevSpace = true;  // collapse white space across runs, as the browser does
          for (const run of runs) {
            if (run.br) { prevSpace = true; continue; }
            if (run.keep) {
              if (prevSpace) run.s = ''; else prevSpace = true;
            } else if (!/pre/.test(run.ws)) {
              run.s = run.s.replace(/\s+/g, ' ');
              if (prevSpace) run.s = run.s.replace(/^ /, '');
              if (run.s) prevSpace = run.s.endsWith(' ');
            }
          }
          for (let i = runs.length - 1; i >= 0; i--) { if (runs[i].br) continue; runs[i].s = runs[i].s.replace(/ $/, ''); if (runs[i].s) break; }
          const live = runs.filter(x => x.br || x.s);
          if (live.some(x => !x.br) && rects.length) {
            const L = Math.min(...rects.map(q => q.left)) - S.left, R = Math.max(...rects.map(q => q.right)) - S.left;
            const T = Math.min(...rects.map(q => q.top)) - S.top, B = Math.max(...rects.map(q => q.bottom)) - S.top;
            const tops = [];
            rects.forEach(q => { if (!tops.some(t => Math.abs(t - q.top) < 4)) tops.push(q.top); });
            const contentH = Math.max(...rects.map(q => q.height));
            const lh = cs.lineHeight === 'normal' ? contentH : px(cs.lineHeight);
            const pad = (lh - contentH) / 2;
            const ta = cs.textAlign;
            const align = ta === 'center' ? 'c' : (ta === 'right' || ta === 'end') ? 'r' : 'l';
            const cbx = r.x + px(cs.paddingLeft) + px(cs.borderLeftWidth);
            const cbw = r.w - px(cs.paddingLeft) - px(cs.paddingRight) - px(cs.borderLeftWidth) - px(cs.borderRightWidth);
            let tb, indent = 0;
            if (tops.length === 1) {
              // one line: no wrap in PPTX, so a slightly wider rendering cannot add a line
              const w = R - L;
              const extra = Math.max(8, w * 0.06);
              tb = { x: align === 'c' ? L - extra / 2 : align === 'r' ? L - extra : L, w: w + extra, wrap: false };
            } else {
              tb = { x: cbx, w: cbw + Math.max(2, cbw * 0.004), wrap: true };
              const firstTop = Math.min(...tops);
              const firstLeft = Math.min(...rects.filter(q => Math.abs(q.top - firstTop) < 4).map(q => q.left)) - S.left;
              if (align === 'l' && firstLeft - cbx > 2) indent = firstLeft - cbx;  // text after an inline badge
            }
            const paras = [[]];
            live.forEach(x => { if (x.br) paras.push([]); else paras[paras.length - 1].push({ s: x.s, size: x.size, color: x.color, bold: x.bold, ls: x.ls, italic: x.italic }); });
            const ti = { t: 'text', layer, o: order++, x: tb.x, y: T - pad, w: tb.w, h: (B - T) + 2 * pad, wrap: tb.wrap,
              align, lh, paras, indent, vmid: Math.abs((T + B) / 2 - (r.y + r.h / 2)) < 2 };
            if (boxItem && !boxItem.topOnly) boxItem.text = ti; else items.push(ti);
          }
        }

        // 5. children
        let clip = ctx.clip, rclip = ctx.rclip;
        if (cs.overflow !== 'visible' && !isInline(el)) {
          const x0 = Math.max(clip.x, r.x), y0 = Math.max(clip.y, r.y);
          const x1 = Math.min(clip.x + clip.w, r.x + r.w), y1 = Math.min(clip.y + clip.h, r.y + r.h);
          clip = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
          if (px(cs.borderTopLeftRadius) > 0) rclip = { ...r, rad: px(cs.borderTopLeftRadius) };
        }
        for (const ch of el.children) walk(ch, { layer, under, op, clip, rclip });
      }

      const sbg = parse(getComputedStyle(slide).backgroundColor);
      const base = sbg && sbg.a > 0 ? sbg : WHITE;
      for (const ch of slide.children) walk(ch, { layer: 0, under: base, op: 1, clip: { x: 0, y: 0, w: S.width, h: S.height }, rclip: null });
      result.push({ bg: hex(base), w: S.width, h: S.height, items });
    });
    return result;
  }, selector);

  if (!slides.length) throw new Error(`no element matches ${selector}`);

  // reference screenshot of each slide
  const els = await page.$$(selector);
  for (let i = 0; i < els.length; i++) {
    slides[i].ref = path.join(out, `ref-${String(i + 1).padStart(2, '0')}.png`);
    await els[i].screenshot({ path: slides[i].ref, animations: 'disabled' });
  }

  // rasters: show one element at a time on a transparent page
  const jobs = slides.flatMap(s => s.items.filter(i => i.t === 'raster'));
  const base = `html,body,${selector}{background:transparent!important;box-shadow:none!important}*{visibility:hidden!important}`;
  for (const j of jobs) {
    const css = base + (j.mode === 'svg'
      ? `[data-rx="${j.id}"],[data-rx="${j.id}"] *{visibility:visible!important}[data-rx="${j.id}"] text{visibility:hidden!important}`
      : `[data-rx="${j.id}"]{visibility:visible!important;color:transparent!important}[data-rx="${j.id}"] *{visibility:hidden!important}`);
    const tag = await page.addStyleTag({ content: css });
    j.png = path.join(out, 'r', j.id + '.png');
    await (await page.$(`[data-rx="${j.id}"]`)).screenshot({ path: j.png, omitBackground: true, animations: 'disabled' });
    await tag.evaluate(t => t.remove());
  }

  const missing = slides.flatMap(s => s.items.filter(i => i.t === 'img' && !i.src)).map(i => i.url);
  if (missing.length) console.error('warn: images not on disk are skipped:', missing.join(', '));
  fs.writeFileSync(path.join(out, 'layout.json'), JSON.stringify({ measuredWith, slides }, null, 1));
  console.log(`slides ${slides.length}, items ${slides.reduce((a, s) => a + s.items.length, 0)}, rasters ${jobs.length}, measured with ${measuredWith}`);
  await browser.close();
})().catch(e => { console.error(e.message || e); process.exit(1); });
