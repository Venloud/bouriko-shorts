"""Download curated free stock SFX for Bouriko.

No procedural/generated tones. Every effect is downloaded from a named source
and reused across builds. Source/license metadata is kept in SFX_SOURCES.md.
"""
import json
from pathlib import Path

import requests

from common import ROOT

SFX_DIR = ROOT / "output/sfx"

# Mixkit Free License assets. The files are downloaded at build time rather
# than generated locally, so the project uses real recorded sound effects.
SFX = {
    "whoosh": "https://assets.mixkit.co/active_storage/sfx/1490/1490-preview.mp3",
    "sweep": "https://assets.mixkit.co/active_storage/sfx/166/166-preview.mp3",
    "click": "https://assets.mixkit.co/active_storage/sfx/1133/1133-preview.mp3",
    "camera": "https://assets.mixkit.co/active_storage/sfx/1430/1430-preview.mp3",
    "interface": "https://assets.mixkit.co/sfx/preview/mixkit-software-interface-start-2574.mp3",
    "beep": "https://assets.mixkit.co/sfx/preview/mixkit-positive-interface-beep-221.mp3",
    "impact": "https://assets.mixkit.co/active_storage/sfx/2299/2299-preview.mp3",
    "glitch": "https://assets.mixkit.co/active_storage/sfx/2595/2595-preview.mp3",
}


def download_assets():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in SFX.items():
        path = SFX_DIR / f"{name}.mp3"
        if path.exists() and path.stat().st_size > 1000:
            continue
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        path.write_bytes(response.content)
        print(f"Downloaded {name}: {len(response.content):,} bytes")


def main():
    download_assets()

    story = json.loads((ROOT / "output/story.json").read_text())
    starts = []
    t = 0.0
    for i, line in enumerate(story.get("lines", [])):
        wav = ROOT / "output/audio" / f"{i:02}.wav"
        if not wav.exists():
            continue
        import wave
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

        if effect:
            events.append({
                "time": round(start + 0.08, 3),
                "file": f"output/sfx/{effect}.mp3",
                "volume": volume,
                "type": effect,
            })

    (ROOT / "output/sfx_events.json").write_text(json.dumps(events, indent=2))
    print(f"SFX library ready: {len(SFX)} downloaded assets, {len(events)} events")


if __name__ == "__main__":
    main()
