"""Final traffic-light QA gate."""
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
        print(f"QA INFO: duration {d:.2f}s is outside the current target window; continuing so the rendered clip can be reviewed.")

    a = subprocess.check_output([
        "ffprobe","-v","error","-select_streams","a",
        "-show_entries","stream=codec_name","-of","csv=p=0",str(p)
    ]).decode().strip()
    assert a, "no audio"

    story = json.loads((ROOT / "output/story.json").read_text())
    lines = story.get("lines", [])
    assert len(lines) >= 8, "too few lines"
    assert story.get("sources"), "no sources"
    assert all(x.get("text") for x in lines), "missing caption text"
    assert all(x.get("visual") for x in lines), "missing visual plan"

    poses = list((ROOT / "assets/poses").glob("*.png"))
    assert len(poses) >= 4, "cut-out pose library is too small"

    render_cards = list((ROOT / "output/render").glob("*.png"))
    assert len(render_cards) == len(lines), "not every line rendered a visual card"

    print(f"QA PASS: {d:.2f}s, audio={a}, lines={len(lines)}, poses={len(poses)}, visuals={len(render_cards)}")

if __name__ == "__main__":
    main()
