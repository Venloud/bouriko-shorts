"""Use the owner-approved narration mp3 AS-IS (0 credits) and force-align it to the V4 script.

- Audio: assets/anime/jujutsu_kaisen/narration/young_jamal_v4.mp3 (never regenerated).
- Alignment: faster-whisper word timestamps (local, free), matched to the exact script words
  with difflib; script words Whisper heard differently get interpolated times. [bracket] tags
  are not spoken and are never part of the timed words.
- The alignment is saved to experiments/jjk/v4_alignment.json keyed by the mp3's sha256, so CI
  reuses it without installing Whisper. Re-align with --realign.
Writes output/audio/NN.wav (one per story line, cut at the middle of the silence between
lines), output/word_timings.json and output/voice_report.json.
"""
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "assets/anime/jujutsu_kaisen/narration/young_jamal_v4.mp3"
CACHE = ROOT / "experiments/jjk/v4_alignment.json"
TAG = re.compile(r"\[[^\]]*\]")


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def whisper_words(model_name="small.en"):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(AUDIO), word_timestamps=True, language="en", beam_size=5,
                                   vad_filter=False, condition_on_previous_text=True)
    out = []
    for seg in segments:
        for w in seg.words or []:
            out.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return out


def align(script_words, heard):
    a = [norm(w) for w in script_words]
    b = [norm(w["word"]) for w in heard]
    times = [None] * len(script_words)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    matched = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
                matched += 1
        elif tag == "replace" and j2 > j1:
            s0, e0 = heard[j1]["start"], heard[j2 - 1]["end"]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
    # interpolate anything still missing between known neighbours
    for i, t in enumerate(times):
        if t is None:
            prev = next((times[k] for k in range(i - 1, -1, -1) if times[k]), (0.0, 0.0))
            nxt = next((times[k] for k in range(i + 1, len(times)) if times[k]), (prev[1] + 0.3, prev[1] + 0.6))
            times[i] = (prev[1], max(prev[1] + 0.05, min(nxt[0], prev[1] + 0.3)))
    return times, matched


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    lines = story["lines"]
    script_words, owner = [], []
    for li, line in enumerate(lines):
        for w in line["text"].split():
            script_words.append(w)
            owner.append(li)
    digest = sha(AUDIO)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if cache.get("audio_sha256") == digest and cache.get("script") == script_words and "--realign" not in sys.argv:
        times = [tuple(t) for t in cache["times"]]
        matched, heard_n = cache["matched"], cache["heard_words"]
        print(f"ALIGN: cached alignment for {AUDIO.name} ({matched}/{len(script_words)} words matched exactly)")
    else:
        heard = whisper_words()
        times, matched = align(script_words, heard)
        heard_n = len(heard)
        CACHE.write_text(json.dumps({"audio_sha256": digest, "audio": str(AUDIO.relative_to(ROOT)),
                                     "aligner": "faster-whisper small.en + difflib", "script": script_words,
                                     "heard_words": heard_n, "matched": matched,
                                     "transcript": " ".join(w["word"] for w in heard),
                                     "times": [[round(s, 3), round(e, 3)] for s, e in times]}, indent=1))
        print(f"ALIGN: whisper heard {heard_n} words; {matched}/{len(script_words)} script words matched exactly")

    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "default=nw=1:nk=1", str(AUDIO)]).decode().strip())
    first = {}
    last = {}
    for i, li in enumerate(owner):
        first.setdefault(li, times[i][0])
        last[li] = times[i][1]
    cuts = [0.0] + [round((last[li - 1] + first[li]) / 2, 3) for li in range(1, len(lines))] + [total]
    out = ROOT / "output/audio"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.wav"):
        old.unlink()
    for li in range(len(lines)):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(AUDIO), "-ss", f"{cuts[li]:.3f}",
                        "-to", f"{cuts[li + 1]:.3f}", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le",
                        str(out / f"{li:02}.wav")], check=True)
    words = [{"word": w, "start": round(times[i][0], 3), "end": round(times[i][1], 3), "line": owner[i]}
             for i, w in enumerate(script_words)]
    (ROOT / "output/word_timings.json").write_text(json.dumps(words, indent=1))
    (ROOT / "output/audio_concat.txt").write_text(
        "".join(f"file '{(out / f'{i:02}.wav').resolve()}'\n" for i in range(len(lines))))
    report = {"engine": "supplied_audio", "file": str(AUDIO.relative_to(ROOT)), "sha256": digest,
              "voice": "ElevenLabs Young Jamal (PVC), eleven_v4, speed 1.00, stability 0.37, similarity 0.67",
              "duration_s": round(total, 3), "credits_used": 0, "regenerated": False,
              "alignment": {"aligner": "faster-whisper small.en + difflib", "script_words": len(script_words),
                            "matched_exactly": matched, "heard_words": heard_n}}
    (ROOT / "output/voice_report.json").write_text(json.dumps(report, indent=2))
    print(f"AUDIO: {AUDIO.name} used as-is, {total:.2f}s, {len(lines)} lines, 0 credits")


if __name__ == "__main__":
    main()
