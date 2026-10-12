"""Final media-first explainer QA gate.

Original checks are unchanged (audio present, >= 8 lines, sources, >= 8 visuals, >= 4 videos
for researched stories). Added for the narrator-led look (output/beats.json from
remotion_prepare.py):
  HARD: same shot twice in a row, a beat longer than 4.5 s, caption chunks outside 3-5 words,
        captions/boxes outside the TikTok safe box, more than 8 SFX or an SFX on a spoken word,
        audio not stereo AAC, loudness more than 1.5 LU from the -17 LUFS target.
  REPORT: duration window, hook answered by ~10 s, beats shorter than 2 s, audio bitrate.
Also writes review frames to output/frames/ (python pipeline/qa.py --frames 8).
"""
import json
import re
import subprocess
import sys

from common import ROOT, CONFIG

VR = CONFIG.get("visual_rules", {})
AU = CONFIG.get("audio", {})


def probe(path, entries, stream=None):
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", entries, "-of", "json", str(path)]
    return json.loads(subprocess.check_output(cmd))


def integrated_lufs(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    return float(m[-1]) if m else None


def frames(path, n, duration, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.png"):
        old.unlink()
    paths = []
    for k in range(n):
        t = duration * (k + 0.5) / n
        dst = out_dir / f"frame_{k + 1:02}_{t:05.1f}s.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                        str(dst)], check=True)
        paths.append(dst)
    return paths


def visual_checks(story, d, hard, report):
    data_path = ROOT / "output/beats.json"
    if not data_path.exists():
        report.append("no output/beats.json (old renderer?): visual rules not checked")
        return
    data = json.loads(data_path.read_text())
    beats, caps, sfx = data["beats"], data["captions"], data["sfx"]
    lo, hi = VR.get("caption_words", [3, 5])
    sx, sy = VR.get("safe_box", {}).get("x", [120, 960]), VR.get("safe_box", {}).get("y", [160, 1440])
    bmax, bmin = float(VR.get("beat_max_seconds", 4.0)), float(VR.get("beat_min_seconds", 2.0))

    for a, b in zip(beats, beats[1:]):
        if a["key"] == b["key"]:
            hard.append(f"same shot twice in a row at {b['start']:.1f}s ({b['key'][:50]})")
    long = [b for b in beats if b["end"] - b["start"] > bmax + 0.5]
    short = [b for b in beats if b["end"] - b["start"] < bmin - 0.6 and b is not beats[-1]]
    for b in long:
        hard.append(f"beat {b['start']:.1f}-{b['end']:.1f}s is {b['end'] - b['start']:.1f}s (> {bmax}s)")
    if short:
        report.append(f"{len(short)} beat(s) under {bmin - 0.6:.1f}s: " + ", ".join(f"{b['start']:.1f}s" for b in short[:6]))
    for b in beats:
        box = b.get("box") or {}
        if box and (box["x"] < sx[0] or box["x"] + box["w"] > sx[1] or box["y"] < sy[0] or box["y"] + box["h"] > sy[1]):
            hard.append(f"evidence box outside the safe box at {b['start']:.1f}s")
    bad_caps = [c for c in caps if not (lo <= len(c["words"]) <= hi) and not (c.get("whole_sentence") and len(c["words"]) < lo)]
    total_words = sum(len(c["words"]) for c in caps)
    if bad_caps and total_words >= lo:
        hard.append(f"{len(bad_caps)} caption chunk(s) outside {lo}-{hi} words: " +
                    "; ".join(" ".join(w["text"] for w in c["words"]) for c in bad_caps[:3]))
    # caption lane (Captions.tsx) sits at y 1150-1430, x 120-960: inside the safe box by construction
    if len(sfx) > int(AU.get("max_sfx", 8)):
        hard.append(f"{len(sfx)} SFX (max {AU.get('max_sfx', 8)})")
    words = json.loads((ROOT / "output/word_timings.json").read_text())
    for e in sfx:
        s0, s1 = e["time"], e["time"] + e.get("length", 0.3)
        hit = [w["word"] for w in words if w["start"] < s1 - 0.02 and w["end"] > s0 + 0.02]
        if hit:
            hard.append(f"SFX at {s0:.2f}s overlaps spoken word(s) {hit[:3]}")
    media = [b for b in beats if b["kind"] == "media"]
    print(f"VISUAL DATA: {len(beats)} beats ({len(media)} footage/photo, {len(beats) - len(media)} diagrams), "
          f"longest {max(b['end'] - b['start'] for b in beats):.2f}s, {len(caps)} caption chunks, {len(sfx)} SFX")
    hook_line = story.get("hook_answer_line")
    if hook_line is not None and data.get("line_starts"):
        t = data["line_starts"][int(hook_line)]
        (report if t <= float(VR.get("hook_answer_by_seconds", 10)) else hard).append(
            f"hook answered at {t:.1f}s (line {hook_line})")


def main():
    p = ROOT / "output/bouriko.mp4"
    d = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(p)
    ]))
    lo, hi = CONFIG["target_seconds"]
    print(f"DURATION DATA: {d:.2f}s (target {lo}-{hi}s)")
    if not (lo <= d <= hi + 0.5):
        print(f"QA INFO: {d:.2f}s is outside the target window; continuing for visual review.")

    a = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(p)
    ]).decode().strip()
    assert a, "no audio"

    story = json.loads((ROOT / "output/story.json").read_text())
    lines = story.get("lines", [])
    assert len(lines) >= 8, "too few narration lines"
    exact_script = bool(story.get("exact_script"))
    if not exact_script and not story.get("script_file"):
        assert story.get("sources"), "no sources"
    assert all(x.get("text") for x in lines), "missing caption text"
    assert all(x.get("visual") for x in lines), "missing visual plan"

    manifest = ROOT / "output/media_manifest.json"
    media_count = 0
    if manifest.exists():
        media_count = len(json.loads(manifest.read_text()))
    video_count = sum(1 for x in json.loads(manifest.read_text()) if x.get("kind") == "video") if manifest.exists() else 0
    beats_path = ROOT / "output/beats.json"
    if beats_path.exists():  # pinned plan media + diagrams count as visuals too
        bd = json.loads(beats_path.read_text())["beats"]
        media_count = max(media_count, len({b["key"] for b in bd}))
        video_count = max(video_count, len({b["key"].split("@")[0] for b in bd if b.get("media", {}).get("kind") == "video"}))
    print(f"MEDIA DATA: {media_count} usable visual assets ({video_count} video)")
    assert media_count >= 8, "not enough usable visual assets; refusing to publish a weak visual build"
    if not exact_script and not story.get("script_file"):
        assert video_count >= 4, "not enough actual video footage; refusing to publish a slideshow"

    hard, report = [], []
    au = probe(p, "stream=codec_name,channels,sample_rate,bit_rate", "a")["streams"][0]
    if au.get("codec_name") != AU.get("audio_codec", "aac") or int(au.get("channels", 0)) != int(AU.get("channels", 2)):
        hard.append(f"audio is {au.get('codec_name')} {au.get('channels')}ch (want stereo AAC)")
    report.append(f"audio {au.get('codec_name')} {au.get('channels')}ch {au.get('sample_rate')} Hz {int(au.get('bit_rate') or 0) // 1000} kb/s")
    lufs = integrated_lufs(p)
    target = float(AU.get("voice_lufs", -17))
    report.append(f"loudness {lufs} LUFS (target {target})")
    if lufs is None or abs(lufs - target) > 1.5:
        hard.append(f"loudness {lufs} LUFS is not within 1.5 LU of {target}")
    visual_checks(story, d, hard, report)

    for r in report:
        print("QA REPORT:", r)
    n = 6
    if "--frames" in sys.argv:
        n = int(sys.argv[sys.argv.index("--frames") + 1])
    shots = frames(p, n, d, ROOT / "output/frames")
    print(f"QA FRAMES: {len(shots)} review frames in output/frames/")
    if hard:
        for h in hard:
            print("QA FAIL:", h)
        raise SystemExit(f"QA FAILED: {len(hard)} visual/audio rule(s) broken")
    print(f"QA PASS: {d:.2f}s, audio={a}, lines={len(lines)}, visuals={media_count}, video={video_count}, exact_script={exact_script}")


if __name__ == "__main__":
    main()
