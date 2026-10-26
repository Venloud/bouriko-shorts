#!/usr/bin/env python3
"""Offline Bouriko media acceptance regression (no network or YouTube login)."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from media import mixkit, usable_media_file

class FakeReply:
    def __init__(self, request_url, actual_url=None, title="cars"):
        self.ok = True
        self.url = actual_url or request_url
        self.text = ('<html><head><title>Free ' + title +
                     ' stock videos</title></head><body>' +
                     'https://assets.mixkit.co/videos/64/64-720.mp4' +
                     '</body></html>')

def fake_unrelated(url, **kwargs):
    return FakeReply(url, title="cars")

with patch("media.requests.get", side_effect=fake_unrelated):
    assert mixkit("glycerin moisture skincare cosmetic demonstration", "video") == [], (
        "Unrelated cars page was accepted for a beauty video"
    )
with patch("media.requests.get", side_effect=lambda url, **kw: FakeReply(url, title="skincare cream")):
    assert len(mixkit("skincare cream", "video")) == 1, "Topical stock page was incorrectly rejected"
with patch("media.requests.get", side_effect=lambda url, **kw: FakeReply(url, actual_url="https://mixkit.co/free-stock-video/cars/")):
    assert mixkit("skincare cream", "video") == [], "Redirected unrelated category accepted"
print("PASS: Mixkit topical page check rejects mislabeled cars.")

with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    broken = folder / "broken.mp4"
    broken.write_bytes(b"not a video stream" * 200)
    assert not usable_media_file(broken, "video"), "Corrupt media accepted"
    good = folder / "real.mp4"
    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=64x64:r=5",
        "-t", "1.2", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(good)
    ], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert usable_media_file(good, "video"), "Valid MP4 rejected"
    ogv = folder / "not_supported.ogv"
    shutil.copy2(good, ogv)
    assert not usable_media_file(ogv, "video"), "Unsupported extension accepted"
print("PASS: video stream ffprobe detects corrupt media and unsupported containers.")
