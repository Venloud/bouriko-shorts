"""Prepare narration, media, and SFX for the Remotion render."""
import json
import shutil
import subprocess
import wave
from pathlib import Path

from common import ROOT

REMOTION = ROOT / "remotion"
PUBLIC = REMOTION / "public"
GENERATED = PUBLIC / "generated"


def dur(path):
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    GENERATED.mkdir(parents=True, exist_ok=True)
    if story.get("pillar") == "anime_explainer":
        kinds = {"animated_map", "animated_counter", "animated_timer", "energy_diagram", "hero_motion", "anime_reference", "blackboard"}
        if any(line.get("anime_visual_type") not in kinds for line in story.get("lines", [])):
            raise RuntimeError("Missing approved JJK motion graphic visual plan")

    audio = ROOT / "output/audio"
    cursor = 0.0
    prepared = []
    concat = []

    for i, raw in enumerate(story.get("lines", [])):
        wav = audio / f"{i:02}.wav"
        if not wav.exists():
            raise RuntimeError(f"Missing narration audio: {wav}")
        d = dur(wav)
        line = dict(raw)
        line["start"] = round(cursor, 4)
        line["duration"] = round(d, 4)
        prepared.append(line)
        concat.append(f"file '{wav.as_posix()}'")
        cursor += d

    (ROOT / "output/audio_concat.txt").write_text("\n".join(concat) + "\n")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(ROOT / "output/audio_concat.txt"),
            "-ar",
            "24000",
            "-ac",
            "1",
            str(GENERATED / "narration.wav"),
        ],
        check=True,
    )

    for line in prepared:
        asset = line.get("media_asset")
        if not asset:
            continue
        src = ROOT / asset
        if not src.exists():
            continue
        dst = GENERATED / "media" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        line["media_asset"] = str(dst.relative_to(PUBLIC))
        line["media_kind"] = line.get("media_kind") or (
            "video"
            if src.suffix.lower() in {".mp4", ".webm", ".mov", ".ogv"}
            else "image"
        )

    events = []
    event_path = ROOT / "output/sfx_events.json"
    if event_path.exists():
        for event in json.loads(event_path.read_text()):
            src = ROOT / event["file"]
            if not src.exists():
                continue
            dst = GENERATED / "sfx" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            events.append({**event, "file": str(dst.relative_to(PUBLIC))})

    (REMOTION / "props.json").write_text(
        json.dumps(
            {
                "lines": prepared,
                "durationSeconds": round(cursor, 4),
                "sfxEvents": events,
            },
            indent=2,
        )
    )
    print(f"Remotion prepared: {len(prepared)} scenes, {cursor:.2f}s")


if __name__ == "__main__":
    main()
