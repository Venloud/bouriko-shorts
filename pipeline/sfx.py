"""Generate lightweight original sound effects for Bouriko."""
import json
import wave
from pathlib import Path
import numpy as np
from common import ROOT

RATE = 24000
SFX_DIR = ROOT / "output/sfx"

def write_wav(path, samples):
    samples = np.clip(samples, -1, 1)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(pcm.tobytes())

def tone(freq, dur, amp=0.35, decay=7.0, freq2=None):
    n = max(1, int(RATE * dur)); t = np.arange(n) / RATE
    f = np.linspace(freq, freq2 or freq, n)
    phase = 2 * np.pi * np.cumsum(f) / RATE
    return amp * np.sin(phase) * np.exp(-decay * t)

def layer(*parts):
    """Mix sounds of different lengths without numpy broadcasting errors."""
    size = max(len(x) for x in parts)
    out = np.zeros(size, dtype=np.float64)
    for part in parts:
        out[:len(part)] += part
    return out

def click():
    return layer(tone(1450, 0.075, 0.28, 45),
                 tone(3100, 0.035, 0.12, 70))

def beep():
    return layer(tone(880, 0.18, 0.18, 10),
                 tone(1320, 0.12, 0.10, 14))

def ping():
    return tone(900, 0.22, 0.16, 8, 1550)

def camera():
    n = int(RATE * 0.16); rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, n); env = np.exp(-28 * np.arange(n) / RATE)
    return layer(0.20 * noise * env, tone(1700, 0.08, 0.10, 35))

def whoosh():
    n = int(RATE * 0.32); rng = np.random.default_rng(11)
    noise = rng.normal(0, 1, n); t = np.arange(n) / RATE
    env = np.sin(np.pi * np.clip(t / 0.32, 0, 1)) ** 1.7
    return layer(0.10 * noise * env, tone(500, 0.32, 0.07, 3, 110))

def main():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    makers = {"whoosh":whoosh, "click":click, "beep":beep, "ping":ping, "camera":camera}
    for name, maker in makers.items():
        write_wav(SFX_DIR / f"{name}.wav", maker())

    story = json.loads((ROOT / "output/story.json").read_text())
    starts = []; t = 0.0
    for i, line in enumerate(story.get("lines", [])):
        wav = ROOT / "output/audio" / f"{i:02}.wav"
        if not wav.exists(): continue
        with wave.open(str(wav), "rb") as w: dur = w.getnframes() / w.getframerate()
        starts.append((i, t, line.get("text", ""))); t += dur

    events = []
    for i, start, text in starts:
        lower = text.lower(); effect = None; volume = 0.18
        if i == 0: effect, volume = "whoosh", 0.16
        elif "pavement" in lower or "rectangle" in lower: effect, volume = "click", 0.16
        elif "induction loop" in lower or "wire buried" in lower: effect, volume = "beep", 0.13
        elif "magnetic field" in lower or "detects" in lower: effect, volume = "ping", 0.16
        elif "camera" in lower: effect, volume = "camera", 0.14
        elif "bicycle" in lower: effect, volume = "beep", 0.10
        if effect:
            events.append({"time":round(start + 0.08,3),
                           "file":f"output/sfx/{effect}.wav","volume":volume,"type":effect})
    (ROOT / "output/sfx_events.json").write_text(json.dumps(events, indent=2))
    print(f"SFX generated: {len(makers)} assets, {len(events)} events")

if __name__ == "__main__":
    main()
