"""Fetch JJK character reference images for experimental review rendering.

Uses Jikan character search. Images are third-party copyrighted references,
not licensed stock. This workflow is REVIEW ONLY and must not auto-publish.
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]
STORY=ROOT/"output/story.json"
OUT=ROOT/"output"
CHARACTERS={
    "Kenjaku":["Kenjaku"],
    "YUJI AND MEGUMI":["Yuji Itadori","Megumi Fushiguro"],
    "GAME MASTER":["Kogane"],
}
def fetch_character(name):
    endpoint="https://api.jikan.moe/v4/characters?q="+quote(name)+"&limit=10"
    resp=requests.get(endpoint,timeout=25)
    resp.raise_for_status()
    for item in resp.json().get("data",[]):
        if item.get("name","").casefold()!=name.casefold():
            continue
        image=((item.get("images") or {}).get("jpg") or {}).get("image_url")
        if not image:
            continue
        photo=requests.get(image,timeout=25,headers={"User-Agent":"BourikoExperimentalReview/1.0"})
        photo.raise_for_status()
        if not photo.headers.get("content-type","").startswith("image/"):
            continue
        return photo.content, image, item.get("url")
    return None

def main():
    story=json.loads(STORY.read_text())
    manifest=[]
    matches=[]
    cache={}
    media=OUT/"anime_images"
    media.mkdir(parents=True,exist_ok=True)
    for i,line in enumerate(story["lines"]):
        visual=line.get("visual","")
        names=CHARACTERS.get(visual,[])
        selected=None
        for name in names:
            if name not in cache:
                try:
                    cache[name]=fetch_character(name)
                except (requests.RequestException,ValueError) as exc:
                    print("Image lookup unavailable:",name,type(exc).__name__,str(exc)[:160])
                    cache[name]=None
                time.sleep(0.4)
            result=cache[name]
            if result:
                raw,image_url,character_url=result
                filename=re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")+".jpg"
                path=media/filename
                path.write_bytes(raw)
                selected={"scene":i,"kind":"image","provider":"jikan_character_reference",
                    "character":name,"path":str(path.relative_to(ROOT)),
                    "source_url":character_url,"image_url":image_url,
                    "rights_status":"review_only_unlicensed","reviewed":False}
                line["media_kind"]="image"
                line["media_asset"]=str(path.relative_to(ROOT))
                print("Reference image prepared:",name)
                break
        if selected:
            manifest.append(selected)
            matches.append({"scene":i,"status":"reference_image","character":selected["character"],"rights_status":"review_only_unlicensed"})
        else:
            line["media_kind"]="motion_graphic"
            line.pop("media_asset",None)
            manifest.append({"scene":i,"kind":"motion_graphic","provider":"remotion","visual_type":line.get("anime_visual_type")})
            matches.append({"scene":i,"status":"graphic"})
    STORY.write_text(json.dumps(story,indent=2)+"\n")
    (OUT/"media_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (OUT/"scene_matches.json").write_text(json.dumps(matches,indent=2)+"\n")
    print("Prepared",sum(x["kind"]=="image" for x in manifest),"reference-image scenes out of",len(manifest))
if __name__=="__main__":
    main()
