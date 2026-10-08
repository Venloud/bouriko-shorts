"""Standalone anime media pull diagnostic.

Character lookup tests Jikan's public metadata/image API.
Video extraction requires an episode file already provided in the repo under
assets/anime/<slug>/season_<N>/episode_<N>.mp4 (or mkv/webm).
This tool does not scrape streaming sites or claim metadata contains video.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"clip_pull_test"
ANIME={
    "jujutsu_kaisen": {"title":"Jujutsu Kaisen","mal_id":40748},
    "naruto": {"title":"Naruto","mal_id":20},
    "one_piece": {"title":"One Piece","mal_id":21},
    "demon_slayer": {"title":"Kimetsu no Yaiba","mal_id":38000},
    "attack_on_titan": {"title":"Shingeki no Kyojin","mal_id":16498},
    "bleach": {"title":"Bleach","mal_id":269},
    "dragon_ball_z": {"title":"Dragon Ball Z","mal_id":813},
    "chainsaw_man": {"title":"Chainsaw Man","mal_id":44511},
    "solo_leveling": {"title":"Ore dake Level Up na Ken","mal_id":52299},
    "my_hero_academia": {"title":"Boku no Hero Academia","mal_id":31964},
}
def fetch_character(name):
    if not name.strip():
        return {"status":"skipped","reason":"no character name supplied"}
    url="https://api.jikan.moe/v4/characters?q="+quote(name)+"&limit=15"
    r=requests.get(url,timeout=(7,20),headers={"User-Agent":"BourikoMediaTest/1.0"})
    r.raise_for_status()
    matches=[x for x in r.json().get("data",[]) if name.casefold() in x.get("name","").casefold()]
    if not matches:
        return {"status":"not_found","query":name,"api":url}
    x=matches[0]
    images=x.get("images") or {}
    img=(images.get("jpg") or {}).get("image_url")
    result={"status":"metadata_found","name":x.get("name"),"mal_id":x.get("mal_id"),"url":x.get("url"),"image_url":img}
    if img:
        try:
            response=requests.get(img,timeout=(7,20),headers={"User-Agent":"BourikoMediaTest/1.0"})
            response.raise_for_status()
            if not response.headers.get("content-type","").startswith("image/") or len(response.content)<2000:
                raise RuntimeError("invalid image response")
            suffix=".png" if "png" in response.headers.get("content-type","") else ".jpg"
            file=OUT/("character_reference"+suffix)
            file.write_bytes(response.content)
            result.update(status="image_downloaded",downloaded_file=str(file.relative_to(ROOT)),bytes=len(response.content),rights_status="third_party_review_only")
        except (requests.RequestException,RuntimeError) as e:
            result.update(status="image_failed",error=str(e))
    return result

def find_episode(slug,season,episode):
    root=ROOT/"assets"/"anime"/slug/f"season_{season}"
    for ext in (".mp4",".mkv",".webm",".mov"):
        file=root/f"episode_{episode}{ext}"
        if file.is_file():
            return file
    return None

def extract_clip(slug,season,episode,seconds,duration):
    source=find_episode(slug,season,episode)
    if source is None:
        return {"status":"source_missing","expected_folder":f"assets/anime/{slug}/season_{season}/",
                "expected_basename":f"episode_{episode}.mp4","reason":"No user-provided episode footage. Metadata APIs do not supply full episodes."}
    metadata=source.with_suffix(source.suffix+".json")
    if not metadata.is_file():
        return {"status":"source_unverified","reason":"Missing provenance sidecar","expected_sidecar":str(metadata.relative_to(ROOT))}
    meta=json.loads(metadata.read_text())
    if meta.get("rights_status") not in {"licensed","user_supplied_review_only"} or not meta.get("source_url"):
        return {"status":"source_unverified","reason":"Need source_url and explicit rights_status in sidecar"}
    result=OUT/"sample_clip.mp4"
    command=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(seconds),"-i",str(source),"-t",str(duration),
             "-map","0:v:0","-map","0:a?","-vf","scale=720:-2","-c:v","libx264","-preset","veryfast",
             "-crf","24","-c:a","aac","-movflags","+faststart",str(result)]
    subprocess.run(command,check=True,timeout=180)
    probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(result)],text=True,timeout=20).strip()
    if not result.exists() or result.stat().st_size<5000 or float(probe)<0.5:
        raise RuntimeError("clip extraction produced no usable video")
    return {"status":"clip_extracted","file":str(result.relative_to(ROOT)),"seconds":seconds,
            "duration":float(probe),"bytes":result.stat().st_size,"source":str(source.relative_to(ROOT)),
            "rights_status":meta["rights_status"],"source_url":meta["source_url"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--anime",choices=ANIME,default="jujutsu_kaisen")
    p.add_argument("--season",type=int,default=None)
    p.add_argument("--episode",type=int,default=None)
    p.add_argument("--character",default="")
    p.add_argument("--mode",choices=["image","clip","both","catalog"],default="catalog")
    p.add_argument("--timestamp",type=float,default=None)
    p.add_argument("--duration",type=float,default=None)
    args=p.parse_args()
    if args.season<1 or args.episode<1 or args.timestamp<0 or not 0.5<=args.duration<=20:
        p.error("Season/episode must be positive, timestamp >= 0, duration 0.5-20 seconds")
    OUT.mkdir(parents=True,exist_ok=True)
    report={"anime":args.anime,"anime_title":ANIME[args.anime]["title"],
            "season":args.season,"episode":args.episode,"character_query":args.character,
            "mode":args.mode,"requested_timestamp":args.timestamp,"requested_duration":args.duration}
    if args.mode == "catalog":
        report["catalog"]={"status":"catalog_only","available_anime":[{"id":key,**value} for key,value in ANIME.items()],
                           "note":"Anime list is metadata only, not an episode-video provider"}
    if args.mode in {"image","both"}:
        try:
            report["image"]=fetch_character(args.character)
        except Exception as exc:
            report["image"]={"status":"network_error","error":str(exc)}
    if args.mode in {"clip","both"}:
        try:
            report["clip"]=extract_clip(args.anime,args.season,args.episode,args.timestamp,args.duration)
        except Exception as exc:
            report["clip"]={"status":"extract_error","error":str(exc)}
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2),flush=True)
    attempted=[report[k]["status"] for k in ("image","clip") if k in report and report[k]["status"]!="skipped"]
    passed=args.mode=="catalog" or any(x in {"image_downloaded","clip_extracted"} for x in attempted)
    if not passed:
        raise SystemExit("TEST FAILED: no actual image downloaded or clip extracted. See report.json")
    print("TEST PASS: catalog generated." if args.mode=="catalog" else "TEST PASS: at least one actual media file created. Inspect report for partial failures.")
if __name__=="__main__":
    main()
