#!/usr/bin/env python3
"""Offline regression tests for JJK episode metadata and safe, timestamped scene selection."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import anime_scene_library as jjk


class SceneLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lib = Path(self.tmp.name)
        self.lib.joinpath("videos").mkdir()
        self.lib.joinpath("videos", "sample.mp4").write_bytes(b"test-only-video-stub")
        self.patch = patch.object(jjk, "LIBRARY", self.lib)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_verified_episode_index_without_invented_timestamps(self):
        e = jjk.episode_for(3, 3)
        self.assertEqual(e["overall_episode"], 50)
        self.assertEqual(e["title"], "About the Culling Game")
        self.assertEqual(e["scene_offsets_verified"], False)
        self.assertIsNone(jjk.episode_for(4, 99))

    def test_cannot_escape_private_library(self):
        with self.assertRaises(ValueError):
            jjk.library_path("../secret.mp4")
        with self.assertRaises(ValueError):
            jjk.add_scene("../secret.mp4", 3, 3, 1, 3, "rules",
                          ["game", "rule"], [], "owner supplied")

    def test_unreviewed_cue_is_not_renderable(self):
        scene = jjk.add_scene("videos/sample.mp4", 3, 3, 4, 7,
                              "Culling Game rules and scoring",
                              ["rules", "scoring"], ["points"],
                              "owner review only", approved=False)
        self.assertEqual(scene["overall_episode"], 50)
        self.assertIsNone(jjk.choose_scene("Players earn points for sorcerers", 3))
        catalog = jjk.load_catalog()
        catalog["scenes"][0]["approved"] = True
        jjk.save_catalog(catalog)
        found = jjk.choose_scene("Players earn points for sorcerers", 3)
        self.assertEqual(found["id"], scene["id"])
        self.assertEqual(found["start_seconds"], 4)
        self.assertEqual(found["end_seconds"], 7)
        self.assertIsNone(jjk.choose_scene("Players earn points", 3, used={scene["id"]}))

    def test_rejects_unsafe_or_impossible_trim(self):
        for start, end in [(4, 4), (-1, 2), (0, 50)]:
            with self.assertRaises(ValueError):
                jjk.add_scene("videos/sample.mp4", 3, 3, start, end, "rules",
                              ["rules"], [], "owner")

    def test_srt_proposals_are_not_approved(self):
        srt = self.lib / "sub.srt"
        srt.write_text("1\n00:00:04,000 --> 00:00:07,200\n"
                       "The Culling Game rules reward points.\n\n"
                       "2\n00:00:08,000 --> 00:00:10,000\n"
                       "Yuji must save Megumi.\n", encoding="utf-8")
        cues = jjk.subtitle_candidates(srt)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0]["start"], 4.0)
        self.assertEqual(cues[0]["end"], 7.2)

    def test_no_assets_fails_without_generating_placeholders(self):
        output = self.lib / "project"
        output.joinpath("output").mkdir(parents=True)
        with patch.object(jjk, "ROOT", output):
            with self.assertRaisesRegex(RuntimeError, "JJK footage library incomplete"):
                jjk.populate_jjk({"test_topic_id":"jjk",
                    "lines":[{"text":"Kenjaku starts the ritual."}]})


if __name__ == "__main__":
    unittest.main()
