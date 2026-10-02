"""Download real SFX from the Night Files library first, then Mixkit.

No procedural/generated tones. Night Files is the primary reusable library;
Mixkit is the secondary fallback/source. Files are fetched at build time.
"""
import json
import wave
from pathlib import Path

import requests

from common import ROOT

SFX_DIR = ROOT / "output/sfx"
NIGHT_FILES_BASE = "https://raw.githubusercontent.com/Venloud/horror-shorts/main"

NIGHT_FILES_SFX = {
    "whoosh": "assets/sfx/whoosh.mp3",
    "sweep": "assets/sfx/whoosh.mp3",
    "click": "assets/sfx/ui_click.mp3",
    "camera": "assets/sfx/camera_shutter.mp3",
    "interface": "assets/sfx/ui_click.mp3",
    "beep": "assets/sfx/phone_notification.mp3",
    "impact": "assets/stings/default_impact.mp3",
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
    for name in NIGHT_FILES_SFX:
        path = SFX_DIR / f"{name}.mp3"
        if path.exists() and path.stat().st_size > 1000:
            sources[name] = "Night Files (cached)"
            continue
        night_url = f"{NIGHT_FILES_BASE}/{NIGHT_FILES_SFX[name]}"
        if fetch(night_url, path):
            sources[name] = f"Night Files: {NIGHT_FILES_SFX[name]}"
            print(f"Downloaded {name} from Night Files")
            continue
        if fetch(MIXKIT_SFX[name], path):
            sources[name] = f"Mixkit: {MIXKIT_SFX[name]}"
            print(f"Downloaded {name} from Mixkit fallback")
        else:
            print(f"No usable source for {name}")
    return sources

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

    events = []
    for i, start, text in starts:
        lower = text.lower()
        effect = None
        volume = 0.14
        if i == 0:
            effect, volume = "whoosh", 0.13
        elif "pavement" in lower or "rectangle" in lower:
            effect, volume = "click", 0.13
        elif "induction loop" in lower or "wire buried" in lower:
            effect, volume = "beep", 0.10
        elif "magnetic field" in lower or "detects" in lower:
            effect, volume = "interface", 0.11
        elif "camera" in lower or "radar" in lower:
            effect, volume = "camera", 0.10
        elif "bicycle" in lower:
            effect, volume = "click", 0.09
        elif "green light" in lower:
            effect, volume = "sweep", 0.10
        if effect and (SFX_DIR / f"{effect}.mp3").exists():
            events.append({
                "time": round(start + 0.08, 3),
                "file": f"output/sfx/{effect}.mp3",
                "volume": volume,
                "type": effect,
                "source": sources.get(effect, "unknown"),
            })

    (ROOT / "output/sfx_events.json").write_text(json.dumps(events, indent=2))
    (ROOT / "output/sfx_sources.json").write_text(json.dumps(sources, indent=2))
    print(f"SFX library ready: {len(sources)} usable assets, {len(events)} events")

if __name__ == "__main__":
    main()
