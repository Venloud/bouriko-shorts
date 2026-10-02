"""Final traffic-light QA gate."""
import json,subprocess,wave
from pathlib import Path
from common import ROOT,CONFIG
def main():
    p=ROOT/"output/bouriko.mp4"
    d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)]))
    lo,hi=CONFIG["target_seconds"]
    assert lo<=d<=hi+0.5,f"duration {d:.2f}s outside {lo}-{hi}s"
    a=subprocess.check_output(["ffprobe","-v","error","-select_streams","a","-show_entries","stream=codec_name","-of","csv=p=0",str(p)]).decode().strip()
    assert a,"no audio"
    story=json.loads((ROOT/"output/story.json").read_text())
    assert len(story.get("lines",[]))>=8,"too few lines"
    assert story.get("sources"),"no sources"
    print(f"QA PASS: {d:.2f}s, audio={a}")
if __name__=="__main__": main()
