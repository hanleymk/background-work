"""Run under the venv python (has Pillow): resize.py <rawdir> <outdir>. Output: <name>_t.jpg (640px) and <name>_l.jpg (1600px)."""
import os, sys
from PIL import Image, ImageOps
src, dst = sys.argv[1:3]
for f in os.listdir(src):
    name = os.path.splitext(f)[0]
    im = ImageOps.exif_transpose(Image.open(os.path.join(src, f))).convert("RGB")
    for suf, px, q in (("t", 640, 78), ("l", 1600, 78)):
        c = im.copy(); c.thumbnail((px, px)); c.save(os.path.join(dst, f"{name}_{suf}.jpg"), quality=q, optimize=True, progressive=True)
