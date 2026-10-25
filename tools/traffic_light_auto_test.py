#!/usr/bin/env python3
"""Bounded automatic traffic-light media discovery + review clip test.
Runs on GitHub Actions without requiring the owner's Windows machine.
Generated clips are PROVISIONAL until semantic scene and rights verification.
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"traffic_light_auto_test"
CLIPS=OUT/"clips"
SOURCE=OUT/"source.mp4"
REPORT=OUT/"report.json"
SEARCH="ytsearch6:traffic signal intersection cars red green driving traffic light"
LABELS=["car_arrives","light_turns_red","light_turns_green","car_leaves"]

def run(args, **kw):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)

def status(stage, error=None, **info):
    OUT.mkdir(parents=True,exist_ok=True)
    d=dict(stage=stage, success=(error is None), error=error, **info)
    REPORT.write_text(json.dumps(d,indent=2))
    print(json.dumps(d,indent=2),flush=True)
    return d

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    CLIPS.mkdir(parents=True,exist_ok=True)
    try:
        import yt_dlp
    except ImportError:
        status("DEPENDENCY", "yt-dlp Python package missing");return 2
    chosen=None
    requested=os.getenv("BOURIKO_YOUTUBE_URL","").strip()
    try:
        with yt_dlp.YoutubeDL({"quiet":True,"no_warnings":True,"extract_flat":True,"skip_download":True}) as ydl:
            if requested:
                candidates=[{"url":requested,"title":"Explicit candidate","description":"","license":"","score":0}]
            else:
                searches=[
                    "ytsearch8:traffic light intersection stock footage royalty free no watermark",
                    "ytsearch8:car traffic light red green road creative commons free footage",
                ]
                seen={}
                for search in searches:
                    result=ydl.extract_info(search,download=False)
                    for e in result.get("entries",[]):
                        if not e or not e.get("id"):continue
                        key=e["id"]
                        if key not in seen:seen[key]={"title":e.get("title") or "","id":key,"url":f"https://www.youtube.com/watch?v={key}"}
                candidates=list(seen.values())
                if not candidates:raise RuntimeError("No search candidates")
                # Flat search doesn't reliably provide descriptions or license data:
                # query each candidate for explicit usage signals.
                enriched=[]
                for item in candidates:
                    try:
                        with yt_dlp.YoutubeDL({"quiet":True,"no_warnings":True,"skip_download":True,"noplaylist":True}) as details:
                            info=details.extract_info(item["url"],download=False)
                        item["description"]=str(info.get("description") or "")[:2500]
                        item["license"]=str(info.get("license") or "")
                        item["duration"]=info.get("duration")
                    except Exception as exc:
                        item["description"]=""
                        item["license"]=""
                        item["metadata_error"]=str(exc)[:250]
                    signal=(item["title"]+" "+item["description"]+" "+item["license"]).lower()
                    positive=["creative commons","cc by","copyright free","copyright-free","royalty free","royalty-free","free to use","free for commercial use","no copyright","public domain"]
                    negative=["all rights reserved","do not reupload","do not redistribute","not for commercial use","no permission to reuse"]
                    item["permission_signal"]=any(x in signal for x in positive)
                    item["restriction_signal"]=any(x in signal for x in negative)
                    item["branding_risk"]=any(x in signal for x in ["watermarked","watermark included","logo overlay","branded footage"])
                    # A statement 'no watermark' is positive rather than evidence of a watermark.
                    item["score"]=5*int(item["permission_signal"])-50*int(item["restriction_signal"])-10*int(item["branding_risk"])+sum(1 for s in ["traffic light","intersection","car","footage"] if s in signal)
                    if "no watermark" in signal or "without watermark" in signal:item["score"]+=3
                    enriched.append(item)
                candidates=sorted(enriched,key=lambda x:x["score"],reverse=True)
                (OUT/"candidates.json").write_text(json.dumps(candidates,indent=2))
                candidates=[x for x in candidates if x["permission_signal"] and not x["restriction_signal"] and not x["branding_risk"]]
                if not candidates:raise RuntimeError("No candidates with explicit reuse-positive metadata and no stated restrictions; cannot auto-select.")
        chosen=candidates[0]
        status("DISCOVERED",candidate=chosen)
        if not SOURCE.exists() or SOURCE.stat().st_size<100000:
            opts={"outtmpl":str(OUT/"download.%(ext)s"),"format":"bv*[height<=720]+ba/b[height<=720]/best","merge_output_format":"mp4",
                  "noplaylist":True,"quiet":True,"no_warnings":True,"retries":2,"fragment_retries":2}
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([chosen["url"]])
            files=sorted([p for p in OUT.glob("download.*") if p.suffix in {".mp4",".webm",".mkv"}])
            if not files:raise RuntimeError("No downloaded media")
            files[0].rename(SOURCE)
        probe=run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(SOURCE)])
        if probe.returncode:raise RuntimeError(probe.stderr[-1000:])
        duration=float(probe.stdout.strip())
        if duration<16:raise RuntimeError("Candidate too short for four samples")
        # Spread four clips across the input. These are EDITING DIAGNOSTICS, not event detections.
        offsets=[round(duration*x,2) for x in (.12,.35,.59,.83)]
        produced=[]
        for n,(label,start) in enumerate(zip(LABELS,offsets),1):
            dest=CLIPS/f"{n:02d}_{label}.mp4"
            cmd=[sys.executable,str(ROOT/"tools/windows/extract-video-clips.py"),
                 "--source",str(SOURCE),"--output",str(dest),"--start",str(start),"--duration","2"]
            result=run(cmd)
            if result.returncode:raise RuntimeError(f"{label}: {result.stderr[-1200:]}")
            produced.append(dict(label=label,file=str(dest.relative_to(ROOT)),source_second=start,
                                 visually_verified=False,rights_verified=False))
        # Only disposable raw source generated by this isolated test is removed, after all outputs pass.
        SOURCE.unlink()
        for leftover in OUT.glob("download.*"):
            if leftover.is_file() and leftover.suffix in {".mp4",".webm",".mkv",".part"}:
                leftover.unlink()
        status("REVIEW_CLIPS_READY",candidate=chosen,clips=produced,raw_source_deleted=True,
               warning="Provisional timeline samples only. No automatic event recognition, no publication, no scene acceptance.")
        return 0
    except Exception as exc:
        status("FAILED",str(exc),candidate=chosen,raw_source_preserved=SOURCE.exists())
        return 1

if __name__=="__main__":
    sys.exit(main())
