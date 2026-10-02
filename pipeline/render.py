"""Offline-first Bouriko renderer: narrated card/storyboard video with captions and sketch visuals."""
import json,math,subprocess
from pathlib import Path
from common import ROOT,CONFIG,run
W,H=1080,1920
def svg(text,idx,out):
    safe=text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="#F4EFE4"/><g stroke="#1B1B1B" fill="none" stroke-width="9"><circle cx="540" cy="620" r="190"/><path d="M300 900 Q540 760 780 900"/><path d="M350 1150 L730 1150"/><circle cx="540" cy="400" r="70"/></g><text x="540" y="1380" text-anchor="middle" font-family="sans-serif" font-size="58" fill="#1B1B1B">{safe}</text><text x="540" y="1510" text-anchor="middle" font-family="sans-serif" font-size="42" fill="#2EA8FF">BOURIKO • {idx}</text></svg>'''
    out.write_text(svg); return out
def main():
    story=json.loads((ROOT/"output/story.json").read_text()); od=ROOT/"output/render"; od.mkdir(parents=True,exist_ok=True)
    lines=story["lines"]; per=max(2.0,61.5/len(lines)); clips=[]
    for i,line in enumerate(lines):
        s=svg(line["visual"],i+1,od/f"{i:02}.svg"); mp4=od/f"{i:02}.mp4"
        dur=per
        run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c=#F4EFE4:s={W}x{H}:r=30:d={dur:.3f}","-vf",f"drawtext=text='{line['text'].replace("'","\\'")}':fontcolor=#1B1B1B:fontsize=42:x=(w-text_w)/2:y=h-360:box=1:boxcolor=#F4EFE4@0.85:boxborderw=18","-c:v","libx264","-pix_fmt","yuv420p",str(mp4)])
        clips.append(mp4)
    lst=od/"concat.txt"; lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips))
    out=ROOT/"output/bouriko.mp4"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(out)])
    return out
if __name__=="__main__": print(main())
