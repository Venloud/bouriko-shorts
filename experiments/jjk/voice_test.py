"""10-15 s ElevenLabs pronunciation test for the JJK names, run BEFORE the full read.

Voices one short line with the JJK story's voice + model + settings (same cache, same credit
guard), then transcribes it with ElevenLabs speech-to-text and checks every name came back.
A failed TTS request stops the run with "VOICE BLOCKED". A name the transcript misses is
flagged in output/voice_test/report.json for a human listen (STT spelling can differ).
Run after experiments/jjk/jjk_story.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
import elevenlabs_voice as el  # noqa: E402
from common import CONFIG  # noqa: E402

NAMES = ["Kogane", "shikigami", "Yuji", "Megumi", "Tsumiki", "Kenjaku", "Tengen"]
TEXT = ("Kogane is a shikigami. It hands the rules to Yuji Itadori, Megumi Fushiguro, and his sister "
        "Tsumiki. Behind it all stands Kenjaku. And at the center of his plan... Master Tengen.")


def transcribe(mp3: Path) -> str:
    import requests
    with mp3.open("rb") as f:
        r = requests.post("https://api.elevenlabs.io/v1/speech-to-text",
                          headers={"xi-api-key": el.key() or ""},
                          data={"model_id": "scribe_v1", "language_code": "en"},
                          files={"file": ("test.mp3", f, "audio/mpeg")}, timeout=120)
    if not r.ok:
        return f"(transcription failed: HTTP {r.status_code})"
    return r.json().get("text", "")


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    cfg = dict(CONFIG.get("elevenlabs", {}))
    cfg["voice_settings"] = {**cfg.get("voice_settings", {}), **(story.get("voice_settings") or {})}
    cfg.update(story.get("elevenlabs", {}))
    out = ROOT / "output/voice_test"
    try:
        report = el.synthesize_story([{"text": TEXT, "tts_text": "[intense] " + TEXT}], out,
                                     ROOT / "cache/tts", cfg, log=print)
    except el.SkipElevenLabs as e:
        raise SystemExit(f"VOICE BLOCKED: {e}")
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"VOICE BLOCKED: {type(e).__name__}: {str(e)[:300]}")
    words = report.pop("words")
    take = out / "elevenlabs_take.mp3"
    test_mp3 = out / "voice_test.mp3"
    take.replace(test_mp3)
    duration = words[-1]["end"] if words else 0
    text = transcribe(test_mp3)
    norm = re.sub(r"[^a-z ]", " ", text.lower())
    names = {n: (n.lower() in norm) for n in NAMES}
    result = {"text": TEXT, "model": report.get("model"), "voice_id": report.get("voice_id"),
              "voice_name": report.get("voice_name"), "duration_s": round(duration, 2),
              "credits_used": report.get("credits_used", 0), "cache_hit": report.get("cache_hit"),
              "transcript": text, "names_heard": names,
              "names_to_check_by_ear": [n for n, ok in names.items() if not ok],
              "word_timings": words}
    (out / "report.json").write_text(json.dumps(result, indent=2))
    print(f"VOICE TEST: {report.get('model')} \"{report.get('voice_name')}\" {duration:.1f}s, "
          f"credits {report.get('credits_used', 0)}; transcript: {text}")
    print("VOICE TEST names:", ", ".join(f"{n} {'ok' if ok else 'CHECK'}" for n, ok in names.items()))


if __name__ == "__main__":
    main()
