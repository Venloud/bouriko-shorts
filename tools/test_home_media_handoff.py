#!/usr/bin/env python3
"""Offline fixture for Windows->GitHub artifact handoff; no network required."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verify_home_media as verify

def expect_failure(fn, message):
    try:
        fn()
    except (ValueError, OSError):
        return
    raise AssertionError(message)

with tempfile.TemporaryDirectory() as temp:
    base = Path(temp)
    output = base / "output"
    media = output / "media"
    media.mkdir(parents=True)
    good = media / "test_cc.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "color=c=blue:s=64x64:r=5",
           "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(good)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    rel = "output/media/test_cc.mp4"
    story = {"lines": [{"text": "A traffic light stops cars.", "media_asset": rel}]}
    metadata = [{"index": 0, "query": "traffic light intersection",
                 "kind": "video", "provider": "youtube_cc",
                 "license": "Creative Commons Attribution",
                 "local_path": rel,
                 "source_url": "https://www.youtube.com/watch?v=licensed_example"}]
    (output / "story.json").write_text(json.dumps(story))
    (output / "media_manifest.json").write_text(json.dumps(metadata))
    with patch.object(verify, "ROOT", base), patch.object(verify, "STORY", output / "story.json"), \
         patch.object(verify, "MANIFEST", output / "media_manifest.json"):
        receipt = verify.audit(min_youtube=1)
        assert receipt["youtube_count"] == 1
        assert receipt["media_count"] == 1
        assert receipt["file_sha256"][rel] == verify.checksum(good)
        expect_failure(lambda: verify.audit(min_youtube=2), "Accepted fewer than required YouTube files")
        metadata[0]["license"] = "Standard YouTube License"
        (output / "media_manifest.json").write_text(json.dumps(metadata))
        expect_failure(lambda: verify.audit(1), "Accepted unlicensed YouTube candidate")
        metadata[0]["license"] = "Creative Commons Attribution"
        metadata[0]["local_path"] = "../../outside.mp4"
        (output / "media_manifest.json").write_text(json.dumps(metadata))
        expect_failure(lambda: verify.audit(1), "Accepted directory-traversal path")
        metadata[0]["local_path"] = rel
        (output / "media_manifest.json").write_text(json.dumps(metadata))
        assert verify.audit(1) == receipt
        good.write_bytes(b"corrupted video")
        expect_failure(lambda: verify.audit(1), "Accepted corrupted media")
print("PASS: home-media receipt checks licensed source, hash, paths, and playable MP4.")
