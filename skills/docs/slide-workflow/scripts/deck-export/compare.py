"""Stack each HTML slide (top) over the PowerPoint rendering (bottom) for review.

Usage: python compare.py <workDir> <outDir>
workDir holds ref-NN.png (from extract.js) and ppt-NN.png (from pdftoppm).
"""
import sys
from pathlib import Path

from PIL import Image

work, out = Path(sys.argv[1]), Path(sys.argv[2])
refs = sorted(work.glob("ref-*.png"))
ppts = sorted(work.glob("ppt-*.png"))
if len(refs) != len(ppts):
    print(f"warn: {len(refs)} HTML slides but {len(ppts)} PowerPoint pages")
for i, (r, p) in enumerate(zip(refs, ppts), 1):
    a = Image.open(r).convert("RGB")
    a = a.resize((1280, round(1280 * a.height / a.width)))
    b = Image.open(p).convert("RGB").resize(a.size)
    c = Image.new("RGB", (a.width, a.height * 2 + 10), (255, 0, 0))
    c.paste(a, (0, 0))
    c.paste(b, (0, a.height + 10))
    c.save(out / f"cmp-{i:02d}.png")
print(f"{min(len(refs), len(ppts))} compare images")
