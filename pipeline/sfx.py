"""Download real SFX from the Night Files library first, then Mixkit.

No procedural/generated tones. Night Files is the primary reusable library;
Mixkit is the secondary fallback/source. Files are fetched at build time.
"""
import json
import wave
from pathlib import Path

import requests

from common import ROOT, CONFIG

SFX_DIR = ROOT / "output/sfx"
NIGHT_FILES_BASE = "https://raw.githubusercontent.com/Venloud/horror-shorts/main"

NIGHT_FILES_SFX = {
    "whoosh": "assets/sfx/whoosh.mp3",
    "sweep": "assets/sfx/whoosh.mp3",
    "click": "assets/sfx/ui_click.mp3",
    "camera": "assets/sfx/camera_shutter.mp3",
    "interface": "assets/sfx/ui_click.mp3",
    "beep": "assets/sfx/phone_notification.mp3",
    "glitch": "assets/sfx/radio_static.mp3",
}

MIXKIT_SFX = {
    "whoosh": "https://assets.mixkit.co/active_storage/sfx/1490/1490-preview.mp3",
    "sweep": "https://assets.mixkit.co/active_storage/sfx/166/166-preview.mp3",
    "click": "https://assets.mixkit.co/active_storage/sfx/1133/1133-preview.mp3",
    "camera": "https://assets.mixkit.co/active_storage/sfx/1430/1430-preview.mp3",
    "interface": "https://assets.mixkit.co/sfx/preview/mixkit-software-interface-start-2574.mp3",
    "beep": "https://assets.mixkit.co/sfx/preview/mixkit-positive-interface-beep-221.mp3",
    "impact": "https://assets.mixkit.co/active_storage/sfx/2299/2299-preview.mp3",
    "glitch": "https://assets.mixkit.co/active_storage/sfx/2595/2595-preview.mp3",
}

def fetch(url: str, path: Path) -> bool:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if len(response.content) <= 1000:
            raise RuntimeError("downloaded file is unexpectedly small")
        path.write_bytes(response.content)
        return True
    except Exception as exc:
        print(f"SFX source failed: {url} ({exc})")
        return False

def download_assets():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    sources = {}
    import os
    local = os.getenv("BOURIKO_SFX_DIR")  # optional local copy of the Night Files library
    for name in MIXKIT_SFX:
        if local and name in NIGHT_FILES_SFX:
            src = Path(local) / Path(NIGHT_FILES_SFX[name]).name
            if src.exists():
                (SFX_DIR / f"{name}.mp3").write_bytes(src.read_bytes())
                sources[name] = f"Night Files (local copy): {NIGHT_FILES_SFX[name]}"
                continue
        path = SFX_DIR / f"{name}.mp3"
        if path.exists() and path.stat().st_size > 1000:
            sources[name] = "Night Files (cached)"
            continue
        night_url = f"{NIGHT_FILES_BASE}/{NIGHT_FILES_SFX[name]}" if name in NIGHT_FILES_SFX else None
        if night_url and fetch(night_url, path):
            sources[name] = f"Night Files: {NIGHT_FILES_SFX[name]}"
            print(f"Downloaded {name} from Night Files")
            continue
        if fetch(MIXKIT_SFX[name], path):
            sources[name] = f"Mixkit: {MIXKIT_SFX[name]}"
            print(f"Downloaded {name} from Mixkit fallback")
        else:
            print(f"No usable source for {name}")
    return sources


def analyze_sfx(starts, sources):
    """Use Gemini to choose sparse, semantic SFX instead of keyword spam."""
    import os
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    model = os.getenv("GEMINI_ANALYST_MODEL", "gemini-3.8-flash")
    compact = [{"line": i, "start": round(t, 3), "text": text} for i, t, text in starts]
    prompt = """You are the sound designer for a modern vertical tech explainer.
Choose only a few SFX moments that make the explanation feel alive. Do NOT put an effect on every sentence.
Available effects: whoosh, sweep, click, camera, interface, beep, impact, glitch.
Rules:
- 3 to 7 total events for a 60-second short.
- whoosh/sweep = a meaningful reveal or visual transition.
- click/beep/interface = a machine, sensor, detection, or UI moment.
- camera = camera/radar reveal.
- impact = a real punchline or major reveal only.
- glitch = a deliberate tech/error moment only.
- Prefer silence when an effect would distract.
Return JSON only: {"events":[{"line":0,"offset":0.1,"effect":"whoosh","volume":0.10,"reason":"..."}]}
NARRATION:
""" + json.dumps(compact)
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key,
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"temperature":0.2,"responseMimeType":"application/json"}},
            timeout=60,
        )
        if not r.ok:
            print(f"SFX analyst failed: {r.status_code}")
            return None
        raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw)
        valid = []
        starts_by_line = {i:t for i,t,_ in starts}
        for e in data.get("events", []):
            try:
                line = int(e["line"])
                effect = str(e["effect"])
                if effect not in sources or line not in starts_by_line:
                    continue
                valid.append({
                    "time": round(starts_by_line[line] + max(0, min(1.2, float(e.get("offset", .1)))), 3),
                    "file": f"output/sfx/{effect}.mp3",
                    "volume": max(.05, min(.16, float(e.get("volume", .1)))),
                    "type": effect,
                    "reason": str(e.get("reason","")),
                    "source": sources.get(effect, "unknown"),
                })
            except (TypeError, ValueError, KeyError):
                continue
        return valid[:7]
    except Exception as exc:
        print(f"SFX analyst exception: {exc}")
        return None

