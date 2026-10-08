"""Prepare verified, locally available episode clips for the JJK experiment.

A review manifest must name an existing source video and an exact timestamp for
each narration beat. We never infer that a random stream matches a story event.
Run after experiments/jjk_story.py, before voice/remotion preparation.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "experiments/jjk_verified_clips.json"
OUTPUT = ROOT / "output"


def main():
    story_path = OUTPUT / "story.json"
    story = json.loads(story_path.read_text())
    if not INPUT.exists():
        raise RuntimeError(f"Missing verified clip manifest: {INPUT}. Cannot select episodes by keyword alone.")
    specs = json.loads(INPUT.read_text())
    if len(specs) != len(story["lines"]):
        raise RuntimeError(f"Expected {len(story['lines'])} verified clips, got {len(specs)}")
    media_dir = OUTPUT / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    records, matches = [], []
    for index, (line, spec) in enumerate(zip(story["lines"], specs)):
        episode = str(spec.get("episode", "")).strip()
        source = Path(str(spec.get("source_file", "")))
        if not source.is_absolute():
            source = ROOT / source
        start, end = float(spec.get("start", -1)), float(spec.get("end", -1))
        if not episode or not source.is_file() or start < 0 or end <= start:
            raise RuntimeError(f"Scene {index}: missing verified episode, source file or valid start/end")
        if not spec.get("verified_by") or not spec.get("visual_evidence"):
            raise RuntimeError(f"Scene {index}: requires human visual verification and description")
        duration = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(source)]).decode().strip())
        if end > duration:
            raise RuntimeError(f"Scene {index}: timestamp {end}s exceeds episode duration {duration}s")
        target = media_dir / f"jjk_scene_{index:02}.mp4"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(start),"-i",str(source),"-t",str(end-start),"-an","-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast",str(target)],check=True)
        rec = {"index":index,"kind":"video","provider":"verified_episode","episode":episode,"source_url":None,"local_path":str(target.relative_to(ROOT)),"start":start,"end":end,"visual_evidence":spec["visual_evidence"],"verified_by":spec["verified_by"]}
        line.update(media_asset=rec["local_path"],media_kind="video",media_source=rec)
        records.append(rec)
        matches.append({"scene_index":index,"status":"verified","match":{"episode":episode,"start":start,"end":end},"visual_evidence":spec["visual_evidence"],"verified_by":spec["verified_by"]})
    (OUTPUT / "media_manifest.json").write_text(json.dumps(records,indent=2))
    (OUTPUT / "scene_matches.json").write_text(json.dumps(matches,indent=2))
    story_path.write_text(json.dumps(story,indent=2))
    print(f"Prepared {len(records)} verified JJK episode clips")


if __name__ == "__main__":
    main()
