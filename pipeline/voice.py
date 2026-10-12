"""Bouriko narrator voice: ElevenLabs (own account) first, Kokoro as the fallback.

Writes output/audio/NN.wav per line, output/word_timings.json (caption words with real timings)
and output/voice_report.json (engine, model, credits used, fallback reason).

Captions and timings always use line["text"]. The optional line["tts_text"] is what ElevenLabs
speaks ([tags], "...", "—"); Kokoro never sees tags (it would read them aloud).
"""
import json
import os
import re

import numpy as np

from common import ROOT, CONFIG, log

AUDIO = ROOT / "output/audio"
TTS_CACHE = ROOT / "cache/tts"


def _kokoro_line(pipe, text, voice, speed, out):
    """One Kokoro line. Uses Kokoro's own token timestamps; proportional split only if missing."""
    import soundfile as sf
    chunks, tokens, offset = [], [], 0.0
    for result in pipe(text, voice=voice, speed=speed):
        audio = result.audio if hasattr(result, "audio") else result[2]
        if audio is None:
            continue
        audio = audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio)
        for t in getattr(result, "tokens", None) or []:
            if getattr(t, "start_ts", None) is not None and getattr(t, "end_ts", None) is not None:
                tokens.append((t.text, offset + t.start_ts, offset + t.end_ts))
        chunks.append(audio)
        offset += len(audio) / 24000
    if not chunks:
        raise RuntimeError("Kokoro returned no audio")
    audio = np.concatenate(chunks)
    sf.write(str(out), audio, 24000)
    total = len(audio) / 24000

    words = re.findall(r"\S+", text)
    spoken = [(t, s, e) for t, s, e in tokens if re.search(r"[A-Za-z0-9]", t)]
    if spoken:
        # walk caption words and Kokoro tokens together on their alphanumeric text
        norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        result, k = [], 0
        for w in words:
            target, got, start, end = norm(w), "", None, None
            while k < len(spoken) and len(got) < len(target):
                got += norm(spoken[k][0])
                start = spoken[k][1] if start is None else start
                end = spoken[k][2]
                k += 1
            if start is None:
                start = result[-1]["end"] if result else 0.0
                end = start + 0.15
            result.append({"word": w, "start": round(start, 3), "end": round(end, 3)})
        if k >= len(spoken) * 0.8:
            return result
    total_chars = max(1, sum(len(x) for x in words))
    t, result = 0.0, []
    for w in words:
        d = total * len(w) / total_chars
        result.append({"word": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return result


def kokoro(story, reason):
    import soundfile as sf
    from kokoro import KPipeline
    voice = os.getenv("BOURIKO_KOKORO_VOICE") or os.getenv("NIGHTFILES_VOICE") or CONFIG["voices"]["narrator"]
    speed = float(story.get("voice_speed") or CONFIG["voices"].get("speed", 0.98))
    lang = voice[0] if voice and voice[0] in "abefhijpz" else CONFIG["voices"].get("lang", "a")
    log(f"VOICE: Kokoro fallback ({reason}) | voice={voice} speed={speed}")
    pipe = KPipeline(lang_code=lang)
    words, offset = [], 0.0
    trim = story.get("trim_pauses")  # e.g. {"lead": 0.08, "tail": 0.14}: tighter, more energetic pacing
    for i, line in enumerate(story["lines"]):
        wav = AUDIO / f"{i:02}.wav"
        line_words = _kokoro_line(pipe, line["text"], voice, speed, wav)
        if trim and line_words:
            audio, sr = sf.read(str(wav), always_2d=False)
            a = max(0, int((line_words[0]["start"] - float(trim.get("lead", 0.08))) * sr))
            b = min(len(audio), int((line_words[-1]["end"] + float(trim.get("tail", 0.14))) * sr))
            sf.write(str(wav), audio[a:b], sr)
            shift = a / sr
            line_words = [{**w, "start": round(max(0, w["start"] - shift), 3), "end": round(max(0, w["end"] - shift), 3)}
                          for w in line_words]
        for w in line_words:
            words.append({**w, "line": i, "start": round(w["start"] + offset, 3),
                          "end": round(w["end"] + offset, 3)})
        frames, sr = sf.read(str(wav), always_2d=False)
        offset += len(frames) / sr
    return words, {"engine": "kokoro", "voice": voice, "speed": speed, "fallback_reason": reason,
                   "credits_used": 0}


def render_lines(story):
    import elevenlabs_voice as el
    AUDIO.mkdir(parents=True, exist_ok=True)
    for old in AUDIO.glob("*.wav"):
        old.unlink()
    cfg = dict(CONFIG.get("elevenlabs", {}))
    # A story can ask for its own delivery (JJK = more energy) without touching the tech default.
    cfg["voice_settings"] = {**cfg.get("voice_settings", {}), **(story.get("voice_settings") or {})}
    engine = os.getenv("BOURIKO_VOICE_ENGINE", CONFIG.get("voice_engine", "elevenlabs")).lower()
    report = None
    if engine == "elevenlabs":
        try:
            report = el.synthesize_story(story["lines"], AUDIO, TTS_CACHE, cfg, log=log)
            words = report.pop("words")
            log(f"VOICE: ElevenLabs {report['model']} voice={report['voice_id']} "
                f"credits_used={report.get('credits_used', 0)} cache_hit={report['cache_hit']}")
        except el.SkipElevenLabs as e:
            reason = str(e)
            if "credits too low" in reason:
                try:
                    from notify import notify_text
                    notify_text("Bouriko: ElevenLabs credits low", reason + " - used Kokoro instead.", warn=True)
                except Exception as exc:  # noqa: BLE001
                    log(f"ntfy alert failed: {type(exc).__name__}")
            report = None
            words, report = kokoro(story, "ElevenLabs skipped: " + reason)
        except Exception as e:  # noqa: BLE001  any API/alignment failure -> still ship a voice
            words, report = kokoro(story, f"ElevenLabs failed: {str(e)[:200]}")
    else:
        words, report = kokoro(story, f"voice_engine={engine}")

    manifest = [f"file '{(AUDIO / f'{i:02}.wav').resolve()}'" for i in range(len(story["lines"]))]
    (ROOT / "output/audio_concat.txt").write_text("\n".join(manifest) + "\n")
    (ROOT / "output/word_timings.json").write_text(json.dumps(words, indent=2))
    (ROOT / "output/voice_report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    story = json.loads((ROOT / "output/story.json").read_text())
    render_lines(story)
