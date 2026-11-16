"""Build a PPTX from layout.json (written by extract.js).

Usage: python build_pptx.py <layout.json> <out.pptx> [--image] [--font NAME] [--title TEXT]

Default: an editable deck. Text is native text boxes, boxes are native shapes, pictures
use the original files. --image: one full-slide screenshot per slide (exact look, no edits).
"""
import argparse
import json

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

PX = 9525  # EMU per CSS px (96 dpi)
ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
FONT = "Microsoft JhengHei"


def E(v):
    return Emu(int(round(v * PX)))


def no_style(shape):
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


def set_font(run, f):
    font = run.font
    font.size = Emu(int(round(f["size"] * 0.75 * 100)) * 127)  # exact size in 1/100 pt
    font.bold = bool(f.get("bold"))
    font.italic = bool(f.get("italic"))
    font.color.rgb = RGBColor.from_string(f["color"])
    rPr = run._r.get_or_add_rPr()
    rPr.set("lang", "zh-TW")  # lets PowerPoint apply Chinese line-break rules
    rPr.set("altLang", "en-US")
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT)
    if f.get("ls"):
        rPr.set("spc", str(int(round(f["ls"] * 0.75 * 100))))


def fill_text(tf, t, inset):
    tf.word_wrap = bool(t["wrap"])
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (E(v) for v in inset)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, para in enumerate(t["paras"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ALIGN[t["align"]]
        p.line_spacing = Pt(t["lh"] * 0.75)
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        if i == 0 and t.get("indent"):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "0")
            pPr.set("indent", str(int(round(t["indent"] * PX))))
        for f in para:
            r = p.add_run()
            r.text = f["s"]
            set_font(r, f)


def add_text(slide, t):
    tb = slide.shapes.add_textbox(E(t["x"]), E(t["y"]), E(t["w"]), E(t["h"]))
    fill_text(tb.text_frame, t, (0, 0, 0, 0))


def add_rect(slide, it):
    rad = it.get("rad") or 0
    if rad and it.get("topOnly"):
        kind = MSO_SHAPE.ROUND_2_SAME_RECTANGLE
    elif rad:
        kind = MSO_SHAPE.ROUNDED_RECTANGLE
    else:
        kind = MSO_SHAPE.RECTANGLE
    lw = it["line"]["w"] if it.get("line") else 0
    # a CSS border is inside the box; a PowerPoint line is centered on the edge
    x, y, w, h = it["x"] + lw / 2, it["y"] + lw / 2, it["w"] - lw, it["h"] - lw
    sh = slide.shapes.add_shape(kind, E(x), E(y), E(max(w, 0.5)), E(max(h, 0.5)))
    no_style(sh)
    if rad:
        sh.adjustments[0] = min(0.5, rad / max(min(w, h), 1))
    if it.get("fill"):
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(it["fill"])
    else:
        sh.fill.background()
    if it.get("line"):
        sh.line.color.rgb = RGBColor.from_string(it["line"]["color"])
        sh.line.width = E(lw)
        if it.get("dash"):
            etree.SubElement(sh.line._get_or_add_ln(), qn("a:prstDash")).set("val", "dash")
    else:
        sh.line.fill.background()
    t = it.get("text")
    if t:
        # a rounded rectangle insets its text area by 0.29289 x corner radius on each side
        il = 0.29289 * min(rad, min(w, h) / 2) if kind == MSO_SHAPE.ROUNDED_RECTANGLE else 0
        left = max(t["x"] - x - il, 0)
        right = max((x + w) - (t["x"] + t["w"]) - il, 0)
        top = 0 if t.get("vmid") else max(t["y"] - y - il, 0)
        fill_text(sh.text_frame, t, (left, top, right, 0))
        sh.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE if t.get("vmid") else MSO_ANCHOR.TOP


def add_img(slide, it):
    if not it.get("src"):
        return
    pic = slide.shapes.add_picture(it["src"], E(it["x"]), E(it["y"]), E(it["w"]), E(it["h"]))
    c = it["crop"]
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = c["l"], c["t"], c["r"], c["b"]


def add_raster(slide, it):
    slide.shapes.add_picture(it["png"], E(it["x"]), E(it["y"]), E(it["w"]), E(it["h"]))


def main():
    global FONT
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("out")
    ap.add_argument("--image", action="store_true")
    ap.add_argument("--font", default=FONT)
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    FONT = a.font
    data = json.load(open(a.layout))
    first = data["slides"][0]
    prs = Presentation()
    prs.slide_width, prs.slide_height = E(first["w"]), E(first["h"])
    blank = prs.slide_layouts[6]
    for s in data["slides"]:
        slide = prs.slides.add_slide(blank)
        if a.image:
            slide.shapes.add_picture(s["ref"], 0, 0, prs.slide_width, prs.slide_height)
            continue
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string(s["bg"])
        draw = {"rect": add_rect, "text": add_text, "img": add_img, "raster": add_raster}
        for it in sorted(s["items"], key=lambda i: (i["layer"], i["o"])):
            draw[it["t"]](slide, it)
    cp = prs.core_properties  # do not leave the python-pptx defaults in the file
    cp.title = cp.author = cp.last_modified_by = a.title
    cp.subject = cp.keywords = cp.comments = ""
    prs.save(a.out)


if __name__ == "__main__":
    main()
