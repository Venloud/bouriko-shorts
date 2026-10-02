"""Build a cut-out pose library from Bouriko reference sheets."""
import json, math
from pathlib import Path
from PIL import Image, ImageChops, ImageOps, ImageDraw

from common import ROOT

POSES = ROOT / "assets/poses"
REFS = ROOT / "assets/reference"
_REMBG_SESSION = None
_REMBG_OK = None

def _files():
    return [p for p in REFS.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]

def _grid_boxes(im):
    w, h = im.size
    for rows, cols in ((4, 4), (3, 4), (4, 3), (5, 4)):
        boxes = []
        for r in range(rows):
            for c in range(cols):
                b = (c*w//cols, r*h//rows, (c+1)*w//cols, (r+1)*h//rows)
                cell = im.crop(b).convert("RGB")
                diff = ImageOps.grayscale(ImageChops.difference(cell, Image.new("RGB", cell.size, "white")))
                if diff.getextrema()[1] > 35:
                    boxes.append(b)
        if len(boxes) >= 4:
            return boxes
    return []

def _cutout(im):
    global _REMBG_SESSION, _REMBG_OK
    if _REMBG_OK is not False:
        try:
            from rembg import remove, new_session
            if _REMBG_SESSION is None:
                _REMBG_SESSION = new_session("u2netp")
            _REMBG_OK = True
            return remove(im, session=_REMBG_SESSION).convert("RGBA")
        except Exception:
            _REMBG_OK = False

    rgba = im.convert("RGBA")
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if r > 245 and g > 245 and b > 245:
                px[x, y] = (r, g, b, 0)
    return rgba

def _trim(im):
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im

def build():
    POSES.mkdir(parents=True, exist_ok=True)
    items = []
    for src in _files():
        sheet = Image.open(src).convert("RGBA")
        for i, box in enumerate(_grid_boxes(sheet)):
            crop = _trim(_cutout(sheet.crop(box)))
            if crop.width < 40 or crop.height < 40:
                continue
            name = f"{src.stem}_{i:02}"
            out = POSES / f"{name}.png"
            crop.save(out)
            items.append({
                "name": name,
                "file": f"assets/poses/{name}.png",
                "tags": ["talking", "pointing", "confused", "phone"],
            })
    if not items:
        raise RuntimeError("No usable reference poses found")
    (POSES / "poses.json").write_text(json.dumps(items, indent=2))

    thumbs = []
    for item in items:
        im = Image.open(ROOT / item["file"]).convert("RGBA")
        im.thumbnail((180, 260))
        card = Image.new("RGBA", (190, 280), "white")
        card.alpha_composite(im, ((190-im.width)//2, 4))
        ImageDraw.Draw(card).text((5, 262), item["name"], fill="black")
        thumbs.append(card.convert("RGB"))

    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols*190, max(1, rows)*280), "white")
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols)*190, (i // cols)*280))
    (ROOT / "output").mkdir(exist_ok=True)
    sheet.save(ROOT / "output/pose_review.png")

if __name__ == "__main__":
    build()
