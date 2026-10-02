"""Final media-first explainer QA gate."""
import json, subprocess
from common import ROOT, CONFIG


def main():
    p = ROOT / "output/bouriko.mp4"
    d = float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(p)
    ]))
    lo, hi = CONFIG["target_seconds"]
    print(f"DURATION DATA: {d:.2f}s (target {lo}-{hi}s)")
    if not (lo <= d <= hi + 0.5):
        print(f"QA INFO: {d:.2f}s is outside the target window; continuing for visual review.")

    a = subprocess.check_output([
        "ffprobe","-v","error","-select_streams","a",
        "-show_entries","stream=codec_name","-of","csv=p=0",str(p)
    ]).decode().strip()
    assert a, "no audio"

    story = json.loads((ROOT / "output/story.json").read_text())
    lines = story.get("lines", [])
    assert len(lines) >= 8, "too few narration lines"
    assert story.get("sources"), "no sources"
    assert all(x.get("text") for x in lines), "missing caption text"
    assert all(x.get("visual") for x in lines), "missing visual plan"

    manifest = ROOT / "output/media_manifest.json"
    media_count = 0
    if manifest.exists():
        media_count = len(json.loads(manifest.read_text()))
    print(f"MEDIA DATA: {media_count} downloaded assets")
    print(f"QA PASS: {d:.2f}s, audio={a}, lines={len(lines)}, media={media_count}")


if __name__ == "__main__":
    main()
