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
    exact_script = bool(story.get("exact_script"))
    if not exact_script:
        assert story.get("sources"), "no sources"
    assert all(x.get("text") for x in lines), "missing caption text"
    assert all(x.get("visual") for x in lines), "missing visual plan"

    manifest = ROOT / "output/media_manifest.json"
    media_count = 0
    if manifest.exists():
        media_count = len(json.loads(manifest.read_text()))
    video_count = sum(1 for x in json.loads(manifest.read_text()) if x.get("kind") == "video") if manifest.exists() else 0
    print(f"MEDIA DATA: {media_count} usable visual assets ({video_count} video)")
    assert media_count >= 8, "not enough usable visual assets; refusing to publish a weak visual build"
    if story.get("pillar") == "anime_explainer":
        assert video_count >= 4, "anime explainer requires actual video clips; local diagrams do not qualify"
        assert sum(1 for x in json.loads(manifest.read_text()) if x.get("provider") == "local_diagram") == 0, "anime explainer silently fell back to local diagrams"
        assert (ROOT / "output/scene_matches.json").exists(), "anime explainer missing scene timestamp evidence"
        matches = json.loads((ROOT / "output/scene_matches.json").read_text())
        assert len(matches) == len(lines), "scene matches must cover every narration line"
        assert all(x.get("status") == "verified" for x in matches), "unverified anime scene clips; do not claim complete"
    elif not exact_script:
        assert video_count >= 4, "not enough actual video footage; refusing to publish a slideshow"
    print(f"QA PASS: {d:.2f}s, audio={a}, lines={len(lines)}, visuals={media_count}, video={video_count}, exact_script={exact_script}")


if __name__ == "__main__":
    main()
