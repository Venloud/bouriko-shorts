"""Optional real-world footage support for Bouriko.

Real clips are an enhancement, never a hard dependency. Sources should be
owned, licensed, public-domain, or otherwise permitted for the channel's use.
A story line can reference a local file or a URL in a real_clip visual action.
"""
import json
import shutil
import subprocess
from pathlib import Path

from common import ROOT, run


def _safe_name(value):
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(value))[:100]


def resolve_source(source, out_dir):
    """Return a local MP4 path for a local file or permitted downloadable URL."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source = str(source or "").strip()
    if not source:
        raise ValueError("real_clip requires a source")

    local = ROOT / source if not Path(source).is_absolute() else Path(source)
    if local.exists():
        return local

    if not source.startswith(("http://", "https://")):
        raise FileNotFoundError(f"Real clip not found: {source}")

    target = out_dir / (_safe_name(source.rsplit("/", 1)[-1]) or "real_clip")
    if target.suffix.lower() != ".mp4":
        target = target.with_suffix(".mp4")

    if target.exists() and target.stat().st_size > 0:
        return target

    # yt-dlp is installed by CI only for this optional path.
    run([
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--max-filesize", "80M",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "-o", str(target),
        source,
    ])
    if not target.exists():
        raise RuntimeError(f"yt-dlp did not produce {target}")
    return target


def prepare_vertical(source, out_path, duration):
    """Crop/pad a source clip to Bouriko's 1080x1920 vertical canvas."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-stream_loop", "-1", "-i", str(source),
        "-t", f"{float(duration):.3f}",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path),
    ])
    return out_path


def load_action(line):
    for action in line.get("visual_actions", []) or []:
        if str(action.get("type", "")).lower() == "real_clip":
            return action
    action = line.get("real_clip")
    return action if isinstance(action, dict) else None