def silence_gaps(words, total, min_gap=0.14):
    """Silences between spoken words: (start, end). SFX may only start inside one."""
    gaps, prev_end = [], 0.0
    for w in sorted(words, key=lambda x: x["start"]):
        if w["start"] - prev_end >= min_gap:
            gaps.append((prev_end, w["start"]))
        prev_end = max(prev_end, w["end"])
    if total - prev_end >= min_gap:
        gaps.append((prev_end, total))
    return gaps


def snap(t, gaps, window=0.9):
    """Nearest silence to a wanted time; None if there is none close enough."""
    best = None
    for a, b in gaps:
        d = 0 if a <= t <= b else min(abs(t - a), abs(t - b))
        if d <= window and (best is None or d < best[0]):
            best = (d, a, b)
    return best and (best[1], best[2])


def place(candidates, words, total, sources, max_events=8, spacing=2.5):
    """Put each wanted effect inside a silence, trimmed so it ends before the next word."""
    gaps = silence_gaps(words, total)
    events, last = [], -99.0
    for t, effect, reason in sorted(candidates):
        if effect not in sources or len(events) >= max_events:
            continue
        g = snap(t, gaps)
        if not g:
            continue
        a, b = g
        onset = max(a + 0.02, min(t, b - 0.15))
        max_len = round(b - onset - 0.03, 3)
        if max_len < 0.12 or onset - last < spacing:
            continue
        events.append({"time": round(onset, 3), "max_len": max_len, "file": f"output/sfx/{effect}.mp3",
                       "type": effect, "reason": reason, "source": sources.get(effect, "unknown")})
        last = onset
    return events


def main():
    sources = download_assets()
    story = json.loads((ROOT / "output/story.json").read_text())
    starts = []
    t = 0.0
    for i, line in enumerate(story.get("lines", [])):
        wav = ROOT / "output/audio" / f"{i:02}.wav"
        if not wav.exists():
            continue
        with wave.open(str(wav), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        starts.append((i, t, line.get("text", "")))
        t += dur
    total = t
    words = json.loads((ROOT / "output/word_timings.json").read_text())
    by_line = {}
    for w in words:
        by_line.setdefault(w.get("line", 0), []).append(w)
    starts_by_line = {i: s for i, s, _ in starts}

    # 1) effects the visual plan asked for, on the beat they belong to
    candidates = []
    for i, line in enumerate(story.get("lines", [])):
        for k, b in enumerate(line.get("beats", [])):
            if not b.get("sfx"):
                continue
            lw = by_line.get(i, [])
            if k == 0 or not lw:
                bt = starts_by_line.get(i, 0.0)
            else:
                bt = lw[max(0, min(len(lw) - 1, int(b.get("word", 0))))]["start"]
            candidates.append((bt, b["sfx"], "visual plan"))
    # 2) otherwise the sparse Gemini sound designer, then keyword rules
    if not candidates:
        analysed = analyze_sfx(starts, sources) or []
        candidates = [(e["time"], e["type"], e.get("reason", "analyst")) for e in analysed]
    if not candidates:
        for i, start, text in starts:
            lower = text.lower()
            effect = None
            if i == 0:
                effect = "whoosh"
            elif "camera" in lower or "radar" in lower:
                effect = "camera"
            elif "detect" in lower or "sensor" in lower:
                effect = "beep"
            if effect:
                candidates.append((start, effect, "keyword rule"))

    cap = int(CONFIG.get("audio", {}).get("max_sfx", 8))
    events = place(candidates, words, total, sources, max_events=cap)
    (ROOT / "output/sfx_events.json").write_text(json.dumps(events, indent=2))
    (ROOT / "output/sfx_sources.json").write_text(json.dumps(sources, indent=2))
    print(f"SFX: {len(events)} events (max {cap}), all placed in silences; {len(candidates)} candidates")

if __name__ == "__main__":
    main()
