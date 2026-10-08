"""Index user-supplied anime media for scene-specific retrieval.

Place files in assets/anime/<show>/<character_or_topic>/; create sidecar .json
with source_url, rights_status, episode, timestamp_seconds and tags.
This is an opt-in local library, not a copyright-scraping service.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXT={".mp4":"video",".mov":"video",".webm":"video",".png":"image",".jpg":"image",".jpeg":"image",".webp":"image"}
def build(root: Path):
    records=[]
    if not root.exists():
        return records
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXT:
            continue
        meta=path.with_suffix(path.suffix+".json")
        info=json.loads(meta.read_text()) if meta.exists() else {}
        relative=path.relative_to(root)
        tags=list(dict.fromkeys([*relative.with_suffix("").parts,*info.get("tags",[])]))
        records.append({"id":hashlib.sha256(path.read_bytes()).hexdigest()[:16],
            "path":str(path),"kind":EXT[path.suffix.lower()],"tags":tags,
            "show":info.get("show",relative.parts[0] if len(relative.parts)>1 else ""),
            "episode":info.get("episode"),"timestamp_seconds":info.get("timestamp_seconds"),
            "source_url":info.get("source_url"),"rights_status":info.get("rights_status","unknown"),
            "reviewed":info.get("reviewed",False)})
    return records

def match(records, query):
    tokens={s.casefold() for s in query.replace("_"," ").split() if len(s)>2}
    results=[]
    for record in records:
        hay=" ".join(map(str,record["tags"])).casefold()
        score=sum(t in hay for t in tokens)
        if score:
            results.append((score,record))
    return [r for _,r in sorted(results,key=lambda x:(-x[0],x[1]["path"]))]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="assets/anime")
    p.add_argument("--output",default="output/anime_asset_index.json")
    p.add_argument("--query")
    args=p.parse_args()
    records=build(Path(args.root))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(records,indent=2)+"\n")
    print(f"Indexed {len(records)} local anime media assets")
    if args.query:
        print(json.dumps(match(records,args.query),indent=2))
if __name__=="__main__":
    main()
