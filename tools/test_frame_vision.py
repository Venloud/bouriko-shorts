#!/usr/bin/env python3
"""Offline pixel-gate regression: never confuse a transcript match for visuals."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import frame_vision as vision


class VisualFramesTests(unittest.TestCase):
    def test_matched_two_frames_pass_review_only(self):
        scores = [[.31, .15, .13], [.32, .20, .14], [.14, .23, .21]]
        decision = vision.decide_visual(scores, {}, [])
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["passing_frame_count"], 2)
        self.assertIn("REVIEW_REQUIRED", decision["reason"])

    def test_spoken_about_but_not_shown_rejected(self):
        scores = [[.12, .30], [.18, .27], [.19, .20], [.13, .26]]
        decision = vision.decide_visual(scores, {}, [])
        self.assertFalse(decision["accepted"])
        self.assertEqual(decision["reason"], "FRAMES_DO_NOT_SHOW_SUBJECT")

    def test_named_person_requires_two_reference_matches(self):
        visual = [[.33, .1], [.35, .10], [.31, .15]]
        self.assertEqual(vision.decide_visual(visual, {}, ["Amina"])["reason"],
                         "MISSING_IDENTITY_REFERENCE")
        ref_scores = {"Amina": [[.61], [.74], [.53]]}
        self.assertEqual(
            vision.decide_visual(visual, ref_scores, ["Amina"])["reason"],
            "CHARACTER_OR_OBJECT_NOT_VISIBLE")
        ref_scores["Amina"] = [[.75], [.78], [.61]]
        self.assertTrue(vision.decide_visual(visual, ref_scores, ["Amina"])["accepted"])

    def test_name_detection_general_purpose(self):
        self.assertEqual(vision.proper_names("Kenjaku created the rules."), ["Kenjaku"])
        self.assertEqual(vision.proper_names("Yuji and Megumi discuss the rules."),
                         ["Yuji", "Megumi"])
        self.assertEqual(vision.proper_names("Players earn points."), [])

    def test_private_reference_folder_does_not_escape(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            refs = folder / "references"
            refs.mkdir()
            (folder / "hidden.png").write_bytes(b"x")
            (refs / "index.json").write_text(
                json.dumps({"entities": {"amina": ["../hidden.png"]}}),
                encoding="utf-8")
            with self.assertRaises(ValueError):
                vision.reference_images(folder, ["Amina"])
            (refs / "index.json").write_text(
                json.dumps({"entities": {"amina": ["not-here.png"]}}),
                encoding="utf-8")
            with self.assertRaises(ValueError):
                vision.reference_images(folder, ["Amina"])

    def test_missing_reference_blocks_before_model_or_download(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(vision, "sample_frames") as sample:
                result = vision.inspect_clip("some-video.mp4",
                    "Kenjaku explains the plan", "Jujutsu Kaisen",
                    library=td)
                self.assertFalse(result["accepted"])
                self.assertEqual(result["reason"], "MISSING_IDENTITY_REFERENCE")
                sample.assert_not_called()

    def test_inspector_uses_frame_scores_and_records_subject(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(vision, "sample_frames", return_value=[1, 2, 3]), \
                 patch.object(vision, "score_images", return_value=(
                   [[.32,.14],[.31,.18],[.16,.25]], {})) as scorer:
                result = vision.inspect_clip("video.mp4", "Satellites send signals",
                    "GPS navigation", library=td)
            self.assertTrue(result["accepted"])
            self.assertEqual(result["source"], "sampled_video_frames")
            self.assertFalse(result["rights_verified"])
            self.assertIn("GPS navigation", scorer.call_args.args[1][0])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Needs installed FFmpeg/FFprobe on CI")
    def test_real_sampled_pixels_not_thumbnail(self):
        with tempfile.TemporaryDirectory() as td:
            clip = Path(td) / "source.mp4"
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", "color=c=red:s=320x240:d=1.8",
                 "-c:v", "mpeg4", str(clip)],
                check=True, timeout=25)
            frames = vision.sample_frames(clip, count=3)
            self.assertEqual(len(frames), 3)
            self.assertTrue(all(im.size[0] >= 100 and im.size[1] >= 100
                                for im in frames))
            self.assertTrue(all(im.getpixel((5, 5))[0] > 150 for im in frames))


if __name__ == "__main__":
    unittest.main()
