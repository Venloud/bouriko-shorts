#!/usr/bin/env python3
"""Regression: selected visual duration must cover recorded narration."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from remotion_prepare import validate_scene_coverage, source_video_duration


class RemotionMediaCoverageTests(unittest.TestCase):
    def test_rejects_short_video_for_long_narration(self):
        with self.assertRaisesRegex(RuntimeError, "Select a longer scene"):
            validate_scene_coverage(3.0, 7.0)

    def test_accepts_proper_coverage(self):
        validate_scene_coverage(7.0, 6.0)
        validate_scene_coverage(5.99, 6.0)

    def test_rejects_nonpositive_durations(self):
        with self.assertRaises(ValueError):
            validate_scene_coverage(0.0, 6.0)
        with self.assertRaises(ValueError):
            validate_scene_coverage(6.0, -1.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and ffprobe required")
    def test_probe_duration_from_actual_video(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1.8",
                "-c:v", "mpeg4", str(video),
            ], check=True, timeout=30)
            duration = source_video_duration(video)
            self.assertGreater(duration, 1.5)
            self.assertLess(duration, 2.2)
            with self.assertRaises(RuntimeError):
                validate_scene_coverage(duration, 6.0)


if __name__ == "__main__":
    unittest.main()
