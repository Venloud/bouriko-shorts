"""Kokoro TTS for Bouriko."""
import json,re
from common import ROOT,CONFIG
def synthesize(text,voice,out):
    import soundfile as sf,numpy as np
    from kokoro import KPipeline
    pipe=KPipeline(lang_code=CONFIG.get("voices",{}).get("lang","a"))
    chunks=[]
    for _,_,audio in pipe(text,voice=voice,speed=CONFIG.get("voices",{}).get("speed",1.05)): chunks.append(audio)
    if not chunks: raise RuntimeError("Kokoro returned no audio")
    audio=np.concatenate(chunks); sf.write(str(out),audio,24000)
    words=re.findall(r"\\S+",text); total=len(audio)/24000; total_chars=max(1,sum(len(x) for x in words))
    t=0; result=[]
    for w in words:
        d=total*len(w)/total_chars; result.append({"word":w,"start":round(t,3),"end":round(t+d,3)}); t+=d
    return result
def render_lines(story):
    od=ROOT/"output/audio"; od.mkdir(parents=True,exist_ok=True); all_words=[]; offset=0
    for i,line in enumerate(story["lines"]):
        voice=CONFIG["voices"]["bouriko"] if line["speaker"]=="BOURIKO" else CONFIG["voices"]["rock_phone"]
        wav=od/f"{i:02}.wav"; words=synthesize(line["text"],voice,wav)
        import soundfile as sf
        frames,sr=sf.read(str(wav),always_2d=False)
        for w in words: w.update(line=i,start=round(w["start"]+offset,3),end=round(w["end"]+offset,3)); all_words.append(w)
        offset+=len(frames)/sr
    manifest=[]
    for i in range(len(story["lines"])): manifest.append("file '"+str((od/f"{i:02}.wav").resolve())+"'")
    (ROOT/"output/audio_concat.txt").write_text("\\n".join(manifest)+"\\n")
    (ROOT/"output/word_timings.json").write_text(json.dumps(all_words,indent=2))
if __name__=="__main__":
    story=json.loads((ROOT/"output/story.json").read_text()); render_lines(story)
