#!/usr/bin/env python3
"""Lossy, silent short-clip extraction from a local source.

Default vertical 9:16 framing uses a centered crop. Optional normalized crop
center overrides it. Never claims that timestamps contain requested events.
Job cleanup deletes only within an explicit isolated job directory.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

def probe(path: Path):
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height:format=duration",
               "-of", "json", str(path)]
    data = json.loads(subprocess.check_output(command, text=True))
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"]), float(data["format"]["duration"])

def crop_filter(width, height, cx, cy):
    # Crop to 9:16 without stretching. Coordinates are center fractions [0,1].
    target_ratio = 9 / 16
    if width / height > target_ratio:
        ch = height
        cw = max(2, int(height * target_ratio) // 2 * 2)
    else:
        cw = width
        ch = max(2, int(width / target_ratio) // 2 * 2)
    x = max(0, min(width - cw, int(width * cx - cw / 2)))
    y = max(0, min(height - ch, int(height * cy - ch / 2)))
    x = x // 2 * 2
    y = y // 2 * 2
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1"

def run():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--start", type=float, required=True, help="source timeline seconds")
    p.add_argument("--duration", type=float, required=True, help="length in seconds, max 3")
    p.add_argument("--center-x", type=float, default=.5)
    p.add_argument("--center-y", type=float, default=.5)
    p.add_argument("--job-dir", type=Path, help="isolated disposable source directory")
    p.add_argument("--delete-job-source", action="store_true",
                   help="delete only this source in job-dir after clip passes probe")
    args = p.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if not (0 < args.duration <= 3):
        p.error("clip duration must be > 0 and <= 3 seconds")
    if args.start < 0 or not (0 <= args.center_x <= 1 and 0 <= args.center_y <= 1):
        p.error("invalid timeline or crop center")
    if source == output:
        p.error("source and output cannot be the same file")
    w, h, source_duration = probe(source)
    if args.start + args.duration > source_duration + .05:
        p.error("requested clip exceeds source duration")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.stem + ".partial.mp4")
    temp.unlink(missing_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-ss", str(args.start), "-i", str(source),
           "-t", str(args.duration), "-vf", crop_filter(w, h, args.center_x, args.center_y),
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temp)]
    try:
        subprocess.run(cmd, check=True)
        ow, oh, od = probe(temp)
        if (ow, oh) != (1080, 1920) or not (0 < od <= 3.05):
            raise RuntimeError(f"invalid output dimensions/duration: {ow}x{oh}, {od:.3f}s")
        if temp.stat().st_size < 10000:
            raise RuntimeError("clip too small")
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    print(json.dumps({"status": "VERIFIED_EDIT", "clip": str(output), "start": args.start,
                      "duration": od, "dimensions": [ow, oh], "source_audio": "REMOVED",
                      "note": "The event shown in this clip has NOT been semantically verified."}))
    if args.delete_job_source:
        if not args.job_dir:
            p.error("--delete-job-source requires --job-dir")
        job = args.job_dir.resolve(strict=True)
        expected = (Path.home() / "homebeacon" / "media" / "youtube" / "jobs").resolve()
        if expected not in job.parents or job == expected:
            raise RuntimeError("refusing deletion outside HomeBeacon isolated jobs")
        if job not in source.parents:
            raise RuntimeError("source is not inside the specified job directory")
        if output == source or job in output.parents:
            raise RuntimeError("output must be outside disposable job directory")
        source.unlink()
        print("DELETED_JOB_SOURCE:", source)

if __name__ == "__main__":
    run()
