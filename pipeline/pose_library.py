"""Build a reusable pose library and review sheet from Bouriko reference sheets."""
import json, math
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from common import ROOT
POSES=ROOT/"assets/poses"; REFS=ROOT/"assets/reference"
def _files():
    return [p for p in REFS.rglob("*") if p.suffix.lower() in {".png",".jpg",".jpeg"}]
def _crop_sheet(p):
    im=Image.open(p).convert("RGBA")
    # First pass: remove near-white pixels; connected components become candidate pose boxes.
    rgb=im.convert("RGB")
    bg=Image.new("RGB",rgb.size,"white")
    diff=ImageOps.invert(ImageOps.grayscale(ImageOps.autocontrast(ImageOps.difference(rgb,bg))))
    mask=ImageOps.invert(diff.point(lambda x: 255 if x<245 else 0))
    # Grid fallback is safer for the supplied pose sheet: split into 4x4 cells and keep non-empty cells.
    w,h=im.size; boxes=[]
    for rows,cols in [(4,4),(3,4),(4,3)]:
        cells=[]
        for r in range(rows):
            for c in range(cols):
                box=(c*w//cols,r*h//rows,(c+1)*w//cols,(r+1)*h//rows)
                cell=im.crop(box).convert("RGB")
                extrema=ImageOps.grayscale(ImageOps.autocontrast(ImageOps.difference(cell,Image.new("RGB",cell.size,"white")))).getextrema()
                if extrema[1]>35: cells.append(box)
        if len(cells)>=4: boxes=cells; break
    return im,boxes
def build():
    POSES.mkdir(parents=True,exist_ok=True); items=[]
    for src in _files():
        im,boxes=_crop_sheet(src)
        for i,b in enumerate(boxes):
            crop=im.crop(b)
            # Trim transparent/near-white border.
            crop.save(POSES/f"{src.stem}_{i:02}.png")
            items.append({"name":f"{src.stem}_{i:02}","file":f"assets/poses/{src.stem}_{i:02}.png","tags":["candidate"]})
    (POSES/"poses.json").write_text(json.dumps(items,indent=2))
    if not items: raise RuntimeError("No reference poses found")
    thumbs=[]
    for x in items:
        im=Image.open(ROOT/x["file"]).convert("RGB"); im.thumbnail((180,260)); thumbs.append((x["name"],im.copy()))
    sheet=Image.new("RGB",(800,max(1,math.ceil(len(thumbs)/4))*310),"white"); d=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(thumbs):
        x=(i%4)*200;y=(i//4)*310;sheet.paste(im,(x+(180-im.width)//2,y));d.text((x+5,y+265),name,fill="black")
    sheet.save(ROOT/"output/pose_review.png")
if __name__=="__main__": build()
