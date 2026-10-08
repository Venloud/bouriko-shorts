"""Create timed character image cues from a word- or sentence-timed transcript."""
import argparse
import json
import re
from pathlib import Path

CHARACTERS={
 "jujutsu_kaisen":{
  "gojo":("Satoru Gojo",["satoru gojo","satoru gojou","gojo","gojou"]),
  "yuji":("Yuji Itadori",["yuji itadori","yuji","yuuji","itadori"]),
  "megumi":("Megumi Fushiguro",["megumi fushiguro","megumi","fushiguro"]),
  "nobara":("Nobara Kugisaki",["nobara kugisaki","nobara","kugisaki"]),
  "sukuna":("Ryomen Sukuna",["ryomen sukuna","sukuna"])},
 "naruto":{
  "naruto":("Naruto Uzumaki",["naruto uzumaki","naruto"]),
  "sasuke":("Sasuke Uchiha",["sasuke uchiha","sasuke"]),
  "kakashi":("Kakashi Hatake",["kakashi hatake","kakashi"])}
}
def make_timeline(data,manifest=None,hold=1.8):
    anime=data.get("anime")
    if anime not in CHARACTERS:
        raise ValueError("Unsupported anime: "+str(anime))
    segments=data.get("segments")
    if not isinstance(segments,list):
        raise ValueError("segments must be a list")
    if hold<=0:
        raise ValueError("hold must be positive")
    manifest=manifest or {}
    cues=[]
    for i,segment in enumerate(segments):
        start=float(segment["start"])
        end=float(segment["end"])
        if start<0 or end<=start:
            raise ValueError("Invalid segment times at index "+str(i))
        words=segment.get("text","")
        if not isinstance(words,str):
            raise ValueError("segment text must be a string")
        for key,(name,aliases) in CHARACTERS[anime].items():
            matches=[a for a in aliases if re.search(r"(?<!\\w)"+re.escape(a)+r"(?!\\w)",words,re.I)]
            if matches:
                cues.append({"start":start,"end":max(end,start+hold),
                             "anime":anime,"character_id":key,"character":name,
                             "matched_alias":max(matches,key=len),"segment_index":i,
                             "image_path":manifest.get(anime,{}).get(key),
                             "effect":{"type":"slow_zoom","scale_start":1.0,"scale_end":1.08}})
    cues.sort(key=lambda x:(x["start"],x["character_id"]))
    return {"anime":anime,"count":len(cues),"cues":cues,
            "missing_images":sorted({c["character_id"] for c in cues if not c["image_path"]})}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript",type=Path)
    parser.add_argument("--manifest",type=Path)
    parser.add_argument("--output",type=Path,default=Path("output/character_timeline.json"))
    parser.add_argument("--hold",type=float,default=1.8)
    args=parser.parse_args()
    data=json.loads(args.transcript.read_text(encoding="utf-8"))
    manifest=json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
    result=make_timeline(data,manifest,args.hold)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
