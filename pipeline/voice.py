"""Single deep narrator TTS for the Bouriko explainer format."""
import json, os, re
import numpy as np
from common import ROOT, CONFIG

def synthesize(text, voice, out):
    import soundfile as sf
    from kokoro import KPipeline
    lang_code = voice[0] if voice and voice[0] in {"a", "b", "e", "f", "h", "i", "j", "p", "z"} else CONFIG.get("voices", {}).get("lang", "a")
    pipe = KPipeline(lang_code=lang_code)
    chunks = []
    for _, _, audio in pipe(
        text,
        voice=voice,
        speed=CONFIG.get("voices", {}).get("speed", 0.94),
    ):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("Kokoro returned no audio")
    audio = np.concatenate(chunks)
    sf.write(str(out), audio, 24000)

    words = re.findall(r"\S+", text)
    total = len(audio) / 24000
    total_chars = max(1, sum(len(x) for x in words))
    t = 0
    result = []
    for w in words:
        d = total * len(w) / total_chars
        result.append({"word": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return result

def render_lines(story):
    od = ROOT / "output/audio"
    od.mkdir(parents=True, exist_ok=True)
    all_words = []
    offset = 0

    voice = os.getenv("NIGHTFILES_VOICE") or CONFIG["voices"]["narrator"]
    print(f"Narrator voice: {voice} | speed={CONFIG['voices'].get('speed', 0.94)}")

    for i, line in enumerate(story["lines"]):
        wav = od / f"{i:02}.wav"
        words = synthesize(line["text"], voice, wav)
        import soundfile as sf
        frames, sr = sf.read(str(wav), always_2d=False)
        for w in words:
            w.update(
                line=i,
                start=round(w["start"] + offset, 3),
                end=round(w["end"] + offset, 3),
            )
            all_words.append(w)
        offset += len(frames) / sr

    manifest = [f"file '{(od / f'{i:02}.wav').resolve()}'" for i in range(len(story["lines"]))]
    (ROOT / "output/audio_concat.txt").write_text("\n".join(manifest) + "\n")
    (ROOT / "output/word_timings.json").write_text(json.dumps(all_words, indent=2))

if __name__ == "__main__":
    story = json.loads((ROOT / "output/story.json").read_text())
    render_lines(story)
