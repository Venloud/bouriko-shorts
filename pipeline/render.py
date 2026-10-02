"""Bouriko renderer: TTS-backed vertical video with sketch cards and caption overlays."""
import json, subprocess, wave
from pathlib import Path
from common import ROOT, run
W,H,FPS=1080,1920,30
def main():
    story=json.loads((ROOT/"output/story.json").read_text())
    audio_dir=ROOT/"output/audio"; audio_dir.mkdir(parents=True,exist_ok=True)
    # Audio is generated separately so the renderer can be tested with or without Kokoro.
    segments=[]
    for i,line in enumerate(story["lines"]):
        wav=audio_dir/f"{i:02}.wav"
        if not wav.exists(): raise RuntimeError(f"Missing voice audio: {wav}")
        with wave.open(str(wav),"rb") as f: dur=f.getnframes()/f.getframerate()
        segments.append((line,dur))
    concat=ROOT/"output/audio_all.wav"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(ROOT/"output/audio_concat.txt"),"-ar","24000","-ac","1",str(concat)])
    clips=[]; od=ROOT/"output/render";od.mkdir(parents=True,exist_ok=True)
    for i,(line,dur) in enumerate(segments):
        text=line["visual"].replace("\\"," ").replace("'","\\'")
        caption=line["text"].replace("\\"," ").replace(":","\\:").replace("'","\\'")
        vf=(f"drawtext=text='{text}':fontcolor=#1B1B1B:fontsize=52:x=(w-text_w)/2:y=560:"
            f"box=1:boxcolor=#F4EFE4@0.88:boxborderw=22,"
            f"drawtext=text='{caption}':fontcolor=#1B1B1B:fontsize=42:x=(w-text_w)/2:y=h-400:"
            f"box=1:boxcolor=#F4EFE4@0.90:boxborderw=18")
        out=od/f"{i:02}.mp4"
        run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"color=c=#F4EFE4:s={W}x{H}:r={FPS}:d={dur:.3f}","-vf",vf,"-c:v","libx264","-pix_fmt","yuv420p",str(out)])
        clips.append(out)
    lst=od/"concat.txt";lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips))
    silent=ROOT/"output/silent.mp4"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)])
    final=ROOT/"output/bouriko.mp4"
    run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(concat),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest",str(final)])
    return final
if __name__=="__main__": main()
